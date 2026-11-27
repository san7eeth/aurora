"""ONEDIR Windows packaging; PyInstaller 6 keeps collected files in runtime."""
from pathlib import Path
from PyInstaller.utils.hooks import collect_all

root = Path(SPECPATH).resolve().parents[1]
backend = root / "backend"
frontend = root / "frontend" / "dist"
config_template = root / "packaging" / "portable" / "resources" / "aurora.env.example"
icon = root / "packaging" / "assets" / "aurora.ico"
if not (frontend / "index.html").is_file():
    raise SystemExit("Build frontend/dist before packaging")
if not config_template.is_file():
    raise SystemExit("Portable configuration template is missing")

datas = [(str(config_template), "resources/aurora.env.example")]
binaries, hiddenimports = [], [
    # Static and dynamic runtime imports discovered by Analysis.
    # Torch autograd imports this module during normal model initialization.
    "faiss", "faiss.swigfaiss", "pythoncom", "pywintypes", "win32timezone", "torch.testing",
]
optional_excludes = (
    "einops",
    "tensorboard",
    "tensorflow",
    "torch.utils.tensorboard",
    "transformers.kernels.falcon_mamba",
)


def _is_optional_transformers_module(module):
    if not module.startswith("transformers."):
        return False
    name = module.rsplit(".", 1)[-1]
    return (
        name.startswith(("modeling_tf_", "tf_"))
        or name.endswith("_tf")
        or "_tf_" in name
        or module == "transformers.keras_callbacks"
    )


def _is_excluded_module(module):
    return any(
        module == excluded or module.startswith(excluded + ".")
        for excluded in optional_excludes
    )


for package in ("fastapi", "uvicorn", "sqlalchemy", "aiosqlite", "multipart", "pydantic_settings",
                "sentence_transformers", "transformers", "torch", "faiss", "faster_whisper", "ctranslate2",
                "av", "pyttsx3", "pydub", "pypdf", "docx"):
    package_data, package_bins, package_imports = collect_all(package)
    datas += package_data
    binaries += package_bins
    hiddenimports += package_imports

# Source files are compiled into PyInstaller's PYZ archive by Analysis. Do not
# duplicate vendor Python sources, bytecode caches, or test trees as data files.
datas = [
    (source, destination)
    for source, destination in datas
    if Path(source).suffix.lower() not in {".py", ".pyc", ".pyo"}
    and not any(part.lower() in {"tests", "test", "__pycache__"} for part in Path(source).parts)
]
hiddenimports = sorted({
    module for module in hiddenimports
    if not any(part.lower() in {"tests", "test"} for part in module.split("."))
    and not _is_excluded_module(module)
    and not _is_optional_transformers_module(module)
})

a = Analysis([str(backend / "desktop_launcher.py")], pathex=[str(backend)], binaries=binaries, datas=datas,
             hiddenimports=hiddenimports,
             excludes=[
                 "pytest", "_pytest", "IPython", "notebook", "jupyter", "pip", "setuptools",
                          *optional_excludes,
             ],
             module_collection_mode={"torch": "pyz", "transformers": "pyz"})

# The PyInstaller Torch hook opts into source-on-disk collection. Keep runtime
# modules in PYZ while dropping package source, type stubs, caches, and tests.
def _runtime_data(entry):
    destination, source, *_ = entry
    suffix = Path(destination).suffix.lower()
    parts = {part.lower() for part in Path(destination).parts}
    return suffix not in {".py", ".pyc", ".pyo", ".pyi", ".pyx", ".pxd"} and not parts.intersection(
        {"tests", "test", "testing", "__pycache__"}
    )

a.datas = [entry for entry in a.datas if _runtime_data(entry)]
a.binaries = [entry for entry in a.binaries if _runtime_data(entry)]
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="Aurora", console=False, icon=str(icon),
          contents_directory="runtime")
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="Aurora")
