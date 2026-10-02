from __future__ import annotations

import math

WEIGHT_MUTUAL = 0.45
WEIGHT_REFEREE = 0.40
WEIGHT_EMBEDDING = 0.15

REFEREE_DIMENSIONS = (
    "chemistry",
    "values_fit",
    "lifestyle_fit",
    "ambition_fit",
    "interests_fit",
)


def geometric_mean(a: float, b: float) -> float:
    if a < 0 or b < 0:
        raise ValueError("geometric mean requires non-negative inputs")
    return math.sqrt(a * b)


def referee_mean(dimensions: dict[str, float]) -> float:
    if not dimensions:
        return 0.0
    values = [float(dimensions[d]) for d in REFEREE_DIMENSIONS if d in dimensions]
    if not values:
        return 0.0
    return sum(values) / len(values)


def final_score(mutual: float, referee: float, embedding: float) -> float:
    return WEIGHT_MUTUAL * mutual + WEIGHT_REFEREE * referee + WEIGHT_EMBEDDING * embedding


def rescale_embeddings(similarities: list[float]) -> list[float]:
    """Rescale cosine similarities to 0-100 across the run (min-max).

    Falls back to clipping into [0, 100] when all pairs are identical.
    """
    if not similarities:
        return []
    low = min(similarities)
    high = max(similarities)
    if math.isclose(low, high):
        return [max(0.0, min(100.0, s * 100.0)) for s in similarities]
    spread = high - low
    return [((s - low) / spread) * 100.0 for s in similarities]


def score_breakdown(referee_dimensions: dict[str, float]) -> dict[str, float]:
    return {
        "values": float(referee_dimensions.get("values_fit", 0.0)),
        "interests": float(referee_dimensions.get("interests_fit", 0.0)),
        "lifestyle": float(referee_dimensions.get("lifestyle_fit", 0.0)),
        "ambition": float(referee_dimensions.get("ambition_fit", 0.0)),
        "chemistry": float(referee_dimensions.get("chemistry", 0.0)),
    }
