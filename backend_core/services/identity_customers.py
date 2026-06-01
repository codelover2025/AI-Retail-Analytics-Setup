import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend_core.models.identity import Customer, FaceEmbedding, PersonRecognition
from backend_core.schemas.identity import CustomerOut, RepeatVisitorOut


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class IdentityCustomerService:
    def __init__(self, db: Session):
        self.db = db

    def list_customers(self, limit: int = 500) -> list[CustomerOut]:
        rows = (
            self.db.execute(
                select(Customer).order_by(Customer.last_seen.desc()).limit(limit)
            )
            .scalars()
            .all()
        )
        return [
            CustomerOut(
                id=str(c.id),
                first_seen=c.first_seen,
                last_seen=c.last_seen,
                visit_count=c.visit_count,
            )
            for c in rows
        ]

    def list_repeat_visitors(self, min_visits: int = 2, limit: int = 500) -> list[RepeatVisitorOut]:
        subquery = (
            select(
                PersonRecognition.person_id,
                func.min(PersonRecognition.timestamp).label("first_seen"),
                func.max(PersonRecognition.timestamp).label("last_seen"),
                func.count().label("visit_count"),
            )
            .where(PersonRecognition.type.in_(("customer", "new_visitor", "repeat_visitor", "visitor")))
            .group_by(PersonRecognition.person_id)
            .having(func.count() >= min_visits)
            .subquery()
        )
        
        stmt = (
            select(subquery, Customer)
            .outerjoin(Customer, subquery.c.person_id == Customer.id)
            .order_by(subquery.c.last_seen.desc())
            .limit(limit)
        )
        rows = self.db.execute(stmt).all()
        out: list[RepeatVisitorOut] = []
        for row in rows:
            cust = row.Customer
            if cust:
                out.append(
                    RepeatVisitorOut(
                        person_id=str(cust.id),
                        visit_count=cust.visit_count,
                        first_seen=cust.first_seen,
                        last_seen=cust.last_seen,
                    )
                )
            else:
                out.append(
                    RepeatVisitorOut(
                        person_id=str(row.person_id),
                        visit_count=int(row.visit_count),
                        first_seen=row.first_seen,
                        last_seen=row.last_seen,
                    )
                )
        return out

    def upsert_from_recognition(self, person_id: uuid.UUID, ts: datetime) -> Customer:
        """Used by ingestion endpoint: increment counts based on recognition stream."""
        cust = self.db.get(Customer, person_id)
        if cust is None:
            cust = Customer(
                id=person_id,
                first_seen=ts,
                last_seen=ts,
                visit_count=1,
            )
            self.db.add(cust)
            return cust
        if ts < cust.first_seen:
            cust.first_seen = ts
        if ts > cust.last_seen:
            cust.last_seen = ts
        cust.visit_count += 1
        return cust

    def create_or_update_customer(
        self,
        *,
        person_id: uuid.UUID,
        first_seen: datetime | None,
        last_seen: datetime | None,
        visit_count: int | None = None,
    ) -> Customer:
        """Create or update a customer profile (does not modify visit_count incrementally)."""
        cust = self.db.get(Customer, person_id)
        if cust is None:
            cust = Customer(
                id=person_id,
                first_seen=first_seen or _utcnow(),
                last_seen=last_seen or _utcnow(),
                visit_count=visit_count if visit_count is not None else 1,
            )
            self.db.add(cust)
            self.db.flush()
            return cust

        if first_seen is not None:
            cust.first_seen = min(cust.first_seen, first_seen)
        if last_seen is not None:
            cust.last_seen = max(cust.last_seen, last_seen)
        if visit_count is not None:
            cust.visit_count = visit_count
        return cust

    def enroll_face_embedding(
        self,
        *,
        customer_id: uuid.UUID,
        embedding: list[float],
    ) -> FaceEmbedding:
        if not embedding:
            raise ValueError("embedding cannot be empty")
        cust = self.db.get(Customer, customer_id)
        if cust is None:
            raise ValueError("customer does not exist")

        emb = FaceEmbedding(customer_id=cust.id, embedding=embedding)
        self.db.add(emb)
        self.db.commit()
        self.db.refresh(emb)
        return emb
