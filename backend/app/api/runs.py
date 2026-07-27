from fastapi import APIRouter, Depends, HTTPException, Query

from ..dependencies import get_run_service
from ..models.run import RunDetail, RunSummary
from ..services.image_catalog import PUBLIC_PROFILE_IDS
from ..services.run_service import RunSecurityError, RunService

router = APIRouter(prefix="/api/runs", tags=["runs"])
PUBLIC_SCENARIOS = frozenset(PUBLIC_PROFILE_IDS)


@router.get("", response_model=list[RunSummary])
def list_runs(
    limit: int | None = Query(default=None, ge=1, le=1000),
    scenario: str | None = Query(default=None),
    status: str | None = Query(default=None),
    service: RunService = Depends(get_run_service),
) -> list[RunSummary]:
    if scenario and scenario not in PUBLIC_SCENARIOS:
        return []
    runs = [run for run in service.list_runs(scenario=scenario, status=status) if run.scenario in PUBLIC_SCENARIOS]
    return runs[:limit] if limit is not None else runs


@router.get("/latest", response_model=RunDetail)
def latest_run(service: RunService = Depends(get_run_service)) -> RunDetail:
    summary = next((run for run in service.list_runs() if run.scenario in PUBLIC_SCENARIOS), None)
    run = service.get_run(summary.run_id) if summary else None
    if run is None:
        raise HTTPException(status_code=404, detail={"code": "RUN_NOT_FOUND", "message": "No valid runs were found."})
    return run


@router.get("/{run_id}", response_model=RunDetail)
def get_run(run_id: str, service: RunService = Depends(get_run_service)) -> RunDetail:
    try:
        run = service.get_run(run_id)
    except RunSecurityError:
        raise HTTPException(status_code=400, detail={"code": "INVALID_RUN_ID", "message": "Invalid run id."}) from None
    if run is None:
        raise HTTPException(status_code=404, detail={"code": "RUN_NOT_FOUND", "message": "Run was not found."})
    if run.metadata.get("scenario") not in PUBLIC_SCENARIOS:
        raise HTTPException(status_code=404, detail={"code": "RUN_NOT_FOUND", "message": "Run was not found."})
    return run
