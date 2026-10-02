from __future__ import annotations

import asyncio
import logging

from sqlalchemy import select

from .analysis.agent import analyze_person
from .config import get_settings
from .db import get_session_factory
from .events import emit
from .models import Person, PersonStatus
from .scrapers.base import ScrapeError, read_cache, write_cache
from .scrapers.instagram import fetch_instagram
from .scrapers.linkedin import fetch_linkedin

logger = logging.getLogger(__name__)

_scrape_semaphore: asyncio.Semaphore | None = None


def _semaphore() -> asyncio.Semaphore:
    global _scrape_semaphore
    if _scrape_semaphore is None:
        _scrape_semaphore = asyncio.Semaphore(get_settings().scrape_concurrency)
    return _scrape_semaphore


async def process_person(person_id: int) -> None:
    """Scrape both sources then analyze. Never raises; failures are recorded."""
    try:
        await _scrape(person_id)
    except Exception as exc:  # noqa: BLE001
        logger.exception("scrape pipeline failed for person %s", person_id)
        await _fail(person_id, str(exc))
        return

    person = await _get_person(person_id)
    if person is None or person.status == PersonStatus.FAILED:
        return
    await analyze_person(person_id)


async def _scrape(person_id: int) -> None:
    person = await _get_person(person_id)
    if person is None:
        return

    person.status = PersonStatus.SCRAPING
    person.error = None
    await _commit(person)
    emit("person.status", person_id=person.id, name=person.name, status=person.status)

    async with _semaphore():
        linkedin_task = _safe_fetch(person.linkedin_url, fetch_linkedin)
        instagram_task = _safe_fetch(person.instagram_url, fetch_instagram)
        li_result, ig_result = await asyncio.gather(linkedin_task, instagram_task)

    # Instagram is required; LinkedIn is best-effort (paid actor may fail on free plan)
    if ig_result["error"] and li_result["error"]:
        # Both failed — hard fail
        await _fail(person_id, f"LinkedIn: {li_result['error']}; Instagram: {ig_result['error']}")
        return

    if ig_result["error"]:
        # Instagram failed, LinkedIn ok — still fail (Instagram is primary source)
        await _fail(person_id, f"Instagram: {ig_result['error']}")
        return

    # LinkedIn optional — warn but continue if only LinkedIn failed
    warning = None
    if li_result["error"]:
        warning = f"LinkedIn unavailable: {li_result['error']}"
        logger.warning("person %s: %s", person_id, warning)

    person = await _get_person(person_id)
    if person is None:
        return
    person.linkedin_data = li_result["data"]  # may be None if LinkedIn failed
    person.instagram_data = ig_result["data"]
    person.status = PersonStatus.SCRAPED
    person.error = warning  # surface as a non-fatal warning
    await _commit(person)
    emit("person.status", person_id=person.id, name=person.name, status=person.status)


async def _safe_fetch(url: str, fetcher) -> dict:
    try:
        data = await fetcher(url)
        return {"data": data, "error": None}
    except ScrapeError as exc:
        return {"data": None, "error": str(exc)}
    except Exception as exc:  # noqa: BLE001
        logger.exception("fetch failed for %s", url)
        return {"data": None, "error": f"{type(exc).__name__}: {exc}"}


async def prewarm_cache(person_id: int) -> None:
    """If a URL already has a cached scrape, adopt it without hitting Apify."""
    person = await _get_person(person_id)
    if person is None:
        return
    if person.linkedin_data is None:
        cached = read_cache(person.linkedin_url)
        if cached is not None:
            person.linkedin_data = cached
    if person.instagram_data is None:
        cached = read_cache(person.instagram_url)
        if cached is not None:
            person.instagram_data = cached
    if person.linkedin_data is not None and person.instagram_data is not None:
        person.status = PersonStatus.SCRAPED
    await _commit(person)


async def store_raw(url: str, data: dict) -> None:
    write_cache(url, data)


async def _fail(person_id: int, error: str) -> None:
    person = await _get_person(person_id)
    if person is None:
        return
    person.status = PersonStatus.FAILED
    person.error = error
    await _commit(person)
    emit("person.status", person_id=person.id, name=person.name, status=person.status, error=error)


async def _get_person(person_id: int) -> Person | None:
    factory = get_session_factory()
    async with factory() as session:
        return await session.get(Person, person_id)


async def _commit(person: Person) -> None:
    factory = get_session_factory()
    async with factory() as session:
        merged = await session.merge(person)
        await session.commit()
        await session.refresh(merged)


async def list_person_ids() -> list[int]:
    factory = get_session_factory()
    async with factory() as session:
        rows = (await session.execute(select(Person.id).order_by(Person.id))).scalars().all()
        return list(rows)


async def resume_queued_people(include_failed: bool = False) -> list[int]:
    factory = get_session_factory()
    statuses = [PersonStatus.QUEUED, PersonStatus.SCRAPING]
    if include_failed:
        statuses.append(PersonStatus.FAILED)
    async with factory() as session:
        rows = (
            await session.execute(
                select(Person.id).where(Person.status.in_(statuses)).order_by(Person.id)
            )
        ).scalars().all()
        pids = list(rows)
    for pid in pids:
        asyncio.create_task(process_person(pid))
    return pids
