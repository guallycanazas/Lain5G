#!/bin/bash

set -euo pipefail

if [[ $# -ne 1 || -z $1 ]]; then
    exit 2
fi

hnet_dir=$1
curve_tmp=
secp_tmp=

cleanup() {
    [[ -z $curve_tmp ]] || rm -f -- "$curve_tmp"
    [[ -z $secp_tmp ]] || rm -f -- "$secp_tmp"
}
trap cleanup EXIT HUP INT TERM

if [[ -L $hnet_dir ]]; then
    exit 1
fi

umask 077
install -d -m 0700 -- "$hnet_dir"
chmod 0700 -- "$hnet_dir"

curve_tmp=$(mktemp "$hnet_dir/.curve25519-1.key.XXXXXX")
secp_tmp=$(mktemp "$hnet_dir/.secp256r1-2.key.XXXXXX")

openssl genpkey -algorithm X25519 -out "$curve_tmp"
openssl ecparam -name prime256v1 -genkey -conv_form compressed -out "$secp_tmp"
openssl pkey -in "$curve_tmp" -check -noout >/dev/null 2>&1
openssl ec -in "$secp_tmp" -check -noout >/dev/null 2>&1

chmod 0600 -- "$curve_tmp" "$secp_tmp"
mv -f -- "$curve_tmp" "$hnet_dir/curve25519-1.key"
curve_tmp=
mv -f -- "$secp_tmp" "$hnet_dir/secp256r1-2.key"
secp_tmp=

trap - EXIT HUP INT TERM
