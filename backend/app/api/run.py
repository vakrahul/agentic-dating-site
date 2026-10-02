from __future__ import annotations

import logging

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from ..db import get_session_factory
from ..events import sse_stream
from ..models import Person, PersonStatus, Run, RunStatus
from ..schemas import RunOut

router = APIRouter()
logger = logging.getLogger(__name__)

from ..dating.engine import spawn_run  # noqa: E402


@router.post("/run", response_model=RunOut)
async def start_run() -> RunOut:
    factory = get_session_factory()
    async with factory() as session:
        active = (
            await session.execute(
                select(Run).where(Run.status == RunStatus.RUNNING).order_by(Run.id.desc())
            )
        ).scalars().first()
        if active is not None:
            return RunOut(
                id=active.id,
                status=active.status,
                error=active.error,
                stats=active.stats or {},
                started_at=active.started_at,
                finished_at=active.finished_at,
            )
        run = Run(status=RunStatus.RUNNING, stats={"phase": "starting", "done": 0, "total": 0})
        session.add(run)
        await session.commit()
        await session.refresh(run)
        run_id = run.id

    excluded = await _excluded_people()
    spawn_run(run_id, excluded)
    return RunOut(
        id=run_id,
        status=RunStatus.RUNNING,
        stats={"phase": "starting", "done": 0, "total": 0, "excluded": excluded},
    )


@router.get("/run", response_model=RunOut | None)
async def current_run() -> RunOut | None:
    factory = get_session_factory()
    async with factory() as session:
        run = (
            await session.execute(select(Run).order_by(Run.id.desc()).limit(1))
        ).scalars().first()
        if run is None:
            return None
        return RunOut(
            id=run.id,
            status=run.status,
            error=run.error,
            stats=run.stats or {},
            started_at=run.started_at,
            finished_at=run.finished_at,
        )


@router.get("/run/stream")
async def run_stream() -> StreamingResponse:
    return StreamingResponse(
        sse_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


async def _excluded_people() -> list[dict]:
    factory = get_session_factory()
    async with factory() as session:
        people = (await session.execute(select(Person).order_by(Person.id))).scalars().all()
        excluded = []
        for person in people:
            if person.status != PersonStatus.ANALYZED:
                excluded.append(
                    {
                        "person_id": person.id,
                        "name": person.name,
                        "reason": person.error or f"status is {person.status}, not analyzed",
                    }
                )
        return excluded
