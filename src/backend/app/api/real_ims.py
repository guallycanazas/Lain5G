from typing import Any

from fastapi import APIRouter, Body, Depends, Query

from ..dependencies import get_real_ims_service, settings_dependency
from ..models.real_ims import (
    Mode,
    RealIMSImagesRequest,
    RealIMSProvisionRequest,
    RealIMSStartRequest,
    RealIMSStatusReport,
    RealIMSStopRequest,
    RealIMSSubscriberList,
)
from ..services.real_ims_service import RealIMSService
from ..security import ensure_mutation_allowed
from ..settings import Settings


router = APIRouter(prefix="/api/ims-real", tags=["real-ims"])


@router.get("/preflight", response_model=RealIMSStatusReport)
def preflight(
    mode: Mode = Query(...),
    service: RealIMSService = Depends(get_real_ims_service),
) -> RealIMSStatusReport:
    return service.preflight(mode)


@router.get("/status", response_model=RealIMSStatusReport)
def status(
    mode: Mode = Query(...),
    imsi: str | None = Query(default=None),
    service: RealIMSService = Depends(get_real_ims_service),
) -> RealIMSStatusReport:
    return service.status(mode, imsi=imsi)


@router.get("/subscribers", response_model=RealIMSSubscriberList)
def subscribers(
    mode: Mode = Query(...),
    service: RealIMSService = Depends(get_real_ims_service),
) -> RealIMSSubscriberList:
    return service.subscribers(mode)


@router.post("/images")
def images(
    payload: RealIMSImagesRequest = Body(default=RealIMSImagesRequest()),
    service: RealIMSService = Depends(get_real_ims_service),
    settings: Settings = Depends(settings_dependency),
) -> dict[str, Any]:
    if payload.execute:
        ensure_mutation_allowed(settings)
    return service.build_images(execute=payload.execute, force=payload.force)


@router.post("/start")
def start(
    payload: RealIMSStartRequest,
    service: RealIMSService = Depends(get_real_ims_service),
    settings: Settings = Depends(settings_dependency),
) -> dict[str, Any]:
    if payload.execute:
        ensure_mutation_allowed(settings)
    return service.start(payload.mode, payload.mcc, payload.mnc, execute=payload.execute)


@router.post("/stop")
def stop(
    payload: RealIMSStopRequest,
    service: RealIMSService = Depends(get_real_ims_service),
    settings: Settings = Depends(settings_dependency),
) -> dict[str, Any]:
    if payload.execute:
        ensure_mutation_allowed(settings)
    return service.stop(payload.mode, execute=payload.execute)


@router.post("/provision")
def provision(
    payload: RealIMSProvisionRequest,
    service: RealIMSService = Depends(get_real_ims_service),
    settings: Settings = Depends(settings_dependency),
) -> dict[str, Any]:
    if payload.execute:
        ensure_mutation_allowed(settings)
    return service.provision(
        payload.mode,
        payload.subscriber,
        payload.mcc,
        payload.mnc,
        execute=payload.execute,
    )
