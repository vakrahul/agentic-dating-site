from __future__ import annotations

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from ..db import get_session_factory
from ..models import PairScore, Person, PersonStatus, RefereeScore, Run, RunStatus
from ..scoring.composite import score_breakdown
from ..scoring.ranks import link_badge_turn, match_ranks
from ..schemas import MatchOut, PersonOut, RankingOut, RankingsOverviewOut

router = APIRouter()


async def _latest_run():
    factory = get_session_factory()
    async with factory() as session:
        completed = (
            (
                await session.execute(
                    select(Run)
                    .where(Run.status == RunStatus.COMPLETED)
                    .order_by(Run.id.desc())
                    .limit(1)
                )
            )
            .scalars()
            .first()
        )
        if completed is not None:
            return completed, True
        latest = (
            await session.execute(select(Run).order_by(Run.id.desc()).limit(1))
        ).scalars().first()
        return latest, False


@router.get("/rankings", response_model=RankingsOverviewOut)
async def rankings_overview() -> RankingsOverviewOut:
    factory = get_session_factory()
    async with factory() as session:
        people = (
            (
                await session.execute(
                    select(Person)
                    .where(Person.status == PersonStatus.ANALYZED)
                    .order_by(Person.name)
                )
            )
            .scalars()
            .all()
        )
    run, _completed = await _latest_run()
    return RankingsOverviewOut(
        people=[
            PersonOut(
                id=p.id,
                name=p.name,
                linkedin_url=p.linkedin_url,
                instagram_url=p.instagram_url,
                status=p.status,
                error=p.error,
                has_analysis=True,
            )
            for p in people
        ],
        run_id=run.id if run is not None else None,
    )


@router.get("/rankings/{person_id}", response_model=RankingOut)
async def person_ranking(person_id: int) -> RankingOut:
    factory = get_session_factory()
    async with factory() as session:
        person = await session.get(Person, person_id)
        if person is None:
            raise HTTPException(status_code=404, detail="Person not found")

        run, completed = await _latest_run()
        person_out = PersonOut(
            id=person.id,
            name=person.name,
            linkedin_url=person.linkedin_url,
            instagram_url=person.instagram_url,
            status=person.status,
            error=person.error,
            has_analysis=person.status == PersonStatus.ANALYZED,
        )
        if run is None:
            return RankingOut(person=person_out, run_id=None, matches=[], excluded=[])

        pairs = (
            (
                await session.execute(
                    select(PairScore)
                    .where(
                        PairScore.run_id == run.id,
                        (PairScore.person_a == person_id) | (PairScore.person_b == person_id),
                    )
                )
            )
            .scalars()
            .all()
        )
        if not pairs:
            excluded = (run.stats or {}).get("excluded", []) if run else []
            return RankingOut(
                person=person_out, run_id=run.id, matches=[], excluded=excluded
            )

        partner_ids = [
            p.person_b if p.person_a == person_id else p.person_a for p in pairs
        ]
        partners = {
            p.id: p
            for p in (
                (await session.execute(select(Person).where(Person.id.in_(partner_ids))))
                .scalars()
                .all()
            )
        }
        date_ids = [p.date_id for p in pairs]
        referees = {
            r.date_id: r
            for r in (
                (await session.execute(select(RefereeScore).where(RefereeScore.date_id.in_(date_ids))))
                .scalars()
                .all()
            )
        }

    partner_rows = []
    for pair in pairs:
        pid = pair.person_b if pair.person_a == person_id else pair.person_a
        partner_rows.append(
            {
                "person_id": pid,
                "embedding": pair.embedding,
                "final": pair.final,
                "mutual": pair.mutual,
                "referee": pair.referee,
                "round_used": pair.round_used,
                "date_id": pair.date_id,
                "why": pair.why,
            }
        )

    ranked = match_ranks(partner_rows)

    matches: list[MatchOut] = []
    for row in ranked:
        referee = referees.get(row["date_id"])
        breakdown = (
            score_breakdown(
                {
                    "chemistry": referee.chemistry,
                    "values_fit": referee.values_fit,
                    "lifestyle_fit": referee.lifestyle_fit,
                    "ambition_fit": referee.ambition_fit,
                    "interests_fit": referee.interests_fit,
                }
            )
            if referee
            else {"values": 0, "interests": 0, "lifestyle": 0, "ambition": 0, "chemistry": 0}
        )
        badge = row.get("badge")
        badge_link = link_badge_turn((referee.tagged_turns if referee else []) or [], badge)
        partner = partners.get(row["person_id"])
        partner_name = partner.name if partner else f"Person {row['person_id']}"
        matches.append(
            MatchOut(
                person_id=row["person_id"],
                person_name=partner_name,
                round_used=row["round_used"],
                final=row["final"],
                mutual=row["mutual"],
                referee=row["referee"],
                embedding=row["embedding"],
                breakdown=breakdown,
                why=row.get("why"),
                similarity_rank=row["similarity_rank"],
                final_rank=row["final_rank"],
                delta=row["delta"],
                badge=badge,
                badge_turn_link=badge_link,
                pair_href=f"/pair/{person_id}/{row['person_id']}",
                date_id=row["date_id"],
            )
        )

    excluded = ((run.stats or {}).get("excluded") if run else []) or []
    return RankingOut(
        person=person_out, run_id=run.id, matches=matches, excluded=excluded
    )
