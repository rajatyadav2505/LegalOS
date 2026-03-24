from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Literal
from uuid import UUID

from app.db.session import SessionLocal
from app.services.research import ResearchService
from pydantic import BaseModel


class ExportMemoTask(BaseModel):
    kind: Literal["export_memo"]
    matter_id: UUID


class QuoteValidationTask(BaseModel):
    kind: Literal["validate_quote"]
    quote_span_id: UUID


TaskEnvelope = ExportMemoTask | QuoteValidationTask


async def run_task(task: TaskEnvelope) -> dict[str, str]:
    async with SessionLocal() as session:
        service = ResearchService(session)
        if task.kind == "export_memo":
            memo = await service.export_memo(matter_id=task.matter_id)
            return {"file_name": memo.file_name, "status": "ok"}

        _, checksum = await service.quote_lock(quote_span_id=task.quote_span_id)
        return {"checksum": checksum, "status": "ok"}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a bounded research task.")
    parser.add_argument("task", help="Path to a JSON task envelope.")
    args = parser.parse_args()

    raw = json.loads(Path(args.task).read_text("utf-8"))
    task = (
        ExportMemoTask.model_validate(raw)
        if raw.get("kind") == "export_memo"
        else QuoteValidationTask.model_validate(raw)
    )
    result = asyncio.run(run_task(task))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
