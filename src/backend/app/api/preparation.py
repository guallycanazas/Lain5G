from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import FileResponse

from ..dependencies import get_preparation_service, require_mutations_enabled
from ..models.preparation import ComponentPullJob, ComponentPullRequest, InstallationRecord, PreparationReport, ProfileComponentStatus
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


@router.get("/installations", response_model=list[InstallationRecord])
def installation_history(
    limit: int = Query(default=50, ge=1, le=200),
    service: PreparationService = Depends(get_preparation_service),
) -> list[InstallationRecord]:
    return service.installation_records(limit)


@router.get("/installations/{record_id}", response_model=InstallationRecord)
def installation_report(
    record_id: str,
    service: PreparationService = Depends(get_preparation_service),
) -> InstallationRecord:
    try:
        record = service.installation_record(record_id)
    except ValueError:
        record = None
    if record is None:
        raise HTTPException(status_code=404, detail={"code": "INSTALLATION_REPORT_NOT_FOUND", "message": "Installation report was not found."})
    return record


@router.get("/installations/{record_id}/download")
def download_installation_report(
    record_id: str,
    service: PreparationService = Depends(get_preparation_service),
) -> FileResponse:
    try:
        record = service.installation_record(record_id)
    except ValueError:
        record = None
    if record is None:
        raise HTTPException(status_code=404, detail={"code": "INSTALLATION_REPORT_NOT_FOUND", "message": "Installation report was not found."})
    path = service.installation_history.directory / f"{record_id}.json"
    return FileResponse(path, media_type="application/json", filename=f"{record_id}.json")


@router.get("/installations/{record_id}/log")
def download_installation_log(
    record_id: str,
    service: PreparationService = Depends(get_preparation_service),
) -> FileResponse:
    try:
        path = service.installation_log_path(record_id)
    except ValueError:
        path = None
    if path is None:
        raise HTTPException(status_code=404, detail={"code": "INSTALLATION_LOG_NOT_FOUND", "message": "Installation log was not found."})
    return FileResponse(path, media_type="text/plain", filename=path.name)


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
