"""
KEPCO BizMail 발송 프로그램 (HAR 분석 기반)
완전한 프로세스 재현 (파일첨부 포함)
"""

import asyncio
import websockets
import requests
import os
from datetime import datetime
import uuid


# ==========================================
# 설정 - 여기만 수정하세요
# ==========================================

FROM_EMAIL = "gwpower@kepco.co.kr"
FROM_NAME = "강원본부 전자제어부"

# 수신자는 이메일 주소만 입력
RECIPIENTS = [
    'jaajung@kepco.co.kr',
]

SUBJECT = "RPA 테스트 메일입니다."

BODY = """<html><head><style type="text/css">
p {padding:0;margin:0;}
</style>
</head><body><div class="sensEdContentAreaCls" data-id="sensEdContentArea" style="color:#000;line-height:150%;font-size:12pt;font-family:돋움 !important;padding:0;margin:0;">
RPA 테스트 메일입니다.
</div></body></html>"""

# 첨부파일 경로 (슬래시 / 사용 권장)
ATTACHMENTS = [
    # "C:/Users/jsk/Downloads/test.xlsx",
    # "C:/Data/report.pdf",
]

# 메일 서버
MAIL_SERVER = "http://bizmail.kepco.co.kr"

# ==========================================
# 메인 코드
# ==========================================


async def get_powergate_cookies():
    """PowerGate WebSocket 인증"""
    uri = "ws://127.0.0.1:21777"

    try:
        async with websockets.connect(uri, timeout=10) as ws:
            await ws.send(";;;GETCONFIGep;")
            response = await ws.recv()
            parts = response.split(';')

            if len(parts) >= 4 and parts[2] != "R":
                cookies = {
                    'pgsecuid': parts[1],
                    'pgsecuid2': f'"{parts[1]}"',
                    'opv': parts[3]
                }
                print(f"[성공] PowerGate 인증 완료")
                print(f"     세션: {parts[0][:20]}...")
                print(f"     ID: {parts[2]}\n")
                return cookies
            else:
                print("[실패] 응답 형식 오류")
                return None

    except Exception as e:
        print(f"[실패] PowerGate 오류: {e}")
        return None


def generate_temp_key():
    """임시 키 생성 (예: 691bef103fe3dc6ef9f177fa)"""
    return uuid.uuid4().hex[:24]


def upload_files(session, file_paths):
    """
    파일 업로드

    Args:
        session: requests.Session 객체
        file_paths: 업로드할 파일 경로 리스트

    Returns:
        list: 업로드된 파일 정보 [{filekey, filename, size}, ...]
    """
    uploaded_files = []

    if not file_paths:
        return uploaded_files

    print(f"\n[파일 업로드] {len(file_paths)}개 파일 업로드 중...")

    for filepath in file_paths:
        if not os.path.exists(filepath):
            print(f"  [경고] 파일 없음: {filepath}")
            continue

        filename = os.path.basename(filepath)
        filesize = os.path.getsize(filepath)

        # 내부 파일명 생성 (plupload 방식)
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
                    f'{MAIL_SERVER}/mail/json/uploadFile.do?_csrf=',
                    files=files,
                    data=data,
                    timeout=30
                )

                result = resp.json()

                if result.get('result') == 1 and 'filekey' in result:
                    filekey = result['filekey'][0]
                    uploaded_files.append({
                        'filekey': filekey,
                        'filename': filename,
                        'size': filesize
                    })
                    print(f"  [성공] {filename} ({filesize} bytes)")
                    print(f"         filekey: {filekey}")
                else:
                    print(f"  [실패] {filename}: {result}")

        except Exception as e:
            print(f"  [실패] {filename}: {e}")

    print(f"\n[완료] {len(uploaded_files)}개 파일 업로드 완료\n")
    return uploaded_files


