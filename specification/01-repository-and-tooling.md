# Task 01 — Repository and tooling

> This is a self-contained implementation task split from the complete BlueBubbles Version 1.0 specification. Source requirements below are reproduced verbatim, not summarised. Where a repeated project-wide rule conflicts with a task-local choice, the project-wide rule wins.

## Required predecessors

None.

## Completion boundary

Implement the whole task, all integrations named in this file, its tests, documentation, migration or configuration effects, and its stage exit checks. Do not implement later tasks merely because their contracts are visible for integration.

---

## Project-wide contract — verbatim source

# BlueBubbles Software Engineering & Architecture Specification
## Version 1.0
### Author
Zak MacLeod

---

# Document Purpose

This document serves as the complete software engineering specification for the BlueBubbles messaging platform.

Unlike a traditional Software Requirements Specification (SRS), this document has been designed specifically to act as the master blueprint for both human software engineers and modern AI coding assistants.

The purpose of this document is to remove ambiguity from development by specifying every architectural decision before implementation begins.

This document should be considered the single source of truth for the project.

Whenever implementation decisions conflict with this document, this document takes precedence.

---

# Document Goals

BlueBubbles shall be developed as a professional, enterprise-grade desktop messaging platform designed exclusively for Local Area Networks (LANs).

The application must prioritise:

- Security
- Reliability
- Maintainability
- Scalability
- Readability
- Extensibility
- Performance
- Low Resource Usage

The software must be capable of operating entirely without an Internet connection.

No cloud services may ever be required.

All communication shall remain inside the organisation's own network.

---

# Intended Audience

This document is intended for:

• Software Engineers

• AI Coding Models

• Security Analysts

• OCR A-Level NEA Moderators

• System Administrators

• Future Developers

---

# Coding Philosophy

BlueBubbles shall not be developed as a prototype.

It shall instead follow professional software engineering practices used in industry.

Every feature shall be designed before implementation.

Every class shall have a single responsibility.

Every module shall solve exactly one problem.

Every dependency shall have a clearly defined purpose.

Every component shall be testable independently.

---

# Software Engineering Principles

The project shall follow the following principles.

## SOLID

### Single Responsibility Principle

Each class shall only have one reason to change.

Example:

UserRepository

ONLY interacts with users.

Never encrypts messages.

Never performs authentication.

Never communicates directly with the GUI.

---

MessageEncryptor

ONLY encrypts messages.

Never stores messages.

Never communicates with the database.

Never authenticates users.

---

ChatWindow

ONLY displays data.

Never communicates directly with PostgreSQL.

Never performs encryption.

Never performs authentication.

---

### Open / Closed Principle

Classes should be open for extension but closed for modification.

New features should normally be implemented through inheritance or composition rather than modifying stable code.

---

### Liskov Substitution Principle

Derived classes must always be usable in place of their parent classes.

---

### Interface Segregation Principle

Interfaces shall remain small and focused.

Avoid "God Interfaces".

---

### Dependency Inversion Principle

High-level modules shall never depend directly upon low-level implementations.

Dependencies shall instead depend upon abstractions.

---

# General Coding Standards

Programming Language

Python 3.13+

---

GUI Framework

PySide6 (Qt6)

---

Database

PostgreSQL

---

ORM

SQLAlchemy 2.x

---

Networking

FastAPI

HTTP/2

WebSockets

---

Caching

Redis

---

Authentication

LDAP

Active Directory

---

Cryptography

cryptography

PyNaCl

Argon2

OpenSSL

---

Testing

pytest

pytest-asyncio

pytest-cov

---

Formatting

black

ruff

mypy

---

Documentation

Markdown

Google-style Docstrings

Type Hints

---

# Object Oriented Programming Standards

The entire codebase shall be Object Oriented.

Procedural programming shall only be used where it improves readability.

Every significant object inside the system shall be represented as a class.

Examples include:

User

Message

Conversation

Attachment

Server

Session

Notification

FileTransfer

Group

Channel

Presence

EncryptionContext

AuthenticationSession

DatabaseConnection

SettingsManager

ThemeManager

KeyManager

AuditLogger

---

No global mutable state shall exist.

Configuration shall instead be loaded through dependency injection.

---

# Architectural Goals

The software shall be designed around loose coupling.

Modules should know as little as possible about one another.

The software shall instead communicate through:

Interfaces

DTOs

Events

Dependency Injection

Service Layers

Repository Layers

---

The architecture shall support future features without requiring significant rewrites.

Future features include:

Voice Calls

Video Calls

Screen Sharing

Remote Desktop

Message Reactions

Bots

Plugin System

Cross-platform Clients

Mobile Client

Linux Client

macOS Client

---

# High-Level System Overview

The application consists of five major systems.

──────────────────────────────

Desktop Client

↓

API Layer

↓

Application Services

↓

Persistence Layer

↓

Storage

──────────────────────────────

The Desktop Client is responsible only for presentation.

The API Layer exposes endpoints.

Application Services contain business logic.

Repositories communicate with databases.

Storage manages PostgreSQL, Redis and encrypted files.

---

# Architectural Rules

The GUI may NEVER communicate directly with PostgreSQL.

The GUI may NEVER perform SQL queries.

The GUI may NEVER manipulate cryptographic keys.

The GUI may NEVER perform authentication.

The GUI must communicate exclusively with service classes.

---

Services shall never render GUI components.

Repositories shall never perform encryption.

Encryption classes shall never communicate directly with SQL.

Authentication classes shall never display GUI windows.

Every responsibility belongs to exactly one layer.

---

# Performance Objectives

The application shall remain responsive under normal office workloads.

Target Performance

10 simultaneous users

Average message latency:

<100ms on Gigabit LAN

Message delivery:

<300ms

Cold startup:

<5 seconds

Warm startup:

<2 seconds

Database query:

<50ms average

Message encryption:

<5ms

Conversation loading:

<250ms

Search:

<500ms

File transfer startup:

<200ms

Memory usage:

Idle Client

<300MB RAM

Typical Client

<600MB RAM

Server

<4GB RAM for 50 users

---

# Security Objectives

BlueBubbles is designed around the assumption that attackers may already have access to the internal network.

Therefore:

The network shall never be trusted.

Clients shall never be trusted.

Servers shall never be trusted.

Authentication shall always be required.

Messages shall always remain encrypted.

Private keys shall never leave client devices.

The server shall never possess plaintext messages.

Every action shall be logged.

Every login shall be verified.

Every request shall be authenticated.

Every permission shall be checked.

---

# AI Development Instructions

The implementation AI shall follow these rules without exception.

DO NOT generate placeholder implementations.

DO NOT generate TODO comments.

DO NOT create unfinished methods.

DO NOT ignore type hints.

DO NOT merge unrelated classes.

DO NOT create God Objects.

DO NOT duplicate logic.

DO NOT sacrifice architecture for shorter code.

DO NOT skip testing.

DO NOT use weak cryptography.

DO NOT invent APIs.

DO NOT create undocumented behaviour.

Every generated file shall compile.

Every generated module shall contain documentation.

Every generated class shall include complete docstrings.

Every public method shall include:

Purpose

Arguments

Return Value

Exceptions

Every module shall be independently testable.

This concludes Part 1.

Part 2 begins with the complete system architecture, network topology, message lifecycle, encryption lifecycle, deployment architecture, and the rationale behind every major engineering decision.

# Part 2 — Complete System Architecture

---

# Chapter 1 — System Overview

BlueBubbles follows a traditional client-server architecture specifically designed for deployment within a trusted physical environment while assuming the network itself cannot be trusted.

Although all devices operate on the same Local Area Network (LAN), every communication channel is encrypted and authenticated. No client communicates directly with another client. Every request flows through the central server.

This architecture provides:

- Centralised user management
- Simplified backup
- Easier auditing
- Message persistence
- Reduced client complexity
- Better scalability
- Easier administration
- Complete separation of concerns

Unlike peer-to-peer messaging systems, the server acts as the authoritative source for all metadata while remaining incapable of reading encrypted message content.

---

# Chapter 2 — High-Level Architecture

```text
                         ┌───────────────────────────┐
                         │      Active Directory     │
                         │          (LDAP)           │
                         └─────────────┬─────────────┘
                                       │
                              Authentication
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     BlueBubbles Application Server                  │
│                                                                     │
│  ┌──────────────────────────────────────────────┐                  │
│  │                FastAPI Gateway                │                  │
│  └──────────────────────────────────────────────┘                  │
│                     │                     │                         │
│                     ▼                     ▼                         │
│      Authentication Service     WebSocket Manager                  │
│                     │                     │                         │
│                     ▼                     ▼                         │
│          Messaging Service      Presence Service                    │
│                     │                     │                         │
│                     └──────────┬──────────┘                         │
│                                ▼                                    │
│                     Repository Layer                                │
│                                │                                    │
│        ┌──────────────┬──────────────┬──────────────┐               │
│        ▼              ▼              ▼              ▼               │
│   PostgreSQL       Redis      File Storage     Audit Logs           │
└─────────────────────────────────────────────────────────────────────┘
               ▲                    ▲                     ▲
               │                    │                     │
               │ HTTPS/WebSocket    │                     │
               │                    │                     │
      ┌────────┴─────────┐  ┌───────┴────────┐  ┌────────┴─────────┐
      │ Windows Client 1 │  │ Windows Client │  │ Windows Client N │
      └──────────────────┘  └────────────────┘  └──────────────────┘
```

---

# Chapter 3 — Architectural Philosophy

Every subsystem has exactly one responsibility.

No subsystem is permitted to "reach around" another subsystem.

Example:

Correct

GUI

↓

API Client

↓

Application Service

↓

Repository

↓

Database

Incorrect

GUI

↓

SQL Query

The second approach tightly couples the user interface to the database and violates separation of concerns.

---

# Chapter 4 — Layered Architecture

BlueBubbles is divided into seven logical layers.

---

## Layer 1 — Presentation Layer

Purpose

Everything the user sees.

Contains

Main Window

Chat Window

Contact List

Notifications

Settings

Dialogs

File Pickers

Emoji Picker

Theme Engine

Responsibilities

Display information

Collect user input

Send requests

Render responses

Must NOT

Encrypt messages

Perform SQL

Authenticate users

Read configuration files directly

Generate keys

---

## Layer 2 — Client Services

Purpose

Coordinates the GUI.

Contains

ChatService

MessageService

FileTransferService

SettingsService

NotificationService

Responsibilities

Convert GUI actions into requests.

Update interface.

Manage local cache.

Synchronise state.

---

## Layer 3 — Networking Layer

Purpose

All network communication.

Contains

HTTP Client

WebSocket Client

Request Queue

Retry Manager

Heartbeat Manager

Connection Monitor

Responsibilities

Send requests.

Reconnect automatically.

Maintain WebSocket.

Queue failed requests.

Retry safely.

---

## Layer 4 — API Layer

Purpose

Expose server functionality.

Contains

REST Endpoints

Authentication

Validation

Rate Limiting

Permissions

Responsibilities

Validate requests.

Authorise users.

Call services.

Return responses.

---

## Layer 5 — Business Logic Layer

Purpose

Contains all application rules.

Contains

Messaging Service

Authentication Service

Group Service

Contact Service

Presence Service

Audit Service

Announcement Service

Responsibilities

Apply permissions.

Encrypt metadata.

Process requests.

Store messages.

Notify users.

---

## Layer 6 — Persistence Layer

Purpose

Hide all storage implementations.

Contains

Repositories

Database Models

Transactions

Responsibilities

Read data.

Write data.

Cache data.

Maintain consistency.

---

## Layer 7 — Storage Layer

Contains

PostgreSQL

Redis

Encrypted Attachments

Log Files

Backups

Responsibilities

Persist data.

Recover data.

Provide durability.

---

# Chapter 5 — Server Responsibilities

The server is responsible for:

User authentication

Session management

Permission checking

Group membership

Message routing

Encrypted message storage

Attachment storage

Presence

Typing indicators

Notifications

Audit logging

Configuration

Backups

Statistics

Health monitoring

The server SHALL NOT

Read plaintext messages.

Store plaintext files.

Store decrypted AES keys.

Store plaintext private keys.

Modify encrypted payloads.

---

# Chapter 6 — Client Responsibilities

The desktop client is responsible for:

Rendering UI

Generating encryption keys

Encrypting messages

Decrypting messages

Signing messages

Verifying signatures

Displaying notifications

Caching recent chats

Uploading files

Downloading files

Maintaining active sessions

The client SHALL NEVER

Run SQL queries.

Modify server configuration.

Authenticate other users.

---

# Chapter 7 — Threading Model

The application shall be heavily asynchronous.

Separate execution contexts shall exist for:

GUI Thread

Network Thread

Encryption Worker Pool

Database Thread Pool

File Upload Workers

File Download Workers

Notification Worker

Logging Worker

Image Thumbnail Generator

This prevents the interface from freezing during expensive operations.

---

# Chapter 8 — Client Startup Sequence

```text
User launches BlueBubbles

↓

Load configuration

↓

Initialise logging

↓

Load theme

↓

Load encrypted local profile

↓

Initialise cryptographic providers

↓

Connect to server

↓

Authenticate user

↓

Download profile

↓

Synchronise contacts

↓

Synchronise unread messages

↓

Connect WebSocket

↓

Display UI
```

Target startup time:

Cold Start

<5 seconds

Warm Start

<2 seconds

---

# Chapter 9 — Message Lifecycle

```text
User types message

↓

Message DTO created

↓

Validate input

↓

Generate AES-256 session key

↓

Encrypt plaintext

↓

Encrypt AES key using recipient public key

↓

Sign encrypted payload

↓

Transmit via HTTPS/WebSocket

↓

Server validates request

↓

Server stores encrypted payload

↓

Server stores encrypted AES key

↓

Server publishes event via Redis

↓

Recipient notified

↓

Recipient downloads message

↓

Recipient decrypts AES key

↓

Recipient decrypts payload

↓

Verify digital signature

↓

Render message
```

The server never possesses the plaintext.

---

# Chapter 10 — File Transfer Lifecycle

```text
User selects file

↓

Calculate SHA-256 hash

↓

Split into chunks

↓

Compress (optional)

↓

Encrypt each chunk independently

↓

Upload chunks

↓

Server stores encrypted chunks

↓

Recipient downloads chunks

↓

Verify chunk hashes

↓

Decrypt chunks

↓

Reassemble file

↓

Verify final SHA-256 checksum
```

Chunking enables:

Resume uploads

Resume downloads

Parallel transfers

Reduced RAM usage

Better scalability

---

# Chapter 11 — Authentication Lifecycle

```text
Launch application

↓

User enters credentials

↓

Credentials transmitted via TLS

↓

LDAP validation

↓

User record retrieved

↓

JWT Access Token issued

↓

Refresh Token issued

↓

Encrypted session created

↓

Client stores session securely

↓

WebSocket authenticated

↓

User becomes online
```

Passwords are never stored locally.

Only encrypted session tokens are cached.

---

# Chapter 12 — Presence System

Presence shall be managed independently of messaging.

Supported states:

Online

Away

Busy

Do Not Disturb

Invisible

Offline

Redis Pub/Sub shall distribute presence updates in real time.

Presence data expires automatically if heartbeat packets stop arriving.

---

# Chapter 13 — Failure Recovery

The application shall recover automatically from:

Server restart

Redis restart

Temporary network loss

Dropped WebSocket

Database reconnect

Client sleep

Client wake

Connection retries shall use exponential backoff.

No user action should normally be required.

---

# Chapter 14 — Scalability Targets

Version 1.0

10–50 concurrent users

Future Version

250+ users

The architecture must therefore avoid assumptions that only a handful of users will ever exist.

No hard-coded limits shall exist for:

Users

Messages

Groups

Contacts

Channels

Attachments

---

# End of Part 2

The next section (Part 3) will define the **complete folder structure**, development standards, package layout, dependency graph, naming conventions, and the exact directory tree for every Python module before any code is written. This will become the blueprint that the coding AI follows when creating the project structure.

# Part 3 — Project Structure, Package Layout and Development Standards

---

# Chapter 15 — Project Philosophy

The project shall be organised using a modular architecture based upon Object-Oriented Programming (OOP) principles.

Each module shall have exactly one responsibility.

Large files containing unrelated logic are strictly prohibited.

The software shall be structured so that an unfamiliar developer can immediately determine where every feature belongs.

Every package shall have a clearly defined purpose.

---

# Chapter 16 — Root Project Structure

The entire project shall be organised as follows.

```text
BlueBubbles/

├── client/
├── server/
├── shared/
├── tests/
├── docs/
├── deployment/
├── scripts/
├── assets/
├── config/
├── database/
├── logs/
├── uploads/
├── cache/
├── requirements/
├── .env.example
├── pyproject.toml
├── README.md
├── LICENSE
└── CHANGELOG.md
```

The root directory shall never contain application logic.

Its only purpose is project organisation.

---

# Chapter 17 — Client Package

The client package contains the desktop application.

```text
client/

main.py

application.py

bootstrap.py

config/

gui/

controllers/

services/

network/

crypto/

storage/

models/

events/

workers/

utils/

resources/
```

The client package is responsible only for:

Rendering

Input

Encryption

Networking

Local Storage

Notifications

It shall never communicate directly with PostgreSQL.

---

# Chapter 18 — GUI Package

The GUI package shall be organised as follows.

```text
gui/

windows/

dialogs/

widgets/

layouts/

themes/

icons/

animations/

styles/

validators/
```

Every visible component belongs here.

---

## Windows

Contains:

MainWindow

LoginWindow

SettingsWindow

ProfileWindow

AdminWindow

AboutWindow

---

## Dialogs

Contains:

File Dialog

Delete Dialog

Confirmation Dialog

Group Creation

Rename Group

Join Group

Leave Group

---

## Widgets

Contains reusable controls.

Examples:

Chat Bubble

Message Card

Typing Indicator

User Avatar

Presence Badge

Contact Item

Conversation Item

Attachment Preview

Progress Bar

Emoji Picker

Image Viewer

Notification Card

---

# Chapter 19 — Controllers

Controllers connect GUI events with application services.

Controllers contain NO business logic.

Example

```text
LoginController

↓

AuthenticationService.login()

↓

Response

↓

Update GUI
```

Controllers never access SQL.

Controllers never encrypt data.

---

# Chapter 20 — Client Services

Client Services coordinate application behaviour.

```text
services/

AuthenticationService

ChatService

GroupService

MessageService

PresenceService

NotificationService

FileTransferService

SettingsService

ThemeService

CacheService

SearchService
```

Services communicate with networking classes.

Services do not render GUI.

---

# Chapter 21 — Networking Package

```text
network/

ApiClient

WebSocketClient

RequestQueue

HeartbeatManager

ConnectionMonitor

ReconnectManager

PacketSerializer

PacketDeserializer
```

Networking classes know nothing about GUI.

Networking classes know nothing about SQL.

---

# Chapter 22 — Cryptography Package

The crypto package is completely isolated.

```text
crypto/

KeyManager

AESManager

SignatureManager

NonceGenerator

RandomGenerator

KeyStore

Hashing

CertificateValidator

EncryptionContext
```

No other package shall directly perform cryptographic operations.

All encryption must pass through these classes.

---

# Chapter 23 — Storage Package

Responsible for local data.

```text
storage/

CacheManager

ProfileStore

ConversationCache

AttachmentCache

SettingsStore

SessionStore
```

The storage package never communicates with PostgreSQL.

---

# Chapter 24 — Worker Package

Long-running tasks execute here.

```text
workers/

EncryptionWorker

DecryptionWorker

UploadWorker

DownloadWorker

ThumbnailWorker

NotificationWorker

SearchWorker

BackupWorker
```

Workers prevent the GUI thread from freezing.

---

# Chapter 25 — Server Package

```text
server/

main.py

application.py

bootstrap.py

api/

services/

repositories/

database/

auth/

crypto/

websocket/

middleware/

models/

schemas/

events/

workers/

logging/

utils/

configuration/
```

---

# Chapter 26 — API Package

```text
api/

auth.py

messages.py

groups.py

contacts.py

users.py

files.py

presence.py

settings.py

admin.py

health.py
```

Every file exposes one REST endpoint group.

---

# Chapter 27 — Service Layer

Contains business logic.

```text
services/

AuthenticationService

MessagingService

GroupService

AttachmentService

PresenceService

TypingService

AuditService

AnnouncementService

PermissionService

SearchService

StatisticsService

HealthService
```

Business rules belong only here.

---

# Chapter 28 — Repository Layer

Repositories communicate with PostgreSQL.

```text
repositories/

UserRepository

MessageRepository

AttachmentRepository

GroupRepository

SessionRepository

AuditRepository

SettingsRepository

PresenceRepository
```

Repositories shall never:

Encrypt

Authenticate

Validate permissions

Render UI

---

# Chapter 29 — Database Package

```text
database/

connection.py

session.py

migration.py

base.py

seed.py

```

Contains only database infrastructure.

---

# Chapter 30 — Authentication Package

```text
auth/

LDAPAuthenticator

SessionManager

TokenManager

PasswordHasher

PermissionManager

RoleManager

AccountRecovery
```

Authentication logic belongs nowhere else.

---

# Chapter 31 — Middleware

```text
middleware/

AuthenticationMiddleware

LoggingMiddleware

RateLimitMiddleware

CORSMiddleware

ExceptionMiddleware

TimingMiddleware
```

---

# Chapter 32 — Shared Package

Everything shared by client and server belongs here.

```text
shared/

constants/

dto/

enums/

exceptions/

protocol/

validators/

utilities/

interfaces/

events/
```

No application-specific logic belongs inside shared.

---

# Chapter 33 — Data Transfer Objects

DTOs define network communication.

Examples

LoginRequest

LoginResponse

MessageRequest

MessageResponse

GroupRequest

PresenceUpdate

TypingEvent

AttachmentMetadata

UserProfile

ConversationSummary

DTOs contain no logic.

---

# Chapter 34 — Events

Every major action shall produce an event.

Examples

UserLoggedIn

UserLoggedOut

MessageSent

MessageDelivered

MessageRead

AttachmentUploaded

AttachmentDownloaded

PresenceChanged

GroupCreated

GroupDeleted

Events allow future expansion without modifying existing code.

---

# Chapter 35 — Utility Package

Contains small reusable helpers.

Examples

DateFormatter

TimeFormatter

UUIDGenerator

FileUtilities

ImageUtilities

ClipboardUtilities

CompressionUtilities

NetworkUtilities

Utilities shall remain stateless.

---

# Chapter 36 — Configuration

No magic numbers.

No hardcoded addresses.

No hardcoded ports.

No hardcoded passwords.

Configuration shall be loaded from:

```text
.env

config.yaml

settings.json
```

Priority

Environment Variables

↓

YAML

↓

Defaults

---

# Chapter 37 — Naming Conventions

Classes

PascalCase

Example

AuthenticationService

Variables

snake_case

Functions

snake_case

Constants

UPPER_CASE

Private members

_prefix

Protected members

_prefix

Magic methods

Python standard naming only.

---

# Chapter 38 — File Size Limits

Maximum class size

≈400 lines

Maximum module

≈800 lines

Maximum function

≈50 lines

Maximum nesting

3 levels

Maximum cyclomatic complexity

10

If these limits are exceeded, refactor.

---

# Chapter 39 — Import Rules

Allowed

GUI

↓

Controller

↓

Service

↓

Repository

↓

Database

Forbidden

Repository

↓

GUI

Forbidden

GUI

↓

Database

Forbidden

Encryption

↓

GUI

Forbidden

Repository

↓

Networking

Dependencies shall always point downward.

---

# Chapter 40 — Dependency Graph

```text
GUI

↓

Controllers

↓

Services

↓

Repositories

↓

Database

↓

Storage
```

Cross-layer shortcuts are forbidden.

---

# Chapter 41 — Logging Standards

Every module shall use structured logging.

Log Levels

DEBUG

INFO

WARNING

ERROR

CRITICAL

Every exception shall include:

Timestamp

Class

Method

Stack Trace

User (if applicable)

Session ID

Correlation ID

---

# Chapter 42 — Documentation Standards

Every public class must include:

Purpose

Responsibilities

Dependencies

Usage Example

Every public method shall document:

Arguments

Returns

Raises

Side Effects

Examples

Every module shall include a module-level description.

---

# Chapter 43 — AI Implementation Rules

The implementation AI must:

Create every directory before writing code.

Generate __init__.py files where required.

Use type hints throughout.

Follow SOLID principles.

Use dependency injection.

Avoid circular imports.

Generate docstrings.

Generate unit tests alongside implementation.

Refactor duplicated logic immediately.

Never implement placeholder code.

Never leave TODO comments.

