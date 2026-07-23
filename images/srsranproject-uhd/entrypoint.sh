#!/usr/bin/env bash
set -euo pipefail

# Never download images or touch FPGA/FW automatically from this container.
exec "$@"