def send_bizmail(cookies, from_addr, from_name, subject, body, recipients, attachments=None):
    """
    bizmail.kepco.co.kr을 통해 메일 발송
    HAR 파일 분석 기반 완전한 프로세스 구현
    """

    print("=" * 60)
    print("BIZMAIL 발송 프로세스")
    print("=" * 60)

    session = requests.Session()
    session.cookies.update(cookies)
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Origin': MAIL_SERVER,
        'Referer': f'{MAIL_SERVER}/mail/list.do',
        'X-Requested-With': 'XMLHttpRequest',
    })

    try:
        # ==========================================
        # 단계 1: 세션 확인
        # ==========================================
        print("\n[1/4] 세션 확인 중...")

        timestamp = int(datetime.now().timestamp() * 1000)
        session_url = f"{MAIL_SERVER}/common/json/session/check.do?_={timestamp}"

        session_resp = session.get(session_url)
        session_data = session_resp.json()

        if not session_data.get('alive'):
            print("[실패] 세션 만료")
            return {"success": False, "message": "세션 만료"}

        print("      세션 상태: 정상")

        # ==========================================
        # 단계 2: 파일 업로드
        # ==========================================
        print("\n[2/4] 파일 업로드 중...")

        uploaded_files = upload_files(session, attachments or [])

        # 첨부파일 정보 준비
        attach_size = sum(f['size'] for f in uploaded_files)
        attach_list = ':'.join([f"{f['filename']}:{f['size']}:1:0" for f in uploaded_files])
        attachments_param = ':'.join([f"{f['filekey']}:0:1:0" for f in uploaded_files])

        # ==========================================
        # 단계 3: 수신자 확인
        # ==========================================
        print("\n[3/4] 수신자 검증 중...")

        receiver_data = {
            'subject': subject,
            'subjecthead': '-1',
            'content': body,
            'fromaddr': from_addr,
            'attach_size': str(attach_size),
            'attach_list': attach_list,
        }

        # 수신자 추가
        for recipient in recipients:
            receiver_data['to'] = recipient

        receiver_resp = session.post(
            f"{MAIL_SERVER}/mail/json/receiverCheck.do",
            data=receiver_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
        )

        receiver_result = receiver_resp.json()
        print(f"      발송 권한: {receiver_result.get('permission', False)}")
        print(f"      수신자 수: {receiver_result.get('receiver_count', 0)}")

        if not receiver_result.get('permission'):
            print("[실패] 발송 권한 없음")
            return {"success": False, "message": "발송 권한 없음"}

        # ==========================================
        # 단계 4: 메일 발송 (HAR 완전 재현)
        # ==========================================
        print("\n[4/4] 메일 발송 중...")

        # tempKey 생성
        temp_key = generate_temp_key()
        secure_value = temp_key[:10]

        current_date = datetime.now().strftime("%Y-%m-%d")

        # HAR에서 추출한 완전한 파라미터
        send_data = {
            # 기본 정보
            'fromaddr': from_addr,
            'fromname': from_name,
            'subject': subject,
            'subjecthead': '-1',
            'body': body,

            # 수신자
            '_tome': 'on',
            '_is_report': 'on',

            # 임시키 & 보안
            'tempKey': temp_key,
            'secureValue': secure_value,
            'ukey': '',
            'first': '0',
            'tempsave': '0',

            # 첨부파일
            'attachments': attachments_param,

            # 예약 & 결재
            'reserverTime': '',
            'req_reserverTime': '',
            'mail_cancel_time': '0',
            'approval_flag': '0',
            'isPermissionMail': '',
            'reserveEndTime': '',
            'repeat_type': '',
            'repeat_cycle': '0',
            'repeat_dayofweek': '',
            'repeat_mailkey': '',
            'myTemplateKey': '',

            # 링크 첨부
            'islinkattach': '0',
            'use_bigfile_password': '0',
            'linkattach_filesize': '',
            'linkattach_downterm': '',
            'temp_save_bigfile': '1',

            # 결재
            'approvalkey': '',
            'ap_send_type': '0',
            'approver': '',
            'is_ap': '0',

            # 옵션 (HAR에서 발견 - 중요!)
            '_is_each': 'on',
            '_important': 'on',
            '_use_sign': 'on',
            'sign': 'mail_sign',

            # 예약 시간
            'reserveTime': current_date,
            'c_reserveTime': current_date,
            'hour_c': '23',
            'minute_c': '50',

            # 에디터
            'editor_type': '1',
            'characterset': 'utf-8',

            # 보안 & 수신확인
            '_is_secure': 'on',
            'is_receipt': '1',
            '_is_receipt': 'on',

            # 보낸메일함에 저장 (핵심!)
            'is_save': '1',
            '_is_save': 'on',

            # 알림 & SMS
            '_alarm': 'on',
            '_sms': 'on',

            # 회신 요청
            'replyRequestTime': current_date,
            'hour_r': '23',
            'minute_r': '50',

            # 결재 보고
            'apUser': '',
            'apUserText': '',
            '_apReport': 'on',

            # 편집
            'editHtml': '',
            'editText': '',
            'divText': '',
        }

        # 수신자 추가
        for recipient in recipients:
            send_data['to'] = recipient

        print(f"      발신: {from_name} <{from_addr}>")
        print(f"      수신: {len(recipients)}명")
        print(f"      제목: {subject}")
        print(f"      첨부: {len(uploaded_files)}개 파일")
        print(f"      TempKey: {temp_key}")
        print(f"      보낸메일함 저장: 활성화")

        # 발송!
        send_resp = session.post(
            f"{MAIL_SERVER}/mail/json/send.do",
            data=send_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
        )

        send_result = send_resp.json()

        print("\n" + "=" * 60)

        if send_result.get('code') == 1:
            print("[성공] 메일 발송 완료!")
            print(f"        {send_result.get('send_result_txt', '성공')}")
            print(f"        {send_result.get('send_result_txt_desc', '')}")
            print(f"        발송 메일 키: {send_result.get('sent_mail_key', 'N/A')}")
            print(f"        저장 메일 키: {send_result.get('save_mail_key', 'N/A')}")
            print("=" * 60)
            return {"success": True, "message": "발송 완료", "response": send_result}
        else:
            print("[실패] 발송 실패")
            print(f"       응답: {send_result}")
            print("=" * 60)
            return {"success": False, "message": "발송 실패", "response": send_result}

    except requests.exceptions.RequestException as e:
        print(f"\n[실패] 네트워크 오류: {e}")
        return {"success": False, "message": str(e)}

    except Exception as e:
        print(f"\n[실패] 예상치 못한 오류: {e}")
        return {"success": False, "message": str(e)}