Never generate dead code.

Never violate the architectural rules defined in Parts 1–3.

---

# End of Part 3

Part 4 will define the **complete object-oriented domain model**, including every core class (User, Message, Conversation, Group, Attachment, Session, Notification, etc.), their attributes, methods, inheritance relationships, interfaces, and interactions before implementation begins.

# Part 30 — Project-wide execution and quality rules (selected verbatim chapters)

# Chapter 3325 — Final Execution Contract Purpose

This section defines the binding implementation contract for any coding AI, developer or automated development system producing BlueBubbles.

It converts the complete specification into mandatory execution rules.

The implementation process shall:

* Follow the defined architecture.
* Preserve the defined security boundaries.
* Produce functional code rather than placeholders.
* Build the project in dependency order.
* Verify each subsystem before continuing.
* Keep server and client protocol models compatible.
* Prevent plaintext content from entering server-controlled storage.
* Preserve user work during failures.
* Produce tested installation and recovery procedures.
* Generate documentation matching the final implementation.
* Deliver one complete Version 1.0 project.

Where an implementation choice conflicts with this specification, the specification shall take priority unless the change is documented formally and all affected requirements are updated.

---

# Chapter 3326 — Coding-AI Role

The coding AI shall act as:

```text
Software architect

Backend developer

Desktop-client developer

Database designer

Security engineer

Test engineer

Deployment engineer

Technical-documentation writer
```

It shall not act as an unconstrained code generator that produces disconnected files without verification.

Every generated component shall fit the defined system.

---

# Chapter 3327 — Binding Instruction Priority

Implementation decisions shall follow this priority:

```text
1. Security and data-integrity requirements

2. Explicit functional requirements

3. Architectural boundaries

4. Protocol and database contracts

5. Reliability and recovery requirements

6. Testing requirements

7. User-interface requirements

8. Performance guidance

9. Optional implementation preferences
```

A lower-priority convenience shall not override a higher-priority requirement.

---

# Chapter 3328 — No Silent Requirement Changes

The coding AI shall not silently:

* Remove features.
* Add unsupported features.
* Weaken encryption.
* Change roles.
* Replace PostgreSQL with SQLite on the server.
* Replace PySide6 with a browser interface.
* Replace FastAPI with another framework.
* Expose PostgreSQL or Redis to clients.
* Change recipient-key semantics.
* Store plaintext for convenience.
* Change the supported deployment model.
* Claim deferred functionality is implemented.

Any required change shall be recorded as an architecture or requirement amendment.

---

# Chapter 3329 — Mandatory Technology Stack

The implementation shall use:

```text
Programming language:

Python 3.13 or the final tested supported Python version

Server framework:

FastAPI

ASGI server:

Uvicorn

Desktop interface:

PySide6 with Qt 6

Primary server database:

PostgreSQL

Server ORM and database toolkit:

SQLAlchemy 2.x async APIs

Database migrations:

Alembic

Transient server state:

Redis

Reverse proxy:

Nginx

Server service manager:

systemd

Message and attachment authenticated encryption:

AES-256-GCM

User encryption keys:

X25519

User signing keys:

Ed25519

Key derivation:

HKDF-SHA-256

Local password hashing:

Argon2id

Primary production server OS:

Debian 13

Primary production client OS:

Windows 11
```

Equivalent substitutions require explicit approval and complete retesting.

---

# Chapter 3330 — Mandatory Architectural Style

BlueBubbles shall be implemented as:

```text
A layered modular monolith
```

Server layers:

```text
API routers

↓

Application services

↓

Domain rules and repository interfaces

↓

Unit of Work

↓

Infrastructure repositories and adapters

↓

PostgreSQL, Redis, LDAP and filesystem
```

Client layers:

```text
Views

↓

ViewModels

↓

Client application services

↓

Networking, cryptography and local repositories

↓

Server APIs, secure store and local database
```

Layers shall not be bypassed merely to reduce code length.

---

# Chapter 3331 — Required Repository Layout

The final project shall use a coherent structure similar to:

```text
bluebubbles/
├── pyproject.toml
├── README.md
├── LICENSE
├── CHANGELOG.md
├── requirements/
├── configuration/
├── deployment/
├── documentation/
├── migrations/
├── scripts/
├── src/
│   └── bluebubbles/
│       ├── shared/
│       ├── server/
│       └── client/
└── tests/
```

Within `server`:

```text
api/
application/
domain/
infrastructure/
workers/
monitoring/
security/
configuration/
```

Within `client`:

```text
application/
services/
security/
storage/
networking/
viewmodels/
views/
widgets/
resources/
```

---

# Chapter 3332 — Shared Package Rules

The shared package may contain:

* DTOs.
* Enums.
* Error codes.
* Protocol envelopes.
* Pagination models.
* Algorithm identifiers.
* Version models.
* Canonicalisation contracts.
* General immutable value types.

It shall not contain:

* FastAPI router code.
* SQLAlchemy ORM models.
* PySide6 widgets.
* PostgreSQL sessions.
* Windows-specific secure-store implementations.
* Server service instances.
* Client application state.

---

# Chapter 3333 — Server Domain Rules

The server domain layer shall not import:

```text
FastAPI
Uvicorn
PySide6
SQLAlchemy AsyncSession
Redis clients
LDAP libraries
Filesystem implementation classes
```

It may define:

* Entities.
* Value objects.
* Domain services.
* Repository protocols.
* Permission rules.
* State transitions.
* Domain exceptions.

---

# Chapter 3334 — Application Service Rules

Application services shall:

* Receive dependencies through constructors.
* Perform permission checks.
* Coordinate repositories.
* Define transaction boundaries.
* Create audit events.
* Create outbox events.
* Return typed results.
* Translate domain failures into application errors.

Application services shall not:

* Create global database connections.
* Access PySide6 widgets.
* Build SQL manually without repository boundaries.
* Read environment variables directly.
* Decrypt end-to-end message content on the server.

---

# Chapter 3335 — Router Rules

FastAPI routers shall:

* Parse and validate requests.
* Obtain authenticated request context.
* Call application services.
* Map service results to responses.
* Map application errors through central handlers.

Routers shall not:

* Implement business rules.
* Write directly through SQLAlchemy.
* Open raw filesystem paths.
* Perform cryptographic content decryption.
* Duplicate permission logic.
* Contain large transaction workflows.

---

# Chapter 3336 — Client View Rules

PySide6 views shall:

* Construct visual controls.
* Bind to ViewModels.
* Display state.
* Emit user actions.
* Manage focus and presentation.
* Dispose connections safely.

Views shall not:

* Call HTTP endpoints directly.
* Query SQLite directly.
* Generate encryption keys.
* Encrypt or decrypt messages.
* Apply server permissions.
* Manage authentication tokens.
* Start unmanaged background tasks.

---

# Chapter 3337 — ViewModel Rules

ViewModels shall:

* Expose presentation state.
* Validate user input for usability.
* Call client application services.
* Translate results into UI state.
* Emit signals.
* Preserve drafts through repositories.
* Handle loading, empty and error states.
* Dispose subscriptions.

They shall not become general-purpose service containers.

---

# Chapter 3338 — Constructor Injection Rule

Important classes shall receive dependencies explicitly.

Prohibited pattern:

```python
class Service:
    def __init__(self) -> None:
        self.settings = load_settings()
        self.database = connect_database()
        self.redis = connect_redis()
```

Required pattern:

```python
class Service:
    def __init__(
        self,
        repository: Repository,
        permission_service: PermissionService,
        clock: Clock,
    ) -> None:
        self._repository = repository
        self._permission_service = permission_service
        self._clock = clock
```

---

# Chapter 3339 — Global State Restriction

The implementation shall not store request-specific mutable data in global variables.

Prohibited global state includes:

```text
Current user
Current session
Current transaction
Current conversation
Current request
Current access token
Current message plaintext
Current encryption key
```

Application-wide immutable configuration and safely managed singleton resources are permitted.

---

# Chapter 3340 — Async Implementation Rule

Network, database and filesystem I/O shall use asynchronous interfaces where supported.

Examples:

```text
PostgreSQL queries
Redis operations
HTTP requests
WebSocket operations
LDAP requests where adapter support allows
File streaming
Background workers
```

CPU-intensive or blocking operations shall not execute on the Qt GUI thread.

---

# Chapter 3341 — Async Task Ownership

Every asynchronous task shall have one clear owner.

The owner shall:

* Store the task reference.
* Observe completion.
* Retrieve exceptions.
* Cancel it during shutdown.
* Remove completed references.
* Prevent duplicate task creation.

Untracked calls to:

```python
asyncio.create_task(...)
```

shall be avoided.

---

# Chapter 3342 — Cancellation Rule

Long-running operations shall support cooperative cancellation.

Mandatory cancellable operations:

* Attachment preparation.
* Attachment upload.
* Attachment download.
* Full synchronisation.
* Search-index rebuild.
* Cache cleanup.
* Diagnostic-package generation.
* Large export generation where client controlled.

Cancellation shall occur only at safe boundaries.

---

# Chapter 3343 — Database Authority Rule

PostgreSQL shall remain authoritative for:

```text
Users
Roles
Permissions
Sessions
Conversation membership
Messages
Recipient envelopes
Attachments
Audit
Outbox
Announcements
Configuration history
Security alerts
Administrative records
```

Redis shall never become the only source of permanent business state.

---

# Chapter 3344 — Local Database Authority Rule

The client local database shall be authoritative only for local state such as:

```text
Drafts
Offline queue
Local cache
Transfer state
Search index
Synchronisation checkpoints
Local preferences
```

It shall not override current server membership, permissions or key revocation state.

---

# Chapter 3345 — Unit of Work Requirement

Every multi-record server business transaction shall use one Unit of Work.

Examples:

* Send message.
* Edit message.
* Delete message.
* Disable user.
* Change role.
* Transfer group ownership.
* Finalise attachment.
* Publish announcement.
* Update configuration.

The business record, audit event and outbox event shall commit atomically where required.

---

# Chapter 3346 — Explicit Commit Rule

Services shall commit explicitly.

A context manager shall not automatically commit every transaction solely because no exception was raised unless that behaviour is deliberately standardised and documented.

The preferred pattern is:

```python
async with unit_of_work_factory() as unit_of_work:
    ...
    await unit_of_work.commit()
```

---

# Chapter 3347 — Transaction Duration Rule

Database transactions shall remain short.

Do not hold transactions open during:

* File upload streaming.
* File download streaming.
* LDAP authentication.
* Long cryptographic processing.
* WebSocket publication.
* User interaction.
* External diagnostics.
* Long export generation.

---

# Chapter 3348 — Row-Locking Rule

Use row locks only when required for consistency.

Examples:

* Refresh-token rotation.
* Audit-chain append.
* Group ownership transfer.
* Versioned message edit.
* Configuration version update.
* Final SuperAdministrator protection.
* Upload finalisation.

Lock ordering shall be documented where multiple rows are involved.

---

# Chapter 3349 — Database Migration Rule

Every database schema change shall include:

* Alembic migration.
* ORM update.
* Repository update.
* Constraint tests.
* Migration test.
* Upgrade documentation.
* Rollback or restore impact.
* Schema documentation update.

Manual production schema edits shall not be part of normal operation.

---

# Chapter 3350 — Database Naming Rule

Database names shall use consistent lowercase snake case.

Examples:

```text
user_id
conversation_id
created_at
is_enabled
message_recipient_keys
audit_chain_state
```

Foreign-key and index naming shall follow the SQLAlchemy naming convention.

---

# Chapter 3351 — Database Constraint Rule

The database shall enforce critical invariants where possible.

Examples:

* Unique normalised username.
* Unique direct-conversation pair.
* Unique recipient envelope per message and recipient.
* Unique chunk index per attachment.
* Valid positive sizes.
* Valid message version.
* Valid active group owner constraint where implementable.
* Valid audit sequence uniqueness.
* Valid configuration version uniqueness.

Application validation alone is insufficient.

---

# Chapter 3352 — Soft Deletion Rule

Shared records shall use soft deletion or tombstones where history and references must remain intact.

Examples:

* Messages.
* Conversations.
* Users.
* Announcements.
* Attachments awaiting retention cleanup.

Physical deletion shall follow explicit retention and recovery rules.

---

# Chapter 3353 — Audit Append-Only Rule

Normal application code shall have no capability to update or delete individual audit events.

Required protections:

```text
No repository update method

No repository delete method

Restricted database role

Database trigger or equivalent rejection

Hash-chain verification
```

Audit correction shall use a new compensating event.

---

# Chapter 3354 — Outbox Rule

Any durable event that must be published after a database change shall first be recorded in the transactional outbox.

The coding AI shall not:

```text
Commit business record

then

Directly publish event

without recovery record
```

The outbox worker shall publish events after commit.

---

# Chapter 3355 — Outbox Idempotency

Outbox publication shall be safe under retry.

The system shall:

* Claim events safely.
* Detect already published events.
* Record failures.
* Apply bounded retries.
* Prevent one poison event blocking the entire queue.
* Preserve durable business state even if publication fails.

---

# Chapter 3356 — Server Plaintext Prohibition

The server shall not store or intentionally log:

```text
Message plaintext
Attachment plaintext
Draft plaintext
Search plaintext
Message content keys
Attachment file keys
User private keys
Local cache keys
```

This prohibition applies to:

* PostgreSQL.
* Redis.
* Outbox.
* Audit details.
* Logs.
* Diagnostics.
* Exports.
* Temporary files.
* Backups.
* Error messages.

---

# Chapter 3357 — Server Decryption Prohibition

No server service shall require client private keys or decrypt ordinary end-to-end encrypted message or attachment content.

Administrative access shall not provide a hidden decryption path.

Any future moderation design requiring plaintext access would require a separate security model and is outside Version 1.0.

---

# Chapter 3358 — Client Private-Key Rule

Client private keys shall:

* Be generated on the client.
* Be encrypted before disk storage.
* Remain local.
* Use versioned records.
* Be loaded only through the key manager.
* Never be sent to the server.
* Never be placed in logs.
* Never be embedded in diagnostics.
* Be cleared from active references where practical after logout.

---

# Chapter 3359 — Message Encryption Rule

Every message version shall use:

```text
One new random 32-byte content key

AES-256-GCM

One new 12-byte nonce

Canonical AAD

One recipient-specific key envelope per active recipient

One sender key envelope

Ed25519 signature

Explicit format and algorithm identifiers
```

Content-key reuse is prohibited.

---

# Chapter 3360 — Attachment Encryption Rule

Every attachment shall use:

```text
One new random attachment master key

HKDF-derived purpose subkeys

Independent AES-256-GCM encryption per chunk

Fresh 12-byte nonce per chunk

Encrypted metadata

Recipient-specific file-key envelopes

Signed manifest

Encrypted chunk hashes

Final plaintext checksum verification
```

Whole-file loading into memory is prohibited.

---

# Chapter 3361 — Signature Verification Rule

The recipient client shall verify the message or attachment signature before displaying or completing decrypted content.

If verification fails:

* No plaintext shall be returned.
* No partial content shall be displayed.
* The record shall be marked unverified.
* Safe diagnostic information shall be recorded.
* Public-key refresh may be attempted through the defined flow.

---

# Chapter 3362 — Authentication-Tag Rule

AES-GCM authentication failures shall be terminal for that decryption attempt.

The implementation shall not:

* Return partial plaintext.
* Ignore the tag.
* Retry using modified AAD guesses.
* Fall back to unauthenticated decryption.
* Display corrupted output.

---

# Chapter 3363 — Nonce Rule

All AES-GCM operations shall use 12-byte nonces.

Nonces shall be:

* Generated through cryptographically secure randomness.
* Fresh within the key scope.
* Stored with ciphertext.
* Included in signed or authenticated structures where required.

Static or predictable nonce reuse is prohibited.

---

# Chapter 3364 — Algorithm Allowlist Rule

Network-provided algorithm identifiers shall be checked against a fixed allowlist.

The application shall not:

* Dynamically import an algorithm named by a request.
* Accept arbitrary cipher names.
* Negotiate to weak fallback algorithms.
* Accept unknown format versions.
* Guess interpretation of malformed envelopes.

---

# Chapter 3365 — Authentication Provider Rule

Authentication providers shall return validated identities only.

They shall not:

* Issue application tokens.
* Create application sessions directly.
* Set UI state.
* Assign unrestricted roles without mapping policy.
* Log submitted passwords.
* Persist plaintext credentials.

---

# Chapter 3366 — Active Directory Security Rule

Production directory authentication shall use:

```text
LDAPS

or

LDAP with StartTLS
```

Certificate validation is mandatory.

LDAP search values shall use library-supported escaping.

A directory service account shall be least privileged.

---

# Chapter 3367 — Token Rule

Access tokens shall:

* Have bounded lifetime.
* Validate issuer.
* Validate audience.
* Validate algorithm.
* Validate session identifier.
* Validate token version.
* Validate expiry.
* Reject inactive sessions.

Refresh tokens shall:

* Be random.
* Be stored hashed on the server.
* Rotate after use.
* Detect reuse.
* Be stored in the client secure store.

---

# Chapter 3368 — Session Revocation Rule

Session revocation shall:

```text
Invalidate database session

↓

Commit

↓

Publish revocation event

↓

Disconnect WebSockets
```

Failure to disconnect a socket shall not reactivate the session.

---

# Chapter 3369 — Authorisation Rule

Every protected server endpoint shall enforce:

```text
Authentication

↓

Session validity

↓

Enabled user state

↓

Named permission

↓

Resource-level policy
```

Client-side hidden buttons are not authorisation.

---

# Chapter 3370 — Group Membership Rule

For each group message, the server shall verify that recipient envelopes correspond exactly to currently authorised active members.

The recipient set shall:

* Include the sender.
* Exclude removed members.
* Exclude unrelated users.
* Contain no duplicates.
* Use acceptable active key versions.

---

# Chapter 3371 — Offline Replay Rule

Before replaying queued protected writes, the client shall refresh:

```text
Protocol compatibility
Current user state
Policy
Conversation membership
Relevant permissions
Recipient public keys
```

Stale local assumptions shall never override server state.

---

# Chapter 3372 — Idempotency Rule

Every retryable write shall have a stable idempotency identifier.

At minimum:

* Message send uses stable message UUID.
* Upload chunks use upload ID and chunk index.
* Announcement acknowledgement uses stable user and announcement identity.
* Preference writes use action identity or expected version.
* Administrative background jobs use job UUID.

---

# Chapter 3373 — Duplicate Conflict Rule

A repeated request may be treated as success only when the stored operation is equivalent to the repeated request.

A duplicate identifier with different content shall return a conflict.

The system shall never replace an existing message silently because a client reused its UUID incorrectly.

---

# Chapter 3374 — Offline Work Preservation Rule

Drafts, pending messages and prepared attachments shall not be removed automatically because:

* The server is offline.
* Synchronisation fails.
* A message conflicts.
* An edit window expires.
* Membership changes.
* The application restarts.

User work shall be preserved securely unless deletion is explicit or retention cleanup has been confirmed.

---

# Chapter 3375 — Client Profile Isolation Rule

Each user profile shall have separate:

* Local database.
* Local encryption keys.
* Drafts.
* Offline queue.
* Transfer state.
* Search index.
* Cached messages.
* Secure-store namespace.

Signing in as another user shall not expose or process the previous user’s data.

---

# Chapter 3376 — Single-Instance Rule

Only one writable client process may open a profile at a time.

The implementation shall use a profile-specific lock and shall reject unsafe concurrent access.

This protects drafts, queue state and local migrations.

---

# Chapter 3377 — GUI Responsiveness Rule

The GUI thread shall not perform:

```text
Network requests
Database migrations
Large database queries
Message-history decryption batches
Attachment encryption
Attachment hashing
Attachment transfer
Search-index rebuild
Large cache cleanup
Diagnostic archive generation
```

These operations shall use asynchronous tasks or approved workers.

---

# Chapter 3378 — Error Handling Rule

Every boundary shall translate errors into stable application errors.

Flow:

```text
Library exception

↓

Infrastructure or adapter error

↓

Application error

↓

API or client error model

↓

Safe user message
```

Raw stack traces shall not be shown to users.

---

# Chapter 3379 — Sensitive Error Restriction

Error messages and exception context shall not contain:

* Passwords.
* Tokens.
* Database URLs with credentials.
* LDAP credentials.
* Private keys.
* Plaintext messages.
* Attachment plaintext.
* Raw secure-store values.
* Complete encrypted payloads.

---

# Chapter 3380 — Logging Rule

Structured logs shall include where relevant:

```text
Timestamp
Level
Event code
Component
Correlation ID
Safe resource identifiers
Duration
Result
```

They shall exclude prohibited sensitive data.

Logging configuration shall be validated in production.

---

# Chapter 3381 — Correlation Rule

HTTP requests, WebSocket actions, workers and major client operations shall use correlation identifiers.

The same identifier should connect:

* Request log.
* Service log.
* Error response.
* Audit event.
* Outbox event.
* Diagnostic report.

Correlation IDs shall not encode personal data.

---

# Chapter 3382 — Health Endpoint Rule

The final server shall expose:

```text
Liveness

Readiness

Detailed authorised health
```

Liveness shall remain lightweight.

Readiness shall reflect critical dependencies.

Detailed health shall require administrative permission.

---

# Chapter 3383 — Maintenance Mode Rule

Maintenance mode shall have server-authoritative states.

At minimum:

```text
off

read_only

full_maintenance
```

Write endpoints shall check maintenance state.

Health and controlled recovery endpoints shall remain accessible.

---

# Chapter 3384 — Background Worker Rule

Every worker shall have:

* Unique name.
* Configurable schedule.
* Run lock.
* Retry policy.
* Failure count.
* Last-run state.
* Health reporting.
* Graceful shutdown.
* Optional manual-run policy.
* Tests.

---

# Chapter 3385 — Deployment Security Rule

Production deployment shall ensure:

```text
Nginx is the external entry point.

FastAPI binds to loopback or Unix socket.

PostgreSQL is not exposed to the client LAN.

Redis is not exposed to the client LAN.

TLS is required.

Service runs as an unprivileged account.

Secrets remain outside source code.

Attachment mount is validated.

Firewall exposes only approved ports.
```

---

# Chapter 3386 — Configuration Rule

Configuration shall use typed Pydantic models.

Precedence:

```text
Defaults

↓

YAML

↓

Environment variables

↓

Secret files

↓

Approved runtime configuration
```

Unknown keys and unsafe production defaults shall fail startup.

---

# Chapter 3387 — Secret Management Rule

Secrets shall not be stored in:

* Git.
* YAML examples.
* Command histories.
* Process command-line arguments.
* Logs.
* Installer resources.
* Diagnostic packages.
* Unit-test snapshots.

Production secrets shall use protected files or approved secret storage.

---

# Chapter 3388 — Build Reproducibility Rule

The final project shall include:

* Locked dependency versions.
* Repeatable server installation.
* Repeatable client build script.
* Version injection.
* Release checksums.
* Build metadata.
* Clean-environment build instructions.

A build that depends on undocumented local files is not acceptable.

---

# Chapter 3389 — Prohibited Placeholder Implementations

The coding AI shall not leave required production paths containing:

```python
pass
```

```python
raise NotImplementedError
```

```text
TODO: implement later
```

```text
Mock response returned
```

```text
Always allow permission
```

```text
Always return healthy
```

```text
Encryption placeholder
```

Abstract interfaces may use `NotImplementedError` only where a real concrete implementation exists for Version 1.0.

---

# Chapter 3390 — Prohibited Fake Security

The coding AI shall not claim security while using:

* Base64 as encryption.
* Reversible text obfuscation.
* Static AES keys.
* Hard-coded passwords.
* Disabled TLS validation.
* Shared private keys.
* One global message key.
* Client-only permission checks.
* Server-readable plaintext copies.
* Unauthenticated encryption.
* Missing signature verification.
* Silent cryptographic fallback.

---

# Chapter 3391 — Prohibited Fake Reliability

The coding AI shall not claim reliability while:

* Ignoring failed commits.
* Treating timeouts as definite failure without idempotency.
* Deleting drafts after submission begins.
* Marking transfers complete before verification.
* Ignoring background-task exceptions.
* Using fixed sleeps to hide races.
* Advancing sync cursors before commit.
* Silently dropping queue actions.
* Assuming backups work without restore testing.

---

# Chapter 3392 — Prohibited Monolithic Files

The coding AI shall not generate one oversized file containing:

```text
All routes
All models
All services
All database code
All client widgets
All cryptography
```

Modules shall remain cohesive and testable.

Excessive fragmentation into trivial one-line modules shall also be avoided.

---

# Chapter 3393 — Prohibited Circular Dependency Workarounds

