"""Resolve writable user data and read-only frontend assets."""

from dataclasses import dataclass
import os
import shutil
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


@dataclass(frozen=True)
class PortableDataPaths:
    root: Path
    config: Path
    database: Path
    conversations: Path
    faiss_index: Path
    documents: Path
    logs: Path
    backups: Path


def portable_data_paths(root: Path) -> PortableDataPaths:
    """Return the stable per-user layout used by portable Windows builds."""
    root = root.expanduser().resolve()
    return PortableDataPaths(
        root=root,
        config=root / "config",
        database=root / "database",
        conversations=root / "conversations",
        faiss_index=root / "faiss_index",
        documents=root / "documents",
        logs=root / "logs",
        backups=root / "backups",
    )


def _copy_missing(source: str, destination: str) -> str:
    """Copy old files without overwriting files in the new layout."""
    if not Path(destination).exists():
        shutil.copy2(source, destination)
    return destination


def migrate_legacy_portable_data(root: Path) -> PortableDataPaths:
    """Migrate old portable data while preserving files in the new layout."""
    paths = portable_data_paths(root)
    for directory in (
        paths.config,
        paths.database,
        paths.conversations,
        paths.faiss_index,
        paths.documents,
        paths.logs,
        paths.backups,
    ):
        directory.mkdir(parents=True, exist_ok=True)

    legacy_database = paths.root / "aurora.db"
    target_database = paths.database / "aurora.db"
    if legacy_database.is_file() and not target_database.exists():
        shutil.copy2(legacy_database, target_database)
        for suffix in ("-wal", "-shm"):
            legacy_sidecar = Path(f"{legacy_database}{suffix}")
            if legacy_sidecar.is_file():
                target_sidecar = Path(f"{target_database}{suffix}")
                shutil.copy2(legacy_sidecar, target_sidecar)

    for legacy_name, destination in (
        ("docs", paths.documents),
        ("vectorstore", paths.faiss_index),
    ):
        legacy_directory = paths.root / legacy_name
        if legacy_directory.is_dir():
            shutil.copytree(
                legacy_directory,
                destination,
                dirs_exist_ok=True,
                copy_function=_copy_missing,
            )
    return paths
