# Changelog

## Task 07 - Unit of Work

- Added fresh async session construction, a complete immutable repository bundle,
  SQLAlchemy repository composition, and explicit Unit of Work transaction control.
- Added rollback-on-error and rollback-on-uncommitted-exit cleanup, safe closure,
  guarded completion states, and redacted commit error translation.
- Aligned message and attachment adapters with their `Sequence`-based repository
  protocols and added focused plus opt-in PostgreSQL transaction tests.
- Added an AI-focused root guide, canonical repository index, transaction guide,
  and complete Task 07 verification report.

## Task 06 - Repository infrastructure

- Added infrastructure-neutral repository protocols for all Version 1.0 server
  persistence areas and async SQLAlchemy 2.x adapters using caller-owned sessions.
- Added pure ORM/domain mappers, deterministic cursor query models, optimistic
  concurrency, soft-delete visibility, recipient-key scoping, bounded cleanup,
  audit-chain locking, and skip-locked transactional outbox claiming.
- Added redacted persistence error translation and explicit encrypted attachment
  chunk/key metadata requirements; repositories never invent cryptographic values.
- Added comprehensive unit evidence and an opt-in real PostgreSQL workflow covering
  user uniqueness and outbox claiming.

All notable changes to BlueBubbles are documented in this file. The format is
based on Keep a Changelog, and versions follow Semantic Versioning.

## [Unreleased]

### Added

- Complete PostgreSQL Version 1.0 ORM schema, deterministic naming and constraints,
  initial Alembic migration, append-only audit trigger, fixed role and permission
  seeding, schema revision verification, and database contract tests.
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