async def main():
    """메인 실행"""
    print("\n" + "=" * 60)
    print("KEPCO BIZMAIL 발송 프로그램")
    print("=" * 60)
    print(f"시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 쿠키 획득
    print("=" * 60)
    print("인증")
    print("=" * 60)

    cookies = await get_powergate_cookies()

    if not cookies:
        print("\n[실패] 쿠키를 가져올 수 없습니다")
        print("\n해결 방법:")
        print("  1. PowerGate가 실행 중인지 확인")
        print("  2. 작업 관리자에서 PowerGate 프로세스 확인")
        print("  3. PowerGate를 재시작하고 다시 시도")
        return

    # 메일 발송
    result = send_bizmail(
        cookies=cookies,
        from_addr=FROM_EMAIL,
        from_name=FROM_NAME,
        subject=SUBJECT,
        body=BODY,
        recipients=RECIPIENTS,
        attachments=ATTACHMENTS
    )

    # 결과
    print("\n" + "=" * 60)
    print("완료")
    print("=" * 60)
    print(f"종료: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"결과: {'성공' if result['success'] else '실패'}")

    if result['success']:
        print("\n확인 사항:")
        print("  1. 받은메일함 - 메일이 도착했나요?")
        print("  2. 보낸메일함 - 메일이 저장되었나요? (is_save=1)")

    print("=" * 60)


if __name__ == '__main__':
    """
    사용 방법:

    1. 설정 수정 (19-36번째 줄)
       - FROM_EMAIL: 발신자 이메일
       - FROM_NAME: 발신자 이름
       - RECIPIENTS: 수신자 목록 (이메일 주소만)
       - SUBJECT: 메일 제목
       - BODY: 메일 본문 (HTML)
       - ATTACHMENTS: 첨부파일 경로

    2. PowerGate 실행 확인

    3. 실행:
       python bizmail_send.py

    참고:
    - 수신자는 이메일 주소만 입력
    - 첨부파일 경로는 슬래시(/) 사용 권장
    - is_save=1로 보낸메일함에 자동 저장
    - HAR 파일의 모든 파라미터 포함
    """
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n사용자가 중단했습니다")
