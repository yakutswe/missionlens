from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SourceType(StrEnum):
    FIELD_REPORT = "field_report"
    SENSOR = "sensor"
    OPEN_SOURCE = "open_source"
    PARTNER = "partner"


class ReportStatus(StrEnum):
    RECEIVED = "received"
    PROCESSED = "processed"


class GeoPoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    latitude: float = Field(
        ge=-90,
        le=90,
        description="Latitude in decimal degrees.",
    )
    longitude: float = Field(
        ge=-180,
        le=180,
        description="Longitude in decimal degrees.",
    )


class ReportCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    external_id: str = Field(
        min_length=3,
        max_length=100,
        pattern=r"^[A-Za-z0-9._-]+$",
        description="Stable identifier supplied by the source system.",
    )
    title: str = Field(
        min_length=3,
        max_length=200,
    )
    content: str = Field(
        min_length=20,
        max_length=20_000,
    )
    language: str = Field(
        pattern=r"^[a-z]{2,3}(?:-[A-Z]{2})?$",
        description="BCP 47-style language code, such as en, tr, or en-US.",
    )
    source_type: SourceType
    source_name: str = Field(
        min_length=2,
        max_length=120,
    )
    location: GeoPoint
    observed_at: datetime

    @field_validator("observed_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("observed_at must include a timezone")

        return value


class ReportResponse(ReportCreate):
    id: UUID
    status: ReportStatus
    ingested_at: datetime