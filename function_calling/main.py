from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
import json

app = FastAPI()

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Use aipipe as the OpenAI-compatible proxy
client = OpenAI(
    api_key="eyJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6IjI1ZHMzMDAwMTE5QGRzLnN0dWR5LmlpdG0uYWMuaW4ifQ.h1tYPsuTaQhRjZ0IBXL6t7em244Yuxaza6kVD0-rVNc",
    base_url="https://aipipe.org/openai/v1"
)

# Define all 5 functions as OpenAI tools
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_ticket_status",
            "description": "Get the status of an IT support ticket",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticket_id": {"type": "integer", "description": "The ticket ID number"}
                },
                "required": ["ticket_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "schedule_meeting",
            "description": "Schedule a meeting on a given date, time and room",
            "parameters": {
                "type": "object",
                "properties": {
                    "date":         {"type": "string", "description": "Date in YYYY-MM-DD format"},
                    "time":         {"type": "string", "description": "Time in HH:MM format"},
                    "meeting_room": {"type": "string", "description": "The meeting room name"}
                },
                "required": ["date", "time", "meeting_room"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_expense_balance",
            "description": "Get the expense reimbursement balance for an employee",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_id": {"type": "integer", "description": "The employee ID number"}
                },
                "required": ["employee_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_performance_bonus",
            "description": "Calculate the performance bonus for an employee for a given year",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_id":  {"type": "integer", "description": "The employee ID number"},
                    "current_year": {"type": "integer", "description": "The year for the bonus calculation"}
                },
                "required": ["employee_id", "current_year"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "report_office_issue",
            "description": "Report an office issue by issue code and department",
            "parameters": {
                "type": "object",
                "properties": {
                    "issue_code":  {"type": "integer", "description": "The office issue code number"},
                    "department":  {"type": "string",  "description": "The department name"}
                },
                "required": ["issue_code", "department"]
            }
        }
    }
]


@app.get("/execute")
async def execute(q: str):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a corporate assistant. Identify the correct function to call based on the user query and extract all parameters."},
                {"role": "user", "content": q}
            ],
            tools=TOOLS,
            tool_choice="required"   # Force it to always call a function
        )

        tool_call = response.choices[0].message.tool_calls[0]
        
        # Parse arguments to ensure correct ordering
        args = json.loads(tool_call.function.arguments)

        return {
            "name": tool_call.function.name,
            "arguments": json.dumps(args)   # Re-encode as compact JSON string
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
