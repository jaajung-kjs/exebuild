"""EXE(또는 임의의 파일)를 PNG 이미지로 인코딩하고, 다시 원래 파일로 복원한다.

사내망 반입용. base64 txt와 원리는 같다 — 파일의 바이트를 다른 그릇(여기서는
무손실 PNG의 픽셀)에 담았다가 그대로 되돌린다. PNG은 무손실이라 복원하면 바이트가
100% 동일하다. (JPG는 손실 압축이라 쓰면 안 된다.)

표준 라이브러리(zlib)만 사용한다 — Pillow 같은 외부 패키지가 없는 사내망 파이썬에서도
복원된다. 인코더가 쓰는 PNG는 모든 스캔라인 필터를 0(None)으로 고정하므로, 디코더는
그 전제만으로 간단히 읽는다.

사용:
    python scripts/exe_image.py encode <입력파일> <출력.png>
    python scripts/exe_image.py decode <입력.png> <복원파일>

이미지 맨 앞 픽셀에 매직('EXEIMG\\0') + 원본 길이(8바이트)를 심어, 복원 시 뒤쪽
패딩을 정확히 잘라낸다.
"""

import struct
import sys
import zlib

PNG_SIG = b"\x89PNG\r\n\x1a\n"
MAGIC = b"EXEIMG\x00"              # 7바이트
HEADER_LEN = len(MAGIC) + 8       # 매직 + uint64 길이 = 15바이트
DEFAULT_WIDTH = 2048              # 픽셀 폭 (행당 WIDTH*3 바이트)
BYTES_PER_PIXEL = 3               # RGB


def _chunk(tag: bytes, data: bytes) -> bytes:
    """PNG 청크 하나를 바이트로 만든다 (길이 + 태그 + 데이터 + CRC)."""
    body = tag + data
    return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)


def encode(in_path: str, out_path: str, width: int = DEFAULT_WIDTH) -> None:
    with open(in_path, "rb") as f:
        raw = f.read()

    payload = MAGIC + struct.pack(">Q", len(raw)) + raw

    row_bytes = width * BYTES_PER_PIXEL
    if len(payload) % row_bytes:                       # 마지막 행을 0으로 채운다
        payload += b"\x00" * (row_bytes - len(payload) % row_bytes)
    height = len(payload) // row_bytes

    # 각 스캔라인 앞에 필터 타입 바이트 0(None)을 붙인 뒤 zlib 압축 → IDAT
    raw_scanlines = bytearray()
    for y in range(height):
        raw_scanlines.append(0)
        raw_scanlines += payload[y * row_bytes:(y + 1) * row_bytes]

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)  # 8bit, RGB(2), 기본
    idat = zlib.compress(bytes(raw_scanlines), 9)

    with open(out_path, "wb") as f:
        f.write(PNG_SIG)
        f.write(_chunk(b"IHDR", ihdr))
        f.write(_chunk(b"IDAT", idat))
        f.write(_chunk(b"IEND", b""))

    print(f"encoded: {in_path} ({len(raw) / 1048576:.1f} MB) -> {out_path} "
          f"({width}x{height} PNG)")


def _iter_chunks(data: bytes):
    pos = len(PNG_SIG)
    while pos < len(data):
        (length,) = struct.unpack(">I", data[pos:pos + 4])
        tag = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + length]
        yield tag, body
        pos += 12 + length                             # 길이4 + 태그4 + 데이터 + CRC4


def decode(in_path: str, out_path: str) -> None:
    with open(in_path, "rb") as f:
        data = f.read()
    if data[:8] != PNG_SIG:
        raise ValueError("PNG 파일이 아닙니다.")

    width = height = None
    idat = bytearray()
    for tag, body in _iter_chunks(data):
        if tag == b"IHDR":
            width, height, depth, color_type = struct.unpack(">IIBB", body[:10])
            if (depth, color_type) != (8, 2):
                raise ValueError("이 디코더는 8bit RGB PNG만 지원합니다.")
        elif tag == b"IDAT":
            idat += body
        elif tag == b"IEND":
            break

    row_bytes = width * BYTES_PER_PIXEL
    scanlines = zlib.decompress(bytes(idat))

    payload = bytearray()
    for y in range(height):                            # 행마다 맨 앞 필터 바이트 제거
        start = y * (row_bytes + 1)
        if scanlines[start] != 0:
            raise ValueError("예상치 못한 PNG 필터 — 이 스크립트가 만든 이미지가 아닙니다.")
        payload += scanlines[start + 1:start + 1 + row_bytes]

    if bytes(payload[:len(MAGIC)]) != MAGIC:
        raise ValueError("매직 헤더 불일치 — 이 스크립트로 만든 이미지가 아닙니다.")
    (size,) = struct.unpack(">Q", payload[len(MAGIC):HEADER_LEN])
    raw = bytes(payload[HEADER_LEN:HEADER_LEN + size])

    with open(out_path, "wb") as f:
        f.write(raw)
    print(f"decoded: {in_path} -> {out_path} ({size / 1048576:.1f} MB)")


def main(argv) -> int:
    if len(argv) != 4 or argv[1] not in ("encode", "decode"):
        print(__doc__)
        return 1
    (encode if argv[1] == "encode" else decode)(argv[2], argv[3])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
