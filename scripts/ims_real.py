#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ValidationError

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.models.real_ims import RealIMSSubscriber  # noqa: E402
from backend.app.services.pyhss_service import PyHSSError  # noqa: E402
from backend.app.services.real_ims_service import RealIMSError, RealIMSService  # noqa: E402
from backend.app.settings import get_settings  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Operate the Lain5G-Lab real IMS package")
    commands = parser.add_subparsers(dest="command", required=True)

    images = commands.add_parser("images", help="plan or build the pinned IMS images")
    images.add_argument("--force", action="store_true", help="rebuild images that already exist")
    _execution_flag(images)

    preflight = commands.add_parser("preflight", help="check package and host prerequisites")
    _mode(preflight)

    start = commands.add_parser("start", help="plan or start the core and IMS services")
    _mode(start)
    _plmn(start)
    _execution_flag(start)

    provision = commands.add_parser("provision", help="plan or reconcile a subscriber from JSON")
    _mode(provision)
    _plmn(provision)
    provision.add_argument("--subscriber-file", type=Path, required=True)
    _execution_flag(provision)

    status = commands.add_parser("status", help="inspect core, IMS, and registration readiness")
    _mode(status)
    status.add_argument("--imsi", help="check one provisioned IMSI")

    wait_register = commands.add_parser("wait-register", help="wait for authenticated IMS registration evidence")
    _mode(wait_register)
    wait_register.add_argument("--timeout", type=float, default=300.0)
    wait_register.add_argument("--interval", type=float, default=2.0)

    stop = commands.add_parser("stop", help="plan or stop services without deleting volumes")
    _mode(stop)
    _execution_flag(stop)
    return parser


def _mode(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--mode", choices=("4g", "5g"), required=True)


def _plmn(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--mcc", default="001")
    parser.add_argument("--mnc", default="01")


def _execution_flag(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--execute", action="store_true", help="perform the mutation instead of returning a dry-run plan")


def _subscriber(path: Path) -> RealIMSSubscriber:
    payload = json.loads(path.expanduser().read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("subscriber JSON must contain one object")
    return RealIMSSubscriber.model_validate(payload)


def _wait_for_registration(service: RealIMSService, mode: str, timeout: float, interval: float) -> tuple[BaseModel, int]:
    if timeout <= 0 or interval <= 0:
        raise ValueError("timeout and interval must be positive")
    deadline = time.monotonic() + timeout
    report = service.status(mode)  # type: ignore[arg-type]
    while time.monotonic() < deadline:
        registration = next((check for check in report.checks if check.id == "authenticated_registration"), None)
        if registration is not None and registration.status == "PASS":
            return report, 0
        time.sleep(min(interval, max(0.0, deadline - time.monotonic())))
        report = service.status(mode)  # type: ignore[arg-type]
    return report, 1


def _validation_error(exc: ValidationError) -> str:
    return "; ".join(
        f"{'.'.join(str(item) for item in error['loc'])}: {error['msg']}"
        for error in exc.errors(include_input=False)
    )


def _json_value(value: Any) -> Any:
    return value.model_dump(mode="json") if isinstance(value, BaseModel) else value


def main() -> int:
    args = build_parser().parse_args()
    service = RealIMSService(get_settings())
    try:
        if args.command == "images":
            result, exit_code = service.build_images(execute=args.execute, force=args.force), 0
        elif args.command == "preflight":
            result, exit_code = service.preflight(args.mode), 0
        elif args.command == "start":
            result, exit_code = service.start(args.mode, args.mcc, args.mnc, execute=args.execute), 0
        elif args.command == "provision":
            result = service.provision(
                args.mode,
                _subscriber(args.subscriber_file),
                args.mcc,
                args.mnc,
                execute=args.execute,
            )
            exit_code = 0
        elif args.command == "status":
            result, exit_code = service.status(args.mode, imsi=args.imsi), 0
        elif args.command == "wait-register":
            result, exit_code = _wait_for_registration(service, args.mode, args.timeout, args.interval)
        else:
            result, exit_code = service.stop(args.mode, execute=args.execute), 0
    except ValidationError as exc:
        print(json.dumps({"status": "FAIL", "error": _validation_error(exc)}, indent=2), file=sys.stderr)
        return 1
    except (RealIMSError, PyHSSError, json.JSONDecodeError, OSError, ValueError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, indent=2), file=sys.stderr)
        return 1
    print(json.dumps(_json_value(result), indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
