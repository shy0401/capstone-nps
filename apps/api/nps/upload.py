import socket
import struct
import zipfile
from pathlib import PurePosixPath
from nps.config import settings
from nps.errors import DomainError
from nps.storage import sha256_file, storage

MIMES = {
    ".pdf": {"application/pdf"},
    ".docx": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
    ".xlsx": {"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"},
    ".hwpx": {"application/hwp+zip", "application/vnd.hancom.hwpx", "application/zip"},
    ".hwp": {"application/x-hwp", "application/haansofthwp", "application/vnd.hancom.hwp"},
    ".pptx": {"application/vnd.openxmlformats-officedocument.presentationml.presentation"},
}


def extension_for(filename, template=False):
    if not filename or any(c in filename for c in ("/", "\\", ":", "\x00")) or filename in {".", ".."}:
        raise DomainError("DOC_UNSAFE_FILENAME")
    ext = PurePosixPath(filename).suffix.lower()
    if ext not in MIMES or (ext == ".pptx" and not template):
        raise DomainError("DOC_UNSUPPORTED")
    return ext


async def quarantine_upload(file, template=False):
    key, path = storage.allocate("quarantine")
    size = 0
    try:
        with path.open("xb") as out:
            while block := await file.read(64 * 1024):
                size += len(block)
                if size > settings().upload_max_bytes:
                    raise DomainError("DOC_TOO_LARGE", 413)
                out.write(block)
        ext = extension_for(file.filename, template)
        return {
            "quarantine_key": key,
            "extension": ext,
            "mime": file.content_type or "application/octet-stream",
            "size": size,
        }
    except Exception:
        path.unlink(missing_ok=True)
        raise
    finally:
        await file.close()


def archive_guard(path):
    try:
        with zipfile.ZipFile(path) as z:
            entries = z.infolist()
            cfg = settings()
            if len(entries) > cfg.archive_max_entries:
                raise DomainError("DOC_ARCHIVE_BOMB")
            total = 0
            names = set()
            for item in entries:
                parts = PurePosixPath(item.filename).parts
                if (
                    item.filename.startswith(("/", "\\"))
                    or ".." in parts
                    or "\\" in item.filename
                    or ":" in item.filename
                    or item.filename in names
                ):
                    raise DomainError("DOC_ARCHIVE_UNSAFE")
                names.add(item.filename)
                if item.flag_bits & 1:
                    raise DomainError("DOC_ENCRYPTED")
                total += item.file_size
                if (
                    total > cfg.archive_max_bytes
                    or item.file_size / max(1, item.compress_size) > cfg.archive_max_ratio
                ):
                    raise DomainError("DOC_ARCHIVE_BOMB")
                if ((item.external_attr >> 16) & 0o170000) == 0o120000:
                    raise DomainError("DOC_ARCHIVE_UNSAFE")
                lower = item.filename.lower()
                if "vbaproject" in lower or "/embeddings/" in lower:
                    raise DomainError("DOC_EMBEDDED_ACTIVE_CONTENT")
            return names
    except zipfile.BadZipFile:
        raise DomainError("DOC_MALFORMED") from None


def validate_file(path, extension, mime):
    if path.stat().st_size == 0:
        raise DomainError("DOC_MALFORMED")
    if path.stat().st_size > settings().upload_max_bytes:
        raise DomainError("DOC_TOO_LARGE", 413)
    if mime not in MIMES[extension] | {"application/octet-stream"}:
        raise DomainError("DOC_MIME_MISMATCH")
    with path.open("rb") as f:
        magic = f.read(8)
    if extension == ".pdf":
        if not magic.startswith(b"%PDF-"):
            raise DomainError("DOC_MIME_MISMATCH")
    elif extension == ".hwp":
        if magic != b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
            raise DomainError("DOC_MIME_MISMATCH")
        import olefile

        try:
            with olefile.OleFileIO(path) as ole:
                header = ole.openstream("FileHeader").read(256)
                if not header.startswith(b"HWP Document File"):
                    raise DomainError("DOC_MIME_MISMATCH")
        except (OSError, IOError):
            raise DomainError("DOC_MALFORMED") from None
    else:
        if not magic.startswith(b"PK\x03\x04"):
            raise DomainError("DOC_MIME_MISMATCH")
        names = archive_guard(path)
        required = {".docx": "word/document.xml", ".xlsx": "xl/workbook.xml", ".pptx": "ppt/presentation.xml"}
        if extension in required and not {required[extension], "[Content_Types].xml"}.issubset(names):
            raise DomainError("DOC_MIME_MISMATCH")
        if extension == ".hwpx" and (
            "mimetype" not in names
            or not any(n.startswith("Contents/section") and n.endswith(".xml") for n in names)
        ):
            raise DomainError("DOC_MIME_MISMATCH")
        if extension == ".hwpx":
            with zipfile.ZipFile(path) as z:
                if z.read("mimetype").strip() != b"application/hwp+zip":
                    raise DomainError("DOC_MIME_MISMATCH")
    return sha256_file(path)


class MockScanner:
    """Deterministic TEST ONLY signature adapter, not an antivirus substitute."""

    mode = "mock"

    def scan(self, path):
        tail = b""
        with path.open("rb") as f:
            while block := f.read(65536):
                data = tail + block
                if b"EICAR-STANDARD-ANTIVIRUS-TEST-FILE" in data:
                    raise DomainError("DOC_MALWARE")
                tail = data[-80:]
        return "CLEAN"


class ClamAVScanner:
    mode = "clamav"

    def scan(self, path):
        try:
            with socket.create_connection(
                (settings().clamav_host, settings().clamav_port), timeout=settings().scan_timeout
            ) as sock:
                sock.settimeout(settings().scan_timeout)
                sock.sendall(b"zINSTREAM\0")
                with path.open("rb") as f:
                    while block := f.read(65536):
                        sock.sendall(struct.pack("!I", len(block)) + block)
                sock.sendall(struct.pack("!I", 0))
                response = b""
                while b"\0" not in response and len(response) < 4096:
                    part = sock.recv(4096)
                    if not part:
                        break
                    response += part
            if b"FOUND" in response:
                raise DomainError("DOC_MALWARE")
            if response.strip(b"\0\r\n") != b"stream: OK":
                raise DomainError("DOC_SCAN_UNAVAILABLE", 503)
            return "CLEAN"
        except (OSError, TimeoutError):
            raise DomainError("DOC_SCAN_UNAVAILABLE", 503) from None


def scanner():
    if settings().scan_mode == "mock" and settings().environment == "dev":
        return MockScanner()
    if settings().scan_mode == "clamav":
        return ClamAVScanner()
    raise DomainError("DOC_SCAN_UNAVAILABLE", 503)


def security_scan(payload):
    path = storage.path(payload["quarantine_key"])
    digest = validate_file(path, payload["extension"], payload["mime"])
    scan = scanner()
    if scan.scan(path) != "CLEAN":
        raise DomainError("DOC_SCAN_UNAVAILABLE", 503)
    return {
        "sha256": digest,
        "storage_key": storage.promote(payload["quarantine_key"]),
        "scan_status": "CLEAN",
        "scan_mode": scan.mode,
    }
