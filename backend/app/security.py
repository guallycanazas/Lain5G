from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .settings import Settings


class MutationDisabledError(PermissionError):
    pass


def ensure_mutation_allowed(settings: Settings, *, allow_dry_run: bool = False) -> None:
    if settings.mutating_operations_enabled:
        return
    if allow_dry_run and settings.dry_run:
        return
    raise MutationDisabledError("Mutating operations are disabled by the local operator configuration.")
