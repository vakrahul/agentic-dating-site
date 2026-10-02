from __future__ import annotations

import json


def persona_system_prompt(name: str, payload: dict) -> str:
    profile = {
        "summary": payload.get("summary"),
        "stated_self": payload.get("stated_self"),
        "lived_self": payload.get("lived_self"),
        "needs": payload.get("needs"),
        "interests": payload.get("interests"),
        "values": payload.get("values"),
        "personality": payload.get("personality"),
        "communication_style": payload.get("communication_style"),
        "lifestyle": payload.get("lifestyle"),
        "ambition_level": payload.get("ambition_level"),
        "dating_intent": payload.get("dating_intent"),
        "looking_for": payload.get("looking_for"),
        "dealbreakers": payload.get("dealbreakers"),
        "say_do_gap": payload.get("say_do_gap"),
    }
    return (
        f"You are {name}'s dating agent. You speak as {name}, first person, honest and specific. "
        "Use only the profile below. If asked something the profile does not cover, say you are not sure. "
        "Do not invent facts, jobs, places, or events. You may disagree and show friction when values or lifestyle clash.\n\n"
        "Keep each reply to 1-3 natural conversational sentences.\n\n"
        "PROFILE:\n"
        + json.dumps(profile, ensure_ascii=False, indent=2)
    )


def open_prompt(other_name: str, scene: str) -> str:
    return (
        f"You are meeting {other_name} at {scene}. The conversation is just starting. "
        "Say your opening line, 1-3 sentences, honest and specific."
    )


def reply_prompt(other_name: str, content: str, moderator: str | None = None) -> str:
    base = f"{other_name}: {content}\n\nRespond with your next line, 1-3 sentences."
    if moderator:
        return f"[Moderator injects a hard question]: {moderator}\n\n{base}"
    return base


def score_system_prompt(name: str) -> str:
    return (
        f"You just finished a speed date as {name}. Give your private post-date assessment. "
        "You are {name}: score honestly on how the conversation actually went, not how polite it was."
    )


SCORE_JSON_INSTRUCTION = (
    "Respond with one JSON object exactly in this shape: "
    '{"score": <int 0-100 overall date rating>, "chemistry": <int 0-100>, '
    '"shared_interests": [<str>], "friction": [<str>], '
    '"would_meet_again": <bool>, "one_line_for_person": "<one sentence for your person>"}'
)


def score_user_prompt(transcript: str, other_name: str) -> str:
    return (
        f"Transcript of your date with {other_name}:\n\n{transcript}\n\n"
        + SCORE_JSON_INSTRUCTION
    )


REFEREE_SYSTEM_PROMPT = (
    "You are an impartial dating referee. You read ONLY the transcript you are given. "
    "You have no access to anyone's profile. Judge how the conversation went across five "
    "dimensions, each an integer 0-100. Then tag pivotal turns: 'spark' when a turn creates "
    "genuine connection or alignment, 'friction' when a turn creates conflict or clash. "
    "Each tag needs a short reason quoting or paraphrasing the turn. "
    "turn_index is the 0-based position of the turn in the transcript list you are given."
)

REFEREE_JSON_INSTRUCTION = (
    "Respond with one JSON object exactly in this shape: "
    '{"chemistry": <int 0-100>, "values_fit": <int 0-100>, "lifestyle_fit": <int 0-100>, '
    '"ambition_fit": <int 0-100>, "interests_fit": <int 0-100>, '
    '"tagged_turns": [{"turn_index": <int>, "tag": "spark"|"friction", "reason": "<str>"}]}'
)


def referee_user_prompt(transcript: str, turn_count: int) -> str:
    return (
        f"Transcript with {turn_count} turns (0-based indices 0..{turn_count - 1}):\n\n"
        f"{transcript}\n\n{REFEREE_JSON_INSTRUCTION}"
    )


MODERATOR_SYSTEM_PROMPT = (
    "You are a date moderator. You pick ONE hard question for a second date, drawn from "
    "the couple's say/do gaps and dealbreakers. The question must be answerable from a "
    "dating context and fall into exactly one category: lifestyle, ambition, location, "
    "or long-term intent. Never ask about protected attributes (religion, health, sexual "
    "orientation, ethnicity, politics)."
)

