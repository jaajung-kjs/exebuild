"""EXE를 사내망 반입용 base64 txt(한 덩어리)로 인코딩.

certutil -encode 는 큰 파일에서 '산술 결과가 32비트를 초과' 오류가 나지만,
여기서는 Python으로 인코딩하므로 그 문제가 없다. 사내망에서는 certutil -decode
(크기 제한 없음)로 한 번에 풀면 된다.

사용: python scripts/make_txt_package.py <exe경로> <출력폴더>
결과: <출력폴더>/KEPCO_RPA.txt (base64), 사용법.txt
"""

import base64
import os
import sys

USAGE = """[KEPCO_RPA.exe 사내망 반입 방법]

1. KEPCO_RPA.txt 를 사내망으로 옮깁니다.
2. 명령 프롬프트에서:
     certutil -decode KEPCO_RPA.txt KEPCO_RPA.exe
   → KEPCO_RPA.exe 가 만들어집니다.

(GitHub에서 이미 txt로 인코딩되어 있으므로, certutil -encode 는 필요 없습니다.
 decode 는 큰 파일도 정상 동작합니다.)
"""


def main():
    exe_path = sys.argv[1]
    out_dir = sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)

    with open(exe_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")

    with open(os.path.join(out_dir, "KEPCO_RPA.txt"), "w", newline="\n") as f:
        for j in range(0, len(b64), 76):     # 76열 줄바꿈(표준 base64 형식)
            f.write(b64[j:j + 76] + "\n")

    with open(os.path.join(out_dir, "사용법.txt"), "w", encoding="utf-8") as f:
        f.write(USAGE)

    print(f"base64 txt created: {len(b64) / 1024 / 1024:.1f} MB (text)")


if __name__ == "__main__":
    main()
