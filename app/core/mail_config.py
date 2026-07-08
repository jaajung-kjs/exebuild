"""Preset의 메일 필드를 mailer.send_mail이 받는 dict로 변환 (순수)"""

from app.core.settings import Preset


def preset_to_mail_config(preset: Preset) -> dict:
    return {
        "from_name": preset.mail_from_name,
        "from_email": preset.mail_from_email,
        "recipients": list(preset.mail_recipients),
        "subject": preset.mail_subject,
        "body": preset.mail_body,
    }
