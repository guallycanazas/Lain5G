from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api import deployments, health, preparation, profiles, real_ims, runs, subscribers, validation
from .models.deployment import ErrorDetail, ErrorResponse
from .security import MutationDisabledError
from .services.command_service import CommandSecurityError
from .services.deployment_service import DeploymentCommandError, DeploymentConflictError, DeploymentNotFoundError
from .services.preparation_service import PreparationError
from .services.run_service import RunSecurityError
from .services.real_ims_service import RealIMSError
from .services.subscriber_service import SubscriberServiceError
from .settings import get_settings
from .version import VERSION


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Lain5G-Lab API",
        version=VERSION,
        description="Backend API for operating the validated Lain5G-Lab 5G SA deployment.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(deployments.router)
    app.include_router(runs.router)
    app.include_router(subscribers.router)
    app.include_router(profiles.router)
    app.include_router(validation.router)
    app.include_router(real_ims.router)
    app.include_router(preparation.router)

    register_exception_handlers(app)
    return app


def error_response(status_code: int, code: str, message: str, *, exit_code: int | None = None, stderr: str | None = None, active_scenario: str | None = None) -> JSONResponse:
    body = ErrorResponse(detail=ErrorDetail(code=code, message=message, exit_code=exit_code, stderr=stderr, active_scenario=active_scenario))
    return JSONResponse(status_code=status_code, content=body.model_dump())


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        errors = _redact_validation_errors(jsonable_encoder(exc.errors()))
        return JSONResponse(status_code=422, content={"detail": errors})

    @app.exception_handler(DeploymentNotFoundError)
    async def deployment_not_found_handler(request: Request, exc: DeploymentNotFoundError) -> JSONResponse:
        return error_response(404, "DEPLOYMENT_NOT_FOUND", str(exc))

    @app.exception_handler(DeploymentConflictError)
    async def deployment_conflict_handler(request: Request, exc: DeploymentConflictError) -> JSONResponse:
        return error_response(409, "DEPLOYMENT_CONFLICT", str(exc), active_scenario=getattr(exc, "active_scenario", None))

    @app.exception_handler(DeploymentCommandError)
    async def deployment_command_handler(request: Request, exc: DeploymentCommandError) -> JSONResponse:
        status_code = 504 if exc.result.timed_out else 500
        return error_response(status_code, exc.code, exc.message, exit_code=exc.result.exit_code, stderr=exc.result.stderr)

    async def bad_request_handler(request: Request, exc: Exception) -> JSONResponse:
        return error_response(400, "BAD_REQUEST", str(exc))

    app.add_exception_handler(CommandSecurityError, bad_request_handler)
    app.add_exception_handler(RunSecurityError, bad_request_handler)
    app.add_exception_handler(ValueError, bad_request_handler)

    @app.exception_handler(MutationDisabledError)
    async def mutation_disabled_handler(request: Request, exc: MutationDisabledError) -> JSONResponse:
        return error_response(403, "MUTATING_OPERATIONS_DISABLED", str(exc))

    @app.exception_handler(SubscriberServiceError)
    async def subscriber_error_handler(request: Request, exc: SubscriberServiceError) -> JSONResponse:
        return error_response(exc.status_code, exc.code, exc.message)

    @app.exception_handler(RealIMSError)
    async def real_ims_error_handler(request: Request, exc: RealIMSError) -> JSONResponse:
        return error_response(409, "REAL_IMS_CONFLICT", "The real IMS operation could not be completed.")

    @app.exception_handler(PreparationError)
    async def preparation_error_handler(request: Request, exc: PreparationError) -> JSONResponse:
        return error_response(exc.status_code, exc.code, exc.message)

    from .services.profile_config_service import ProfileConfigError

    @app.exception_handler(ProfileConfigError)
    async def profile_config_error_handler(request: Request, exc: ProfileConfigError) -> JSONResponse:
        return error_response(exc.status_code, exc.code, exc.message)

    @app.exception_handler(Exception)
    async def internal_error_handler(request: Request, exc: Exception) -> JSONResponse:
        return error_response(500, "INTERNAL_ERROR", "An internal backend error occurred.")


app = create_app()


SENSITIVE_API_FIELDS = {
    "authorization",
    "imsi",
    "impi",
    "impu",
    "k",
    "ki",
    "msisdn",
    "op",
    "opc",
    "operator_note",
    "password",
    "provisioning_key",
    "secret",
    "sqn",
    "supi",
    "token",
}


def _redact_secret_values(value):
    if isinstance(value, dict):
        return {
            key: "[REDACTED]" if str(key).lower() in SENSITIVE_API_FIELDS else _redact_secret_values(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact_secret_values(item) for item in value]
    return value


def _redact_validation_errors(errors):
    redacted = _redact_secret_values(errors)
    for error in redacted:
        if any(str(part).lower() in SENSITIVE_API_FIELDS for part in error.get("loc", [])):
            error["input"] = "[REDACTED]"
    return redacted
