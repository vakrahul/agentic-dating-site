"""Run the full dating pipeline and compute rankings for all analyzed candidates."""
import asyncio
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.db import init_db, get_session_factory
from app.models import Run, RunStatus
from app.dating.engine import _run_dating


async def main():
    print("Initializing DB...")
    await init_db()
    
    factory = get_session_factory()
    async with factory() as session:
        # Mark previous running runs as failed
        from sqlalchemy import select
        stale = (await session.execute(select(Run).where(Run.status == RunStatus.RUNNING))).scalars().all()
        for r in stale:
            r.status = RunStatus.FAILED
            r.error = "Superceded by fresh run"
        
        # Create fresh run
        run = Run(status=RunStatus.RUNNING, stats={"phase": "starting", "done": 0, "total": 0})
        session.add(run)
        await session.commit()
        await session.refresh(run)
        run_id = run.id
        print(f"Created fresh Run {run_id}")

    t0 = time.time()
    print("Executing dating simulation and rankings...")
    await _run_dating(run_id, excluded=[])
    
    async with factory() as session:
        completed_run = await session.get(Run, run_id)
        print(f"Run {run_id} status: {completed_run.status}")
        print(f"Total time: {time.time() - t0:.1f}s")
        print(f"Stats: {completed_run.stats}")


if __name__ == "__main__":
    asyncio.run(main())
