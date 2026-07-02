from pathlib import Path
import app.app_paths as ap


def test_presets_dir_created_under_base(monkeypatch, tmp_path):
    monkeypatch.setattr(ap.config, "get_base_dir", lambda: str(tmp_path))
    d = ap.presets_dir()
    assert d == tmp_path / "presets"
    assert d.exists()


def test_output_dir_is_base(monkeypatch, tmp_path):
    monkeypatch.setattr(ap.config, "get_base_dir", lambda: str(tmp_path))
    assert ap.output_dir() == tmp_path
