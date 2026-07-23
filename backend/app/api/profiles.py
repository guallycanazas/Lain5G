from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Depends

from ..dependencies import get_profile_config_service, require_mutations_enabled
from ..services.profile_config_service import ProfileConfigService

router = APIRouter(prefix="/api/profiles", tags=["profiles"])


@router.get("")
def list_profiles(service: ProfileConfigService = Depends(get_profile_config_service)) -> list[dict[str, Any]]:
    return service.list_profiles()


@router.get("/{profile_id}")
def get_profile(profile_id: str, service: ProfileConfigService = Depends(get_profile_config_service)) -> dict[str, Any]:
    return service.get_profile(profile_id)


@router.post("/{profile_id}/validate")
def validate_profile(profile_id: str, service: ProfileConfigService = Depends(get_profile_config_service)) -> dict[str, Any]:
    return service.validate_profile(profile_id)


@router.get("/{profile_id}/diff")
def diff_profile(profile_id: str, service: ProfileConfigService = Depends(get_profile_config_service)) -> dict[str, Any]:
    return service.diff_profile(profile_id)


@router.put("/{profile_id}", dependencies=[Depends(require_mutations_enabled)])
def update_profile(profile_id: str, payload: dict[str, Any] = Body(...), service: ProfileConfigService = Depends(get_profile_config_service)) -> dict[str, Any]:
    return service.update_profile(profile_id, payload)


@router.post("/{profile_id}/apply", dependencies=[Depends(require_mutations_enabled)])
def apply_profile(profile_id: str, service: ProfileConfigService = Depends(get_profile_config_service)) -> dict[str, Any]:
    return service.apply_profile(profile_id)


@router.post("/{profile_id}/restore", dependencies=[Depends(require_mutations_enabled)])
def restore_profile(profile_id: str, service: ProfileConfigService = Depends(get_profile_config_service)) -> dict[str, Any]:
    return service.restore_profile(profile_id)
