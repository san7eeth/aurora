# PyInstaller one-file build for Windows x64. Run from the repository root.
from pathlib import Path
from PyInstaller.utils.hooks import collect_all

project_root = Path(SPECPATH).resolve().parents[1]
backend_root = project_root / "backend"
frontend_dist = project_root / "frontend" / "dist"
icon_path = project_root / "packaging" / "assets" / "aurora.ico"

if not (frontend_dist / "index.html").is_file():
    raise SystemExit("Frontend build missing. Run npm run build in frontend/ first.")

datas = [(str(frontend_dist), "frontend/dist")]
binaries = []
hiddenimports = ["pythoncom", "pywintypes", "win32timezone", "win32com.client"]

# These libraries use native extensions and runtime imports that PyInstaller's
# normal static analysis cannot reliably discover.
for package in (
    "fastapi",
    "uvicorn",
    "sqlalchemy",
    "aiosqlite",
    "multipart",
    "pydantic_settings",
    "sentence_transformers",
    "transformers",
    "torch",
    "faiss",
    "faster_whisper",
    "ctranslate2",
    "av",
    "pyttsx3",
    "pydub",
    "pypdf",
    "docx",
    "webrtcvad",
):
    package_datas, package_binaries, package_hiddenimports = collect_all(package)
    datas += package_datas
    binaries += package_binaries
    hiddenimports += package_hiddenimports

a = Analysis(
    [str(backend_root / "desktop_launcher.py")],
    pathex=[str(backend_root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "IPython", "notebook", "jupyter"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="Aurora",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    icon=str(icon_path),
)
