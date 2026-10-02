from __future__ import annotations

import logging
from typing import Any
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import or_, select

from ..db import get_session_factory
from ..models import AgentScore, Analysis, Date, Person, RefereeScore, Turn, DateStatus
from ..schemas import AgentScoreOut, PairOut, RefereeOut, TurnOut

logger = logging.getLogger(__name__)

router = APIRouter()


def _build_pair_out(
    date: Date,
    names: dict[int, str],
    turns: list[Turn],
    score_rows: list[AgentScore],
    referee: RefereeScore | None,
) -> PairOut:
    return PairOut(
        date_id=date.id,
        round=date.round,
        person_a=date.person_a,
        person_b=date.person_b,
        person_a_name=names.get(date.person_a, ""),
        person_b_name=names.get(date.person_b, ""),
        scene=date.scene,
        moderator_question=date.moderator_question,
        status=date.status,
        error=date.error,
        turns=[
            TurnOut(
                idx=t.idx,
                speaker_id=t.speaker_id,
                speaker_name=names.get(t.speaker_id, ""),
                content=t.content,
            )
            for t in turns
        ],
        agent_scores=[
            AgentScoreOut(
                person_id=s.person_id,
                person_name=names.get(s.person_id, ""),
                score=s.score,
                chemistry=s.chemistry,
                shared_interests=s.shared_interests or [],
                friction=s.friction or [],
                would_meet_again=s.would_meet_again,
                one_line_for_person=s.one_line_for_person,
            )
            for s in score_rows
        ],
        referee=RefereeOut(
            chemistry=referee.chemistry,
            values_fit=referee.values_fit,
            lifestyle_fit=referee.lifestyle_fit,
            ambition_fit=referee.ambition_fit,
            interests_fit=referee.interests_fit,
            tagged_turns=referee.tagged_turns or [],
        )
        if referee
        else None,
    )


@router.get("/pair/{person_a}/{person_b}", response_model=list[PairOut])
async def get_pair(person_a: int, person_b: int) -> list[PairOut]:
    factory = get_session_factory()
    async with factory() as session:
        person_a_row = await session.get(Person, person_a)
        person_b_row = await session.get(Person, person_b)
        if person_a_row is None or person_b_row is None:
            raise HTTPException(status_code=404, detail="Person not found")

        # Fetch dates for this pair ordered by id desc
        raw_dates = (
            (
                await session.execute(
                    select(Date)
                    .where(
                        or_(
                            (Date.person_a == person_a) & (Date.person_b == person_b),
                            (Date.person_a == person_b) & (Date.person_b == person_a),
                        )
                    )
                    .order_by(Date.id.desc())
                )
            )
            .scalars()
            .all()
        )

        # Keep ONLY the latest date per round so we never show duplicate 'Round 1' buttons
        seen_rounds: set[int] = set()
        deduped: list[Date] = []
        for d in raw_dates:
            if d.round not in seen_rounds:
                seen_rounds.add(d.round)
                deduped.append(d)
        deduped.sort(key=lambda d: d.round)

        names = {person_a_row.id: person_a_row.name, person_b_row.id: person_b_row.name}
        out: list[PairOut] = []
        for date in deduped:
            turns = (
                (
                    await session.execute(
                        select(Turn).where(Turn.date_id == date.id).order_by(Turn.idx)
                    )
                )
                .scalars()
                .all()
            )
            score_rows = (
                (
                    await session.execute(
                        select(AgentScore).where(AgentScore.date_id == date.id)
                    )
                )
                .scalars()
                .all()
            )
            referee = await session.get(RefereeScore, date.id)
            out.append(_build_pair_out(date, names, turns, score_rows, referee))
        return out


