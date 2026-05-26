"""Quick offline test for cosine matcher (no camera)."""

import numpy as np

from edge_ai.pipeline.matcher import CosineMatcher, GalleryEntry


def main() -> None:
    rng = np.random.default_rng(0)
    base = rng.standard_normal(512).astype(np.float32)
    base /= np.linalg.norm(base)

    matcher = CosineMatcher(threshold=0.55)
    matcher.load_gallery(
        [
            GalleryEntry(person_id=1, embedding=base, person_kind="customer"),
            GalleryEntry(
                person_id=2,
                embedding=rng.standard_normal(512).astype(np.float32),
                person_kind="employee",
            ),
        ]
    )

    noise = base + rng.standard_normal(512).astype(np.float32) * 0.05
    hit = matcher.match_customer(noise)
    assert hit is not None and hit.person_id == 1, hit

    emp = matcher.match_employee(
        matcher._employee_gallery[0].embedding  # type: ignore[index]
    )
    assert emp is not None and emp.person_id == 2, emp

    print("matcher OK: customer + employee paths")


if __name__ == "__main__":
    main()
