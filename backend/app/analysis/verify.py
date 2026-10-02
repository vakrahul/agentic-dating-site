from __future__ import annotations

import re
import unicodedata


def normalize_text(text: str) -> str:
    decomposed = unicodedata.normalize("NFKC", text or "")
    collapsed = re.sub(r"\s+", " ", decomposed)
    return collapsed.strip().lower()


def is_substring(quote: str, source_text: str) -> bool:
    if not quote or not quote.strip():
        return False
    needle = normalize_text(quote)
    haystack = normalize_text(source_text)
    if not needle or not haystack:
        return False
    return needle in haystack


def verify_analysis(payload: dict, linkedin: dict, instagram: dict) -> tuple[dict, list[dict]]:
    """Verify every quote is a verbatim substring of its declared source.

    Returns (cleaned_payload, dropped_records). Claims and say_do_gap evidence
    that fail verification are dropped; failures are recorded and, when a gap
    loses all evidence, the gap is dropped too. Empty support is added to data_gaps.
    """
    li_text = _source_text(linkedin, "linkedin")
    ig_text = _source_text(instagram, "instagram")
    dropped: list[dict] = []

    claims_in = list(payload.get("claims") or [])
    claims_out: list[dict] = []
    for claim in claims_in:
        quote = claim.get("quote") or ""
        source = claim.get("source") or "both"
        if source == "linkedin":
            ok = is_substring(quote, li_text)
        elif source == "instagram":
            ok = is_substring(quote, ig_text)
        else:
            ok = is_substring(quote, li_text) or is_substring(quote, ig_text)
        if ok:
            claims_out.append(claim)
        else:
            dropped.append(
                {"kind": "claim", "claim": claim.get("claim"), "quote": quote, "source": source,
                 "reason": "quote not found verbatim in declared source"}
            )

    gaps_in = list(payload.get("say_do_gap") or [])
    gaps_out: list[dict] = []
    for gap in gaps_in:
        evidence_in = list(gap.get("evidence") or [])
        evidence_out: list[dict] = []
        for ev in evidence_in:
            src = ev.get("source") or "linkedin"
            text = li_text if src == "linkedin" else ig_text
            if is_substring(ev.get("quote") or "", text):
                evidence_out.append(ev)
            else:
                dropped.append(
                    {"kind": "say_do_gap_evidence", "stated": gap.get("stated"),
                     "quote": ev.get("quote"), "source": src,
                     "reason": "quote not found verbatim in declared source"}
                )
        if evidence_out:
            gap = dict(gap)
            gap["evidence"] = evidence_out
            gaps_out.append(gap)
        else:
            dropped.append(
                {"kind": "say_do_gap", "stated": gap.get("stated"), "lived": gap.get("lived"),
                 "reason": "no verifiable evidence remained"}
            )

    cleaned = dict(payload)
    cleaned["claims"] = claims_out
    cleaned["say_do_gap"] = gaps_out

    if dropped:
        gaps = list(cleaned.get("data_gaps") or [])
        gaps.append(
            f"{len(dropped)} quoted item(s) failed verbatim verification and were removed"
        )
        cleaned["data_gaps"] = gaps

    return cleaned, dropped


def _source_text(data: dict | None, source: str) -> str:
    if not data:
        return ""
    if source == "linkedin":
        parts: list[str] = [
            str(data.get("name") or ""),
            str(data.get("headline") or ""),
            str(data.get("about") or ""),
            str(data.get("location") or ""),
        ]
        for item in data.get("experience") or []:
            parts.extend(
                [str(item.get("title") or ""), str(item.get("company") or ""),
                 str(item.get("description") or ""), str(item.get("duration") or "")]
            )
        for item in data.get("education") or []:
            parts.extend([str(item.get("school") or ""), str(item.get("degree") or "")])
        parts.extend(str(s) for s in (data.get("skills") or []))
        return " \n ".join(p for p in parts if p)

    parts = [
        str(data.get("biography") or ""),
        str(data.get("full_name") or ""),
        str(data.get("username") or ""),
        str(data.get("category") or ""),
    ]
    for post in data.get("latest_posts") or []:
        parts.append(str(post.get("caption") or ""))
        parts.extend(str(h) for h in (post.get("hashtags") or []))
    return " \n ".join(p for p in parts if p)
