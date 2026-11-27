import json
import inspect
import os
from pathlib import Path
import subprocess
import sys
from types import ModuleType
from urllib.error import URLError

import pytest


PORTABLE_DIR = Path(__file__).resolve().parents[3] / "packaging" / "portable"
BACKEND_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(PORTABLE_DIR))
import desktop_launcher  # noqa: E402
import start_aurora  # noqa: E402


def test_launcher_reads_configured_model_from_user_data(monkeypatch, tmp_path):
    config = tmp_path / "Aurora" / "config"
    config.mkdir(parents=True)
    (config / "aurora.env").write_text("OLLAMA_MODEL=local-model:latest\n", encoding="utf-8")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))

    assert start_aurora._configured_model() == "local-model:latest"


def test_launcher_rejects_an_empty_model_setting(monkeypatch, tmp_path):
    config = tmp_path / "Aurora" / "config"
    config.mkdir(parents=True)
    (config / "aurora.env").write_text("OLLAMA_MODEL=\n", encoding="utf-8")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))

    with pytest.raises(ValueError, match="OLLAMA_MODEL is empty"):
        start_aurora._configured_model()


def test_launcher_explains_how_to_install_missing_ollama(monkeypatch):
    def unavailable(_url, timeout):
        assert timeout == 2
        raise URLError("connection refused")

    monkeypatch.setattr(start_aurora, "urlopen", unavailable)

    message = start_aurora._ollama_status("llama3.2:3b")

    assert "Ollama is not responding" in message
    assert "ollama run llama3.2:3b" in message


def test_launcher_identifies_a_missing_local_model(monkeypatch):
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return json.dumps({"models": [{"name": "another-model"}]}).encode()

    monkeypatch.setattr(start_aurora, "urlopen", lambda *_args, **_kwargs: Response())

    message = start_aurora._ollama_status("llama3.2:3b")

    assert "model 'llama3.2:3b' is not installed" in message
    assert "ollama run llama3.2:3b" in message


def test_process_detection_handles_current_and_nonexistent_processes():
    assert desktop_launcher._is_running(os.getpid())
    assert not desktop_launcher._is_running(2**31 - 1)


def test_runtime_configures_database_path_before_settings_import(tmp_path):
    script = """
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[2])
from desktop_launcher import _configure_runtime
_configure_runtime(sys.argv[1])
from app.database.engine import DB_PATH
expected = (Path(sys.argv[1]) / "database" / "aurora.db").resolve()
assert DB_PATH == expected, f"{DB_PATH} != {expected}"
"""
    subprocess.run(
        [sys.executable, "-c", script, str(tmp_path), str(BACKEND_DIR)],
        check=True,
        capture_output=True,
        text=True,
    )


def test_runtime_does_not_enable_duplicate_openmp_workaround(tmp_path):
    script = """
import os
import sys
sys.path.insert(0, sys.argv[2])
os.environ.pop("KMP_DUPLICATE_LIB_OK", None)
from desktop_launcher import _configure_runtime
_configure_runtime(sys.argv[1])
assert "KMP_DUPLICATE_LIB_OK" not in os.environ
"""
    subprocess.run(
        [sys.executable, "-c", script, str(tmp_path), str(BACKEND_DIR)],
        check=True,
        capture_output=True,
        text=True,
    )


def test_frozen_torch_config_source_fallback_is_narrow(monkeypatch):
    original_getsource = inspect.getsource
    try:
        monkeypatch.setattr(desktop_launcher.sys, "frozen", True, raising=False)
        desktop_launcher._install_torch_config_source_fallback()
        torch_configs = (
            ModuleType("torch.distributed.config"),
            ModuleType("torch.fx.experimental._config"),
        )
        for torch_config in torch_configs:
            torch_config.__file__ = "missing-torch-config.py"
        app_config = ModuleType("aurora.config")
        app_config.__file__ = "missing-aurora-config.py"
        torch_module = ModuleType("torch.fx.experimental")
        torch_module.__file__ = "missing-torch-module.py"

        assert all(inspect.getsource(module) == "" for module in torch_configs)
        with pytest.raises(OSError):
            inspect.getsource(app_config)
        with pytest.raises(OSError):
            inspect.getsource(torch_module)
    finally:
        inspect.getsource = original_getsource


def test_frozen_transformers_import_uses_loaded_package_without_source(
    monkeypatch, tmp_path
):
    transformers = ModuleType("transformers")
    transformers.__file__ = str(tmp_path / "transformers" / "__init__.py")
    transformers.__path__ = [str(tmp_path / "transformers")]
    transformers_utils = ModuleType("transformers.utils")
    import_utils = ModuleType("transformers.utils.import_utils")
    calls = []

    def original_import(path, file="__init__.py"):
        calls.append((path, file))
        return "source-import"

    transformers_utils.direct_transformers_import = original_import
    import_utils.direct_transformers_import = original_import
    monkeypatch.setitem(sys.modules, "transformers", transformers)
    monkeypatch.setitem(sys.modules, "transformers.utils", transformers_utils)
    monkeypatch.setitem(sys.modules, "transformers.utils.import_utils", import_utils)
    monkeypatch.setattr(desktop_launcher.sys, "frozen", True, raising=False)

    desktop_launcher._install_transformers_frozen_import_fallback()

    package_dir = str(Path(transformers.__file__).parent)
    assert transformers_utils.direct_transformers_import(package_dir) is transformers
    assert import_utils.direct_transformers_import(package_dir) is transformers
    assert transformers_utils.direct_transformers_import("C:/unrelated") == "source-import"
    assert calls == [("C:/unrelated", "__init__.py")]
