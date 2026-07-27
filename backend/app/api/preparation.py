from fastapi import APIRouter, Depends, Query

from ..dependencies import get_preparation_service, require_mutations_enabled
from ..models.preparation import ComponentPullRequest, ComponentPullResponse, PreparationReport, ProfileComponentStatus
from ..services.image_catalog import PUBLIC_PROFILE_IDS
from ..services.preparation_service import PreparationError, PreparationService


router = APIRouter(prefix="/api/preparation", tags=["preparation"])


def require_public_profile(profile_id: str) -> None:
    if profile_id not in PUBLIC_PROFILE_IDS:
        raise PreparationError(404, "IMAGE_PROFILE_NOT_FOUND", f"Unknown image profile: {profile_id}")


@router.get("", response_model=PreparationReport)
def preparation_report(service: PreparationService = Depends(get_preparation_service)) -> PreparationReport:
    return service.report()


@router.get("/profiles/{profile_id}", response_model=ProfileComponentStatus)
def profile_components(
    profile_id: str,
    core_only: bool = Query(default=False),
    service: PreparationService = Depends(get_preparation_service),
) -> ProfileComponentStatus:
    require_public_profile(profile_id)
    return service.profile_status(profile_id, core_only)


@router.post("/profiles/{profile_id}/pull", response_model=ComponentPullResponse, dependencies=[Depends(require_mutations_enabled)])
def pull_profile_components(
    profile_id: str,
    payload: ComponentPullRequest,
    service: PreparationService = Depends(get_preparation_service),
) -> ComponentPullResponse:
    require_public_profile(profile_id)
    return service.pull(profile_id, payload.core_only)
