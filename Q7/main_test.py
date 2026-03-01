import os
import re
import tempfile
import subprocess
import time
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import google.generativeai as genai

from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title="Video Timestamp Search API")

# Add this block right after app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # Allow all origins
    allow_methods=["*"],      # Allow GET, POST, etc.
    allow_headers=["*"],
)

# Configure Gemini
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)


class AskRequest(BaseModel):
    video_url: str
    topic: str


class AskResponse(BaseModel):
    timestamp: str
    video_url: str
    topic: str


def download_audio(video_url: str, output_path: str) -> str:
    """Download audio-only from YouTube using yt-dlp."""
    cmd = [
        "yt-dlp",
        "--no-playlist",
        "-x",                        # Extract audio only
        "--audio-format", "mp3",     # Convert to mp3
        "--audio-quality", "0",      # Best quality
        "-o", output_path,
        video_url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        raise RuntimeError(f"yt-dlp failed: {result.stderr}")
    return output_path


def upload_and_wait(file_path: str):
    """Upload file to Gemini Files API and wait for it to become ACTIVE."""
    uploaded_file = genai.upload_file(path=file_path, mime_type="audio/mpeg")
    # Poll until ACTIVE
    max_wait = 120  # seconds
    waited = 0
    while uploaded_file.state.name != "ACTIVE":
        if waited >= max_wait:
            raise RuntimeError("Uploaded file did not become ACTIVE in time.")
        time.sleep(5)
        waited += 5
        uploaded_file = genai.get_file(uploaded_file.name)
    return uploaded_file


def ask_gemini_for_timestamp(uploaded_file, topic: str) -> str:
    """Ask Gemini to find when the topic is spoken in the audio."""
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            response_schema={
                "type": "object",
                "properties": {
                    "timestamp": {
                        "type": "string",
                        "description": "Timestamp in HH:MM:SS format when the topic is first spoken or discussed"
                    }
                },
                "required": ["timestamp"]
            }
        )
    )

    prompt = f"""Listen carefully to this audio and find the exact moment when the topic "{topic}" is first spoken or discussed.

Return a JSON object with a single field "timestamp" containing the time in HH:MM:SS format (e.g. "00:05:47").

Rules:
- The timestamp MUST be in HH:MM:SS format with exactly 2 digits for each unit (hours, minutes, seconds)
- Return the FIRST occurrence of the topic
- If the topic is not found, return "00:00:00"

Find when "{topic}" is first mentioned."""

    response = model.generate_content([uploaded_file, prompt])
    
    # Parse JSON response
    try:
        data = json.loads(response.text)
        timestamp = data.get("timestamp", "00:00:00")
    except (json.JSONDecodeError, AttributeError):
        # Try to extract HH:MM:SS from text
        match = re.search(r'\d{2}:\d{2}:\d{2}', response.text or "")
        timestamp = match.group(0) if match else "00:00:00"

    # Validate HH:MM:SS format
    if not re.match(r'^\d{2}:\d{2}:\d{2}$', timestamp):
        # Try to fix MM:SS -> 00:MM:SS
        mm_ss = re.search(r'^(\d{1,2}):(\d{2})$', timestamp)
        if mm_ss:
            timestamp = f"00:{mm_ss.group(1).zfill(2)}:{mm_ss.group(2)}"
        else:
            timestamp = "00:00:00"

    return timestamp


@app.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest):
    """
    Given a YouTube URL and a topic/phrase, return the timestamp (HH:MM:SS)
    when that topic is first spoken in the video.
    """
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured")

    audio_path = None
    uploaded_file = None

    try:
        # Create a temp file path for the audio
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            audio_path = tmp.name

        # 1. Download audio using yt-dlp
        download_audio(request.video_url, audio_path)

        # 2. Upload to Gemini Files API
        uploaded_file = upload_and_wait(audio_path)

        # 3. Ask Gemini for the timestamp
        timestamp = ask_gemini_for_timestamp(uploaded_file, request.topic)

        return AskResponse(
            timestamp=timestamp,
            video_url=request.video_url,
            topic=request.topic
        )

    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    finally:
        # Clean up temp audio file
        if audio_path and os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except Exception:
                pass
        # Delete uploaded file from Gemini
        if uploaded_file:
            try:
                genai.delete_file(uploaded_file.name)
            except Exception:
                pass


@app.get("/")
def root():
    return {"message": "Video Timestamp Search API. POST /ask with video_url and topic."}
