import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend_core.models.identity import Employee
from backend_core.schemas.identity import EmployeeCreateIn, EmployeeOut


class IdentityEmployeeService:
    def __init__(self, db: Session):
        self.db = db

    def list_employees(self, limit: int = 200) -> list[EmployeeOut]:
        rows = (
            self.db.execute(
                select(Employee).order_by(Employee.created_at.desc()).limit(limit)
            )
            .scalars()
            .all()
        )
        return [
            EmployeeOut(
                id=str(e.id),
                name=e.name,
                created_at=e.created_at,
            )
            for e in rows
        ]

    def create_employee(self, payload: EmployeeCreateIn) -> EmployeeOut:
        emp_id = uuid.UUID(payload.id) if payload.id else uuid.uuid4()
        existing = self.db.get(Employee, emp_id)

        if existing is None:
            existing = Employee(
                id=emp_id,
                name=payload.name,
                embedding=payload.embedding,
            )
            self.db.add(existing)
        else:
            existing.name = payload.name
            existing.embedding = payload.embedding

        self.db.commit()
        self.db.refresh(existing)
        return EmployeeOut(
            id=str(existing.id),
            name=existing.name,
            created_at=existing.created_at,
        )
