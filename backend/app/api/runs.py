from fastapi import APIRouter, Depends, HTTPException, Query

from ..dependencies import get_run_service
from ..models.run import RunDetail, RunSummary
from ..services.run_service import RunSecurityError, RunService

router = APIRouter(prefix="/api/runs", tags=["runs"])


@router.get("", response_model=list[RunSummary])
def list_runs(
    limit: int | None = Query(default=None, ge=1, le=1000),
    scenario: str | None = Query(default=None),
    status: str | None = Query(default=None),
    service: RunService = Depends(get_run_service),
) -> list[RunSummary]:
    return service.list_runs(limit=limit, scenario=scenario, status=status)


@router.get("/latest", response_model=RunDetail)
def latest_run(service: RunService = Depends(get_run_service)) -> RunDetail:
    run = service.latest_run()
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
    return run
