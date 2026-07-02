import app.app_paths as ap


def test_output_dir_is_base(monkeypatch, tmp_path):
    monkeypatch.setattr(ap.config, "get_base_dir", lambda: str(tmp_path))
    assert ap.output_dir() == tmp_path
