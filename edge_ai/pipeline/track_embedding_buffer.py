"""Per-track multi-frame embedding average before identity match."""

from __future__ import annotations

import numpy as np

from edge_ai.embeddings.face_embedder import FaceEmbedder, normalize_embedding


class TrackEmbeddingAccumulator:
    """
    Collects embeddings per track_id; returns a stable mean after ``min_frames``.

    Once stable, the averaged vector is cached until ``clear_track``.
    """

    def __init__(self, *, min_frames: int = 3, max_frames: int = 8):
        self.min_frames = max(1, min_frames)
        self.max_frames = max(self.min_frames, max_frames)
        self._buffers: dict[int, list[np.ndarray]] = {}
        self._stable: dict[int, np.ndarray] = {}

    def update(self, track_id: int, embedding: np.ndarray) -> tuple[np.ndarray, bool]:
        """
        Add one frame embedding.

        Returns ``(embedding_for_match, is_stable)``.
        Before ``min_frames``, returns the latest normalized vector with ``is_stable=False``.
        After enough frames, returns mean embedding with ``is_stable=True``.
        """
        if track_id in self._stable:
            return self._stable[track_id], True

        emb = normalize_embedding(np.asarray(embedding, dtype=np.float32))
        buf = self._buffers.setdefault(track_id, [])
        buf.append(emb)
        if len(buf) > self.max_frames:
            buf.pop(0)

        if len(buf) < self.min_frames:
            return emb, False

        mean = FaceEmbedder.enroll_from_frames(buf)
        self._stable[track_id] = mean
        self._buffers.pop(track_id, None)
        return mean, True

    def clear_track(self, track_id: int) -> None:
        self._buffers.pop(track_id, None)
        self._stable.pop(track_id, None)

    def clear_all(self) -> None:
        self._buffers.clear()
        self._stable.clear()

    def prune_inactive(self, active_track_ids: set[int]) -> None:
        for tid in list(self._buffers):
            if tid not in active_track_ids:
                self.clear_track(tid)
        for tid in list(self._stable):
            if tid not in active_track_ids:
                self.clear_track(tid)