The coding AI shall not solve architecture errors by scattering runtime imports throughout the codebase.

Circular imports shall be corrected through:

* Interface extraction.
* Dependency inversion.
* Shared DTO movement.
* Event interfaces.
* Constructor injection.
* Module responsibility correction.

---

# Chapter 3394 — Prohibited Broad Exception Handling

Avoid:

```python
except Exception:
    return None
```

Broad exception handlers may exist only at process or request boundaries where they:

* Log safely.
* Preserve correlation.
* Perform cleanup.
* Return a generic safe error.
* Do not hide programming defects during tests.

---

# Chapter 3395 — Prohibited Data-Loss Shortcuts

The coding AI shall not:

* Delete local databases automatically after migration failure.
* Drop production tables automatically.
* Clear queues on login failure.
* Remove drafts during cache cleanup.
* Overwrite download destinations without confirmation.
* Delete attachment objects without reconciliation.
* Destroy old private keys immediately after rotation.
* Reset the audit chain to hide integrity failure.

---

# Chapter 3396 — Mandatory Development Sequence

The coding AI shall generate the project in this order:

```text
1. Repository and tooling

2. Shared contracts

3. Configuration

4. Domain models and errors

5. Database schema and migrations

6. Repository infrastructure

7. Unit of Work

8. Server lifecycle and health

9. Authentication and sessions

10. Users, contacts and public keys

11. Conversations and groups

12. Client cryptographic prototype

13. Encrypted messaging

14. WebSocket and outbox delivery

15. Attachments

16. Local client storage

17. Offline queue and synchronisation

18. PySide6 interface

19. Administration and audit

20. Monitoring and workers

21. Deployment and packaging

22. Full testing

23. Documentation

24. Release candidate
```

Dependent phases shall not be generated first.

---

# Chapter 3397 — Stage Completion Rule

After each implementation stage, the coding AI shall:

```text
Run formatting

Run linting

Run type checking

Run relevant unit tests

Run relevant integration tests

Start affected executable

Verify one real workflow

Update documentation

Report unresolved defects
```

It shall not continue as though a failed stage succeeded.

---

# Chapter 3416 — Source-Code Documentation Rule

Public classes and important methods shall include concise docstrings describing:

* Purpose.
* Inputs.
* Outputs.
* Important side effects.
* Authorisation assumptions.
* Transaction behaviour.
* Expected errors.

Docstrings shall not repeat obvious syntax without adding value.

---

# Chapter 3417 — Comment Rule

Comments shall explain:

* Why a non-obvious approach is required.
* Security assumptions.
* Lock ordering.
* Canonicalisation rules.
* Compatibility constraints.
* Migration risks.
* Recovery behaviour.

Comments shall not excuse incomplete code.

---

# Chapter 3418 — Type-Checking Requirement

The project shall use strict or near-strict mypy configuration for important modules.

At minimum:

* Public functions fully typed.
* No unbounded `Any` at service boundaries.
* DTOs typed.
* Repositories typed.
* ViewModel signals and state typed where practical.
* Cryptographic binary fields typed as `bytes`.
* Optional values explicit.

---

# Chapter 3419 — Linting Requirement

Ruff shall enforce:

* Import order.
* Unused imports.
* Undefined names.
* Basic correctness rules.
* Modern Python syntax.
* Security-relevant lint rules where appropriate.
* Complexity review for oversized functions.

Lint suppressions shall be local and justified.

---

# Chapter 3420 — Formatting Requirement

All Python source shall use one formatter configuration.

Formatting shall run automatically in development and verification scripts.

Manually inconsistent formatting shall not remain in committed code.

---

# Chapter 3421 — Test Requirement by Module

Every major production module shall have:

```text
Successful-path test

Validation-failure test

Dependency-failure test

Permission test where applicable

State or concurrency test where applicable

Sensitive-data handling test where applicable
```

A module without meaningful tests is incomplete.

---

# Chapter 3422 — Release-Critical Test Set

The following tests shall block release:

```text
Authentication and refresh-token tests
Permission-boundary tests
Cryptographic vectors
Wrong-recipient tests
Tamper-detection tests
Server plaintext absence
Attachment round trip
Attachment corruption
Offline idempotency
Membership change while offline
Audit append
Audit tamper detection
Final SuperAdministrator protection
Migration from empty state
Client migration preservation
Clean deployment
Backup restore
TLS rejection
```

---

# Chapter 3423 — No Test-Only Security Path

Production code shall not contain hidden paths such as:

```text
Skip authentication when test header present
Disable signature verification in testing
Accept any certificate in test mode through production binary
Use fixed encryption keys in demonstration mode
Grant administrator to all test users through shared production logic
```

Tests shall inject controlled dependencies through configuration and containers.

---

# Chapter 3424 — Test Data Separation

Synthetic test fixtures shall never be loaded automatically into production.

Demonstration seed commands shall:

* Require demonstration environment.
* Display a visible warning.
* Refuse production execution.
* Use fake credentials.
* Avoid predictable secrets in any production context.

---

# Chapter 3425 — Verification After Generation

After generating or modifying code, the coding AI shall perform the applicable checks immediately.

It shall not wait until the entire project is generated to discover:

* Syntax errors.
* Import failures.
* Missing dependencies.
* Invalid migrations.
* Broken tests.
* Circular imports.
* Qt resource errors.
* Configuration mismatches.

---

# Chapter 3426 — Failure Reporting Rule

When verification fails, the coding AI shall report:

```text
Failed command
Relevant safe output
Affected subsystem
Likely cause
Correction applied
Retest result
Remaining uncertainty
```

It shall not claim success if the command was not run or did not pass.

---

# Chapter 3427 — No Fabricated Verification

The coding AI shall never state:

```text
Fully tested
Production ready
Secure
Verified
All tests pass
```

unless the corresponding work was actually performed and evidence exists.

When only static reasoning was possible, it shall state that explicitly.

---

# Chapter 3428 — Partial Implementation Reporting

If the implementation cannot be completed in one output, the coding AI shall:

* Deliver a working completed stage.
* State the exact stage boundary.
* List remaining stages.
* Keep the repository executable.
* Avoid leaving broken imports into future files.
* Avoid presenting unfinished code as complete.

---

# Chapter 3429 — File Creation Sequence

When generating the repository, create files in dependency order.

Recommended sequence:

```text
Configuration-independent shared types

↓

Domain models and protocols

↓

Infrastructure settings

↓

Database models and migrations

↓

Repositories and Unit of Work

↓

Application services

↓

API routes

↓

Client networking and storage

↓

Client services and cryptography

↓

ViewModels and views

↓

Deployment files

↓

Documentation
```

---

# Chapter 3430 — File Completeness Rule

Every generated file shall contain:

* Correct imports.
* Valid syntax.
* Necessary type annotations.
* Real implementation where required.
* Appropriate error handling.
* No unrelated dead code.
* No secret values.
* Tests or corresponding planned test file.

---

# Chapter 3431 — No Duplicate Contract Definitions

Shared DTOs, error codes and protocol enums shall have one authoritative definition.

The coding AI shall not create separate incompatible client and server versions of:

* Message envelope.
* WebSocket event.
* Error response.
* Pagination cursor.
* Algorithm identifier.
* Protocol version.
* Attachment manifest.

---

# Chapter 3432 — Version Source Rule

Application version shall have one authoritative source.

The same version shall appear in:

* Server health.
* Client About page.
* Release package.
* Installer.
* Logs.
* API capability response.
* Documentation.
* Migration compatibility checks where relevant.

---

# Chapter 3433 — Protocol Compatibility Rule

The client shall negotiate protocol compatibility before authentication and protected use.

The server response shall define:

* Current protocol.
* Supported range.
* Minimum client version.
* Feature capabilities.
* Required upgrade state.

Unsupported combinations shall fail clearly.

---

# Chapter 3434 — Database Revision Compatibility Rule

Server startup shall compare:

```text
Expected Alembic revision

against

Database revision
```

Behaviour:

```text
Revision matches:

Continue.

Database behind:

Fail readiness and require migration.

Database ahead:

Fail startup or readiness as incompatible.
```

It shall not guess compatibility.

---

# Chapter 3435 — Client Schema Compatibility Rule

Client local storage shall use explicit migration versions.

Before opening user data:

* Unlock encryption.
* Inspect schema version.
* Apply tested migrations.
* Back up where required.
* Roll back or preserve prior database on failure.
* Never delete unsent work automatically.

---

# Chapter 3436 — Deployment Verification Rule

After installation, verify:

```text
Service user
Directory permissions
Attachment mount
PostgreSQL binding
Redis binding
Uvicorn binding
Nginx configuration
TLS trust
Firewall
Liveness
Readiness
Authentication
Messaging
Audit
Backup status
```

A running process alone is not sufficient.

---

# Chapter 3437 — Upgrade Verification Rule

Every release upgrade shall verify:

```text
Pre-upgrade backup
Package checksum
Configuration compatibility
Migration success
Application version
Database revision
Health
Login
Messaging
Attachments
WebSocket
Audit
Workers
Client compatibility
```

---

# Chapter 3438 — Backup Verification Rule

A successful backup job shall produce:

* Backup artifact.
* Backup manifest.
* Checksums.
* Status record.
* Protected logs.
* Off-host or separate storage copy.
* No error exit status.

Backup completion shall not be inferred from file existence alone.

---

# Chapter 3439 — Restore Verification Rule

A restore shall be considered successful only after:

* Database loads.
* Attachments match metadata.
* Configuration validates.
* Application starts.
* Audit verifies.
* Administrator authenticates.
* Ordinary user authenticates.
* Historical message decrypts on a valid client.
* Attachment decrypts on a valid client.
* Smoke test passes.

---

# Chapter 3440 — Security Invariant Checklist

The final implementation shall preserve all of these invariants:

```text
Server stores no ordinary message plaintext.

Server stores no attachment plaintext.

Server stores no user private identity key.

Every message version uses a fresh content key.

Every AES-GCM operation uses a valid fresh nonce.

Every recipient receives a separate key envelope.

Sender receives a key envelope.

Messages are signed.

Attachments have signed manifests.

Clients verify signatures before display.

GCM failures return no plaintext.

Removed members receive no future keys.

Revoked sessions cannot refresh.

Administrative access does not imply plaintext access.

Secrets do not enter logs or diagnostics.

TLS validation cannot be bypassed in production.

PostgreSQL and Redis are not exposed to ordinary clients.

Audit events are append-only and hash-linked.

Queued writes are idempotent.

Drafts and pending work remain encrypted locally.
```

---

# Chapter 3441 — Database Invariant Checklist

Required database invariants:

```text
Normalised usernames unique.

Direct user pairs unique.

Conversation membership periods valid.

One active recipient envelope per recipient and message.

Message versions increase monotonically.

Attachment chunk indices unique within attachment.

Session token versions increase during rotation.

Audit sequence values unique and continuous under valid writes.

Audit rows cannot be updated or deleted by runtime role.

Configuration versions remain immutable.

Outbox events preserve publication state.

Final active SuperAdministrator cannot be removed through normal service.
```

---

# Chapter 3442 — Client Invariant Checklist

Required client invariants:

```text
One writable process per profile.

Profiles are isolated.

Private keys remain encrypted on disk.

Refresh tokens use secure storage.

Drafts survive restart.

Pending messages survive restart.

Queue payloads remain encrypted.

Server acknowledgements determine stored state.

Search indexes contain token digests rather than plaintext tokens.

Message display occurs only after verification and decryption.

Attachment completion occurs only after checksum verification.

GUI thread remains responsive.

Logout clears active decrypted state.
```

---

# Chapter 3443 — Server Completion Checklist

The server is complete when it provides functional:

```text
Configuration loading
Dependency injection
PostgreSQL
Redis
LDAP authentication
Optional local recovery authentication
Sessions
Token rotation
Users
Roles
Permissions
Contacts
Public keys
Conversations
Groups
Messages
Recipient envelopes
Attachments
WebSockets
Outbox
Audit
Alerts
Announcements
Monitoring
Workers
Administration
Maintenance
Exports
Health
Deployment CLI
Backup status
```

---

# Chapter 3444 — Client Completion Checklist

The client is complete when it provides functional:

```text
Server configuration
TLS validation
Login
Secure token storage
Private-key storage
Conversation list
Direct messaging
Group messaging
Replies
Editing
Deletion
Delivery states
Read states
Attachments
Transfer recovery
Drafts
Offline queue
Synchronisation
Search
Contacts
Groups
Announcements
Settings
Sessions
Diagnostics
Administration pages
Themes
Accessibility
System tray
Notifications
Installer
```

---

# Chapter 3445 — User Workflow Completion Checklist

A normal user shall be able to:

```text
Install client

Open application

Authenticate

Find another user

Start direct conversation

Send encrypted message

Receive message

Reply

Edit own message

Delete own message

Create group

Send group message

Send attachment

Download attachment

Search cached messages

Work temporarily offline

Recover queued work

Manage own sessions

Run diagnostics

Log out
```

---

# Chapter 3446 — Administrator Workflow Completion Checklist

An authorised administrator shall be able to:

```text
Open dashboard

Review component health

Search users

Enable and disable permitted users

Change permitted roles

Review sessions

Revoke sessions

Review active connections

Disconnect connection

Review audit events

Verify audit integrity

Review and resolve alerts

Run permitted workers

Manage announcements

Review configuration

Apply approved configuration changes

Create audit export

Enter maintenance mode

Exit maintenance mode
```

---

# Chapter 3447 — Security Demonstration Checklist

The final demonstration shall show:

```text
Client encrypts message before sending.

Server database contains ciphertext.

Recipient client decrypts successfully.

Wrong user cannot decrypt.

Modified ciphertext fails.

Attachment server storage contains encrypted chunks.

Session revocation disconnects client.

Removed group member receives no later key envelope.

Audit records administrative action.

Audit tampering is detected.

Invalid TLS certificate blocks connection.
```

---

# Chapter 3448 — Reliability Demonstration Checklist

The final demonstration shall show:

```text
Draft survives client restart.

Queued message survives server outage.

Queued message is stored once.

Interrupted upload resumes.

Interrupted download resumes.

Server restart preserves data.

Redis restart does not lose messages.

Expired event cursor triggers resynchronisation.

Backup restores into clean environment.

Upgrade preserves data.
```

---

# Chapter 3449 — Accessibility Completion Checklist

The final interface shall verify:

```text
Keyboard-only login

Keyboard conversation selection

Keyboard message send

Visible focus

Accessible icon names

Readable high-contrast theme

Usable 150% font scale

Non-colour state indicators

Correct dialog focus

Accessible progress and error states
```

---

# Chapter 3450 — Documentation Completion Checklist

Documentation shall accurately explain:

```text
What BlueBubbles does

System architecture

Trust boundaries

Cryptographic design

Key-loss limitations

Metadata visibility

Offline limitations

Installation

Configuration

Active Directory

Client installation

User workflows

Administrator workflows

Backup

Restore

Upgrade

Rollback

Emergency recovery

Testing

Known limitations
```

---

# Chapter 3451 — Required NEA Evidence Package

The final NEA evidence package should contain:

```text
Problem analysis

Stakeholder requirements

Measurable objectives

Research

Alternative solutions

Architecture diagrams

Class diagrams

Database design

Algorithms

Pseudocode

Interface designs

Security design

Development iterations

Testing records

Failed tests and corrections

Performance measurements

User feedback

Final evaluation

Future improvements
```

---

# Chapter 3452 — Required Architecture Diagrams

Final diagrams shall include:

```text
System context diagram

Deployment diagram

Server component diagram

Client component diagram

Authentication flow

Message encryption flow

Message send sequence

Attachment upload flow

Attachment download flow

Offline replay flow

Database entity relationship diagram

Audit-chain flow

Backup and restore flow
```

Diagrams shall match the implementation.

---

# Chapter 3453 — Required Algorithm Evidence

The NEA documentation shall explain algorithms such as:

```text
Recipient-envelope generation

Canonical message serialisation

Message encryption and signing

Message verification and decryption

Attachment chunk encryption

Attachment resume selection

Offline queue replay

Conflict classification

Audit hash-chain append

Audit verification

Message pagination

Local search token generation
```

---

# Chapter 3454 — Required Pseudocode Evidence

Pseudocode shall be included for important operations.

At minimum:

```text
Authenticate user

Refresh session

Send encrypted message

Decrypt received message

Create group

Transfer ownership

Prepare attachment

Upload missing chunks

Process offline queue

Recover event gap

Append audit event

Verify audit chain

Apply configuration update
```

---

# Chapter 3455 — Required Test Evidence

The final report shall include representative evidence from:

```text
Unit testing

Database testing

API testing

Cryptographic testing

Security testing

File-transfer testing

Offline testing

GUI testing

Accessibility testing

Performance testing

Deployment testing

Backup restoration

User acceptance testing
```

---

# Chapter 3456 — Evaluation Rule

The final evaluation shall compare actual results against every success criterion.

For each criterion, state:

```text
Met

Partially met

Not met
```

Then provide:

* Evidence.
* Explanation.
* Limitation.
* Improvement where applicable.

The evaluation shall not overstate the project.

---

# Chapter 3457 — Known Limitation Requirement

The final delivery shall clearly state at least:

```text
LAN-only operation.

Windows client focus.

One primary cryptographic device per user.

No automatic private-key recovery.

No full forward secrecy.

No voice or video calling.

No public federation.

Server can observe routing metadata.

Offline revocation is delayed until reconnection.

Previously decrypted content cannot be remotely erased.

Local search covers only cached authorised messages.

Administrators cannot recover lost end-to-end encryption keys.
```

---

---

## Mandatory sequence and task output — verbatim source

# Chapter 3396 — Mandatory Development Sequence

The coding AI shall generate the project in this order:

```text
1. Repository and tooling

2. Shared contracts

3. Configuration

4. Domain models and errors

5. Database schema and migrations

6. Repository infrastructure

7. Unit of Work

8. Server lifecycle and health

9. Authentication and sessions

10. Users, contacts and public keys

11. Conversations and groups

12. Client cryptographic prototype

13. Encrypted messaging

14. WebSocket and outbox delivery

15. Attachments

16. Local client storage

17. Offline queue and synchronisation

18. PySide6 interface

19. Administration and audit

20. Monitoring and workers

21. Deployment and packaging

22. Full testing

23. Documentation

24. Release candidate
```

Dependent phases shall not be generated first.

---

# Chapter 3397 — Stage Completion Rule

After each implementation stage, the coding AI shall:

```text
Run formatting

Run linting

Run type checking

Run relevant unit tests

Run relevant integration tests

Start affected executable

Verify one real workflow

Update documentation

Report unresolved defects
```

It shall not continue as though a failed stage succeeded.

---

# Chapter 3398 — Initial Repository Output

The first generated output shall include:

```text
pyproject.toml
README development section
Package directories
Test directories
Ruff configuration
mypy configuration
pytest configuration
Version module
Logging skeleton
Application factories
Minimal server entry point
Minimal client entry point
```

The project shall import and start.

---

---

## Task-specific authoritative source: Part 16

# Part 16 — Configuration, Dependency Injection and Application Lifecycle

---

# Chapter 879 — Configuration Subsystem Purpose

The configuration subsystem controls how BlueBubbles behaves across:

* Development.
* Automated testing.
* Demonstration environments.
* Production deployment.
* Client installations.
* Server installations.

It shall provide:

* Validated settings.
* Environment-specific profiles.
* Secure secret loading.
* Safe defaults.
* Feature flags.
* Protocol compatibility rules.
* Dependency construction.
* Predictable application startup.
* Graceful shutdown.
* Clear configuration errors.
* Testable service registration.

Configuration shall be treated as part of the application architecture rather than as scattered constants.

---

# Chapter 880 — Configuration Principles

BlueBubbles configuration shall follow these principles:

```text
Validate settings before startup.

Fail early when required values are missing.

Keep secrets outside source code.

Use safe defaults where possible.

Separate client and server configuration.

Separate environment configuration from user preferences.

Do not allow clients to override server security policy.

Document every setting.

Avoid duplicate configuration sources.

Keep production behaviour explicit.
```

---

# Chapter 881 — Configuration Categories

Server configuration shall include:

```text
Application identity
Environment mode
Network listener
TLS
Database
Redis
Active Directory
Authentication
Tokens
File storage
Message limits
Attachment limits
Rate limiting
Retention
Logging
Monitoring
Background workers
Feature flags
Protocol compatibility
```

Client configuration shall include:

```text
Server endpoint
Connection timeouts
TLS trust
Local storage
Cache limits
Transfer settings
Logging
Application appearance defaults
Feature flags
Protocol compatibility
```

---

# Chapter 882 — Configuration Sources

BlueBubbles may load configuration from:

```text
Built-in safe defaults

↓

Environment-specific configuration file

↓

Environment variables

↓

Protected secret files

↓

Command-line startup overrides
```

Later sources may override earlier sources only where explicitly permitted.

User interface preferences shall be loaded separately after authentication.

---

# Chapter 883 — Configuration Precedence

Recommended precedence:

```text
1. Built-in defaults

2. Base configuration file

3. Environment-specific configuration file

4. Environment variables

5. Secret-file values

6. Explicit command-line overrides
```

Command-line overrides shall not be used for secrets because command-line arguments may be visible to other processes.

---

# Chapter 884 — ServerSettings

```python
class ServerSettings(BaseSettings):
    """Defines and validates all server configuration values."""

    application: ApplicationSettings
    network: NetworkSettings
    tls: TLSSettings
    database: DatabaseSettings
    redis: RedisSettings
    directory: DirectorySettings
    authentication: AuthenticationSettings
    tokens: TokenSettings
    storage: StorageSettings
    messaging: MessagingSettings
    attachments: AttachmentSettings
    rate_limits: RateLimitSettings
    retention: RetentionSettings
    logging: LoggingSettings
    monitoring: MonitoringSettings
    workers: WorkerSettings
    features: FeatureFlagSettings
    protocol: ProtocolSettings
```

Nested settings objects shall keep the configuration understandable.

---

# Chapter 885 — ClientSettings

```python
class ClientSettings(BaseSettings):
    """Defines validated installation-wide client configuration."""

    application: ClientApplicationSettings
    server: ServerConnectionSettings
    tls: ClientTLSSettings
    network: ClientNetworkSettings
    storage: ClientStorageSettings
    transfers: ClientTransferSettings
    logging: ClientLoggingSettings
    features: ClientFeatureFlagSettings
    protocol: ClientProtocolSettings
```

Authenticated user preferences shall not be mixed into this installation-level settings class.

---

# Chapter 886 — UserPreferences

```python
class UserPreferences(BaseModel):
    """Represents user-controlled client preferences."""

    theme: ThemeName
    font_scale: float
    reduced_motion: bool
    notification_settings: NotificationPreferences
    download_directory: Path
    cache_limit_bytes: int
    upload_bandwidth_limit: int | None
    download_bandwidth_limit: int | None
    close_to_tray: bool
    send_with_enter: bool
    show_message_previews: bool
```

User preferences shall be constrained by server policy where required.

---

# Chapter 887 — ApplicationSettings

```python
class ApplicationSettings(BaseModel):
    """Defines general server application behaviour."""

    name: str = "BlueBubbles"
    environment: EnvironmentName
    version: str
    debug: bool = False
    timezone: str = "UTC"
    instance_id: UUID
```

The server shall store timestamps in UTC.

The configured timezone may be used only for administrative display or scheduled local-time operations.

---

# Chapter 888 — Environment Names

```python
class EnvironmentName(StrEnum):
    """Defines recognised application environments."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    DEMONSTRATION = "demonstration"
    PRODUCTION = "production"
```

The application shall reject unknown environment names.

---

# Chapter 889 — Development Profile

Development mode may enable:

```text
Automatic code reload
Verbose structured logging
Local authentication provider
OpenAPI documentation
Test TLS certificates
Seeded development users
Detailed diagnostic responses on localhost
Reduced retention periods
```

Development mode shall still avoid logging passwords, tokens and plaintext messages.

---

# Chapter 890 — Testing Profile

Testing mode shall use:

```text
Isolated PostgreSQL database
Isolated Redis namespace
Temporary filesystem storage
Mock or local authentication provider
Predictable clock where needed
Disabled external directory dependency
Fast worker intervals
Deterministic test feature flags
```

Testing shall never use production data or credentials.

---

# Chapter 891 — Demonstration Profile

Demonstration mode may provide:

```text
Pre-created sample accounts
Sample conversations
Sample encrypted attachments
Simplified local authentication
Resettable data
Visible feature walkthroughs
```

The interface shall clearly identify that it is a demonstration environment.

Demonstration credentials shall never work in production.

---

# Chapter 892 — Production Profile

