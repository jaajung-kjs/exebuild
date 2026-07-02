import os
from app.adapters import config


def test_get_base_dir_is_repo_root_in_script_mode():
    # 스크립트 모드에서는 저장소 루트를 가리켜야 함 (app/adapters/config.py 기준 2단계 상위)
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    assert os.path.normpath(config.get_base_dir()) == os.path.normpath(repo_root)
