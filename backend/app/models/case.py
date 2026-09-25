from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CaseCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str = Field(min_length=3, max_length=200)
    summary: str = Field(min_length=10, max_length=2000)
    report_ids: list[UUID] = Field(min_length=1, max_length=50)

    @field_validator("report_ids")
    @classmethod
    def unique_reports(cls, value: list[UUID]) -> list[UUID]:
        if len(value) != len(set(value)):
            raise ValueError("report_ids must not contain duplicates")
        return value


class CaseResponse(CaseCreate):
    id: UUID
    created_at: datetime
    report_titles: list[str]