Production mode shall require:

```text
TLS enabled
Strong token-signing secret
Non-default database credentials
Protected Redis access
Validated storage path
Production authentication provider
Debug mode disabled
Restricted API documentation
Secure logging
Safe retention settings
No seeded test users
No mock providers
```

The server shall refuse to start if dangerous production values are detected.

---

# Chapter 893 — Production Safety Validation

Examples of startup failures:

```text
Default token secret detected

Debug enabled in production

Mock authentication provider enabled

Database using default password

Storage directory is world-writable

TLS disabled without an explicit approved exception

Test administrator account present

Temporary development certificate configured
```

The validation error shall explain exactly which setting must be corrected.

---

# Chapter 894 — NetworkSettings

```python
class NetworkSettings(BaseModel):
    """Defines the server listening interface and request limits."""

    host: str
    port: int
    trusted_proxy_count: int = 0
    request_timeout_seconds: int
    maximum_request_body_bytes: int
    websocket_auth_timeout_seconds: int
    websocket_heartbeat_seconds: int
    websocket_missed_heartbeat_limit: int
```

Recommended production listener:

```text
127.0.0.1 behind a reverse proxy

or

A private LAN address
```

The server shall not bind publicly unless explicitly configured.

---

# Chapter 895 — ServerConnectionSettings

```python
class ServerConnectionSettings(BaseModel):
    """Defines how the desktop client connects to the server."""

    base_url: AnyHttpUrl
    websocket_url: AnyUrl
    connect_timeout_seconds: float
    request_timeout_seconds: float
    retry_limit: int
    automatic_reconnect: bool
```

The client shall reject unsupported URL schemes.

Production connections shall use:

```text
https://
wss://
```

---

# Chapter 896 — TLSSettings

```python
class TLSSettings(BaseModel):
    """Defines server TLS certificate configuration."""

    enabled: bool
    certificate_path: Path | None
    private_key_path: Path | None
    certificate_chain_path: Path | None
    minimum_tls_version: str = "1.2"
```

TLS private-key files shall use restrictive filesystem permissions.

---

# Chapter 897 — ClientTLSSettings

```python
class ClientTLSSettings(BaseModel):
    """Defines client certificate verification behaviour."""

    verify_certificates: bool = True
    trusted_ca_path: Path | None
    expected_hostname: str | None
    allow_certificate_pinning: bool = True
    pinned_certificate_fingerprint: str | None
```

Production clients shall not expose a simple “ignore certificate errors” button.

---

# Chapter 898 — Certificate Trust

The client may trust:

```text
An organisation-managed certificate authority

or

A pinned server certificate fingerprint
```

A self-signed certificate may be acceptable for development.

Production deployment should distribute a trusted internal CA certificate to client devices.

---

# Chapter 899 — Certificate Pinning

Certificate pinning may compare:

```text
SHA-256 fingerprint of the server certificate
```

If the fingerprint changes unexpectedly:

```text
Stop connection

↓

Display security warning

↓

Require administrator-approved configuration update
```

The client shall not silently trust the new certificate.

---

# Chapter 900 — DatabaseSettings

```python
class DatabaseSettings(BaseModel):
    """Defines PostgreSQL connectivity and pooling."""

    url: SecretStr
    pool_size: int
    maximum_overflow: int
    connection_timeout_seconds: int
    statement_timeout_seconds: int
    pool_recycle_seconds: int
    echo_sql: bool = False
```

`echo_sql` shall be disabled in production because SQL logs may expose metadata.

---

# Chapter 901 — Database URL Security

The database URL may contain credentials.

Therefore, it shall:

* Use a secret-aware type.
* Be redacted from logs.
* Never be returned through API responses.
* Never appear in exception messages shown to users.
* Be loaded from environment or protected secret storage.

---

# Chapter 902 — RedisSettings

```python
class RedisSettings(BaseModel):
    """Defines Redis connectivity and namespace behaviour."""

    url: SecretStr
    namespace: str = "bluebubbles"
    connection_timeout_seconds: int
    operation_timeout_seconds: int
    maximum_connections: int
    fallback_enabled: bool
```

Testing environments shall use a unique namespace to prevent key collisions.

---

# Chapter 903 — DirectorySettings

```python
class DirectorySettings(BaseModel):
    """Defines LDAP or Active Directory integration."""

    provider: DirectoryProviderName
    server: str | None
    port: int | None
    use_tls: bool
    bind_dn: str | None
    bind_password: SecretStr | None
    base_dn: str | None
    user_search_base: str | None
    group_search_base: str | None
    username_attribute: str
    guid_attribute: str
    email_attribute: str
    department_attribute: str
    job_title_attribute: str
    connection_timeout_seconds: int
    search_timeout_seconds: int
```

Provider-specific fields shall become required only when that provider is active.

---

# Chapter 904 — AuthenticationSettings

```python
class AuthenticationSettings(BaseModel):
    """Defines authentication and account-management behaviour."""

    provider: AuthenticationProviderName
    allow_local_accounts: bool
    failed_login_limit: int
    failed_login_window_seconds: int
    application_lockout_seconds: int
    directory_sync_interval_seconds: int
    default_role: RoleName
    one_primary_crypto_device: bool
```

Production validation shall reject mock authentication.

---

# Chapter 905 — TokenSettings

```python
class TokenSettings(BaseModel):
    """Defines session token signing and lifetime rules."""

    signing_algorithm: str
    signing_secret: SecretStr
    issuer: str
    audience: str
    access_token_lifetime_seconds: int
    refresh_token_lifetime_seconds: int
    rotation_enabled: bool
    reuse_detection_enabled: bool
```

Recommended defaults:

```text
Access token:

900 seconds

Refresh token:

604800 seconds
```

---

# Chapter 906 — Token Secret Validation

The token secret shall:

* Contain at least 32 random bytes.
* Not equal a documented example value.
* Not be reused from a database password.
* Not be committed to Git.
* Be different between development and production.
* Support planned rotation.

The application shall not automatically generate a new production secret on every startup because that would invalidate all tokens unexpectedly.

---

# Chapter 907 — StorageSettings

```python
class StorageSettings(BaseModel):
    """Defines server-side encrypted attachment storage."""

    root_path: Path
    temporary_path: Path
    export_path: Path
    reserved_free_bytes: int
    reserved_free_percentage: float
    create_missing_directories: bool
    allow_network_filesystem: bool
```

Startup shall verify read and write access.

---

# Chapter 908 — Path Validation

Configured paths shall be:

* Absolute.
* Normalised.
* Inside approved storage roots.
* Writable by the service account where required.
* Not world-writable.
* Located on a filesystem with sufficient free capacity.
* Distinct where separation is required.

The server shall reject paths containing unresolved parent references.

---

# Chapter 909 — MessagingSettings

```python
class MessagingSettings(BaseModel):
    """Defines message limits and conversation behaviour."""

    client_plaintext_character_limit: int
    maximum_encrypted_request_bytes: int
    default_page_size: int
    maximum_page_size: int
    edit_window_seconds: int
    direct_conversation_unique: bool
    read_receipts_enabled: bool
    typing_indicators_enabled: bool
    maximum_group_members: int
```

The plaintext character limit is communicated to clients.

The server still enforces the encrypted request limit.

---

# Chapter 910 — AttachmentSettings

```python
class AttachmentSettings(BaseModel):
    """Defines encrypted attachment transfer limits."""

    maximum_plaintext_size_bytes: int
    default_chunk_size_bytes: int
    minimum_chunk_size_bytes: int
    maximum_chunk_size_bytes: int
    upload_session_lifetime_seconds: int
    orphan_lifetime_seconds: int
    maximum_concurrent_uploads_per_user: int
    blocked_extensions: set[str]
    thumbnail_maximum_bytes: int
```

Chunk-size relationships shall be validated.

---

# Chapter 911 — RateLimitSettings

```python
class RateLimitSettings(BaseModel):
    """Defines request thresholds for protected endpoint categories."""

    login_requests_per_window: int
    login_window_seconds: int
    message_requests_per_minute: int
    search_requests_per_minute: int
    administration_requests_per_minute: int
    upload_chunk_requests_per_minute: int
    websocket_events_per_minute: int
```

Rate limits shall remain configurable rather than hard-coded.

---

# Chapter 912 — RetentionSettings

```python
class RetentionSettings(BaseModel):
    """Defines lifecycle periods for stored records."""

    expired_session_days: int
    temporary_upload_hours: int
    orphan_attachment_hours: int
    deleted_message_days: int
    deleted_attachment_days: int
    operational_log_days: int
    audit_event_days: int | None
    export_file_hours: int
```

`audit_event_days = None` may represent indefinite retention where policy permits.

---

# Chapter 913 — Retention Relationship Validation

The settings validator shall check relationships.

Examples:

```text
Export expiry must be positive.

Temporary upload expiry must be shorter than orphan retention.

Deleted attachment retention must not be negative.

Audit retention must not violate configured minimum policy.

Refresh-token lifetime must not exceed maximum session lifetime where one exists.
```

Invalid relationships shall stop startup or reject administrative changes.

---

# Chapter 914 — LoggingSettings

```python
class LoggingSettings(BaseModel):
    """Defines structured logging and file rotation."""

    level: LogLevel
    directory: Path
    json_format: bool
    console_enabled: bool
    maximum_file_bytes: int
    retained_files: int
    compress_rotated_files: bool
    redact_sensitive_values: bool = True
```

Sensitive-value redaction shall not be configurable to `False` in production.

---

# Chapter 915 — MonitoringSettings

```python
class MonitoringSettings(BaseModel):
    """Defines health checks, metrics and alert thresholds."""

    health_check_interval_seconds: int
    metrics_collection_interval_seconds: int
    storage_warning_percentage: float
    storage_critical_percentage: float
    database_latency_warning_ms: float
    redis_latency_warning_ms: float
    repeated_failure_alert_threshold: int
```

Thresholds shall be validated as sensible percentages and durations.

---

# Chapter 916 — WorkerSettings

```python
class WorkerSettings(BaseModel):
    """Defines recurring background worker schedules."""

    session_cleanup_interval_seconds: int
    attachment_cleanup_interval_seconds: int
    audit_recent_check_interval_seconds: int
    audit_full_check_interval_seconds: int
    directory_sync_interval_seconds: int
    statistics_interval_seconds: int
```

Worker intervals shall not be so short that they overload the server.

---

# Chapter 917 — ClientStorageSettings

```python
class ClientStorageSettings(BaseModel):
    """Defines installation-wide local storage defaults."""

    profile_root: Path
    default_cache_limit_bytes: int
    maximum_cache_limit_bytes: int
    thumbnail_cache_limit_bytes: int
    encrypted_message_cache_limit_bytes: int
    local_database_backend: str
    retain_cache_after_logout: bool
```

Server policy may impose stricter cache rules.

---

# Chapter 918 — ClientTransferSettings

```python
class ClientTransferSettings(BaseModel):
    """Defines local transfer behaviour."""

    default_download_directory: Path
    upload_concurrency: int
    download_concurrency: int
    chunk_concurrency: int
    automatic_image_download_limit_bytes: int
    default_upload_limit_bytes_per_second: int | None
    default_download_limit_bytes_per_second: int | None
```

The client shall check destination write access before starting downloads.

---

# Chapter 919 — Configuration Files

Recommended server configuration structure:

```text
config/
├── base.yaml
├── development.yaml
├── testing.yaml
├── demonstration.yaml
└── production.yaml
```

Secret values shall not appear in these files unless the files are separately protected and excluded from source control.

---

# Chapter 920 — Example Base Configuration

```yaml
application:
  name: BlueBubbles
  timezone: UTC

network:
  host: 127.0.0.1
  port: 8443
  request_timeout_seconds: 30
  websocket_heartbeat_seconds: 30
  websocket_missed_heartbeat_limit: 3

messaging:
  client_plaintext_character_limit: 8000
  default_page_size: 50
  maximum_page_size: 100
  edit_window_seconds: 900
  maximum_group_members: 100

attachments:
  default_chunk_size_bytes: 1048576
  maximum_plaintext_size_bytes: 2147483648
```

The example shall contain no real credentials.

---

# Chapter 921 — Environment Variables

Suggested environment variables:

```text
BLUEBUBBLES_ENVIRONMENT
BLUEBUBBLES_DATABASE_URL
BLUEBUBBLES_REDIS_URL
BLUEBUBBLES_TOKEN_SECRET
BLUEBUBBLES_STORAGE_ROOT
BLUEBUBBLES_TLS_CERTIFICATE
BLUEBUBBLES_TLS_PRIVATE_KEY
BLUEBUBBLES_LDAP_SERVER
BLUEBUBBLES_LDAP_BIND_DN
BLUEBUBBLES_LDAP_BIND_PASSWORD
BLUEBUBBLES_LDAP_BASE_DN
```

Nested values may use a documented delimiter.

Example:

```text
BLUEBUBBLES_NETWORK__PORT
```

---

# Chapter 922 — Secret Files

For larger secret values, the application may support file-based loading.

Example:

```text
BLUEBUBBLES_TOKEN_SECRET_FILE
BLUEBUBBLES_LDAP_BIND_PASSWORD_FILE
```

The loader shall:

* Read the file once.
* Trim only documented trailing newline characters.
* Validate file permissions.
* Never log the contents.
* Reject empty secret files.
* Avoid retaining unnecessary duplicate copies.

---

# Chapter 923 — SecretStr and Redaction

Pydantic secret-aware fields shall be used.

Example:

```python
class DatabaseSettings(BaseModel):
    url: SecretStr
```

Printing the settings object shall show a redacted value rather than the secret.

Custom logs and exception handlers must preserve this redaction.

---

# Chapter 924 — Configuration Loader

```python
class ConfigurationLoader:
    """Loads, merges and validates application configuration."""

    def load_server_settings(
        self,
        environment: EnvironmentName,
    ) -> ServerSettings:
        ...

    def load_client_settings(self) -> ClientSettings:
        ...

    def load_yaml_file(
        self,
        path: Path,
    ) -> dict[str, Any]:
        ...

    def load_environment_values(self) -> dict[str, Any]:
        ...

    def load_secret_files(self) -> dict[str, Any]:
        ...
```

The loader shall be deterministic and testable.

---

# Chapter 925 — Configuration Merge Rules

Configuration dictionaries shall merge by documented nested key.

Rules:

```text
Scalar value:

Later source replaces earlier value.

Mapping:

Merge recognised nested keys.

List:

Replace entire list unless setting explicitly supports extension.

Unknown key:

Reject.

Type mismatch:

Reject.
```

Silently ignoring unknown keys shall not be allowed because it can hide spelling mistakes.

---

# Chapter 926 — Configuration Validation Errors

A validation error shall include:

```text
Setting path
Invalid value category
Expected format
Source file or environment variable
Safe corrective guidance
```

It shall not include secret values.

Example:

```text
Configuration error: attachments.default_chunk_size_bytes

The value must be between 262144 and 8388608 bytes.

Source: production.yaml
```

---

# Chapter 927 — Configuration Report

At startup, the server may log a safe configuration summary.

Example:

```text
Environment: production
Database configured: yes
Redis configured: yes
Authentication provider: LDAP
TLS enabled: yes
Attachment root: configured
Message limit: 8000 characters
Maximum group members: 100
```

Secrets and full paths may be redacted where appropriate.

---

# Chapter 928 — Feature Flags

Feature flags allow incomplete or optional features to be controlled safely.

Initial flags may include:

```text
message_editing
read_receipts
typing_indicators
attachment_uploads
image_thumbnails
local_search
announcements
administration_dashboard
audit_exports
multi_device_sessions
```

Feature flags shall not disable mandatory security checks.

---

# Chapter 929 — FeatureFlagSettings

```python
class FeatureFlagSettings(BaseModel):
    """Defines server-controlled optional feature availability."""

    message_editing: bool = True
    read_receipts: bool = True
    typing_indicators: bool = True
    attachment_uploads: bool = True
    image_thumbnails: bool = True
    local_search: bool = True
    announcements: bool = True
    audit_exports: bool = True
    multi_device_sessions: bool = False
```

Version 1.0 shall keep complex multi-device cryptographic support disabled unless implemented fully.

---

# Chapter 930 — Feature Flag Authority

The server is authoritative for shared application features.

The client may contain a feature flag only to:

* Hide unsupported local interface components.
* Control experimental development behaviour.
* Match server-advertised capabilities.

A client-side flag shall never unlock a feature disabled by the server.

---

# Chapter 931 — Feature Capability Response

After login, the server shall return an effective capability document.

```python
class ServerCapabilities(BaseModel):
    """Describes features and limits supported by the active server."""

    server_version: str
    protocol_versions: list[int]
    features: dict[str, bool]
    limits: ClientVisibleLimits
    policies: ClientVisiblePolicies
```

The client shall use this instead of assuming all features are available.

---

# Chapter 932 — Client-Visible Limits

```python
class ClientVisibleLimits(BaseModel):
    """Provides server-enforced values required by the client interface."""

    message_character_limit: int
    maximum_attachment_bytes: int
    maximum_group_members: int
    accepted_chunk_size_range: tuple[int, int]
    default_page_size: int
```

These limits shall be refreshed after policy updates.

---

# Chapter 933 — Client-Visible Policies

```python
class ClientVisiblePolicies(BaseModel):
    """Provides server-enforced behaviour required by clients."""

    read_receipts_enabled: bool
    decrypted_cache_allowed: bool
    blocked_file_extensions: list[str]
    group_history_policy: str
    one_primary_crypto_device: bool
    session_management_enabled: bool
```

Sensitive server configuration shall not be included.

---

# Chapter 934 — ProtocolSettings

```python
class ProtocolSettings(BaseModel):
    """Defines supported application protocol versions."""

    current_version: int
    minimum_supported_version: int
    supported_versions: list[int]
    deprecated_versions: list[int]
    minimum_client_version: str
```

The supported versions list shall be internally consistent.

---

# Chapter 935 — Protocol Negotiation

Connection flow:

```text
Client submits:

Client version
Supported protocol versions

↓

Server compares versions

↓

Select highest mutually supported version

↓

Return selected protocol version

↓

Client uses selected version
```

If there is no compatible version, the connection shall be rejected clearly.

---

# Chapter 936 — Protocol Negotiation DTO

```python
class ProtocolNegotiationRequest(BaseModel):
    """Describes the client’s supported protocol capabilities."""

    client_version: str
    supported_protocol_versions: list[int]
    platform: str
```

Response:

```python
class ProtocolNegotiationResponse(BaseModel):
    """Returns the protocol version selected by the server."""

    selected_protocol_version: int
    server_version: str
    minimum_client_version: str
    update_required: bool
```

---

# Chapter 937 — Unsupported Client Behaviour

If the client is too old:

```text
Reject authentication or restricted operations

↓

Return minimum required version

↓

Display clear update instruction
```

Because BlueBubbles is LAN-only, update guidance may point to an internal network share or administrator.

---

# Chapter 938 — Semantic Versioning

Application versions shall follow:

```text
MAJOR.MINOR.PATCH
```

Meaning:

```text
MAJOR:

Breaking application or protocol changes

MINOR:

Backwards-compatible features

PATCH:

Backwards-compatible bug and security fixes
```

Pre-release versions may use:

```text
1.0.0-alpha.1
1.0.0-beta.1
```

---

# Chapter 939 — Build Information

The application may expose safe build information:

```text
Application version
Build identifier
Commit identifier where appropriate
Protocol version
Build timestamp
```

Production responses shall not expose unnecessary repository details.

---

# Chapter 940 — Dependency Injection Purpose

Dependency injection shall ensure that classes receive the services they depend upon.

Benefits:

* Easier testing.
* Clear ownership.
* Fewer global variables.
* Replaceable infrastructure.
* Mockable dependencies.
* Predictable startup.
* Controlled shutdown.

Business services shall not create infrastructure dependencies internally.

---

# Chapter 941 — ServerContainer

```python
class ServerContainer:
    """Builds and owns server-side dependencies."""

    settings: ServerSettings

    database_manager: DatabaseManager
    redis_manager: RedisManager
    file_storage: FileStorage

    repositories: ServerRepositories
    services: ServerServices
    websocket_manager: WebSocketConnectionManager
    worker_manager: WorkerManager
```

The container shall be constructed during startup.

---

# Chapter 942 — ClientContainer

```python
class ClientContainer:
    """Builds and owns client-side dependencies."""

    settings: ClientSettings

    secure_store: SecureStore
    local_database: LocalDatabaseManager
    api_client: ApiClient
    websocket_client: WebSocketClient

    repositories: ClientRepositories
    services: ClientServices
    viewmodels: ViewModelFactory
```

Views shall receive ViewModels from a factory or container.

---

# Chapter 943 — Container Construction Order

Server dependency order:

```text
Validated settings

↓

Logging

↓

Database manager

↓

Redis manager

↓

Storage implementation

↓

Repositories

↓

Low-level infrastructure services

↓

Business services

↓

WebSocket manager

↓

Workers

↓

API dependency providers
```

A dependency shall not be constructed before its own requirements are ready.

---

# Chapter 944 — Service Lifetimes

Dependencies shall use defined lifetimes.

```text
Application singleton:

Configuration
Database engine
Redis pool
File storage
WebSocket manager
Worker manager

Request scoped:

Database session
Unit of Work
Authentication context

Operation scoped:

Upload transaction
Audit export job
Search operation
```

Long-lived services shall not retain request-scoped database sessions.

---

# Chapter 945 — Repository Container

```python
class ServerRepositories:
    """Groups server repository factories."""

    users: UserRepository
    sessions: SessionRepository
    conversations: ConversationRepository
    messages: MessageRepository
    attachments: AttachmentRepository
    audit: AuditRepository
    announcements: AnnouncementRepository
```

Grouping improves discoverability but shall not become an unrestricted service locator inside business code.

---

# Chapter 946 — Service Container

```python
class ServerServices:
    """Groups constructed server application services."""

    authentication: AuthenticationService
    sessions: SessionService
    users: UserService
    permissions: PermissionService
    conversations: ConversationService
    messaging: MessagingService
    groups: GroupService
    attachments: AttachmentService
    audit: AuditService
    announcements: AnnouncementService
    monitoring: MonitoringService
```

Services shall still receive explicit constructor dependencies.

---

# Chapter 947 — Avoiding the Service-Locator Pattern

Business classes shall not receive the entire container.

Incorrect:

```python
class MessagingService:
    def __init__(self, container: ServerContainer):
        self.container = container
```

Preferred:

```python
class MessagingService:
    def __init__(
        self,
        message_repository: MessageRepository,
        conversation_repository: ConversationRepository,
        permission_service: PermissionService,
        audit_service: AuditService,
        event_publisher: EventPublisher,
    ):
        ...
```

Explicit dependencies make tests and architecture clearer.

---

# Chapter 948 — FastAPI Dependency Providers

FastAPI dependency functions shall retrieve constructed services safely.

Example:

```python
def get_messaging_service(
    request: Request,
) -> MessagingService:
    """Return the application messaging service."""

    return request.app.state.container.services.messaging
```

Request-scoped database dependencies shall still create and close their own sessions.

---

# Chapter 949 — Request-Scoped Unit of Work

```python
async def get_unit_of_work(
    request: Request,
) -> AsyncIterator[UnitOfWork]:
    """Provide one transaction context for a request."""

    factory = request.app.state.container.unit_of_work_factory

    async with factory() as unit_of_work:
        yield unit_of_work
```

Commit behaviour shall remain controlled by the service or Unit of Work pattern.

---

# Chapter 950 — ViewModelFactory

```python
class ViewModelFactory:
    """Creates client ViewModels with explicit service dependencies."""

    def create_login_viewmodel(self) -> LoginViewModel:
        ...

    def create_main_viewmodel(self) -> MainViewModel:
        ...

    def create_chat_viewmodel(
        self,
        conversation_id: UUID,
    ) -> ChatViewModel:
        ...

    def create_settings_viewmodel(self) -> SettingsViewModel:
        ...
```

Views shall not construct their own networking or storage services.

---

# Chapter 951 — Server Application Factory

```python
def create_application(
    settings: ServerSettings | None = None,
) -> FastAPI:
    """Create a fully configured FastAPI server application."""
```

The function shall:

* Load settings when none are supplied.
* Validate environment safety.
* Configure logging.
* Create the FastAPI object.
* Register middleware.
* Register exception handlers.
* Register routers.
* Register lifespan management.
* Avoid opening infrastructure connections before the lifespan begins.

---

# Chapter 952 — FastAPI Lifespan

The server shall use FastAPI lifespan management.

```python
@asynccontextmanager
async def application_lifespan(
    app: FastAPI,
) -> AsyncIterator[None]:
    """Start and stop application infrastructure safely."""

    container = await build_server_container(settings)
    app.state.container = container

    await container.start()

    try:
        yield
    finally:
        await container.stop()
```

