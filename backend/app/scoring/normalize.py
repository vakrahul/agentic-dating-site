from __future__ import annotations

import math


def z_scores(values: list[float]) -> list[float]:
    if not values:
        return []
    mean = sum(values) / len(values)
    if len(values) == 1:
        return [0.0]
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    std = math.sqrt(variance)
    if std == 0.0:
        return [0.0 for _ in values]
    return [(v - mean) / std for v in values]


def normal_cdf(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def rescale_z_to_100(z: list[float]) -> list[float]:
    return [max(0.0, min(100.0, normal_cdf(value) * 100.0)) for value in z]


def z_normalize(values: list[float]) -> list[float]:
    """Z-normalize one agent's self-scores, then rescale to 0-100.

    Removes generous/harsh scoring tendencies. Zero-variance input (an agent
    who scored everyone identically) maps to 50 for every entry.
    """
    if not values:
        return []
    zs = z_scores(values)
    if all(z == 0.0 for z in zs) and len(set(values)) == 1:
        return [50.0 for _ in values]
    return rescale_z_to_100(zs)
