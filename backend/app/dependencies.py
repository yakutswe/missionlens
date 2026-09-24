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
from backend.app.services.case_repository import CaseRepository
from backend.app.services.postgres_case_store import PostgresCaseStore


DatabaseSession = Annotated[
    Session,
    Depends(get_db_session),
]


def get_report_repository(
    session: DatabaseSession,
) -> ReportRepository:
    """Provide PostgreSQL-backed report persistence to the API."""

    return PostgresReportStore(session)


def get_case_repository(session: DatabaseSession) -> CaseRepository:
    """Provide PostgreSQL-backed case persistence to the API."""
    return PostgresCaseStore(session)
