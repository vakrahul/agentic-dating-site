from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import delete, select

from ..db import get_session_factory
from ..models import AgentScore, Date, DateStatus, PairScore, Person, RefereeScore
from ..scoring.composite import (
    final_score,
    geometric_mean,
    referee_mean,
    rescale_embeddings,
    score_breakdown,
)
from ..scoring.embeddings import cosine
from ..scoring.normalize import z_normalize

logger = logging.getLogger(__name__)


async def compute_pair_scores(
    *,
    run_id: int,
    people: list[Person],
    payloads: dict[int, dict],
    embeddings: dict[int, list[float]],
) -> list[dict[str, Any]]:
    """Compute final scores for every pair.

    Round 2 overrides Round 1 for the pairs that got a second date.
    Self-scores are z-normalized per agent before any cross-agent math.
    """
    used = await _load_used_dates(run_id)
    if not used:
        return []

    names = {p.id: p.name for p in people}
    scores_by_agent: dict[int, dict[int, float]] = {}
    for key, date_data in used.items():
        a, b = key
        for pid in (a, b):
            raw = date_data["scores"].get(pid)
            if raw is None:
                continue
            scores_by_agent.setdefault(pid, {})[b if pid == a else a] = raw

    norm_by_agent: dict[int, dict[int, float]] = {}
    for pid, partner_scores in scores_by_agent.items():
        values = list(partner_scores.values())
        scaled = z_normalize(values)
        norm_by_agent[pid] = dict(zip(partner_scores.keys(), scaled))

    candidates: list[dict[str, Any]] = []
    for key, date_data in used.items():
        a, b = key
        norm_a = norm_by_agent.get(a, {}).get(b)
        norm_b = norm_by_agent.get(b, {}).get(a)
        if norm_a is None or norm_b is None:
            logger.warning("missing normalized scores for pair %s", key)
            continue
        emb_a = embeddings.get(a)
        emb_b = embeddings.get(b)
        if not emb_a or not emb_b:
            logger.warning("missing embeddings for pair %s", key)
            continue
        referee_dims = {
            "chemistry": date_data["referee"]["chemistry"],
            "values_fit": date_data["referee"]["values_fit"],
            "lifestyle_fit": date_data["referee"]["lifestyle_fit"],
            "ambition_fit": date_data["referee"]["ambition_fit"],
            "interests_fit": date_data["referee"]["interests_fit"],
        }
        candidates.append(
            {
                "person_a": a,
                "person_b": b,
                "name_a": names.get(a, ""),
                "name_b": names.get(b, ""),
                "date_id": date_data["date_id"],
                "round_used": date_data["round"],
                "mutual": geometric_mean(norm_a, norm_b),
                "referee": referee_mean(referee_dims),
                "breakdown": score_breakdown(referee_dims),
                "tagged_turns": date_data["referee"].get("tagged_turns") or [],
                "cosine": cosine(emb_a, emb_b),
            }
        )

    if not candidates:
        return []

    rescaled = rescale_embeddings([c["cosine"] for c in candidates])
    for candidate, emb_score in zip(candidates, rescaled):
        candidate["embedding"] = emb_score
        candidate["final"] = final_score(
            candidate["mutual"], candidate["referee"], candidate["embedding"]
        )
        candidate["why"] = None
        del candidate["cosine"]

    candidates.sort(key=lambda c: (-c["final"], c["person_a"], c["person_b"]))
    return candidates


async def _load_used_dates(run_id: int) -> dict[tuple[int, int], dict[str, Any]]:
    factory = get_session_factory()
    async with factory() as session:
        dates = (
            (
                await session.execute(
                    select(Date)
                    .where(Date.run_id == run_id, Date.status == DateStatus.DONE)
                    .order_by(Date.round, Date.id)
                )
            )
            .scalars()
            .all()
        )
        if not dates:
            return {}
        date_ids = [d.id for d in dates]
        score_rows = (
            (
                await session.execute(
                    select(AgentScore).where(AgentScore.date_id.in_(date_ids))
                )
            )
            .scalars()
            .all()
        )
        referee_rows = (
            (
                await session.execute(
                    select(RefereeScore).where(RefereeScore.date_id.in_(date_ids))
                )
            )
            .scalars()
            .all()
        )

    scores_by_date: dict[int, dict[int, float]] = {}
    for score in score_rows:
        scores_by_date.setdefault(score.date_id, {})[score.person_id] = float(score.score)
    referees_by_date = {r.date_id: r for r in referee_rows}

    used: dict[tuple[int, int], dict[str, Any]] = {}
    for date in dates:
        scores = scores_by_date.get(date.id)
        referee = referees_by_date.get(date.id)
        if not scores or referee is None or len(scores) < 2:
            continue
        key = tuple(sorted((date.person_a, date.person_b)))
        if date.round == 1 and key in used:
            continue
        used[key] = {
            "date_id": date.id,
            "round": date.round,
            "scores": scores,
            "referee": {
                "chemistry": referee.chemistry,
                "values_fit": referee.values_fit,
                "lifestyle_fit": referee.lifestyle_fit,
                "ambition_fit": referee.ambition_fit,
                "interests_fit": referee.interests_fit,
                "tagged_turns": referee.tagged_turns or [],
            },
        }
    return used


async def persist_pair_scores(run_id: int, rows: list[dict[str, Any]]) -> None:
    factory = get_session_factory()
    async with factory() as session:
        await session.execute(delete(PairScore).where(PairScore.run_id == run_id))
        for row in rows:
            session.add(
                PairScore(
                    run_id=run_id,
                    person_a=row["person_a"],
                    person_b=row["person_b"],
                    date_id=row.get("date_id"),
                    round_used=row["round_used"],
                    mutual=row["mutual"],
                    referee=row["referee"],
                    embedding=row["embedding"],
                    final=row["final"],
                    why=row.get("why"),
                )
            )
        await session.commit()
