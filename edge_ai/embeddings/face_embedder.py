import numpy as np

INSIGHTFACE_MODEL = "buffalo_l"
EMBEDDING_DIM = 512


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

    @staticmethod
    def enroll_from_frames(
        embeddings: list[np.ndarray],
        *,
        min_similarity: float = 0.6,
    ) -> np.ndarray:
        """
        Mean embedding from multiple frames; rejects if frames look like different people.
        """
        if not embeddings:
            raise ValueError("enroll_from_frames requires at least one embedding")
        normed = [normalize_embedding(np.asarray(e, dtype=np.float32)) for e in embeddings]
        if len(normed) == 1:
            return normed[0]
        for i in range(1, len(normed)):
            sim = float(np.dot(normed[0], normed[i]))
            if sim < min_similarity:
                raise ValueError(
                    f"Enrollment frames inconsistent (similarity {sim:.2f} < {min_similarity})"
                )
        stacked = np.stack(normed, axis=0)
        mean = np.mean(stacked, axis=0)
        return normalize_embedding(mean)
