from typing import Any

from fastapi import APIRouter, Body, Depends, Query, status

from ..dependencies import get_subscriber_service, require_mutations_or_dry_run
from ..models.subscriber import Open5GSConnectionStatus, SubscriberListResponse, SubscriberOperationResponse, SubscriberValidationResult
from ..services.subscriber_service import SubscriberService

router = APIRouter(prefix="/api/subscribers", tags=["subscribers"])


@router.get("/connection", response_model=Open5GSConnectionStatus)
def connection(service: SubscriberService = Depends(get_subscriber_service)) -> Open5GSConnectionStatus:
    return service.connection_status()


@router.get("", response_model=SubscriberListResponse)
def list_subscribers(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    search: str | None = Query(default=None, max_length=32),
    service: SubscriberService = Depends(get_subscriber_service),
) -> SubscriberListResponse:
    return service.list_subscribers(limit=limit, offset=offset, search=search)


@router.get("/{imsi}")
def get_subscriber(imsi: str, service: SubscriberService = Depends(get_subscriber_service)):
    return service.get_subscriber(imsi)


@router.post("/validate", response_model=SubscriberValidationResult)
def validate_subscriber(payload: dict[str, Any] = Body(...), service: SubscriberService = Depends(get_subscriber_service)) -> SubscriberValidationResult:
    return service.validate_payload(payload)


@router.post("", response_model=SubscriberOperationResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_mutations_or_dry_run)])
def create_subscriber(payload: dict[str, Any] = Body(...), service: SubscriberService = Depends(get_subscriber_service)) -> SubscriberOperationResponse:
    return service.create_subscriber(payload)


@router.patch("/{imsi}", response_model=SubscriberOperationResponse, dependencies=[Depends(require_mutations_or_dry_run)])
def update_subscriber(imsi: str, payload: dict[str, Any] = Body(...), service: SubscriberService = Depends(get_subscriber_service)) -> SubscriberOperationResponse:
    return service.update_subscriber(imsi, payload)


@router.post("/{imsi}/clone", response_model=SubscriberOperationResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_mutations_or_dry_run)])
def clone_subscriber(imsi: str, payload: dict[str, Any] = Body(...), service: SubscriberService = Depends(get_subscriber_service)) -> SubscriberOperationResponse:
    return service.clone_subscriber(imsi, payload)


@router.delete("/{imsi}", response_model=SubscriberOperationResponse, dependencies=[Depends(require_mutations_or_dry_run)])
def delete_subscriber(imsi: str, payload: dict[str, Any] = Body(...), service: SubscriberService = Depends(get_subscriber_service)) -> SubscriberOperationResponse:
    return service.delete_subscriber(imsi, confirm=bool(payload.get("confirm")))
