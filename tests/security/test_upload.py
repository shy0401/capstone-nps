import zipfile
from unittest.mock import patch
import pytest
from nps.errors import DomainError
from nps.upload import ClamAVScanner, MockScanner, archive_guard, extension_for, validate_file


@pytest.mark.parametrize("name", ["../x.pdf", "..\\x.pdf", "C:\\x.pdf", "file.pdf:evil.exe", "/x.pdf"])
def test_path_traversal(name):
    with pytest.raises(DomainError, match="DOC_UNSAFE_FILENAME"):
        extension_for(name)


def test_disguised_executable(tmp_path):
    p = tmp_path / "x.pdf"
    p.write_bytes(b"MZ executable")
    with pytest.raises(DomainError, match="DOC_MIME_MISMATCH"):
        validate_file(p, ".pdf", "application/pdf")


@pytest.mark.parametrize(
    "entry,contents,code",
    [("../x", b"x", "DOC_ARCHIVE_UNSAFE"), ("x", b"0" * 200000, "DOC_ARCHIVE_BOMB")],
    ids=["traversal", "bomb"],
)
def test_zip_guard(tmp_path, entry, contents, code):
    p = tmp_path / "x.zip"
    with zipfile.ZipFile(p, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(entry, contents)
    with pytest.raises(DomainError, match=code):
        archive_guard(p)


def test_scan_fail_closed(tmp_path):
    p = tmp_path / "x"
    p.write_bytes(b"EICAR-STANDARD-ANTIVIRUS-TEST-FILE")
    with pytest.raises(DomainError, match="DOC_MALWARE"):
        MockScanner().scan(p)
    with patch("socket.create_connection", side_effect=TimeoutError):
        with pytest.raises(DomainError, match="DOC_SCAN_UNAVAILABLE"):
            ClamAVScanner().scan(p)


def test_container_mismatch(tmp_path):
    p = tmp_path / "x.docx"
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("anything.txt", "not docx")
    with pytest.raises(DomainError, match="DOC_MIME_MISMATCH"):
        validate_file(p, ".docx", "application/octet-stream")
