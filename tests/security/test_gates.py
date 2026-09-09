import zipfile
import pytest
from pydantic import ValidationError
from nps.config import settings
from nps.errors import DomainError
from nps.parsers import ParserRegistry
from nps.storage import storage
from nps.upload import ClamAVScanner, archive_guard
from nps.contracts import ContentBlock


def test_schema_extra_fields_and_missing_evidence():
    with pytest.raises(ValidationError):
        ContentBlock(text="unsupported fact", source_refs=[])
    with pytest.raises(ValidationError):
        ContentBlock(text="x", source_refs=[], approved=True)


def test_storage_path_escape_rejected():
    for key in ["originals/../../secret", "C:/secret", "originals/..\\secret", "/etc/passwd"]:
        with pytest.raises(DomainError):
            storage.path(key)


def test_xml_entity_expansion_rejected(tmp_path):
    p = tmp_path / "entity.hwpx"
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("mimetype", "application/hwp+zip")
        z.writestr(
            "Contents/section0.xml",
            '<!DOCTYPE x [<!ENTITY attack SYSTEM "file:///etc/passwd">]><x>&attack;</x>',
        )
    with pytest.raises(DomainError, match="DOC_PARSE_FAILED"):
        ParserRegistry().parse(p, ".hwpx")


def test_encrypted_pdf_fails(tmp_path):
    from pypdf import PdfWriter

    writer = PdfWriter()
    writer.add_blank_page(200, 200)
    writer.encrypt("synthetic-encryption")
    p = tmp_path / "encrypted.pdf"
    writer.write(p)
    with pytest.raises(DomainError, match="DOC_ENCRYPTED"):
        ParserRegistry().parse(p, ".pdf")


def test_hwp_invalid_format_explicit(tmp_path):
    path = tmp_path / "x.hwp"
    path.write_bytes(b"not an HWP document")
    with pytest.raises(DomainError, match="HWP_FORMAT_UNSUPPORTED"):
        ParserRegistry().parse(path, ".hwp")


def test_archive_entry_count(tmp_path, monkeypatch):
    monkeypatch.setattr(settings(), "archive_max_entries", 2)
    p = tmp_path / "too-many.zip"
    with zipfile.ZipFile(p, "w") as z:
        for i in range(3):
            z.writestr(str(i), "x")
    with pytest.raises(DomainError, match="DOC_ARCHIVE_BOMB"):
        archive_guard(p)


def test_clamav_unknown_response_fail_closed(tmp_path):
    from unittest.mock import MagicMock

    p = tmp_path / "x"
    p.write_bytes(b"synthetic")
    sock = MagicMock()
    sock.__enter__.return_value = sock
    sock.recv.return_value = b"stream: UNKNOWN\0"
    with (
        patch("socket.create_connection", return_value=sock),
        pytest.raises(DomainError, match="DOC_SCAN_UNAVAILABLE"),
    ):
        ClamAVScanner().scan(p)


def test_no_unclassified_protected_routes():
    from nps.main import app

    data = app.openapi()
    public = {"/api/v1/auth/login", "/api/v1/auth/refresh", "/api/v1/health/live", "/api/v1/health/ready"}
    for path, methods in data["paths"].items():
        for method, operation in methods.items():
            if path not in public:
                assert operation.get("security"), (path, method)


@pytest.mark.clamav
def test_real_clamav_eicar(tmp_path):
    import os

    if os.environ.get("RUN_CLAMAV_TEST") != "1":
        pytest.skip(
            "real ClamAV container unavailable on this host; deterministic fail-closed tests run separately"
        )
    p = tmp_path / "eicar.com"
    # Standard non-executable antivirus test string, synthesized only in a temporary fixture.
    p.write_bytes(b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*")
    with pytest.raises(DomainError, match="DOC_MALWARE"):
        ClamAVScanner().scan(p)
