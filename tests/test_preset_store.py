from app.core import preset_store as ps
from app.core.settings import Preset, Rule


def test_save_and_load(tmp_path):
    p = Preset(name="강원본부 기본", department_code="4200",
               rules=[Rule(column="공사명", keyword="활선", priority=1, color="#FFFF00")])
    path = ps.save_preset(p, tmp_path)
    assert path.exists()
    loaded = ps.load_preset("강원본부 기본", tmp_path)
    assert loaded == p


def test_list_presets_sorted(tmp_path):
    ps.save_preset(Preset(name="나본부", department_code="1"), tmp_path)
    ps.save_preset(Preset(name="가본부", department_code="2"), tmp_path)
    assert ps.list_presets(tmp_path) == ["가본부", "나본부"]


def test_delete_preset(tmp_path):
    ps.save_preset(Preset(name="삭제대상", department_code="1"), tmp_path)
    ps.delete_preset("삭제대상", tmp_path)
    assert ps.list_presets(tmp_path) == []


def test_list_presets_empty_dir(tmp_path):
    assert ps.list_presets(tmp_path) == []
