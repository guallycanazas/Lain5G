# Key Management

## UDM home-network keys

Open5GS UDM uses two home-network private keys to decrypt SUCI values:

- Key identifier 1 uses ECIES profile A with X25519.
- Key identifier 2 uses ECIES profile B with compressed prime256v1.

The repository contains only the UDM configuration paths and generation code.
It does not contain private keys. The Open5GS image context also rejects common
private-key file types through `.dockerignore`.

## Runtime generation

`images/ims-real-open5gs/roles/udm/generate_hnet_keys.sh` implements the key
formats documented by the pinned Open5GS source:

```sh
openssl genpkey -algorithm X25519 -out curve25519-1.key
openssl ecparam -name prime256v1 -genkey -conv_form compressed -out secp256r1-2.key
```

The UDM entrypoint invokes the generator before starting `open5gs-udmd`. It:

- creates the key directory with mode `0700`;
- uses `umask 077` and enforces mode `0600` on both files;
- generates temporary files and atomically replaces the configured paths;
- validates each private key without displaying it; and
- generates a new pair on every UDM process start.

The 5G Compose service mounts `/open5gs/install/etc/open5gs/hnet` as a `0700`
tmpfs. Keys therefore remain in memory for the container runtime and are not
stored in a named volume. The image build removes the upstream demo keys from
the final filesystem view before role files are copied. Because the pinned base
image may still contain those demo files in an inherited lower layer, it must
not be treated as a source of operational keys; runtime generation always
replaces the configured paths.

A clean checkout needs no key bootstrap step. Building the image and starting
the 5G stack creates a fresh pair automatically. For an isolated format and
permission check, generate into a new directory outside the repository:

```sh
umask 077
runtime_dir="$(mktemp -d)"
images/ims-real-open5gs/roles/udm/generate_hnet_keys.sh "$runtime_dir"
stat -c '%a %n' "$runtime_dir" "$runtime_dir"/*.key
```

Do not run OpenSSL private-key text or modulus display commands in terminals,
CI logs, issue reports, or release evidence.

## Public-key provisioning

SUCI-capable UEs must hold the public key corresponding to the UDM private key,
the matching key identifier, and the matching protection scheme. Fresh runtime
keys deliberately invalidate previously provisioned public keys. Before using
profile A or B, export only the public component to a protected provisioning
workflow and update the UE or USIM for that runtime. A UE that cannot be
reprovisioned on each runtime must use a separately approved persistent key
service; do not change the generator to read a repository file.

Public components may be written to files without printing them:

```sh
openssl pkey -in curve25519-1.key -pubout -out curve25519-1.public.pem
openssl ec -in secp256r1-2.key -pubout -conv_form compressed -out secp256r1-2.public.pem
```

Public-key files are not secrets, but they are configuration artifacts and must
be reviewed before publication. Never copy the corresponding private files out
of the UDM runtime.

## Rotation and response

The private keys formerly tracked by Git must be considered compromised and
must never be reused. Runtime generation is their replacement, not a way to
make the historic values safe.

To rotate the active pair, restart or recreate the UDM service, then provision
the newly derived public components before allowing SUCI profile A or B traffic.
Record the rotation time and key identifiers, but never private values or
private-key fingerprints in normal logs. If a runtime key may have escaped,
stop the affected UDM runtime, create a new runtime, reprovision public keys,
and review logs and artifacts for disclosure.

Run `scripts/security/check-sensitive-files.sh` in CI. It scans only tracked
worktree files and emits JSON lines containing exactly category, path,
approximate line, severity, and result. It never emits matched values and does
not traverse ignored operational data. This focused worktree check is not a
substitute for a release-grade scanner over all Git refs and image layers.
