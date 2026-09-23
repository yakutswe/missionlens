from datetime import datetime, timezone
from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel


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
        "Secure mission-intelligence API for multilingual reports, "
        "geospatial events, cases, approvals, and audit history."
    ),
    version=SERVICE_VERSION,
)


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["system"],
    summary="Check API health",
)
async def health_check() -> HealthResponse:
    """Confirm that the MissionLens API process is available."""

    return HealthResponse(
        status="healthy",
        service=SERVICE_NAME,
        version=SERVICE_VERSION,
        timestamp=datetime.now(timezone.utc),
    )