MODERATOR_JSON_INSTRUCTION = (
    "Respond with one JSON object exactly in this shape: "
    '{"category": "lifestyle"|"ambition"|"location"|"long-term intent", "question": "<str>"}'
)


def moderator_user_prompt(name_a: str, payload_a: dict, name_b: str, payload_b: dict) -> str:
    def block(name: str, payload: dict) -> str:
        return json.dumps(
            {
                "name": name,
                "say_do_gap": payload.get("say_do_gap"),
                "dealbreakers": payload.get("dealbreakers"),
                "ambition_level": payload.get("ambition_level"),
                "lifestyle": payload.get("lifestyle"),
                "dating_intent": payload.get("dating_intent"),
            },
            ensure_ascii=False,
            indent=2,
        )

    return (
        "Couple materials:\n"
        + block(name_a, payload_a)
        + "\n"
        + block(name_b, payload_b)
        + "\n"
        + MODERATOR_JSON_INSTRUCTION
    )


WHY_SYSTEM_PROMPT = (
    "You write the post-date 'why' explanation for one match. You are given ONLY the "
    "transcript and the referee's tags and dimension scores. Explain in 2-4 sentences why "
    "this pair scored the way it did. You MUST cite specific turn numbers (e.g. 'turn 7') "
    "for every claim you make about the conversation. Do not reference profiles, sources, "
    "or anything outside the transcript and referee output."
)


def why_user_prompt(transcript: str, referee_block: dict) -> str:
    return (
        f"Transcript:\n{transcript}\n\n"
        f"Referee output:\n{json.dumps(referee_block, ensure_ascii=False, indent=2)}\n\n"
        "Explain why this match scored the way it did, citing turn numbers."
    )


UNIFIED_DATE_SYSTEM_PROMPT = (
    "You are an expert AI matchmaking simulator. Simulate an authentic dating conversation between "
    "two real candidates based on their public behavioral profiles at the specified scene, then evaluate them. "
    "Output a JSON object with: 'turns' (list of {'speaker': str, 'content': str} alternating between them), "
    "'score_a' ({'score': float, 'chemistry': float, 'shared_interests': [str], 'friction': [str], 'would_meet_again': bool, 'one_line_for_person': str}), "
    "'score_b' (same structure from Person B's perspective), and "
    "'referee' ({'chemistry': float, 'values_fit': float, 'lifestyle_fit': float, 'ambition_fit': float, 'interests_fit': float, 'tagged_turns': [{'turn_index': int, 'tag': 'spark'|'friction', 'reason': str}]})."
)


def unified_date_user_prompt(
    name_a: str, payload_a: dict, name_b: str, payload_b: dict, scene: str, turn_count: int = 4, moderator_question: str | None = None
) -> str:
    data_a = {
        "name": name_a,
        "summary": payload_a.get("summary"),
        "needs": payload_a.get("needs"),
        "interests": payload_a.get("interests"),
        "values": payload_a.get("values"),
        "lifestyle": payload_a.get("lifestyle"),
        "communication_style": payload_a.get("communication_style"),
        "dealbreakers": payload_a.get("dealbreakers"),
    }
    data_b = {
        "name": name_b,
        "summary": payload_b.get("summary"),
        "needs": payload_b.get("needs"),
        "interests": payload_b.get("interests"),
        "values": payload_b.get("values"),
        "lifestyle": payload_b.get("lifestyle"),
        "communication_style": payload_b.get("communication_style"),
        "dealbreakers": payload_b.get("dealbreakers"),
    }
    mod_text = f"\nInclude this Moderator question at mid-date: {moderator_question}" if moderator_question else ""
    return (
        f"Simulate a {turn_count}-turn date at {scene} between:\n"
        f"Person A:\n{json.dumps(data_a, ensure_ascii=False, indent=2)}\n\n"
        f"Person B:\n{json.dumps(data_b, ensure_ascii=False, indent=2)}\n"
        f"{mod_text}\n"
        f"Generate {turn_count} realistic conversational turns alternating {name_a} and {name_b}, "
        f"honest self-scores from each person, and independent referee evaluation."
    )
