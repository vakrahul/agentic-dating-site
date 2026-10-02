"""Export the current DB to demo_run.json (repo root + web/public).

Run after a completed dating run:
  python scripts/export_demo.py
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.db import init_db  # noqa: E402
from app.api.transfer import export_run  # noqa: E402


async def main() -> None:
    await init_db()
    data = await export_run()

    if not data.people:
        print("database is empty; run the pipeline first (seed.py, then start a run)")
        sys.exit(1)
    if not data.dates:
        print("no dates in database; start a dating run first")
        sys.exit(1)

    payload = json.loads(data.model_dump_json())
    for target in (ROOT / "demo_run.json", ROOT / "web" / "public" / "demo_run.json"):
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"wrote {target}")

    runs = [r for r in payload["runs"] if r.get("status") == "completed"]
    print(
        f"summary: {len(payload['people'])} people, {len(runs)} completed runs, "
        f"{len(payload['dates'])} dates, {len(payload['pair_scores'])} pair scores"
    )


if __name__ == "__main__":
    asyncio.run(main())
