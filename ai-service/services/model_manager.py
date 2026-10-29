# ai-service/services/model_manager.py
import os
import threading
from typing import Optional, List

# Set cache dir inside ai-service/models_cache so model downloads persist locally
MODELS_CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models_cache")
os.makedirs(MODELS_CACHE_DIR, exist_ok=True)
os.environ["HF_HOME"] = MODELS_CACHE_DIR
os.environ["SENTENCE_TRANSFORMERS_HOME"] = MODELS_CACHE_DIR

class ModelManager:
    """
    Thread-safe lazy-loading model singleton.
    Models are NOT loaded at server startup to guarantee instantaneous 0-second boot.
    Weights are loaded into RAM strictly upon first call.
    """
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self._embedder = None
        self._embedder_lock = threading.Lock()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def get_embedder(self):
        """
        Loads sentence-transformers/all-MiniLM-L6-v2 on-demand (80MB, ~12ms inference).
        """
        if self._embedder is None:
            with self._embedder_lock:
                if self._embedder is None:
                    print("[ModelManager] ⚡ Loading Hugging Face 'all-MiniLM-L6-v2' on-demand...")
                    from sentence_transformers import SentenceTransformer
                    self._embedder = SentenceTransformer(
                        'sentence-transformers/all-MiniLM-L6-v2',
                        cache_folder=MODELS_CACHE_DIR
                    )
                    print("[ModelManager] ✅ Embedder ready in memory.")
        return self._embedder

    def compute_similarity(self, text_a: str, text_b: str) -> float:
        """
        Computes semantic cosine similarity (0.0 to 1.0) between two text strings.
        """
        if not text_a or not text_b:
            return 0.0
        embedder = self.get_embedder()
        from sentence_transformers import util
        embeddings = embedder.encode([text_a, text_b], convert_to_tensor=True)
        cos_sim = util.cos_sim(embeddings[0], embeddings[1]).item()
        return max(0.0, min(1.0, float(cos_sim)))

    def compute_embeddings(self, texts: List[str]):
        """
        Generates dense vector embeddings for a list of texts.
        """
        if not texts:
            return []
        embedder = self.get_embedder()
        return embedder.encode(texts, convert_to_tensor=False).tolist()

model_manager = ModelManager.get_instance()
