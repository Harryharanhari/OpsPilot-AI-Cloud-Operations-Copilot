"""
FAISS Vector Store for semantic log search.
Falls back gracefully if faiss is not installed.
"""
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import faiss
    import numpy as np
    _FAISS_AVAILABLE = True
except ImportError:
    _FAISS_AVAILABLE = False
    logger.warning("faiss-cpu not installed — semantic search disabled. Install with: pip install faiss-cpu")


INDEX_PATH = Path("vector_store/opspilot_faiss.index")
META_PATH  = Path("vector_store/opspilot_meta.json")


class VectorStore:
    def __init__(self):
        self.index = None
        self.metadata = []
        self.enabled = False

        if not _FAISS_AVAILABLE:
            return

        try:
            if INDEX_PATH.exists() and META_PATH.exists():
                self.index = faiss.read_index(str(INDEX_PATH))
                with open(META_PATH, "r") as f:
                    self.metadata = json.load(f)
                self.enabled = True
                logger.info(f"FAISS index loaded: {self.index.ntotal} vectors")
            else:
                self.index = faiss.IndexFlatL2(384)  # 384-dim for all-MiniLM-L6-v2
                self.enabled = True
                logger.info("New FAISS index created")
        except Exception as e:
            logger.warning(f"FAISS init failed: {e}")

    def add_logs(self, log_metas: list, embeddings: list):
        if not self.enabled or not self.index:
            return
        try:
            import numpy as np
            vecs = np.array(embeddings, dtype=np.float32)
            if vecs.ndim == 1:
                vecs = vecs.reshape(1, -1)
            self.index.add(vecs)
            self.metadata.extend(log_metas)
            self._save()
        except Exception as e:
            logger.error(f"FAISS add_logs error: {e}")

    def search(self, query: str, top_k: int = 5) -> list:
        if not self.enabled or not self.index or self.index.ntotal == 0:
            return []
        try:
            from ..ai_engine.embeddings import embedder
            import numpy as np
            vec = embedder.embed(query)
            if vec is None:
                return []
            vec = np.array(vec, dtype=np.float32).reshape(1, -1)
            k = min(top_k, self.index.ntotal)
            distances, indices = self.index.search(vec, k)
            results = []
            for dist, idx in zip(distances[0], indices[0]):
                if idx < len(self.metadata):
                    entry = dict(self.metadata[idx])
                    entry["distance"] = float(dist)
                    results.append(entry)
            return results
        except Exception as e:
            logger.error(f"FAISS search error: {e}")
            return []

    def _save(self):
        try:
            INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
            if self.index:
                faiss.write_index(self.index, str(INDEX_PATH))
            with open(META_PATH, "w") as f:
                json.dump(self.metadata, f)
        except Exception as e:
            logger.error(f"FAISS save error: {e}")


vector_store = VectorStore()
