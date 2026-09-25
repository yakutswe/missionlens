from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.dependencies import get_case_repository
from backend.app.models.case import CaseCreate, CaseResponse
from backend.app.services.case_repository import (
    CaseNotFoundError, CaseRepository, UnknownReportError,
)

router = APIRouter(prefix="/api/v1/cases", tags=["cases"])
CaseRepositoryDependency = Annotated[CaseRepository, Depends(get_case_repository)]


@router.post("", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
def create_case(data: CaseCreate, repository: CaseRepositoryDependency) -> CaseResponse:
    try:
        return repository.create(data)
    except UnknownReportError as error:
        raise HTTPException(
            status_code=422,
            detail={"code": "unknown_report", "report_id": str(error.report_id)},
        ) from error


@router.get("", response_model=list[CaseResponse])
def list_cases(repository: CaseRepositoryDependency) -> list[CaseResponse]:
    return repository.list_all()


@router.get("/{case_id}", response_model=CaseResponse)
def get_case(case_id: UUID, repository: CaseRepositoryDependency) -> CaseResponse:
    try:
        return repository.get(case_id)
    except CaseNotFoundError as error:
        raise HTTPException(status_code=404, detail="Case not found") from error
