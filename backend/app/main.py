from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_settings()
    await init_db()
    await _fail_stale_runs()
    from .scoring.embeddings import warmup

    warmup()

    from .pipeline import resume_queued_people

    await resume_queued_people(include_failed=True)
    yield


async def _fail_stale_runs() -> None:
    """Mark runs interrupted by a restart as failed so POST /api/run can start fresh."""
    from sqlalchemy import select

    from .db import get_session_factory
    from .models import Run, RunStatus

    factory = get_session_factory()
    async with factory() as session:
        stale = (
            (await session.execute(select(Run).where(Run.status == RunStatus.RUNNING)))
            .scalars()
            .all()
        )
        for run in stale:
            run.status = RunStatus.FAILED
            run.error = "Interrupted by server restart"
        if stale:
            await session.commit()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Proxy", version="1.0.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from .api import people, rankings, run, transfer, pair

    app.include_router(people.router, prefix="/api", tags=["people"])
    app.include_router(run.router, prefix="/api", tags=["run"])
    app.include_router(pair.router, prefix="/api", tags=["pair"])
    app.include_router(rankings.router, prefix="/api", tags=["rankings"])
    app.include_router(transfer.router, prefix="/api", tags=["transfer"])

    @app.get("/health")
    async def health() -> dict:
        settings = get_settings()
        return {
            "status": "ok",
            "provider": settings.llm_provider,
            "model": settings.resolved_model,
            "base_url": settings.resolved_base_url,
        }

    return app


app = create_app()
