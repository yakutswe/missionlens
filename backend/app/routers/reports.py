from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from backend.app.models.report import (
    ReportCreate,
    ReportResponse,
    SourceType,
)
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
    summary="Search ingested reports",
)
async def list_reports(
    language: Annotated[
        str | None,
        Query(
            pattern=r"^[a-z]{2,3}(?:-[A-Z]{2})?$",
            description="Filter by language code.",
        ),
    ] = None,
    source_type: Annotated[
        SourceType | None,
        Query(description="Filter by report source type."),
    ] = None,
    min_latitude: Annotated[
        float | None,
        Query(ge=-90, le=90),
    ] = None,
    max_latitude: Annotated[
        float | None,
        Query(ge=-90, le=90),
    ] = None,
    min_longitude: Annotated[
        float | None,
        Query(ge=-180, le=180),
    ] = None,
    max_longitude: Annotated[
        float | None,
        Query(ge=-180, le=180),
    ] = None,
) -> list[ReportResponse]:
    coordinates = (
        min_latitude,
        max_latitude,
        min_longitude,
        max_longitude,
    )

    has_any_coordinate = any(
        value is not None for value in coordinates
    )
    has_all_coordinates = all(
        value is not None for value in coordinates
    )

    if has_any_coordinate and not has_all_coordinates:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "code": "incomplete_bounding_box",
                "message": "All four geographic boundaries are required.",
            },
        )

    if (
        min_latitude is not None
        and max_latitude is not None
        and min_latitude > max_latitude
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "code": "invalid_latitude_range",
                "message": "min_latitude cannot exceed max_latitude.",
            },
        )

    if (
        min_longitude is not None
        and max_longitude is not None
        and min_longitude > max_longitude
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "code": "invalid_longitude_range",
                "message": "min_longitude cannot exceed max_longitude.",
            },
        )

    return report_store.search(
        language=language,
        source_type=source_type,
        min_latitude=min_latitude,
        max_latitude=max_latitude,
        min_longitude=min_longitude,
        max_longitude=max_longitude,
    )