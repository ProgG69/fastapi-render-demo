import execute_code
import ai_error_analysis
from fastapi import FastAPI,HTTPException
from pydantic import BaseModel

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Add this block right after app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # Allow all origins
    allow_methods=["*"],      # Allow GET, POST, etc.
    allow_headers=["*"],
)

class Input(BaseModel):
    code:str
class Response(BaseModel):
    error:list[int]
    result:str

@app.post("/code-interpreter", response_model = Response)

async def analyze_code(input:Input):
    try:
        result = execute_code.execute_python_code(input.code)
        if result["success"] == True:
            return Response(
                error = [],
                result = result["output"].strip()
            )
        else:
            error_lines = ai_error_analysis.analyze_error_with_ai(
                code=input.code,
                traceback=result["output"]      # The error traceback is in "output"
            )
            return Response(
                error = error_lines,
                result = result["output"]
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))