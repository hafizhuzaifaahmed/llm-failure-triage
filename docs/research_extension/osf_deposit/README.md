# OSF deposit package (not deposited)

Built by `python scripts/extension/osf_package.py bundle`. Nothing here has been sent anywhere.

- `cfp_confirmation_frozen_bundle.zip`: the registration text, the frozen engine and scripts, the frame, the
  manifests, the planning output and `SHA256SUMS.txt`. Attach it to the OSF registration.
- `SHA256SUMS.txt`: content hash of every file in the bundle (CRLF normalised to LF).

Steps for the authors and the record command are in `../EXECUTION_READINESS.md` section 3.
If the registration text changes before deposit, rebuild the bundle; after deposit it must not change.
