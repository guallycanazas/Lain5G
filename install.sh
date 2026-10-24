#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
dry_run=false
install_started_at="$(date +%s)"
install_log="${LAIN5G_INSTALL_LOG:-}"
if [ -z "$install_log" ]; then
  state_root="${XDG_STATE_HOME:-${HOME:-/tmp}/.local/state}"
  log_dir="$state_root/lain5g"
  if mkdir -p "$log_dir" 2>/dev/null; then
    install_log="$log_dir/install-$(date -u +%Y%m%dT%H%M%SZ).log"
  fi
fi
if [ -n "$install_log" ]; then
  if touch "$install_log" 2>/dev/null; then
    chmod 600 "$install_log" 2>/dev/null || true
    exec > >(tee -a "$install_log") 2>&1
    echo "Install log: $install_log"
    export LAIN5G_INSTALL_LOG="$install_log"
  else
    install_log=""
  fi
fi
export LAIN5G_INSTALL_STARTED_AT="$install_started_at"

finish_install() {
  status=$?
  trap - EXIT
  elapsed=$(( $(date +%s) - install_started_at ))
  if [ "$status" -eq 0 ]; then
    echo "RESULTADO DE INSTALACION: CORRECTO (codigo 0; ${elapsed} s)"
  else
    echo "RESULTADO DE INSTALACION: ERROR (codigo $status; ${elapsed} s)" >&2
  fi
  if [ -n "$install_log" ]; then
    echo "Registro completo de instalacion: $install_log"
  else
    echo "Registro persistente no disponible: no se pudo escribir en el directorio de estado del usuario."
  fi
  exit "$status"
}
trap finish_install EXIT

for argument in "$@"; do
  [ "$argument" = "--dry-run" ] && dry_run=true
done

if command -v python3 >/dev/null 2>&1 && python3 -c 'import sys; raise SystemExit(sys.version_info < (3, 10))'; then
  python3 "$root/lain5g" bootstrap "$@"
  exit $?
fi

privileged=()
if [ "${EUID:-$(id -u)}" -ne 0 ]; then
  command -v sudo >/dev/null 2>&1 || { echo "ERROR: Python 3 no esta instalado y sudo no esta disponible." >&2; exit 2; }
  privileged=(sudo)
fi

if command -v apt-get >/dev/null 2>&1; then
  commands=("${privileged[*]} apt-get update" "${privileged[*]} apt-get install -y python3")
elif command -v dnf >/dev/null 2>&1; then
  commands=("${privileged[*]} dnf install -y python3")
elif command -v pacman >/dev/null 2>&1; then
  commands=("${privileged[*]} pacman -Sy --needed --noconfirm python")
elif command -v zypper >/dev/null 2>&1; then
  commands=("${privileged[*]} zypper --non-interactive install python3")
else
  echo "ERROR: instala Python 3.10+; no se encontro apt-get, dnf, pacman ni zypper." >&2
  exit 2
fi

for command in "${commands[@]}"; do
  echo "$ $command"
  [ "$dry_run" = true ] || bash -lc "$command"
done

[ "$dry_run" = true ] && { echo '$ python3 ./lain5g bootstrap --dry-run'; exit 0; }
python3 -c 'import sys; raise SystemExit(sys.version_info < (3, 10))' || {
  echo "ERROR: el gestor no proporciono Python 3.10 o posterior." >&2
  exit 2
}
export LAIN5G_BOOTSTRAP_PYTHON_INSTALLED=true
python3 "$root/lain5g" bootstrap "$@"
