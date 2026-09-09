"""Diagnostic host E2E ONLY. PostgreSQL is replaced by SQLite and Redis by a TCP emulator.

This does not satisfy Docker/offline release gates. All listeners bind loopback.
"""

import os
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT / "apps/api"))
os.environ.update(
    {
        "DATABASE_URL": "sqlite:///" + (ROOT / "storage/host-e2e.db").as_posix(),
        "REDIS_URL": "redis://127.0.0.1:16379/0",
        "LLM_ADAPTER_URL": "http://127.0.0.1:18010",
        "COMFY_ADAPTER_URL": "http://127.0.0.1:18020",
        "ENVIRONMENT": "dev",
        "SCAN_MODE": "mock",
        "LLM_MODE": "mock",
        "COMFY_MODE": "mock",
        "DEV_INSECURE_COOKIE": "true",
        "STORAGE_ROOT": str(ROOT / "storage/host-e2e"),
        "PYTHONPATH": str(ROOT / "apps/api"),
    }
)

if __name__ == "__main__":
    import fakeredis
    import uvicorn
    from nps.config import settings
    from nps.db import Base, engine, SessionLocal
    from nps.seed import seed
    from nps.adapter_api import llm_app, comfy_app
    from nps.main import app
    from nps.jobs import heartbeat, claim, recover_expired
    from nps.pipeline import execute_step

    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed(db, settings().seed_password)
    redis_server = fakeredis.TcpFakeServer(("127.0.0.1", 16379), server_type="redis")
    threading.Thread(target=redis_server.serve_forever, daemon=True).start()
    for adapter, port in [(llm_app, 18010), (comfy_app, 18020)]:
        threading.Thread(
            target=uvicorn.run,
            args=(adapter,),
            kwargs={"host": "127.0.0.1", "port": port, "access_log": False, "log_level": "warning"},
            daemon=True,
        ).start()
    stop = threading.Event()

    def worker(queue):
        ident = "host-diagnostic-" + queue
        while not stop.is_set():
            try:
                heartbeat(ident, queue, "cpu", 0)
                with SessionLocal() as db:
                    recover_expired(db)
                    job = claim(db, queue, ident)
                    if job:
                        execute_step(db, job.id)
            except Exception as exc:
                print("DIAGNOSTIC_WORKER_ERROR", type(exc).__name__, flush=True)
            stop.wait(0.25)

    for queue in ("document", "llm", "ppt", "image", "video"):
        threading.Thread(target=worker, args=(queue,), daemon=True).start()
    print(
        "HOST DIAGNOSTIC: SQLite + Redis TCP emulator + actual HTTP adapters; NOT a Docker gate.", flush=True
    )
    uvicorn.run(app, host="127.0.0.1", port=8000, access_log=False, log_level="warning")
