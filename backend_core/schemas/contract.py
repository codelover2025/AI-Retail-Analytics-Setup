"""Strict HTTP response shapes for dashboard consumption."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


class LiveVisitorsResponse(BaseModel):
    count: int
    timestamp: datetime


RecognitionType = Literal["vip", "new_visitor", "repeat_visitor", "visitor"]


class RecognitionItem(BaseModel):
    id: str
    type: RecognitionType
    time: datetime


class FootfallDailyPoint(BaseModel):
    day: date
    unique_visitors: int
    total_detections: int


class FootfallHourlyPoint(BaseModel):
    bucket_start: datetime = Field(
        ...,
        description="UTC hour bucket start from PostgreSQL date_trunc('hour', ...)",
    )
    count: int


class FootfallResponse(BaseModel):
    daily: list[FootfallDailyPoint]
    hourly: list[FootfallHourlyPoint]


class AlertItem(BaseModel):
    type: str
    message: str
    time: datetime
