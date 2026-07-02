from app.core.mail_config import preset_to_mail_config
from app.core.settings import Preset


def test_preset_to_mail_config_maps_fields():
    p = Preset(name="t", department_code="4200",
               mail_from_name="홍길동", mail_from_email="hong@kepco.co.kr",
               mail_recipients=["a@kepco.co.kr", "b@kepco.co.kr"],
               mail_subject="{DATE} 리스트", mail_body="본문 {DATE}")
    mc = preset_to_mail_config(p)
    assert mc == {
        "from_name": "홍길동",
        "from_email": "hong@kepco.co.kr",
        "recipients": ["a@kepco.co.kr", "b@kepco.co.kr"],
        "subject": "{DATE} 리스트",
        "body": "본문 {DATE}",
    }
    # 원본 리스트와 분리(복사)되어야 함
    mc["recipients"].append("x")
    assert p.mail_recipients == ["a@kepco.co.kr", "b@kepco.co.kr"]
