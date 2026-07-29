#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
dry_run=false
for argument in "$@"; do
  [ "$argument" = "--dry-run" ] && dry_run=true
done

if command -v python3 >/dev/null 2>&1 && python3 -c 'import sys; raise SystemExit(sys.version_info < (3, 10))'; then
  exec python3 "$root/lain5g" bootstrap "$@"
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
exec python3 "$root/lain5g" bootstrap "$@"