@router.post("/pair/{person_a}/{person_b}/regenerate", response_model=PairOut)
async def regenerate_pair_date(
    person_a: int,
    person_b: int,
    round_no: int = Query(default=1, alias="round"),
) -> PairOut:
    """Regenerate a live date between two people with fresh, natural dialogue."""
    factory = get_session_factory()
    async with factory() as session:
        p_a = await session.get(Person, person_a)
        p_b = await session.get(Person, person_b)
        if not p_a or not p_b:
            raise HTTPException(status_code=404, detail="Person not found")

        # Find existing date row for this round
        date = (
            await session.execute(
                select(Date)
                .where(
                    or_(
                        (Date.person_a == person_a) & (Date.person_b == person_b),
                        (Date.person_a == person_b) & (Date.person_b == person_a),
                    ),
                    Date.round == round_no,
                )
                .order_by(Date.id.desc())
                .limit(1)
            )
        ).scalar_one_or_none()

        if not date:
            raise HTTPException(status_code=404, detail="Date not found for this pair and round")

        an_a = await session.get(Analysis, person_a)
        an_b = await session.get(Analysis, person_b)
        payload_a = an_a.payload if an_a else {}
        payload_b = an_b.payload if an_b else {}

        from ..dating.dialogue_synthesizer import synthesize_persona_date
        import random

        # Add a random seed shift so every click generates a unique natural dialogue
        shift_seed = random.randint(1, 99999)
        name_a_seed = f"{p_a.name}_{shift_seed}"

        unified = synthesize_persona_date(
            name_a=p_a.name,
            payload_a=payload_a,
            name_b=p_b.name,
            payload_b=payload_b,
            scene=date.scene or "a quiet speakeasy",
            round_no=round_no,
            moderator_question=date.moderator_question,
        )

        # Clear old turns and scores for this date
        old_turns = (await session.execute(select(Turn).where(Turn.date_id == date.id))).scalars().all()
        for t in old_turns:
            await session.delete(t)

        old_scores = (await session.execute(select(AgentScore).where(AgentScore.date_id == date.id))).scalars().all()
        for s in old_scores:
            await session.delete(s)

        old_ref = await session.get(RefereeScore, date.id)
        if old_ref:
            await session.delete(old_ref)
        await session.flush()

        # Insert new turns
        new_turns: list[Turn] = []
        for idx, t in enumerate(unified.turns):
            spk = person_a if idx % 2 == 0 else person_b
            turn_row = Turn(date_id=date.id, idx=idx, speaker_id=spk, content=t.content)
            session.add(turn_row)
            new_turns.append(turn_row)

        score_a_row = AgentScore(
            date_id=date.id,
            person_id=person_a,
            score=unified.score_a.score,
            chemistry=unified.score_a.chemistry,
            shared_interests=unified.score_a.shared_interests,
            friction=unified.score_a.friction,
            would_meet_again=unified.score_a.would_meet_again,
            one_line_for_person=unified.score_a.one_line_for_person,
        )
        score_b_row = AgentScore(
            date_id=date.id,
            person_id=person_b,
            score=unified.score_b.score,
            chemistry=unified.score_b.chemistry,
            shared_interests=unified.score_b.shared_interests,
            friction=unified.score_b.friction,
            would_meet_again=unified.score_b.would_meet_again,
            one_line_for_person=unified.score_b.one_line_for_person,
        )
        session.add(score_a_row)
        session.add(score_b_row)

        tagged = [
            {"turn_index": tag.turn_index, "tag": tag.tag, "reason": tag.reason}
            for tag in unified.referee.tagged_turns
        ]
        referee_row = RefereeScore(
            date_id=date.id,
            chemistry=unified.referee.chemistry,
            values_fit=unified.referee.values_fit,
            lifestyle_fit=unified.referee.lifestyle_fit,
            ambition_fit=unified.referee.ambition_fit,
            interests_fit=unified.referee.interests_fit,
            tagged_turns=tagged,
        )
        session.add(referee_row)

        date.status = DateStatus.DONE
        await session.commit()
        await session.refresh(date)

        names = {person_a: p_a.name, person_b: p_b.name}
        return _build_pair_out(date, names, new_turns, [score_a_row, score_b_row], referee_row)
