"""Nuitka project entry point for a standalone Windows build."""

# nuitka-project: --mode=standalone
# nuitka-project: --windows-console-mode=disable
# nuitka-project: --include-package=app
# nuitka-project: --include-package-data=fastapi
# nuitka-project: --include-package-data=uvicorn
# nuitka-project: --include-package-data=faiss
# nuitka-project: --include-package-data=sentence_transformers
# nuitka-project: --include-package-data=transformers
# nuitka-project: --include-package-data=faster_whisper
# nuitka-project: --include-data-dir=frontend/dist=frontend/dist
# nuitka-project: --include-data-file=packaging/portable/resources/aurora.env.example=resources/aurora.env.example

import sys
from pathlib import Path

repository = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repository / "backend"))
from desktop_launcher import main


if __name__ == "__main__":
    raise SystemExit(main())
