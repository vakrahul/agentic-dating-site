"""Seed people from seed.json and kick off the scrape+analysis pipeline.

seed.json format:
  [{"name": "...", "linkedin_url": "...", "instagram_url": "..."}, ...]
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.db import init_db  # noqa: E402
from app.api.people import create_people  # noqa: E402
from app.schemas import PeopleBatchRequest, PairInput  # noqa: E402


async def main() -> None:
    seed_path = ROOT / "seed.json"
    if not seed_path.exists():
        print(f"seed.json not found at {seed_path}")
        print('Expected: [{"name": "...", "linkedin_url": "...", "instagram_url": "..."}, ...]')
        sys.exit(1)

    rows = json.loads(seed_path.read_text(encoding="utf-8"))
    if not rows:
        print("seed.json is empty")
        sys.exit(1)

    await init_db()

    people = [
        PairInput(
            name=r.get("name"),
            linkedin_url=r["linkedin_url"],
            instagram_url=r["instagram_url"],
        )
        for r in rows
    ]

    result = await create_people(PeopleBatchRequest(people=people))
    print(f"seeded {result['count']} people; scrape+analysis tasks started")
    print("watch progress at http://localhost:3000 (SSE: /api/run/stream)")


if __name__ == "__main__":
    asyncio.run(main())
