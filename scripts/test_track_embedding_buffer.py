"""Multi-frame track embedding average."""

import numpy as np

from edge_ai.pipeline.track_embedding_buffer import TrackEmbeddingAccumulator


def main() -> None:
    rng = np.random.default_rng(1)
    base = rng.standard_normal(512).astype(np.float32)
    base /= np.linalg.norm(base)
    acc = TrackEmbeddingAccumulator(min_frames=3, max_frames=5)

    stable_hits = 0
    for i in range(5):
        noise = base + rng.standard_normal(512).astype(np.float32) * 0.02
        _, stable = acc.update(42, noise)
        if stable:
            stable_hits += 1

    assert stable_hits == 3, f"expected stable on frames 3-5, got {stable_hits}"
    final, stable = acc.update(42, base)
    assert stable and np.allclose(final, acc._stable[42])
    acc.clear_track(42)
    assert 42 not in acc._stable
    print("track_embedding_buffer OK")


if __name__ == "__main__":
    main()
