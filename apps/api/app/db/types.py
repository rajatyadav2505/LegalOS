from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any

from sqlalchemy import JSON
from sqlalchemy.engine import Dialect
from sqlalchemy.types import TypeDecorator, UserDefinedType


class _PgVector(UserDefinedType[list[float]]):
    cache_ok = True

    def __init__(self, dimensions: int) -> None:
        self.dimensions = dimensions

    def get_col_spec(self, **_: Any) -> str:
        return f"VECTOR({self.dimensions})"


class EmbeddingVectorType(TypeDecorator[list[float] | None]):
    impl = JSON
    cache_ok = True

    def __init__(self, dimensions: int) -> None:
        super().__init__()
        self.dimensions = dimensions

    def load_dialect_impl(self, dialect: Dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(_PgVector(self.dimensions))
        return dialect.type_descriptor(JSON())

    def process_bind_param(
        self,
        value: Sequence[float] | None,
        dialect: Dialect,
    ) -> str | list[float] | None:
        if value is None:
            return None
        normalized = [float(item) for item in value]
        if dialect.name == "postgresql":
            return "[" + ",".join(f"{item:.8f}" for item in normalized) + "]"
        return normalized

    def process_result_value(
        self,
        value: Any,
        dialect: Dialect,
    ) -> list[float] | None:
        if value is None:
            return None
        if dialect.name == "postgresql":
            if isinstance(value, str):
                stripped = value.strip()
                if stripped.startswith("[") and stripped.endswith("]"):
                    inner = stripped[1:-1].strip()
                    if not inner:
                        return []
                    return [float(item) for item in inner.split(",")]
            if isinstance(value, Sequence):
                return [float(item) for item in value]
            return None
        if isinstance(value, str):
            decoded = json.loads(value)
            return [float(item) for item in decoded]
        return [float(item) for item in value]

    def copy(self, **_: Any) -> EmbeddingVectorType:
        return EmbeddingVectorType(self.dimensions)
