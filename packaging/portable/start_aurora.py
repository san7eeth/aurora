"""Windows entry point for the user-facing Start Aurora.exe launcher."""

import json
import os
from pathlib import Path
import platform
import subprocess
import sys
from urllib.error import URLError
from urllib.request import urlopen


def _show_message(message: str, title: str = "Aurora") -> int:
    if os.name == "nt":
        import ctypes

        return ctypes.windll.user32.MessageBoxW(None, message, title, 0x00000001 | 0x00000040)
    print(f"{title}: {message}", file=sys.stderr)
    return 1


def _configured_model() -> str:
    local_app_data = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    config = local_app_data / "Aurora" / "config" / "aurora.env"
    if config.is_file():
        for line in config.read_text(encoding="utf-8").splitlines():
            key, separator, value = line.partition("=")
            if separator and key.strip() == "OLLAMA_MODEL":
                model = value.strip().strip("\"'")
                if not model:
                    raise ValueError(f"OLLAMA_MODEL is empty in {config}")
                return model
    return "llama3.2:3b"


def _ollama_status(model: str) -> str | None:
    try:
        with urlopen("http://127.0.0.1:11434/api/tags", timeout=2) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (OSError, URLError, ValueError):
        return (
            "Aurora uses Ollama for local AI, but Ollama is not responding at "
            "http://127.0.0.1:11434.\n\nInstall Ollama from https://ollama.com/download, "
            "start it, then run `ollama run " + model + "`. You can still open Aurora "
            "without Ollama."
        )
    if not isinstance(data, dict) or not isinstance(data.get("models"), list):
        return "Ollama returned an unexpected model list. Check the local Ollama installation and try again."
    models = data["models"]
    names = {entry.get("name") for entry in models if isinstance(entry, dict)}
    if model not in names and f"{model}:latest" not in names:
        return (
            f"The configured Ollama model '{model}' is not installed.\n\n"
            f"Open a terminal and run `ollama run {model}`. You can still open Aurora."
        )
    return None


def main() -> int:
    if os.name != "nt":
        _show_message("This Aurora package supports Windows 10/11 x64 only.")
        return 1
    if sys.getwindowsversion().major < 10:
        _show_message("This Aurora package requires Windows 10 or Windows 11.")
        return 1
    if platform.machine().lower() not in {"amd64", "x86_64"}:
        _show_message("This Aurora package requires a 64-bit x64 Windows computer.")
        return 1

    app_dir = Path(sys.executable).resolve().parent
    app_exe = app_dir / "Aurora.exe"
    if not app_exe.is_file() or not (app_dir / "runtime").is_dir():
        _show_message("Aurora.exe or its runtime folder is missing. Re-extract the complete ZIP.")
        return 1

    try:
        model = _configured_model()
    except (OSError, ValueError) as exc:
        _show_message(f"Aurora could not read its Ollama model setting:\n{exc}")
        return 1
    warning = _ollama_status(model)
    if warning and _show_message(warning + "\n\nChoose OK to continue or Cancel to exit.") == 2:
        return 0
    try:
        subprocess.Popen([str(app_exe)], cwd=str(app_dir), close_fds=True)
    except OSError as exc:
        _show_message(f"Aurora could not be started:\n{exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
