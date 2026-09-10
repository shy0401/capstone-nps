"""Run inside API container: real INSTREAM scan and fail-closed integration."""

import json
import tempfile
from pathlib import Path
from nps.config import settings
from nps.errors import DomainError
from nps.upload import ClamAVScanner


def run():
    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp) / "synthetic-scan.txt"
        path.write_bytes(b"Synthetic safe text")
        ClamAVScanner().scan(path)
        path.write_bytes(b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*")
        try:
            ClamAVScanner().scan(path)
        except DomainError as exc:
            assert exc.code == "DOC_MALWARE", exc.code
        else:
            raise AssertionError("Real antivirus did not reject EICAR")
        config = settings()
        host, port = config.clamav_host, config.clamav_port
        try:
            config.clamav_host, config.clamav_port = "127.0.0.1", 9
            try:
                ClamAVScanner().scan(path)
            except DomainError as exc:
                assert exc.code == "DOC_SCAN_UNAVAILABLE", exc.code
            else:
                raise AssertionError("Scanner failure was not fail-closed")
        finally:
            config.clamav_host, config.clamav_port = host, port
    result = {
        "status": "PASS",
        "scanner": "real ClamAV INSTREAM",
        "clean": "PASS",
        "eicar": "BLOCKED",
        "unavailable": "BLOCKED",
        "signature_policy": "image-bundled; institutional freshness approval TBD",
    }
    print(json.dumps(result))
    return result


if __name__ == "__main__":
    run()
