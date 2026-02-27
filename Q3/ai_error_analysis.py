from pydantic import BaseModel
from google import genai
from google.genai import types
from typing import List
import os
from dotenv import load_dotenv
load_dotenv()   # ← This reads .env and sets all variables automatically

class ErrorAnalysis(BaseModel):
    error_lines: List[int]  # Line numbers with errors

client = genai.Client(api_key=os.environ.get("AIzaSyD0PwfnX4mG50YXiI8x0uTguochDi9QTgY"))

def analyze_error_with_ai(code: str, traceback: str) -> List[int]:
    """
    Use LLM with structured output to identify error line numbers.
    """

    prompt = f"""
Analyze this Python code and its error traceback.
Identify the line number(s) where the error occurred.

CODE:
{code}

TRACEBACK:
{traceback}

Return the line number(s) where the error is located.
"""

    response = client.models.generate_content(
        model='gemini-2.5-flash-exp',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "error_lines": types.Schema(
                        type=types.Type.ARRAY,
                        items=types.Schema(type=types.Type.INTEGER)
                    )

                },
                required=["error_lines"]
            )
        )
    )

    result = ErrorAnalysis.model_validate_json(response.text)
    return result.error_lines