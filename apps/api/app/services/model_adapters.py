from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from app.core.config import get_settings

WORD_PATTERN = re.compile(r"[A-Za-z0-9_]+")


class EmbeddingAdapter(Protocol):
    provider_name: str
    model_name: str

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError


class RerankerAdapter(Protocol):
    provider_name: str
    model_name: str

    def rerank(self, *, query: str, items: list[tuple[str, float]]) -> list[tuple[str, float]]:
        raise NotImplementedError


class GenerationAdapter(Protocol):
    provider_name: str
    model_name: str

    def generate_markdown(
        self,
        *,
        title: str,
        sections: list[tuple[str, list[str]]],
    ) -> str:
        raise NotImplementedError


class DeterministicEmbeddingAdapter:
    provider_name = "deterministic-local"

    def __init__(self, dimensions: int) -> None:
        self.dimensions = dimensions
        self.model_name = f"hashed-bow-{dimensions}"

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            vector = [0.0] * self.dimensions
            for token in WORD_PATTERN.findall(text.lower()):
                digest = hashlib.sha256(token.encode("utf-8")).digest()
                bucket = digest[0] % self.dimensions
                sign = 1.0 if digest[1] % 2 == 0 else -1.0
                vector[bucket] += sign
            norm = math.sqrt(sum(value * value for value in vector))
            if norm > 0:
                vector = [value / norm for value in vector]
            vectors.append(vector)
        return vectors


class DeterministicRerankerAdapter:
    provider_name = "deterministic-local"
    model_name = "score-pass-through"

    def rerank(self, *, query: str, items: list[tuple[str, float]]) -> list[tuple[str, float]]:
        query_tokens = set(WORD_PATTERN.findall(query.lower()))
        ranked: list[tuple[str, float]] = []
        for text, score in items:
            overlap = sum(1 for token in query_tokens if token and token in text.lower())
            ranked.append((text, score + overlap * 0.05))
        ranked.sort(key=lambda item: item[1], reverse=True)
        return ranked


class TemplateGenerationAdapter:
    provider_name = "deterministic-local"
    model_name = "template-markdown-v1"

    def generate_markdown(
        self,
        *,
        title: str,
        sections: list[tuple[str, list[str]]],
    ) -> str:
        lines = [f"# {title}", ""]
        for heading, items in sections:
            if not items:
                continue
            lines.append(f"## {heading}")
            lines.extend(items)
            lines.append("")
        return "\n".join(lines).strip() + "\n"


@dataclass(slots=True)
class AdapterRunRecord:
    adapter_kind: str
    provider_name: str
    model_name: str
    request_json: dict[str, object]
    response_json: dict[str, object]
    started_at: datetime
    completed_at: datetime


class AdapterRegistry:
    def __init__(self) -> None:
        settings = get_settings()
        self.embedding_adapter = DeterministicEmbeddingAdapter(
            settings.hybrid_embedding_dimensions
        )
        self.reranker_adapter = DeterministicRerankerAdapter()
        self.generation_adapter = TemplateGenerationAdapter()

    def embed(self, texts: list[str]) -> tuple[list[list[float]], AdapterRunRecord]:
        started_at = datetime.now(UTC)
        output = self.embedding_adapter.embed_texts(texts)
        completed_at = datetime.now(UTC)
        return output, AdapterRunRecord(
            adapter_kind="embedding",
            provider_name=self.embedding_adapter.provider_name,
            model_name=self.embedding_adapter.model_name,
            request_json={"text_count": len(texts)},
            response_json={"embedding_count": len(output)},
            started_at=started_at,
            completed_at=completed_at,
        )

    def rerank(
        self,
        *,
        query: str,
        items: list[tuple[str, float]],
    ) -> tuple[list[tuple[str, float]], AdapterRunRecord]:
        started_at = datetime.now(UTC)
        output = self.reranker_adapter.rerank(query=query, items=items)
        completed_at = datetime.now(UTC)
        return output, AdapterRunRecord(
            adapter_kind="reranker",
            provider_name=self.reranker_adapter.provider_name,
            model_name=self.reranker_adapter.model_name,
            request_json={"query": query, "item_count": len(items)},
            response_json={"item_count": len(output)},
            started_at=started_at,
            completed_at=completed_at,
        )

    def render_markdown(
        self,
        *,
        title: str,
        sections: list[tuple[str, list[str]]],
    ) -> tuple[str, AdapterRunRecord]:
        started_at = datetime.now(UTC)
        output = self.generation_adapter.generate_markdown(title=title, sections=sections)
        completed_at = datetime.now(UTC)
        return output, AdapterRunRecord(
            adapter_kind="generation",
            provider_name=self.generation_adapter.provider_name,
            model_name=self.generation_adapter.model_name,
            request_json={"title": title, "section_count": len(sections)},
            response_json={"character_count": len(output)},
            started_at=started_at,
            completed_at=completed_at,
        )
