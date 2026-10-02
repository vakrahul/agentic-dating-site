from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from ..db import get_session_factory
from ..models import (
    AgentScore,
    Analysis,
    Date,
    PairScore,
    Person,
    RefereeScore,
    Run,
    Turn,
)
from ..schemas import ExportOut, ImportRequest

router = APIRouter()

EXPORT_VERSION = 1


def _parse_dt(value: object) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
    return None


@router.get("/export", response_model=ExportOut)
async def export_run() -> ExportOut:
    factory = get_session_factory()
    async with factory() as session:
        people = (await session.execute(select(Person).order_by(Person.id))).scalars().all()
        analyses = (await session.execute(select(Analysis))).scalars().all()
        runs = (await session.execute(select(Run).order_by(Run.id))).scalars().all()
        dates = (await session.execute(select(Date).order_by(Date.id))).scalars().all()
        turns = (await session.execute(select(Turn).order_by(Turn.id))).scalars().all()
        agent_scores = (await session.execute(select(AgentScore))).scalars().all()
        referee_scores = (await session.execute(select(RefereeScore))).scalars().all()
        pair_scores = (await session.execute(select(PairScore))).scalars().all()

        return ExportOut(
            version=EXPORT_VERSION,
            exported_at=datetime.now(timezone.utc),
            people=[
                {
                    "id": p.id,
                    "name": p.name,
                    "linkedin_url": p.linkedin_url,
                    "instagram_url": p.instagram_url,
                    "status": p.status,
                    "error": p.error,
                    "linkedin_data": p.linkedin_data,
                    "instagram_data": p.instagram_data,
                    "created_at": p.created_at,
                }
                for p in people
            ],
            analyses=[
                {
                    "person_id": a.person_id,
                    "payload": a.payload,
                    "embedding": a.embedding,
                    "overall_confidence": a.overall_confidence,
                    "verified_count": a.verified_count,
                    "dropped_count": a.dropped_count,
                    "dropped": a.dropped,
                }
                for a in analyses
            ],
            runs=[
                {
                    "id": r.id,
                    "status": r.status,
                    "error": r.error,
                    "stats": r.stats,
                    "started_at": r.started_at,
                    "finished_at": r.finished_at,
                }
                for r in runs
            ],
            dates=[
                {
                    "id": d.id,
                    "run_id": d.run_id,
                    "round": d.round,
                    "person_a": d.person_a,
                    "person_b": d.person_b,
                    "scene": d.scene,
                    "moderator_question": d.moderator_question,
                    "status": d.status,
                    "error": d.error,
                }
                for d in dates
            ],
            turns=[
                {"id": t.id, "date_id": t.date_id, "idx": t.idx,
                 "speaker_id": t.speaker_id, "content": t.content}
                for t in turns
            ],
            agent_scores=[
                {"id": s.id, "date_id": s.date_id, "person_id": s.person_id,
                 "score": s.score, "chemistry": s.chemistry,
                 "shared_interests": s.shared_interests, "friction": s.friction,
                 "would_meet_again": s.would_meet_again,
                 "one_line_for_person": s.one_line_for_person}
                for s in agent_scores
            ],
            referee_scores=[
                {"date_id": r.date_id, "chemistry": r.chemistry,
                 "values_fit": r.values_fit, "lifestyle_fit": r.lifestyle_fit,
                 "ambition_fit": r.ambition_fit, "interests_fit": r.interests_fit,
                 "tagged_turns": r.tagged_turns}
                for r in referee_scores
            ],
            pair_scores=[
                {"id": ps.id, "run_id": ps.run_id, "person_a": ps.person_a,
                 "person_b": ps.person_b, "date_id": ps.date_id,
                 "round_used": ps.round_used,
                 "mutual": ps.mutual, "referee": ps.referee,
                 "embedding": ps.embedding, "final": ps.final, "why": ps.why}
                for ps in pair_scores
            ],
        )


