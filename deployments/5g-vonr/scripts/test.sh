#!/usr/bin/env bash
set -euo pipefail
export LAIN5G_DRY_RUN=true
"$(dirname "${BASH_SOURCE[0]}")/start.sh"
"$(dirname "${BASH_SOURCE[0]}")/validate.sh"
"$(dirname "${BASH_SOURCE[0]}")/stop.sh"
