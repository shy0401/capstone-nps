import json
import signal
import socket
import sys
import threading
from datetime import timedelta
from sqlalchemy import update
from nps.config import settings
from nps.db import SessionLocal, uid, utcnow
from nps.jobs import claim, heartbeat, recover_expired
from nps.models import GenerationJob
from nps.pipeline import execute_step


def main(queue):
    worker_id = f"{socket.gethostname()}-{queue}-{uid()}"
    stop = threading.Event()
    current = {"job": None}
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    signal.signal(signal.SIGINT, lambda *_: stop.set())

    def pulse():
        while not stop.is_set():
            try:
                heartbeat(worker_id, queue, settings().worker_capability, settings().worker_vram_mb)
                if current["job"]:
                    with SessionLocal() as db:
                        db.execute(
                            update(GenerationJob)
                            .where(GenerationJob.id == current["job"], GenerationJob.worker_id == worker_id)
                            .values(lease_until=utcnow() + timedelta(seconds=settings().worker_lease_seconds))
                        )
                        db.commit()
            except Exception:
                pass
            stop.wait(5)

    thread = threading.Thread(target=pulse, daemon=True)
    thread.start()
    while not stop.is_set():
        try:
            with SessionLocal() as db:
                recover_expired(db)
                job = claim(db, queue, worker_id, settings().worker_capability, settings().worker_vram_mb)
                if job:
                    current["job"] = job.id
                    execute_step(db, job.id)
                    current["job"] = None
                else:
                    stop.wait(0.5)
        except Exception:
            print(json.dumps({"worker_id": worker_id, "status": "dependency_retry"}), flush=True)
            stop.wait(2)


if __name__ == "__main__":
    main(sys.argv[1])
