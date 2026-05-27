"""FAISS gallery path (skips if faiss not installed)."""

import numpy as np

from edge_ai.pipeline.faiss_index import faiss_available
from edge_ai.pipeline.matcher import CosineMatcher, GalleryEntry


def main() -> None:
    if not faiss_available():
        print("SKIP: faiss not installed")
        return

    rng = np.random.default_rng(2)
    entries = []
    base = rng.standard_normal(512).astype(np.float32)
    base /= np.linalg.norm(base)
    entries.append(GalleryEntry(person_id=1, embedding=base, person_kind="customer"))
    for i in range(60):
        v = rng.standard_normal(512).astype(np.float32)
        v /= np.linalg.norm(v)
        entries.append(
            GalleryEntry(person_id=i + 2, embedding=v, person_kind="customer")
        )

    matcher = CosineMatcher(threshold=0.55, use_faiss=True, faiss_min_gallery_size=50)
    matcher.load_gallery(entries)
    query = base + rng.standard_normal(512).astype(np.float32) * 0.03
    hit = matcher.match_customer(query)
    assert hit is not None and hit.person_id == 1, hit
    print("faiss matcher OK")


if __name__ == "__main__":
    main()
