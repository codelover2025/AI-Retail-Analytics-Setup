"""Manual employee / customer enrollment from face images (edge-only, no HTTP API)."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import cv2
import numpy as np

from edge_ai.embeddings.face_embedder import FaceEmbedder
from edge_ai.pipeline.face_processor import FaceProcessor
from edge_ai.pipeline.store import PersonGalleryStore
from shared.config import get_settings
from shared.database.session import SessionLocal, init_db
from shared.tenant_resolve import resolve_brand_id

logger = logging.getLogger(__name__)


def _load_image(path: Path) -> np.ndarray:
    frame = cv2.imread(str(path))
    if frame is None:
        raise FileNotFoundError(f"Cannot read image: {path}")
    return frame


def enroll_from_image(
    image_path: Path,
    *,
    person_kind: str,
    label: str,
) -> int:
    settings = get_settings()
    init_db()
    processor = FaceProcessor.from_settings(settings)
    frame = _load_image(image_path)
    faces = processor.process_frame(frame)
    if not faces:
        raise ValueError("No face above quality threshold in image")
    if len(faces) > 1:
        logger.warning("Multiple faces detected; using highest score")
    face = max(faces, key=lambda f: f.score)
    embedding = FaceEmbedder.to_list(face.embedding)

    db = SessionLocal()
    try:
        brand_id = resolve_brand_id(db, settings)
        store = PersonGalleryStore(db, settings, brand_id)
        if person_kind == "employee":
            visitor = store.register_employee(embedding, employee_code=label)
        else:
            visitor = store.register_person(embedding, person_kind=person_kind, display_name=label)
        db.commit()
        from edge_ai.pipeline.store import person_id_from_visitor

        pid = person_id_from_visitor(visitor)
        logger.info("Enrolled %s person_id=%s visitor_id=%s", person_kind, pid, visitor.id)
        return pid
    finally:
        db.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Enroll face embedding (employee or customer)")
    parser.add_argument("image", type=Path, help="Path to face photo (jpg/png)")
    parser.add_argument(
        "--kind",
        choices=("employee", "customer"),
        default="employee",
        help="Person kind (default: employee)",
    )
    parser.add_argument(
        "--label",
        default="E001",
        help="Display name / employee code",
    )
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO)
    enroll_from_image(args.image, person_kind=args.kind, label=args.label)
    return 0


if __name__ == "__main__":
    sys.exit(main())
