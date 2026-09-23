from datetime import datetime
from uuid import UUID, uuid4

from geoalchemy2 import Geometry
from geoalchemy2.elements import WKBElement
from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class ReportRecord(Base):
    __tablename__ = "reports"

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    external_id: Mapped[str] = mapped_column(
        String(128),
        unique=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text)
    language: Mapped[str] = mapped_column(
        String(35),
        index=True,
    )
    source_type: Mapped[str] = mapped_column(
        String(64),
        index=True,
    )
    source_name: Mapped[str] = mapped_column(String(255))
    location: Mapped[WKBElement] = mapped_column(
        Geometry(
            geometry_type="POINT",
            srid=4326,
            spatial_index=True,
        )
    )
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default="received",
    )
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
    )