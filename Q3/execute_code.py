def execute_python_code(code: str) -> dict:
    """
    Execute Python code and return exact output.

    Returns:
        {
            "success": bool,
            "output": str  # Exact stdout or traceback
        }
    """
    import sys
    from io import StringIO
    import traceback

    # Capture stdout
    old_stdout = sys.stdout
    sys.stdout = StringIO()

    try:
        # Execute code
        exec(code)
        output = sys.stdout.getvalue()
        return {"success": True, "output": output}

    except Exception as e:
        # Get full traceback
        output = traceback.format_exc()
        return {"success": False, "output": output}

    finally:
        sys.stdout = old_stdout