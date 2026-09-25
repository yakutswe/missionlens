from geoalchemy2.elements import WKTElement
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.db.models import ReportRecord
from backend.app.models.report import (
    GeoPoint,
    ReportCreate,
    ReportResponse,
    ReportStatus,
    SourceType,
)
from backend.app.services.report_repository import DuplicateReportError, ReportPage

class PostgresReportStore:
    """Persist and search mission reports using PostgreSQL/PostGIS."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, report_data: ReportCreate) -> ReportResponse:
        record = ReportRecord(
            external_id=report_data.external_id,
            title=report_data.title,
            content=report_data.content,
            language=report_data.language,
            source_type=report_data.source_type.value,
            source_name=report_data.source_name,
            location=WKTElement(
                (
                    f"POINT("
                    f"{report_data.location.longitude} "
                    f"{report_data.location.latitude}"
                    f")"
                ),
                srid=4326,
            ),
            observed_at=report_data.observed_at,
            status=ReportStatus.RECEIVED.value,
        )

        self._session.add(record)

        try:
            self._session.commit()
            self._session.refresh(record)
        except IntegrityError as error:
            self._session.rollback()

            if getattr(error.orig, "sqlstate", None) == "23505":
                raise DuplicateReportError(
                    report_data.external_id
                ) from error

            raise

        return self._to_response(
            record=record,
            latitude=report_data.location.latitude,
            longitude=report_data.location.longitude,
        )

    def search_page(
        self,
        *,
        language: str | None = None,
        source_type: SourceType | None = None,
        min_latitude: float | None = None,
        max_latitude: float | None = None,
        min_longitude: float | None = None,
        max_longitude: float | None = None,
        query: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> ReportPage:
        conditions = []

        if language is not None:
            conditions.append(ReportRecord.language == language)

        if source_type is not None:
            conditions.append(ReportRecord.source_type == source_type.value)

        if query:
            # Treat %, _ and ! as ordinary text, not SQL LIKE wildcards.
            escaped = query.replace("!", "!!").replace("%", "!%").replace("_", "!_")
            pattern = f"%{escaped}%"
            conditions.append(or_(*(
                column.ilike(pattern, escape="!") for column in (
                    ReportRecord.title, ReportRecord.content,
                    ReportRecord.source_name, ReportRecord.external_id,
                )
            )))

        coordinates = (
            min_latitude,
            max_latitude,
            min_longitude,
            max_longitude,
        )

        if all(value is not None for value in coordinates):
            assert min_latitude is not None
            assert max_latitude is not None
            assert min_longitude is not None
            assert max_longitude is not None

            bounding_box = func.ST_MakeEnvelope(
                min_longitude,
                min_latitude,
                max_longitude,
                max_latitude,
                4326,
            )

            conditions.append(
                func.ST_Intersects(
                    ReportRecord.location,
                    bounding_box,
                )
            )

        total = self._session.scalar(
            select(func.count()).select_from(ReportRecord).where(*conditions)
        ) or 0
        statement = select(
            ReportRecord,
            func.ST_Y(ReportRecord.location).label("latitude"),
            func.ST_X(ReportRecord.location).label("longitude"),
        ).where(*conditions).order_by(
            ReportRecord.ingested_at.desc(), ReportRecord.id.desc()
        ).limit(limit).offset(offset)

        rows = self._session.execute(statement).all()

        items = [
            self._to_response(
                record=record,
                latitude=float(latitude),
                longitude=float(longitude),
            )
            for record, latitude, longitude in rows
        ]
        return ReportPage(items=items, total=total)

    def languages(self) -> list[str]:
        return list(self._session.scalars(
            select(ReportRecord.language).distinct().order_by(ReportRecord.language)
        ))

    @staticmethod
    def _to_response(
        *,
        record: ReportRecord,
        latitude: float,
        longitude: float,
    ) -> ReportResponse:
        return ReportResponse(
            id=record.id,
            external_id=record.external_id,
            title=record.title,
            content=record.content,
            language=record.language,
            source_type=SourceType(record.source_type),
            source_name=record.source_name,
            location=GeoPoint(
                latitude=latitude,
                longitude=longitude,
            ),
            observed_at=record.observed_at,
            status=ReportStatus(record.status),
            ingested_at=record.ingested_at,
        )
