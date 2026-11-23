"""Small, allowlisted local tools. No shell or arbitrary-path execution is exposed."""

import os
import platform
import subprocess
from pathlib import Path


TOOL_SCHEMAS = [
    {
        "name": "system_info",
        "description": "Read basic operating system and runtime information.",
        "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "list_files",
        "description": "List filenames in Aurora's uploaded documents folder (names and sizes only).",
        "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "launch_app",
        "description": "Open one of the built-in allowlisted desktop apps.",
        "parameters": {
            "type": "object",
            "properties": {"app": {"type": "string", "enum": ["notepad", "calculator", "settings"]}},
            "required": ["app"],
            "additionalProperties": False,
        },
    },
    {
        "name": "clipboard_read",
        "description": "Read up to 1000 characters of Windows text clipboard content.",
        "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
    },
]

SENSITIVE_TOOLS = {"launch_app", "clipboard_read"}
TOOL_NAMES = {tool["name"] for tool in TOOL_SCHEMAS}


def validate_arguments(name: str, arguments: dict) -> dict:
    if name not in TOOL_NAMES or not isinstance(arguments, dict):
        raise ValueError("Unknown tool or invalid arguments")
    if name == "launch_app":
        if set(arguments) != {"app"} or arguments["app"] not in {"notepad", "calculator", "settings"}:
            raise ValueError("App must be one of notepad, calculator, or settings")
    elif arguments:
        raise ValueError(f"{name} does not accept arguments")
    return arguments


def execute_tool(name: str, arguments: dict) -> dict:
    validate_arguments(name, arguments)
    if name == "system_info":
        return {
            "os": platform.platform(),
            "python": platform.python_version(),
            "architecture": platform.machine(),
            "logical_cpus": os.cpu_count(),
        }
    if name == "list_files":
        from ..intent.load_documents import DOCS_DIR
        root = Path(DOCS_DIR).resolve()
        root.mkdir(parents=True, exist_ok=True)
        return {"directory": "Aurora uploaded documents", "files": [
            {"name": item.name, "size_bytes": item.stat().st_size}
            for item in sorted(root.iterdir()) if item.is_file() and item.resolve().parent == root
        ][:100]}
    if name == "launch_app":
        if platform.system() != "Windows":
            raise RuntimeError("Allowlisted app launch is currently supported on Windows only")
        app = arguments["app"]
        if app == "notepad":
            subprocess.Popen(["notepad.exe"], shell=False)
        elif app == "calculator":
            subprocess.Popen(["calc.exe"], shell=False)
        else:
            os.startfile("ms-settings:")  # fixed URI; never accepts user-supplied commands
        return {"launched": app}
    if name == "clipboard_read":
        if platform.system() != "Windows":
            raise RuntimeError("Clipboard reading is currently supported on Windows only")
        import win32clipboard
        win32clipboard.OpenClipboard()
        try:
            text = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
        except TypeError:
            text = ""
        finally:
            win32clipboard.CloseClipboard()
        return {"text": str(text)[:1000]}
    raise ValueError("Unknown tool")