@router.post("/import", response_model=dict)
async def import_run(request: ImportRequest) -> dict:
    data = request.data
    factory = get_session_factory()

    async with factory() as session:
        person_map: dict[int, int] = {}
        people_count = 0
        for p in data.people:
            existing = (
                await session.execute(
                    select(Person).where(Person.linkedin_url == p["linkedin_url"])
                )
            ).scalars().first()
            if existing is not None:
                person_map[p["id"]] = existing.id
                existing.name = p.get("name") or existing.name
                existing.instagram_url = p.get("instagram_url") or existing.instagram_url
                existing.status = p.get("status") or existing.status
                existing.error = p.get("error")
                if p.get("linkedin_data"):
                    existing.linkedin_data = p["linkedin_data"]
                if p.get("instagram_data"):
                    existing.instagram_data = p["instagram_data"]
            else:
                person = Person(
                    name=p.get("name") or "Unnamed",
                    linkedin_url=p["linkedin_url"],
                    instagram_url=p["instagram_url"],
                    status=p.get("status") or "queued",
                    error=p.get("error"),
                    linkedin_data=p.get("linkedin_data"),
                    instagram_data=p.get("instagram_data"),
                )
                session.add(person)
                await session.flush()
                person_map[p["id"]] = person.id
            people_count += 1

        analyses_count = 0
        for a in data.analyses:
            new_pid = person_map.get(a["person_id"])
            if new_pid is None:
                continue
            existing = await session.get(Analysis, new_pid)
            payload = {
                "person_id": new_pid,
                "payload": a["payload"],
                "embedding": a.get("embedding"),
                "overall_confidence": a.get("overall_confidence") or 0.0,
                "verified_count": a.get("verified_count") or 0,
                "dropped_count": a.get("dropped_count") or 0,
                "dropped": a.get("dropped") or [],
            }
            if existing is not None:
                for key, value in payload.items():
                    setattr(existing, key, value)
            else:
                session.add(Analysis(**payload))
            analyses_count += 1

        run_map: dict[int, int] = {}
        runs_count = 0
        for r in data.runs:
            started_at = _parse_dt(r["started_at"])
            existing = (
                await session.execute(
                    select(Run).where(
                        Run.started_at == started_at
                        if started_at is not None
                        else Run.id.is_(None)
                    )
                )
            ).scalars().first()
            if existing is not None:
                run_map[r["id"]] = existing.id
            else:
                run = Run(
                    status=r.get("status") or "completed",
                    error=r.get("error"),
                    stats=r.get("stats"),
                    started_at=started_at,
                    finished_at=_parse_dt(r.get("finished_at")),
                )
                session.add(run)
                await session.flush()
                run_map[r["id"]] = run.id
            runs_count += 1

        date_map: dict[int, int] = {}
        dates_count = 0
        for d in data.dates:
            new_run = run_map.get(d["run_id"])
            new_a = person_map.get(d["person_a"])
            new_b = person_map.get(d["person_b"])
            if new_run is None or new_a is None or new_b is None:
                continue
            existing = (
                await session.execute(
                    select(Date).where(
                        Date.run_id == new_run,
                        Date.round == d["round"],
                        Date.person_a == new_a,
                        Date.person_b == new_b,
                    )
                )
            ).scalars().first()
            if existing is not None:
                date_map[d["id"]] = existing.id
            else:
                date = Date(
                    run_id=new_run,
                    round=d["round"],
                    person_a=new_a,
                    person_b=new_b,
                    scene=d.get("scene"),
                    moderator_question=d.get("moderator_question"),
                    status=d.get("status") or "done",
                    error=d.get("error"),
                )
                session.add(date)
                await session.flush()
                date_map[d["id"]] = date.id
            dates_count += 1

        turns_count = 0
        for t in data.turns:
            new_date = date_map.get(t["date_id"])
            new_speaker = person_map.get(t["speaker_id"])
            if new_date is None or new_speaker is None:
                continue
            existing = (
                await session.execute(
                    select(Turn).where(Turn.date_id == new_date, Turn.idx == t["idx"])
                )
            ).scalars().first()
            if existing is not None:
                existing.content = t["content"]
                existing.speaker_id = new_speaker
            else:
                session.add(
                    Turn(
                        date_id=new_date,
                        idx=t["idx"],
                        speaker_id=new_speaker,
                        content=t["content"],
                    )
                )
            turns_count += 1

        scores_count = 0
        for s in data.agent_scores:
            new_date = date_map.get(s["date_id"])
            new_person = person_map.get(s["person_id"])
            if new_date is None or new_person is None:
                continue
            existing = (
                await session.execute(
                    select(AgentScore).where(
                        AgentScore.date_id == new_date, AgentScore.person_id == new_person
                    )
                )
            ).scalars().first()
            if existing is not None:
                existing.score = s["score"]
                existing.chemistry = s.get("chemistry") or 0.0
                existing.shared_interests = s.get("shared_interests")
                existing.friction = s.get("friction")
                existing.would_meet_again = bool(s.get("would_meet_again"))
                existing.one_line_for_person = s.get("one_line_for_person")
            else:
                session.add(
                    AgentScore(
                        date_id=new_date,
                        person_id=new_person,
                        score=s["score"],
                        chemistry=s.get("chemistry") or 0.0,
                        shared_interests=s.get("shared_interests"),
                        friction=s.get("friction"),
                        would_meet_again=bool(s.get("would_meet_again")),
                        one_line_for_person=s.get("one_line_for_person"),
                    )
                )
            scores_count += 1

        ref_count = 0
        for r in data.referee_scores:
            new_date = date_map.get(r["date_id"])
            if new_date is None:
                continue
            existing = await session.get(RefereeScore, new_date)
            if existing is not None:
                existing.chemistry = r["chemistry"]
                existing.values_fit = r["values_fit"]
                existing.lifestyle_fit = r["lifestyle_fit"]
                existing.ambition_fit = r["ambition_fit"]
                existing.interests_fit = r["interests_fit"]
                existing.tagged_turns = r.get("tagged_turns")
            else:
                session.add(
                    RefereeScore(
                        date_id=new_date,
                        chemistry=r["chemistry"],
                        values_fit=r["values_fit"],
                        lifestyle_fit=r["lifestyle_fit"],
                        ambition_fit=r["ambition_fit"],
                        interests_fit=r["interests_fit"],
                        tagged_turns=r.get("tagged_turns") or [],
                    )
                )
            ref_count += 1

        pairs_count = 0
        for ps in data.pair_scores:
            new_run = run_map.get(ps["run_id"])
            new_a = person_map.get(ps["person_a"])
            new_b = person_map.get(ps["person_b"])
            new_date = date_map.get(ps.get("date_id")) if ps.get("date_id") is not None else None
            if new_run is None or new_a is None or new_b is None:
                continue
            existing = (
                await session.execute(
                    select(PairScore).where(
                        PairScore.run_id == new_run,
                        PairScore.person_a == new_a,
                        PairScore.person_b == new_b,
                    )
                )
            ).scalars().first()
            if existing is not None:
                existing.mutual = ps["mutual"]
                existing.referee = ps["referee"]
                existing.embedding = ps["embedding"]
                existing.final = ps["final"]
                existing.round_used = ps.get("round_used") or 1
                existing.why = ps.get("why")
                if new_date is not None:
                    existing.date_id = new_date
            else:
                session.add(
                    PairScore(
                        run_id=new_run,
                        person_a=new_a,
                        person_b=new_b,
                        date_id=new_date,
                        round_used=ps.get("round_used") or 1,
                        mutual=ps["mutual"],
                        referee=ps["referee"],
                        embedding=ps["embedding"],
                        final=ps["final"],
                        why=ps.get("why"),
                    )
                )
            pairs_count += 1

        await session.commit()
        from ..events import emit

        emit("import.done", people=people_count, analyses=analyses_count, runs=runs_count)

    return {
        "imported": {
            "people": people_count,
            "analyses": analyses_count,
            "runs": runs_count,
            "dates": dates_count,
            "turns": turns_count,
            "agent_scores": scores_count,
            "referee_scores": ref_count,
            "pair_scores": pairs_count,
        },
        "idempotent": True,
    }
