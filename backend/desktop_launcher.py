"""PyInstaller entry point for the local Windows app bundle."""

import argparse
import ctypes
import os
from pathlib import Path
import sys
import threading
import time
import webbrowser
from types import ModuleType

def _resource_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parents[1]


def _install_torch_config_source_fallback() -> None:
    if not getattr(sys, "frozen", False):
        return

    import inspect

    original_getsource = inspect.getsource

    def getsource(obj):
        try:
            return original_getsource(obj)
        except OSError:
            name = getattr(obj, "__name__", "")
            if (
                isinstance(obj, ModuleType)
                and name.startswith("torch.")
                and name.endswith((".config", "._config"))
            ):
                return ""
            raise

    inspect.getsource = getsource


def _install_transformers_frozen_import_fallback() -> None:
    if not getattr(sys, "frozen", False):
        return

    import transformers
    import transformers.utils as transformers_utils
    import transformers.utils.import_utils as import_utils

    original_import = import_utils.direct_transformers_import
    package_dir = Path(transformers.__file__).resolve().parent

    def direct_transformers_import(path, file="__init__.py"):
        if file == "__init__.py" and Path(path).resolve() == package_dir:
            return transformers
        return original_import(path, file)

    import_utils.direct_transformers_import = direct_transformers_import
    transformers_utils.direct_transformers_import = direct_transformers_import


def _user_data_root(override: str | None = None) -> Path:
    configured = override or os.environ.get("AURORA_DATA_DIR")
    if configured:
        return Path(configured).expanduser().resolve()
    local_app_data = os.environ.get("LOCALAPPDATA")
    base = Path(local_app_data) if local_app_data else Path.home() / "AppData" / "Local"
    return base / "Aurora"


def _configure_runtime(data_directory: str | None = None, port: int = 8000) -> tuple[Path, Path, Path]:
    data_dir = _user_data_root(data_directory)
    config_dir = data_dir / "config"
    database_dir = data_dir / "database"
    conversations_dir = data_dir / "conversations"
    faiss_index_dir = data_dir / "faiss_index"
    documents_dir = data_dir / "documents"
    log_dir = data_dir / "logs"
    backups_dir = data_dir / "backups"
    for directory in (
        data_dir,
        config_dir,
        database_dir,
        conversations_dir,
        faiss_index_dir,
        documents_dir,
        log_dir,
        backups_dir,
    ):
        directory.mkdir(parents=True, exist_ok=True)
    model_cache = data_dir / "models" / "huggingface"
    model_cache.mkdir(parents=True, exist_ok=True)
    os.environ["AURORA_DATA_DIR"] = str(data_dir)
    version_file = Path(sys.executable).resolve().parent / "VERSION"
    if version_file.is_file():
        os.environ["AURORA_VERSION"] = version_file.read_text(encoding="utf-8").strip()
    portable_frontend = (
        Path(sys.executable).resolve().parent / "frontend" / "dist"
    )
    bundled_frontend = _resource_root() / "frontend" / "dist"
    frontend_dist = (
        portable_frontend
        if (portable_frontend / "index.html").is_file()
        else bundled_frontend
    )
    os.environ["AURORA_FRONTEND_DIST"] = str(frontend_dist)
    os.environ["AURORA_LOG_FILE"] = str(log_dir / "aurora.log")
    os.environ["AURORA_CONFIG_FILE"] = str(config_dir / "aurora.env")
    config_file = config_dir / "aurora.env"
    if not config_file.exists():
        resource_config = Path(sys.executable).resolve().parent
        resource_config = resource_config / "resources" / "aurora.env.example"
        if not resource_config.is_file():
            resource_config = _resource_root() / "resources"
            resource_config = resource_config / "aurora.env.example"
        if resource_config.is_file():
            config_file.write_bytes(resource_config.read_bytes())
    os.environ["AURORA_DATABASE_PATH"] = str(database_dir / "aurora.db")
    os.environ["AURORA_DOCUMENTS_DIR"] = str(documents_dir)
    os.environ["AURORA_FAISS_DIR"] = str(faiss_index_dir)
    os.environ.setdefault("HF_HOME", str(model_cache))
    database_path = (database_dir / "aurora.db").resolve().as_posix()
    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{database_path}"
    os.environ["BACKEND_HOST"] = "127.0.0.1"
    os.environ["BACKEND_PORT"] = str(port)
    os.environ.setdefault("LOG_LEVEL", "INFO")
    os.environ.setdefault("LOG_JSON", "true")
    return data_dir, log_dir, frontend_dist


