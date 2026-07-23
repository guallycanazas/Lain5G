from fastapi import APIRouter, Depends, Query

from ..dependencies import get_preparation_service, require_mutations_enabled
from ..models.preparation import ComponentPullRequest, ComponentPullResponse, PreparationReport, ProfileComponentStatus
from ..services.preparation_service import PreparationService


router = APIRouter(prefix="/api/preparation", tags=["preparation"])


@router.get("", response_model=PreparationReport)
def preparation_report(service: PreparationService = Depends(get_preparation_service)) -> PreparationReport:
    return service.report()


@router.get("/profiles/{profile_id}", response_model=ProfileComponentStatus)
def profile_components(
    profile_id: str,
    core_only: bool = Query(default=False),
    service: PreparationService = Depends(get_preparation_service),
) -> ProfileComponentStatus:
    return service.profile_status(profile_id, core_only)


@router.post("/profiles/{profile_id}/pull", response_model=ComponentPullResponse, dependencies=[Depends(require_mutations_enabled)])
def pull_profile_components(
    profile_id: str,
    payload: ComponentPullRequest,
    service: PreparationService = Depends(get_preparation_service),
) -> ComponentPullResponse:
    return service.pull(profile_id, payload.core_only)
