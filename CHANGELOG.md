# Changelog

All notable changes to BlueBubbles are documented in this file. The format is
based on Keep a Changelog, and versions follow Semantic Versioning.

## [Unreleased]

### Added

- Repository-and-tooling foundation for Version 1.0.
- Typed server and desktop-client application factories and entry points.
- Structured JSON logging foundation.
- Automated formatting, linting, type-checking, and test configuration.
- Strict shared API, error, pagination, WebSocket, version-negotiation, and
  encrypted-envelope contracts.
- Deterministic protocol serialisation and public-key fingerprint helpers.
- Separate infrastructure-free Debian server and Windows client domain layers,
  including membership, session, delivery, upload, audit, transfer, and outbox
  state invariants.
- Typed application exception hierarchy, safe REST/WebSocket error envelopes,
  stable error metadata, bounded retries, and dependency circuit breaking.
