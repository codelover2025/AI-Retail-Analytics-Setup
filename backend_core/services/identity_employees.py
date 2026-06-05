import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend_core.models.identity import Employee
from backend_core.schemas.identity import EmployeeCreateIn, EmployeeOut, EmployeeUpdateIn
from shared.config import Settings, get_settings
from shared.face_enrollment import embedding_from_upload
from shared.identity.visitor_sync import upsert_employee_visitor


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class IdentityEmployeeService:
    def __init__(self, db: Session, settings: Settings | None = None):
        self.db = db
        self.settings = settings or get_settings()

    def list_employees(
        self, brand_id: uuid.UUID, limit: int = 200, *, active_only: bool = True
    ) -> list[EmployeeOut]:
        stmt = select(Employee).where(Employee.brand_id == brand_id).order_by(Employee.created_at.desc()).limit(limit)
        if active_only:
            stmt = stmt.where(Employee.active.is_(True))
        rows = self.db.execute(stmt).scalars().all()
        return [self._to_out(e) for e in rows]

    def get_employee(self, employee_id: uuid.UUID) -> Employee:
        emp = self.db.get(Employee, employee_id)
        if emp is None:
            raise HTTPException(status_code=404, detail="Employee not found")
        return emp

    def create_employee(self, brand_id: uuid.UUID, payload: EmployeeCreateIn) -> EmployeeOut:
        emp_id = uuid.UUID(payload.id) if payload.id else uuid.uuid4()
        existing = self.db.get(Employee, emp_id)

        if existing is None:
            existing = Employee(
                id=emp_id,
                brand_id=brand_id,
                name=payload.name,
                embedding=payload.embedding,
                active=True,
            )
            self.db.add(existing)
        else:
            existing.brand_id = brand_id
            existing.name = payload.name
            existing.embedding = payload.embedding
            existing.active = True
            existing.updated_at = _utcnow()

        upsert_employee_visitor(
            self.db,
            self.settings,
            employee_id=existing.id,
            name=existing.name,
            embedding=existing.embedding,
        )
        self.db.commit()
        self.db.refresh(existing)
        return self._to_out(existing)

    def create_employee_from_images(
        self,
        *,
        brand_id: uuid.UUID,
        name: str,
        files: list,
        employee_id: uuid.UUID | None = None,
    ) -> EmployeeOut:
        embedding = embedding_from_upload(files)
        payload = EmployeeCreateIn(
            id=str(employee_id) if employee_id else None,
            name=name,
            embedding=embedding,
        )
        return self.create_employee(brand_id, payload)

    def re_enroll_from_images(self, employee_id: uuid.UUID, brand_id: uuid.UUID, files: list) -> EmployeeOut:
        emp = self.get_employee(employee_id)
        if emp.brand_id is not None and emp.brand_id != brand_id:
            raise HTTPException(status_code=404, detail="Employee not found")
        if not emp.active:
            raise HTTPException(status_code=400, detail="Employee is inactive")
        embedding = embedding_from_upload(files)
        emp.embedding = embedding
        emp.updated_at = _utcnow()
        if emp.brand_id is None:
            emp.brand_id = brand_id
        upsert_employee_visitor(
            self.db,
            self.settings,
            employee_id=emp.id,
            name=emp.name,
            embedding=embedding,
        )
        self.db.commit()
        self.db.refresh(emp)
        return self._to_out(emp)

    def update_employee(
        self, employee_id: uuid.UUID, brand_id: uuid.UUID, payload: EmployeeUpdateIn
    ) -> EmployeeOut:
        emp = self.get_employee(employee_id)
        if emp.brand_id is not None and emp.brand_id != brand_id:
            raise HTTPException(status_code=404, detail="Employee not found")
        if payload.name is not None:
            emp.name = payload.name
        if payload.active is not None:
            emp.active = payload.active
        emp.updated_at = _utcnow()
        if emp.brand_id is None:
            emp.brand_id = brand_id
        if emp.active:
            upsert_employee_visitor(
                self.db,
                self.settings,
                employee_id=emp.id,
                name=emp.name,
                embedding=emp.embedding,
            )
        self.db.commit()
        self.db.refresh(emp)
        return self._to_out(emp)

    @staticmethod
    def _to_out(emp: Employee) -> EmployeeOut:
        return EmployeeOut(
            id=str(emp.id),
            name=emp.name,
            active=emp.active,
            created_at=emp.created_at,
            updated_at=emp.updated_at,
        )
