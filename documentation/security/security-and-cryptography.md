# Security and cryptography guide

## Trust and threat model

BlueBubbles protects message and attachment content from the server, database
administrator, Redis, backup media, and unauthorised conversation members. It does
not conceal routing metadata needed to operate the service: user IDs, conversation
membership, timestamps, ciphertext sizes, delivery state, IP/session metadata, and
attachment sizes remain visible. A compromised authorised endpoint can read content
available to that endpoint. This is end-to-end content encryption, not anonymity.

The public network boundary is Nginx TLS 1.2/1.3. FastAPI, PostgreSQL, and Redis
remain loopback-only. Authentication, authorisation, cryptographic verification,
path containment, audit integrity, and backup restore are independent controls; TLS
does not replace any of them.

## Identity keys and local protection

Each user has one primary cryptographic device in Version 1.0. The Windows client
generates Ed25519 signing and X25519 envelope keys locally. Private identity keys
never enter REST/WebSocket DTOs, PostgreSQL, Redis, server logs, diagnostics,
exports, or backups. The client encrypts private material at rest with a local key
protected by Windows credential facilities. Local encrypted storage is isolated by
profile UUID.

Public keys are versioned, fingerprinted, time-bounded, and revocable. Historical
private-key versions must remain locally available to decrypt authorised history;
revoked versions are not used for new envelopes. Fingerprint changes require a
clear user-visible trust decision.

There is no automatic private-key recovery. If the client profile and protected
key material are lost, administrators cannot decrypt or restore message content.
Back up Windows profiles only under an explicitly approved endpoint-recovery policy.

## Message protection

The sender creates a fresh AES-256-GCM content key and nonce, canonicalises the
message metadata/ciphertext envelope, seals the content key independently to each
active recipient's current X25519 public key, and signs the canonical envelope with
Ed25519. Recipients verify the sender key/version and signature before opening their
recipient envelope, then require a valid GCM authentication tag before accepting
plaintext. Unknown algorithms, missing envelopes, duplicate recipient IDs, changed
metadata, invalid signatures, tags, or lengths fail closed.

The server validates structure, membership, versions, idempotency, sizes, and
recipient sets, but cannot decrypt. Stored and outbox representations contain
ciphertext/envelopes only.

## Attachment protection

The client hashes plaintext, encrypts bounded chunks with unique nonces and
authenticated context, and uploads ciphertext. Resume requests operate on verified
missing indexes, never on guessed completion. Downloads recheck authorisation,
verify every chunk tag, stream through a temporary file, verify final plaintext
SHA-256, and rename atomically. The server filename is a safe identifier, not an
untrusted client path.

## Authentication and sessions

LDAP/Active Directory uses TLS with certificate validation and a least-privilege
bind identity. Local passwords use Argon2id. Access tokens are short-lived signed
tokens bound to a server-side session; refresh tokens are opaque, hashed at rest,
rotated once, and reuse-detected. Logout, administrative revocation, user disable,
and refresh reuse invalidate the authoritative session. WebSocket authentication
uses the same session authority.

Permissions are evaluated in services against the current role/capability set.
Client-side visibility is usability only and never authorisation. Group membership
is rechecked at send, receive publication, and attachment access boundaries.

## Audit and operational security

Administrative/security events append canonical metadata to a SHA-256 hash chain.
The runtime database role must not update or delete audit rows. Recent and full
verification failures create critical alerts. Audit metadata never contains
passwords, tokens, private keys, or message/attachment plaintext.

Secrets reside in protected files owned by `root:bluebubbles` mode `0640`, allowing
the non-interactive service identity to read but not modify them. TLS private keys
remain root/Nginx-only mode `0600`. Diagnostics and release evidence are scanned for
private-key headers, token-like values, non-example connection secrets, and known
plaintext markers.

## Security limitations

- No full forward secrecy: compromise of retained endpoint private keys may expose
  history encrypted to those key versions.
- Offline revocation takes effect when the device reconnects; already decrypted
  local content cannot be remotely erased.
- One primary cryptographic device per user; no multi-device key sharing.
- The server observes operational metadata and traffic patterns.
- Administrators cannot recover lost end-to-end encryption keys.
- Certificate/signing infrastructure is installation-owned; the current NEA client
  artifact and manifest are unsigned.
- The current packaged client backend is unbound, so end-to-end security acceptance
  cannot run and release remains blocked.

## Review checklist

Before every candidate: audit dependencies; scan source/artifacts; confirm algorithm
allowlists and canonicalisation unchanged; inspect nonce generation; verify negative
signature/tag tests; inspect server DTO/storage/logs for plaintext/private-key
fields; test TLS hostname/CA failures; test session rotation/reuse/revocation;
tamper audit history; inspect database privileges; restore a backup; and run the
two-client plaintext-marker smoke test.
