"""
KEPCO 웹메일(mail.kepco.co.kr) 발송 모듈 — 로그인된 SSO 세션 기준.
메일 설정(발신·수신·제목·본문)은 UI에서 편집한 값을 dict로 받아 발송한다.
요청 구조는 브라우저 HAR(session/check → uploadFile → receiverCheck → send)과 동일.
발신자(fromaddr/fromname)는 서버가 반드시 요구하는 값이라 mail_config로 받아 그대로 전송한다.
"""

import requests
import os
from datetime import datetime, timedelta
import uuid
from app.adapters.config import MAIL_URL, HTTP_TIMEOUT


def generate_temp_key():
    """Generate temporary key for mail tracking (24 chars)"""
    return uuid.uuid4().hex[:24]


def upload_files(session, file_paths):
    """
    Upload file attachments

    Args:
        session (requests.Session): Authenticated session
        file_paths (list): List of file paths to upload

    Returns:
        list: Uploaded file info [{'filekey', 'filename', 'size'}, ...]
    """
    uploaded_files = []

    if not file_paths:
        return uploaded_files

    print(f"\n  파일 업로드 중... ({len(file_paths)}개)")

    for filepath in file_paths:
        if not os.path.exists(filepath):
            print(f"    [경고] 파일 없음: {filepath}")
            continue

        filename = os.path.basename(filepath)
        filesize = os.path.getsize(filepath)

        # Internal filename (plupload format)
        internal_name = f"o_{uuid.uuid4().hex[:24]}{os.path.splitext(filename)[1]}"

        try:
            with open(filepath, 'rb') as f:
                files = {
                    'file': (filename, f, 'application/octet-stream')
                }
                data = {
                    'name': internal_name,
                    'chunk': '0',
                    'chunks': '1',
                    'filename': filename
                }

                resp = session.post(
                    f'{MAIL_URL}/mail/json/uploadFile.do?_csrf=',
                    files=files,
                    data=data,
                    timeout=HTTP_TIMEOUT
                )

                result = resp.json()

                if result.get('result') == 1 and 'filekey' in result:
                    filekey = result['filekey'][0]
                    uploaded_files.append({
                        'filekey': filekey,
                        'filename': filename,
                        'size': filesize
                    })
                    print(f"    [완료] {filename}")
                else:
                    print(f"    [실패] {filename}: {result}")

        except Exception as e:
            print(f"    [오류] {filename}: {e}")

    print(f"  업로드 완료: {len(uploaded_files)}개\n")
    return uploaded_files


