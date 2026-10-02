from __future__ import annotations

import threading

import numpy as np

_model = None
_lock = threading.Lock()

TEXT_FIELDS = (
    "summary",
    "communication_style",
    "lifestyle",
    "ambition_level",
    "dating_intent",
)


def warmup() -> None:
    try:
        get_model()
    except Exception:
        pass


def get_model():
    global _model
    with _lock:
        if _model is None:
            from sentence_transformers import SentenceTransformer

            _model = SentenceTransformer("all-MiniLM-L6-v2")
        return _model


def profile_text(payload: dict) -> str:
    parts: list[str] = []
    for field in TEXT_FIELDS:
        value = payload.get(field)
        if isinstance(value, str) and value.strip():
            parts.append(value.strip())
    for field in ("interests", "values", "personality", "needs", "looking_for", "dealbreakers"):
        items = payload.get(field) or []
        if items:
            parts.append(field + ": " + ", ".join(str(i) for i in items))
    stated = payload.get("stated_self") or {}
    lived = payload.get("lived_self") or {}
    if stated.get("career"):
        parts.append("career: " + str(stated["career"]))
    if lived.get("hobbies"):
        parts.append("hobbies: " + ", ".join(str(h) for h in lived["hobbies"]))
    if lived.get("social_energy"):
        parts.append("social energy: " + str(lived["social_energy"]))
    return "\n".join(parts)


def embed_text(text: str) -> list[float]:
    model = get_model()
    vector = model.encode(text, normalize_embeddings=True)
    return [float(x) for x in np.asarray(vector, dtype=np.float64)]


def embed_payload(payload: dict) -> list[float]:
    return embed_text(profile_text(payload))


def cosine(a: list[float], b: list[float]) -> float:
    va = np.asarray(a, dtype=np.float64)
    vb = np.asarray(b, dtype=np.float64)
    denom = float(np.linalg.norm(va) * np.linalg.norm(vb))
    if denom == 0.0:
        return 0.0
    return float(np.dot(va, vb) / denom)
