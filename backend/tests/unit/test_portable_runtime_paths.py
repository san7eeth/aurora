from app.core.runtime_paths import migrate_legacy_portable_data, portable_data_paths


def test_portable_layout_and_legacy_migration_preserves_existing_files(tmp_path):
    (tmp_path / "aurora.db").write_bytes(b"old-db")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "guide.txt").write_text("legacy", encoding="utf-8")
    paths = portable_data_paths(tmp_path)
    paths.database.mkdir()
    (paths.database / "aurora.db").write_bytes(b"newer-db")

    migrated = migrate_legacy_portable_data(tmp_path)

    assert migrated.root == tmp_path.resolve()
    assert (paths.database / "aurora.db").read_bytes() == b"newer-db"
    assert (paths.documents / "guide.txt").read_text(encoding="utf-8") == "legacy"
    for name in ("config", "database", "conversations", "faiss_index", "documents", "logs", "backups"):
        assert (tmp_path / name).is_dir()
