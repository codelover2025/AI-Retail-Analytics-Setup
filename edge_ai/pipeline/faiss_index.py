"""Optional FAISS inner-product index for L2-normalized cosine search."""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np

from edge_ai.pipeline.matcher import GalleryEntry, MatchHit, PersonKind
from edge_ai.pipeline.types import EMBEDDING_DIM

logger = logging.getLogger(__name__)


def faiss_available() -> bool:
    try:
        import faiss  # noqa: F401

        return True
    except ImportError:
        return False


class FaissGalleryIndex:
    """One FAISS index per person_kind (inner product on unit vectors = cosine)."""

    def __init__(self) -> None:
        self._entries: dict[PersonKind, list[GalleryEntry]] = {
            "customer": [],
            "employee": [],
        }
        self._indices: dict[PersonKind, object] = {}
        self._built = False

    def rebuild(self, entries: list[GalleryEntry]) -> None:
        import faiss

        self._entries = {"customer": [], "employee": []}
        for entry in entries:
            self._entries[entry.person_kind].append(entry)

        self._indices = {}
        for kind in ("customer", "employee"):
            rows = self._entries[kind]
            if not rows:
                continue
            matrix = np.stack(
                [np.asarray(e.embedding, dtype=np.float32) for e in rows],
                axis=0,
            )
            faiss.normalize_L2(matrix)
            index = faiss.IndexFlatIP(EMBEDDING_DIM)
            index.add(matrix)
            self._indices[kind] = index
        self._built = True

    def search(
        self,
        embedding: np.ndarray,
        *,
        kinds: tuple[PersonKind, ...],
        threshold: float,
        top_k: int = 1,
    ) -> Optional[MatchHit]:
        if not self._built:
            return None

        import faiss

        query = np.asarray(embedding, dtype=np.float32).reshape(1, -1)
        faiss.normalize_L2(query)

        best: Optional[MatchHit] = None
        for kind in kinds:
            index = self._indices.get(kind)
            entries = self._entries.get(kind, [])
            if index is None or not entries or index.ntotal == 0:
                continue
            scores, indices = index.search(query, min(top_k, index.ntotal))
            for score, idx in zip(scores[0], indices[0]):
                if idx < 0 or score < threshold:
                    continue
                entry = entries[int(idx)]
                if best is None or float(score) > best.score:
                    best = MatchHit(
                        person_id=entry.person_id,
                        score=float(score),
                        person_kind=kind,
                        visitor_id=entry.visitor_id,
                    )
        return best
