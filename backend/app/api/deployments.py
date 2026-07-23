from fastapi import APIRouter, Depends, Query

from ..dependencies import get_deployment_service, require_mutations_or_dry_run, settings_dependency
from ..models.deployment import DeploymentActionResponse, DeploymentStatus, DeploymentSummary, LogsResponse, RfStartRequest
from ..models.validation import ValidationReport
from ..services.deployment_service import DeploymentService
from ..security import ensure_mutation_allowed
from ..settings import Settings

router = APIRouter(prefix="/api/deployments", tags=["deployments"])


@router.get("", response_model=list[DeploymentSummary])
def list_deployments(service: DeploymentService = Depends(get_deployment_service)) -> list[DeploymentSummary]:
    return service.list_deployments()


@router.get("/{scenario}", response_model=DeploymentSummary)
def get_deployment(scenario: str, service: DeploymentService = Depends(get_deployment_service)) -> DeploymentSummary:
    return service.get_deployment(scenario)


@router.post("/{scenario}/start", response_model=DeploymentActionResponse, dependencies=[Depends(require_mutations_or_dry_run)])
def start_deployment(scenario: str, service: DeploymentService = Depends(get_deployment_service)) -> DeploymentActionResponse:
    return service.start(scenario)


@router.post("/{scenario}/stop", response_model=DeploymentActionResponse, dependencies=[Depends(require_mutations_or_dry_run)])
def stop_deployment(scenario: str, service: DeploymentService = Depends(get_deployment_service)) -> DeploymentActionResponse:
    return service.stop(scenario)


@router.post("/{scenario}/restart", response_model=DeploymentActionResponse, dependencies=[Depends(require_mutations_or_dry_run)])
def restart_deployment(scenario: str, service: DeploymentService = Depends(get_deployment_service)) -> DeploymentActionResponse:
    return service.restart(scenario)


@router.get("/{scenario}/status", response_model=DeploymentStatus)
def deployment_status(scenario: str, service: DeploymentService = Depends(get_deployment_service)) -> DeploymentStatus:
    return service.get_status(scenario)


@router.get("/{scenario}/logs", response_model=LogsResponse)
def deployment_logs(
    scenario: str,
    container: str | None = Query(default=None),
    tail: int | None = Query(default=None, ge=1, le=5000),
    service: DeploymentService = Depends(get_deployment_service),
) -> LogsResponse:
    return service.logs(scenario, container=container, tail=tail)


@router.post("/{scenario}/validate", response_model=ValidationReport, dependencies=[Depends(require_mutations_or_dry_run)])
def validate_deployment(scenario: str, service: DeploymentService = Depends(get_deployment_service)) -> ValidationReport:
    return service.validate(scenario)


@router.post("/4g-lte-x310/hardware-check", response_model=DeploymentActionResponse, dependencies=[Depends(require_mutations_or_dry_run)])
def x310_hardware_check(service: DeploymentService = Depends(get_deployment_service)) -> DeploymentActionResponse:
    return service.hardware_check("4g-lte-x310")


@router.post("/4g-lte-x310/preflight", response_model=DeploymentActionResponse, dependencies=[Depends(require_mutations_or_dry_run)])
def x310_preflight(service: DeploymentService = Depends(get_deployment_service)) -> DeploymentActionResponse:
    return service.preflight("4g-lte-x310")


@router.post("/4g-lte-x310/start-epc", response_model=DeploymentActionResponse, dependencies=[Depends(require_mutations_or_dry_run)])
def x310_start_epc(service: DeploymentService = Depends(get_deployment_service)) -> DeploymentActionResponse:
    return service.start_epc("4g-lte-x310")


@router.post("/4g-lte-x310/emergency-stop", response_model=DeploymentActionResponse, dependencies=[Depends(require_mutations_or_dry_run)])
def x310_emergency_stop(service: DeploymentService = Depends(get_deployment_service)) -> DeploymentActionResponse:
    return service.emergency_stop("4g-lte-x310")


@router.post("/{scenario}/start-core", response_model=DeploymentActionResponse, dependencies=[Depends(require_mutations_or_dry_run)])
def start_rf_core(scenario: str, service: DeploymentService = Depends(get_deployment_service)) -> DeploymentActionResponse:
    return service.start_core(scenario)


@router.post("/{scenario}/start-rf", response_model=DeploymentActionResponse)
def start_guarded_rf(
    scenario: str,
    payload: RfStartRequest,
    service: DeploymentService = Depends(get_deployment_service),
    settings: Settings = Depends(settings_dependency),
) -> DeploymentActionResponse:
    if payload.execute:
        ensure_mutation_allowed(settings)
    return service.start_rf(scenario, payload)


@router.post("/{scenario}/hardware-check", response_model=DeploymentActionResponse, dependencies=[Depends(require_mutations_or_dry_run)])
def scenario_hardware_check(scenario: str, service: DeploymentService = Depends(get_deployment_service)) -> DeploymentActionResponse:
    return service.hardware_check(scenario)


@router.post("/{scenario}/preflight", response_model=DeploymentActionResponse, dependencies=[Depends(require_mutations_or_dry_run)])
def scenario_preflight(scenario: str, service: DeploymentService = Depends(get_deployment_service)) -> DeploymentActionResponse:
    return service.preflight(scenario)


@router.post("/{scenario}/emergency-stop", response_model=DeploymentActionResponse, dependencies=[Depends(require_mutations_or_dry_run)])
def scenario_emergency_stop(scenario: str, service: DeploymentService = Depends(get_deployment_service)) -> DeploymentActionResponse:
    return service.emergency_stop(scenario)
