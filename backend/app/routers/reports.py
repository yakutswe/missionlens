from fastapi import APIRouter, HTTPException, status

from backend.app.models.report import ReportCreate, ReportResponse
from backend.app.services.report_store import (
    DuplicateReportError,
    report_store,
)


router = APIRouter(
    prefix="/api/v1/reports",
    tags=["reports"],
)


@router.post(
    "",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a mission report",
)
async def create_report(report_data: ReportCreate) -> ReportResponse:
    try:
        return report_store.create(report_data)
    except DuplicateReportError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "duplicate_report",
                "message": str(error),
                "external_id": error.external_id,
            },
        ) from error


@router.get(
    "",
    response_model=list[ReportResponse],
    summary="List ingested reports",
)
async def list_reports() -> list[ReportResponse]:
    return report_store.list_all()