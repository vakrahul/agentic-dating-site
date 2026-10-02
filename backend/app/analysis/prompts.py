ANALYSIS_SYSTEM_PROMPT = """You are Proxy's profile analysis agent. You receive ONLY two normalized sources: a public LinkedIn profile and a public Instagram profile for one person.

Rules:
- Use only the provided source text. Never use outside knowledge about this person. Never invent facts, jobs, places, events, or attributes.
- Every quote you output must be copied VERBATIM as an exact substring of the provided source text, preserving original spelling, spacing, and punctuation.
- Every claim must carry a source tag (linkedin, instagram, or both) and a confidence between 0 and 1.
- If a claim is your interpretation rather than something literally present, set kind to "inferred" and say so plainly.
- If a field has no support in the sources, return an empty list for it and add a short note about the missing support to data_gaps.
- Never infer protected attributes: religion, health, sexual orientation, ethnicity, or politics.
- Do not speculate about dating behavior beyond what the sources show; dating_intent and looking_for must be grounded in the sources or explicitly hedged with low confidence and a data gap note.
- say_do_gap compares what the person states (LinkedIn) against how they live (Instagram evidence). type is "agree" when both align and "diverge" when they conflict.
- overall_confidence reflects how much usable public material you were given.
- Keep lists focused: provide 3 to 6 high-signal items each for needs, hobbies, interests, values, and 4 to 8 key verifiable claims with concise quotes.

Respond with a single JSON object matching the schema given by the user."""


def build_analysis_messages(linkedin: dict, instagram: dict) -> list[dict]:
    import json

    li_block = {
        "name": linkedin.get("name"),
        "headline": linkedin.get("headline"),
        "about": linkedin.get("about"),
        "location": linkedin.get("location"),
        "experience": linkedin.get("experience"),
        "education": linkedin.get("education"),
        "skills": linkedin.get("skills"),
    }
    ig_block = {
        "username": instagram.get("username"),
        "full_name": instagram.get("full_name"),
        "biography": instagram.get("biography"),
        "followers": instagram.get("followers"),
        "post_count": instagram.get("post_count"),
        "category": instagram.get("category"),
        "external_url": instagram.get("external_url"),
        "captions": [
            {
                "caption": p.get("caption"),
                "hashtags": p.get("hashtags"),
                "taken_at": p.get("taken_at"),
            }
            for p in (instagram.get("latest_posts") or [])
        ],
    }
    user = (
        "Analyze this person from these two sources only.\n\n"
        "=== LINKEDIN SOURCE ===\n"
        + json.dumps(li_block, ensure_ascii=False, indent=2)
        + "\n\n=== INSTAGRAM SOURCE ===\n"
        + json.dumps(ig_block, ensure_ascii=False, indent=2)
        + "\n\nReturn one JSON object with exactly these keys:\n"
        '{"summary": str, "stated_self": {"career": str, "ambitions": [str], "presentation": str}, '
        '"lived_self": {"hobbies": [str], "places": [str], "social_energy": str, "aesthetic": str}, '
        '"say_do_gap": [{"stated": str, "lived": str, "type": "agree"|"diverge", '
        '"evidence": [{"source": "linkedin"|"instagram", "quote": str}]}], '
        '"needs": [str], "interests": [str], "values": [str], "personality": [str], '
        '"communication_style": str, "lifestyle": str, "ambition_level": str, '
        '"dating_intent": str, "looking_for": [str], "dealbreakers": [str], '
        '"claims": [{"claim": str, "source": "linkedin"|"instagram"|"both", "quote": str, '
        '"kind": "stated"|"inferred", "confidence": float}], '
        '"overall_confidence": float, "data_gaps": [str]}'
    )
    return [
        {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]