This is preferred over scattered startup and shutdown handlers.

---

# Chapter 953 — Server Startup Phases

Server startup shall use defined phases.

```text
Phase 1:

Load and validate configuration

Phase 2:

Configure logging

Phase 3:

Create infrastructure objects

Phase 4:

Connect to PostgreSQL

Phase 5:

Verify migration state

Phase 6:

Connect to Redis

Phase 7:

Verify storage

Phase 8:

Construct repositories and services

Phase 9:

Start WebSocket and event systems

Phase 10:

Start background workers

Phase 11:

Mark application ready
```

---

# Chapter 954 — Startup Readiness

The server shall not report itself ready before critical dependencies pass validation.

Critical dependencies:

```text
PostgreSQL
Attachment storage
Token-signing configuration
Authentication configuration
Audit writer
```

Redis may permit degraded operation if fallback behaviour is implemented.

---

# Chapter 955 — Readiness and Liveness

Two health concepts shall be distinguished.

```text
Liveness:

The process is running.

Readiness:

The process can serve normal application traffic.
```

Endpoints:

```http
GET /health/live

GET /health/ready
```

A live but unready server shall not accept ordinary traffic through a load balancer or reverse proxy.

---

# Chapter 956 — Startup Failure Behaviour

If startup fails:

* Log the failure category.
* Redact sensitive values.
* Stop already-started components.
* Close connections.
* Return a non-zero process exit code.
* Avoid entering a partially operational state.
* Display concise console guidance for administrators.

---

# Chapter 957 — Startup Rollback

If startup reaches Redis and then storage validation fails:

```text
Stop Redis manager

↓

Close database pool

↓

Flush logs

↓

Exit
```

Every component started during startup shall have a matching cleanup operation.

---

# Chapter 958 — ServerContainer Lifecycle

```python
class ServerContainer:
    """Owns server components and their lifecycle."""

    async def start(self) -> None:
        ...

    async def stop(self) -> None:
        ...
```

`start()` shall be idempotent or explicitly reject repeated calls.

`stop()` shall tolerate partially started components.

---

# Chapter 959 — Graceful Server Shutdown

Shutdown phases:

```text
Mark server not ready

↓

Stop accepting new long-running tasks

↓

Stop scheduling workers

↓

Allow active database transactions to finish

↓

Cancel or preserve resumable transfer operations

↓

Notify connected WebSocket clients

↓

Close WebSocket connections

↓

Stop workers

↓

Close Redis pool

↓

Close database pool

↓

Flush structured logs

↓

Exit
```

---

# Chapter 960 — Shutdown Timeout

The service manager shall allow a configurable graceful shutdown period.

Recommended:

```text
30 seconds
```

After the timeout, remaining operations may be cancelled safely.

Completed database commits must not be rolled back merely because WebSocket notification did not finish.

---

# Chapter 961 — WebSocket Shutdown Event

Before closing, the server may send:

```json
{
    "event_type": "server_shutdown",
    "data": {
        "reason": "maintenance",
        "reconnect_after_seconds": 30
    }
}
```

Clients shall treat this as advisory.

They shall still handle abrupt connection loss.

---

# Chapter 962 — Client Application Lifecycle

Client lifecycle:

```text
Create QApplication

↓

Load installation settings

↓

Configure logging

↓

Initialise secure store

↓

Create unauthenticated client container

↓

Display login interface

↓

Authenticate

↓

Open user-specific storage

↓

Load keys and cache

↓

Create authenticated services

↓

Display main window

↓

Connect WebSocket

↓

Synchronise data

↓

Run until logout or exit
```

---

# Chapter 963 — ClientApplication

```python
class ClientApplication:
    """Coordinates the complete desktop application lifecycle."""

    def __init__(
        self,
        settings: ClientSettings,
    ):
        ...

    async def initialise(self) -> None:
        ...

    async def authenticate(
        self,
        credentials: LoginCredentials,
    ) -> AuthenticatedSession:
        ...

    async def open_main_window(self) -> None:
        ...

    async def logout(self) -> None:
        ...

    async def shutdown(self) -> None:
        ...
```

---

# Chapter 964 — Unauthenticated Client Container

Before login, only limited dependencies are required.

```text
Client settings
Logging
Secure store
API client
Protocol negotiation
Authentication service
Login ViewModel
```

User-specific database, message services and private keys shall not be opened for the wrong user.

---

# Chapter 965 — Authenticated Client Container

After login, the client shall construct or activate:

```text
User-specific local database
Key manager
Encryption services
Conversation service
Messaging service
File transfer service
Search service
Offline queue
Notification service
WebSocket client
Main ViewModels
```

Logout shall dispose of these user-specific components.

---

# Chapter 966 — Client Logout Lifecycle

```text
Stop outgoing queue processing

↓

Save drafts

↓

Pause or cancel transfers according to policy

↓

Close WebSocket

↓

Call server logout

↓

Close user database

↓

Clear in-memory keys

↓

Delete tokens

↓

Dispose authenticated services

↓

Return to login window
```

The installation-level application process may remain open.

---

# Chapter 967 — Client Exit Lifecycle

```text
Prevent new user actions

↓

Save window state

↓

Save drafts

↓

Persist resumable transfer state

↓

Close WebSocket

↓

Stop workers

↓

Close local database

↓

Clear in-memory secrets

↓

Flush logs

↓

Exit QApplication
```

A forced operating-system shutdown may skip some steps, so recovery mechanisms remain necessary.

---

# Chapter 968 — Signal Handling

The server shall handle:

```text
SIGTERM
SIGINT
```

These signals shall initiate graceful shutdown.

The client shall handle:

```text
Window close
System logout
System shutdown
Application exit command
```

Qt system events shall be used where available.

---

# Chapter 969 — Component Start Order

Components shall declare their dependencies.

Example:

```text
AuditService depends on:

AuditRepository
AuditWriter

MessagingService depends on:

MessageRepository
ConversationRepository
PermissionService
AuditService
EventPublisher
```

The container shall construct components in topological dependency order.

Circular dependencies shall be treated as architecture errors.

---

# Chapter 970 — Circular Dependency Avoidance

If two services appear to depend on one another, introduce:

* A smaller interface.
* An event.
* A coordinator service.
* A repository abstraction.
* A domain operation boundary.

Example:

`MessagingService` should publish an event rather than directly call `NotificationService` if that would create a cycle.

---

# Chapter 971 — Event-Driven Decoupling

Internal application events may include:

```text
UserAuthenticated
MessageStored
AttachmentCompleted
GroupMemberRemoved
SessionRevoked
SecurityAlertCreated
ConfigurationUpdated
```

Handlers may perform secondary actions such as:

* Publish WebSocket notifications.
* Update metrics.
* Invalidate caches.
* Create notifications.

The core transaction shall remain clear.

---

# Chapter 972 — Internal Event Bus

```python
class InternalEventBus:
    """Dispatches application events to registered handlers."""

    async def publish(
        self,
        event: ApplicationEvent,
    ) -> None:
        ...

    def subscribe(
        self,
        event_type: type[ApplicationEvent],
        handler: EventHandler,
    ) -> None:
        ...
```

Version 1.0 may implement an in-process event bus.

Permanent events requiring guaranteed delivery shall use an outbox pattern or database-backed recovery.

---

# Chapter 973 — Transactional Outbox

A transactional outbox prevents loss between database commit and event publication.

Workflow:

```text
Begin database transaction

↓

Write business record

↓

Write outbox event

↓

Commit transaction

↓

Background publisher reads outbox

↓

Publish event

↓

Mark outbox event delivered
```

This is particularly useful for:

* Message delivery.
* Group membership events.
* Session revocation events.
* Announcements.

---

# Chapter 974 — Version 1.0 Outbox Decision

For maximum reliability, BlueBubbles should implement a basic outbox for durable events.

Required durable events:

```text
MESSAGE_STORED
GROUP_MEMBER_ADDED
GROUP_MEMBER_REMOVED
SESSION_REVOKED
ANNOUNCEMENT_PUBLISHED
```

Transient events such as typing indicators do not require the outbox.

---

# Chapter 975 — OutboxEvent Model

```python
class OutboxEvent(BaseEntity):
    """Stores a durable application event awaiting publication."""

    event_type: str
    aggregate_type: str
    aggregate_id: UUID
    payload: dict[str, Any]
    created_at: datetime
    published_at: datetime | None
    attempt_count: int
    next_attempt_at: datetime | None
    last_error: str | None
```

Payloads shall not contain plaintext message bodies.

---

# Chapter 976 — Outbox Worker

```python
class OutboxPublisherWorker(BackgroundWorker):
    """Publishes committed application events reliably."""

    async def run_once(self) -> None:
        ...
```

The worker shall:

* Load unpublished events.
* Publish them.
* Mark successful events.
* Retry temporary failures.
* Avoid duplicate client effects through event IDs.
* Alert after repeated failures.

---

# Chapter 977 — Configuration Reload

Not every setting may be changed without restart.

Settings may be classified as:

```text
Static:

Database URL
Redis URL
TLS private key path
Storage root
Authentication provider

Reloadable:

Message limit
File-size limit
Rate limits
Retention values
Feature flags
Logging level
Worker intervals
```

The classification shall be documented.

---

# Chapter 978 — Configuration Reload Workflow

```text
Administrator submits change

↓

Validate new configuration

↓

Write configuration version

↓

Apply reloadable values

↓

Invalidate relevant caches

↓

Notify affected workers

↓

Publish policy-update event

↓

Audit change
```

If a static setting changes, the server shall indicate that restart is required.

---

# Chapter 979 — Atomic Configuration Updates

A configuration update shall either:

```text
Apply completely

or

Apply nothing
```

The server shall validate the full resulting configuration before storing it.

Partial settings updates shall merge into a candidate configuration and then validate the complete model.

---

# Chapter 980 — Configuration Versioning

Every application-managed configuration revision shall include:

```text
Version number
Changed values
Previous values where safe
Changed by
Change reason
Timestamp
Restart required
```

Secret values shall not be included in change history.

---

# Chapter 981 — Client Policy Updates

When server policy changes, connected clients may receive:

```text
POLICY_UPDATED
```

The client shall:

```text
Request latest capability document

↓

Recalculate effective settings

↓

Update interface limits

↓

Stop newly prohibited actions

↓

Inform user where necessary
```

Existing completed data shall not be silently deleted unless policy explicitly requires it.

---

# Chapter 982 — Dependency Health

The container shall expose component health.

Examples:

```text
Database manager started
Redis manager degraded
File storage writable
Audit writer operational
Outbox worker running
WebSocket manager accepting connections
```

Readiness shall use these component states.

---

# Chapter 983 — Dependency Failure at Runtime

If a dependency fails after startup:

```text
Detect failure

↓

Update health state

↓

Attempt bounded reconnection where appropriate

↓

Disable affected capability

↓

Log incident

↓

Create alert if threshold reached

↓

Recover automatically when safe
```

The application shall not repeatedly reconnect without delay.

---

# Chapter 984 — Database Runtime Failure

When PostgreSQL becomes unavailable:

* New permanent writes shall fail safely.
* Existing database transactions shall roll back.
* Server readiness shall become unhealthy.
* WebSocket connections may remain temporarily open.
* Clients shall receive retryable errors.
* The server shall not claim messages were stored.
* Reconnection shall use bounded backoff.

---

# Chapter 985 — Redis Runtime Failure

When Redis becomes unavailable:

* Presence may become unknown.
* Typing indicators may stop.
* Distributed rate limiting may degrade.
* Durable PostgreSQL writes may continue.
* Health shall become degraded.
* Redis reconnection shall occur automatically.
* Permanent message data shall not be lost.

---

# Chapter 986 — Storage Runtime Failure

When attachment storage becomes unavailable:

* New uploads shall be rejected.
* Downloads shall return a storage-unavailable error.
* Text messaging may continue.
* Health shall become degraded or unhealthy.
* Administrators shall receive an alert.
* Existing attachment database records shall not be deleted automatically.

---

# Chapter 987 — Configuration Documentation

Every setting shall document:

```text
Setting name
Purpose
Type
Default
Allowed range
Required environment
Security implications
Whether restart is required
Whether it is exposed to clients
```

Documentation may be generated from settings metadata where practical.

---

# Chapter 988 — Example Settings Metadata

```python
message_character_limit: int = Field(
    default=8000,
    ge=1,
    le=50000,
    description="Maximum plaintext characters accepted by supported clients.",
)
```

Validation metadata shall support both runtime checking and documentation.

---

# Chapter 989 — Command-Line Interface

The server command-line interface may support:

```text
bluebubbles-server run
bluebubbles-server validate-config
bluebubbles-server show-config
bluebubbles-server migrate
bluebubbles-server create-admin
bluebubbles-server verify-audit
bluebubbles-server check-storage
```

`show-config` shall redact secrets.

---

# Chapter 990 — Validate Configuration Command

Example:

```text
bluebubbles-server validate-config --environment production
```

The command shall:

* Load all configuration sources.
* Validate relationships.
* Perform production safety checks.
* Verify referenced paths.
* Avoid starting the full server.
* Return a non-zero exit code on failure.

---

# Chapter 991 — Diagnostic Startup Mode

A diagnostic command may verify:

```text
Configuration
PostgreSQL connectivity
Redis connectivity
LDAP connectivity
Storage access
TLS files
Audit permissions
```

Example:

```text
bluebubbles-server diagnose
```

This supports deployment troubleshooting.

---

# Chapter 992 — Configuration Unit Tests

Tests shall include:

```text
Load built-in defaults
Load base YAML
Load environment-specific YAML
Override with environment variable
Load secret file
Reject unknown setting
Reject invalid type
Reject invalid port
Reject unsafe production secret
Reject mock provider in production
Validate chunk-size relationships
Validate retention relationships
Redact secrets in output
Resolve client-visible limits
```

---

# Chapter 993 — Dependency Injection Tests

Tests shall include:

```text
Construct server container
Construct client container
Replace repository with mock
Replace authentication provider with mock
Create ViewModel with test services
Verify explicit dependencies
Reject circular construction
Use request-scoped Unit of Work
Close partially started container
Avoid duplicate singleton construction
```

---

# Chapter 994 — Lifecycle Unit Tests

Tests shall include:

```text
Successful server startup
Database startup failure
Redis degraded startup
Storage startup failure
Migration mismatch
Worker startup failure
Startup rollback
Graceful shutdown
Repeated shutdown call
Partial-start shutdown
Client login lifecycle
Client logout lifecycle
Client exit lifecycle
Draft save during shutdown
Transfer-state persistence during exit
```

---

# Chapter 995 — Protocol Tests

Tests shall include:

```text
Negotiate highest shared version
Reject no shared version
Reject client below minimum version
Accept supported previous version
Return client-visible capabilities
Update feature flag
Apply server policy update
Ignore unknown future optional field safely
Reject incompatible required field
```

---

# Chapter 996 — Configuration Security Tests

Security tests shall include:

```text
Secret values absent from logs
Secret values absent from API
Command-line output redacts secrets
Unknown production defaults rejected
TLS key permissions checked
Storage path traversal rejected
World-writable storage rejected
Client cannot enable server-disabled feature
Client cannot override file-size limit
Environment variable injection cannot create unknown settings
Configuration export excludes credentials
```

---

# Chapter 997 — Lifecycle Integration Tests

Integration tests shall include:

```text
Start full test server
Authenticate client
Open WebSocket
Send message
Perform graceful server restart
Reconnect client
Recover missed durable event
Preserve queued message
Reload feature flag
Update message limit
Apply policy update to client
Stop server during upload
Resume upload after restart
```

---

# Chapter 998 — Startup Performance Targets

Suggested targets in the test environment:

```text
Server configuration loading:

Under 200 ms

Server dependency construction:

Under 1 second

Server ready with healthy dependencies:

Under 5 seconds

Client installation configuration loading:

Under 100 ms

Client cached shell after login:

Under 1 second
```

External services such as LDAP may increase total login time.

---

# Chapter 999 — Simplified Version 1.0 Configuration Scope

Version 1.0 shall implement:

```text
Pydantic server settings
Pydantic client settings
YAML configuration files
Environment-variable overrides
Secret-aware fields
Development, testing and production profiles
Production safety validation
Server and client dependency containers
FastAPI lifespan startup
Graceful shutdown
Fixed feature flags
Protocol negotiation
Client-visible limits and policies
Basic transactional outbox
Configuration validation command
```

The following may be deferred:

```text
Live TLS certificate replacement
Automatic secret rotation
Distributed configuration service
Remote configuration editor
Plugin dependency loading
Complex feature rollout percentages
Per-department feature flags
Dynamic database replacement
```

---

# Chapter 1000 — Configuration and Lifecycle Summary

BlueBubbles shall use structured, validated configuration for both the server and client.

Configuration shall:

* Use safe defaults.
* Separate environments.
* Keep secrets outside source code.
* Reject unknown keys.
* Validate relationships.
* Fail early when unsafe.
* Expose only necessary limits and policies to clients.

Dependency injection shall:

* Use explicit constructor dependencies.
* Avoid global service access.
* Support mocks and tests.
* Define component lifetimes.
* Separate application-wide and request-scoped objects.

The server shall:

* Use a FastAPI application factory.
* Use lifespan-based startup and shutdown.
* Validate critical dependencies before readiness.
* Roll back partial startup safely.
* Shut down connections and workers gracefully.
* Preserve durable events through a basic transactional outbox.

The client shall:

* Separate unauthenticated and authenticated dependencies.
* Open user-specific storage only after authentication.
* Save drafts and transfer state during shutdown.
* Clear in-memory secrets during logout.
* Rebuild services cleanly for a new session.

Feature flags shall control optional functionality but shall never bypass security.

Protocol negotiation shall ensure that clients and servers agree on a supported communication format.

Production mode shall reject development providers, default secrets and unsafe configuration.

---

# End of Part 16

Part 17 will define the complete error-handling, structured logging, diagnostics and recovery subsystem, including:

* Application exception hierarchies.
* Stable API error responses.
* Client-facing error messages.
* Correlation identifiers.
* Retry classification.
* Circuit breakers.
* Service degradation.
* Crash reporting without external services.
* Diagnostic packages.
* Recovery workflows.
* Logging sanitisation.
* Error-handling tests.

---

## Task-specific authoritative source: Part 21

# Part 21 — Source-Code Structure and Per-File Implementation Contract

---

# Chapter 1585 — Source-Code Structure Purpose

This section defines the final BlueBubbles repository layout and the responsibilities of each major source file.

The purpose is to ensure that the coding AI:

* Places code in predictable locations.
* Avoids duplicate classes.
* Keeps client and server code separate.
* Keeps shared contracts independent.
* Uses clear dependency directions.
* Avoids circular imports.
* Separates business logic from infrastructure.
* Creates testable modules.
* Does not place unrelated logic inside large files.
* Implements every required subsystem consistently.

The generated code shall follow this structure unless a small, clearly justified change is required.

---

# Chapter 1586 — Repository Root Layout

The complete repository shall use the following high-level structure:

```text
bluebubbles/
├── README.md
├── LICENSE
├── pyproject.toml
├── requirements/
├── config/
├── docs/
├── scripts/
├── deployment/
├── migrations/
├── src/
├── tests/
├── resources/
├── build/
└── .github/
```

Each directory shall have one defined purpose.

---

# Chapter 1587 — Root Files

Required root files:

```text
README.md
LICENSE
pyproject.toml
.gitignore
.env.example
CHANGELOG.md
SECURITY.md
CONTRIBUTING.md
```

Purpose:

`README.md`

Provides project overview, installation summary and development commands.

`LICENSE`

States the selected software licence.

`pyproject.toml`

Defines Python project metadata, dependencies and tool configuration.

`.gitignore`

Excludes secrets, caches, databases, build output and virtual environments.

`.env.example`

Documents environment-variable names using placeholders only.

`CHANGELOG.md`

Records user-visible changes by version.

`SECURITY.md`

Explains how security issues should be reported and handled.

---

# Chapter 1588 — Python Package Root

All production Python code shall be placed under:

```text
src/bluebubbles/
```

This prevents accidental imports from the repository root and supports reliable packaging.

The package root shall contain:

```text
src/bluebubbles/
├── __init__.py
├── version.py
├── shared/
├── server/
└── client/
```

---

# Chapter 1589 — Package Dependency Direction

The dependency direction shall be:

```text
shared
↑
server
↑
server API infrastructure
```

and:

```text
shared
↑
client
↑
client UI infrastructure
```

The following shall not occur:

```text
shared importing server
shared importing client
server importing client
client importing server implementation
```

The client and server may share DTO definitions and protocol constants through `shared`.

---

# Chapter 1590 — Shared Package Purpose

The `shared` package shall contain code that is genuinely common to both client and server.

It may contain:

* Protocol enums.
* API DTOs.
* WebSocket event DTOs.
* Stable error codes.
* Shared validation constants.
* Version information.
* Canonical serialisation.
* Cryptographic envelope structures.
* Common type aliases.

It shall not contain:

* Database repositories.
* PySide6 views.
* FastAPI routers.
* Server storage code.
* Client local-database code.
* Environment-specific secrets.

---

# Chapter 1591 — Shared Package Layout

```text
src/bluebubbles/shared/
├── __init__.py
├── constants.py
├── types.py
├── versioning.py
├── validation.py
├── errors/
├── models/
├── protocol/
├── security/
└── utilities/
```

---

# Chapter 1592 — shared/constants.py

Purpose:

Stores stable non-secret constants used by both applications.

Examples:

```text
Application name
Default protocol identifier
Maximum UUID string length
Supported timestamp format
Common content-type values
```

It shall not contain:

```text
Passwords
Database URLs
Token secrets
Deployment-specific paths
Environment-specific limits
```

Configurable values shall remain in settings models.

---

# Chapter 1593 — shared/types.py

Purpose:

Defines common type aliases and lightweight value types.

Possible contents:

```python
UserId = UUID
ConversationId = UUID
MessageId = UUID
AttachmentId = UUID
SessionId = UUID
CorrelationId = UUID
```

Distinct wrapper types may be used where they improve safety.

This file shall remain small and dependency-free.

---

# Chapter 1594 — shared/versioning.py

Required classes and functions:

```text
SemanticVersion
ProtocolVersion
parse_version()
compare_versions()
select_highest_common_protocol()
is_client_supported()
```

Responsibilities:

* Parse application versions.
* Validate protocol versions.
* Select compatible protocol versions.
* Reject malformed version strings.
* Avoid deployment-specific update logic.

---

# Chapter 1595 — shared/validation.py

Purpose:

Provides shared validation helpers for DTOs.

Possible functions:

```text
validate_uuid_list()
normalise_display_text()
validate_base64_length()
validate_protocol_version()
validate_safe_display_filename()
validate_message_type()
```

Security-sensitive server authority checks shall not be placed here.

For example, conversation membership validation belongs on the server.

---

# Chapter 1596 — Shared Error Package

Layout:

```text
shared/errors/
├── __init__.py
├── codes.py
├── models.py
└── mappings.py
```

---

# Chapter 1597 — shared/errors/codes.py

Required content:

```python
class ErrorCode(StrEnum):
    ...
```

This file shall contain the central public error-code catalogue.

No duplicate error-code enum shall exist elsewhere.

Domain modules may group constants, but all public codes shall resolve to this catalogue.

---

# Chapter 1598 — shared/errors/models.py

Required DTOs:

```text
ApiErrorResponse
ApiErrorDetail
FieldError
WebSocketErrorEventData
```

These models shall contain only client-safe information.

Technical exception objects shall never be serialised into these DTOs.

---

# Chapter 1599 — shared/errors/mappings.py

Purpose:

Defines stable metadata for public errors.

Possible mapping fields:

```text
Default message
HTTP status
Retry classification
Severity
Help code
```

Server exception handlers and client message catalogues may use this mapping.

The client may override display wording without changing semantics.

---

# Chapter 1600 — Shared Models Package

Layout:

```text
shared/models/
├── __init__.py
├── users.py
├── sessions.py
├── contacts.py
├── conversations.py
├── messages.py
├── attachments.py
├── announcements.py
├── administration.py
├── health.py
└── pagination.py
```

These files shall contain API-facing Pydantic models rather than ORM classes.

---

# Chapter 1601 — shared/models/users.py

Required models may include:

```text
UserSummary
UserProfileResponse
UpdateUserProfileRequest
UserSearchRequest
UserSearchResponse
PublicUserKeyResponse
```

This file shall not contain password hashes or server-only directory credentials.

---

# Chapter 1602 — shared/models/sessions.py

Required models:

