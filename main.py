from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import OpenAI
import json

app = FastAPI()

# 1. Setup the AI connection using your AIpipe details
# Using the OpenRouter endpoint as per your documentation
client = OpenAI(
    api_key="eyJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6IjI1ZHMzMDAwMTE5QGRzLnN0dWR5LmlpdG0uYWMuaW4ifQ.h1tYPsuTaQhRjZ0IBXL6t7em244Yuxaza6kVD0-rVNc",
    base_url="https://aipipe.org/openrouter/v1"
)

# 2. Blueprints: This tells FastAPI what the data SHOULD look like
class RequestBody(BaseModel):
    comment: str

class SentimentResponse(BaseModel):
    sentiment: str
    rating: int

# 3. The Endpoint: This is the 'mailbox' where comments are sent
@app.post("/comment", response_model = SentimentResponse)
async def analyze_comment(data: RequestBody):
    try:
        # 4. Ask the AI for a structured response
        completion = client.chat.completions.create(
            model="gpt-4.1-mini",  # Assignment requirement
            messages=[
                {"role": "system", "content": "Analyze sentiment of user review or comment. You must respond ONLY with JSON."},
                {"role": "user", "content": data.comment}
            ],
            # 5. This 'response_format' is the Structured Output feature
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "sentiment_analysis",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "sentiment": {"type": "string", "enum": ["positive", "negative", "neutral"]},
                            "rating": {"type": "integer", "minimum": 1, "maximum": 5}
                        },
                        "required": ["sentiment", "rating"]
                    }
                }
            }
        )

        # 6. Take the AI's text and turn it into a real Python object
        raw_content = completion.choices[0].message.content
        return json.loads(raw_content)

    except Exception as e:
        # This helps you see why it failed (like the 403 regional block)
        raise HTTPException(status_code=500, detail=str(e))