from __future__ import annotations

from typing import Any

SURPRISE = "surprise_match"
FALSE_FRIEND = "false_friend"


def rank_desc(items: list[tuple[Any, float]]) -> dict[Any, int]:
    """1-based ranks by score descending; ties broken by key ascending."""
    ordered = sorted(items, key=lambda item: (-item[1], str(item[0])))
    return {key: index + 1 for index, (key, _) in enumerate(ordered)}


def match_ranks(
    partners: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Attach similarity_rank, final_rank and delta to each partner row.

    partners rows must carry: person_id, embedding, final.
    delta = similarity_rank - final_rank (positive means the date improved rank).
    """
    sim_ranks = rank_desc([(p["person_id"], p["embedding"]) for p in partners])
    final_ranks = rank_desc([(p["person_id"], p["final"]) for p in partners])
    out: list[dict[str, Any]] = []
    for partner in partners:
        pid = partner["person_id"]
        sim_rank = sim_ranks[pid]
        final_rank = final_ranks[pid]
        row = dict(partner)
        row["similarity_rank"] = sim_rank
        row["final_rank"] = final_rank
        row["delta"] = sim_rank - final_rank
        row["badge"] = badge_for(sim_rank, final_rank, len(partners))
        out.append(row)
    out.sort(key=lambda r: (r["final_rank"], str(r["person_id"])))
    return out


def badge_for(similarity_rank: int, final_rank: int, partner_count: int) -> str | None:
    bottom_half_start = partner_count // 2 + 1
    if similarity_rank >= bottom_half_start and final_rank <= 3:
        return SURPRISE
    if similarity_rank <= 3 and final_rank > 5:
        return FALSE_FRIEND
    return None


def link_badge_turn(
    tagged_turns: list[dict[str, Any]], badge: str | None
) -> dict[str, Any] | None:
    """Pick the highest-impact tagged turn for a badge.

    Surprise matches are driven by sparks, false friends by friction; if the
    preferred tag is absent, fall back to the earliest tagged turn.
    """
    if not badge or not tagged_turns:
        return None
    preferred = "spark" if badge == SURPRISE else "friction"
    candidates = [t for t in tagged_turns if isinstance(t, dict)]
    if not candidates:
        return None
    matching = [t for t in candidates if t.get("tag") == preferred]
    chosen = min(matching or candidates, key=lambda t: int(t.get("turn_index", 0)))
    return {
        "turn_index": int(chosen.get("turn_index", 0)),
        "tag": chosen.get("tag"),
        "reason": chosen.get("reason") or "",
    }