```text
LoginRequest
LoginResponse
RefreshTokenRequest
RefreshTokenResponse
LogoutResponse
SessionSummary
SessionListResponse
RevokeSessionRequest
```

Sensitive fields shall use secret-aware representations where appropriate.

---

# Chapter 1603 — shared/models/contacts.py

Required models:

```text
ContactSummary
ContactListResponse
AddContactRequest
UpdateContactRequest
BlockContactRequest
```

The server derives the authenticated owner from the session.

The request shall not allow a client to act as another user.

---

# Chapter 1604 — shared/models/conversations.py

Required models:

```text
ConversationType
ConversationSummaryResponse
ConversationResponse
CreateDirectConversationRequest
CreateGroupConversationRequest
ConversationParticipantResponse
GroupRole
UpdateGroupRequest
AddGroupMemberRequest
ChangeGroupRoleRequest
TransferOwnershipRequest
```

The file shall contain validation limits shared with the client where appropriate.

---

# Chapter 1605 — shared/models/messages.py

Required models:

```text
MessageType
MessageDeliveryStatus
RecipientKeyEnvelopeRequest
EncryptedMessageResponse
SendMessageRequest
SendMessageResponse
EditMessageRequest
DeletedMessageResponse
MessagePageResponse
MarkConversationReadRequest
```

This file shall not implement encryption.

It only defines the transmitted structures.

---

# Chapter 1606 — shared/models/attachments.py

Required models:

```text
AttachmentStatus
InitialiseUploadRequest
InitialiseUploadResponse
UploadChunkResponse
UploadStatusResponse
AttachmentResponse
AuthorisedAttachmentResponse
AttachmentRecipientKeyRequest
AttachmentRecipientKeyResponse
```

Large binary chunk bodies shall not be embedded directly in Pydantic JSON models unless required by a small metadata endpoint.

---

# Chapter 1607 — shared/models/announcements.py

Required models:

```text
AnnouncementPriority
AnnouncementTargetType
CreateAnnouncementRequest
AnnouncementResponse
AnnouncementAcknowledgementRequest
AnnouncementListResponse
```

Announcement content shall use safe plain-text validation.

---

# Chapter 1608 — shared/models/administration.py

Required models:

```text
AdminDashboardResponse
AdminUserSummary
AuditEventResponse
AuditPageResponse
SecurityAlertResponse
ConfigurationSummary
WorkerStatusResponse
DataExportJobResponse
```

Role-specific filtering shall occur before these models are populated.

---

# Chapter 1609 — shared/models/health.py

Required models:

```text
HealthState
ComponentHealth
PublicHealthResponse
DetailedHealthResponse
CapabilityState
ServerCapabilities
ClientVisibleLimits
ClientVisiblePolicies
```

Public and administrative health responses shall remain separate.

---

# Chapter 1610 — shared/models/pagination.py

Required models:

```text
CursorPage
CursorPageMetadata
PageRequest
OpaqueCursor
```

Cursor generation and signing may remain server-side.

The shared model shall treat cursor strings as opaque.

---

# Chapter 1611 — Shared Protocol Package

Layout:

```text
shared/protocol/
├── __init__.py
├── envelope.py
├── events.py
├── event_types.py
├── negotiation.py
└── serialisation.py
```

---

# Chapter 1612 — shared/protocol/envelope.py

Required models:

```text
WebSocketEventEnvelope
WebSocketAcknowledgement
ProtocolMetadata
```

Fields:

```text
event_id
event_type
protocol_version
timestamp
correlation_id
data
```

Envelope parsing shall validate required fields but not perform business authorisation.

---

# Chapter 1613 — shared/protocol/event_types.py

Required enum:

```python
class WebSocketEventType(StrEnum):
    ...
```

Values shall include:

```text
AUTHENTICATE
AUTHENTICATED
HEARTBEAT
MESSAGE_RECEIVED
MESSAGE_UPDATED
MESSAGE_DELETED
MESSAGE_DELIVERED
MESSAGE_READ
TYPING_CHANGED
PRESENCE_CHANGED
GROUP_MEMBER_ADDED
GROUP_MEMBER_REMOVED
SESSION_REVOKED
ANNOUNCEMENT_PUBLISHED
POLICY_UPDATED
SERVER_SHUTDOWN
ERROR
```

No duplicate string literals shall be scattered through handlers.

---

# Chapter 1614 — shared/protocol/events.py

Required event-data models:

```text
AuthenticationEventData
HeartbeatEventData
MessageReceivedEventData
MessageUpdatedEventData
MessageDeletedEventData
TypingEventData
PresenceEventData
GroupMembershipEventData
SessionRevokedEventData
PolicyUpdatedEventData
ServerShutdownEventData
```

Each event type shall have a matching validated data model.

---

# Chapter 1615 — shared/protocol/negotiation.py

Required DTOs and functions:

```text
ProtocolNegotiationRequest
ProtocolNegotiationResponse
negotiate_protocol()
```

The server remains authoritative for the selected version.

---

# Chapter 1616 — shared/protocol/serialisation.py

Purpose:

Provides deterministic serialisation for:

* Signed message envelopes.
* Attachment metadata envelopes.
* Audit event content where shared implementation is justified.
* Protocol event signatures where added.

Required functions:

```text
canonical_json_bytes()
canonical_timestamp()
canonical_uuid()
```

Canonical serialisation shall have comprehensive tests.

---

# Chapter 1617 — Shared Security Package

Layout:

```text
shared/security/
├── __init__.py
├── algorithms.py
├── key_models.py
├── message_envelope.py
├── attachment_envelope.py
└── fingerprints.py
```

The shared package may define structures and algorithm identifiers.

Client-only private-key operations shall remain in the client package.

---

# Chapter 1618 — shared/security/algorithms.py

Required enums:

```text
ContentEncryptionAlgorithm
KeyEnvelopeAlgorithm
SignatureAlgorithm
HashAlgorithm
```

Algorithm identifiers shall be explicit and versioned.

Unsupported algorithms shall be rejected rather than guessed.

---

# Chapter 1619 — shared/security/key_models.py

Required models:

```text
PublicKeyDescriptor
RecipientKeyEnvelope
KeyFingerprint
KeyVersion
```

No private-key object shall appear in API-facing response models.

---

# Chapter 1620 — shared/security/message_envelope.py

Required structures:

```text
EncryptedMessageEnvelope
SignedMessageFields
MessageRecipientEnvelope
```

Responsibilities:

* Represent encrypted message data.
* Produce canonical signing fields.
* Validate envelope completeness.
* Avoid performing server membership checks.

---

# Chapter 1621 — shared/security/attachment_envelope.py

Required structures:

```text
EncryptedAttachmentMetadata
AttachmentChunkMetadata
AttachmentRecipientEnvelope
AttachmentManifestData
```

The server may read structural metadata but shall not receive plaintext file contents or plaintext content keys.

---

# Chapter 1622 — shared/security/fingerprints.py

Required functions:

```text
calculate_public_key_fingerprint()
format_fingerprint()
validate_fingerprint()
```

The fingerprint representation shall be consistent across client, server and interface displays.

---

# Chapter 1623 — Server Package Layout

```text
src/bluebubbles/server/
├── __init__.py
├── main.py
├── application.py
├── bootstrap.py
├── container.py
├── dependencies.py
├── configuration/
├── domain/
├── database/
├── repositories/
├── services/
├── api/
├── authentication/
├── websocket/
├── storage/
├── workers/
├── monitoring/
├── logging/
└── utilities/
```

---

# Chapter 1624 — server/main.py

Purpose:

Provides the server application entry point.

Required content:

```text
create_application import
optional command-line start function
version logging
```

It shall not contain:

* Business logic.
* Database queries.
* Router implementations.
* Secret values.
* Dependency construction details.

Example:

```python
from bluebubbles.server.application import create_application

app = create_application()
```

Where factory deployment is used, the exact export shall match the Uvicorn command.

---

# Chapter 1625 — server/application.py

Required function:

```python
def create_application(
    settings: ServerSettings | None = None,
) -> FastAPI:
    ...
```

Responsibilities:

* Create FastAPI object.
* Register lifespan.
* Register middleware.
* Register exception handlers.
* Register routers.
* Configure OpenAPI behaviour.
* Store no business logic.

---

# Chapter 1626 — server/bootstrap.py

Purpose:

Coordinates infrastructure startup.

Required functions:

```text
build_server_container()
validate_startup_dependencies()
verify_migration_state()
verify_storage_paths()
run_startup_checks()
```

It shall return a fully constructed `ServerContainer`.

---

# Chapter 1627 — server/container.py

Required classes:

```text
ServerContainer
ServerRepositories
ServerServices
```

Responsibilities:

* Own application-wide dependencies.
* Start and stop infrastructure.
* Construct services explicitly.
* Avoid acting as a general business service locator.
* Support test replacement of dependencies.

---

# Chapter 1628 — server/dependencies.py

Purpose:

Contains FastAPI dependency provider functions.

Required functions may include:

```text
get_current_user()
get_current_session()
get_unit_of_work()
get_authentication_service()
get_messaging_service()
get_conversation_service()
get_attachment_service()
get_admin_service()
require_permission()
```

No route shall manually construct a service.

---

# Chapter 1629 — Server Configuration Package

Layout:

```text
server/configuration/
├── __init__.py
├── settings.py
├── loader.py
├── validation.py
└── environment.py
```

---

# Chapter 1630 — server/configuration/settings.py

Required settings classes:

```text
ServerSettings
ApplicationSettings
NetworkSettings
TLSSettings
DatabaseSettings
RedisSettings
DirectorySettings
AuthenticationSettings
TokenSettings
StorageSettings
MessagingSettings
AttachmentSettings
RateLimitSettings
RetentionSettings
LoggingSettings
MonitoringSettings
WorkerSettings
FeatureFlagSettings
ProtocolSettings
```

This file may be divided into multiple files if it becomes excessively large.

---

# Chapter 1631 — server/configuration/loader.py

Required class:

```text
ConfigurationLoader
```

Responsibilities:

* Load YAML.
* Read environment variables.
* Read secret files.
* Apply precedence.
* Validate unknown keys.
* Produce `ServerSettings`.
* Avoid printing secrets.

---

# Chapter 1632 — server/configuration/validation.py

Required functions:

```text
validate_production_safety()
validate_path_permissions()
validate_tls_files()
validate_setting_relationships()
validate_no_test_defaults()
```

This module shall raise typed `ConfigurationError` exceptions.

---

# Chapter 1633 — Server Domain Package

Layout:

```text
server/domain/
├── __init__.py
├── users.py
├── sessions.py
├── contacts.py
├── conversations.py
├── messages.py
├── attachments.py
├── audit.py
├── alerts.py
├── announcements.py
├── configuration.py
├── outbox.py
└── common.py
```

These are server-side domain entities and rules, not SQLAlchemy ORM models.

---

# Chapter 1634 — server/domain/common.py

Possible contents:

```text
BaseEntity
VersionedEntity
SoftDeletableEntity
DomainEvent
DomainValidationResult
```

This file shall not become a dumping ground for unrelated helpers.

---

# Chapter 1635 — server/domain/users.py

Required entities:

```text
User
Role
Permission
LocalCredential
PublicKeyRecord
```

Possible rule functions:

```text
can_assign_role()
can_disable_target()
normalise_username()
```

Database access shall not occur here.

---

# Chapter 1636 — server/domain/sessions.py

Required entities:

```text
Session
LoginAttempt
AuthenticatedUser
```

Required behaviour:

```text
is_expired()
is_active()
invalidate()
can_refresh()
```

Token encoding shall remain in authentication infrastructure.

---

# Chapter 1637 — server/domain/conversations.py

Required entities:

```text
Conversation
ConversationMember
ConversationEvent
DirectConversationPair
```

Required rules:

```text
is_active_member()
can_add_member()
can_remove_member()
can_transfer_ownership()
validate_group_owner_transition()
```

---

# Chapter 1638 — server/domain/messages.py

Required entities:

```text
Message
MessageRecipientKey
MessageDelivery
MessageVersion
```

Required rules:

```text
can_edit()
can_delete()
validate_version()
validate_delivery_transition()
```

Message plaintext shall never be part of the server domain entity.

---

# Chapter 1639 — server/domain/attachments.py

Required entities:

```text
Attachment
AttachmentChunk
AttachmentRecipientKey
UploadSession
```

Required rules:

```text
can_accept_chunk()
is_complete()
can_be_linked()
is_expired()
```

No file I/O shall occur in the domain model.

---

# Chapter 1640 — server/domain/audit.py

Required entities:

```text
AuditEvent
AuditChainState
AuditVerificationResult
```

Required functions:

```text
build_canonical_audit_data()
calculate_audit_hash()
verify_audit_link()
```

---

# Chapter 1641 — Server Database Package

Layout:

```text
server/database/
├── __init__.py
├── base.py
├── engine.py
├── session.py
├── unit_of_work.py
├── migrations.py
└── models/
```

---

# Chapter 1642 — server/database/base.py

Required content:

```text
SQLAlchemy DeclarativeBase
shared column helpers
naming convention metadata
```

A naming convention shall support deterministic migration names.

---

# Chapter 1643 — server/database/engine.py

Required class:

```text
DatabaseManager
```

Responsibilities:

* Create async SQLAlchemy engine.
* Configure connection pool.
* Test connectivity.
* Dispose engine.
* Expose health state.
* Avoid retaining request sessions.

---

# Chapter 1644 — server/database/session.py

Required content:

```text
async_sessionmaker
session factory creation
database session context helper
```

Sessions shall roll back safely after exceptions.

---

# Chapter 1645 — server/database/unit_of_work.py

Required classes:

```text
UnitOfWork
UnitOfWorkFactory
```

Responsibilities:

* Create one async session.
* Construct repositories sharing that session.
* Commit.
* Roll back.
* Close.
* Support async context management.

---

# Chapter 1646 — server/database/migrations.py

Required functions:

```text
get_current_revision()
get_expected_revision()
verify_revision()
```

The running application shall not perform unsafe automatic production migrations.

---

# Chapter 1647 — ORM Models Layout

```text
server/database/models/
├── __init__.py
├── identity.py
├── sessions.py
├── contacts.py
├── keys.py
├── conversations.py
├── messages.py
├── attachments.py
├── announcements.py
├── audit.py
├── administration.py
├── configuration.py
└── outbox.py
```

Files may contain closely related table models.

---

# Chapter 1648 — database/models/identity.py

Required ORM models:

```text
RoleORM
PermissionORM
RolePermissionORM
UserORM
LocalCredentialORM
```

Only persistence mapping belongs here.

Business methods shall remain minimal.

---

# Chapter 1649 — database/models/sessions.py

Required ORM models:

```text
SessionORM
LoginAttemptORM
PolicyAcknowledgementORM
```

Refresh-token hashes shall use binary storage.

---

# Chapter 1650 — database/models/conversations.py

Required ORM models:

```text
ConversationORM
DirectConversationPairORM
ConversationMemberORM
ConversationEventORM
```

Relationships shall avoid eager loading complete message collections.

---

# Chapter 1651 — database/models/messages.py

Required ORM models:

```text
MessageORM
MessageRecipientKeyORM
MessageDeliveryORM
MessageVersionORM where implemented
```

Encrypted binary fields shall use `LargeBinary` or appropriate PostgreSQL `BYTEA` mapping.

---

# Chapter 1652 — database/models/attachments.py

Required ORM models:

```text
AttachmentORM
AttachmentRecipientKeyORM
AttachmentChunkORM
UploadSessionORM
UploadSessionChunkORM where implemented
```

Physical file bytes shall not be stored in these ORM models.

---

# Chapter 1653 — database/models/audit.py

Required ORM models:

```text
AuditEventORM
AuditChainStateORM
SecurityAlertORM
```

The ORM shall not expose ordinary update or delete repository methods for audit events.

---

# Chapter 1654 — database/models/administration.py

Required ORM models:

```text
AnnouncementORM
AnnouncementAcknowledgementORM
DataExportJobORM
DataDeletionRequestORM
WorkerExecutionRecordORM
```

---

# Chapter 1655 — database/models/configuration.py

Required ORM models:

```text
ConfigurationVersionORM
```

Secret configuration values shall not be stored.

---

# Chapter 1656 — database/models/outbox.py

Required ORM model:

```text
OutboxEventORM
```

The model shall include retry, lock and publication fields.

---

# Chapter 1657 — Server Repository Package

Layout:

```text
server/repositories/
├── __init__.py
├── interfaces/
├── sqlalchemy/
└── mapping/
```

Using interfaces and implementations shall make services testable.

---

# Chapter 1658 — Repository Interfaces Layout

```text
repositories/interfaces/
├── users.py
├── sessions.py
├── contacts.py
├── keys.py
├── conversations.py
├── messages.py
├── attachments.py
├── audit.py
├── announcements.py
├── administration.py
├── configuration.py
└── outbox.py
```

Each file shall define an abstract interface or protocol.

---

# Chapter 1659 — SQLAlchemy Repository Layout

```text
repositories/sqlalchemy/
├── users.py
├── sessions.py
├── contacts.py
├── keys.py
├── conversations.py
├── messages.py
├── attachments.py
├── audit.py
├── announcements.py
├── administration.py
├── configuration.py
└── outbox.py
```

Each implementation shall receive an async SQLAlchemy session.

---

# Chapter 1660 — Repository Mapping Package

Layout:

```text
repositories/mapping/
├── users.py
├── sessions.py
├── conversations.py
├── messages.py
├── attachments.py
└── audit.py
```

Purpose:

Converts between ORM and domain models.

Mapping functions shall not perform database queries.

---

# Chapter 1661 — UserRepository Contract

Required methods:

```text
get_by_id()
get_by_normalised_username()
get_by_directory_guid()
search()
create()
update_profile()
set_enabled()
set_role()
soft_delete()
```

The interface shall define return types and not expose SQLAlchemy query objects.

---

# Chapter 1662 — SessionRepository Contract

Required methods:

```text
create()
get_by_id()
get_active_by_id()
list_active_for_user()
update_last_seen()
rotate_refresh_token()
invalidate()
invalidate_all_for_user()
list_expired()
delete_expired()
```

Raw refresh tokens shall never be returned.

---

# Chapter 1663 — ConversationRepository Contract

Required methods:

```text
get_by_id()
find_direct_pair()
create_direct()
create_group()
list_for_user()
get_active_members()
get_membership()
add_member()
remove_member()
change_member_role()
update_last_activity()
```

Membership queries shall support row locking where required.

---

# Chapter 1664 — MessageRepository Contract

Required methods:

```text
create()
get_by_id()
get_for_user()
list_for_conversation()
insert_recipient_keys()
get_recipient_key()
update_encrypted_payload()
soft_delete()
create_delivery_rows()
update_delivery_state()
```

The repository shall not decide whether the requester has permission.

---

# Chapter 1665 — AttachmentRepository Contract

Required methods:

```text
create_pending()
get_by_id()
get_for_user()
add_chunk()
list_chunks()
add_recipient_keys()
get_recipient_key()
mark_complete()
link_to_message()
mark_deleted()
list_expired_orphans()
```

---

# Chapter 1666 — AuditRepository Contract

Required methods:

```text
append()
get_latest_chain_state()
list_events()
get_by_sequence()
verify_range_data()
```

It shall not expose:

```text
update_event()
delete_event()
```

---

# Chapter 1667 — OutboxRepository Contract

Required methods:

```text
add()
claim_batch()
mark_published()
mark_failed()
release_expired_locks()
list_repeated_failures()
delete_old_published()
```

Claiming shall support safe concurrent workers.

---

# Chapter 1668 — Server Services Package

Layout:

```text
server/services/
├── __init__.py
├── authentication.py
├── sessions.py
├── users.py
├── contacts.py
├── keys.py
├── permissions.py
├── conversations.py
├── groups.py
├── messaging.py
├── attachments.py
├── presence.py
├── notifications.py
├── announcements.py
├── audit.py
├── administration.py
├── monitoring.py
├── configuration.py
├── diagnostics.py
└── exports.py
```

Each file shall focus on one application domain.

---

# Chapter 1669 — services/authentication.py

Required class:

```text
AuthenticationService
```

Responsibilities:

* Normalise username.
* Enforce login-attempt policy.
* Call authentication provider.
* Synchronise user.
* Check account state.
* Create session.
* Issue tokens.
* Record audit event.

It shall not implement LDAP protocol details directly.

---

# Chapter 1670 — services/sessions.py

Required class:

```text
SessionService
```

Responsibilities:

* Create sessions.
* Validate sessions.
* Refresh tokens.
* Rotate refresh tokens.
* Detect reuse.
* Invalidate sessions.
* Revoke all user sessions.
* Coordinate WebSocket disconnection.

---

# Chapter 1671 — services/users.py

Required class:

```text
UserService
```

Responsibilities:

* Retrieve user profile.
* Search users.
* Update permitted profile fields.
* Synchronise directory fields.
* Enable and disable accounts.
* Coordinate account lifecycle.

---

# Chapter 1672 — services/contacts.py

Required class:

```text
ContactService
```

Responsibilities:

* List contacts.
* Add or remove contact.
* Favourite.
* Block.
* Unblock.
* Calculate contact weighting.

---

# Chapter 1673 — services/keys.py

Required class:

```text
PublicKeyService
```

Responsibilities:

* Register public keys.
* Retrieve active keys.
* Validate key versions.
* Rotate keys.
* Revoke keys.
* Publish key-change events.
* Prevent private-key submission.

---

# Chapter 1674 — services/permissions.py

Required class:

```text
PermissionService
```

Responsibilities:

* Resolve user role.
* Resolve permission set.
* Require application permission.
* Check resource-level access.
* Compare group roles.
* Invalidate permission cache.

No route shall manually reproduce permission logic.

---

# Chapter 1675 — services/conversations.py

Required class:

```text
ConversationService
```

Responsibilities:

* Create direct conversations.
* Create groups.
* List conversations.
* Retrieve conversation.
* Archive, pin and mute per user.
* Validate conversation access.

---

# Chapter 1676 — services/groups.py

Required class:

```text
GroupService
```

Responsibilities:

* Add member.
* Remove member.
* Leave group.
* Promote and demote.
* Transfer ownership.
* Rename group.
* Soft-delete group.

Group hierarchy rules shall be centralised here.

---

# Chapter 1677 — services/messaging.py

Required class:

```text
MessagingService
```

Responsibilities:

* Validate message envelopes.
* Validate membership.
* Validate recipient-key coverage.
* Store message transactionally.
* Retrieve paginated messages.
* Edit.
* Delete.
* Update delivery and read state.
* Create audit and outbox events.

It shall never decrypt message content.

---

# Chapter 1678 — services/attachments.py

Required class:

```text
AttachmentService
```

Responsibilities:

* Initialise upload.
* Validate chunk submission.
* Coordinate chunk storage.
* Resume upload.
* Finalise attachment.
* Authorise download.
* Link attachment to message.
* Apply retention state.

It shall not implement raw filesystem operations directly.

---

# Chapter 1679 — services/presence.py

Required class:

```text
PresenceService
```

Responsibilities:

* Set presence.
* Process heartbeat.
* Mark offline.
* Return presence summaries.
* Use Redis with TTL.
* Rebuild state after Redis recovery.

---

# Chapter 1680 — services/notifications.py

Required class:

```text
NotificationService
```

Responsibilities:

* Create application notifications.
* Determine target users.
* Respect notification policy.
* Publish client events.
* Avoid plaintext message previews from the server.

---

# Chapter 1681 — services/announcements.py

Required class:

```text
AnnouncementService
```

Responsibilities:

* Create draft.
* Validate target.
* Publish.
* Withdraw.
* List for user.
* Record acknowledgement.
* Audit administrative actions.

---

# Chapter 1682 — services/audit.py

Required classes:

```text
AuditService
AuditWriter
AuditIntegrityService
```

Responsibilities:

* Create structured audit events.
* Append hash-linked entries.
* Verify ranges.
* Export filtered records.
* Prevent plaintext message inclusion.

---

# Chapter 1683 — services/administration.py

Required class:

```text
AdminService
```

Responsibilities:

* Coordinate high-level administrative actions.
* Require permissions.
* Require reasons.
* Prevent self-lockout.
* Revoke sessions.
* Change roles.
* Disable users.
* Return administrative summaries.

---

# Chapter 1684 — services/monitoring.py

Required class:

```text
MonitoringService
```

Responsibilities:

* Aggregate component health.
* Return connection counts.
* Report storage use.
* Report worker state.
* Produce safe health DTOs.

---

# Chapter 1685 — services/configuration.py

Required class:

```text
ConfigurationService
```

Responsibilities:

