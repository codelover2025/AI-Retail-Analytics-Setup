import numpy as np


def normalize_embedding(embedding: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(embedding)
    if norm < 1e-8:
        return embedding.astype(np.float32)
    return (embedding / norm).astype(np.float32)


class FaceEmbedder:
    """
    Embedding utilities. Detection already returns normed embeddings from InsightFace;
    this module normalizes and serializes for storage.
    """

    @staticmethod
    def from_detection(embedding: np.ndarray) -> np.ndarray:
        return normalize_embedding(embedding)

    @staticmethod
    def to_list(embedding: np.ndarray) -> list[float]:
        return normalize_embedding(embedding).tolist()
