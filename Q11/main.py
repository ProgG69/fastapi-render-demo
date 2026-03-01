import sys
import json
import time
import os
from google import genai
from google.genai import types
from pydantic import BaseModel
from typing import List


# ── Data models ──────────────────────────────────────────────
class Attendee(BaseModel):
    name: str
    date: str          # format: dd/mm/yyyy

class AttendeeList(BaseModel):
    attendees: List[Attendee]

# ── Main logic ───────────────────────────────────────────────
def extract_attendees(video_path: str) -> List[dict]:
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

    MY_NEW_KEY = "AIzaSyBUBv7UmCT68IA7cCE6c2G-4HRPCQeY_CA"

    client = genai.Client(api_key=MY_NEW_KEY)

    # Step 1: Upload video to Gemini Files API
    print(f"Uploading {video_path}...")
    video_file = client.files.upload(
        file=video_path,
        config={"mime_type": "video/webm"}
    )
    print(f"Uploaded: {video_file.name}")

    # Step 2: Wait until Gemini finishes processing the video
    print("Waiting for video to be processed...")
    while video_file.state.name == "PROCESSING":
        time.sleep(3)
        video_file = client.files.get(name=video_file.name)
        print(f"  State: {video_file.state.name}")

    if video_file.state.name == "FAILED":
        raise ValueError("Video processing failed!")

    print("Video ready. Extracting attendees...")

    # Step 3: Ask Gemini to extract all attendees with structured output
    response = client.models.generate_content(
        model="gemini-2.0-flash-lite",
        contents=[
            video_file,
            """Watch this entire check-in video carefully.
Extract ALL attendee name and check-in date pairs shown on screen.
- Capture every single entry shown throughout the full video.
- Date format must be dd/mm/yyyy (e.g. 03/07/2025).
- Return exactly 20 attendees if 20 are shown."""
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "attendees": types.Schema(
                        type=types.Type.ARRAY,
                        items=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "name": types.Schema(type=types.Type.STRING),
                                "date": types.Schema(type=types.Type.STRING)
                            },
                            required=["name", "date"]
                        )
                    )
                },
                required=["attendees"]
            )
        )
    )

    # Step 4: Parse and return
    result = AttendeeList.model_validate_json(response.text)
    return [{"name": a.name, "date": a.date} for a in result.attendees]


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py attendee_checkin.webm")
        sys.exit(1)

    video_path = sys.argv[1]
    attendees = extract_attendees(video_path)

    # Print final JSON — copy this into the assignment field
    print("\n── FINAL JSON OUTPUT ──")
    print(json.dumps(attendees, indent=2))

    # Also save to file so you don't lose it
    with open("attendees_output.json", "w") as f:
        json.dump(attendees, f, indent=2)
    print("\nSaved to attendees_output.json")
