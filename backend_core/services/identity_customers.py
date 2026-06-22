import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Mapped, Session

from backend_core.models.identity import Customer, FaceEmbedding, PersonRecognition
from backend_core.schemas.identity import CustomerOut, RepeatVisitorOut, CustomerCreateIn, CustomerUpdateIn
from shared.config import Settings, get_settings
from shared.face_enrollment import embedding_from_upload, check_duplicate_face
from shared.database.models import Visitor
from shared.tenant_resolve import resolve_brand_id


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class IdentityCustomerService:
    def __init__(self, db: Session, settings: Settings | None = None):
        self.db = db
        self.settings = settings or get_settings()

    def list_customers(self, brand_id: uuid.UUID, limit: int = 500) -> list[CustomerOut]:
        rows = (
            self.db.execute(
                select(Customer)
                .where(Customer.brand_id == brand_id)
                .order_by(Customer.last_seen.desc())
                .limit(limit)
            )
            .scalars()
            .all()
        )
        return [self._to_out(c) for c in rows]

    def get_customer(self, customer_id: uuid.UUID) -> Customer:
        cust = self.db.get(Customer, customer_id)
        if cust is None:
            raise HTTPException(status_code=404, detail="Customer not found")
        return cust

    def create_customer(self, brand_id: uuid.UUID, payload: CustomerCreateIn) -> CustomerOut:
        person_id = uuid.UUID(payload.id) if payload.id else uuid.uuid4()
        existing = self.db.get(Customer, person_id)

        # Check duplicate face
        if payload.embedding:
            is_dup, dup_name = check_duplicate_face(self.db, payload.embedding, current_person_id=person_id)
            if is_dup:
                raise HTTPException(
                    status_code=400,
                    detail=f"Face embedding already matches existing enrolled person: {dup_name}"
                )

        if existing is None:
            existing = Customer(
                id=person_id,
                brand_id=brand_id,
                first_seen=payload.first_seen or _utcnow(),
                last_seen=payload.last_seen or _utcnow(),
                visit_count=payload.visit_count if payload.visit_count is not None else 0,
                name=payload.name,
                phone=payload.phone,
                email=payload.email,
                membership_id=payload.membership_id,
                loyalty_points=payload.loyalty_points if payload.loyalty_points is not None else 0,
                is_vip=payload.is_vip if payload.is_vip is not None else False,
                preferred_store=payload.preferred_store,
                notes=payload.notes,
                is_watchlist=payload.is_watchlist if payload.is_watchlist is not None else False,
            )
            self.db.add(existing)
        else:
            existing.brand_id = brand_id
            if payload.first_seen is not None:
                existing.first_seen = payload.first_seen
            if payload.last_seen is not None:
                existing.last_seen = payload.last_seen
            if payload.visit_count is not None:
                existing.visit_count = payload.visit_count
            existing.name = payload.name
            existing.phone = payload.phone
            existing.email = payload.email
            existing.membership_id = payload.membership_id
            if payload.loyalty_points is not None:
                existing.loyalty_points = payload.loyalty_points
            if payload.is_vip is not None:
                existing.is_vip = payload.is_vip
            existing.preferred_store = payload.preferred_store
            existing.notes = payload.notes
            if payload.is_watchlist is not None:
                existing.is_watchlist = payload.is_watchlist

        self.db.flush()

        # Enroll embedding if provided
        if payload.embedding:
            emb = FaceEmbedding(customer_id=existing.id, embedding=payload.embedding)
            self.db.add(emb)
            self.db.flush()
            self.sync_customer_visitor(existing, payload.embedding)
        else:
            self.sync_customer_visitor(existing)

        self.db.commit()
        self.db.refresh(existing)
        return self._to_out(existing)

    def create_or_update_customer(
        self,
        *,
        person_id: uuid.UUID,
        brand_id: uuid.UUID,
        first_seen: datetime | None,
        last_seen: datetime | None,
        visit_count: int | None = None,
    ) -> Customer:
        """Create or update a customer profile from legacy ingest (does not modify other fields)."""
        cust = self.db.get(Customer, person_id)
        if cust is None:
            cust = Customer(
                id=person_id,
                brand_id=brand_id,
                first_seen=first_seen or _utcnow(),
                last_seen=last_seen or _utcnow(),
                visit_count=visit_count if visit_count is not None else 1,
            )
            self.db.add(cust)
            self.db.flush()
            return cust

        if cust.brand_id is None:
            cust.brand_id = brand_id
        if first_seen is not None:
            cust.first_seen = min(cust.first_seen, first_seen)
        if last_seen is not None:
            cust.last_seen = max(cust.last_seen, last_seen)
        if visit_count is not None:
            cust.visit_count = visit_count
        return cust

    def update_customer(self, customer_id: uuid.UUID, brand_id: uuid.UUID, payload: CustomerUpdateIn) -> CustomerOut:
        cust = self.get_customer(customer_id)
        if cust.brand_id is not None and cust.brand_id != brand_id:
            raise HTTPException(status_code=404, detail="Customer not found")

        if payload.first_seen is not None:
            cust.first_seen = payload.first_seen
        if payload.last_seen is not None:
            cust.last_seen = payload.last_seen
        if payload.visit_count is not None:
            cust.visit_count = payload.visit_count
        if payload.name is not None:
            cust.name = payload.name
        if payload.phone is not None:
            cust.phone = payload.phone
        if payload.email is not None:
            cust.email = payload.email
        if payload.membership_id is not None:
            cust.membership_id = payload.membership_id
        if payload.loyalty_points is not None:
            cust.loyalty_points = payload.loyalty_points
        if payload.is_vip is not None:
            cust.is_vip = payload.is_vip
        if payload.preferred_store is not None:
            cust.preferred_store = payload.preferred_store
        if payload.notes is not None:
            cust.notes = payload.notes
        if payload.is_watchlist is not None:
            cust.is_watchlist = payload.is_watchlist

        self.db.flush()
        self.sync_customer_visitor(cust)
        self.db.commit()
        self.db.refresh(cust)
        return self._to_out(cust)

    def delete_customer(self, customer_id: uuid.UUID, brand_id: uuid.UUID) -> None:
        cust = self.get_customer(customer_id)
        if cust.brand_id is not None and cust.brand_id != brand_id:
            raise HTTPException(status_code=404, detail="Customer not found")

        # delete visitor row
        visitor = self.db.get(Visitor, customer_id)
        if visitor:
            self.db.delete(visitor)

        self.db.delete(cust)
        self.db.commit()

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

        # Check duplicate face
        is_dup, dup_name = check_duplicate_face(self.db, embedding, current_person_id=customer_id)
        if is_dup:
            raise HTTPException(
                status_code=400,
                detail=f"Face embedding already matches existing enrolled person: {dup_name}"
            )

        emb = FaceEmbedding(customer_id=cust.id, embedding=embedding)
        self.db.add(emb)
        self.db.flush()
        self.sync_customer_visitor(cust, embedding)
        self.db.commit()
        self.db.refresh(emb)
        return emb

    def delete_customer_face(self, customer_id: uuid.UUID, brand_id: uuid.UUID) -> CustomerOut:
        cust = self.get_customer(customer_id)
        if cust.brand_id is not None and cust.brand_id != brand_id:
            raise HTTPException(status_code=404, detail="Customer not found")

        # Delete all customer embeddings
        stmt = select(FaceEmbedding).where(FaceEmbedding.customer_id == customer_id)
        embs = self.db.scalars(stmt).all()
        for e in embs:
            self.db.delete(e)
        self.db.flush()

        # delete/prune visitor row
        visitor = self.db.get(Visitor, customer_id)
        if visitor:
            self.db.delete(visitor)

        self.db.commit()
        self.db.refresh(cust)
        return self._to_out(cust)

    def sync_customer_visitor(self, customer: Customer, embedding: list[float] | None = None) -> Optional[Visitor]:
        """Sync Customer data to Visitor table for immediate Edge recognition."""
        visitor = self.db.get(Visitor, customer.id)

        if not embedding:
            # Check if there is an existing FaceEmbedding
            stmt = select(FaceEmbedding).where(FaceEmbedding.customer_id == customer.id).order_by(FaceEmbedding.created_at.desc()).limit(1)
            latest_emb = self.db.scalar(stmt)
            if latest_emb:
                embedding = latest_emb.embedding

        if not embedding:
            if visitor:
                self.db.delete(visitor)
                self.db.flush()
            return None

        display_name = customer.name or f"Customer-{str(customer.id)[:8]}"

        if visitor is None:
            visitor = Visitor(
                id=customer.id,
                brand_id=customer.brand_id or resolve_brand_id(self.db, self.settings),
                embedding=embedding,
                display_name=display_name,
                is_vip=customer.is_vip or False,
                visit_count=customer.visit_count or 0,
                first_seen_at=customer.first_seen,
                last_seen_at=customer.last_seen,
                metadata_={
                    "person_id": int(customer.id.int % (10**9)),
                    "person_kind": "customer",
                    "is_watchlist": customer.is_watchlist or False,
                }
            )
            self.db.add(visitor)
        else:
            visitor.embedding = embedding
            visitor.display_name = display_name
            visitor.is_vip = customer.is_vip or False
            visitor.visit_count = customer.visit_count or 0
            visitor.first_seen_at = customer.first_seen
            visitor.last_seen_at = customer.last_seen
            meta = dict(visitor.metadata_ or {})
            meta["person_kind"] = "customer"
            meta["is_watchlist"] = customer.is_watchlist or False
            visitor.metadata_ = meta

        self.db.flush()
        return visitor

    def list_repeat_visitors_filtered(self, brand_id: uuid.UUID, min_visits: int = 2, limit: int = 500) -> list[RepeatVisitorOut]:
        subquery = (
            select(
                PersonRecognition.person_id,
                func.min(PersonRecognition.timestamp).label("first_seen"),
                func.max(PersonRecognition.timestamp).label("last_seen"),
                func.count().label("visit_count"),
            )
            .where(
                PersonRecognition.brand_id == brand_id,
                PersonRecognition.type.in_(("customer", "new_visitor", "repeat_visitor", "visitor"))
            )
            .group_by(PersonRecognition.person_id)
            .having(func.count() >= min_visits)
            .subquery()
        )
        
        stmt = (
            select(subquery, Customer)
            .outerjoin(Customer, subquery.c.person_id == Customer.id)
            .where((Customer.brand_id == brand_id) | (Customer.brand_id.is_(None)))
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

    def upsert_from_recognition(self, person_id: uuid.UUID, brand_id: uuid.UUID, ts: datetime) -> Customer:
        """Used by ingestion endpoint: increment counts based on recognition stream."""
        cust = self.db.get(Customer, person_id)
        if cust is None:
            cust = Customer(
                id=person_id,
                brand_id=brand_id,
                first_seen=ts,
                last_seen=ts,
                visit_count=1,
            )
            self.db.add(cust)
            return cust
        if cust.brand_id is None:
            cust.brand_id = brand_id
        if ts < cust.first_seen:
            cust.first_seen = ts
        if ts > cust.last_seen:
            cust.last_seen = ts
        cust.visit_count += 1
        return cust

    def _to_out(self, c: Customer) -> CustomerOut:
        # Check if customer has face enrolled
        stmt = select(func.count()).select_from(FaceEmbedding).where(FaceEmbedding.customer_id == c.id)
        count = self.db.scalar(stmt) or 0
        has_face = count > 0
        return CustomerOut(
            id=str(c.id),
            first_seen=c.first_seen,
            last_seen=c.last_seen,
            visit_count=c.visit_count,
            name=c.name,
            phone=c.phone,
            email=c.email,
            membership_id=c.membership_id,
            loyalty_points=c.loyalty_points,
            is_vip=c.is_vip,
            preferred_store=c.preferred_store,
            notes=c.notes,
            is_watchlist=c.is_watchlist,
            has_face_enrolled=has_face,
        )
