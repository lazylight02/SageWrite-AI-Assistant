"""
SageWrite — AI Professional Communication Assistant
Root entrypoint to allow seamless execution from repository root:
    streamlit run app.py
"""
import os
import sys
from pathlib import Path

# Target inner app path
target_app = Path(__file__).resolve().parent / "ai_communication_assistant" / "app.py"

if not target_app.is_file():
    raise FileNotFoundError(f"Could not locate main application at {target_app}")

# Execute main application script
with open(target_app, "r", encoding="utf-8") as f:
    code = compile(f.read(), str(target_app), "exec")
    exec(code, {"__name__": "__main__", "__file__": str(target_app)})
