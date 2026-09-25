from datetime import datetime, timezone
from typing import Literal

from fastapi import FastAPI
from fastapi import Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.app.db.session import get_db_session

from backend.app.routers.reports import router as reports_router
from backend.app.routers.cases import router as cases_router
from backend.app.routers.approvals import router as approvals_router


SERVICE_NAME = "missionlens-api"
SERVICE_VERSION = "0.1.0"


class HealthResponse(BaseModel):
    status: Literal["healthy"]
    service: str
    version: str
    timestamp: datetime


app = FastAPI(
    title="MissionLens API",
    description=(
        "Local portfolio API for synthetic multilingual geospatial reports "
        "and linked investigation cases. A synthetic-only demo approval and "
        "audit workflow is provided; demo actor headers are not authentication."
    ),
    version=SERVICE_VERSION,
)

app.include_router(reports_router)
app.include_router(cases_router)
app.include_router(approvals_router)


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["system"],
    summary="Check API health",
)
async def health_check() -> HealthResponse:
    """Confirm the API process is available; /ready checks the database."""

    return HealthResponse(
        status="healthy",
        service=SERVICE_NAME,
        version=SERVICE_VERSION,
        timestamp=datetime.now(timezone.utc),
    )


@app.get("/ready", tags=["system"], summary="Check database readiness")
def readiness_check(session: Session = Depends(get_db_session)) -> dict[str, str]:
    try:
        session.execute(text("SELECT 1"))
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=503,
            detail="Database unavailable",
        ) from error
    return {"status": "ready"}
