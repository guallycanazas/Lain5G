# History Sanitization Options

## Scope

Two Open5GS UDM private-key paths entered reachable Git history. Removing them
from the current tree prevents future builds from copying those repository
files, but it does not remove old blobs from commits, tags, forks, clones,
caches, pull-request refs, or previously published source archives. Both former
keys must be treated as compromised regardless of the history option selected.

No history rewrite has been performed as part of this change.

## Option 1: removal-only

Removal-only records ordinary deletions and preserves every existing commit ID:

```sh
git rm -- \
  images/ims-real-open5gs/roles/udm/curve25519-1.key \
  images/ims-real-open5gs/roles/udm/secp256r1-2.key
git commit -m "Remove tracked UDM private keys"
```

Consequences:

- Existing branches, tags, signatures, and clones remain compatible.
- The private-key blobs remain retrievable from old commits.
- Secret scanners will continue to report reachable history.
- Hosting-provider caches and source archives remain unchanged.
- Rotation and permanent non-reuse are still mandatory.

Choose removal-only only when published-history stability is more important
than removing the blobs and the residual exposure is explicitly accepted and
documented.

## Option 2: `git-filter-repo`

A coordinated rewrite can remove both paths from all rewritten refs. Perform it
from a fresh mirror after freezing pushes and recording protected branches,
tags, release artifacts, and hosting-provider cleanup requirements:

```sh
git clone --mirror https://github.com/guallycanazas/Lain5G-Lab.git repository-sanitized.git
cd repository-sanitized.git
git filter-repo --force --invert-paths \
  --path images/ims-real-open5gs/roles/udm/curve25519-1.key \
  --path images/ims-real-open5gs/roles/udm/secp256r1-2.key
git log --all -- \
  images/ims-real-open5gs/roles/udm/curve25519-1.key \
  images/ims-real-open5gs/roles/udm/secp256r1-2.key
git push --force --mirror https://github.com/guallycanazas/Lain5G-Lab.git
```

Before the force push, run a release-grade secret scanner over all rewritten
refs and verify that the path-scoped log is empty. Keep any mirror backup in
restricted storage with a defined destruction date; it still contains the old
blobs.

Consequences:

- Rewritten commits and tags receive new object IDs.
- Signed commits and tags no longer validate as the original signed objects.
- Open pull requests, branch protections, release links, and CI references may
  need repair.
- Every collaborator must discard or carefully rebase old clones; an ordinary
  pull can reintroduce removed objects.
- Forks, caches, pull-request refs, package registries, and downloaded archives
  require separate owner or hosting-provider action.
- Rotation remains mandatory because rewriting cannot retract material already
  copied by others.

## Recommendation

For a public `v1.0.0` release, use the `git-filter-repo` option before creating
or publishing the final release tag. The findings are valid private keys, the
paths are known, and leaving them in reachable release history creates a
persistent critical scanner finding with no operational benefit. Coordinate a
short push freeze, rewrite all intended public refs, invalidate superseded
release artifacts, ask the hosting provider to purge cached views where
available, and require fresh clones.

If repository owners decline a rewrite because existing public object IDs are
an immutable compatibility boundary, use removal-only, publish the residual
risk decision, and verify that runtime-generated replacements are active. In
either case, never restore the old files, never derive new keys from their
contents, and rotate any UE public-key provisioning that referenced them.