def send_mail(session, mail_config, attachment_paths=None, date_yymmdd=None, date_yy_mm_dd=None):
    """
    KEPCO 웹메일(mail.kepco.co.kr)로 메일 발송

    Args:
        session (requests.Session): Authenticated session
        mail_config (dict): UI에서 편집한 메일 설정
            {
                'from_name': str,
                'from_email': str,
                'recipients': [str, ...],
                'subject': str,
                'body': str
            }
        attachment_paths (list): Optional list of file paths to attach
        date_yymmdd (str): Date in YYMMDD format for subject (default: tomorrow)
        date_yy_mm_dd (str): Date in 'YY-MM-DD format for body (default: tomorrow)

    Returns:
        dict: {'success': bool, 'message': str, 'response': dict}
    """
    print("=" * 60)
    print("메일 전송")
    print("=" * 60)

    # 발신자는 서버가 반드시 요구하는 값(빈 값이면 수신자 검증에서 권한 없음으로 실패).
    if not (mail_config.get('from_email') or "").strip():
        print("  [실패] 발신 이메일이 비어 있음 (③메일 설정에서 발신 이메일을 입력하세요)")
        return {"success": False, "message": "발신 이메일이 설정되지 않았습니다. ③메일 설정에서 발신 이메일을 입력하세요."}

    # 검증된 발송 스크립트의 헤더를 그대로 사용 (동작 확인된 헤더)
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Origin': MAIL_URL,
        'Referer': f'{MAIL_URL}/mail/list.do',
        'X-Requested-With': 'XMLHttpRequest',
    })

    try:
        # Use provided dates or fallback to tomorrow
        if date_yymmdd is None:
            tomorrow = datetime.now() + timedelta(days=1)
            date_yymmdd = tomorrow.strftime('%y%m%d')  # 251120 format
        if date_yy_mm_dd is None:
            tomorrow = datetime.now() + timedelta(days=1)
            date_yy_mm_dd = tomorrow.strftime("'%y-%m-%d")  # '25-11-20 format
        # Step 1: Session validation
        print(f"\n  세션 확인 중...")
        timestamp = int(datetime.now().timestamp() * 1000)
        session_url = f"{MAIL_URL}/common/json/session/check.do?_={timestamp}"

        session_resp = session.get(session_url, timeout=HTTP_TIMEOUT)
        session_data = session_resp.json()

        if not session_data.get('alive'):
            print("  [실패] 세션 만료")
            return {"success": False, "message": "세션 만료"}

        print("  세션 정상")

        # Step 2: File upload
        uploaded_files = upload_files(session, attachment_paths or [])

        # Prepare attachment parameters
        attach_size = sum(f['size'] for f in uploaded_files)
        attach_list = ':'.join([f"{f['filename']}:{f['size']}:1:0" for f in uploaded_files])
        attachments_param = ':'.join([f"{f['filekey']}:0:1:0" for f in uploaded_files])

        # Step 3: Receiver validation
        print(f"  수신자 검증 중...")

        # Inject tomorrow's date into subject and body
        subject = mail_config['subject'].replace('{DATE}', date_yymmdd)
        body_text = mail_config['body'].replace('{DATE}', date_yy_mm_dd)

        # Convert body to HTML format if not already
        # (UI 리치텍스트는 <!DOCTYPE ...><html>… 형태이므로 이미 html이면 그대로 사용)
        body_html = body_text
        if '<html' not in body_html.lower():
            body_html = f"""<html><head><style type="text/css">
p {{padding:0;margin:0;}}
</style>
</head><body><div class="sensEdContentAreaCls" data-id="sensEdContentArea" style="color:#000;line-height:150%;font-size:12pt;font-family:돋움 !important;padding:0;margin:0;">
{body_html}
</div></body></html>"""

        # Build receiver_data with multiple 'to' parameters
        receiver_data = [
            ('subject', subject),
            ('subjecthead', '-1'),
            ('content', body_html),
            ('fromname', mail_config['from_name']),
            ('fromaddr', mail_config['from_email']),
            ('attach_size', str(attach_size)),
            ('attach_list', attach_list),
        ]

        # Add each recipient as separate 'to' parameter
        for recipient in mail_config['recipients']:
            receiver_data.append(('to', recipient))

        receiver_resp = session.post(
            f"{MAIL_URL}/mail/json/receiverCheck.do",
            data=receiver_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'},
            timeout=HTTP_TIMEOUT
        )

        receiver_result = receiver_resp.json()
        print(f"    수신자: {receiver_result.get('receiver_count', 0)}명")

        if not receiver_result.get('permission'):
            print("  [실패] 발송 권한 없음")
            return {"success": False, "message": "발송 권한 없음"}

        # Step 4: Send email
        print(f"\n  메일 발송 중...")

        # Generate temporary key
        temp_key = generate_temp_key()
        current_date = datetime.now().strftime("%Y-%m-%d")

        # Build send_data with multiple 'to' parameters (list of tuples)
        send_data = [
            # Basic info
            ('fromaddr', mail_config['from_email']),
            ('fromname', mail_config['from_name']),
            ('subject', subject),
            ('subjecthead', '-1'),
            ('body', body_html),

            # Recipients flags
            ('_tome', 'on'),
            ('_is_report', 'on'),

            # Temporary key
            ('tempKey', temp_key),
            ('ukey', ''),
            ('first', '0'),
            ('tempsave', '0'),

            # Attachments
            ('attachments', attachments_param),

            # Reservation & approval
            ('reserverTime', ''),
            ('req_reserverTime', ''),
            ('mail_cancel_time', '0'),
            ('approval_flag', '0'),
            ('isPermissionMail', ''),
            ('reserveEndTime', ''),
            ('repeat_type', ''),
            ('repeat_cycle', '0'),
            ('repeat_dayofweek', ''),
            ('repeat_mailkey', ''),
            ('myTemplateKey', ''),

            # Link attachment
            ('islinkattach', '0'),
            ('use_bigfile_password', '0'),
            ('linkattach_filesize', ''),
            ('linkattach_downterm', ''),
            ('temp_save_bigfile', '1'),

            # Approval
            ('approvalkey', ''),
            ('ap_send_type', '0'),
            ('approver', ''),

            # Options
            ('_is_each', 'on'),
            ('_important', 'on'),
            ('_use_sign', 'on'),
            ('sign', 'mail_sign'),

            # Reservation time
            ('reserveTime', current_date),
            ('c_reserveTime', current_date),
            ('hour_c', '23'),
            ('minute_c', '50'),

            # Editor
            ('editor_type', '1'),
            ('characterset', 'utf-8'),

            # Security & receipt
            ('_is_secure', 'on'),
            ('is_receipt', '1'),
            ('_is_receipt', 'on'),

            # Save to sent mail (important!)
            ('is_save', '1'),
            ('_is_save', 'on'),

            # Notifications & SMS
            ('_alarm', 'on'),
            ('_sms', 'on'),

            # Reply request
            ('replyRequestTime', current_date),
            ('hour_r', '23'),
            ('minute_r', '50'),

            # Approval report
            ('apUser', ''),
            ('apUserText', ''),
            ('_apReport', 'on'),

            # Edit
            ('editHtml', ''),
            ('editText', ''),
            ('divText', ''),
        ]

        # Add each recipient as separate 'to' parameter (CRITICAL for multiple recipients!)
        for recipient in mail_config['recipients']:
            send_data.append(('to', recipient))

        print(f"    발신: {mail_config['from_name']} <{mail_config['from_email']}>")
        print(f"    수신: {len(mail_config['recipients'])}명")
        for rcpt in mail_config['recipients']:
            print(f"      - {rcpt}")
        print(f"    제목: {subject}")
        print(f"    첨부: {len(uploaded_files)}개")

        # Send!
        send_resp = session.post(
            f"{MAIL_URL}/mail/json/send.do",
            data=send_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'},
            timeout=HTTP_TIMEOUT
        )

        send_result = send_resp.json()

        if send_result.get('code') == 1:
            print(f"\n  [성공] 메일 발송 완료!")
            print(f"    발송 키: {send_result.get('sent_mail_key', 'N/A')}")
            print(f"    저장 키: {send_result.get('save_mail_key', 'N/A')}")
            print("=" * 60 + "\n")
            return {"success": True, "message": "발송 완료", "response": send_result}
        else:
            reason = send_result.get('send_result_txt') or send_result.get('send_result_txt_desc') or "발송 실패"
            print(f"\n  [실패] {reason}")
            print(f"    응답: {send_result}")
            print("=" * 60 + "\n")
            return {"success": False, "message": str(reason), "response": send_result}

    except requests.exceptions.Timeout:
        print(f"\n  [실패] 타임아웃 ({HTTP_TIMEOUT}초 초과)")
        return {"success": False, "message": "타임아웃"}

    except requests.exceptions.RequestException as e:
        print(f"\n  [실패] 네트워크 오류: {e}")
        return {"success": False, "message": str(e)}

    except Exception as e:
        print(f"\n  [실패] 예상치 못한 오류: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "message": str(e)}
