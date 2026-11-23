"""Desktop bundles use writable AppData paths and packaged static assets."""
from app.core.runtime_paths import app_data_dir, find_frontend_dist
from desktop_launcher import _user_data_root


def test_app_data_directory_defaults_to_source_data(tmp_path, monkeypatch):
    monkeypatch.delenv("AURORA_DATA_DIR", raising=False)
    assert app_data_dir(tmp_path / "backend" / "data") == (tmp_path / "backend" / "data").resolve()


def test_app_data_directory_uses_packaged_user_location(tmp_path, monkeypatch):
    configured = tmp_path / "LocalAppData" / "Aurora"
    monkeypatch.setenv("AURORA_DATA_DIR", str(configured))
    assert app_data_dir(tmp_path / "backend" / "data") == configured.resolve()


def test_launcher_data_directory_override_is_resolved(tmp_path):
    configured = tmp_path / "isolated" / "Aurora"
    assert _user_data_root(str(configured)) == configured.resolve()


def test_frontend_bundle_path_prefers_explicit_bundle_root(tmp_path, monkeypatch):
    monkeypatch.delenv("AURORA_FRONTEND_DIST", raising=False)
    bundled = tmp_path / "bundle" / "frontend" / "dist"
    bundled.mkdir(parents=True)
    (bundled / "index.html").write_text("<html></html>", encoding="utf-8")
    source = tmp_path / "source"
    source.mkdir()
    assert find_frontend_dist(source, tmp_path / "bundle") == bundled.resolve()


def test_frontend_dist_is_none_when_no_index_exists(tmp_path, monkeypatch):
    monkeypatch.delenv("AURORA_FRONTEND_DIST", raising=False)
    assert find_frontend_dist(tmp_path / "empty-source", tmp_path / "empty-bundle") is None
