#!/usr/bin/env bash
set -euo pipefail
export LAIN5G_DRY_RUN=true
"$(dirname "${BASH_SOURCE[0]}")/preflight.sh" || true
"$(dirname "${BASH_SOURCE[0]}")/validate.sh"