* Return editable settings.
* Validate candidate configuration.
* Save configuration versions.
* Apply reloadable changes.
* Mark restart-required changes.
* Publish policy updates.

It shall never return server secrets.

---

# Chapter 1686 — services/diagnostics.py

Required classes:

```text
ServerDiagnosticService
HelpdeskDiagnosticService
```

Responsibilities:

* Run bounded checks.
* Produce safe diagnostic results.
* Redact paths and credentials.
* Separate ordinary-user and administrator detail levels.

---

# Chapter 1687 — services/exports.py

Required classes:

```text
AuditExportService
UserDataExportService
```

Responsibilities:

* Create export jobs.
* Apply authorised filters.
* Generate protected files.
* Expire exports.
* Record audit events.

Long-running export generation shall use workers.

---

# Chapter 1688 — Server API Package

Layout:

```text
server/api/
├── __init__.py
├── router.py
├── middleware/
├── exception_handlers.py
└── v1/
```

---

# Chapter 1689 — server/api/router.py

Purpose:

Constructs the top-level API router.

It shall include versioned routers such as:

```text
/api/v1/auth
/api/v1/users
/api/v1/contacts
/api/v1/conversations
/api/v1/messages
/api/v1/attachments
/api/v1/announcements
/api/v1/admin
```

No endpoint implementation shall exist in this file.

---

# Chapter 1690 — API v1 Layout

```text
server/api/v1/
├── __init__.py
├── auth.py
├── users.py
├── contacts.py
├── keys.py
├── conversations.py
├── groups.py
├── messages.py
├── attachments.py
├── announcements.py
├── sessions.py
├── diagnostics.py
├── health.py
└── admin/
```

---

# Chapter 1691 — API Route File Contract

Every route file shall:

* Define one FastAPI `APIRouter`.
* Use Pydantic request and response models.
* Use dependency injection.
* Contain thin endpoint functions.
* Avoid direct ORM access.
* Avoid cryptographic implementation.
* Avoid file-path manipulation.
* Return documented status codes.

---

# Chapter 1692 — api/v1/auth.py

Endpoints:

```text
POST /login
POST /refresh
POST /logout
POST /logout-all
POST /protocol
```

Responsibilities:

* Parse request.
* Call authentication or session service.
* Return session DTO.
* Set no browser cookies unless explicitly designed.

---

# Chapter 1693 — api/v1/users.py

Endpoints may include:

```text
GET /me
PATCH /me
GET /users/{user_id}
GET /users
GET /users/{user_id}/keys
```

Search endpoints shall be paginated.

---

# Chapter 1694 — api/v1/conversations.py

Endpoints:

```text
GET /conversations
POST /conversations/direct
POST /conversations/group
GET /conversations/{conversation_id}
PATCH /conversations/{conversation_id}/preferences
GET /conversations/{conversation_id}/members
```

Group-specific member changes may be delegated to `groups.py`.

---

# Chapter 1695 — api/v1/groups.py

Endpoints:

```text
POST /groups/{group_id}/members
DELETE /groups/{group_id}/members/{user_id}
PATCH /groups/{group_id}/members/{user_id}/role
POST /groups/{group_id}/transfer-ownership
POST /groups/{group_id}/leave
PATCH /groups/{group_id}
DELETE /groups/{group_id}
```

---

# Chapter 1696 — api/v1/messages.py

Endpoints:

```text
POST /messages
GET /conversations/{conversation_id}/messages
PATCH /messages/{message_id}
DELETE /messages/{message_id}
POST /conversations/{conversation_id}/read
```

Routes shall not decrypt content.

---

# Chapter 1697 — api/v1/attachments.py

Endpoints:

```text
POST /attachments/uploads
GET /attachments/uploads/{upload_id}
PUT /attachments/uploads/{upload_id}/chunks/{chunk_index}
POST /attachments/uploads/{upload_id}/complete
DELETE /attachments/uploads/{upload_id}
GET /attachments/{attachment_id}
GET /attachments/{attachment_id}/chunks/{chunk_index}
```

Chunk responses shall stream bytes.

---

# Chapter 1698 — API Admin Package

Layout:

```text
server/api/v1/admin/
├── __init__.py
├── router.py
├── dashboard.py
├── users.py
├── sessions.py
├── connections.py
├── audit.py
├── alerts.py
├── announcements.py
├── configuration.py
├── workers.py
├── exports.py
└── health.py
```

Each file shall enforce the required permission through dependencies or services.

---

# Chapter 1699 — Server Middleware Package

Layout:

```text
server/api/middleware/
├── __init__.py
├── correlation.py
├── request_logging.py
├── security_headers.py
├── rate_limiting.py
├── request_limits.py
└── timing.py
```

---

# Chapter 1700 — middleware/correlation.py

Required class or function:

```text
CorrelationIdMiddleware
```

Responsibilities:

* Validate inbound ID.
* Generate fallback.
* Store context.
* Add response header.
* Clear context after request.

---

# Chapter 1701 — middleware/request_logging.py

Responsibilities:

* Log request method.
* Log route template.
* Log status.
* Log duration.
* Include correlation ID.
* Avoid logging sensitive bodies and headers.

---

# Chapter 1702 — middleware/rate_limiting.py

Responsibilities:

* Identify endpoint category.
* Use user ID or source IP.
* Query rate-limit store.
* Return structured 429.
* Add retry-after information.
* Fall back safely if Redis fails.

---

# Chapter 1703 — api/exception_handlers.py

Required handlers:

```text
handle_application_error()
handle_request_validation_error()
handle_http_exception()
handle_unexpected_exception()
```

Only this boundary should generate final REST error envelopes.

---

# Chapter 1704 — Server Authentication Package

Layout:

```text
server/authentication/
├── __init__.py
├── providers.py
├── ldap_provider.py
├── local_provider.py
├── mock_provider.py
├── tokens.py
├── password_hashing.py
├── directory_sync.py
└── login_attempts.py
```

---

# Chapter 1705 — authentication/providers.py

Required abstract interface:

```text
AuthenticationProvider
```

Required DTO:

```text
DirectoryUser
```

No LDAP-specific library object shall leave the provider implementation.

---

# Chapter 1706 — authentication/ldap_provider.py

Required class:

```text
LDAPAuthenticationProvider
```

Responsibilities:

* Establish secure connection.
* Escape filters.
* Locate user.
* Bind credentials.
* Read account state.
* Map attributes.
* Read group membership.
* Translate LDAP failures.

---

# Chapter 1707 — authentication/local_provider.py

Required class:

```text
LocalAuthenticationProvider
```

Responsibilities:

* Load user credentials.
* Verify Argon2id hash.
* Check lockout.
* Return normalised identity.
* Remain disabled unless configured.

---

# Chapter 1708 — authentication/tokens.py

Required class:

```text
TokenManager
```

Responsibilities:

* Generate access tokens.
* Generate refresh tokens.
* Hash refresh tokens.
* Decode and validate access tokens.
* Validate issuer and audience.
* Expose no database operations.

---

# Chapter 1709 — authentication/password_hashing.py

Required class:

```text
PasswordHasher
```

Responsibilities:

* Hash Argon2id.
* Verify.
* Detect rehash requirement.
* Avoid logging inputs.

---

# Chapter 1710 — authentication/directory_sync.py

Required class:

```text
DirectorySynchronisationService
```

Responsibilities:

* Synchronise one user.
* Synchronise all users.
* Map groups to roles.
* Disable missing or disabled users according to policy.
* Produce change report.

---

# Chapter 1711 — Server WebSocket Package

Layout:

```text
server/websocket/
├── __init__.py
├── endpoint.py
├── connection.py
├── manager.py
├── dispatcher.py
├── handlers.py
├── heartbeat.py
├── publisher.py
└── subscriptions.py
```

---

# Chapter 1712 — websocket/endpoint.py

Purpose:

Defines the FastAPI WebSocket route.

Responsibilities:

* Accept connection.
* Enforce authentication timeout.
* Delegate messages to dispatcher.
* Handle disconnect.
* Avoid implementing event-specific business logic.

---

# Chapter 1713 — websocket/connection.py

Required class:

```text
WebSocketConnection
```

Stores:

```text
connection_id
user_id
session_id
device_id
connected_at
last_heartbeat
subscriptions
```

Methods:

```text
send()
close()
mark_heartbeat()
```

---

# Chapter 1714 — websocket/manager.py

Required class:

```text
WebSocketConnectionManager
```

Responsibilities:

* Register connection.
* Remove connection.
* Index by user and session.
* Send to user.
* Send to session.
* Disconnect session.
* List administrative summaries.

---

# Chapter 1715 — websocket/dispatcher.py

Required class:

```text
WebSocketEventDispatcher
```

Responsibilities:

* Parse envelope.
* Validate event type.
* Validate DTO.
* Route to handler.
* Return acknowledgement or error.
* Apply event rate limit.

---

# Chapter 1716 — websocket/handlers.py

Required handlers:

```text
handle_heartbeat()
handle_typing()
handle_presence()
handle_delivery_acknowledgement()
handle_read_receipt()
```

Durable message sending should remain REST-based in Version 1.0 unless explicitly changed.

---

# Chapter 1717 — websocket/publisher.py

Required classes:

```text
EventPublisher
LocalWebSocketEventPublisher
RedisBackedEventPublisher where enabled
```

Responsibilities:

* Build event envelopes.
* Select recipients.
* Publish durable notifications.
* Avoid publishing before commit.

---

# Chapter 1718 — Server Storage Package

Layout:

```text
server/storage/
├── __init__.py
├── interface.py
├── local_filesystem.py
├── paths.py
├── checksums.py
├── manifests.py
└── cleanup.py
```

---

# Chapter 1719 — storage/interface.py

Required abstract class:

```text
FileStorage
```

It shall define:

```text
create_upload_area()
write_chunk()
read_chunk()
chunk_exists()
finalise_upload()
delete_upload()
delete_attachment()
get_usage()
verify_reference()
```

---

# Chapter 1720 — storage/local_filesystem.py

Required class:

```text
LocalFileStorage
```

Responsibilities:

* Use safe generated paths.
* Write atomically.
* Stream reads.
* Prevent path traversal.
* Check mount availability.
* Apply permissions.
* Report capacity.

---

# Chapter 1721 — storage/paths.py

Required class:

```text
AttachmentPathBuilder
```

Responsibilities:

* Build paths from UUIDs only.
* Resolve and verify root containment.
* Format chunk filenames.
* Build temporary and permanent paths.
* Never use user filename as path component.

---

# Chapter 1722 — storage/checksums.py

Required class:

```text
ChecksumService
```

Responsibilities:

* Stream SHA-256.
* Verify expected checksum.
* Avoid loading complete files.
* Use constant-time comparison where appropriate.

---

# Chapter 1723 — Server Workers Package

Layout:

```text
server/workers/
├── __init__.py
├── base.py
├── manager.py
├── outbox.py
├── session_cleanup.py
├── attachment_cleanup.py
├── audit_verification.py
├── directory_sync.py
├── statistics.py
├── export_jobs.py
└── backup_monitor.py
```

---

# Chapter 1724 — workers/base.py

Required abstract class:

```text
BackgroundWorker
```

Responsibilities:

* Start.
* Stop.
* Run loop.
* Execute one iteration.
* Handle cancellation.
* Record health.
* Apply retry policy.

---

# Chapter 1725 — workers/manager.py

Required class:

```text
WorkerManager
```

Responsibilities:

* Register workers.
* Start in order.
* Stop in reverse order.
* Return statuses.
* Prevent duplicate starts.
* Permit authorised manual run.

---

# Chapter 1726 — workers/outbox.py

Required class:

```text
OutboxPublisherWorker
```

Responsibilities:

* Claim bounded batch.
* Publish.
* Mark success.
* Schedule retry.
* Handle poison events.
* Emit alerts after repeated failure.

---

# Chapter 1727 — workers/session_cleanup.py

Responsibilities:

* Find expired sessions.
* Invalidate or remove according to policy.
* Disconnect matching WebSockets.
* Record execution result.

---

# Chapter 1728 — workers/attachment_cleanup.py

Responsibilities:

* Remove expired upload sessions.
* Remove orphaned attachments.
* Process retention deletions.
* Reconcile filesystem and database.
* Avoid deleting held records.

---

# Chapter 1729 — workers/audit_verification.py

Responsibilities:

* Verify recent range.
* Run scheduled full verification.
* Create critical alert after failure.
* Never alter audit entries.

---

# Chapter 1730 — Server Monitoring Package

Layout:

```text
server/monitoring/
├── __init__.py
├── health.py
├── metrics.py
├── database.py
├── redis.py
├── storage.py
├── workers.py
└── system.py
```

Each module shall focus on one component.

---

# Chapter 1731 — monitoring/health.py

Required class:

```text
HealthAggregator
```

Responsibilities:

* Collect component results.
* Determine combined state.
* Produce public and detailed responses.
* Apply timeouts to health checks.

---

# Chapter 1732 — monitoring/metrics.py

Required class:

```text
MetricsCollector
```

Responsibilities:

* Count requests.
* Record latency.
* Count connections.
* Record message and transfer statistics.
* Avoid sensitive labels.

---

# Chapter 1733 — Server Logging Package

Layout:

```text
server/logging/
├── __init__.py
├── configuration.py
├── processors.py
├── context.py
└── sanitisation.py
```

---

# Chapter 1734 — logging/configuration.py

Required function:

```text
configure_logging()
```

Responsibilities:

* Configure JSON or console output.
* Configure rotation.
* Configure categories.
* Apply environment level.
* Register sanitisation processors.

---

# Chapter 1735 — logging/context.py

Required functions:

```text
set_correlation_context()
get_correlation_context()
clear_correlation_context()
```

Context variables shall work correctly with asynchronous requests.

---

# Chapter 1736 — logging/sanitisation.py

Required functions:

```text
redact_mapping()
redact_headers()
sanitise_exception()
is_sensitive_field_name()
```

Tests shall verify that secret markers never appear.

---

# Chapter 1737 — Client Package Layout

```text
src/bluebubbles/client/
├── __init__.py
├── main.py
├── application.py
├── bootstrap.py
├── container.py
├── configuration/
├── domain/
├── models/
├── repositories/
├── services/
├── networking/
├── security/
├── storage/
├── workers/
├── viewmodels/
├── views/
├── widgets/
├── notifications/
├── administration/
├── logging/
└── utilities/
```

---

# Chapter 1738 — client/main.py

Purpose:

Creates the Qt application and starts `ClientApplication`.

Responsibilities:

* Install crash handler.
* Configure event-loop integration.
* Load installation settings.
* Start application.
* Return exit code.

It shall not contain page or service logic.

---

# Chapter 1739 — client/application.py

Required class:

```text
ClientApplication
```

Responsibilities:

* Coordinate login lifecycle.
* Create unauthenticated container.
* Create authenticated container.
* Show login window.
* Show main window.
* Handle logout.
* Handle shutdown.
* Clear in-memory secrets.

---

# Chapter 1740 — client/bootstrap.py

Required functions:

```text
build_unauthenticated_container()
build_authenticated_container()
verify_client_environment()
```

It shall construct dependencies in the defined order.

---

# Chapter 1741 — client/container.py

Required classes:

```text
ClientContainer
ClientRepositories
ClientServices
ViewModelFactory
```

The authenticated container shall be disposable at logout.

---

# Chapter 1742 — Client Configuration Package

Layout:

```text
client/configuration/
├── __init__.py
├── settings.py
├── loader.py
├── preferences.py
├── policies.py
└── effective_settings.py
```

---

# Chapter 1743 — client/configuration/settings.py

Required classes:

```text
ClientSettings
ClientApplicationSettings
ServerConnectionSettings
ClientTLSSettings
ClientNetworkSettings
ClientStorageSettings
ClientTransferSettings
ClientLoggingSettings
ClientFeatureFlagSettings
ClientProtocolSettings
```

---

# Chapter 1744 — client/configuration/preferences.py

Required classes:

```text
UserPreferences
NotificationPreferences
AppearancePreferences
TransferPreferences
```

Preferences shall be persisted through the local settings repository.

---

# Chapter 1745 — client/configuration/policies.py

Required class:

```text
ClientPolicy
```

Contains server-controlled values such as:

```text
Maximum attachment size
Decrypted cache permission
Read receipt policy
Blocked file extensions
Maximum group size
```

---

# Chapter 1746 — client/configuration/effective_settings.py

Required class:

```text
EffectiveSettingsResolver
```

Responsibilities:

* Combine installation defaults.
* Combine user preferences.
* Apply server restrictions.
* Produce effective values.
* Report overridden preferences.

---

# Chapter 1747 — Client Domain Package

Layout:

```text
client/domain/
├── __init__.py
├── identity.py
├── conversations.py
├── messages.py
├── attachments.py
├── transfers.py
├── drafts.py
├── offline_actions.py
└── search.py
```

Client domain models may include decrypted in-memory representations.

They shall not be shared with the server.

---

# Chapter 1748 — client/domain/messages.py

Required entities:

```text
ClientMessage
DecryptedMessageContent
MessageDraft
MessageDisplayState
```

The model shall distinguish:

```text
Encrypted transport data
Decrypted in-memory content
Encrypted local cache content
```

---

# Chapter 1749 — client/domain/transfers.py

Required entities:

```text
FileTransfer
PreparedUpload
TransferState
TransferProgress
EncryptedChunk
```

Required state-transition methods shall reject invalid transitions.

---

# Chapter 1750 — Client Models Package

Layout:

```text
client/models/
├── __init__.py
├── users.py
├── conversations.py
├── messages.py
├── attachments.py
├── transfers.py
├── settings.py
└── administration.py
```

These are UI-facing models where separation from domain entities is helpful.

---

# Chapter 1751 — Client Repository Package

Layout:

```text
client/repositories/
├── __init__.py
├── interfaces/
└── sqlite/
```

Repository interfaces shall support testing with in-memory fakes.

---

# Chapter 1752 — Client Repository Interfaces

Required interfaces:

```text
CachedUserRepository
CachedConversationRepository
CachedMessageRepository
DraftRepository
OfflineActionRepository
TransferStateRepository
SearchIndexRepository
LocalSettingsRepository
PublicKeyCacheRepository
```

---

# Chapter 1753 — SQLite Repository Implementations

Layout:

```text
client/repositories/sqlite/
├── users.py
├── conversations.py
├── messages.py
├── drafts.py
├── offline_actions.py
├── transfers.py
├── search.py
├── settings.py
└── keys.py
```

All SQL shall be parameterised.

---

# Chapter 1754 — Client Services Package

Layout:

```text
client/services/
├── __init__.py
├── authentication.py
├── sessions.py
├── users.py
├── contacts.py
├── conversations.py
├── messaging.py
├── groups.py
├── attachments.py
├── transfers.py
├── notifications.py
├── search.py
├── synchronisation.py
├── offline_queue.py
├── settings.py
├── diagnostics.py
└── administration.py
```

---

# Chapter 1755 — client/services/authentication.py

Required class:

```text
ClientAuthenticationService
```

Responsibilities:

* Negotiate protocol.
* Submit login.
* Store tokens securely.
* Return authenticated identity.
* Never persist plaintext password.

---

# Chapter 1756 — client/services/sessions.py

Required class:

```text
ClientSessionService
```

Responsibilities:

* Supply valid access token.
* Coordinate refresh.
* Logout.
* Revoke sessions.
* Handle session-revoked events.

---

# Chapter 1757 — client/services/conversations.py

Required class:

```text
ClientConversationService
```

Responsibilities:

* Load cached list.
* Fetch server list.
* Merge versions.
* Create direct or group conversation.
* Load membership.
* Update local cache.

---

# Chapter 1758 — client/services/messaging.py

Required class:

```text
ClientMessagingService
```

Responsibilities:

* Build outgoing message.
* Encrypt.
* Sign.
* Queue offline.
* Submit.
* Process incoming encrypted message.
* Verify.
* Decrypt.
* Cache.
* Update delivery state.

---

# Chapter 1759 — client/services/transfers.py

Required class:

```text
FileTransferService
```

Responsibilities:

* Prepare upload.
* Start upload worker.
* Resume.
* Download.
* Verify.
* Decrypt.
* Expose progress.
* Persist transfer state.

---

# Chapter 1760 — client/services/search.py

Required class:

```text
LocalSearchService
```

Responsibilities:

* Index decrypted authorised messages.
* Generate HMAC tokens.
* Search.
* Verify candidates.
* Rebuild.
* Remove edited or deleted records.

---

# Chapter 1761 — client/services/synchronisation.py

Required class:

```text
SynchronisationService
```

Responsibilities:

* Initial sync.
* Reconnection sync.
* Apply missed events.
* Detect gaps.
* Refresh stale scopes.
* Process version conflicts.

---

# Chapter 1762 — client/services/offline_queue.py

Required class:

```text
OfflineQueueService
```

Responsibilities:

* Enqueue.
* Encrypt local payload.
* Preserve ordering.
* Process after reconnect.
* Classify failures.
* Expose manual retry and cancellation.

---

# Chapter 1763 — Client Networking Package

Layout:

```text
client/networking/
├── __init__.py
├── api_client.py
├── websocket_client.py
├── authentication.py
├── retry.py
├── circuit_breaker.py
├── connectivity.py
└── tls.py
```

---

# Chapter 1764 — networking/api_client.py

Required class:

```text
ApiClient
```

Responsibilities:

* Build URLs.
* Attach access token.
* Attach correlation ID.
* Send JSON and binary requests.
* Parse error envelopes.
* Apply timeouts.
* Coordinate one token refresh.
* Support streaming.

It shall not contain business-specific methods for every domain if separate API wrappers are used.

---

# Chapter 1765 — networking/websocket_client.py

Required class:

```text
WebSocketClient
```

Responsibilities:

* Connect.
* Authenticate.
* Receive events.
* Dispatch events.
* Heartbeat.
* Reconnect.
* Track last processed event.
* Close cleanly.

---

# Chapter 1766 — networking/retry.py

Required classes:

```text
RetryPolicy
RetryExecutor
```

Responsibilities:

* Classify safe retry.
* Apply backoff.
* Apply jitter.
* Respect cancellation.
* Respect retry-after.

---

# Chapter 1767 — networking/connectivity.py

Required class:

```text
ConnectivityMonitor
```

Responsibilities:

* Determine server reachability.
* Track online/offline state.
* Notify services.
* Avoid excessive polling.
* Trigger synchronisation after reconnect.

---

# Chapter 1768 — Client Security Package

Layout:

```text
client/security/
├── __init__.py
├── key_store.py
├── key_manager.py
├── message_crypto.py
├── attachment_crypto.py
├── signatures.py
├── secure_store.py
├── local_encryption.py
└── memory.py
```

---

# Chapter 1769 — security/secure_store.py

Required interface and implementation:

```text
SecureStore
WindowsCredentialManagerStore
```

Responsibilities:

* Store token secrets.
* Store local cache keys.
* Store device ID.
* Delete secrets.
* Avoid plaintext files.

---

# Chapter 1770 — security/key_store.py

Required class:

```text
EncryptedPrivateKeyStore
```

Responsibilities:

* Store encrypted private keys.
* Unlock after authentication.
* Lock during logout.
* Rotate keys.
* Never expose keys through logs or DTOs.

---

# Chapter 1771 — security/key_manager.py

Required class:

```text
ClientKeyManager
```

Responsibilities:

* Generate identity keys.
* Register public keys.
* Retrieve private keys.
* Retrieve recipient public keys.
* Handle versions.
* Process revocation.
* Coordinate key export or recovery where implemented.

---

# Chapter 1772 — security/message_crypto.py

Required class:

```text
MessageEncryptionService
```

Responsibilities:

* Generate content key.
* Encrypt plaintext.
* Generate recipient envelopes.
* Build canonical fields.
* Sign.
* Verify.
* Decrypt recipient content.

It shall use established cryptographic library APIs.

---

# Chapter 1773 — security/attachment_crypto.py

Required class:

```text
AttachmentEncryptionService
```

Responsibilities:

* Generate file key.
* Encrypt chunks.
* Decrypt chunks.
* Encrypt metadata.
* Decrypt metadata.
* Build authenticated data.
* Verify authentication tags.

---

# Chapter 1774 — security/local_encryption.py

Required class:

```text
LocalEncryptionService
```

Responsibilities:

* Encrypt decrypted cache fields.
* Encrypt drafts.
* Encrypt offline queue payloads.
* Encrypt transfer manifests.
* Use dedicated keys and unique nonces.

---

# Chapter 1775 — Client Storage Package

Layout:

```text
client/storage/
├── __init__.py
├── database.py
├── migrations.py
├── cache_manager.py
├── paths.py
├── temporary_files.py
└── integrity.py
```

---

# Chapter 1776 — storage/database.py

