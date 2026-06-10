"""Generic REST HRMS adapter — Module 7 (Phase 4)."""

from __future__ import annotations

import logging
from typing import Optional

import httpx

from backend_core.integrations.hrms.base import HRMSAdapter, HRMSAttendanceRecord, HRMSEmployee

logger = logging.getLogger(__name__)


class GenericHRMSAdapter(HRMSAdapter):
    """
    REST-based generic HRMS adapter.

    Expects the HRMS to expose:
      GET {base_url}/employees          → [{id, name, department, ...}]
      GET {base_url}/attendance?date=X  → [{employee_id, status, ...}]
      GET {base_url}/employees/{id}     → {id, name, ...}
    """

    def __init__(self, api_url: str, api_key: Optional[str] = None, timeout: float = 15.0) -> None:
        self._url = api_url.rstrip("/")
        self._headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        self._timeout = timeout

    def sync_employees(self, brand_id: str) -> list[HRMSEmployee]:
        try:
            resp = httpx.get(
                f"{self._url}/employees",
                headers=self._headers,
                params={"brand_id": brand_id},
                timeout=self._timeout,
            )
            resp.raise_for_status()
            return [
                HRMSEmployee(
                    external_id=str(e.get("id", "")),
                    name=e.get("name", ""),
                    department=e.get("department"),
                    designation=e.get("designation"),
                    email=e.get("email"),
                    phone=e.get("phone"),
                    is_active=e.get("is_active", True),
                    extra=e,
                )
                for e in resp.json()
            ]
        except Exception as exc:
            logger.error("HRMS sync_employees failed: %s", exc)
            return []

    def sync_attendance(self, brand_id: str, date: str) -> list[HRMSAttendanceRecord]:
        try:
            resp = httpx.get(
                f"{self._url}/attendance",
                headers=self._headers,
                params={"brand_id": brand_id, "date": date},
                timeout=self._timeout,
            )
            resp.raise_for_status()
            return [
                HRMSAttendanceRecord(
                    employee_external_id=str(r.get("employee_id", "")),
                    date=date,
                    status=r.get("status", "present"),
                    check_in=r.get("check_in"),
                    check_out=r.get("check_out"),
                )
                for r in resp.json()
            ]
        except Exception as exc:
            logger.error("HRMS sync_attendance failed: %s", exc)
            return []

    def get_employee_profile(self, external_id: str) -> Optional[HRMSEmployee]:
        try:
            resp = httpx.get(
                f"{self._url}/employees/{external_id}",
                headers=self._headers,
                timeout=self._timeout,
            )
            resp.raise_for_status()
            e = resp.json()
            return HRMSEmployee(
                external_id=str(e.get("id", external_id)),
                name=e.get("name", ""),
                department=e.get("department"),
                designation=e.get("designation"),
                email=e.get("email"),
                phone=e.get("phone"),
                is_active=e.get("is_active", True),
                extra=e,
            )
        except Exception as exc:
            logger.error("HRMS get_employee_profile failed: %s", exc)
            return None


class StubHRMSAdapter(HRMSAdapter):
    """No-op adapter for testing — returns empty data."""

    def sync_employees(self, brand_id: str) -> list[HRMSEmployee]:
        logger.info("[HRMS STUB] sync_employees called")
        return []

    def sync_attendance(self, brand_id: str, date: str) -> list[HRMSAttendanceRecord]:
        logger.info("[HRMS STUB] sync_attendance called for %s", date)
        return []

    def get_employee_profile(self, external_id: str) -> Optional[HRMSEmployee]:
        logger.info("[HRMS STUB] get_employee_profile: %s", external_id)
        return None
