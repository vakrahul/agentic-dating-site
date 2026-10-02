from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from typing import Any

from sqlalchemy import select

from .db import get_session_factory
from .models import Date, Person, Run


class Broker:
    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue[dict[str, Any]]] = set()

    def subscribe(self) -> asyncio.Queue[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=1000)
        self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[dict[str, Any]]) -> None:
        self._subscribers.discard(queue)

    def publish(self, event: dict[str, Any]) -> None:
        for queue in list(self._subscribers):
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                pass


broker = Broker()


def emit(event_type: str, **payload: Any) -> None:
    broker.publish({"type": event_type, **payload})


async def sse_stream() -> AsyncIterator[str]:
    queue = broker.subscribe()

    async def snapshot() -> dict[str, Any]:
        factory = get_session_factory()
        async with factory() as session:
            people = (await session.execute(select(Person))).scalars().all()
            runs = (
                (await session.execute(select(Run).order_by(Run.id.desc()).limit(1)))
                .scalars()
                .first()
            )
            dates = (
                (await session.execute(select(Date).where(Date.run_id == runs.id)))
                .scalars()
                .all()
                if runs
                else []
            )
            return {
                "type": "snapshot",
                "people": [
                    {
                        "id": p.id,
                        "name": p.name,
                        "status": p.status,
                        "error": p.error,
                        "linkedin_url": p.linkedin_url,
                        "instagram_url": p.instagram_url,
                    }
                    for p in people
                ],
                "run": {
                    "id": runs.id,
                    "status": runs.status,
                    "stats": runs.stats or {},
                }
                if runs
                else None,
                "dates": [
                    {
                        "id": d.id,
                        "round": d.round,
                        "person_a": d.person_a,
                        "person_b": d.person_b,
                        "status": d.status,
                        "scene": d.scene,
                    }
                    for d in dates
                ],
            }

    try:
        yield _frame(await snapshot())
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=15.0)
                yield _frame(event)
            except asyncio.TimeoutError:
                yield ": keepalive\n\n"
    finally:
        broker.unsubscribe(queue)


def _frame(event: dict[str, Any]) -> str:
    return f"data: {json.dumps(event, default=str)}\n\n"
