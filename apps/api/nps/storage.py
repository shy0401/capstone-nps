import hashlib
import json
import shutil
from pathlib import Path, PurePosixPath
from typing import Protocol
from nps.config import settings
from nps.db import uid
from nps.errors import DomainError


class StorageAdapter(Protocol):
    def path(self, key: str) -> Path: ...
    def write_json(self, namespace: str, data: dict | list) -> str: ...


class FileStorage:
    namespaces = {"quarantine", "originals", "parsed", "chunks", "visuals", "artifacts", "qa", "templates"}

    def path(self, key):
        parts = PurePosixPath(key).parts
        if (
            not parts
            or parts[0] not in self.namespaces
            or any(p in {"..", "."} for p in parts)
            or "\\" in key
            or ":" in key
        ):
            raise DomainError("STORAGE_INVALID_KEY")
        root = settings().storage_root.resolve()
        target = root.joinpath(*parts).resolve()
        if not target.is_relative_to(root):
            raise DomainError("STORAGE_INVALID_KEY")
        return target

    def allocate(self, namespace, suffix=".bin"):
        if namespace not in self.namespaces or suffix not in {".bin", ".json", ".pptx", ".mp4", ".png"}:
            raise DomainError("STORAGE_INVALID_KEY")
        key = f"{namespace}/{uid()}{suffix}"
        path = self.path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        return key, path

    def write_json(self, namespace, data):
        key, path = self.allocate(namespace, ".json")
        with path.open("x", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        return key

    def promote(self, quarantine_key):
        source = self.path(quarantine_key)
        key, target = self.allocate("originals")
        # Keep quarantine until its DB checkpoint commits; a killed worker can retry safely.
        with source.open("rb") as src, target.open("xb") as dst:
            shutil.copyfileobj(src, dst)
        return key


storage = FileStorage()


def sha256_file(path):
    with Path(path).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()
