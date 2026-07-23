#!/usr/bin/env python3
from __future__ import annotations

import sys
from types import SimpleNamespace

from _common import ROOT, relative, source_files

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.services.profile_config_service import ProfileConfigService  # noqa: E402


SOFTWARE_PROFILES = {
    "4g-lte-sim",
    "4g-volte-sim",
    "5g-sa",
    "5g-vonr",
}
RF_GUARD_FAILURES = {
    "4g-lte-x310": {
        "RF authorization must be confirmed before apply",
        "safety.operator_note must not be empty",
    },
    "5g-sa-x310": {
        "RF authorization must be confirmed before apply",
        "safety.operator_note must not be empty",
    },
    "5g-nsa-x310": {
        "RF authorization must be confirmed before apply",
        "safety.operator_note must not be empty",
        "5G NSA requires nr_rf_path_connected=true",
        "5G NSA requires authorized_lab_frequencies=true",
    },
}


def main() -> int:
    expected = SOFTWARE_PROFILES | RF_GUARD_FAILURES.keys()
    discovered = {
        path.stem
        for path in source_files()
        if relative(path).startswith("config/profiles/") and path.suffix == ".yaml"
    }
    errors = [f"unclassified profile: {profile}" for profile in sorted(discovered - expected)]
    errors.extend(f"expected profile is missing: {profile}" for profile in sorted(expected - discovered))

    service = ProfileConfigService(SimpleNamespace(project_root=ROOT))
    for profile in sorted(SOFTWARE_PROFILES):
        result = service.validate_profile(profile)
        if not result["valid"]:
            errors.append(f"{profile}: software profile failed validation")

    for profile, required_errors in sorted(RF_GUARD_FAILURES.items()):
        result = service.validate_profile(profile)
        actual_errors = set(result["errors"])
        if result["valid"]:
            errors.append(f"{profile}: RF profile unexpectedly passed its fail-closed guards")
        missing = required_errors - actual_errors
        if missing:
            errors.append(f"{profile}: expected RF guard failures are missing: {sorted(missing)}")

    if errors:
        print(f"profile-check: FAIL ({len(errors)} error(s))", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(
        f"profile-check: OK ({len(SOFTWARE_PROFILES)} software profiles valid; "
        f"{len(RF_GUARD_FAILURES)} RF profiles failed closed as expected)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
