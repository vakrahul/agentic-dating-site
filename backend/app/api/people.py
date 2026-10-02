from __future__ import annotations

import asyncio
import logging
import re

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from ..db import get_session_factory
from ..models import Analysis, Person, PersonStatus
from ..pipeline import process_person
from ..schemas import (
    AnalysisPayload,
    PeopleBatchRequest,
    PersonDetailOut,
    PersonOut,
    PairInput,
)

router = APIRouter()
logger = logging.getLogger(__name__)

_background_tasks: set[asyncio.Task] = set()


def spawn(coro) -> asyncio.Task:
    task = asyncio.create_task(coro)
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
    return task


def derive_name(linkedin_url: str, instagram_url: str) -> str:
    match = re.search(r"linkedin\.com/in/([^/?#]+)", linkedin_url.lower())
    slug = match.group(1) if match else instagram_url.rstrip("/").split("/")[-1]
    words = re.split(r"[-_]+", slug)
    return " ".join(w.capitalize() for w in words if w) or slug


@router.post("/people", response_model=dict)
async def create_people(batch: PeopleBatchRequest) -> dict:
    created: list[PersonOut] = []
    errors: list[dict] = []
    factory = get_session_factory()

    async with factory() as session:
        for index, item in enumerate(batch.people):
            existing = (
                await session.execute(
                    select(Person).where(
                        (Person.linkedin_url == item.linkedin_url)
                        | (Person.instagram_url == item.instagram_url)
                    )
                )
            ).scalars().first()
            if existing is not None:
                created.append(_person_out(existing))
                continue

            name = item.name or derive_name(item.linkedin_url, item.instagram_url)
            person = Person(
                name=name,
                linkedin_url=item.linkedin_url,
                instagram_url=item.instagram_url,
                status=PersonStatus.QUEUED,
            )
            session.add(person)
            await session.flush()
            created.append(_person_out(person))

        await session.commit()

    person_ids = [p.id for p in created]
    for pid in person_ids:
        spawn(process_person(pid))

    return {"created": created, "errors": errors, "count": len(created)}


@router.post("/people/validate", response_model=dict)
async def validate_rows(batch: PeopleBatchRequest) -> dict:
    results = []
    for index, item in enumerate(batch.people):
        results.append({"index": index, "ok": True, "linkedin_url": item.linkedin_url,
                        "instagram_url": item.instagram_url})
    return {"rows": results}


@router.post("/people/process-queue")
async def process_queue(include_failed: bool = False) -> dict:
    from ..pipeline import resume_queued_people
    pids = await resume_queued_people(include_failed=include_failed)
    return {"resumed_count": len(pids), "person_ids": pids}


@router.post("/people/{person_id}/retry")
async def retry_person(person_id: int) -> dict:
    factory = get_session_factory()
    async with factory() as session:
        person = await session.get(Person, person_id)
        if person is None:
            raise HTTPException(status_code=404, detail="Person not found")
        person.status = PersonStatus.QUEUED
        person.error = None
        await session.commit()
    spawn(process_person(person_id))
    return {"ok": True, "person_id": person_id}


@router.get("/people", response_model=list[PersonOut])
async def list_people() -> list[PersonOut]:
    factory = get_session_factory()
    async with factory() as session:
        people = (await session.execute(select(Person).order_by(Person.id))).scalars().all()
        analysis_ids = set(
            (await session.execute(select(Analysis.person_id))).scalars().all()
        )
        out = []
        for person in people:
            item = _person_out(person)
            item.has_analysis = person.id in analysis_ids and person.status == PersonStatus.ANALYZED
            out.append(item)
        return out


@router.get("/people/{person_id}", response_model=PersonDetailOut)
async def get_person(person_id: int) -> PersonDetailOut:
    factory = get_session_factory()
    async with factory() as session:
        person = await session.get(Person, person_id)
        if person is None:
            raise HTTPException(status_code=404, detail="Person not found")
        analysis_row = await session.get(Analysis, person_id)
        detail = PersonDetailOut(
            id=person.id,
            name=person.name,
            linkedin_url=person.linkedin_url,
            instagram_url=person.instagram_url,
            status=person.status,
            error=person.error,
            has_analysis=analysis_row is not None and person.status == PersonStatus.ANALYZED,
            linkedin_data=person.linkedin_data,
            instagram_data=person.instagram_data,
        )
        if analysis_row is not None:
            payload = AnalysisPayload.model_validate(analysis_row.payload)
            from ..schemas import AnalysisOut

            detail.analysis = AnalysisOut(
                person_id=person_id,
                payload=payload,
                overall_confidence=analysis_row.overall_confidence,
                verified_count=analysis_row.verified_count,
                dropped_count=analysis_row.dropped_count,
                dropped=analysis_row.dropped or [],
                embedding=analysis_row.embedding,
            )
        return detail


def _person_out(person: Person) -> PersonOut:
    return PersonOut(
        id=person.id,
        name=person.name,
        linkedin_url=person.linkedin_url,
        instagram_url=person.instagram_url,
        status=person.status,
        error=person.error,
        has_analysis=person.status == PersonStatus.ANALYZED,
    )
