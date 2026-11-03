from fastapi import APIRouter, Depends, HTTPException, Query

from ..dependencies import get_validation_service
from ..models.validation import ValidationCheck, ValidationReport
from ..services.deployment_registry import get_deployment_definition
from ..services.validation_service import ValidationService

router = APIRouter(prefix="/api/validation", tags=["validation"])


@router.get("/latest", response_model=ValidationReport)
def latest_validation(
    scenario: str = Query(default="5g-sa"),
    service: ValidationService = Depends(get_validation_service),
) -> ValidationReport:
    definition = get_deployment_definition(scenario)
    if definition is None or not definition.catalog_visible:
        raise HTTPException(status_code=404, detail={"code": "DEPLOYMENT_NOT_FOUND", "message": "The selected profile was not found."})

    report = service.latest_validation(scenario=scenario)
    if report is None:
        checks = [
            ValidationCheck(id=check_id, status="NOT_TESTED", detail="No validation run has been recorded for this profile.")
            for check_id in definition.validation_checks
        ]
        return ValidationReport(
            scenario=scenario,
            status="NOT_TESTED",
            validation={check.id: check.status for check in checks},
            checks=checks,
        )
    return report
