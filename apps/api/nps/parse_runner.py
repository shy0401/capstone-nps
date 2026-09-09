import json
import os
import sys
from pathlib import Path
from nps.config import settings
from nps.errors import DomainError

if os.name == "posix":
    import resource

    limit = settings().parse_memory_mb * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (limit, limit))
    resource.setrlimit(resource.RLIMIT_CPU, (settings().parse_timeout, settings().parse_timeout + 1))

from nps.parsers import ParserRegistry  # noqa: E402

if __name__ == "__main__":
    try:
        data = ParserRegistry().parse(Path(sys.argv[1]), sys.argv[2]).model_dump(mode="json")
        code = 0
    except DomainError as exc:
        data, code = {"error": exc.code}, 1
    except (MemoryError, Exception):
        data, code = {"error": "DOC_RESOURCE_LIMIT"}, 1
    Path(sys.argv[3]).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    sys.exit(code)
