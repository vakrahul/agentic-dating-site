import hashlib
import logging
import threading

import numpy as np

logger = logging.getLogger(__name__)

_model = None
_lock = threading.Lock()
_use_fallback = False

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
    except Exception as e:
        logger.warning(f"Embedding warmup error: {e}")


def _hash_vector(text: str, dim: int = 384) -> list[float]:
    """Lightweight 384-dim deterministic fallback embedding using hashed tokens."""
    vec = np.zeros(dim, dtype=np.float32)
    tokens = text.lower().split()
    if not tokens:
        return vec.tolist()
    for token in tokens:
        h = int(hashlib.sha256(token.encode("utf-8")).hexdigest()[:8], 16)
        idx = h % dim
        sign = 1.0 if (h >> 3) & 1 else -1.0
        vec[idx] += sign
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec /= norm
    return [float(x) for x in vec]


def get_model():
    global _model, _use_fallback
    if _use_fallback:
        return None
    with _lock:
        if _model is None and not _use_fallback:
            try:
                from sentence_transformers import SentenceTransformer

                _model = SentenceTransformer("all-MiniLM-L6-v2")
            except Exception as e:
                logger.warning(f"Could not load SentenceTransformer, using fallback: {e}")
                _use_fallback = True
                return None
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
    if model is not None:
        try:
            vector = model.encode(text, normalize_embeddings=True)
            return [float(x) for x in np.asarray(vector, dtype=np.float64)]
        except Exception as e:
            logger.warning(f"SentenceTransformer encode failed ({e}), using fallback: {e}")
    return _hash_vector(text)


def embed_payload(payload: dict) -> list[float]:
    return embed_text(profile_text(payload))


def cosine(a: list[float], b: list[float]) -> float:
    va = np.asarray(a, dtype=np.float64)
    vb = np.asarray(b, dtype=np.float64)
    denom = float(np.linalg.norm(va) * np.linalg.norm(vb))
    if denom == 0.0:
        return 0.0
    return float(np.dot(va, vb) / denom)
