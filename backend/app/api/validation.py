from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import get_validation_service
from ..models.validation import ValidationReport
from ..services.validation_service import ValidationService

router = APIRouter(prefix="/api/validation", tags=["validation"])


@router.get("/latest", response_model=ValidationReport)
def latest_validation(service: ValidationService = Depends(get_validation_service)) -> ValidationReport:
    report = service.latest_validation(scenario="5g-sa")
    if report is None:
        raise HTTPException(status_code=404, detail={"code": "VALIDATION_NOT_FOUND", "message": "No validation result was found."})
    return report
