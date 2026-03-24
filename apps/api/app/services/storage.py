from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.core.config import get_settings


@dataclass(slots=True)
class StoredObject:
    relative_path: str
    absolute_path: Path


class LocalFilesystemStorage:
    def __init__(self, root: Path | None = None) -> None:
        settings = get_settings()
        self.root = root or settings.local_storage_dir
        self.root.mkdir(parents=True, exist_ok=True)

    def save_bytes(self, relative_path: str, content: bytes) -> StoredObject:
        absolute_path = self.root / relative_path
        absolute_path.parent.mkdir(parents=True, exist_ok=True)
        absolute_path.write_bytes(content)
        return StoredObject(relative_path=relative_path, absolute_path=absolute_path)

    def read_bytes(self, relative_path: str) -> bytes:
        return (self.root / relative_path).read_bytes()
