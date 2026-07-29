from fastapi import APIRouter, Depends, Query, Response, status

from ..dependencies import get_preparation_service, require_mutations_enabled
from ..models.preparation import ComponentPullJob, ComponentPullRequest, PreparationReport, ProfileComponentStatus
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


@router.get("/pulls/active", response_model=ComponentPullJob | None)
def active_pull(service: PreparationService = Depends(get_preparation_service)) -> ComponentPullJob | None:
    return service.active_pull()


@router.get("/pulls/{job_id}", response_model=ComponentPullJob)
def pull_status(job_id: str, service: PreparationService = Depends(get_preparation_service)) -> ComponentPullJob:
    return service.pull_job(job_id)


@router.post("/profiles/{profile_id}/pull", response_model=ComponentPullJob, status_code=status.HTTP_202_ACCEPTED, dependencies=[Depends(require_mutations_enabled)])
def pull_profile_components(
    profile_id: str,
    payload: ComponentPullRequest,
    response: Response,
    service: PreparationService = Depends(get_preparation_service),
) -> ComponentPullJob:
    if profile_id != "all":
        require_public_profile(profile_id)
    job = service.start_pull(profile_id, payload.core_only)
    response.headers["Location"] = f"/api/preparation/pulls/{job.job_id}"
    return job
