"""Dedicated video worker entrypoint; shared durable orchestration lives in nps.worker."""

from nps.worker import main

if __name__ == "__main__":
    main("video")
