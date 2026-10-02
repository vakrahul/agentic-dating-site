import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.db import init_db, get_session_factory
from app.models import Person, PersonStatus
from app.pipeline import process_person


async def test():
    await init_db()
    factory = get_session_factory()
    async with factory() as session:
        # Find person #4 (Jade Bonacolta, whose cache or profile we already tested)
        p = await session.get(Person, 4)
        if not p:
            print("Person #4 not found")
            return
        print(f"Starting pipeline for #{p.id} {p.name} (status={p.status})...")

    await process_person(4)

    async with factory() as session:
        p = await session.get(Person, 4)
        print(f"Finished #{p.id} {p.name}: status={p.status}, error={p.error}")
        if p.status == PersonStatus.ANALYZED:
            from app.models import Analysis
            a = await session.get(Analysis, 4)
            if a and a.payload:
                print("Needs:", a.payload.get("needs"))
                print("Hobbies:", a.payload.get("hobbies"))
                print("Interests:", a.payload.get("interests"))
                print("Qualities:", a.payload.get("qualities"))


if __name__ == "__main__":
    asyncio.run(test())
