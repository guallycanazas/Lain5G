# SoftwareX reviewer example: profile reuse

This procedure demonstrates one concrete software extension path in Lain5G: adapt the existing 5G SA software profile to a second lab network by changing its tracking area code (TAC) and data network name (DNN), validate the profile, preview the generated configuration, apply it, and restore the prior runtime files.

The demonstration runs against a temporary copy of the selected profile inputs. It does not edit the checkout's default profile, connect to a radio, start Docker services, or claim UE connectivity. Disposable subscriber credentials are generated only inside the temporary directory and are never printed.

From the repository root, run:

```sh
python3 scripts/revision/demo_profile_reuse.py
```

The JSON report records validation, the files affected by the adaptation, whether the second preview is empty after apply, restoration, and whether the original checkout files retain their SHA-256 hashes. A successful result demonstrates configuration reuse and rollback in software. It does not replace the separate physical RF/UE validation requested by the reviewers.
