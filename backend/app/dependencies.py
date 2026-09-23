from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from backend.app.db.session import get_db_session
from backend.app.services.postgres_report_store import (
    PostgresReportStore,
)
from backend.app.services.report_repository import (
    ReportRepository,
)


DatabaseSession = Annotated[
    Session,
    Depends(get_db_session),
]


def get_report_repository(
    session: DatabaseSession,
) -> ReportRepository:
    """Provide PostgreSQL-backed report persistence to the API."""

    return PostgresReportStore(session)