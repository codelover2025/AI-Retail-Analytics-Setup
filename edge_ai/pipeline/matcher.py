"""Cosine-similarity matching against in-memory embedding galleries."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Literal, Optional

import numpy as np

from edge_ai.embeddings.face_embedder import normalize_embedding
from edge_ai.pipeline.types import EMBEDDING_DIM

logger = logging.getLogger(__name__)

PersonKind = Literal["customer", "employee"]


@dataclass(frozen=True)
class GalleryEntry:
    person_id: int
    embedding: np.ndarray
    person_kind: PersonKind
    visitor_id: Optional[str] = None


@dataclass(frozen=True)
class MatchHit:
    person_id: int
    score: float
    person_kind: PersonKind
    visitor_id: Optional[str] = None


class CosineMatcher:
    """
    Production matcher: cosine similarity on L2-normalized 512-d vectors.
    Uses FAISS when enabled and gallery is large enough; linear scan otherwise.
    """

    def __init__(
        self,
        threshold: float = 0.55,
        *,
        cache_recent: bool = True,
        use_faiss: bool = True,
        faiss_min_gallery_size: int = 50,
    ):
        self.threshold = threshold
        self.cache_recent = cache_recent
        self.use_faiss = use_faiss
        self.faiss_min_gallery_size = faiss_min_gallery_size
        self._customer_gallery: list[GalleryEntry] = []
        self._employee_gallery: list[GalleryEntry] = []
        self._gallery_by_id: dict[int, GalleryEntry] = {}
        self._recent_cache: dict[int, np.ndarray] = {}
        self._faiss = None
        self._faiss_ok = False
        if use_faiss:
            try:
                from edge_ai.pipeline.faiss_index import FaissGalleryIndex, faiss_available

                if faiss_available():
                    self._faiss = FaissGalleryIndex()
                    self._faiss_ok = True
                else:
                    logger.info("faiss not installed; using linear gallery scan")
            except Exception as exc:
                logger.warning("FAISS init failed: %s", exc)

    def load_gallery(self, entries: list[GalleryEntry]) -> None:
        self._customer_gallery = [e for e in entries if e.person_kind == "customer"]
        self._employee_gallery = [e for e in entries if e.person_kind == "employee"]
        self._gallery_by_id = {e.person_id: e for e in entries}
        self._recent_cache.clear()
        if self._faiss_ok and self._faiss is not None:
            total = len(self._customer_gallery) + len(self._employee_gallery)
            if total >= self.faiss_min_gallery_size:
                self._faiss.rebuild(entries)
                logger.debug("FAISS gallery index built (%d entries)", total)
            else:
                self._faiss._built = False

    def add_entry(self, entry: GalleryEntry) -> None:
        if entry.person_kind == "employee":
            self._employee_gallery.append(entry)
        else:
            self._customer_gallery.append(entry)
        self._gallery_by_id[entry.person_id] = entry
        if self.cache_recent:
            self._recent_cache[entry.person_id] = entry.embedding.copy()
            if len(self._recent_cache) > 200:
                first_key = next(iter(self._recent_cache))
                self._recent_cache.pop(first_key, None)
        if self._faiss_ok and self._faiss is not None:
            all_entries = self._customer_gallery + self._employee_gallery
            if len(all_entries) >= self.faiss_min_gallery_size:
                self._faiss.rebuild(all_entries)

    @staticmethod
    def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        a = normalize_embedding(np.asarray(a, dtype=np.float32))
        b = normalize_embedding(np.asarray(b, dtype=np.float32))
        return float(np.dot(a, b))

    def match(
        self,
        embedding: np.ndarray,
        *,
        kinds: tuple[PersonKind, ...] = ("customer", "employee"),
    ) -> Optional[MatchHit]:
        emb = normalize_embedding(np.asarray(embedding, dtype=np.float32))
        if emb.shape[0] != EMBEDDING_DIM:
            return None

        if self.cache_recent:
            hit = self._match_cached(emb, kinds)
            if hit is not None:
                return hit

        total = len(self._customer_gallery) + len(self._employee_gallery)
        if (
            self._faiss_ok
            and self._faiss is not None
            and self._faiss._built
            and total >= self.faiss_min_gallery_size
        ):
            hit = self._faiss.search(
                emb, kinds=kinds, threshold=self.threshold, top_k=3
            )
            if hit is not None:
                if self.cache_recent:
                    self._recent_cache[hit.person_id] = emb
                    if len(self._recent_cache) > 200:
                        first_key = next(iter(self._recent_cache))
                        self._recent_cache.pop(first_key, None)
                return hit

        best = self._match_linear(emb, kinds)
        if best and self.cache_recent:
            self._recent_cache[best.person_id] = emb
            if len(self._recent_cache) > 200:
                first_key = next(iter(self._recent_cache))
                self._recent_cache.pop(first_key, None)
        return best

    def _match_linear(
        self,
        emb: np.ndarray,
        kinds: tuple[PersonKind, ...],
    ) -> Optional[MatchHit]:
        best: Optional[MatchHit] = None
        galleries: list[tuple[PersonKind, list[GalleryEntry]]] = []
        if "employee" in kinds:
            galleries.append(("employee", self._employee_gallery))
        if "customer" in kinds:
            galleries.append(("customer", self._customer_gallery))

        for kind, entries in galleries:
            for entry in entries:
                score = self.cosine_similarity(emb, entry.embedding)
                if score >= self.threshold and (
                    best is None or score > best.score
                ):
                    best = MatchHit(
                        person_id=entry.person_id,
                        score=score,
                        person_kind=kind,
                        visitor_id=entry.visitor_id,
                    )
        return best

    def match_employee(self, embedding: np.ndarray) -> Optional[MatchHit]:
        return self.match(embedding, kinds=("employee",))

    def match_customer(self, embedding: np.ndarray) -> Optional[MatchHit]:
        return self.match(embedding, kinds=("customer",))

    def _match_cached(
        self,
        embedding: np.ndarray,
        kinds: tuple[PersonKind, ...],
    ) -> Optional[MatchHit]:
        best: Optional[MatchHit] = None
        for person_id, cached_emb in self._recent_cache.items():
            score = self.cosine_similarity(embedding, cached_emb)
            if score < self.threshold:
                continue
            entry = self._find_entry(person_id)
            if entry is None or entry.person_kind not in kinds:
                continue
            if best is None or score > best.score:
                best = MatchHit(
                    person_id=person_id,
                    score=score,
                    person_kind=entry.person_kind,
                    visitor_id=entry.visitor_id,
                )
        return best

    def _find_entry(self, person_id: int) -> Optional[GalleryEntry]:
        return self._gallery_by_id.get(person_id)
