"""PyInstaller entry point for the local Windows app bundle."""

import argparse
import os
from pathlib import Path
import sys
import threading
import time
import webbrowser


def _resource_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parents[1]


def _user_data_root(override: str | None = None) -> Path:
    configured = override or os.environ.get("AURORA_DATA_DIR")
    if configured:
        return Path(configured).expanduser().resolve()
    local_app_data = os.environ.get("LOCALAPPDATA")
    base = Path(local_app_data) if local_app_data else Path.home() / "AppData" / "Local"
    return base / "Aurora"


def _configure_runtime(data_directory: str | None = None, port: int = 8000) -> tuple[Path, Path, Path]:
    data_dir = _user_data_root(data_directory)
    log_dir = data_dir / "logs"
    data_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    os.environ["AURORA_DATA_DIR"] = str(data_dir)
    os.environ["AURORA_FRONTEND_DIST"] = str(_resource_root() / "frontend" / "dist")
    os.environ["AURORA_LOG_FILE"] = str(log_dir / "aurora.log")
    os.environ.setdefault("HF_HOME", str(data_dir / "models" / "huggingface"))
    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{(data_dir / 'aurora.db').resolve().as_posix()}"
    os.environ["BACKEND_HOST"] = "127.0.0.1"
    os.environ["BACKEND_PORT"] = str(port)
    os.environ.setdefault("LOG_LEVEL", "INFO")
    os.environ.setdefault("LOG_JSON", "true")
    (data_dir / "models" / "huggingface").mkdir(parents=True, exist_ok=True)
    return data_dir, log_dir, Path(os.environ["AURORA_FRONTEND_DIST"])


def _read_pid(pid_path: Path) -> int | None:
    try:
        return int(pid_path.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return None


def _is_running(pid: int | None) -> bool:
    if not pid:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _request_shutdown(data_dir: Path) -> int:
    pid_path = data_dir / "aurora.pid"
    stop_path = data_dir / "stop.request"
    pid = _read_pid(pid_path)
    if not _is_running(pid):
        pid_path.unlink(missing_ok=True)
        print("Aurora is not running.")
        return 0
    stop_path.write_text("stop", encoding="utf-8")
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if not _is_running(_read_pid(pid_path)):
            print("Aurora stopped cleanly.")
            return 0
        time.sleep(0.25)
    print("Aurora did not stop before the 20 second timeout.")
    return 1


def _run_server(data_dir: Path, frontend_dist: Path, open_browser: bool, port: int) -> int:
    pid_path = data_dir / "aurora.pid"
    stop_path = data_dir / "stop.request"
    existing_pid = _read_pid(pid_path)
    if _is_running(existing_pid):
        if open_browser:
            webbrowser.open(f"http://127.0.0.1:{port}/")
        return 0
    pid_path.unlink(missing_ok=True)
    stop_path.unlink(missing_ok=True)

    if not (frontend_dist / "index.html").is_file():
        raise FileNotFoundError(f"Built frontend not found: {frontend_dist}")

    backend_root = _resource_root() / "backend"
    if str(backend_root) not in sys.path:
        sys.path.insert(0, str(backend_root))

    import uvicorn
    from app.api import app

    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=port,
        log_config=None,
        log_level=os.environ.get("LOG_LEVEL", "INFO").lower(),
        access_log=False,
    )
    server = uvicorn.Server(config)
    server_thread = threading.Thread(target=server.run, name="aurora-api", daemon=True)
    server_thread.start()

    startup_deadline = time.monotonic() + 90
    while not server.started and server_thread.is_alive() and time.monotonic() < startup_deadline:
        time.sleep(0.2)
    if not server.started:
        server.should_exit = True
        server_thread.join(timeout=5)
        raise RuntimeError("Aurora backend failed to start; see the log in %LOCALAPPDATA%\\Aurora\\logs.")

    pid_path.write_text(str(os.getpid()), encoding="utf-8")
    if open_browser:
        webbrowser.open(f"http://127.0.0.1:{port}/")

    try:
        while server_thread.is_alive():
            if stop_path.exists():
                stop_path.unlink(missing_ok=True)
                server.should_exit = True
            server_thread.join(timeout=0.25)
    except KeyboardInterrupt:
        server.should_exit = True
        server_thread.join(timeout=10)
    finally:
        pid_path.unlink(missing_ok=True)
        stop_path.unlink(missing_ok=True)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Aurora local assistant")
    parser.add_argument("--shutdown", action="store_true", help="request a graceful stop of the running Aurora server")
    parser.add_argument("--no-browser", action="store_true", help="start the local server without opening a browser")
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("AURORA_PORT", "8000")),
        help="loopback HTTP port (default: 8000)",
    )
    parser.add_argument("--data-dir", help="override the writable user data directory")
    arguments = parser.parse_args()

    data_dir, _log_dir, frontend_dist = _configure_runtime(arguments.data_dir, arguments.port)
    if arguments.shutdown:
        return _request_shutdown(data_dir)
    try:
        return _run_server(data_dir, frontend_dist, open_browser=not arguments.no_browser, port=arguments.port)
    except Exception as exc:
        log_path = data_dir / "logs" / "aurora.log"
        print(f"Aurora could not start: {exc}\nSee log: {log_path}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
