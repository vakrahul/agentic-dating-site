"""Update existing dates in proxy.db with natural persona-grounded conversations."""
import asyncio
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.db import init_db, get_session_factory
from app.models import Date, Turn, AgentScore, RefereeScore, Person, Analysis
from app.dating.dialogue_synthesizer import synthesize_persona_date


async def main():
    await init_db()
    factory = get_session_factory()
    
    async with factory() as session:
        from sqlalchemy import select
        people = {p.id: p for p in (await session.execute(select(Person))).scalars().all()}
        analyses = {a.person_id: a.payload for a in (await session.execute(select(Analysis))).scalars().all()}
        dates = (await session.execute(select(Date).order_by(Date.id))).scalars().all()
        print(f"Enriching {len(dates)} dates...")
        
        for d in dates:
            p_a = people.get(d.person_a)
            p_b = people.get(d.person_b)
            if not p_a or not p_b:
                continue
            
            payload_a = analyses.get(d.person_a, {})
            payload_b = analyses.get(d.person_b, {})
            
            unified = synthesize_persona_date(
                name_a=p_a.name,
                payload_a=payload_a,
                name_b=p_b.name,
                payload_b=payload_b,
                scene=d.scene or "a quiet speakeasy",
                round_no=d.round,
                moderator_question=d.moderator_question,
            )
            
            # Delete old turns
            old_turns = (await session.execute(select(Turn).where(Turn.date_id == d.id))).scalars().all()
            for t in old_turns:
                await session.delete(t)
            
            # Delete old scores
            old_scores = (await session.execute(select(AgentScore).where(AgentScore.date_id == d.id))).scalars().all()
            for s in old_scores:
                await session.delete(s)
                
            old_ref = await session.get(RefereeScore, d.id)
            if old_ref:
                await session.delete(old_ref)
                
            await session.flush()
            
            # Add new turns
            for idx, t in enumerate(unified.turns):
                spk = d.person_a if idx % 2 == 0 else d.person_b
                session.add(Turn(date_id=d.id, idx=idx, speaker_id=spk, content=t.content))
                
            session.add(
                AgentScore(
                    date_id=d.id,
                    person_id=d.person_a,
                    score=unified.score_a.score,
                    chemistry=unified.score_a.chemistry,
                    shared_interests=unified.score_a.shared_interests,
                    friction=unified.score_a.friction,
                    would_meet_again=unified.score_a.would_meet_again,
                    one_line_for_person=unified.score_a.one_line_for_person,
                )
            )
            session.add(
                AgentScore(
                    date_id=d.id,
                    person_id=d.person_b,
                    score=unified.score_b.score,
                    chemistry=unified.score_b.chemistry,
                    shared_interests=unified.score_b.shared_interests,
                    friction=unified.score_b.friction,
                    would_meet_again=unified.score_b.would_meet_again,
                    one_line_for_person=unified.score_b.one_line_for_person,
                )
            )
            
            tagged = [
                {"turn_index": tag.turn_index, "tag": tag.tag, "reason": tag.reason}
                for tag in unified.referee.tagged_turns
            ]
            session.add(
                RefereeScore(
                    date_id=d.id,
                    chemistry=unified.referee.chemistry,
                    values_fit=unified.referee.values_fit,
                    lifestyle_fit=unified.referee.lifestyle_fit,
                    ambition_fit=unified.referee.ambition_fit,
                    interests_fit=unified.referee.interests_fit,
                    tagged_turns=tagged,
                )
            )
            
        await session.commit()
        print("All dates enriched successfully!")


if __name__ == "__main__":
    asyncio.run(main())
