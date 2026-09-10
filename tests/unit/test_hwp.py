import importlib.util
import struct
import zlib

import pytest

from nps.config import settings
from nps.errors import DomainError
from nps.hwp import decompress_section, paragraph_text, records
from nps.parsers import ParserRegistry, safe_parse


@pytest.fixture
def make_hwp():
    spec = importlib.util.spec_from_file_location("hwp_fixtures", "infra/scripts/generate_fixtures.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.hwp_fixture


@pytest.mark.parametrize("compressed", [True, False])
def test_real_ole_body_and_safe_subprocess(tmp_path, make_hwp, compressed):
    path = tmp_path / "synthetic.hwp"
    make_hwp(path, compressed=compressed)
    parsed = safe_parse(path, ".hwp")
    assert parsed.parser_version == "hwp5-native-1.0"
    assert "18건" in parsed.sections[0].nodes[-1].text
    assert len(parsed.sections[0].nodes) == 3
    assert parsed.warnings
    assert all(n.source_location.section == "hwp-section0" for n in parsed.sections[0].nodes)


@pytest.mark.parametrize(
    "flags,code",
    [
        (2, "DOC_ENCRYPTED"),
        (4, "HWP_DISTRIBUTION_UNSUPPORTED"),
        (16, "HWP_DRM_UNSUPPORTED"),
        (1024, "HWP_DRM_UNSUPPORTED"),
    ],
)
def test_protected_hwp_rejected(tmp_path, make_hwp, flags, code):
    path = tmp_path / "protected.hwp"
    make_hwp(path, flags=flags)
    with pytest.raises(DomainError, match=code):
        ParserRegistry().parse(path, ".hwp")


def test_control_payload_not_interpreted_as_text():
    ctrl = struct.pack("<H", 2) + b"dces" + bytes(8) + struct.pack("<H", 2)
    tab = struct.pack("<H", 9) + bytes(12) + struct.pack("<H", 9)
    assert (
        paragraph_text(ctrl + "본문".encode("utf-16le") + tab + "값😀\r".encode("utf-16le")) == "본문\t값😀"
    )
    with pytest.raises(DomainError, match="DOC_MALFORMED"):
        paragraph_text(ctrl[:4])


def test_extended_record_and_malformed_lengths():
    payload = ("합성" * 1500).encode("utf-16le")
    data = struct.pack("<II", 67 | (4095 << 20), len(payload)) + payload
    assert list(records(data))[0][2] == payload
    with pytest.raises(DomainError, match="DOC_MALFORMED"):
        list(records(data[:-2]))


def test_compression_bomb_and_truncated_deflate():
    encoder = zlib.compressobj(wbits=-15)
    data = encoder.compress(b"a" * 10000) + encoder.flush()
    with pytest.raises(DomainError, match="DOC_RESOURCE_LIMIT"):
        decompress_section(data, 100)
    with pytest.raises(DomainError, match="DOC_MALFORMED"):
        decompress_section(data[:-1], 20000)


def test_empty_hwp_not_fake_success(tmp_path, make_hwp):
    path = tmp_path / "empty.hwp"
    make_hwp(path, body=struct.pack("<I", 66 | (22 << 20)) + bytes(22))
    with pytest.raises(DomainError, match="DOC_EMPTY"):
        ParserRegistry().parse(path, ".hwp")


def test_node_budget(tmp_path, make_hwp, monkeypatch):
    path = tmp_path / "limited.hwp"
    make_hwp(path)
    monkeypatch.setattr(settings(), "max_cells", 2)
    with pytest.raises(DomainError, match="DOC_RESOURCE_LIMIT"):
        ParserRegistry().parse(path, ".hwp")
