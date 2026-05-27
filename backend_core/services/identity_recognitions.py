import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend_core.models.identity import Employee, FaceEmbedding, PersonRecognition
from backend_core.schemas.identity import RecognitionIngest, RecognitionOut
from backend_core.services.identity_customers import IdentityCustomerService


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class IdentityRecognitionService:
    def __init__(self, db: Session):
        self.db = db
        self.customers = IdentityCustomerService(db)

    def list_recognitions(self, limit: int = 500) -> list[RecognitionOut]:
        rows = (
            self.db.execute(
                select(PersonRecognition)
                .order_by(PersonRecognition.timestamp.desc())
                .limit(limit)
            )
            .scalars()
            .all()
        )
        return [
            RecognitionOut(
                id=str(r.id),
                person_id=str(r.person_id),
                type=r.type,
                timestamp=r.timestamp,
                camera_id=r.camera_id,
            )
            for r in rows
        ]

    def list_recognitions_for_person_id(
        self,
        person_id: uuid.UUID,
        *,
        limit: int = 500,
        repeat_only: bool = False,
    ) -> list[RecognitionOut]:
        stmt = select(PersonRecognition).where(PersonRecognition.person_id == person_id)
        if repeat_only:
            stmt = stmt.where(PersonRecognition.type == "repeat_visitor")
        stmt = stmt.order_by(PersonRecognition.timestamp.desc()).limit(limit)

        rows = self.db.execute(stmt).scalars().all()
        return [
            RecognitionOut(
                id=str(r.id),
                person_id=str(r.person_id),
                type=r.type,
                timestamp=r.timestamp,
                camera_id=r.camera_id,
            )
            for r in rows
        ]

    def ingest(self, payload: RecognitionIngest) -> RecognitionOut:
        person_id = uuid.UUID(payload.person_id)
        ts = payload.timestamp
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)

        if payload.type == "employee":
            emp = self.db.get(Employee, person_id)
            if emp is None and payload.embedding:
                self.db.add(
                    Employee(
                        id=person_id,
                        name=f"Employee {str(person_id)[:8]}",
                        embedding=payload.embedding,
                    )
                )
        elif payload.type != "employee":
            cust = self.customers.upsert_from_recognition(person_id, ts)
            if payload.embedding and payload.type in ("customer", "new_visitor", "repeat_visitor"):
                self.db.add(
                    FaceEmbedding(
                        customer_id=cust.id,
                        embedding=payload.embedding,
                    )
                )

        rec = PersonRecognition(
            person_id=person_id,
            type=payload.type,
            timestamp=ts,
            camera_id=payload.camera_id,
        )
        self.db.add(rec)
        self.db.commit()
        self.db.refresh(rec)

        return RecognitionOut(
            id=str(rec.id),
            person_id=str(rec.person_id),
            type=rec.type,
            timestamp=rec.timestamp,
            camera_id=rec.camera_id,
        )
