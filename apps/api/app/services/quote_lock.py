from __future__ import annotations

import hashlib


class QuoteLockService:
    @staticmethod
    def normalize(text: str) -> str:
        return "\n".join(line.rstrip() for line in text.strip().splitlines())

    @classmethod
    def checksum_for_text(cls, text: str) -> str:
        normalized = cls.normalize(text).encode("utf-8")
        return hashlib.sha256(normalized).hexdigest()

    @classmethod
    def matches(cls, candidate_text: str, checksum: str) -> bool:
        return cls.checksum_for_text(candidate_text) == checksum
