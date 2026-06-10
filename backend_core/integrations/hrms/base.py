"""HRMS integration adapter base — Module 7 (Phase 4)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional


class HRMSEmployee:
    """Normalized employee record from any HRMS provider."""
    def __init__(
        self,
        external_id: str,
        name: str,
        department: Optional[str] = None,
        designation: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        is_active: bool = True,
        extra: Optional[dict] = None,
    ) -> None:
        self.external_id = external_id
        self.name = name
        self.department = department
        self.designation = designation
        self.email = email
        self.phone = phone
        self.is_active = is_active
        self.extra = extra or {}


class HRMSAttendanceRecord:
    """Normalized attendance record."""
    def __init__(
        self,
        employee_external_id: str,
        date: str,   # ISO date string
        status: str = "present",
        check_in: Optional[str] = None,
        check_out: Optional[str] = None,
    ) -> None:
        self.employee_external_id = employee_external_id
        self.date = date
        self.status = status
        self.check_in = check_in
        self.check_out = check_out


class HRMSAdapter(ABC):
    """Abstract HRMS integration adapter."""

    @abstractmethod
    def sync_employees(self, brand_id: str) -> list[HRMSEmployee]:
        """Fetch and return all active employees from the HRMS."""
        ...

    @abstractmethod
    def sync_attendance(self, brand_id: str, date: str) -> list[HRMSAttendanceRecord]:
        """Fetch attendance records for a specific date."""
        ...

    @abstractmethod
    def get_employee_profile(self, external_id: str) -> Optional[HRMSEmployee]:
        """Fetch a single employee profile by external ID."""
        ...
