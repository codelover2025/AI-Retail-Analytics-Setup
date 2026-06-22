import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend_core.models.identity import Employee
from backend_core.schemas.identity import EmployeeCreateIn, EmployeeOut, EmployeeUpdateIn
from shared.config import Settings, get_settings
from shared.face_enrollment import embedding_from_upload, check_duplicate_face
from shared.identity.visitor_sync import upsert_employee_visitor


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class IdentityEmployeeService:
    def __init__(self, db: Session, settings: Settings | None = None):
        self.db = db
        self.settings = settings or get_settings()

    def list_employees(
        self, brand_id: uuid.UUID, limit: int = 200, *, active_only: bool = False
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

        # Check duplicate face
        if payload.embedding:
            is_dup, dup_name = check_duplicate_face(self.db, payload.embedding, current_person_id=emp_id)
            if is_dup:
                raise HTTPException(
                    status_code=400,
                    detail=f"Face embedding already matches existing enrolled person: {dup_name}"
                )

        embedding = payload.embedding if payload.embedding is not None else []

        if existing is None:
            existing = Employee(
                id=emp_id,
                brand_id=brand_id,
                name=payload.name,
                embedding=embedding,
                active=True,
                email=payload.email,
                phone=payload.phone,
                department=payload.department,
                designation=payload.designation,
                store_id=payload.store_id,
                branch=payload.branch,
                joining_date=payload.joining_date,
                employee_code=payload.employee_code,
            )
            self.db.add(existing)
        else:
            existing.brand_id = brand_id
            existing.name = payload.name
            if payload.embedding is not None:
                existing.embedding = payload.embedding
            existing.active = True
            existing.email = payload.email
            existing.phone = payload.phone
            existing.department = payload.department
            existing.designation = payload.designation
            existing.store_id = payload.store_id
            existing.branch = payload.branch
            existing.joining_date = payload.joining_date
            existing.employee_code = payload.employee_code
            existing.updated_at = _utcnow()

        if existing.embedding and len(existing.embedding) > 0:
            upsert_employee_visitor(
                self.db,
                self.settings,
                employee_id=existing.id,
                name=existing.name,
                embedding=existing.embedding,
                brand_id=brand_id,
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
        # Check duplicate face
        is_dup, dup_name = check_duplicate_face(self.db, embedding, current_person_id=employee_id)
        if is_dup:
            raise HTTPException(
                status_code=400,
                detail=f"Face embedding already matches existing enrolled person: {dup_name}"
            )

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

        # Check duplicate face
        is_dup, dup_name = check_duplicate_face(self.db, embedding, current_person_id=employee_id)
        if is_dup:
            raise HTTPException(
                status_code=400,
                detail=f"Face embedding already matches existing enrolled person: {dup_name}"
            )

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
            brand_id=brand_id,
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
        if payload.email is not None:
            emp.email = payload.email
        if payload.phone is not None:
            emp.phone = payload.phone
        if payload.department is not None:
            emp.department = payload.department
        if payload.designation is not None:
            emp.designation = payload.designation
        if payload.store_id is not None:
            emp.store_id = payload.store_id
        if payload.branch is not None:
            emp.branch = payload.branch
        if payload.joining_date is not None:
            emp.joining_date = payload.joining_date
        if payload.employee_code is not None:
            emp.employee_code = payload.employee_code

        emp.updated_at = _utcnow()
        if emp.brand_id is None:
            emp.brand_id = brand_id
        if emp.active and emp.embedding and len(emp.embedding) > 0:
            upsert_employee_visitor(
                self.db,
                self.settings,
                employee_id=emp.id,
                name=emp.name,
                embedding=emp.embedding,
                brand_id=brand_id,
            )
        self.db.commit()
        self.db.refresh(emp)
        return self._to_out(emp)

    def delete_employee(self, employee_id: uuid.UUID, brand_id: uuid.UUID) -> None:
        emp = self.get_employee(employee_id)
        if emp.brand_id is not None and emp.brand_id != brand_id:
            raise HTTPException(status_code=404, detail="Employee not found")
        
        # delete linked visitor
        from shared.identity.visitor_sync import find_employee_visitor
        visitor = find_employee_visitor(self.db, self.settings, brand_id, employee_id)
        if visitor:
            self.db.delete(visitor)

        self.db.delete(emp)
        self.db.commit()

    def delete_employee_face(self, employee_id: uuid.UUID, brand_id: uuid.UUID) -> EmployeeOut:
        emp = self.get_employee(employee_id)
        if emp.brand_id is not None and emp.brand_id != brand_id:
            raise HTTPException(status_code=404, detail="Employee not found")
        emp.embedding = []
        emp.updated_at = _utcnow()

        # delete linked visitor
        from shared.identity.visitor_sync import find_employee_visitor
        visitor = find_employee_visitor(self.db, self.settings, brand_id, employee_id)
        if visitor:
            self.db.delete(visitor)

        self.db.commit()
        self.db.refresh(emp)
        return self._to_out(emp)

    @staticmethod
    def _to_out(emp: Employee) -> EmployeeOut:
        has_face = bool(emp.embedding and len(emp.embedding) > 0)
        return EmployeeOut(
            id=str(emp.id),
            name=emp.name,
            active=emp.active,
            created_at=emp.created_at,
            updated_at=emp.updated_at,
            email=emp.email,
            phone=emp.phone,
            department=emp.department,
            designation=emp.designation,
            store_id=emp.store_id,
            branch=emp.branch,
            joining_date=emp.joining_date,
            employee_code=emp.employee_code,
            has_face_enrolled=has_face,
        )
