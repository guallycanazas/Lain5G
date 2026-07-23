#!/usr/bin/env bash
set -euo pipefail
"$(dirname "${BASH_SOURCE[0]}")/stop.sh"
"$(dirname "${BASH_SOURCE[0]}")/start.sh"
