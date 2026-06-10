"""Generic Pydantic pagination schema for paginated list responses."""

from __future__ import annotations

from typing import Generic, List, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated list envelope."""

    items: List[T]
    total: int = Field(description="Total number of matching records")
    page: int = Field(ge=1, description="Current 1-based page number")
    page_size: int = Field(ge=1, le=500, description="Items per page")
    pages: int = Field(ge=0, description="Total number of pages")

    @classmethod
    def build(
        cls,
        items: List[T],
        total: int,
        page: int,
        page_size: int,
    ) -> "PaginatedResponse[T]":
        pages = max(1, (total + page_size - 1) // page_size) if total else 0
        return cls(items=items, total=total, page=page, page_size=page_size, pages=pages)


def paginate(query_results: list, total: int, page: int, page_size: int) -> dict:
    """Helper to build paginated dict for any list."""
    pages = max(1, (total + page_size - 1) // page_size) if total else 0
    return {
        "items": query_results,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages,
    }
