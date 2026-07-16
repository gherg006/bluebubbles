# Shared contracts

Task 02 establishes the single set of network contracts imported by both the
BlueBubbles client and server. The package remains independent of FastAPI,
PySide6, databases, deployment configuration, and private-key operations.

## Package boundaries

The authoritative contracts live under `src/bluebubbles/shared`:

- `versioning.py` parses Semantic Versioning values and negotiates positive
  integer protocol generations.
- `validation.py` contains pure structural validation suitable for both peers.
- `errors/` owns the only public `ErrorCode` catalogue, safe error envelopes,
  and stable HTTP/retry metadata.
- `models/` contains strict API-facing Pydantic models. Unknown input fields are
  rejected and credentials use secret-aware values.
- `protocol/` owns WebSocket event identifiers, event-data models, negotiation,
  and deterministic JSON serialization.
- `security/` defines the approved Version 1 algorithm identifiers and encrypted
  envelope structures. It performs no encryption and contains no private keys.

DTOs never reuse persistence models. Request models also never accept an owner
or acting-user identifier where that identity must come from authentication.

## Wire rules

Timestamps used for signing are converted to UTC RFC 3339 with six fractional
digits and a `Z` suffix. UUIDs use lowercase hyphenated text. Canonical JSON is
UTF-8, key-sorted, compact, and rejects non-finite numbers and unsupported
objects. Binary fields are base64 strings only at the protocol boundary.

Pagination defaults to 50 records and is capped at 250. Cursor strings are
opaque to shared code, and a request cannot specify both `before` and `after`.

The Version 1 allowlist identifies AES-256-GCM content encryption,
X25519/HKDF-SHA256/AES-256-GCM recipient key envelopes, Ed25519 signatures, and
SHA-256 hashes. Unknown enum values are rejected by validation.

## Verification

Run the repository quality workflow:

```powershell
python scripts/development/run_quality_checks.py
```

The tests cover version precedence, negotiation, strict DTO input, secret
redaction, public error stability, pagination bounds, canonical serialization,
fingerprints, encrypted-envelope completeness, and client/server import
boundaries.
