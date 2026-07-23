from fastapi import APIRouter, Depends

from ..dependencies import settings_dependency
from ..models.deployment import HealthResponse
from ..settings import Settings

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(settings: Settings = Depends(settings_dependency)) -> HealthResponse:
    return HealthResponse(dry_run=settings.dry_run)
