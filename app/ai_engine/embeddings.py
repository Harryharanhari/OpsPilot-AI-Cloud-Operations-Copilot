import logging
import numpy as np
from ..config import settings

logger = logging.getLogger(__name__)

# Safe lazy import — old sentence-transformers versions break on import
try:
    from sentence_transformers import SentenceTransformer
    _SENTENCE_TRANSFORMERS_AVAILABLE = True
except (ImportError, Exception) as e:
    logger.warning(f"sentence-transformers unavailable: {e}. Falling back to hash-based embeddings.")
    _SENTENCE_TRANSFORMERS_AVAILABLE = False


def _hash_embed(text: str, dim: int = 384) -> np.ndarray:
    """Deterministic fallback embedding using character hashing (no ML required)."""
    rng = np.random.default_rng(abs(hash(text)) % (2**32))
    vec = rng.standard_normal(dim).astype(np.float32)
    norm = np.linalg.norm(vec)
    return vec / norm if norm > 0 else vec


class Embedder:
    def __init__(self):
        self.model = None
        self.enabled = False

        if _SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
                self.enabled = True
                logger.info("✅ SentenceTransformer loaded successfully.")
            except Exception as e:
                logger.warning(f"Could not load SentenceTransformer model: {e}. Using fallback.")
        else:
            logger.info("Using hash-based fallback embeddings (run: pip install -U sentence-transformers huggingface_hub)")

    def embed(self, text: str) -> np.ndarray:
        if self.enabled and self.model:
            return self.model.encode(text)
        return _hash_embed(text)

    def embed_batch(self, texts: list) -> list:
        if self.enabled and self.model:
            return self.model.encode(texts)
        return [_hash_embed(t) for t in texts]


embedder = Embedder()
