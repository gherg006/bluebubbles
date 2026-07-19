# Known limitations and Version 1.0 evaluation

Status meanings: **Met** has executable evidence; **Partially met** has component
evidence but lacks required live/human evidence; **Not met** fails a mandatory
workflow. The detailed requirement IDs are in the Task 22 acceptance matrix.

## Mandatory evaluation

| Criterion | Status | Evidence and limitation | Required improvement |
|---|---|---|---|
| Server contracts, services and adapters | Partially met | Automated service/route/crypto/storage tests pass; three real PostgreSQL cases skip locally | Run migrated PostgreSQL/Redis/LDAP clean deployment suite |
| Windows user messaging workflow | Not met | UI/ViewModel and client services pass separately; packaged app constructs unavailable backend | Implement production backend composition and pass two-client smoke |
| End-to-end encryption/private-key boundary | Partially met | Crypto, DTO, architecture and secret/plaintext scans pass | Perform deployed plaintext/key inspection after smoke |
| Groups and membership | Partially met | Service invariants and recipient filtering pass | Run live owner/member/removal journey |
| Attachments and resume | Partially met | Bounded crypto/storage/resume components pass | Run large live upload/download/tamper/network interruption |
| Offline replay and synchronisation | Partially met | Queue/idempotency/conflict tests pass | Run real client disconnect/restart/reconnect journey |
| Administration and audit | Partially met | Permission/audit/alert tests pass | Run live admin UI, DB privilege and tamper alert inspection |
| Debian Trixie deployment | Partially met | Templates/scripts/manifests/static tests and reproducible archive pass | Clean Debian/systemd/Nginx/TLS/firewall installation |
| Windows installation | Not met | PyInstaller bundle launches; no Inno Setup compiler/signing certificate | Build/install/uninstall on clean Windows 11 |
| Backup/restore/upgrade/rollback | Not met | Guarded implementations and runbooks exist | Restore into clean host and run full smoke; rehearse two releases |
| Accessibility/usability | Partially met | Widget names, themes, scale logic and keyboard-oriented controls tested | Human keyboard, screen-reader, 150% layout and user observation |
| Performance | Partially met | Local component baselines pass | Measure full LAN/database/WebSocket/GUI datasets |
| Dependency/security quality | Met (point-in-time) | Both 2026-07-18 audits report no known vulnerabilities; final suite reached 90.18% branch-aware coverage | Re-audit immediately before candidate; the 2026-07-19 network refresh was privacy-blocked |

## Published product limitations

- LAN-only; no public federation or cloud dependency.
- Windows desktop client focus; Debian Trixie server.
- One primary cryptographic device per user and no multi-device key sharing.
- No automatic private-key recovery; administrators cannot recover lost encrypted
  content keys.
- No full forward secrecy.
- No voice/video calls, reactions, stickers, bots, public registration, browser
  administration, automatic zero-downtime upgrade, or plaintext moderation.
- Server observes routing metadata, membership, timestamps, ciphertext/attachment
  sizes, delivery state, and connection/session metadata.
- Offline revocation is delayed until reconnection. Already decrypted content
  cannot be remotely erased.
- Local search covers only cached authorised messages and can be incomplete.
- Local cache/device compromise can expose content available to that endpoint.
- The current NEA artifacts are unsigned.
- Current blocker: the shipped desktop UI backend is not connected to real client
  services, so Version 1.0 is not a release candidate.

## Realistic future improvements

First close production client composition with real HTTP/WebSocket adapters and
end-to-end tests. Then automate Debian and clean Windows test machines, add signed
installer builds, hashed/offline Debian wheelhouse publication, repeatable TLS/LAN
impairment and restore labs, screen-reader/user studies, and performance datasets.
Only after those gates pass should forward secrecy or multi-device key recovery be
researched as new security designs rather than incremental toggles.
