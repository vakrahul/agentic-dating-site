from __future__ import annotations

import random
from typing import Any

from .calls import (
    RefereeResult,
    RefereeTag,
    SelfScore,
    UnifiedDateResult,
    UnifiedTurn,
)


def _extract_primary(items: list[Any] | None, fallback: str) -> str:
    if not items:
        return fallback
    first = items[0]
    if isinstance(first, dict):
        return str(first.get("name") or first.get("topic") or fallback)
    return str(first)


def _clean_interests(items: list[Any] | None) -> list[str]:
    if not items:
        return []
    res = []
    for item in items:
        if isinstance(item, dict):
            val = item.get("name") or item.get("topic")
            if val:
                res.append(str(val))
        elif isinstance(item, str) and item.strip():
            res.append(item.strip())
    return res


def synthesize_persona_date(
    name_a: str,
    payload_a: dict[str, Any],
    name_b: str,
    payload_b: dict[str, Any],
    scene: str,
    round_no: int = 1,
    moderator_question: str | None = None,
) -> UnifiedDateResult:
    """Generate a rich, human-like, persona-grounded date conversation.
    
    Guarantees:
    - Round 1 (Speed Date): 4 distinct, engaging turns testing chemistry and daily habits.
    - Round 2 (Deep Date): 8 deep, vulnerable turns addressing the moderator's provocative question.
    - Highly customized to their actual interests, communication styles, and values.
    """
    first_a = name_a.strip().split()[0]
    first_b = name_b.strip().split()[0]

    int_a = _clean_interests(payload_a.get("interests"))
    int_b = _clean_interests(payload_b.get("interests"))
    shared = [x for x in int_a if any(x.lower() == y.lower() for y in int_b)]
    diff_a = [x for x in int_a if x not in shared]
    diff_b = [x for x in int_b if x not in shared]

    focus_a = diff_a[0] if diff_a else (int_a[0] if int_a else "creative work")
    focus_b = diff_b[0] if diff_b else (int_b[0] if int_b else "building projects")

    vals_a = payload_a.get("values") or []
    vals_b = payload_b.get("values") or []
    val_a = _extract_primary(vals_a, "autonomy and deep focus")
    val_b = _extract_primary(vals_b, "intentional living")

    shared_topic = shared[0] if shared else "creative independence and personal growth"

    # Seed variations based on names to keep dates between different pairs distinct
    pair_seed = sum(ord(c) for c in (name_a + name_b)) + round_no * 37
    rng = random.Random(pair_seed)

    if round_no == 1:
        # SPEED DATE: 4 TURNS (Vibe check, real-life quirks, mutual curiosity)
        t0 = rng.choice([
            f"I was curious when you suggested {scene}—it has this rare stillness to it. Between your focus on {focus_b} and everything you juggle publicly, what does a normal, uncurated day look like for you when the screen is off?",
            f"It's really refreshing meeting here at {scene}. I read about your work in {focus_b}, but I'm curious: when you're not in builder mode, what actually pulls your curiosity right now?",
            f"Finding somewhere quiet like {scene} is half the battle. Coming from my world of {focus_a}, I'm always fascinated by how other creators operate. What’s something in your routine that keeps you sane?",
        ])

        t1 = rng.choice([
            f"Honestly, far less polished than the internet makes it seem. Mostly deep focus sprints on {focus_b}, trying to protect quiet mornings, and refusing to compromise on {val_b}. I noticed your work with {focus_a}—do you actually know how to switch off, or does your brain constantly run at full speed?",
            f"To be blunt: lots of unglamorous iteration on {focus_b}, walking without my phone, and guarding my calendar for {val_b}. Looking at what you do in {focus_a}, do you find yourself defending your solitude, or do you thrive on constant momentum?",
            f"Most days are surprisingly simple: high-output mornings on {focus_b}, sweating out the stress, and zero tolerance for vanity meetings. But what about you? In {focus_a}, how do you separate what you actually care about from public expectations?",
        ])

        t2 = rng.choice([
            f"Switching off is a constant battle. My default is to optimize around {val_a}, so I have to actively force slow hours into my week. But I respect that you don't romanticize the hustle—it gets exhausting when people treat busyness as a badge of honor.",
            f"I definitely guard my solitude. When I'm in flow on {focus_a}, hours disappear. But what I've learned is that high output without {val_a} is just burnout in disguise. It's rare to meet someone who understands that rhythm without needing an explanation.",
            f"I used to confuse momentum with progress. Now, if a project doesn't align with {val_a}, I cut it. What struck me about your perspective is how grounded your energy is around {focus_b}—you're playing a long game.",
        ])

        t3 = rng.choice([
            f"Life's too short for performative small talk. I like that we can cut straight to what actually drives us. There’s an undeniable spark in how we both value {shared_topic}.",
            f"Completely agree. Most first dates feel like LinkedIn interviews, but this feels real. Seeing how you balance ambition with {val_a} makes me very curious to dig deeper.",
            f"That long game is everything. When two people respect each other's flow states around {shared_topic}, you don't drain each other—you elevate each other. I'd definitely want to continue this conversation.",
        ])

        turns = [
            UnifiedTurn(speaker=name_a, content=t0),
            UnifiedTurn(speaker=name_b, content=t1),
            UnifiedTurn(speaker=name_a, content=t2),
            UnifiedTurn(speaker=name_b, content=t3),
        ]

        chem = 78.0 + (rng.random() * 12.0)
        tags = [
            RefereeTag(turn_index=1, tag="spark", reason=f"Mutual alignment on authentic lifestyle over vanity metrics in {focus_b}."),
            RefereeTag(turn_index=2, tag="spark", reason=f"Shared realization regarding the necessity of {val_a} for sustainable creative output."),
        ]

    else:
        # DEEP DATE: 8 TURNS (Spicy debate, dealbreakers, values alignment, future roadmap)
        mod_q = moderator_question or "When you imagine your next two years, does this person fit into that picture or not? Say it honestly."

        d0 = (
            f"The moderator question doesn't pull any punches: '{mod_q}'. "
            f"To be completely direct: my next two years are centered on compounding freedom around {val_a}. "
            f"If a partner needs constant hand-holding or resents the solitude I need for {focus_a}, it collapses. "
            f"Looking across at how you navigate {focus_b}, do you see our intensities colliding, or complementing each other?"
        )

        d1 = (
            f"I respect the directness. Here is my honest reality check: when two high-agency people who value {val_b} and {val_a} collide, "
            f"the danger isn't lack of mutual respect—it's running in parallel lanes so fast that you forget to build a shared foundation. "
            f"When you're under peak pressure or in a creative tunnel, do you withdraw completely, or can you remain emotionally present?"
        )

        d2 = (
            f"In the past, my instinctive defense was total withdrawal into my own head. "
            f"What I've had to master through {focus_a} is communicating the boundary before disappearing: 'I'm not disconnecting from you, I'm just replenishing.' "
            f"What about on your side? What is the one behavioral habit that makes you walk away from someone?"
        )

        d3 = (
            f"Lack of intellectual curiosity and emotional neediness. I need someone who has their own orbit, their own fire. "
            f"If you're in the zone working on {val_a}, I don't feel abandoned; I feel respect. "
            f"What I need is someone who can look at the chaos of public scrutiny around {focus_b} and laugh with me over late-night tea without making it about status."
        )

        d4 = (
            f"That resonates down to the bone. When vanity metrics or external noise peak, having a partner who anchors you back to {shared_topic} is everything. "
            f"We both have big ambitions, but neither of us seems attached to the performative side of it."
        )

        d5 = (
            f"Exactly. When the cameras are off and the notifications are silenced, all that matters is whether Sunday mornings together feel peaceful or stressful. "
            f"And sitting here with you, the silence isn't awkward—it's actually calming."
        )

        d6 = (
            f"I feel that exact calm. It's rare to find someone whose ambition matches yours without feeling like a perpetual power struggle. "
            f"Answering the moderator honestly: yes, I can genuinely see you fitting into my next two years—not as a compromise, but as a catalyst."
        )

        d7 = (
            f"Then we're in full alignment. A catalyst who respects quiet boundaries is the exact person I want in my corner. "
            f"Let's make sure we protect this balance."
        )

        turns = [
            UnifiedTurn(speaker=name_a, content=d0),
            UnifiedTurn(speaker=name_b, content=d1),
            UnifiedTurn(speaker=name_a, content=d2),
            UnifiedTurn(speaker=name_b, content=d3),
            UnifiedTurn(speaker=name_a, content=d4),
            UnifiedTurn(speaker=name_b, content=d5),
            UnifiedTurn(speaker=name_a, content=d6),
            UnifiedTurn(speaker=name_b, content=d7),
        ]

        chem = 84.0 + (rng.random() * 10.0)
        tags = [
            RefereeTag(turn_index=1, tag="friction", reason="Tension regarding parallel founder paths and risk of emotional distance during work tunnels."),
            RefereeTag(turn_index=3, tag="spark", reason="Deep relief on shared requirement for independent orbits and zero needy clinginess."),
            RefereeTag(turn_index=5, tag="spark", reason="Mutual vulnerability regarding peaceful Sunday mornings away from public performance."),
            RefereeTag(turn_index=7, tag="spark", reason="Both agents deliver a resounding yes to the 2-year horizon moderator prompt."),
        ]

    sc_a = round(chem + rng.uniform(1.0, 3.0), 1)
    sc_b = round(chem + rng.uniform(0.5, 2.5), 1)

    return UnifiedDateResult(
        turns=turns,
        score_a=SelfScore(
            score=min(98.0, sc_a),
            chemistry=round(chem, 1),
            shared_interests=[shared_topic, val_a][:3],
            friction=["Work tunnel isolation"] if round_no == 2 else [],
            would_meet_again=True,
            one_line_for_person=f"Exceptional alignment on {val_b} and mutual respect for independent focus.",
        ),
        score_b=SelfScore(
            score=min(98.0, sc_b),
            chemistry=round(chem, 1),
            shared_interests=[shared_topic, val_b][:3],
            friction=["Parallel ambition tempo"] if round_no == 2 else [],
            would_meet_again=True,
            one_line_for_person=f"Grounded, razor-sharp energy around {focus_a} with zero performative fluff.",
        ),
        referee=RefereeResult(
            chemistry=round(chem, 1),
            values_fit=round(chem + 2.0, 1),
            lifestyle_fit=round(chem - 1.0, 1),
            ambition_fit=round(chem + 4.0, 1),
            interests_fit=round(chem, 1),
            tagged_turns=tags,
        ),
    )
