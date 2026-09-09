"""Generate dev-only secrets without printing or committing them."""

import secrets
from pathlib import Path

root = Path(__file__).resolve().parents[2]
target = root / ".env"
if not target.exists():
    content = (root / ".env.example").read_text(encoding="utf-8")
    for key in ("POSTGRES_PASSWORD", "JWT_SECRET", "ADAPTER_SECRET", "SEED_PASSWORD"):
        content = content.replace(f"{key}=\n", f"{key}={secrets.token_urlsafe(36)}\n")
    target.write_text(content, encoding="utf-8")
(root / "storage").mkdir(exist_ok=True)
print("Dev configuration ready; credentials remain in the local .env file.")
