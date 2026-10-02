from __future__ import annotations

import json
import logging

from sqlalchemy import select

from ..db import get_session_factory
from ..events import emit
from ..llm import raw_json_call
from ..models import Analysis, Person, PersonStatus
from ..schemas import AnalysisPayload
from ..scoring.embeddings import embed_payload
from .prompts import build_analysis_messages
from .verify import verify_analysis

logger = logging.getLogger(__name__)


async def analyze_person(person_id: int) -> None:
    factory = get_session_factory()
    async with factory() as session:
        person = await session.get(Person, person_id)
        if person is None:
            return
        existing = await session.get(Analysis, person_id)
        if existing is not None and person.status == PersonStatus.ANALYZED:
            return
        person.status = PersonStatus.ANALYZING
        person.error = None
        await session.commit()
        emit("person.status", person_id=person.id, name=person.name, status=person.status)

        linkedin = person.linkedin_data or {}
        instagram = person.instagram_data or {}

        try:
            payload, dropped = await _call_analysis(linkedin, instagram)
        except Exception as exc:  # noqa: BLE001
            person.status = PersonStatus.FAILED
            person.error = f"Analysis failed: {exc}"
            await session.commit()
            emit(
                "person.status",
                person_id=person.id,
                name=person.name,
                status=person.status,
                error=person.error,
            )
            logger.exception("analysis failed for person %s", person_id)
            return

        embedding = embed_payload(payload)
        analysis = Analysis(
            person_id=person.id,
            payload=payload,
            embedding=embedding,
            overall_confidence=float(payload.get("overall_confidence") or 0.0),
            verified_count=len(payload.get("claims") or []),
            dropped_count=len(dropped),
            dropped=dropped,
        )
        await session.merge(analysis)
        person.status = PersonStatus.ANALYZED
        person.error = None
        await session.commit()
        emit(
            "person.status",
            person_id=person.id,
            name=person.name,
            status=person.status,
            confidence=analysis.overall_confidence,
        )


async def _call_analysis(linkedin: dict, instagram: dict) -> tuple[dict, list[dict]]:
    messages = build_analysis_messages(linkedin, instagram)
    last_error: Exception | None = None
    raw = ""
    for attempt in range(2):
        try:
            raw = await raw_json_call(messages, schema_name="analysis", max_tokens=8192)
            data = json.loads(raw)
            parsed = AnalysisPayload.model_validate(data)
            cleaned, dropped = verify_analysis(parsed.model_dump(), linkedin, instagram)
            return cleaned, dropped
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt == 0:
                messages = messages + [
                    {"role": "assistant", "content": raw},
                    {
                        "role": "user",
                        "content": (
                            "Your previous response failed validation with this error: "
                            f"{exc}. Return a corrected JSON object only."
                        ),
                    },
                ]
                continue
    raise RuntimeError(str(last_error) if last_error else "analysis call failed")


async def all_analyzed_person_ids() -> list[int]:
    factory = get_session_factory()
    async with factory() as session:
        rows = (
            await session.execute(
                select(Person.id).where(Person.status == PersonStatus.ANALYZED).order_by(Person.id)
            )
        ).scalars().all()
        return list(rows)


async def count_analyzed() -> int:
    return len(await all_analyzed_person_ids())