Required class:

```text
LocalDatabaseManager
```

Responsibilities:

* Open user database.
* Apply key.
* Run transactions.
* Close.
* Check integrity.
* Expose connection factory.

---

# Chapter 1777 — storage/migrations.py

Required class:

```text
ClientMigrationManager
```

Responsibilities:

* Determine schema version.
* Create backup.
* Apply migrations.
* Restore after failure.
* Preserve drafts and queue.

---

# Chapter 1778 — storage/cache_manager.py

Required class:

```text
CacheManager
```

Responsibilities:

* Calculate use.
* Enforce limits.
* Evict LRU entries.
* Respect pinned entries.
* Remove expired items.
* Report cleanup.

---

# Chapter 1779 — Client Workers Package

Layout:

```text
client/workers/
├── __init__.py
├── base.py
├── upload.py
├── download.py
├── encryption.py
├── search_index.py
├── synchronisation.py
└── cache_cleanup.py
```

Workers shall expose progress and cancellation safely to Qt.

---

# Chapter 1780 — workers/base.py

Required base classes:

```text
AsyncWorker
CancellableWorker
ProgressWorker
```

The implementation shall integrate with the selected Qt and asyncio event-loop strategy.

---

# Chapter 1781 — workers/upload.py

Required class:

```text
UploadWorker
```

Responsibilities:

* Initialise upload.
* Query resume state.
* Upload missing chunks.
* Apply bandwidth limit.
* Finalise.
* Persist progress.
* Emit signals.

---

# Chapter 1782 — workers/download.py

Required class:

```text
DownloadWorker
```

Responsibilities:

* Fetch metadata.
* Retrieve file key.
* Download missing chunks.
* Verify.
* Decrypt.
* Write partial output.
* Rename after final checksum.

---

# Chapter 1783 — workers/search_index.py

Required class:

```text
SearchIndexWorker
```

Responsibilities:

* Index messages.
* Rebuild.
* Report progress.
* Support cancellation.
* Avoid blocking interface.

---

# Chapter 1784 — Client ViewModels Package

Layout:

```text
client/viewmodels/
├── __init__.py
├── base.py
├── login.py
├── main.py
├── navigation.py
├── conversation_list.py
├── chat.py
├── contacts.py
├── groups.py
├── transfers.py
├── search.py
├── settings.py
├── diagnostics.py
└── administration/
```

---

# Chapter 1785 — viewmodels/base.py

Required base class:

```text
BaseViewModel
```

Possible responsibilities:

* Busy state.
* Error signal.
* Cancellation.
* Disposal.
* Common property-change signal.

It shall not become a large inheritance hierarchy.

---

# Chapter 1786 — viewmodels/login.py

Required class:

```text
LoginViewModel
```

State:

```text
server address
username
password
loading
error
connection status
```

Actions:

```text
validate
login
test connection
cancel
```

Password shall be cleared after failed authentication.

---

# Chapter 1787 — viewmodels/main.py

Required class:

```text
MainViewModel
```

Responsibilities:

* Current user.
* Connection state.
* Selected navigation page.
* Global unread count.
* Global banners.
* Logout.
* Shutdown coordination.

---

# Chapter 1788 — viewmodels/conversation_list.py

Required class:

```text
ConversationListViewModel
```

Responsibilities:

* Load cached summaries.
* Refresh.
* Apply sorting.
* Apply archive or pin state.
* Select conversation.
* Show unread counts.

---

# Chapter 1789 — viewmodels/chat.py

Required class:

```text
ChatViewModel
```

Responsibilities:

* Load paginated messages.
* Maintain draft.
* Send.
* Edit.
* Delete.
* Reply.
* Handle incoming events.
* Mark read.
* Start attachment.
* Expose typing state.

No cryptographic implementation shall exist in the ViewModel.

---

# Chapter 1790 — viewmodels/transfers.py

Required class:

```text
TransferListViewModel
```

Responsibilities:

* Display transfers.
* Pause.
* Resume.
* Cancel.
* Retry.
* Open completed destination.
* Display rate and progress.

---

# Chapter 1791 — viewmodels/search.py

Required class:

```text
SearchViewModel
```

Responsibilities:

* Validate query.
* Apply filters.
* Start search.
* Display result.
* Navigate to message.
* Rebuild index where permitted.

---

# Chapter 1792 — Client Views Package

Layout:

```text
client/views/
├── __init__.py
├── login_window.py
├── main_window.py
├── pages/
├── dialogs/
└── layouts/
```

Views shall contain presentation and event wiring only.

---

# Chapter 1793 — views/login_window.py

Required class:

```text
LoginWindow
```

Contains:

* Server field where configurable.
* Username field.
* Password field.
* Login button.
* Connection test.
* Error display.
* Privacy notice.

It binds to `LoginViewModel`.

---

# Chapter 1794 — views/main_window.py

Required class:

```text
MainWindow
```

Contains:

```text
Navigation sidebar
Conversation list region
Content region
Status banner
System-tray integration
```

It shall not directly call API services.

---

# Chapter 1795 — Views Pages Layout

```text
client/views/pages/
├── conversations_page.py
├── chat_page.py
├── contacts_page.py
├── groups_page.py
├── transfers_page.py
├── search_page.py
├── settings_page.py
├── diagnostics_page.py
└── administration_page.py
```

---

# Chapter 1796 — views/pages/chat_page.py

Required class:

```text
ChatPage
```

Contains:

* Header.
* Member information.
* Scrollable message list.
* Loading indicator.
* Typing indicator.
* Composer.
* Attachment controls.
* Send control.

It shall use reusable message widgets.

---

# Chapter 1797 — Client Widgets Package

Layout:

```text
client/widgets/
├── __init__.py
├── message_widget.py
├── message_composer.py
├── conversation_item.py
├── user_avatar.py
├── attachment_widget.py
├── transfer_widget.py
├── status_banner.py
├── loading_indicator.py
├── error_widget.py
└── accessible_icon_button.py
```

Widgets shall remain reusable and focused.

---

# Chapter 1798 — widgets/message_widget.py

Required class:

```text
MessageWidget
```

Responsibilities:

* Render sender and timestamp.
* Render decrypted text.
* Render attachment references.
* Render status.
* Render edited and deleted states.
* Expose context-menu actions.

It shall not decrypt data.

---

# Chapter 1799 — widgets/message_composer.py

Required class:

```text
MessageComposer
```

Responsibilities:

* Text entry.
* Reply indicator.
* Edit indicator.
* Attachment list.
* Character count.
* Send signal.
* Draft-change signal.
* Keyboard shortcuts.

---

# Chapter 1800 — Client Administration Package

Layout:

```text
client/administration/
├── __init__.py
├── services.py
├── models.py
├── viewmodels/
└── views/
```

This package shall only be activated when the authenticated user has administrative capability.

---

# Chapter 1801 — Administration ViewModels

Required classes:

```text
DashboardViewModel
UserAdminViewModel
AuditViewModel
SecurityAlertViewModel
HealthViewModel
ConfigurationViewModel
WorkerViewModel
AnnouncementAdminViewModel
```

The server still enforces all permissions.

---

# Chapter 1802 — Client Notifications Package

Layout:

```text
client/notifications/
├── __init__.py
├── manager.py
├── windows.py
├── tray.py
└── policy.py
```

---

# Chapter 1803 — notifications/manager.py

Required class:

```text
NotificationManager
```

Responsibilities:

* Apply user preferences.
* Apply mute state.
* Apply server policy.
* Generate local previews only after decryption.
* Avoid notifications for active visible conversation where configured.
* Protect sensitive previews on shared screens.

---

# Chapter 1804 — notifications/tray.py

Required class:

```text
SystemTrayManager
```

Responsibilities:

* Show tray icon.
* Show connection state.
* Open window.
* Show unread count.
* Quit application safely.

---

# Chapter 1805 — Client Logging Package

Layout:

```text
client/logging/
├── __init__.py
├── configuration.py
├── sanitisation.py
├── crash_handler.py
└── diagnostics.py
```

---

# Chapter 1806 — logging/crash_handler.py

Required class:

```text
ClientCrashHandler
```

Responsibilities:

* Capture unexpected boundary exceptions.
* Save sanitised record.
* Attempt safe state preservation.
* Show crash dialog.
* Avoid continuing in unknown state.

---

# Chapter 1807 — Scripts Directory

Root layout:

```text
scripts/
├── server/
├── client/
├── development/
└── maintenance/
```

---

# Chapter 1808 — Server Scripts

Required scripts may include:

```text
create_admin.py
validate_config.py
diagnose.py
verify_audit.py
seed_development.py
generate_test_data.py
check_storage.py
```

Scripts shall call application services where practical rather than duplicate business logic.

---

# Chapter 1809 — Client Scripts

Possible scripts:

```text
build_client.py
generate_icons.py
validate_resources.py
create_installer.py
```

Build scripts shall use version metadata from one source.

---

# Chapter 1810 — Development Scripts

Possible scripts:

```text
start_test_services.py
reset_test_database.py
run_quality_checks.py
run_full_test_suite.py
```

Destructive scripts shall verify the environment is not production.

---

# Chapter 1811 — Deployment Directory

Layout:

```text
deployment/
├── systemd/
│   └── bluebubbles.service
├── nginx/
│   └── bluebubbles.conf
├── windows/
│   └── installer.iss
├── scripts/
│   ├── install_server.sh
│   ├── upgrade_server.sh
│   ├── rollback_server.sh
│   └── uninstall_server.sh
└── examples/
```

Templates shall use placeholders rather than real credentials.

---

# Chapter 1812 — Configuration Directory

Layout:

```text
config/
├── server/
│   ├── base.yaml
│   ├── development.yaml
│   ├── testing.yaml
│   ├── demonstration.yaml
│   └── production.example.yaml
└── client/
    ├── default.yaml
    └── managed.example.yaml
```

Actual production configuration shall remain outside the repository.

---

# Chapter 1813 — Requirements Directory

Possible structure:

```text
requirements/
├── base.txt
├── server.txt
├── client.txt
├── development.txt
├── testing.txt
└── hashes/
```

Where `pyproject.toml` and a lock file fully replace these, unnecessary duplication shall be avoided.

One dependency-management approach shall be authoritative.

---

# Chapter 1814 — Documentation Directory

Layout:

```text
docs/
├── architecture/
├── api/
├── deployment/
├── administration/
├── user/
├── development/
├── security/
├── testing/
└── nea/
```

---

# Chapter 1815 — Architecture Documentation

Required documents:

```text
system-overview.md
client-architecture.md
server-architecture.md
database-schema.md
cryptography.md
network-protocol.md
dependency-diagram.md
```

These shall match the implemented source structure.

---

# Chapter 1816 — API Documentation

Required documents:

```text
rest-api.md
websocket-events.md
error-codes.md
protocol-versions.md
```

OpenAPI generation may supplement but not entirely replace human-readable documentation.

---

# Chapter 1817 — Resources Directory

Layout:

```text
resources/
├── icons/
├── themes/
├── fonts/
├── images/
├── translations/
└── certificates/
```

The repository shall not distribute private certificate keys.

Bundled fonts must have appropriate licensing.

---

# Chapter 1818 — Themes Resources

Suggested files:

```text
resources/themes/
├── light.qss
├── dark.qss
└── high_contrast.qss
```

Theme variables may be generated through a controlled loader.

Views shall not contain large embedded style strings.

---

# Chapter 1819 — Test Package Layout

The test structure from Part 18 shall mirror source modules where practical.

Example:

```text
tests/unit/server/services/test_messaging.py
```

corresponds to:

```text
src/bluebubbles/server/services/messaging.py
```

This makes coverage gaps easier to identify.

---

# Chapter 1820 — Test Helpers

Layout:

```text
tests/helpers/
├── api.py
├── websocket.py
├── encryption.py
├── database.py
├── filesystem.py
└── assertions.py
```

Helpers shall reduce boilerplate without hiding test intent.

---

# Chapter 1821 — Test Factories

Layout:

```text
tests/factories/
├── users.py
├── sessions.py
├── conversations.py
├── messages.py
├── attachments.py
├── audit.py
└── configuration.py
```

Each factory shall produce valid defaults.

---

# Chapter 1822 — Migration Directory

Alembic layout:

```text
migrations/
├── env.py
├── script.py.mako
└── versions/
```

Migration files shall be version controlled.

The migration directory shall import ORM metadata without importing full application startup.

---

# Chapter 1823 — Import Boundary Rules

The following import rules shall be enforced:

```text
Views may import ViewModels and UI models.

ViewModels may import client services and client models.

Client services may import networking, security and repositories.

Server routers may import services and shared DTOs.

Server services may import domain models and repository interfaces.

Repositories may import ORM models and domain mappings.

Domain modules shall not import FastAPI, PySide6 or SQLAlchemy sessions.
```

---

# Chapter 1824 — Circular Import Prevention

Strategies:

* Use repository interfaces.
* Use service interfaces.
* Place shared DTOs in `shared`.
* Use event publication for secondary effects.
* Use local imports only as a last justified measure.
* Avoid importing package `__init__.py` files containing broad re-exports.

Circular imports shall be treated as an architecture defect rather than patched repeatedly.

---

# Chapter 1825 — **init**.py Rules

Package `__init__.py` files shall remain minimal.

They may expose:

```text
Version
Small stable public interfaces
```

They shall not import every class from every module.

Large re-export chains can create circular imports and slow startup.

---

# Chapter 1826 — File Size Guidance

Source files should normally remain below approximately:

```text
500 lines
```

This is guidance rather than an absolute rule.

A file exceeding this should be reviewed for:

* Multiple responsibilities.
* Repeated helpers.
* Separate DTOs.
* Separate interfaces and implementations.
* Extractable domain rules.

---

# Chapter 1827 — Class Responsibility Rule

Every class shall have one primary reason to change.

Examples:

```text
MessagingService changes when messaging use cases change.

MessageRepository changes when message persistence changes.

MessageEncryptionService changes when client encryption implementation changes.

ChatViewModel changes when chat presentation behaviour changes.
```

These responsibilities shall not be merged into one large class.

---

# Chapter 1828 — Function Responsibility Rule

Functions shall:

* Have one clear purpose.
* Use descriptive names.
* Avoid excessive nesting.
* Validate inputs at boundaries.
* Return typed results.
* Avoid hidden global state.
* Avoid unrelated side effects.

Long workflows should be decomposed into private helper methods or collaborating services.

---

# Chapter 1829 — Naming Rules

Use:

```text
PascalCase for classes
snake_case for functions and variables
UPPER_SNAKE_CASE for true constants
leading underscore for private implementation details
```

Names shall describe business meaning.

Avoid vague names such as:

```text
Manager
Helper
Data
Thing
Process
```

unless qualified clearly.

---

# Chapter 1830 — Async Naming and Usage

Asynchronous functions do not need an `_async` suffix in Python.

Use:

```python
async def send_message(...)
```

rather than:

```python
async def send_message_async(...)
```

unless both synchronous and asynchronous variants exist and require distinction.

---

# Chapter 1831 — Result Objects

Complex operations may return typed result objects.

Examples:

```text
SendMessageResult
UploadFinalisationResult
SynchronisationResult
CacheCleanupResult
AuditVerificationResult
```

Avoid returning unstructured tuples with many values.

---

# Chapter 1832 — DTO Conversion

Conversions shall use explicit functions or class methods.

Examples:

```text
user_to_response()
message_to_encrypted_response()
attachment_to_response()
orm_to_domain()
domain_to_orm()
```

Automatic broad serialisation of ORM objects shall be avoided.

---

# Chapter 1833 — No Duplicate Models Rule

The coding AI shall not create multiple conflicting definitions of:

```text
User
Message
Conversation
Attachment
ErrorCode
WebSocketEventType
```

Where separate representations are required, names shall clarify them:

```text
UserORM
User
UserProfileResponse
CachedUser
```

---

# Chapter 1834 — No Placeholder Implementation Rule

The generated project shall not leave core methods containing only:

```python
pass
```

or:

```python
raise NotImplementedError
```

unless the class is intentionally abstract.

Version 1.0-required paths shall have real implementations.

Deferred features shall be disabled explicitly rather than represented by broken interface controls.

---

# Chapter 1835 — No Silent Exception Rule

Code shall not contain:

```python
try:
    ...
except Exception:
    pass
```

Expected exceptions shall be handled specifically.

Unexpected exceptions shall be logged and propagated to an application boundary.

---

# Chapter 1836 — No Global Mutable State Rule

Avoid global mutable instances such as:

```text
Global database session
Global current user
Global token
Global message list
Global WebSocket connection dictionary outside manager ownership
```

Application-wide state shall be owned by a container or lifecycle-managed service.

---

# Chapter 1837 — Secret Handling Rule

No source file shall contain:

```text
Real password
Real token
Real database URL
Real private key
Real LDAP bind credential
Real certificate private key
```

Example values shall be visibly fake.

---

# Chapter 1838 — Logging Rule

Every module shall use the configured structured logger.

It shall not use random `print()` statements for production diagnostics.

Command-line scripts may print user-facing status while still using structured logs for technical events.

---

# Chapter 1839 — Type-Hint Rule

Public functions, service methods, repository methods and constructors shall have type hints.

Return types shall be explicit.

`Any` shall be limited to boundaries such as validated JSONB details.

---

# Chapter 1840 — Documentation String Rule

Public classes and non-obvious functions shall include concise docstrings.

Docstrings shall explain:

* Purpose.
* Important security behaviour.
* Exceptions where useful.
* Return meaning.

They shall not repeat obvious code line by line.

---

# Chapter 1841 — Configuration Access Rule

Services shall receive configuration objects through constructors.

They shall not repeatedly read environment variables directly.

Only the configuration loader should access raw environment variables and secret files.

---

# Chapter 1842 — Database Access Rule

Only repositories and database infrastructure shall execute SQLAlchemy queries.

Routers, ViewModels and widgets shall never access database sessions.

---

# Chapter 1843 — Network Access Rule

Only networking clients and server route or WebSocket boundaries shall perform network protocol operations.

Client ViewModels shall call services rather than `httpx` directly.

---

# Chapter 1844 — Cryptography Access Rule

Only defined client security services shall perform private-key operations and content encryption.

Server code shall validate encrypted envelope structure but shall not attempt message decryption.

---

# Chapter 1845 — File Access Rule

Server file access shall go through `FileStorage`.

Client managed-cache file access shall go through client storage services.

Views shall never manipulate physical paths directly beyond receiving user-selected destination paths.

---

# Chapter 1846 — Event Handling Rule

Durable application events shall use the outbox or documented durable mechanism.

Transient events may use direct WebSocket publication.

Event handlers shall be idempotent where duplicate delivery is possible.

---

# Chapter 1847 — Version Source Rule

The application version shall have one authoritative source.

Recommended:

```text
pyproject.toml
```

`version.py` may expose the generated or imported value.

Client, server, installer and deployment manifest shall all use the same version.

---

# Chapter 1848 — Build Output Directory

Generated files shall use:

```text
build/
dist/
```

These directories shall not contain source-controlled secrets.

Most build output shall be excluded from Git.

---

# Chapter 1849 — pyproject.toml Tool Configuration

The file shall configure:

```text
Project metadata
Python version
Dependency groups
Ruff
mypy
pytest
coverage
build backend
```

Tool configuration shall not be duplicated unnecessarily in separate files.

---

# Chapter 1850 — Minimum Python Version

The project specification targets:

```text
Python 3.13 or later compatible release
```

The code shall avoid unsupported deprecated APIs.

The exact tested version shall be documented.

---

# Chapter 1851 — Source-Code Generation Order

The coding AI shall implement in this order:

```text
1. Shared enums and DTOs

2. Configuration models

3. Domain models

4. ORM schema and migrations

5. Repository interfaces

6. Repository implementations

7. Core server services

8. Authentication infrastructure

9. REST API

10. WebSocket infrastructure

11. Server workers and monitoring

12. Client secure storage

13. Client networking

14. Client cryptography

15. Client services

16. Client ViewModels

17. Client views and widgets

18. Deployment files

19. Automated tests

20. Documentation
```

This order reduces unresolved dependencies.

---

# Chapter 1852 — Incremental Build Requirement

The coding AI shall not generate the entire project as one unverified block.

After each subsystem:

```text
Run formatting
Run type checking
Run unit tests
Run relevant integration tests
Fix failures
Commit or mark stable state
```

The next subsystem shall build upon tested interfaces.

---

# Chapter 1853 — Initial Executable Milestone

The first executable milestone shall include:

```text
Server configuration loads
PostgreSQL connects
Migrations apply
Health endpoint responds
Client launches
Client tests server connectivity
```

It does not yet require messaging.

---

# Chapter 1854 — Authentication Milestone

Required:

```text
Login works
Session stored
Access token works
Refresh works
Logout invalidates session
Client stores token securely
```

Only after this milestone shall protected messaging endpoints be implemented.

---

# Chapter 1855 — Messaging Milestone

Required:

```text
Two users exist
Direct conversation created
Client encrypts message
Server stores ciphertext
Recipient retrieves and decrypts
No plaintext appears in server database
```

---

# Chapter 1856 — Group Milestone

Required:

```text
Group created
Owner and members stored
Group message reaches members
Removed member receives no future envelope
Ownership transfer works
```

---

# Chapter 1857 — Attachment Milestone

Required:

```text
File encrypts in chunks
Upload resumes
Server stores encrypted chunks
Recipient downloads
Final checksum matches
```

---

# Chapter 1858 — Administration Milestone

Required:

```text
Audit chain works
User can be disabled
Session revokes
Health dashboard loads
Administrator cannot access plaintext
```

---

# Chapter 1859 — Final Integration Milestone

Required:

```text
Client installation succeeds
Server service starts at boot
TLS validates
Offline queue recovers
Server restart recovers
Upgrade preserves data
Required tests pass
```

---

# Chapter 1860 — Source Contract Tests

Automated architecture tests should verify:

```text
Shared package does not import client or server.

Domain package does not import FastAPI.

Domain package does not import PySide6.

Views do not import repositories.

Routers do not import ORM models directly.

Server does not import client package.

No duplicate ErrorCode definitions exist.

No production source contains obvious hard-coded secrets.
```

---

# Chapter 1861 — Import-Linting

A tool such as `import-linter` may enforce dependency boundaries.

Possible contracts:

```text
shared is independent

server.domain is independent of server.api

client.viewmodels do not import client.views

client.views do not import server
```

If the tool is not used, equivalent tests or code review shall enforce the rules.

---

# Chapter 1862 — Source-Code Review Checklist

Before a module is considered complete:

```text
Correct package
Clear responsibility
Typed public interface
No secret values
No plaintext logging
No direct dependency violation
Expected exceptions handled
Tests included
Docstring included where needed
No placeholder core methods
```

---

# Chapter 1863 — Simplified Version 1.0 File Scope

Version 1.0 shall implement all files required for:

```text
Authentication
User profiles
Contacts
Direct conversations
Groups
Encrypted messages
Encrypted attachments
Local cache
Offline queue
Search
Audit
Administration
Monitoring
Deployment
Testing
```

Files for deferred features shall not be created unless they provide a required interface.

Examples of deferred packages that should not be generated prematurely:

```text
Voice calling
Video calling
Remote desktop
Plugin marketplace
Cloud synchronisation
Bot framework
Multiple server federation
```

---

# Chapter 1864 — Source-Code Structure Summary

The BlueBubbles repository shall use a `src` layout with separate `shared`, `server` and `client` packages.

The shared package shall contain only protocol-safe common definitions.

The server shall separate:

* Domain entities.
* ORM models.
* Repositories.
* Services.
* API routes.
* Authentication providers.
* WebSocket infrastructure.
* Storage.
* Workers.
* Monitoring.
* Logging.

The client shall separate:

* Domain and display models.
* Local repositories.
* Services.
* Networking.
* Cryptography.
* Secure storage.
* Workers.
* ViewModels.
* Views.
* Reusable widgets.
* Notifications.
* Administration.

Routes and views shall remain thin.

Business rules shall remain in services and domain logic.

SQL shall remain in repositories.

Private-key cryptography shall remain in client security services.

Filesystem operations shall remain behind storage interfaces.

Every major source file shall have a clear implementation contract.

The coding AI shall implement the project incrementally and run quality checks after each subsystem rather than generating an unverified monolith.

---

# End of Part 21

Part 22 will define the complete class-level implementation blueprint, including:

* Constructor dependencies.
* Public methods.
* Method input and output types.
* Important private helpers.
* Service collaboration.
* State ownership.
* Async behaviour.
* Signals and callbacks.
* Repository interfaces.
* Worker lifecycles.
* ViewModel contracts.
* Exact responsibilities of the most important classes.