def _read_pid(pid_path: Path) -> int | None:
    try:
        return int(pid_path.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return None


def _is_running(pid: int | None) -> bool:
    if not pid:
        return False
    if os.name == "nt":
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
        kernel32.OpenProcess.restype = wintypes.HANDLE
        kernel32.WaitForSingleObject.argtypes = (wintypes.HANDLE, wintypes.DWORD)
        kernel32.WaitForSingleObject.restype = wintypes.DWORD
        kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
        kernel32.CloseHandle.restype = wintypes.BOOL
        handle = kernel32.OpenProcess(0x00100000, False, pid)
        if not handle:
            return False
        try:
            return kernel32.WaitForSingleObject(handle, 0) == 0x00000102
        finally:
            kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
        return True
    except PermissionError:
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
    from app.core.runtime_paths import migrate_legacy_portable_data

    pid_path = data_dir / "aurora.pid"
    stop_path = data_dir / "stop.request"
    existing_pid = _read_pid(pid_path)
    if _is_running(existing_pid):
        if open_browser:
            webbrowser.open(f"http://127.0.0.1:{port}/")
        return 0
    pid_path.unlink(missing_ok=True)
    stop_path.unlink(missing_ok=True)
    migrate_legacy_portable_data(data_dir)

    if not (frontend_dist / "index.html").is_file():
        raise FileNotFoundError(f"Built frontend not found: {frontend_dist}")

    backend_root = _resource_root() / "backend"
    if str(backend_root) not in sys.path:
        sys.path.insert(0, str(backend_root))

    _install_torch_config_source_fallback()
    _install_transformers_frozen_import_fallback()
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
    parser.add_argument(
        "--self-check",
        action="store_true",
        help="verify bundled application imports and resources",
    )
    arguments = parser.parse_args()

    data_dir, log_dir, frontend_dist = _configure_runtime(
        arguments.data_dir, arguments.port
    )
    if arguments.shutdown:
        return _request_shutdown(data_dir)
    if arguments.self_check:
        try:
            if not (frontend_dist / "index.html").is_file():
                raise FileNotFoundError(
                    f"Built frontend not found: {frontend_dist}"
                )
            _install_torch_config_source_fallback()
            _install_transformers_frozen_import_fallback()
            import faiss
            import numpy as np
            import sentence_transformers
            from app.api import app

            if not hasattr(sentence_transformers, "SentenceTransformer"):
                raise RuntimeError("SentenceTransformer is unavailable.")
            if not app.routes:
                raise RuntimeError("FastAPI has no routes loaded.")
            test_index = faiss.IndexFlatL2(2)
            test_index.add(np.asarray([[0.0, 0.0]], dtype=np.float32))
            query = np.asarray([[0.0, 0.0]], dtype=np.float32)
            _distances, neighbors = test_index.search(query, 1)
            if neighbors.tolist() != [[0]]:
                raise RuntimeError("FAISS native index smoke check failed.")
            return 0
        except Exception as exc:
            message = (
                f"Aurora self-check failed: {type(exc).__name__}: {exc}"
            )
            try:
                with (log_dir / "self-check.log").open(
                    "a", encoding="utf-8"
                ) as error_log:
                    error_log.write(message + "\n")
            except OSError:
                pass
            print(message, file=sys.stderr)
            return 1
    try:
        return _run_server(data_dir, frontend_dist, open_browser=not arguments.no_browser, port=arguments.port)
    except Exception as exc:
        log_path = data_dir / "logs" / "aurora.log"
        print(f"Aurora could not start: {exc}\nSee log: {log_path}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
