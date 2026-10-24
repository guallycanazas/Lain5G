from functools import lru_cache
from typing import Literal

from fastapi import Depends, Query

from .security import ensure_mutation_allowed
from .services.command_service import CommandService
from .services.deployment_service import DeploymentService
from .services.open5gs_connection_service import Open5GSConnectionService
from .services.profile_config_service import ProfileConfigService
from .services.preparation_service import PreparationService
from .services.real_ims_service import RealIMSService
from .services.run_service import RunService
from .services.subscriber_service import SubscriberService
from .services.validation_service import ValidationService
from .settings import Settings, get_settings


@lru_cache
def get_command_service() -> CommandService:
    settings = get_settings()
    return CommandService(settings)


@lru_cache
def get_run_service() -> RunService:
    settings = get_settings()
    return RunService(settings)


@lru_cache
def get_validation_service() -> ValidationService:
    return ValidationService(get_run_service())


@lru_cache
def get_deployment_service() -> DeploymentService:
    return DeploymentService(get_settings(), get_command_service(), get_run_service(), get_validation_service(), get_preparation_service())


@lru_cache
def get_open5gs_connection_service() -> Open5GSConnectionService:
    return Open5GSConnectionService(get_settings())


SubscriberProfile = Literal["4g-lte-x310", "5g-sa-x310", "5g-nsa-x310"]


def get_subscriber_service(
    profile: SubscriberProfile = Query(default="4g-lte-x310"),
) -> SubscriberService:
    settings = get_settings()
    profile_connection = {
        "4g-lte-x310": {
            "open5gs_mongo_uri": "mongodb://lain5g-lab-4g-lte-x310-mongo:27017/open5gs",
            "open5gs_docker_network": "lain5g-lab-4g-lte-x310-core",
            "open5gs_docker_ip": "10.42.0.250",
        },
        "5g-sa-x310": {
            "open5gs_mongo_uri": "mongodb://lain5g-lab-5g-sa-x310-mongo:27017/open5gs",
            "open5gs_docker_network": "lain5g-lab-5g-sa-x310-core",
            "open5gs_docker_ip": "10.20.0.250",
        },
        # NSA uses the LTE EPC and its subscriber database.
        "5g-nsa-x310": {
            "open5gs_mongo_uri": "mongodb://lain5g-lab-4g-lte-x310-mongo:27017/open5gs",
            "open5gs_docker_network": "lain5g-lab-4g-lte-x310-core",
            "open5gs_docker_ip": "10.42.0.250",
        },
    }[profile]
    scoped_settings = settings.model_copy(update=profile_connection)
    connection = Open5GSConnectionService(scoped_settings)
    return SubscriberService(scoped_settings, connection)


@lru_cache
def get_profile_config_service() -> ProfileConfigService:
    return ProfileConfigService(get_settings())


@lru_cache
def get_preparation_service() -> PreparationService:
    return PreparationService(get_settings(), get_command_service())


@lru_cache
def get_real_ims_service() -> RealIMSService:
    return RealIMSService(get_settings())


def settings_dependency() -> Settings:
    return get_settings()


def require_mutations_enabled(settings: Settings = Depends(settings_dependency)) -> None:
    ensure_mutation_allowed(settings)


def require_mutations_or_dry_run(settings: Settings = Depends(settings_dependency)) -> None:
    ensure_mutation_allowed(settings, allow_dry_run=True)
