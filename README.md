# KEPCO RPA 자동화 시스템

Work Monitor 엑셀 다운로드 → 우선순위 분류 → BizMail 전송 자동화 프로그램

## 📋 주요 기능

1. **Excel 다운로드**: Work Monitor에서 사전신고정보 자동 다운로드
2. **우선순위 분류**: 분류표 기준으로 점검순위 자동 분류 (1순위/2순위/3순위)
3. **메일 자동 발송**: BizMail로 처리된 파일 자동 전송

## 🚀 실행 방법

### 기본 실행 (Python)
```bash
python main.py
```

### EXE 실행
```bash
# 더블클릭하여 실행
main.exe
```

## ⚙️ 사전 요구사항

1. **PowerGate 실행 중** ✅
2. **KEPCO 사내망 접속** 🌐
3. **분류표.xlsx 파일** (프로그램과 같은 폴더에 위치)

## 📁 파일 구조

```
totalRPA/
├── main.py                # 메인 실행 파일
├── config.py              # 설정 관리
├── auth.py                # PowerGate 인증
├── downloader.py          # Excel 다운로드
├── processor.py           # 데이터 가공
├── mailer.py              # 메일 전송
├── 분류표.xlsx            # 분류 규칙 + 메일 설정
└── requirements.txt       # Python 패키지 목록
```

## 📊 분류표.xlsx 구조

### 시트 1: 분류 키워드 규칙
- A~F열: 우선순위별 키워드
- I~K열: 특별 우선순위 규칙

### 시트 2: 메일 설정 (신규)
| 열 | 항목 | 설명 | 예시 |
|----|------|------|------|
| A2 | 작성자 이름 | 발신자 이름 | 강원본부 전자제어부 |
| B2 | 작성자 이메일 | 발신자 이메일 주소 | gwpower@kepco.co.kr |
| D2 | 수신자 이메일 | 첫 번째 수신자 | user1@kepco.co.kr |
| D3 | 수신자 이메일 | 두 번째 수신자 | user2@kepco.co.kr |
| D4~ | 수신자 이메일 | 추가 수신자 (빈 셀까지) | ... |
| E2 | 메일 제목 | 이메일 제목 | 공사현장 점검 우선순위 |
| F2 | 메일 본문 | 이메일 본문 내용 | 점검 우선순위를... |

## 🔧 설정 변경

### config.py 수정
```python
# 날짜 설정
# - 현재: 자동으로 내일 날짜

# 부서 코드
DEPARTMENT_CODE = "4200"  # 강원본부

# 페이지당 항목 수
LIST_COUNT = 1000
```

### 분류표.xlsx 시트2 수정
- **발신자 정보**: A2, B2 셀 수정
- **수신자 추가**: D열에 이메일 주소 추가 (D2, D3, D4, ...)
- **제목/본문**: E2, F2 셀 수정

## 📦 출력 파일

- **위치**: 프로그램과 같은 폴더
- **파일명**: `YYMMDD 공사현장 점검 우선순위 리스트.xlsx`
- **예시**: `250120 공사현장 점검 우선순위 리스트.xlsx`

## 🛠️ 개발 환경 설정

### 패키지 설치
```bash
pip install -r requirements.txt
```

### 필수 패키지
- websockets
- requests
- pandas
- openpyxl
- lxml

## 📦 EXE 파일 생성

### PyInstaller 설치
```bash
pip install pyinstaller
```

### EXE 빌드
```bash
pyinstaller --name "KEPCO_RPA" \
            --onefile \
            --windowed \
            --add-data "분류표.xlsx:." \
            --icon=icon.ico \
            main.py
```

### 배포 파일
```
dist/
├── KEPCO_RPA.exe        # 실행 파일
└── 분류표.xlsx          # 설정 파일 (함께 배포)
```

## 🔍 문제 해결

### PowerGate 인증 실패
```
❌ 인증 실패
```
**해결 방법**:
1. PowerGate가 실행 중인지 확인
2. 작업 관리자에서 PowerGate 프로세스 확인
3. PowerGate 재시작

### 다운로드 실패
```
❌ 다운로드 실패
```
**해결 방법**:
1. 사내망 연결 확인
2. Work Monitor 접근 권한 확인
3. 해당 날짜에 데이터 있는지 확인

### 분류표 파일 없음
```
❌ 분류표 파일을 찾을 수 없습니다
```
**해결 방법**:
1. 분류표.xlsx 파일이 프로그램과 같은 폴더에 있는지 확인

### 메일 전송 실패
```
❌ 메일 전송 실패
```
**해결 방법**:
1. 분류표.xlsx 시트2의 메일 설정 확인
2. 수신자 이메일 주소 형식 확인
3. BizMail 접근 권한 확인

## 📝 변경 이력

### v1.0.0 (2025-01-19)
- ✅ 모듈 통합: 3개 파일 → 1개 main.py
- ✅ 단일 인증: WebSocket 연결 1회로 감소
- ✅ 메모리 처리: 디스크 I/O 4회 → 1회 감소
- ✅ 상대 경로: exe 패키징 지원
- ✅ 동적 메일 설정: 분류표.xlsx 시트2에서 로드

## 👥 개발자

강원본부 전자제어부

## 📄 라이선스

Internal Use Only - KEPCO
