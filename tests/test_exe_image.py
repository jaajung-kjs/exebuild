"""exe_image.py 인코딩/디코딩 왕복 테스트 (사내망 불필요, 표준 라이브러리만)."""

import os
import struct
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import exe_image  # noqa: E402


def _roundtrip(tmp_path, data, width=exe_image.DEFAULT_WIDTH):
    src = tmp_path / "in.bin"
    png = tmp_path / "out.png"
    dst = tmp_path / "back.bin"
    src.write_bytes(data)
    exe_image.encode(str(src), str(png), width=width)
    exe_image.decode(str(png), str(dst))
    return png, dst.read_bytes()


def test_roundtrip_is_byte_identical(tmp_path):
    data = bytes(range(256)) * 400 + b"\x00\x01\x02"   # 행 경계에 안 맞는 길이
    _, back = _roundtrip(tmp_path, data)
    assert back == data


def test_empty_file(tmp_path):
    _, back = _roundtrip(tmp_path, b"")
    assert back == b""


def test_exact_row_multiple(tmp_path):
    width = 16
    data = os.urandom(width * exe_image.BYTES_PER_PIXEL * 5)  # 패딩이 전혀 없는 경우
    _, back = _roundtrip(tmp_path, data, width=width)
    assert back == data


def test_output_is_valid_png(tmp_path):
    png, _ = _roundtrip(tmp_path, os.urandom(10000))
    raw = png.read_bytes()
    assert raw[:8] == exe_image.PNG_SIG
    # 첫 청크는 IHDR, 8bit RGB(2) 여야 한다
    tag = raw[12:16]
    depth, color_type = struct.unpack(">BB", raw[24:26])
    assert tag == b"IHDR" and (depth, color_type) == (8, 2)


def test_decode_rejects_non_png(tmp_path):
    bad = tmp_path / "x.png"
    bad.write_bytes(b"not a png file")
    with pytest.raises(ValueError):
        exe_image.decode(str(bad), str(tmp_path / "out.bin"))
