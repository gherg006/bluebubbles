# BlueBubbles 0.1.0-rc1 release notes - draft, not issued

This document is prepared for the eventual first candidate. It is not a release
announcement and must remain marked draft until every candidate gate passes.

## Intended scope

BlueBubbles provides a Debian-hosted FastAPI/PostgreSQL/Redis service and a
Windows 11 PySide6 desktop client for encrypted LAN messaging. The intended scope
includes local/LDAP authentication, contacts, direct and group conversations,
client-side encrypted messages and attachments, offline recovery, administration,
audit, monitoring, backup and controlled deployment.

## Security model

Message/file plaintext and private keys remain client-side. The server stores and
routes ciphertext, envelopes and necessary metadata. TLS protects transport;
client-side authenticated encryption protects content. See the security and
cryptography document for trust boundaries and limitations.

## Blocking issues

- `RC-CLIENT-001`: production `UiBackend` composition is absent.
- `RC-INSTALLER-001`: clean-Windows Setup evidence is absent.
- Required live infrastructure and human acceptance rows remain incomplete.

Do not distribute this draft as a candidate.
