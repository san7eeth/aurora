"""Resolve writable user data and read-only frontend assets."""

import os
from pathlib import Path


def app_data_dir(default_directory: Path) -> Path:
    """Use a per-user data location in packaged builds, source data otherwise."""
    configured = os.environ.get("AURORA_DATA_DIR")
    return Path(configured).expanduser().resolve() if configured else default_directory.resolve()


def find_frontend_dist(source_root: Path, bundle_root: Path | None = None) -> Path | None:
    """Find the production frontend in a PyInstaller bundle or source checkout."""
    configured = os.environ.get("AURORA_FRONTEND_DIST")
    candidates = [Path(configured).expanduser()] if configured else []
    if bundle_root:
        candidates.append(bundle_root / "frontend" / "dist")
    candidates.append(source_root / "frontend" / "dist")
    for candidate in candidates:
        resolved = candidate.resolve()
        if (resolved / "index.html").is_file():
            return resolved
    return None
