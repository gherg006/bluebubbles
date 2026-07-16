# Task 08 — Server lifecycle and health

> This is a self-contained implementation task split from the complete BlueBubbles Version 1.0 specification. Source requirements below are reproduced verbatim, not summarised. Where a repeated project-wide rule conflicts with a task-local choice, the project-wide rule wins.

## Required predecessors

Task 03, Task 07.

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

---

## Task-specific authoritative source: Part 10

# Part 10 — Server-Side Architecture and Application Services

---

# Chapter 261 — Server Purpose

The BlueBubbles server is the central coordination point for the entire messaging system.

It is responsible for:

* Authenticating users.
* Validating sessions.
* Enforcing permissions.
* Routing encrypted messages.
* Storing encrypted messages.
* Managing conversations and groups.
* Storing encrypted attachments.
* Maintaining user presence.
* Delivering real-time events.
* Recording audit events.
* Providing administrative information.
* Coordinating PostgreSQL and Redis.
* Recovering safely after restarts.

The server shall not decrypt user messages or attachments.

The server shall never store plaintext message content.

---

# Chapter 262 — Server Technology Stack

The server shall use:

```text
Python 3.13+
FastAPI
Uvicorn
SQLAlchemy 2.x
PostgreSQL
Redis
Pydantic 2.x
Alembic
httpx
websockets
python-ldap or ldap3
PyJWT or python-jose
argon2-cffi
cryptography
structlog
psutil
pytest
pytest-asyncio
```

The server operating system shall be Debian 13 or a later compatible Debian release.

---

# Chapter 263 — Server Architecture

The server shall follow a layered architecture.

```text
FastAPI Application

↓

Routers

↓

Middleware

↓

Application Services

↓

Repositories

↓

PostgreSQL / Redis / File Storage
```

Each layer shall have one clear responsibility.

---

# Chapter 264 — Server Directory Structure

The server package shall use the following structure.

```text
server/
│
├── main.py
├── application.py
├── bootstrap.py
├── dependencies.py
│
├── api/
│   ├── router.py
│   └── v1/
│       ├── auth.py
│       ├── users.py
│       ├── contacts.py
│       ├── conversations.py
│       ├── messages.py
│       ├── groups.py
│       ├── files.py
│       ├── presence.py
│       ├── notifications.py
│       ├── announcements.py
│       ├── admin.py
│       └── health.py
│
├── services/
│   ├── authentication_service.py
│   ├── session_service.py
│   ├── user_service.py
│   ├── contact_service.py
│   ├── conversation_service.py
│   ├── messaging_service.py
│   ├── group_service.py
│   ├── attachment_service.py
│   ├── presence_service.py
│   ├── notification_service.py
│   ├── announcement_service.py
│   ├── audit_service.py
│   ├── permission_service.py
│   ├── statistics_service.py
│   └── health_service.py
│
├── repositories/
│   ├── base_repository.py
│   ├── user_repository.py
│   ├── contact_repository.py
│   ├── conversation_repository.py
│   ├── message_repository.py
│   ├── group_repository.py
│   ├── attachment_repository.py
│   ├── session_repository.py
│   ├── announcement_repository.py
│   ├── audit_repository.py
│   └── settings_repository.py
│
├── database/
│   ├── base.py
│   ├── connection.py
│   ├── session.py
│   ├── models/
│   ├── migrations/
│   └── seed.py
│
├── redis/
│   ├── client.py
│   ├── keys.py
│   ├── presence_store.py
│   ├── typing_store.py
│   ├── rate_limit_store.py
│   └── event_publisher.py
│
├── authentication/
│   ├── ldap_authenticator.py
│   ├── local_authenticator.py
│   ├── authentication_provider.py
│   ├── token_manager.py
│   ├── session_manager.py
│   └── password_hasher.py
│
├── websocket/
│   ├── connection.py
│   ├── connection_manager.py
│   ├── event_dispatcher.py
│   ├── event_handlers.py
│   └── heartbeat_manager.py
│
├── middleware/
│   ├── authentication.py
│   ├── correlation_id.py
│   ├── request_logging.py
│   ├── rate_limiting.py
│   ├── security_headers.py
│   └── exception_handling.py
│
├── schemas/
│   ├── auth.py
│   ├── users.py
│   ├── conversations.py
│   ├── messages.py
│   ├── files.py
│   ├── groups.py
│   ├── admin.py
│   └── common.py
│
├── storage/
│   ├── file_storage.py
│   ├── attachment_path.py
│   ├── temporary_storage.py
│   ├── checksum_service.py
│   └── storage_cleanup.py
│
├── workers/
│   ├── background_worker.py
│   ├── attachment_cleanup_worker.py
│   ├── session_cleanup_worker.py
│   ├── audit_integrity_worker.py
│   ├── database_maintenance_worker.py
│   └── statistics_worker.py
│
├── monitoring/
│   ├── metrics_collector.py
│   ├── server_health.py
│   ├── database_health.py
│   ├── redis_health.py
│   └── storage_health.py
│
├── configuration/
│   ├── settings.py
│   ├── loader.py
│   └── environment.py
│
└── logging/
    ├── configuration.py
    ├── audit_logger.py
    └── security_logger.py
```

---

# Chapter 265 — FastAPI Application Object

The main FastAPI application shall be created by an application factory.

```python
def create_application() -> FastAPI:
    """Create and configure the BlueBubbles FastAPI application."""
```

The application factory shall:

* Load configuration.
* Configure logging.
* Register middleware.
* Register routers.
* Configure exception handlers.
* Configure startup events.
* Configure shutdown events.
* Configure OpenAPI metadata.
* Add security headers.

The FastAPI application shall not be constructed directly inside route modules.

---

# Chapter 266 — Application Lifecycle

Server startup shall follow this sequence.

```text
Load environment configuration

↓

Validate required settings

↓

Configure structured logging

↓

Create PostgreSQL engine

↓

Test database connection

↓

Run or verify migrations

↓

Create Redis connection

↓

Test Redis connection

↓

Initialise repositories

↓

Initialise services

↓

Initialise WebSocket manager

↓

Initialise background workers

↓

Register API routes

↓

Begin accepting requests
```

The server shall stop startup if PostgreSQL is unavailable.

Redis failure may place the server into degraded mode where practical.

---

# Chapter 267 — ServerApplication Class

```python
class ServerApplication:
    """Coordinates startup, operation and shutdown of the server."""
```

Properties:

```text
settings
database_manager
redis_manager
service_container
websocket_manager
worker_manager
health_monitor
```

Methods:

```text
start()
stop()
validate_dependencies()
start_workers()
stop_workers()
health_check()
```

The class shall coordinate infrastructure but shall not contain business logic.

---

# Chapter 268 — Dependency Injection Container

The server shall use constructor-based dependency injection.

```python
class ServerContainer:
    """Creates and supplies server-side dependencies."""
```

The container shall create:

```text
Database sessions
Redis client
Repositories
Authentication providers
Token manager
Application services
WebSocket manager
File storage service
Health monitoring services
```

Example:

```python
message_repository = MessageRepository(database_session_factory)

audit_service = AuditService(audit_repository)

messaging_service = MessagingService(
    message_repository=message_repository,
    conversation_repository=conversation_repository,
    permission_service=permission_service,
    audit_service=audit_service,
    event_publisher=event_publisher,
)
```

Services shall not construct repositories internally.

---

# Chapter 269 — Router Responsibilities

API routers shall remain thin.

A route handler may:

* Accept a validated DTO.
* Obtain the authenticated user.
* Call one application service.
* Convert the result into a response DTO.
* Return the correct HTTP status.

A route handler shall not:

* Execute SQL.
* Implement permission rules.
* Manage Redis directly.
* Manipulate files directly.
* Contain cryptographic logic.
* Construct audit entries manually.

---

# Chapter 270 — Example Route Flow

```python
@router.post("/messages", response_model=SendMessageResponse)
async def send_message(
    request: SendMessageRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    service: MessagingService = Depends(get_messaging_service),
) -> SendMessageResponse:
    result = await service.send_message(
        sender_id=current_user.id,
        request=request,
    )

    return SendMessageResponse.from_result(result)
```

The route delegates all rules to `MessagingService`.

---

# Chapter 271 — Service Layer Responsibilities

Application services implement business use cases.

Examples:

```text
Authenticate a user
Send a message
Create a group
Remove a group member
Upload an attachment
Disable an account
Publish an announcement
Retrieve server statistics
```

Services may coordinate:

* Multiple repositories.
* Redis.
* File storage.
* Audit logging.
* WebSocket events.
* Permission checks.

Services shall expose task-focused methods rather than general-purpose database access.

---

# Chapter 272 — AuthenticationService

```python
class AuthenticationService:
    """Authenticates users and creates valid application sessions."""
```

Dependencies:

```text
AuthenticationProvider
UserRepository
SessionRepository
TokenManager
AuditService
```

Methods:

```text
authenticate()
refresh_session()
logout()
validate_session()
get_current_user()
```

Authentication process:

```text
Receive username and password

↓

Validate input

↓

Authenticate against LDAP or local provider

↓

Find or synchronise user record

↓

Verify account is enabled

↓

Create server-side session

↓

Generate access token

↓

Generate refresh token

↓

Store token hashes

↓

Create audit event

↓

Return session information
```

---

# Chapter 273 — Authentication Provider Interface

```python
class AuthenticationProvider(ABC):
    """Defines the interface for user authentication providers."""
```

Abstract methods:

```text
authenticate()
get_user_profile()
is_account_enabled()
get_group_memberships()
```

Implementations:

```text
LDAPAuthenticationProvider
LocalAuthenticationProvider
```

Local authentication shall exist only for development or deployments without Active Directory.

---

# Chapter 274 — LDAP Authentication

LDAP integration shall support:

* Active Directory bind authentication.
* User profile lookup.
* Enabled or disabled account checks.
* Group membership retrieval.
* Department and job title synchronisation.
* Stable Active Directory identifiers.

LDAP credentials used by the server shall come from environment variables or a protected secret file.

LDAP passwords shall never appear in source control.

---

# Chapter 275 — SessionService

```python
class SessionService:
    """Creates, validates, refreshes and invalidates user sessions."""
```

Methods:

```text
create_session()
validate_access_token()
refresh_access_token()
invalidate_session()
invalidate_all_user_sessions()
remove_expired_sessions()
```

Sessions shall be stored server-side.

Logging out shall immediately invalidate the server-side session.

A valid JWT associated with an invalidated session shall be rejected.

---

# Chapter 276 — TokenManager

```python
class TokenManager:
    """Creates and validates signed access and refresh tokens."""
```

Responsibilities:

* Generate access tokens.
* Generate refresh tokens.
* Decode tokens.
* Verify signatures.
* Verify expiration.
* Extract session identifiers.
* Reject malformed tokens.

Recommended lifetimes:

```text
Access token: 15 minutes
Refresh token: 7 days
```

These values shall be configurable.

---

# Chapter 277 — UserService

```python
class UserService:
    """Provides user profile and account management operations."""
```

Methods:

```text
get_user()
search_users()
update_profile()
synchronise_from_directory()
enable_user()
disable_user()
export_user_data()
request_user_deletion()
```

Only permitted roles may enable or disable accounts.

Disabling an account shall invalidate all active sessions.

---

# Chapter 278 — ContactService

```python
class ContactService:
    """Manages relationships and contact ordering between users."""
```

Methods:

```text
list_contacts()
add_contact()
remove_contact()
favourite_contact()
unfavourite_contact()
block_contact()
unblock_contact()
calculate_weight()
```

A blocked user shall not be able to begin a new direct conversation unless organisational policy overrides this behaviour.

---

# Chapter 279 — ConversationService

```python
class ConversationService:
    """Creates and manages direct and group conversations."""
```

Methods:

```text
list_conversations()
get_conversation()
create_direct_conversation()
create_group_conversation()
archive_conversation()
rename_conversation()
validate_membership()
```

Direct conversations shall be unique for each pair of users unless the design explicitly supports multiple direct threads.

---

# Chapter 280 — MessagingService

```python
class MessagingService:
    """Validates, stores and routes encrypted messages."""
```

Dependencies:

```text
MessageRepository
ConversationRepository
PermissionService
AuditService
EventPublisher
```

Methods:

```text
send_message()
get_messages()
edit_message()
delete_message()
mark_delivered()
mark_read()
add_reaction()
remove_reaction()
```

The service shall never decrypt the message payload.

---

# Chapter 281 — Message Send Workflow

```text
Receive encrypted message request

↓

Validate sender session

↓

Validate conversation exists

↓

Validate sender membership

↓

Validate request structure

↓

Validate recipient key entries

↓

Validate message size

↓

Validate client signature fields exist

↓

Create database transaction

↓

Insert encrypted message

↓

Insert recipient message keys

↓

Insert audit event

↓

Commit transaction

↓

Publish WebSocket event

↓

Return acknowledgement
```

If database insertion fails, no success event shall be published.

---

# Chapter 282 — Message Validation

The server shall validate:

* Conversation identifier.
* Sender membership.
* Ciphertext is present.
* Nonce has the expected encoded length.
* Authentication tag is present where required.
* Signature is present.
* Recipient key entries match valid recipients.
* Payload size is within limits.
* Reply target belongs to the same conversation.
* Protocol version is supported.

The server does not need to verify that ciphertext decrypts successfully.

---

# Chapter 283 — Message Editing

Editing shall create a new encrypted payload.

The existing row may be updated with:

```text
New ciphertext
New nonce
New authentication tag
New signature
Edited timestamp
Increased version
```

An edit history may be stored as separate encrypted versions if required.

Only the original sender may edit a message.

The edit time limit shall be configurable.

---

# Chapter 284 — Message Deletion

Message deletion shall use soft deletion.

The server shall preserve:

```text
Message identifier
Sender identifier
Conversation identifier
Original timestamp
Deletion timestamp
Encrypted content
Audit record
```

The normal client response shall indicate that the message was deleted.

Whether the encrypted content is eventually permanently removed shall be controlled by data retention policy.

---

# Chapter 285 — GroupService

```python
class GroupService:
    """Manages group conversations and membership permissions."""
```

Methods:

```text
create_group()
rename_group()
delete_group()
add_member()
remove_member()
promote_member()
demote_member()
leave_group()
transfer_ownership()
list_members()
```

Every membership change shall create an audit event.

---

# Chapter 286 — Group Permission Rules

Group roles:

```text
Owner
Moderator
Member
```

Owner permissions:

* Rename group.
* Delete group.
* Add members.
* Remove members.
* Promote moderators.
* Demote moderators.
* Transfer ownership.

Moderator permissions:

* Add members where policy allows.
* Remove ordinary members.
* Manage selected group settings.

Member permissions:

* Send messages.
* Receive messages.
* Leave the group.
* View members.

A user removed from a group shall immediately lose access to future messages and group events.

---

# Chapter 287 — PermissionService

```python
class PermissionService:
    """Determines whether an authenticated user may perform an action."""
```

Methods:

```text
has_permission()
require_permission()
can_access_conversation()
can_manage_group()
can_manage_user()
can_view_audit_event()
```

Permission checks shall be performed server-side for every protected action.

GUI visibility shall never be treated as permission enforcement.

---

# Chapter 288 — AttachmentService

```python
class AttachmentService:
    """Coordinates encrypted attachment upload, storage and download."""
```

Dependencies:

```text
AttachmentRepository
FileStorage
ConversationRepository
PermissionService
ChecksumService
AuditService
```

Methods:

```text
begin_upload()
upload_chunk()
complete_upload()
cancel_upload()
download_chunk()
delete_attachment()
get_attachment_metadata()
```

The server shall store only encrypted attachment bytes.

---

# Chapter 289 — Upload Session

An upload shall begin by creating an upload session.

Upload session properties:

```text
upload_id
user_id
conversation_id
filename
declared_size
encrypted_size
chunk_size
chunk_count
checksum
created_at
expires_at
received_chunks
```

Temporary upload state may be stored in Redis.

Permanent attachment metadata shall only be created after successful finalisation.

---

# Chapter 290 — Chunk Upload Workflow

```text
Client requests upload session

↓

Server validates permission

↓

Server creates temporary upload directory

↓

Client uploads encrypted chunks

↓

Server verifies chunk number and size

↓

Server records received chunk

↓

Client submits completion request

↓

Server verifies all chunks exist

↓

Server calculates encrypted file checksum

↓

Server compares expected checksum

↓

Server moves file into permanent storage

↓

Server creates attachment row

↓

Server writes audit event

↓

Server notifies recipients
```

Incomplete uploads shall expire and be removed automatically.

---

# Chapter 291 — FileStorage Interface

```python
class FileStorage(ABC):
    """Defines storage operations for encrypted attachment data."""
```

Methods:

```text
create_temporary_upload()
write_chunk()
read_chunk()
assemble_chunks()
move_to_permanent_storage()
delete_file()
file_exists()
get_file_size()
```

The initial implementation shall use local filesystem storage.

The interface shall permit future network-attached storage without changing business services.

---

# Chapter 292 — Attachment Paths

Clients shall never provide final filesystem paths.

The server shall generate all paths using UUID values.

Example:

```text
/data/bluebubbles/attachments/
2026/
07/
conversation_uuid/
message_uuid/
attachment_uuid.bin
```

Filenames supplied by users shall be stored as metadata only.

User filenames shall never be used directly as storage paths.

---

# Chapter 293 — Path Traversal Protection

The server shall reject:

* Absolute paths.
* Parent-directory references.
* Null bytes.
* Invalid Unicode path sequences.
* Unexpected separators.
* Filenames exceeding configured limits.

Storage identifiers shall be generated by the server.

---

# Chapter 294 — PresenceService

```python
class PresenceService:
    """Tracks live user availability using Redis."""
```

Methods:

```text
set_presence()
get_presence()
heartbeat()
mark_offline()
list_online_users()
```

Presence records shall expire automatically using Redis TTL values.

PostgreSQL may store only long-term information such as `last_seen`.

---

# Chapter 295 — Typing Events

Typing events shall:

* Be stored temporarily in Redis.
* Expire after approximately five seconds.
* Be visible only to conversation members.
* Never be written to PostgreSQL.
* Never create audit records unless organisational policy explicitly requires it.

Typing event flow:

```text
Client sends typing event

↓

Server verifies membership

↓

Redis stores short-lived state

↓

WebSocket event sent to other members
```

---

# Chapter 296 — NotificationService

```python
class NotificationService:
    """Creates and routes non-message user notifications."""
```

Notification examples:

```text
Group invitation
Account warning
File transfer completion
Announcement
Administrative notice
Server maintenance
```

Notification contents shall not reveal plaintext message data unless the recipient client generates the preview locally.

---

# Chapter 297 — AnnouncementService

```python
class AnnouncementService:
    """Creates and distributes organisation-wide announcements."""
```

Methods:

```text
create_announcement()
publish_announcement()
withdraw_announcement()
list_announcements()
acknowledge_announcement()
```

Announcements may target:

```text
All users
Specific departments
Specific roles
Specific groups
Selected users
```

Only authorised roles may create announcements.

---

# Chapter 298 — AuditService

```python
class AuditService:
    """Creates append-only records of security and business events."""
```

Methods:

```text
record_event()
record_authentication_event()
record_message_event()
record_group_event()
record_file_event()
record_admin_event()
verify_chain()
export_events()
```

Audit entries shall be created through this service only.

Application code shall not insert audit rows manually.

---

# Chapter 299 — Audit Event Structure

Each audit event shall contain:

```text
id
event_type
actor_user_id
target_type
target_id
session_id
source_ip
timestamp
severity
result
details
previous_hash
entry_hash
```

Audit details shall contain metadata only.

Plaintext message content shall never be included.

---

# Chapter 300 — Tamper-Evident Audit Chain

Each audit entry shall include the hash of the previous entry.

```text
Previous entry hash

+

Current entry canonical data

↓

SHA-256

↓

Current entry hash
```

Changing or removing an earlier entry shall break the chain.

This design makes the audit log tamper-evident.

Database administrator access may still technically alter data, so the system shall not inaccurately claim that alteration is impossible.

---

# Chapter 301 — Audit Immutability Controls

The database role used by the application shall receive:

```text
INSERT permission
SELECT permission
```

It shall not receive:

```text
UPDATE permission
DELETE permission
```

for the audit table.

Database triggers shall reject ordinary update and delete attempts.

Audit exports may also be signed or copied to protected backup storage.

---

# Chapter 302 — Audit Privacy

Helpdesk access shall normally expose only operational metadata.

Example:

```text
Message identifier
Sender
Recipient or conversation
Timestamp
Delivery result
Attachment status
```

Helpdesk users shall not receive message content.

HR or administrators shall only receive data permitted by organisational policy and law.

---

# Chapter 303 — Repository Pattern

Every persistent entity shall have a repository.

Repositories shall:

* Open database sessions.
* Perform queries.
* Add or update models.
* Handle pagination.
* Convert database rows into domain objects where required.
* Raise repository-specific exceptions.

Repositories shall not:

* Enforce business permissions.
* Publish WebSocket events.
* Read application configuration directly.
* Generate user-facing messages.

---

# Chapter 304 — BaseRepository

```python
class BaseRepository(Generic[ModelType]):
    """Provides common persistence operations."""
```

Possible methods:

```text
get_by_id()
list()
add()
update()
soft_delete()
exists()
```

Entity-specific repositories shall add focused query methods.

---

# Chapter 305 — UserRepository

Methods:

```text
get_by_id()
get_by_username()
get_by_email()
get_by_directory_guid()
search()
create()
update_directory_fields()
set_enabled()
```

Search queries shall be indexed and paginated.

---

# Chapter 306 — MessageRepository

Methods:

```text
create_message()
create_message_keys()
get_message()
list_conversation_messages()
update_encrypted_payload()
soft_delete_message()
mark_delivered()
mark_read()
```

Message retrieval shall always confirm conversation membership at the service layer.

---

# Chapter 307 — ConversationRepository

Methods:

```text
create_direct_conversation()
create_group_conversation()
get_by_id()
find_direct_conversation()
list_for_user()
add_member()
remove_member()
is_member()
```

Frequently used membership checks shall use indexed queries.

---

# Chapter 308 — Database Session Management

Each HTTP request shall receive an independent SQLAlchemy session.

The session shall:

* Open at request start.
* Commit only when the use case succeeds.
* Roll back after any database error.
* Close after the request completes.

Long-running WebSocket connections shall not hold one permanent database session.

They shall create short-lived sessions when needed.

---

# Chapter 309 — Unit of Work

Complex operations shall use a Unit of Work abstraction where multiple repositories participate in one transaction.

```python
class UnitOfWork:
    """Coordinates repositories within one database transaction."""
```

Example use cases:

```text
Send message and create recipient keys
Create group and add initial members
Complete attachment and link it to a message
Disable user and invalidate sessions
```

---

# Chapter 310 — PostgreSQL Connection Management

The database manager shall configure:

```text
Connection pool size
Pool overflow
Connection timeout
Statement timeout
Connection recycling
Health checks
```

Development defaults shall remain modest.

Production values shall be configurable.

Database credentials shall come from environment variables.

---

# Chapter 311 — Redis Manager

```python
class RedisManager:
    """Controls Redis connectivity and transient data operations."""
```

Responsibilities:

* Create Redis connection pool.
* Test connection health.
* Reconnect after temporary failures.
* Provide namespaced key access.
* Publish events.
* Close connections during shutdown.

Redis keys shall always include a BlueBubbles namespace.

Example:

```text
bluebubbles:presence:user:<uuid>
```

---

# Chapter 312 — Redis Failure Behaviour

If Redis becomes unavailable:

* Permanent messages shall still be saved to PostgreSQL.
* REST requests not dependent on Redis may continue.
* Presence may become unavailable.
* Typing indicators may stop.
* Rate limiting may fall back to an in-process limiter.
* Real-time event delivery may temporarily degrade.
* Errors shall be logged.

The server shall not lose permanent message data because Redis failed.

---

# Chapter 313 — WebSocketConnection

```python
class WebSocketConnection:
    """Represents one authenticated client WebSocket connection."""
```

Properties:

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
send_event()
receive_event()
heartbeat()
close()
```

---

# Chapter 314 — WebSocketConnectionManager

```python
class WebSocketConnectionManager:
    """Tracks active WebSocket connections and routes events."""
```

Methods:

```text
connect()
authenticate()
disconnect()
send_to_user()
send_to_connection()
send_to_conversation()
broadcast()
list_connections()
disconnect_user()
```

One user may have multiple active devices.

Events shall be delivered to all appropriate active sessions.

---

# Chapter 315 — WebSocket Authentication Flow

```text
Client opens socket

↓

Server accepts temporary connection

↓

Client sends authentication event

↓

Server validates access token

↓

Server validates session

↓

Server associates connection with user

↓

Server registers connection

↓

Server sends authentication success

↓

Client begins event subscription
```

Authentication must complete within a short timeout.

Unauthenticated sockets shall be closed.

---

# Chapter 316 — WebSocket Event Envelope

Every event shall use a common structure.

```json
{
    "event_id": "uuid",
    "event_type": "message_received",
    "protocol_version": 1,
    "timestamp": "2026-07-16T15:30:00Z",
    "correlation_id": "uuid",
    "data": {}
}
```

The `data` field shall use a DTO specific to the event type.

---

# Chapter 317 — EventDispatcher

```python
class EventDispatcher:
    """Validates and dispatches incoming WebSocket events."""
```

Responsibilities:

* Parse event envelopes.
* Validate protocol versions.
* Validate DTOs.
* Identify event handlers.
* Record errors.
* Return acknowledgements.

Incoming client WebSocket events may include:

```text
heartbeat
typing_started
typing_stopped
presence_update
message_acknowledgement
read_receipt
```

---

# Chapter 318 — Event Delivery

Important events shall include acknowledgements.

Examples:

```text
Message notification
Group membership update
Announcement
Session revocation
```

Transient events may not require acknowledgements.

Examples:

```text
Typing indicator
Presence heartbeat
Transfer progress
```

---

# Chapter 319 — EventPublisher

```python
class EventPublisher:
    """Publishes application events to connected users."""
```

It shall hide whether delivery uses:

* Local WebSocket manager.
* Redis Pub/Sub.
* A future message broker.

This abstraction supports later multi-server deployment.

---

# Chapter 320 — Multi-Server Compatibility

Version 1.0 may use one application server.

The design shall avoid preventing future horizontal scaling.

In a multi-server deployment:

```text
Client A connects to Server 1

Client B connects to Server 2

Server 1 publishes event to Redis

Server 2 receives event

Server 2 sends event to Client B
```

Permanent data shall remain in PostgreSQL.

Shared attachment storage would be required for multiple server instances.

---

# Chapter 321 — Middleware Order

Recommended middleware order:

```text
Correlation ID

↓

Request Timing

↓

Security Headers

↓

Rate Limiting

↓

Authentication Context

↓

Request Logging

↓

Exception Handling
```

The exact FastAPI middleware order shall be tested because middleware executes in nested order.

---

# Chapter 322 — Correlation IDs

Every request and important background action shall have a correlation identifier.

The identifier shall appear in:

* Application logs.
* Error logs.
* Audit metadata where relevant.
* API error responses.
* WebSocket event acknowledgements.

This allows one action to be traced across components.

---

# Chapter 323 — Authentication Middleware

Authentication middleware may parse tokens and create an authentication context.

Final permission checks shall still occur in dependencies or services.

Public endpoints:

```text
Login
Basic health check
OpenAPI documentation, when enabled
```

All other endpoints shall require authentication unless explicitly documented.

---

# Chapter 324 — Security Headers

The server shall add appropriate headers.

Examples:

```text
Strict-Transport-Security
X-Content-Type-Options
X-Frame-Options
Content-Security-Policy where relevant
Cache-Control
```

Because the primary client is a desktop application, browser-specific headers may have limited effect but remain useful for administrative web documentation.

---

# Chapter 325 — RateLimitMiddleware

Rate limits shall use:

```text
User identifier when authenticated
IP address when unauthenticated
Endpoint category
Time window
```

Rate-limit responses shall include a retry time.

Administrative and authentication routes shall have stricter limits.

---

# Chapter 326 — Exception Hierarchy

Server exceptions shall use a clear hierarchy.

```text
BlueBubblesError
│
├── ValidationError
├── AuthenticationError
├── AuthorisationError
├── ResourceNotFoundError
├── ConflictError
├── RateLimitError
├── RepositoryError
├── StorageError
├── ExternalServiceError
└── ConfigurationError
```

Application exceptions shall be converted into stable API errors.

---

# Chapter 327 — Exception Handling

The global exception handler shall:

* Generate a correlation ID.
* Log technical details.
* Return a safe user-facing message.
* Select the correct HTTP status code.
* Hide internal stack traces.
* Avoid returning secrets.

Unexpected errors shall return:

```text
500 Internal Server Error
```

with a generic message and traceable error code.

---

# Chapter 328 — Structured Logging

Server logs shall use structured fields.

Example:

```json
{
    "timestamp": "2026-07-16T15:30:00Z",
    "level": "INFO",
    "event": "message_stored",
    "message_id": "uuid",
    "conversation_id": "uuid",
    "user_id": "uuid",
    "correlation_id": "uuid"
}
```

Structured logs are easier to filter and analyse than unstructured text.

---

# Chapter 329 — Log Categories

Separate logical log categories shall exist for:

```text
Application
Authentication
Security
Database
WebSocket
File Transfer
Audit
Background Workers
Performance
```

Logs may be written to separate rotating files or a structured logging destination.

---

# Chapter 330 — Sensitive Logging Rules

Never log:

```text
Passwords
Plaintext messages
Private keys
Decrypted attachment data
Raw JWT tokens
Raw refresh tokens
LDAP bind passwords
Database passwords
```

Where token identification is needed, log a non-reversible fingerprint.

---

# Chapter 331 — BackgroundWorker Base Class

```python
class BackgroundWorker(ABC):
    """Defines the lifecycle of a recurring server-side task."""
```

Methods:

```text
start()
stop()
run_once()
run_loop()
handle_failure()
```

Workers shall support graceful cancellation.

---

# Chapter 332 — Session Cleanup Worker

Responsibilities:

* Find expired sessions.
* Invalidate expired refresh tokens.
* Remove old session rows according to retention rules.
* Disconnect invalid WebSocket sessions.
* Record abnormal cleanup failures.

Recommended interval:

```text
Every 15 minutes
```

---

# Chapter 333 — Attachment Cleanup Worker

Responsibilities:

* Remove expired temporary uploads.
* Remove orphaned chunks.
* Process attachments past deletion retention.
* Check storage records against database metadata.
* Report missing files.

The worker shall not permanently delete data before retention rules permit it.

---

# Chapter 334 — Audit Integrity Worker

Responsibilities:

* Verify recent audit hash chains.
* Detect missing sequence entries.
* Record integrity failures.
* Notify administrators.
* Produce integrity reports.

The worker shall not automatically alter broken audit records.

---

# Chapter 335 — Database Maintenance Worker

Possible responsibilities:

* Update statistics.
* Detect slow queries.
* Remove expired temporary records.
* Schedule safe maintenance operations.
* Report index or storage concerns.

PostgreSQL’s own maintenance processes shall not be replaced unnecessarily.

---

# Chapter 336 — Statistics Worker

The statistics worker may calculate aggregate data such as:

```text
Active users
Messages per hour
Files transferred
Average delivery latency
Failed login count
Storage growth
```

It shall not inspect message plaintext.

Aggregates may be stored for the administration dashboard.

---

# Chapter 337 — HealthService

```python
class HealthService:
    """Combines infrastructure health information into server status."""
```

Dependencies:

```text
DatabaseHealthChecker
RedisHealthChecker
StorageHealthChecker
WorkerHealthChecker
```

Methods:

```text
get_public_health()
get_detailed_health()
```

---

# Chapter 338 — Public Health Response

The public health endpoint shall reveal minimal information.

Example:

```json
{
    "status": "healthy",
    "version": "1.0.0"
}
```

It shall not reveal:

* Database addresses.
* Internal file paths.
* Server secrets.
* Detailed software versions unnecessarily.
* User counts.

---

# Chapter 339 — Detailed Health Response

Administrators may receive:

```text
Database connectivity
Redis connectivity
Storage availability
Storage free space
Background worker status
Server uptime
CPU usage
Memory usage
Current WebSocket connection count
Recent internal errors
```

Detailed health information shall require permission.

---

# Chapter 340 — Monitoring Metrics

Recommended metrics:

```text
HTTP request count
HTTP response duration
HTTP error count
Active WebSocket connections
WebSocket disconnect count
Message persistence latency
Message event delivery latency
Database query duration
Redis operation duration
Attachment throughput
Failed login attempts
Worker failures
```

Metrics shall not contain sensitive message content.

---

# Chapter 341 — Performance Timing

The server shall measure important operations.

Examples:

```text
Authentication duration
Message insert duration
Conversation query duration
Attachment upload duration
WebSocket delivery duration
```

Performance logs shall include correlation identifiers.

---

# Chapter 342 — Database Query Targets

Required targets under normal LAN development conditions:

```text
Retrieve 50 recent messages:

Under 200 ms

Retrieve conversation list:

Under 200 ms

Store one encrypted text message:

Under 100 ms

Validate conversation membership:

Under 50 ms
```

These values shall be verified through performance tests.

---

# Chapter 343 — Server Concurrency

FastAPI endpoints shall be asynchronous where appropriate.

Suitable asynchronous operations:

* Database operations using an async SQLAlchemy driver.
* Redis access.
* WebSocket communication.
* File streaming.
* LDAP requests where supported.

CPU-heavy work shall not block the event loop.

The server should not perform client-side encryption or decryption.

---

# Chapter 344 — File Streaming

Downloads shall be streamed in bounded chunks.

The server shall not load entire large attachments into memory.

Chunk size shall be configurable.

Recommended default:

```text
1 MiB
```

Tests shall compare performance with alternative sizes.

---

# Chapter 345 — Resource Limits

The server shall configure:

```text
Maximum request body size
Maximum message payload size
Maximum concurrent uploads per user
Maximum upload session duration
Maximum WebSocket connections per account
Maximum login attempts per interval
Database statement timeout
```

Limits shall be configuration values rather than constants hidden in code.

---

# Chapter 346 — Configuration Model

Server configuration shall use a validated settings class.

```python
class ServerSettings(BaseSettings):
    """Defines validated server configuration."""
```

Settings categories:

```text
Application
Network
Database
Redis
LDAP
Tokens
Storage
Logging
Security
Rate limits
Retention
Monitoring
```

Startup shall fail with a clear error when required settings are missing.

---

# Chapter 347 — Environment Configuration

Suggested environment variables:

```text
BLUEBUBBLES_ENVIRONMENT
BLUEBUBBLES_HOST
BLUEBUBBLES_PORT
BLUEBUBBLES_DATABASE_URL
BLUEBUBBLES_REDIS_URL
BLUEBUBBLES_TOKEN_SECRET
BLUEBUBBLES_STORAGE_ROOT
BLUEBUBBLES_LDAP_SERVER
BLUEBUBBLES_LDAP_BIND_DN
BLUEBUBBLES_LDAP_BIND_PASSWORD
BLUEBUBBLES_LDAP_BASE_DN
```

The `.env.example` file shall contain placeholders only.

Real secret files shall be excluded from Git.

---

# Chapter 348 — Development, Testing and Production Modes

Development mode may enable:

```text
Debug logging
Automatic reload
Local authentication
API documentation
Test certificates
```

Testing mode shall use:

```text
Isolated test database
Isolated Redis database or mock
Temporary file storage
Predictable test configuration
```

Production mode shall enforce:

```text
TLS
Strong secrets
Restricted documentation
No automatic reload
Secure logging
Real directory authentication where configured
```

---

# Chapter 349 — Database Migrations

Alembic shall manage PostgreSQL schema changes.

Rules:

* Every schema change requires a migration.
* Migrations shall be reviewed before production use.
* Destructive migrations require backups.
* Downgrade support should be provided where practical.
* Application startup shall check migration state.
* Production startup shall not silently perform dangerous migrations.

---

# Chapter 350 — Initial Data Seeding

Development and testing environments may create:

```text
Default roles
Default permissions
Example users
Example groups
Example conversations
```

Production seeding shall create only required system data.

No default administrator password shall be hard-coded.

---

# Chapter 351 — Initial Administrator Creation

The initial administrator shall be created using a dedicated command-line setup script.

Example:

```text
python -m scripts.create_admin
```

The script shall:

* Require interactive confirmation.
* Validate the account against LDAP where applicable.
* Assign the administrator role.
* Record an audit event.
* Never print passwords.

---

# Chapter 352 — Graceful Shutdown

Shutdown sequence:

```text
Stop accepting new requests

↓

Notify background workers

↓

Stop recurring workers

↓

Finish or safely interrupt active tasks

↓

Close WebSocket connections

↓

Publish offline presence where possible

↓

Close Redis connections

↓

Close database pool

↓

Flush log handlers

↓

Exit
```

The server shall not terminate abruptly during ordinary service shutdown.

---

# Chapter 353 — Server Restart Recovery

After a restart:

* PostgreSQL remains the source of permanent data.
* Redis presence data may be rebuilt.
* Clients reconnect automatically.
* Clients re-authenticate or refresh sessions.
* Undelivered message events are reconstructed from server state.
* Temporary uploads may resume where valid.
* Expired temporary uploads are removed.
* Audit chain verification continues.

No stored message or completed attachment shall be lost through an ordinary restart.

---

# Chapter 354 — Systemd Integration

Production deployment shall use a systemd service.

The service shall configure:

```text
Dedicated service account
Working directory
Environment file
Automatic restart
Resource limits
Dependency on network availability
Logging destination
Graceful stop timeout
```

The service shall not run as root.

---

# Chapter 355 — Server Security Account

The server process shall run under a dedicated Linux account.

Example:

```text
bluebubbles
```

This account shall have:

* Read access to application files.
* Controlled write access to attachment storage.
* Controlled write access to logs.
* No interactive login where practical.
* No unrestricted sudo access.
* No access to unrelated user data.

---

# Chapter 356 — Firewall Requirements

Only required ports shall be opened.

Typical deployment:

```text
443/TCP

HTTPS and WebSocket traffic

22/TCP

SSH administration from management devices only

5432/TCP

PostgreSQL, local host or private server network only

6379/TCP

Redis, local host or private server network only

389 or 636/TCP

LDAP or LDAPS to Active Directory
```

PostgreSQL and Redis shall not be exposed to ordinary client devices.

---

# Chapter 357 — LAN-Only Enforcement

BlueBubbles shall not make external Internet requests.

The server shall avoid:

* Cloud APIs.
* External analytics.
* Online update checks.
* Remote fonts.
* External notification services.
* Public DNS dependencies where avoidable.

Deployment documentation shall recommend firewall rules preventing outbound Internet access from the application server except where administrators explicitly require operating-system updates.

---

# Chapter 358 — Server Testing Requirements

Server tests shall include:

```text
Application startup
Configuration validation
Authentication
Session invalidation
Token refresh
LDAP provider mocking
Permission enforcement
Message storage
Conversation membership
Group member removal
Attachment chunking
Checksum validation
Audit insertion
Audit chain verification
Redis failure behaviour
WebSocket authentication
WebSocket message delivery
Rate limiting
Repository transactions
Database rollback
Graceful shutdown
Health checks
```

Tests shall use isolated temporary infrastructure.

---

# Chapter 359 — Server Integration Tests

Integration tests shall verify complete workflows.

Examples:

```text
Login → create session → call protected endpoint

Create group → add members → send encrypted message

Remove member → verify future access denied

Upload chunks → finalise attachment → download identical encrypted bytes

Logout → verify token rejected

Restart application → verify stored data remains available
```

---

# Chapter 360 — Server Architecture Summary

The BlueBubbles server shall act as a secure coordinator rather than a plaintext message processor.

Its primary responsibilities are:

* Identity verification.
* Permission enforcement.
* Reliable persistence.
* Encrypted data routing.
* Real-time event distribution.
* Attachment storage.
* Audit generation.
* Administrative monitoring.

FastAPI routers shall remain thin.

Services shall enforce business rules.

Repositories shall perform persistence.

PostgreSQL shall store permanent data.

Redis shall store temporary live state.

The filesystem shall store encrypted attachments.

WebSockets shall deliver real-time events.

No layer shall bypass the architecture defined in this specification.

---

# End of Part 10

Part 11 will define the complete authentication, Active Directory and authorisation design, including:

* LDAP connection configuration.
* Active Directory user synchronisation.
* Local development accounts.
* Login and logout behaviour.
* Access and refresh tokens.
* Server-side session invalidation.
* Roles and permissions.
* Account disabling.
* Password handling.
* Multi-device sessions.
* Failed login protection.
* Authentication test cases.

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

## Task-specific authoritative source: Part 17

# Part 17 — Error Handling, Diagnostics and Recovery

---

# Chapter 1001 — Error-Handling Subsystem Purpose

The error-handling subsystem defines how BlueBubbles detects, classifies, records, communicates and recovers from failures.

It shall ensure that:

* Users receive clear explanations.
* Technical details remain available to administrators.
* Sensitive information is never exposed.
* Recoverable failures trigger safe retries.
* Permanent failures are not retried indefinitely.
* Partial operations are rolled back.
* Errors can be traced across components.
* Degraded services remain usable where safe.
* Unexpected crashes preserve useful diagnostics.
* The application never fails silently.

Error handling shall be consistent across the client, server, workers, WebSockets, storage and external dependencies.

---

# Chapter 1002 — Error-Handling Principles

BlueBubbles shall follow these principles:

```text
Fail safely.

Prefer explicit failure over silent data loss.

Do not expose secrets.

Use stable error codes.

Preserve transactional consistency.

Retry only recoverable failures.

Apply bounded retry limits.

Provide correlation identifiers.

Separate user messages from technical details.

Record enough context for diagnosis.

Avoid duplicate error reporting.

Never claim success before durable completion.
```

---

# Chapter 1003 — Error Categories

Errors shall be grouped into broad categories.

```text
VALIDATION
AUTHENTICATION
AUTHORISATION
RESOURCE
CONFLICT
RATE_LIMIT
NETWORK
DEPENDENCY
DATABASE
REDIS
STORAGE
CRYPTOGRAPHY
PROTOCOL
FILE_TRANSFER
LOCAL_STORAGE
CONFIGURATION
WORKER
INTERNAL
```

Each category shall map to:

* A stable machine-readable code.
* A safe user-facing message.
* A severity.
* A retry classification.
* An HTTP or WebSocket result where applicable.
* A logging policy.

---

# Chapter 1004 — Base Exception Hierarchy

```python
class BlueBubblesError(Exception):
    """Base class for expected application errors."""

    def __init__(
        self,
        code: str,
        user_message: str,
        *,
        technical_message: str | None = None,
        retryable: bool = False,
        severity: "ErrorSeverity" = ErrorSeverity.ERROR,
        context: dict[str, object] | None = None,
    ) -> None:
        super().__init__(technical_message or user_message)
        self.code = code
        self.user_message = user_message
        self.technical_message = technical_message
        self.retryable = retryable
        self.severity = severity
        self.context = context or {}
```

Expected application errors shall inherit from this class.

Unexpected programming exceptions shall remain distinguishable from expected business errors.

---

# Chapter 1005 — Exception Subclasses

Recommended hierarchy:

```text
BlueBubblesError
│
├── ValidationError
├── AuthenticationError
│   ├── InvalidCredentialsError
│   ├── SessionExpiredError
│   ├── InvalidTokenError
│   └── AccountDisabledError
│
├── AuthorisationError
├── ResourceNotFoundError
├── ConflictError
├── RateLimitError
├── NetworkError
├── DependencyError
│   ├── DirectoryUnavailableError
│   ├── DatabaseUnavailableError
│   ├── RedisUnavailableError
│   └── StorageUnavailableError
│
├── RepositoryError
├── StorageError
├── CryptographyError
├── ProtocolError
├── FileTransferError
├── LocalStorageError
├── ConfigurationError
├── WorkerError
└── InternalApplicationError
```

Subclasses may add structured fields relevant to their domain.

---

# Chapter 1006 — Error Severity

```python
class ErrorSeverity(StrEnum):
    """Defines the operational severity of an error."""

    INFORMATIONAL = "informational"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
```

Examples:

```text
Cancelled transfer:

INFORMATIONAL

Temporary network loss:

WARNING

Database transaction failure:

ERROR

Audit-chain failure:

CRITICAL
```

Severity does not automatically determine whether an error is retryable.

---

# Chapter 1007 — Retry Classification

```python
class RetryClassification(StrEnum):
    """Defines whether and how an operation may be retried."""

    NEVER = "never"
    IMMEDIATE_ONCE = "immediate_once"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    RETRY_AFTER = "retry_after"
    USER_ACTION_REQUIRED = "user_action_required"
```

The retry classification shall be explicit.

The application shall not infer retry behaviour solely from a generic exception type.

---

# Chapter 1008 — Retryable Errors

Normally retryable:

```text
Connection timeout
Temporary DNS or LAN failure
Connection reset
HTTP 502
HTTP 503
HTTP 504
Redis temporarily unavailable
Temporary storage lock
Rate limit with retry-after value
WebSocket interruption
Temporary LDAP outage
```

A retry is only appropriate when the operation is safe and idempotent.

---

# Chapter 1009 — Non-Retryable Errors

Normally non-retryable:

```text
Invalid credentials
Permission denied
Account disabled
Unsupported protocol
Malformed request
Invalid signature
Invalid authentication tag
Conversation deleted
User removed from group
File type blocked
Message edit window expired
Conflicting idempotency identifier
```

These errors require user action, data correction or administrative intervention.

---

# Chapter 1010 — Retry Safety

Before retrying, the application shall determine whether the operation is idempotent.

Safe examples:

```text
GET request
Message send using fixed message UUID
Repeated identical chunk upload
Session refresh using protected rotation logic
Read-receipt update
Download chunk
```

Unsafe operations shall either:

* Use an idempotency key.
* Be redesigned transactionally.
* Require confirmation before retry.
* Not retry automatically.

---

# Chapter 1011 — Error Code Format

Stable error codes shall use uppercase words separated by underscores.

Examples:

```text
INVALID_CREDENTIALS
PERMISSION_DENIED
CONVERSATION_NOT_FOUND
MESSAGE_CONFLICT
DATABASE_UNAVAILABLE
UPLOAD_SESSION_EXPIRED
LOCAL_DATABASE_CORRUPT
UNSUPPORTED_PROTOCOL
```

Codes shall describe the condition rather than the internal exception class.

---

# Chapter 1012 — Error Code Stability

Once released, an error code shall not change meaning.

A new condition shall receive a new code.

Clients may map error codes to:

* User-facing messages.
* Recovery actions.
* Retry behaviour.
* Helpdesk guidance.
* Telemetry categories.

Internal Python class names may change without breaking clients.

---

# Chapter 1013 — API Error Envelope

Every REST API error shall use a common structure.

```python
class ApiErrorResponse(BaseModel):
    """Represents a safe structured REST API error."""

    success: bool = False
    error: "ApiErrorDetail"
    correlation_id: UUID
    timestamp: datetime
```

```python
class ApiErrorDetail(BaseModel):
    """Contains the client-safe details of one API failure."""

    code: str
    message: str
    retryable: bool
    retry_after_seconds: int | None = None
    field_errors: list["FieldError"] = []
```

---

# Chapter 1014 — Field Validation Errors

```python
class FieldError(BaseModel):
    """Describes one invalid request field."""

    field: str
    code: str
    message: str
```

Example:

```json
{
    "field": "title",
    "code": "VALUE_TOO_LONG",
    "message": "The group name must not exceed 100 characters."
}
```

Field errors shall not echo sensitive submitted values.

---

# Chapter 1015 — Example API Error

```json
{
    "success": false,
    "error": {
        "code": "NOT_CONVERSATION_MEMBER",
        "message": "You no longer have access to this conversation.",
        "retryable": false,
        "retry_after_seconds": null,
        "field_errors": []
    },
    "correlation_id": "a73d4d13-e978-4bd6-b443-aee18c26d171",
    "timestamp": "2026-07-16T17:00:00Z"
}
```

Internal stack traces shall not appear in the response.

---

# Chapter 1016 — HTTP Status Mapping

Recommended mappings:

| Error Category          | HTTP Status |
| ----------------------- | ----------: |
| Validation              |  400 or 422 |
| Invalid authentication  |         401 |
| Permission denied       |         403 |
| Missing resource        |         404 |
| Locked account          |         423 |
| Conflict                |         409 |
| Payload too large       |         413 |
| Rate limited            |         429 |
| Dependency unavailable  |         503 |
| Unexpected server error |         500 |

The same application code shall map consistently to the same status.

---

# Chapter 1017 — 401 and 403 Distinction

Use:

```text
401 Unauthorized
```

when authentication is missing, invalid or expired.

Use:

```text
403 Forbidden
```

when the user is authenticated but lacks permission.

This distinction shall remain consistent across all endpoints.

---

# Chapter 1018 — WebSocket Error Envelope

WebSocket failures shall use a structured event.

```json
{
    "event_id": "uuid",
    "event_type": "error",
    "protocol_version": 1,
    "timestamp": "2026-07-16T17:00:00Z",
    "correlation_id": "uuid",
    "data": {
        "code": "PERMISSION_DENIED",
        "message": "You cannot perform this action.",
        "retryable": false,
        "request_event_id": "uuid"
    }
}
```

The request event identifier links the error to the initiating client event.

---

# Chapter 1019 — WebSocket Close Codes

Standard close codes shall be used where possible.

Recommended use:

```text
1000

Normal closure

1001

Server shutdown or endpoint going away

1008

Policy violation or unauthorised action

1009

Message too large

1011

Unexpected server condition
```

Application-specific meaning shall be placed in the structured final event where possible.

---

# Chapter 1020 — Correlation Identifiers

Every important operation shall receive a correlation identifier.

A correlation ID shall be:

* A UUID.
* Generated at the first trusted boundary.
* Propagated through services.
* Included in structured logs.
* Included in safe error responses.
* Included in durable events where relevant.
* Included in background jobs derived from the operation.

Clients may submit an identifier, but the server shall validate or replace malformed values.

---

# Chapter 1021 — Correlation Context

```python
class CorrelationContext:
    """Stores trace identifiers for the current operation."""

    correlation_id: UUID
    request_id: UUID | None
    session_id: UUID | None
    user_id: UUID | None
```

Context variables may be used to propagate correlation data through asynchronous code.

---

# Chapter 1022 — Correlation Middleware

The middleware shall:

```text
Read X-Correlation-ID header if valid

↓

Generate UUID if missing or invalid

↓

Store identifier in request context

↓

Add identifier to response header

↓

Add identifier to logs

↓

Include identifier in error response
```

Response header:

```text
X-Correlation-ID
```

---

# Chapter 1023 — Error Context

Technical error context may include:

```text
Component name
Operation name
Resource identifier
User identifier
Session identifier
Retry attempt
Dependency state
Correlation identifier
```

It shall not include:

```text
Password
Raw token
Private key
Message plaintext
Attachment plaintext
LDAP bind secret
Database password
```

---

# Chapter 1024 — Exception Translation

Infrastructure exceptions shall be translated before reaching API handlers.

Example:

```text
asyncpg connection exception

↓

Repository catches infrastructure exception

↓

Raises DatabaseUnavailableError

↓

Global handler maps to:

503 DATABASE_UNAVAILABLE
```

Clients shall not depend upon database-library exception names.

---

# Chapter 1025 — Repository Error Translation

Repositories shall translate:

```text
Unique constraint violation
Foreign key violation
Connection failure
Statement timeout
Transaction failure
```

into domain-appropriate repository exceptions.

Business services may then translate those into application errors.

Example:

```text
Unique direct-conversation constraint violation

↓

Existing conversation lookup

↓

Return existing conversation
```

Not every database exception should become a generic 500 response.

---

# Chapter 1026 — Global Server Exception Handler

The global handler shall:

* Recognise expected application errors.
* Select the correct HTTP status.
* Return the common error envelope.
* Record appropriate logs.
* Increment error metrics.
* Avoid duplicate logging.
* Handle unexpected exceptions safely.

Unexpected exceptions shall receive:

```text
INTERNAL_SERVER_ERROR
```

---

# Chapter 1027 — Unexpected Server Errors

User-facing response:

```text
BlueBubbles could not complete the request because of an unexpected server error.

Try again. If the problem continues, provide the error reference to the helpdesk.
```

The response shall include a correlation ID.

The server log shall include the traceback after sanitisation.

---

# Chapter 1028 — Client Error Model

```python
class ClientError:
    """Represents an error ready for client handling and display."""

    code: str
    title: str
    message: str
    severity: ErrorSeverity
    retryable: bool
    suggested_action: str | None
    correlation_id: UUID | None
    technical_details_available: bool
```

ViewModels shall expose client errors rather than raw exceptions.

---

# Chapter 1029 — Error Presentation Levels

The client shall use different presentation styles.

```text
Inline validation message

Used beside a form field.

Toast notification

Used for brief non-critical failures.

Banner

Used for connection or degraded-service state.

Dialog

Used for actions requiring user acknowledgement.

Dedicated error page

Used for startup, storage or unrecoverable application failure.
```

The severity and required user action shall determine the presentation.

---

# Chapter 1030 — User-Facing Error Language

Messages shall:

* Use plain English.
* Explain what failed.
* Explain whether data was saved.
* Give one useful next action.
* Avoid blame.
* Avoid internal jargon.
* Include a technical code where helpful.

Poor message:

```text
AsyncOperationException: connection refused.
```

Preferred message:

```text
BlueBubbles cannot reach the server.

Your unsent message has been kept and will be retried when the connection returns.

Error code: NETWORK_UNAVAILABLE
```

---

# Chapter 1031 — Error Titles

Recommended titles:

```text
Unable to connect
Message not sent
Upload interrupted
Session expired
Access denied
Local cache problem
Server unavailable
File could not be verified
Application configuration error
```

Titles shall describe the effect rather than the internal cause.

---

# Chapter 1032 — Error Message Ownership

The server shall provide a safe default message.

The client may replace it with a more suitable localised message based on the stable error code.

The client shall not replace an error with wording that changes its meaning.

Example:

```text
Server code:

ACCOUNT_DISABLED

Client message:

This account has been disabled. Contact the helpdesk.
```

---

# Chapter 1033 — ErrorMessageCatalog

```python
class ErrorMessageCatalog:
    """Maps stable error codes to user-facing client content."""

    def get_message(
        self,
        code: str,
        context: ErrorDisplayContext,
    ) -> ClientError:
        ...
```

Unknown error codes shall use a safe generic fallback while preserving the code for diagnostics.

---

# Chapter 1034 — Error Localisation

Error codes shall remain language-independent.

Display strings may later be localised.

The server shall not require clients to parse English text.

Version 1.0 may support English only, but the structure shall not prevent future localisation.

---

# Chapter 1035 — Form Validation Behaviour

Client-side form validation shall:

* Display errors near the affected field.
* Preserve user input except secrets after failed submission.
* Focus the first invalid field.
* Prevent duplicate submission.
* Avoid network calls for clearly invalid input.

Server validation shall still remain authoritative.

---

# Chapter 1036 — Password Error Handling

Passwords shall be cleared after:

```text
Invalid login
Directory error
Unexpected authentication failure
Window closure
```

The client may keep the username.

The password shall never appear in the returned validation error.

---

# Chapter 1037 — Transaction Failure Behaviour

If a transactional operation fails:

```text
Roll back the transaction

↓

Do not publish success event

↓

Do not update client state as successful

↓

Return structured error

↓

Preserve retryable client input

↓

Log correlation identifier
```

No partial business state shall remain unless the workflow explicitly supports partial progress.

---

# Chapter 1038 — Message Failure Behaviour

If a message send fails before server acknowledgement:

* Keep the local message item.
* Mark it failed or pending.
* Preserve the message UUID.
* Preserve the draft source where possible.
* Classify the error.
* Retry only if safe.
* Allow manual retry.
* Never display it as stored.

---

# Chapter 1039 — Attachment Failure Behaviour

If an upload fails:

* Preserve completed encrypted chunks where resumable.
* Preserve upload-session information.
* Remove incomplete plaintext temporary data.
* Display the failed chunk or stage where useful.
* Retry only missing chunks.
* Avoid restarting the entire transfer unnecessarily.

If final checksum verification fails, the attachment shall not become complete.

---

# Chapter 1040 — Session Error Behaviour

When an access token expires:

```text
Pause protected request

↓

Attempt one refresh

↓

Retry original request once after successful refresh
```

If refresh fails:

```text
Stop protected operations

↓

Preserve drafts and queues

↓

Clear invalid session secrets

↓

Return to login
```

The client shall avoid multiple simultaneous refresh requests.

---

# Chapter 1041 — Refresh Coordination

```python
class TokenRefreshCoordinator:
    """Ensures that only one token refresh occurs at a time."""

    async def refresh_if_required(self) -> RefreshResult:
        ...

    async def wait_for_active_refresh(self) -> RefreshResult:
        ...
```

Other requests shall wait for the existing refresh result.

This prevents refresh-token reuse caused by concurrent rotation attempts.

---

# Chapter 1042 — Network Timeout Classes

Separate timeout types shall be recognised:

```text
Connection timeout
Read timeout
Write timeout
Pool timeout
WebSocket heartbeat timeout
```

Different timeouts may require different recovery behaviour.

A read timeout during an idempotent request may be retried.

A write timeout during a non-idempotent request requires idempotency verification.

---

# Chapter 1043 — Retry Policy

```python
class RetryPolicy:
    """Defines bounded retry behaviour for one operation category."""

    maximum_attempts: int
    initial_delay_seconds: float
    maximum_delay_seconds: float
    multiplier: float
    jitter_ratio: float
    retryable_codes: set[str]
```

Policies shall be defined by operation type.

---

# Chapter 1044 — Exponential Backoff

Recommended delays:

```text
Attempt 1:

2 seconds

Attempt 2:

4 seconds

Attempt 3:

8 seconds

Attempt 4:

16 seconds

Later attempts:

Maximum 30 seconds
```

Random jitter shall be applied.

This prevents many clients from retrying simultaneously after a server restart.

---

# Chapter 1045 — Retry Limits

Suggested automatic retry limits:

```text
Ordinary REST request:

3 attempts

Message send:

Until permanent failure or queue policy expiry

Chunk upload:

3 attempts per chunk before transfer pause

Chunk download:

3 attempts per chunk

WebSocket reconnect:

Continues with bounded interval while application is open

LDAP bind inside one login request:

No repeated credential bind beyond controlled policy
```

Retries shall not bypass rate limiting.

---

# Chapter 1046 — Retry-After Handling

For HTTP 429 or temporary maintenance responses, the server may return:

```text
Retry-After
```

The client shall respect the server value within configured safety bounds.

The user shall see a clear state such as:

```text
Waiting before retrying…
```

---

# Chapter 1047 — Circuit Breaker Purpose

A circuit breaker prevents repeated calls to a failing dependency.

Suitable dependencies:

```text
Active Directory
Redis
PostgreSQL health probes
Attachment storage
Internal event publisher
```

It shall not replace ordinary health checks.

---

# Chapter 1048 — Circuit Breaker States

```python
class CircuitState(StrEnum):
    """Defines the current state of a circuit breaker."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"
```

Meaning:

```text
CLOSED

Requests operate normally.

OPEN

Requests fail quickly without calling the dependency.

HALF_OPEN

A limited test request checks whether the dependency recovered.
```

---

# Chapter 1049 — CircuitBreaker

```python
class CircuitBreaker:
    """Prevents repeated calls to a failing dependency."""

    async def execute(
        self,
        operation: Callable[..., Awaitable[ResultType]],
    ) -> ResultType:
        ...

    def record_success(self) -> None:
        ...

    def record_failure(self) -> None:
        ...
```

Configuration:

```text
Failure threshold
Open duration
Half-open test count
Failure categories
```

---

# Chapter 1050 — Circuit Breaker Rules

A circuit shall open only for dependency or infrastructure failures.

It shall not open because of:

```text
Invalid password
Permission denied
Missing resource
Request validation error
```

These are user or business outcomes, not dependency failures.

---

# Chapter 1051 — Service Degradation

BlueBubbles shall continue operating with reduced functionality where safe.

Examples:

```text
Redis unavailable:

Messages may continue through PostgreSQL.
Presence and typing indicators may be unavailable.

Attachment storage unavailable:

Text messaging may continue.
File upload and download are disabled.

Active Directory unavailable:

Existing sessions may continue according to policy.
New directory logins fail.

Search index unavailable:

Messaging continues.
Local search is disabled.
```

---

# Chapter 1052 — Degraded Capability Model

```python
class CapabilityState(BaseModel):
    """Describes whether one application capability is available."""

    capability: str
    available: bool
    degraded: bool
    reason_code: str | None
    message: str | None
    checked_at: datetime
```

The client may use these states to disable affected controls.

---

# Chapter 1053 — Degraded Service Banner

Example:

```text
File transfers are temporarily unavailable.

Text messaging is still working. BlueBubbles will restore file transfers automatically when server storage becomes available.
```

The banner shall not imply that the entire system is offline when only one capability failed.

---

# Chapter 1054 — Dependency Recovery

When a failed dependency recovers:

```text
Circuit enters half-open state

↓

Health check succeeds

↓

Circuit closes

↓

Capability becomes available

↓

Alert is updated

↓

Clients receive capability-restored event where useful
```

Recovery shall be logged once rather than for every successful request.

---

# Chapter 1055 — Error Deduplication

Repeated identical errors shall be grouped.

Deduplication key may include:

```text
Error code
Component
Resource type
Dependency
Time window
```

This reduces:

* Log flooding.
* Repeated alerts.
* Duplicate dialogs.
* Excessive metrics.

---

# Chapter 1056 — Client Notification Deduplication

The client shall avoid showing the same connection error repeatedly.

Example:

```text
First failure:

Show banner.

Continued failures:

Update banner state silently.

Recovery:

Show brief restored notification.
```

One failing queued message may still have its own visible state.

---

# Chapter 1057 — Error Metrics

Metrics shall include:

```text
Errors by code
Errors by component
Retry attempts
Retry successes
Retry exhaustion
Circuit-breaker openings
Dependency failures
Unexpected exceptions
Client crash count
Worker failure count
```

Metric labels shall avoid high-cardinality values such as raw message IDs.

---

# Chapter 1058 — Logging Levels

Recommended mapping:

```text
DEBUG

Detailed development flow without secrets

INFO

Normal lifecycle and successful significant operations

WARNING

Recoverable or degraded condition

ERROR

Operation failed or data could not be processed

CRITICAL

System integrity or essential service failure
```

Expected user validation errors normally do not require ERROR-level logging.

---

# Chapter 1059 — Single-Point Error Logging

Each error shall be logged at the layer with enough context to handle it properly.

The same exception shall not be logged repeatedly by:

```text
Repository
Service
Router
Global handler
```

Recommended approach:

* Lower layers add structured context or translate exceptions.
* The boundary handler performs final logging.
* Critical security events may also create audit or alert records.

---

# Chapter 1060 — Traceback Policy

Tracebacks shall be recorded for:

```text
Unexpected exceptions
Programming defects
Unhandled worker failures
Unexpected dependency-library failures
```

Tracebacks are usually unnecessary for:

```text
Invalid credentials
Permission denied
Expected validation failure
Known message conflict
User-cancelled transfer
```

This keeps logs useful.

---

# Chapter 1061 — Sensitive Traceback Sanitisation

Tracebacks and local variables may contain secrets.

The error logger shall:

* Avoid dumping complete request bodies.
* Avoid serialising stack-frame locals automatically.
* Redact secret-aware values.
* Remove authorisation headers.
* Remove password fields.
* Avoid logging decrypted payloads.
* Limit exception argument output where necessary.

---

# Chapter 1062 — Diagnostic Logging Context

Recommended fields:

```text
timestamp
level
error_code
component
operation
correlation_id
request_id
user_id
session_id
retry_attempt
dependency
duration_ms
```

Resource identifiers may be included when necessary and permitted.

---

# Chapter 1063 — Client Log Files

Client logs may include:

```text
client.log
network.log
storage.log
transfer.log
security.log
```

Logs shall be stored under the user-specific application directory.

They shall rotate and remain bounded.

---

# Chapter 1064 — Server Log Files

Server logs may include:

```text
application.log
authentication.log
security.log
database.log
websocket.log
file_transfer.log
worker.log
performance.log
```

The log configuration defined in Part 14 remains authoritative.

---

# Chapter 1065 — Diagnostic Package Purpose

A diagnostic package allows a user or helpdesk technician to collect relevant troubleshooting information without manually locating files.

The package shall exclude sensitive message and key material.

---

# Chapter 1066 — Diagnostic Package Contents

Possible contents:

```text
Sanitised client logs
Application version
Protocol version
Operating-system version
Client configuration summary
Server hostname
Connection test results
Local storage health
Cache-size summary
Recent error codes
Transfer failure metadata
Certificate fingerprint
```

It shall not contain:

```text
Passwords
Tokens
Private keys
Message plaintext
Attachment plaintext
Draft text
Full local database
Search terms
```

---

# Chapter 1067 — DiagnosticPackageService

```python
class DiagnosticPackageService:
    """Creates a sanitised local troubleshooting archive."""

    async def create_package(
        self,
        options: DiagnosticPackageOptions,
    ) -> Path:
        ...

    async def validate_package(
        self,
        path: Path,
    ) -> DiagnosticPackageValidation:
        ...
```

The package shall be created only after explicit user action.

---

# Chapter 1068 — Diagnostic Package Format

Recommended format:

```text
ZIP archive
```

Example structure:

```text
bluebubbles-diagnostics/
├── summary.json
├── connection-tests.json
├── errors.json
├── logs/
│   ├── client.log
│   └── network.log
└── storage-health.json
```

The filename shall include a timestamp but not the user’s password or token.

---

# Chapter 1069 — Diagnostic Package Review

Before saving, the client may show:

```text
This package contains technical logs and device information.

It does not include message contents, passwords, private keys or attachment contents.
```

The user shall choose where to save it.

The application shall not upload it automatically.

---

# Chapter 1070 — Server Diagnostic Report

Administrators may run a server diagnostic report.

Checks may include:

```text
Configuration validity
Database connectivity
Redis connectivity
Directory connectivity
Storage access
Audit-chain health
Worker state
TLS certificate expiry
Backup status
```

The report shall redact credentials and secrets.

---

# Chapter 1071 — Crash Handling Purpose

An unexpected client or server crash shall:

* Preserve diagnostic information.
* Avoid exposing secrets.
* Avoid corrupting persistent data.
* Permit restart recovery.
* Inform the user or administrator clearly.
* Never claim that data was saved unless confirmed.

---

# Chapter 1072 — Client Crash Handler

```python
class ClientCrashHandler:
    """Captures unexpected client exceptions at the application boundary."""

    def install(self) -> None:
        ...

    def handle_exception(
        self,
        exception_type: type[BaseException],
        exception: BaseException,
        traceback_object: TracebackType,
    ) -> None:
        ...
```

It shall integrate with Python and Qt exception boundaries where practical.

---

# Chapter 1073 — Client Crash Behaviour

On an unrecoverable client exception:

```text
Stop dangerous ongoing writes

↓

Attempt to preserve drafts and transfer state

↓

Write sanitised crash record

↓

Close local database safely where possible

↓

Show crash dialog

↓

Offer restart
```

A crash handler shall not continue normal operation after unknown state corruption.

---

# Chapter 1074 — Client Crash Dialog

Example:

```text
BlueBubbles encountered an unexpected problem and must close.

Your saved drafts and transfer progress have been preserved where possible.

Error reference:
4d8c9504-ec52-46c5-bf56-8a5335ea6ef1
```

Actions:

```text
Restart BlueBubbles
Create diagnostic package
Close
```

---

# Chapter 1075 — Server Crash Behaviour

Unexpected server process termination shall rely on:

* PostgreSQL transaction durability.
* Idempotent client retries.
* Transactional outbox recovery.
* Resumable upload state.
* systemd restart policy.
* Structured crash logs.

The server shall not attempt to keep running after a fatal process-level failure.

---

# Chapter 1076 — Crash Reporting Without External Services

BlueBubbles is LAN-only.

Therefore, crash reports shall be:

```text
Stored locally
Available through diagnostic exports
Visible to administrators
Not uploaded to an external analytics provider
```

No external crash-reporting service shall be required.

---

# Chapter 1077 — Crash Record Model

```python
class CrashRecord:
    """Stores sanitised information about an unexpected process failure."""

    crash_id: UUID
    application_component: str
    application_version: str
    timestamp: datetime
    exception_type: str
    sanitised_message: str
    traceback_reference: str | None
    correlation_id: UUID | None
    recovered_state: dict[str, bool]
```

Crash records shall not include full memory dumps.

---

# Chapter 1078 — Recovery Modes

The client may support:

```text
Normal startup
Safe startup
Cache rebuild
Configuration reset
Offline diagnostic mode
```

The server may support:

```text
Normal startup
Configuration validation
Migration-only mode
Diagnostic mode
Audit verification mode
```

---

# Chapter 1079 — Client Safe Startup

Safe startup shall:

* Disable optional plugins or experimental features.
* Avoid opening the previous active conversation automatically.
* Delay transfer resumption.
* Use default appearance settings.
* Open local storage read-only initially where practical.
* Allow diagnostics and cache rebuild.

Version 1.0 may implement a simplified safe mode.

---

# Chapter 1080 — Cache Rebuild Recovery

If replaceable cache data is corrupt:

```text
Preserve drafts and offline actions

↓

Export diagnostic record

↓

Delete replaceable message and profile cache

↓

Retain protected credentials where safe

↓

Reconnect to server

↓

Re-download authorised data

↓

Rebuild search index
```

The user shall be told which local items could not be recovered.

---

# Chapter 1081 — Draft Recovery

After abnormal shutdown:

* Load saved drafts.
* Detect incomplete autosave transactions.
* Choose the newest valid draft version.
* Keep drafts linked to existing conversations.
* Mark drafts unavailable if the user lost conversation access.
* Never submit recovered drafts automatically.

---

# Chapter 1082 — Offline Queue Recovery

After restart:

```text
Load pending actions

↓

Verify local payload integrity

↓

Verify session state

↓

Refresh conversation membership

↓

Resume safe processing

↓

Leave permanent failures visible
```

A corrupted queue item shall not prevent other valid items from processing.

---

# Chapter 1083 — Transfer Recovery

Uploads and downloads shall resume from confirmed chunk state.

If recovery data conflicts with server state:

```text
Server-confirmed completed chunks win.

Local unconfirmed upload chunks may be retried.

Completed attachment state wins over local pending state.

Checksum mismatch stops recovery.
```

---

# Chapter 1084 — Database Recovery

For PostgreSQL failure:

* Roll back incomplete transactions.
* Reconnect with bounded backoff.
* Verify migration state after extended outage if necessary.
* Reprocess unpublished outbox events.
* Reconcile worker state.
* Mark readiness healthy only after checks pass.

---

# Chapter 1085 — Redis Recovery

After Redis reconnects:

```text
Recreate connection pool

↓

Restore namespace access

↓

Rebuild presence from active WebSockets

↓

Resume Pub/Sub subscriptions

↓

Resume transient rate limiting

↓

Clear degraded status
```

Expired typing state does not need recovery.

---

# Chapter 1086 — Storage Recovery

After attachment storage returns:

* Verify root access.
* Verify free capacity.
* Reconcile temporary uploads.
* Check completed attachment references.
* Resume valid transfers.
* Mark missing completed files as integrity failures.
* Clear degraded capability only after verification.

---

# Chapter 1087 — Active Directory Recovery

After directory recovery:

```text
Close directory circuit breaker

↓

Permit new login attempts

↓

Resume scheduled synchronisation

↓

Revalidate affected account states

↓

Invalidate sessions for newly disabled users

↓

Clear directory outage alert
```

Existing sessions shall follow configured policy.

---

# Chapter 1088 — Worker Failure Handling

A worker failure shall:

* Mark the worker failed.
* Record the error.
* Increment failure count.
* Retry according to worker policy.
* Avoid overlapping duplicate runs.
* Create an alert after repeated failure.
* Remain visible in administration.

Critical workers may affect readiness.

---

# Chapter 1089 — Worker Retry Policy

Recommended:

```text
First failure:

Retry after 30 seconds

Second failure:

Retry after 2 minutes

Third failure:

Retry after 10 minutes

Repeated failure:

Remain failed and alert administrator
```

The exact policy shall be configurable per worker.

---

# Chapter 1090 — Poison Work Items

A poison work item repeatedly fails while other work is valid.

Examples:

```text
One invalid outbox event
One corrupt export job
One malformed cleanup record
```

The worker shall:

* Limit retries for that item.
* Mark it failed.
* Continue processing other items where safe.
* Create an alert.
* Preserve diagnostic metadata.

---

# Chapter 1091 — Outbox Publication Failure

If an outbox event cannot be published:

* Leave it unpublished.
* Increment attempt count.
* Set next retry time.
* Preserve the committed business record.
* Avoid creating duplicate outbox rows.
* Alert after threshold.
* Use event ID for recipient deduplication.

---

# Chapter 1092 — Partial Event Delivery

If an event reaches some recipient sessions but not others:

* The message remains stored.
* The outbox event may be considered published to the event system.
* Disconnected clients recover through synchronisation.
* Connected delivery failures are logged.
* The server does not roll back the stored message.

Real-time notification is not the permanent source of truth.

---

# Chapter 1093 — Error Recovery State Machine

Operations with complex recovery shall use explicit states.

Example transfer state machine:

```text
QUEUED

↓

RUNNING

↓

WAITING_RETRY

↓

RUNNING

↓

COMPLETE
```

Possible terminal states:

```text
FAILED
CANCELLED
EXPIRED
```

State transitions shall be validated.

---

# Chapter 1094 — State Transition Validation

Incorrect transitions shall be rejected.

Examples:

```text
COMPLETE → RUNNING

Rejected

CANCELLED → COMPLETE

Rejected

WAITING_RETRY → RUNNING

Allowed
```

A shared state-machine helper may be used.

---

# Chapter 1095 — Error Recovery Audit Events

Security or administrative recovery actions shall be audited.

Examples:

```text
Session invalidated after token reuse
Audit verification failed
Storage restored
Administrator retried worker
Configuration restored
Data export failed
Cache recovery initiated by user
```

Ordinary client network retries do not require permanent audit events.

---

# Chapter 1096 — Recovery User Confirmation

User confirmation is required when recovery may:

* Remove local cache.
* Discard a draft.
* Cancel a transfer.
* Replace an existing downloaded file.
* Reset configuration.
* Log the user out.
* Delete local keys.

Automatic recovery shall be used only when it cannot cause meaningful data loss.

---

# Chapter 1097 — Error Help Codes

Selected errors may include a help code.

Example:

```text
NETWORK_UNAVAILABLE
Help code: NET-001
```

Helpdesk documentation may map the code to:

* Meaning.
* Likely cause.
* User checks.
* Administrator checks.
* Relevant logs.

Stable machine error codes remain authoritative.

---

# Chapter 1098 — Self-Diagnostic Error Mapping

Examples:

```text
NETWORK_UNAVAILABLE

Check server reachability and LAN connection.

TLS_CERTIFICATE_INVALID

Check certificate trust and hostname.

LOCAL_DATABASE_CORRUPT

Offer local cache rebuild.

DIRECTORY_UNAVAILABLE

Check Active Directory connectivity.

SERVER_STORAGE_FULL

Check attachment storage capacity.
```

The diagnostic tool shall not reveal protected server values.

---

# Chapter 1099 — Error Documentation

Every public error code shall document:

```text
Code
Meaning
Likely cause
Retry classification
HTTP status
User-facing message
Suggested user action
Suggested administrator action
Relevant component
```

Documentation shall be generated or validated against the code catalogue where practical.

---

# Chapter 1100 — ErrorCode Enum

```python
class ErrorCode(StrEnum):
    """Defines stable machine-readable application errors."""

    INVALID_REQUEST = "INVALID_REQUEST"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    SESSION_EXPIRED = "SESSION_EXPIRED"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    NETWORK_UNAVAILABLE = "NETWORK_UNAVAILABLE"
    DATABASE_UNAVAILABLE = "DATABASE_UNAVAILABLE"
    REDIS_UNAVAILABLE = "REDIS_UNAVAILABLE"
    STORAGE_UNAVAILABLE = "STORAGE_UNAVAILABLE"
    CRYPTOGRAPHIC_VERIFICATION_FAILED = (
        "CRYPTOGRAPHIC_VERIFICATION_FAILED"
    )
    UNSUPPORTED_PROTOCOL = "UNSUPPORTED_PROTOCOL"
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
```

Domain-specific modules may define additional codes in one central catalogue.

---

# Chapter 1101 — Error Catalogue Validation

Automated tests shall verify:

* Every public exception has an error code.
* Every error code has a display message.
* Every error code has retry classification.
* Every error code maps to one HTTP status where relevant.
* No duplicate code has conflicting meaning.
* Documentation includes every public code.

---

# Chapter 1102 — Error Privacy

Error messages shall not reveal:

```text
Whether an unrelated username exists
Database table names
Filesystem paths
Internal IP topology
LDAP distinguished names
Private-key fingerprints unnecessarily
Raw SQL
Stack traces
Server secrets
```

Authorised administrators may receive additional diagnostic context through protected tools.

---

# Chapter 1103 — Authentication Enumeration Protection

For login failures, use one general message:

```text
The username or password is incorrect.
```

Internal logs may distinguish:

```text
Unknown user
Incorrect password
Disabled directory account
Directory lookup failure
```

Access to those details shall be restricted.

---

# Chapter 1104 — Resource Enumeration Protection

When appropriate, unauthorised access to a resource may return:

```text
404 Not Found
```

instead of confirming that the resource exists.

This is suitable when revealing existence would create a privacy risk.

The decision shall be consistent per endpoint.

---

# Chapter 1105 — Error Rate Limiting

Repeated invalid requests may themselves be rate-limited.

Examples:

```text
Invalid login attempts
Invalid WebSocket events
Repeated unauthorised attachment requests
Malformed protocol frames
```

The response shall remain safe and shall not amplify an attack with expensive processing.

---

# Chapter 1106 — Client Startup Errors

Startup failures may include:

```text
Invalid installation configuration
Secure store unavailable
Local database key unavailable
Local database corrupt
Migration failure
Unsupported operating system
Missing required dependency
```

The client shall show a dedicated recovery page rather than a blank window.

---

# Chapter 1107 — Server Startup Errors

Startup failures may include:

```text
Invalid production configuration
Database unavailable
Migration mismatch
Storage inaccessible
Token secret invalid
Authentication provider misconfigured
Audit writer unavailable
TLS file invalid
```

The process shall exit non-zero after cleanup.

---

# Chapter 1108 — Startup Error Report

The console or service log shall show:

```text
Component
Error code
Safe description
Configuration path where applicable
Corrective action
Correlation or startup identifier
```

Secrets shall remain redacted.

---

# Chapter 1109 — Migration Failure Recovery

If a server migration fails:

* Stop startup.
* Roll back the migration transaction where supported.
* Preserve the database.
* Log the migration revision.
* Require administrator intervention.
* Do not automatically delete or recreate production tables.

If a local client-cache migration fails, replaceable cache may be rebuilt after drafts and queues are preserved.

---

# Chapter 1110 — Configuration Recovery

The client may offer:

```text
Restore previous configuration
Reset non-sensitive settings
Choose new server address
Open diagnostic mode
```

The server shall require configuration changes through files, environment values or authorised administration.

It shall not guess missing production secrets.

---

# Chapter 1111 — Logging Failure

If file logging fails:

* Attempt console or system journal logging.
* Mark health degraded.
* Avoid terminating messaging immediately if safe.
* Create an administrator alert.
* Never write sensitive data to an insecure fallback file.

Audit logging failure is more serious and may require rejecting high-impact operations.

---

# Chapter 1112 — Audit Write Failure

For operations requiring audit records, the preferred policy is:

```text
Business change and audit insert occur in one transaction.
```

If the audit insert fails:

```text
Roll back the business change.
```

This applies particularly to:

```text
Account disabling
Role changes
Group administration
Message deletion
Configuration changes
Data exports
```

Low-risk transient actions may use a separate policy if documented.

---

# Chapter 1113 — Security Verification Failure

If a signature or authentication tag fails:

* Reject the content.
* Do not display it as trusted.
* Do not retry decryption with guessed parameters.
* Log a security event.
* Avoid exposing key material.
* Allow retrieval of a corrected server record if one exists.
* Alert administrators after repeated failures.

---

# Chapter 1114 — Cryptographic Failure Messages

User-facing message:

```text
This message could not be verified and has not been displayed.

The message may be damaged or was created with an unsupported key.
```

The interface shall not display partially decrypted data.

---

# Chapter 1115 — Recovery Data Integrity

All recovery records shall include integrity protection where necessary.

Examples:

```text
Offline queue payload
Transfer manifest
Draft record
Cached decrypted payload
Diagnostic package manifest
```

If integrity verification fails, the record shall be quarantined rather than trusted.

---

# Chapter 1116 — Quarantine Storage

Corrupt local recovery items may be moved to:

```text
BlueBubbles/
└── recovery/
    └── quarantine/
```

Quarantined items shall:

* Remain encrypted.
* Use server-generated or client-generated identifiers.
* Be excluded from normal processing.
* Be removable through settings.
* Be described in diagnostics without exposing content.

---

# Chapter 1117 — Time Synchronisation Errors

Large clock differences may affect:

* Token validity.
* Certificate validity.
* Message timestamps.
* Retry scheduling.
* Audit display.

The server shall remain authoritative for security-sensitive time.

If client time differs significantly, display:

```text
Your computer’s clock appears to be incorrect.

Correct the date and time before signing in.
```

---

# Chapter 1118 — Version Compatibility Errors

When protocol versions do not overlap:

```text
Return UNSUPPORTED_PROTOCOL

Provide server version

Provide minimum client version

Do not attempt undefined fallback
```

The client shall direct the user to the approved internal update source.

---

# Chapter 1119 — Resource Exhaustion

The application shall detect:

```text
Low memory
Disk full
Database pool exhaustion
Too many WebSocket connections
Too many queued transfers
Too many worker tasks
```

It shall reject new work safely before complete failure where possible.

---

# Chapter 1120 — Queue Capacity Limits

Queues shall have configured maximum sizes.

Examples:

```text
Offline actions per client
Outbox events awaiting publication
Pending export jobs
Concurrent transfer queue
Administrative alert queue
```

When full:

* Reject or pause new work.
* Preserve existing work.
* Display a clear error.
* Alert administrators where appropriate.

---

# Chapter 1121 — Graceful Overload Behaviour

During overload, priority should be:

```text
Authentication and session validation

Text message persistence

Critical security and audit operations

Message retrieval

File transfers

Administrative statistics
```

Non-essential dashboard refreshes may be slowed or disabled first.

---

# Chapter 1122 — Error Handling Unit Tests

Tests shall include:

```text
Construct base application error
Map exception to error code
Map error code to HTTP status
Return API error envelope
Return WebSocket error event
Generate correlation identifier
Propagate correlation identifier
Redact secret context
Translate repository exception
Classify retryable error
Classify permanent error
Respect retry-after
Avoid duplicate logging
Use generic unexpected-error response
```

---

# Chapter 1123 — Retry Tests

Tests shall include:

```text
Retry temporary connection failure
Stop after maximum attempts
Apply exponential delay
Apply jitter within bounds
Do not retry permission denied
Retry idempotent message send
Do not duplicate message
Retry identical upload chunk
Respect cancellation during retry wait
Resume after server recovery
```

---

# Chapter 1124 — Circuit Breaker Tests

Tests shall include:

```text
Remain closed after success
Open after configured failures
Fail fast while open
Enter half-open after timeout
Close after successful test
Reopen after failed test
Ignore business validation errors
Track dependency-specific circuit
```

---

# Chapter 1125 — Recovery Tests

Tests shall include:

```text
Recover draft after client crash
Recover offline queue after restart
Recover upload from confirmed chunks
Recover download from confirmed chunks
Reprocess outbox after server restart
Rebuild presence after Redis recovery
Resume directory sync after outage
Quarantine corrupt recovery record
Rebuild replaceable local cache
Preserve permanent message after event delivery failure
```

---

# Chapter 1126 — Error Security Tests

Tests shall include:

```text
Error response contains no stack trace
Error response contains no SQL
Error response contains no filesystem path
Password absent from authentication error
Token absent from logs
Private key absent from crash record
Plaintext message absent from diagnostic package
Unknown resource does not leak existence where restricted
Invalid signature does not display plaintext
Request body is not dumped into logs
```

---

# Chapter 1127 — Crash Tests

Tests shall include:

```text
Unhandled client exception creates crash record
Crash dialog displays reference
Draft save attempted during crash
Transfer state preserved
Server fatal exception exits non-zero
systemd restarts server
Committed transaction remains
Uncommitted transaction rolls back
Outbox event remains publishable
Diagnostic package excludes sensitive data
```

---

# Chapter 1128 — Diagnostic Tests

Tests shall include:

```text
Create client diagnostic package
Create server diagnostic report
Redact credentials
Include application version
Include recent error codes
Include connection-test results
Exclude local database
Exclude message content
Validate generated archive
Handle logging directory unavailable
```

---

# Chapter 1129 — Error Performance Tests

Performance tests shall measure:

```text
Global exception-handler overhead
Correlation middleware overhead
Structured error serialisation
Retry-queue processing
Circuit-breaker decision time
Log sanitisation overhead
Diagnostic-package generation memory
Audit failure rollback time
```

Error handling shall not significantly slow successful requests.

---

# Chapter 1130 — Simplified Version 1.0 Error Scope

Version 1.0 shall implement:

```text
Application exception hierarchy
Stable error-code catalogue
Common REST error envelope
Common WebSocket error envelope
Correlation identifiers
Client error catalogue
Plain-language messages
Retry classification
Exponential backoff
Retry-after support
Token-refresh coordination
Basic circuit breakers
Degraded capability states
Sanitised structured logging
Client diagnostic packages
Server diagnostic reports
Client crash records
Draft and queue recovery
Worker retry handling
```

The following may be deferred:

```text
Distributed tracing platform
Automatic remote crash upload
Advanced anomaly correlation
Machine-learning failure prediction
Full memory-dump analysis
External incident-management integration
Automatic database failover
Distributed circuit-breaker coordination
```

---

# Chapter 1131 — Error Handling and Recovery Summary

BlueBubbles shall use a consistent error-handling architecture across all components.

Expected failures shall use typed application exceptions and stable error codes.

Unexpected failures shall be captured at application boundaries and returned as safe generic errors.

Every important operation shall have a correlation identifier.

The client shall receive:

* A clear title.
* A plain-language explanation.
* A retry indication.
* A suggested action.
* A technical reference where useful.

The server shall retain:

* Structured technical context.
* Sanitised traceback information.
* Dependency status.
* Retry attempts.
* Correlation identifiers.

Retries shall occur only when:

* The failure is temporary.
* The action is idempotent or protected by an idempotency key.
* The retry policy allows it.
* The maximum attempt count has not been exceeded.

Circuit breakers shall prevent repeated calls to failing dependencies.

BlueBubbles shall remain partially operational when non-essential components fail, provided security and data integrity are preserved.

Client crashes shall preserve drafts and transfer state where possible.

Server crashes shall rely on database transactions, outbox recovery, resumable transfers and service-manager restarts.

Diagnostic packages shall remain local and shall exclude passwords, tokens, keys, messages, drafts and attachment content.

The application shall never fail silently, claim false success or discard recoverable user work without explanation.

---

# End of Part 17

Part 18 will define the complete testing strategy and quality-assurance architecture, including:

* Unit testing.
* Integration testing.
* End-to-end testing.
* Security testing.
* Performance testing.
* Property-based testing.
* Test fixtures.
* Mock services.
* Test databases.
* Coverage expectations.
* Continuous integration.
* Manual acceptance testing.
* Stakeholder testing.
* Regression testing.
* Test evidence for the NEA.

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

---

## Task-specific authoritative source: Part 22

# Part 22 — Class-Level Implementation Blueprint

---

# Chapter 1865 — Class Blueprint Purpose

This section defines the implementation contract for the most important BlueBubbles classes.

It specifies:

* Constructor dependencies.
* Public methods.
* Input and output types.
* State ownership.
* Important private helpers.
* Async behaviour.
* Transaction boundaries.
* Signals and callbacks.
* Error behaviour.
* Collaboration between classes.

The coding AI shall use these contracts to produce consistent implementations.

Minor internal methods may be added where required, but the responsibilities defined here shall not be moved into unrelated classes.

---

# Chapter 1866 — General Constructor Rules

Constructors shall receive dependencies explicitly.

Preferred:

```python
class MessagingService:
    def __init__(
        self,
        unit_of_work_factory: UnitOfWorkFactory,
        permission_service: PermissionService,
        audit_service: AuditService,
        event_factory: EventFactory,
        clock: Clock,
    ) -> None:
        ...
```

Avoid:

```python
class MessagingService:
    def __init__(self) -> None:
        self.database = create_database_connection()
        self.settings = load_environment_variables()
```

Classes shall not construct infrastructure dependencies internally unless construction is their defined responsibility.

---

# Chapter 1867 — Constructor State

Constructors may:

* Store validated dependencies.
* Create small in-memory structures.
* Validate static invariants.
* Prepare locks or cancellation objects.

Constructors shall not:

* Open network connections.
* Run database queries.
* Start background tasks.
* Perform blocking file operations.
* Read user data.
* Start Qt windows.
* Run migrations.

Lifecycle methods shall perform active startup work.

---

# Chapter 1868 — Public Method Rules

Public methods shall:

* Use explicit type hints.
* Return typed values.
* Raise documented application errors.
* Avoid returning raw infrastructure exceptions.
* Preserve transactional consistency.
* Check cancellation where applicable.
* Avoid unnecessary side effects.
* Use async methods for I/O.

Methods performing network, database or filesystem I/O shall normally use:

```python
async def
```

---

# Chapter 1869 — Private Helper Rules

Private helpers may be used to:

* Decompose validation.
* Build domain objects.
* Convert DTOs.
* Calculate derived values.
* Encapsulate repeated internal steps.

Private helpers shall not hide major business transactions unexpectedly.

A method called `_validate_request()` shall not secretly commit database changes.

---

# Chapter 1870 — Service Result Objects

Complex service operations shall return result objects.

Examples:

```python
@dataclass(slots=True, frozen=True)
class SendMessageResult:
    message: Message
    acknowledgement: SendMessageResponse
    outbox_event_id: UUID
```

```python
@dataclass(slots=True, frozen=True)
class AuthenticationResult:
    user: User
    session: Session
    access_token: str
    refresh_token: str
    capabilities: ServerCapabilities
```

Result objects shall make returned values self-describing.

---

# Chapter 1871 — Cancellation Model

Long-running client operations shall support cancellation.

Suitable operations:

* File upload.
* File download.
* Search-index rebuild.
* Initial synchronisation.
* Cache maintenance.
* Diagnostic package generation.

Cancellation shall use:

* `asyncio.Event`.
* A cancellation token abstraction.
* Qt-compatible worker cancellation state.

Cancellation shall not interrupt a database commit halfway through.

---

# Chapter 1872 — CancellationToken

```python
class CancellationToken:
    """Provides cooperative cancellation for long-running operations."""

    def __init__(self) -> None:
        self._cancelled = asyncio.Event()

    def cancel(self) -> None:
        self._cancelled.set()

    @property
    def is_cancelled(self) -> bool:
        return self._cancelled.is_set()

    async def raise_if_cancelled(self) -> None:
        if self._cancelled.is_set():
            raise OperationCancelledError()
```

Operations shall check the token between safe processing units.

---

# Chapter 1873 — Clock Contract

```python
class Clock(Protocol):
    """Provides application time for testable time-dependent logic."""

    def now(self) -> datetime:
        ...
```

Implementation:

```python
class SystemClock:
    def now(self) -> datetime:
        return datetime.now(timezone.utc)
```

All security-sensitive time calculations shall use UTC.

---

# Chapter 1874 — IdentifierGenerator Contract

```python
class IdentifierGenerator(Protocol):
    """Generates application identifiers."""

    def new_uuid(self) -> UUID:
        ...
```

Production implementation shall use UUID generation suitable for application identifiers.

Client-generated message IDs shall remain stable across retries.

---

# Chapter 1875 — ServerContainer Blueprint

```python
class ServerContainer:
    """Owns application-wide server dependencies."""

    def __init__(
        self,
        settings: ServerSettings,
        database_manager: DatabaseManager,
        redis_manager: RedisManager,
        file_storage: FileStorage,
        unit_of_work_factory: UnitOfWorkFactory,
        services: ServerServices,
        websocket_manager: WebSocketConnectionManager,
        worker_manager: WorkerManager,
        logger: BoundLogger,
    ) -> None:
        ...
```

Public methods:

```python
async def start(self) -> None:
    ...

async def stop(self) -> None:
    ...

async def get_health(self) -> DetailedHealthResponse:
    ...
```

State:

```text
_started
_stopping
_start_lock
```

---

# Chapter 1876 — ServerContainer Start Behaviour

`start()` shall:

```text
Acquire lifecycle lock

↓

Reject or ignore duplicate start safely

↓

Connect database

↓

Verify migration revision

↓

Connect Redis

↓

Verify storage

↓

Start WebSocket infrastructure

↓

Start workers

↓

Mark started
```

If a stage fails, previously started components shall stop in reverse order.

---

# Chapter 1877 — ServerContainer Stop Behaviour

`stop()` shall be safe when:

* Startup completed.
* Startup partially completed.
* Stop was already called.
* One component fails during shutdown.

It shall attempt every cleanup stage even if an earlier cleanup fails.

Shutdown errors shall be collected and logged.

---

# Chapter 1878 — DatabaseManager Blueprint

```python
class DatabaseManager:
    """Owns the SQLAlchemy engine and database pool."""

    def __init__(
        self,
        settings: DatabaseSettings,
        logger: BoundLogger,
    ) -> None:
        ...
```

Public methods:

```python
async def start(self) -> None:
    ...

async def stop(self) -> None:
    ...

async def check_health(self) -> ComponentHealth:
    ...

def create_session(self) -> AsyncSession:
    ...
```

Private helpers:

```text
_build_engine()
_verify_connection()
_redact_database_error()
```

---

# Chapter 1879 — DatabaseManager State

State shall include:

```text
_engine
_session_factory
_started
```

The manager shall not expose the raw database password.

`create_session()` shall fail clearly if called before startup.

---

# Chapter 1880 — RedisManager Blueprint

```python
class RedisManager:
    """Owns Redis connectivity and transient state access."""

    def __init__(
        self,
        settings: RedisSettings,
        logger: BoundLogger,
    ) -> None:
        ...
```

Public methods:

```python
async def start(self) -> None:
    ...

async def stop(self) -> None:
    ...

async def ping(self) -> float:
    ...

async def check_health(self) -> ComponentHealth:
    ...

def client(self) -> Redis:
    ...
```

The manager shall translate Redis library errors into application dependency errors.

---

# Chapter 1881 — UnitOfWorkFactory Blueprint

```python
class UnitOfWorkFactory:
    """Creates transaction-scoped Units of Work."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        repository_factory: RepositoryFactory,
    ) -> None:
        ...

    def __call__(self) -> UnitOfWork:
        ...
```

Each call shall produce a fresh Unit of Work and fresh database session.

---

# Chapter 1882 — UnitOfWork Blueprint

```python
class UnitOfWork:
    """Coordinates repositories sharing one database transaction."""

    def __init__(
        self,
        session: AsyncSession,
        repositories: ServerRepositories,
    ) -> None:
        ...
```

Public methods:

```python
async def __aenter__(self) -> "UnitOfWork":
    ...

async def __aexit__(
    self,
    exc_type: type[BaseException] | None,
    exc: BaseException | None,
    traceback: TracebackType | None,
) -> None:
    ...

async def commit(self) -> None:
    ...

async def rollback(self) -> None:
    ...

async def flush(self) -> None:
    ...
```

---

# Chapter 1883 — UnitOfWork Behaviour

Rules:

* No automatic commit merely because no exception occurred unless explicitly chosen.
* Roll back after unhandled exception.
* Close session on exit.
* Prevent commit after rollback.
* Prevent multiple conflicting completion calls.
* Expose repositories sharing the same session.

State:

```text
_committed
_rolled_back
_closed
```

---

# Chapter 1884 — UserRepository Blueprint

```python
class UserRepository(Protocol):
    """Defines persistent user operations."""

    async def get_by_id(
        self,
        user_id: UUID,
        *,
        for_update: bool = False,
    ) -> User | None:
        ...

    async def get_by_normalised_username(
        self,
        username: str,
    ) -> User | None:
        ...

    async def create(
        self,
        user: User,
    ) -> User:
        ...

    async def update(
        self,
        user: User,
        *,
        expected_version: int | None = None,
    ) -> User:
        ...

    async def search(
        self,
        query: UserSearchQuery,
    ) -> CursorPage[User]:
        ...
```

Repository methods shall not perform role-authorisation decisions.

---

# Chapter 1885 — SessionRepository Blueprint

```python
class SessionRepository(Protocol):
    async def create(
        self,
        session: Session,
    ) -> Session:
        ...

    async def get_active(
        self,
        session_id: UUID,
        *,
        for_update: bool = False,
    ) -> Session | None:
        ...

    async def list_active_for_user(
        self,
        user_id: UUID,
    ) -> list[Session]:
        ...

    async def update_refresh_token(
        self,
        session_id: UUID,
        refresh_token_hash: bytes,
        token_version: int,
        last_seen_at: datetime,
    ) -> None:
        ...

    async def invalidate(
        self,
        session_id: UUID,
        invalidated_at: datetime,
        reason: str,
    ) -> bool:
        ...
```

---

# Chapter 1886 — ConversationRepository Blueprint

```python
class ConversationRepository(Protocol):
    async def get_by_id(
        self,
        conversation_id: UUID,
        *,
        for_update: bool = False,
    ) -> Conversation | None:
        ...

    async def get_active_membership(
        self,
        conversation_id: UUID,
        user_id: UUID,
        *,
        for_update: bool = False,
    ) -> ConversationMember | None:
        ...

    async def list_active_members(
        self,
        conversation_id: UUID,
        *,
        for_update: bool = False,
    ) -> list[ConversationMember]:
        ...

    async def find_direct_pair(
        self,
        first_user_id: UUID,
        second_user_id: UUID,
    ) -> Conversation | None:
        ...

    async def create(
        self,
        conversation: Conversation,
    ) -> Conversation:
        ...
```

---

# Chapter 1887 — MessageRepository Blueprint

```python
class MessageRepository(Protocol):
    async def create(
        self,
        message: Message,
    ) -> Message:
        ...

    async def get_by_id(
        self,
        message_id: UUID,
        *,
        for_update: bool = False,
    ) -> Message | None:
        ...

    async def get_existing_idempotent_message(
        self,
        message_id: UUID,
        sender_id: UUID,
    ) -> Message | None:
        ...

    async def add_recipient_keys(
        self,
        keys: Sequence[MessageRecipientKey],
    ) -> None:
        ...

    async def list_for_conversation(
        self,
        query: MessagePageQuery,
    ) -> CursorPage[Message]:
        ...

    async def update_payload(
        self,
        message: Message,
        expected_version: int,
    ) -> Message:
        ...
```

---

# Chapter 1888 — AttachmentRepository Blueprint

```python
class AttachmentRepository(Protocol):
    async def create_upload_session(
        self,
        session: UploadSession,
    ) -> UploadSession:
        ...

    async def get_upload_session(
        self,
        upload_id: UUID,
        *,
        for_update: bool = False,
    ) -> UploadSession | None:
        ...

    async def create_attachment(
        self,
        attachment: Attachment,
    ) -> Attachment:
        ...

    async def add_chunks(
        self,
        chunks: Sequence[AttachmentChunk],
    ) -> None:
        ...

    async def add_recipient_keys(
        self,
        keys: Sequence[AttachmentRecipientKey],
    ) -> None:
        ...

    async def link_to_message(
        self,
        attachment_ids: Sequence[UUID],
        message_id: UUID,
    ) -> None:
        ...
```

---

# Chapter 1889 — AuditRepository Blueprint

```python
class AuditRepository(Protocol):
    async def lock_chain_state(self) -> AuditChainState:
        ...

    async def append(
        self,
        event: AuditEvent,
    ) -> AuditEvent:
        ...

    async def update_chain_state(
        self,
        state: AuditChainState,
    ) -> None:
        ...

    async def list_events(
        self,
        query: AuditQuery,
    ) -> CursorPage[AuditEvent]:
        ...

    async def list_range(
        self,
        first_sequence: int,
        last_sequence: int,
    ) -> list[AuditEvent]:
        ...
```

No update or delete method shall exist for individual audit events.

---

# Chapter 1890 — OutboxRepository Blueprint

```python
class OutboxRepository(Protocol):
    async def add(
        self,
        event: OutboxEvent,
    ) -> OutboxEvent:
        ...

    async def claim_batch(
        self,
        worker_id: str,
        limit: int,
        now: datetime,
    ) -> list[OutboxEvent]:
        ...

    async def mark_published(
        self,
        event_id: UUID,
        published_at: datetime,
    ) -> None:
        ...

    async def mark_failed(
        self,
        event_id: UUID,
        error_code: str,
        next_attempt_at: datetime,
    ) -> None:
        ...
```

Claiming shall prevent two workers processing the same event concurrently.

---

# Chapter 1891 — AuthenticationProvider Blueprint

```python
class AuthenticationProvider(Protocol):
    """Authenticates credentials against one identity source."""

    async def authenticate(
        self,
        credentials: LoginCredentials,
    ) -> AuthenticatedDirectoryIdentity:
        ...

    async def get_user_by_identifier(
        self,
        identifier: str,
    ) -> DirectoryUser | None:
        ...

    async def check_health(self) -> ComponentHealth:
        ...
```

The returned identity shall not contain the submitted password.

---

# Chapter 1892 — LDAPAuthenticationProvider Constructor

```python
class LDAPAuthenticationProvider:
    def __init__(
        self,
        settings: DirectorySettings,
        connection_factory: LDAPConnectionFactory,
        mapper: DirectoryUserMapper,
        circuit_breaker: CircuitBreaker,
        logger: BoundLogger,
    ) -> None:
        ...
```

It shall not receive repositories or issue application sessions.

Its responsibility ends after validated directory identity retrieval.

---

# Chapter 1893 — LDAPAuthenticationProvider Helpers

Important private helpers:

```text
_build_user_search_filter()
_escape_identifier()
_find_user_entry()
_bind_as_user()
_read_group_memberships()
_translate_ldap_error()
```

The provider shall use library-supported LDAP escaping.

---

# Chapter 1894 — LocalAuthenticationProvider Constructor

```python
class LocalAuthenticationProvider:
    def __init__(
        self,
        user_repository: UserRepository,
        credential_repository: LocalCredentialRepository,
        password_hasher: PasswordHasher,
        clock: Clock,
    ) -> None:
        ...
```

Public method:

```python
async def authenticate(
    self,
    credentials: LoginCredentials,
) -> AuthenticatedDirectoryIdentity:
    ...
```

The local provider shall produce the same identity abstraction as LDAP.

---

# Chapter 1895 — PasswordHasher Blueprint

```python
class PasswordHasher:
    """Performs Argon2id password hashing and verification."""

    def __init__(
        self,
        parameters: PasswordHashingParameters,
    ) -> None:
        ...

    def hash_password(
        self,
        password: SecretStr,
    ) -> str:
        ...

    def verify_password(
        self,
        password: SecretStr,
        encoded_hash: str,
    ) -> bool:
        ...

    def requires_rehash(
        self,
        encoded_hash: str,
    ) -> bool:
        ...
```

Passwords shall not be converted to logs or exception context.

---

# Chapter 1896 — TokenManager Blueprint

```python
class TokenManager:
    """Creates and validates access and refresh-token material."""

    def __init__(
        self,
        settings: TokenSettings,
        clock: Clock,
        secure_random: SecureRandom,
    ) -> None:
        ...
```

Public methods:

```python
def create_access_token(
    self,
    user: User,
    session: Session,
) -> str:
    ...

def create_refresh_token(self) -> str:
    ...

def hash_refresh_token(
    self,
    refresh_token: str,
) -> bytes:
    ...

def decode_access_token(
    self,
    token: str,
) -> AccessTokenClaims:
    ...
```

---

# Chapter 1897 — TokenManager Validation

`decode_access_token()` shall validate:

* Signature.
* Algorithm.
* Issuer.
* Audience.
* Expiry.
* Not-before time where used.
* Subject.
* Session identifier.
* Token version.
* Required claim types.

It shall reject unexpected algorithms.

---

# Chapter 1898 — AuthenticationService Constructor

```python
class AuthenticationService:
    def __init__(
        self,
        provider: AuthenticationProvider,
        unit_of_work_factory: UnitOfWorkFactory,
        session_service: SessionService,
        login_attempt_service: LoginAttemptService,
        audit_service: AuditService,
        capability_service: CapabilityService,
        clock: Clock,
        logger: BoundLogger,
    ) -> None:
        ...
```

---

# Chapter 1899 — AuthenticationService Login Contract

```python
async def login(
    self,
    request: LoginRequest,
    context: LoginContext,
) -> AuthenticationResult:
    ...
```

Inputs:

```text
username
password
device identifier
device name
client version
source IP
correlation ID
```

Outputs:

```text
authenticated user
session
access token
refresh token
server capabilities
```

---

# Chapter 1900 — AuthenticationService Login Workflow

```text
Normalise username

↓

Check rate and attempt policy

↓

Authenticate using provider

↓

Open Unit of Work

↓

Create or synchronise user

↓

Check enabled state

↓

Create session

↓

Append successful-login audit event

↓

Commit

↓

Generate access token

↓

Return result
```

Authentication failure shall record safe attempt metadata without exposing whether the username exists.

---

# Chapter 1901 — AuthenticationService Private Helpers

```text
_normalise_login_request()
_synchronise_authenticated_identity()
_resolve_role_mapping()
_validate_account_state()
_build_session()
_record_failed_attempt()
```

Token generation may occur after commit, but the session must already exist.

---

# Chapter 1902 — SessionService Constructor

```python
class SessionService:
    def __init__(
        self,
        unit_of_work_factory: UnitOfWorkFactory,
        token_manager: TokenManager,
        websocket_manager: WebSocketConnectionManager,
        audit_service: AuditService,
        clock: Clock,
    ) -> None:
        ...
```

---

# Chapter 1903 — SessionService Public Methods

```python
async def create_session(
    self,
    user: User,
    device: DeviceDescriptor,
    source_ip: str | None,
) -> SessionTokenPair:
    ...

async def refresh(
    self,
    request: RefreshTokenRequest,
) -> SessionTokenPair:
    ...

async def invalidate(
    self,
    requester: AuthenticatedUser,
    session_id: UUID,
    reason: str,
) -> None:
    ...

async def invalidate_all_for_user(
    self,
    user_id: UUID,
    reason: str,
) -> int:
    ...
```

---

# Chapter 1904 — Session Refresh Workflow

```text
Hash submitted refresh token

↓

Lock session row

↓

Verify active state

↓

Verify expiry

↓

Compare token hash

↓

Detect reuse or mismatch

↓

Generate replacement refresh token

↓

Increment token version

↓

Store replacement hash

↓

Commit

↓

Generate new access token

↓

Return tokens
```

Only one successful use of a rotated refresh token shall be accepted.

---

# Chapter 1905 — Refresh-Token Reuse Handling

On detected reuse:

```text
Invalidate affected session

↓

Optionally invalidate all user sessions

↓

Disconnect associated WebSockets

↓

Create high-severity audit event

↓

Create security alert

↓

Return authentication failure
```

The response shall not reveal token internals.

---

# Chapter 1906 — PermissionService Constructor

```python
class PermissionService:
    def __init__(
        self,
        role_repository: RoleRepository,
        permission_cache: PermissionCache,
        conversation_repository: ConversationRepository,
    ) -> None:
        ...
```

Public methods:

```python
async def require_permission(
    self,
    user: User,
    permission: PermissionName,
) -> None:
    ...

async def require_conversation_access(
    self,
    user_id: UUID,
    conversation_id: UUID,
) -> ConversationMember:
    ...

async def require_group_role(
    self,
    user_id: UUID,
    conversation_id: UUID,
    minimum_role: GroupRole,
) -> ConversationMember:
    ...
```

---

# Chapter 1907 — PermissionService State

The service may hold:

* A reference to permission cache.
* Static group-role ordering.
* No mutable current-user state.

A single service instance shall safely serve many concurrent requests.

---

# Chapter 1908 — ConversationService Constructor

```python
class ConversationService:
    def __init__(
        self,
        unit_of_work_factory: UnitOfWorkFactory,
        permission_service: PermissionService,
        audit_service: AuditService,
        event_factory: EventFactory,
        identifier_generator: IdentifierGenerator,
        clock: Clock,
    ) -> None:
        ...
```

---

# Chapter 1909 — ConversationService Public Methods

```python
async def create_direct(
    self,
    requester: AuthenticatedUser,
    request: CreateDirectConversationRequest,
) -> ConversationResponse:
    ...

async def create_group(
    self,
    requester: AuthenticatedUser,
    request: CreateGroupConversationRequest,
) -> ConversationResponse:
    ...

async def list_for_user(
    self,
    requester: AuthenticatedUser,
    query: ConversationListQuery,
) -> CursorPage[ConversationSummaryResponse]:
    ...

async def get_conversation(
    self,
    requester: AuthenticatedUser,
    conversation_id: UUID,
) -> ConversationResponse:
    ...
```

---

# Chapter 1910 — Direct Conversation Creation Logic

Private helpers:

```text
_validate_direct_target()
_build_canonical_pair()
_find_existing_direct()
_create_direct_memberships()
_build_conversation_response()
```

If a unique constraint race occurs, the service shall retrieve and return the conversation created by the competing request.

---

# Chapter 1911 — GroupService Constructor

```python
class GroupService:
    def __init__(
        self,
        unit_of_work_factory: UnitOfWorkFactory,
        permission_service: PermissionService,
        audit_service: AuditService,
        event_factory: EventFactory,
        settings: MessagingSettings,
        clock: Clock,
    ) -> None:
        ...
```

---

# Chapter 1912 — GroupService Public Methods

```python
async def add_member(
    self,
    requester: AuthenticatedUser,
    group_id: UUID,
    target_user_id: UUID,
) -> GroupMembershipResult:
    ...

async def remove_member(
    self,
    requester: AuthenticatedUser,
    group_id: UUID,
    target_user_id: UUID,
) -> GroupMembershipResult:
    ...

async def leave_group(
    self,
    requester: AuthenticatedUser,
    group_id: UUID,
) -> None:
    ...

async def transfer_ownership(
    self,
    requester: AuthenticatedUser,
    group_id: UUID,
    target_user_id: UUID,
) -> OwnershipTransferResult:
    ...
```

---

# Chapter 1913 — GroupService Role Comparison

A dedicated helper shall compare:

```text
owner
moderator
member
```

Example:

```python
def _can_manage_target(
    self,
    requester_role: GroupRole,
    target_role: GroupRole,
) -> bool:
    ...
```

Application-wide roles shall not automatically override group ownership rules unless an explicit administrative operation is used.

---

# Chapter 1914 — MessagingService Constructor

```python
class MessagingService:
    def __init__(
        self,
        unit_of_work_factory: UnitOfWorkFactory,
        permission_service: PermissionService,
        audit_service: AuditService,
        event_factory: EventFactory,
        message_validator: MessageEnvelopeValidator,
        settings: MessagingSettings,
        clock: Clock,
    ) -> None:
        ...
```

The server service shall not depend on client decryption classes.

---

# Chapter 1915 — MessagingService Send Contract

```python
async def send_message(
    self,
    sender: AuthenticatedUser,
    request: SendMessageRequest,
) -> SendMessageResponse:
    ...
```

Expected errors:

```text
ConversationNotFoundError
NotConversationMemberError
InvalidRecipientKeysError
MessageConflictError
InvalidReplyTargetError
UnsupportedProtocolError
PayloadTooLargeError
```

---

# Chapter 1916 — MessagingService Send Helpers

Important helpers:

```text
_validate_request_size()
_load_required_members()
_validate_recipient_envelopes()
_validate_reply_target()
_compare_idempotent_payload()
_build_message()
_build_recipient_keys()
_build_delivery_records()
```

These helpers shall not individually commit.

---

# Chapter 1917 — MessagingService Send Transaction

Within one Unit of Work:

```text
Check existing message ID

↓

Load and verify membership

↓

Load active recipients

↓

Validate recipient envelopes

↓

Validate attachments

↓

Insert message

↓

Insert keys

↓

Insert delivery rows

↓

Link attachments

↓

Update conversation activity

↓

Append audit event

↓

Add outbox event

↓

Commit
```

The response shall be returned only after commit succeeds.

---

# Chapter 1918 — MessagingService Edit Contract

```python
async def edit_message(
    self,
    requester: AuthenticatedUser,
    message_id: UUID,
    request: EditMessageRequest,
) -> EncryptedMessageResponse:
    ...
```

The service shall:

* Lock message row.
* Check original sender.
* Check membership.
* Check edit window.
* Check expected version.
* Validate new recipient envelopes.
* Replace encrypted fields.
* Increment version.
* Add audit and outbox events.

---

# Chapter 1919 — MessagingService Delete Contract

```python
async def delete_message(
    self,
    requester: AuthenticatedUser,
    message_id: UUID,
    request: DeleteMessageRequest,
) -> DeletedMessageResponse:
    ...
```

The method shall support:

* Sender deletion.
* Explicit moderator or administrator path where permitted.
* Soft deletion.
* Attachment retention update.
* Version conflict handling.
* Durable deletion event.

---

# Chapter 1920 — MessageEnvelopeValidator Blueprint

```python
class MessageEnvelopeValidator:
    """Validates encrypted message structure without decrypting content."""

    def __init__(
        self,
        settings: MessagingSettings,
        protocol_registry: ProtocolRegistry,
    ) -> None:
        ...
```

Public method:

```python
def validate(
    self,
    request: SendMessageRequest,
) -> MessageEnvelopeValidationResult:
    ...
```

It shall check:

* Binary field decoding.
* Nonce length.
* Tag length.
* Signature presence.
* Protocol support.
* Recipient duplicates.
* Size bounds.

---

# Chapter 1921 — AttachmentService Constructor

```python
class AttachmentService:
    def __init__(
        self,
        unit_of_work_factory: UnitOfWorkFactory,
        permission_service: PermissionService,
        file_storage: FileStorage,
        checksum_service: ChecksumService,
        audit_service: AuditService,
        event_factory: EventFactory,
        settings: AttachmentSettings,
        storage_monitor: StorageMonitor,
        clock: Clock,
    ) -> None:
        ...
```

---

# Chapter 1922 — AttachmentService Public Methods

```python
async def initialise_upload(
    self,
    uploader: AuthenticatedUser,
    request: InitialiseUploadRequest,
) -> InitialiseUploadResponse:
    ...

async def upload_chunk(
    self,
    uploader: AuthenticatedUser,
    upload_id: UUID,
    chunk_index: int,
    chunk: IncomingEncryptedChunk,
) -> UploadChunkResponse:
    ...

async def complete_upload(
    self,
    uploader: AuthenticatedUser,
    upload_id: UUID,
) -> AttachmentResponse:
    ...

async def get_authorised_attachment(
    self,
    requester: AuthenticatedUser,
    attachment_id: UUID,
) -> AuthorisedAttachmentResponse:
    ...
```

---

# Chapter 1923 — Upload Initialisation Helpers

```text
_validate_declared_sizes()
_validate_chunk_configuration()
_validate_filename_metadata()
_validate_recipient_keys()
_verify_storage_capacity()
_build_upload_session()
```

The original filename shall not be used to create a physical path.

---

# Chapter 1924 — Chunk Upload Behaviour

`upload_chunk()` shall:

```text
Load upload session

↓

Verify owner and status

↓

Validate index and size

↓

Calculate incoming encrypted checksum

↓

Check existing chunk

↓

Write chunk atomically

↓

Record progress

↓

Return server-confirmed state
```

If database metadata update fails after the file write, the orphaned temporary chunk shall be recoverable or cleaned later.

---

# Chapter 1925 — Attachment Finalisation Helpers

```text
_verify_all_chunks_present()
_stream_complete_encrypted_hash()
_build_attachment()
_build_chunk_records()
_build_recipient_key_records()
_prepare_permanent_storage()
```

The method shall coordinate filesystem and database state carefully.

---

# Chapter 1926 — FileStorage Blueprint

```python
class FileStorage(ABC):
    @abstractmethod
    async def initialise_upload(
        self,
        upload_id: UUID,
    ) -> None:
        ...

    @abstractmethod
    async def write_chunk(
        self,
        upload_id: UUID,
        chunk_index: int,
        stream: AsyncIterator[bytes],
    ) -> StoredChunk:
        ...

    @abstractmethod
    async def read_attachment_chunk(
        self,
        attachment_id: UUID,
        chunk_index: int,
    ) -> AsyncIterator[bytes]:
        ...

    @abstractmethod
    async def finalise(
        self,
        upload_id: UUID,
        attachment_id: UUID,
    ) -> StorageFinalisationResult:
        ...
```

---

# Chapter 1927 — LocalFileStorage Constructor

```python
class LocalFileStorage(FileStorage):
    def __init__(
        self,
        paths: AttachmentPathBuilder,
        checksum_service: ChecksumService,
        permissions: FilePermissionService,
        logger: BoundLogger,
    ) -> None:
        ...
```

The storage implementation shall not query PostgreSQL.

---

# Chapter 1928 — AttachmentPathBuilder Blueprint

```python
class AttachmentPathBuilder:
    def __init__(
        self,
        root_path: Path,
        temporary_path: Path,
    ) -> None:
        ...

    def upload_directory(
        self,
        upload_id: UUID,
    ) -> Path:
        ...

    def upload_chunk_path(
        self,
        upload_id: UUID,
        chunk_index: int,
    ) -> Path:
        ...

    def attachment_directory(
        self,
        attachment_id: UUID,
    ) -> Path:
        ...

    def verify_contained(
        self,
        path: Path,
        root: Path,
    ) -> Path:
        ...
```

All returned paths shall be resolved and checked against the configured root.

---

# Chapter 1929 — AuditService Constructor

```python
class AuditService:
    def __init__(
        self,
        audit_writer: AuditWriter,
        visibility_filter: AuditVisibilityFilter,
        clock: Clock,
    ) -> None:
        ...
```

Public methods:

```python
async def record(
    self,
    data: CreateAuditEvent,
    unit_of_work: UnitOfWork,
) -> AuditEvent:
    ...

async def list_events(
    self,
    requester: AuthenticatedUser,
    query: AuditQuery,
) -> CursorPage[AuditEventResponse]:
    ...
```

When part of a business transaction, `record()` shall use that same Unit of Work.

---

# Chapter 1930 — AuditWriter Constructor

```python
class AuditWriter:
    def __init__(
        self,
        canonical_serialiser: CanonicalAuditSerialiser,
        hash_service: HashService,
        clock: Clock,
        identifier_generator: IdentifierGenerator,
    ) -> None:
        ...
```

Public method:

```python
async def append(
    self,
    unit_of_work: UnitOfWork,
    data: CreateAuditEvent,
) -> AuditEvent:
    ...
```

It shall not open a second independent transaction when called from a business operation.

---

# Chapter 1931 — AuditIntegrityService Blueprint

```python
class AuditIntegrityService:
    def __init__(
        self,
        unit_of_work_factory: UnitOfWorkFactory,
        canonical_serialiser: CanonicalAuditSerialiser,
        hash_service: HashService,
        clock: Clock,
    ) -> None:
        ...
```

Public methods:

```python
async def verify_range(
    self,
    first_sequence: int,
    last_sequence: int,
) -> AuditVerificationResult:
    ...

async def verify_recent(
    self,
    count: int,
) -> AuditVerificationResult:
    ...
```

It shall operate read-only.

---

# Chapter 1932 — AdminService Constructor

```python
class AdminService:
    def __init__(
        self,
        unit_of_work_factory: UnitOfWorkFactory,
        permission_service: PermissionService,
        session_service: SessionService,
        websocket_manager: WebSocketConnectionManager,
        audit_service: AuditService,
        role_policy: RoleAdministrationPolicy,
        clock: Clock,
    ) -> None:
        ...
```

---

# Chapter 1933 — AdminService Disable User Contract

```python
async def disable_user(
    self,
    requester: AuthenticatedUser,
    target_user_id: UUID,
    reason: str,
) -> UserAdministrationResult:
    ...
```

Workflow:

```text
Require permission

↓

Validate reason

↓

Lock target user

↓

Prevent forbidden self-lockout

↓

Set disabled state

↓

Invalidate sessions

↓

Append audit event

↓

Add outbox session-revocation event

↓

Commit

↓

Disconnect active WebSockets
```

If disconnect fails, the sessions remain invalidated.

---

# Chapter 1934 — MonitoringService Constructor

```python
class MonitoringService:
    def __init__(
        self,
        health_checks: Sequence[ComponentHealthCheck],
        metrics_collector: MetricsCollector,
        websocket_manager: WebSocketConnectionManager,
        worker_manager: WorkerManager,
        storage_monitor: StorageMonitor,
        clock: Clock,
    ) -> None:
        ...
```

Public methods:

```python
async def public_health(self) -> PublicHealthResponse:
    ...

async def detailed_health(
    self,
    requester: AuthenticatedUser,
) -> DetailedHealthResponse:
    ...

async def dashboard(
    self,
    requester: AuthenticatedUser,
) -> AdminDashboardResponse:
    ...
```

---

# Chapter 1935 — WebSocketConnection Blueprint

```python
class WebSocketConnection:
    def __init__(
        self,
        websocket: WebSocket,
        connection_id: UUID,
        user_id: UUID,
        session_id: UUID,
        device_id: UUID,
        connected_at: datetime,
    ) -> None:
        ...
```

Public methods:

```python
async def send(
    self,
    event: WebSocketEventEnvelope,
) -> None:
    ...

async def close(
    self,
    code: int,
    reason: str,
) -> None:
    ...

def mark_heartbeat(
    self,
    timestamp: datetime,
) -> None:
    ...
```

Each connection shall own a send lock to prevent overlapping frame writes.

---

# Chapter 1936 — WebSocketConnectionManager Constructor

```python
class WebSocketConnectionManager:
    def __init__(
        self,
        clock: Clock,
        logger: BoundLogger,
    ) -> None:
        ...
```

State:

```text
_connections_by_id
_connection_ids_by_user
_connection_ids_by_session
_lock
```

Public methods:

```python
async def register(
    self,
    connection: WebSocketConnection,
) -> None:
    ...

async def unregister(
    self,
    connection_id: UUID,
) -> None:
    ...

async def send_to_user(
    self,
    user_id: UUID,
    event: WebSocketEventEnvelope,
) -> DeliverySummary:
    ...

async def disconnect_session(
    self,
    session_id: UUID,
    reason: str,
) -> int:
    ...
```

---

# Chapter 1937 — WebSocket Manager Concurrency

All index mutations shall occur under an async lock.

Network sends should not hold the global registry lock for the entire transmission.

Recommended:

```text
Lock registry

↓

Copy target connections

↓

Release registry lock

↓

Send to connections
```

Failed connections shall be unregistered safely.

---

# Chapter 1938 — WebSocketEventDispatcher Blueprint

```python
class WebSocketEventDispatcher:
    def __init__(
        self,
        handlers: Mapping[WebSocketEventType, WebSocketEventHandler],
        error_mapper: WebSocketErrorMapper,
        rate_limiter: WebSocketRateLimiter,
    ) -> None:
        ...
```

Public method:

```python
async def dispatch(
    self,
    connection: WebSocketConnection,
    raw_message: str | bytes,
) -> WebSocketAcknowledgement | None:
    ...
```

It shall validate protocol before invoking a handler.

---

# Chapter 1939 — EventPublisher Blueprint

```python
class EventPublisher:
    def __init__(
        self,
        websocket_manager: WebSocketConnectionManager,
        event_factory: EventFactory,
        logger: BoundLogger,
    ) -> None:
        ...
```

Public methods:

```python
async def publish_to_users(
    self,
    user_ids: Collection[UUID],
    event: ApplicationEvent,
) -> PublicationResult:
    ...

async def publish_to_session(
    self,
    session_id: UUID,
    event: ApplicationEvent,
) -> PublicationResult:
    ...
```

Publication failure shall not roll back already committed business data.

---

# Chapter 1940 — BackgroundWorker Blueprint

```python
class BackgroundWorker(ABC):
    def __init__(
        self,
        name: str,
        interval: timedelta,
        retry_policy: RetryPolicy,
        clock: Clock,
        logger: BoundLogger,
    ) -> None:
        ...
```

Public methods:

```python
async def start(self) -> None:
    ...

async def stop(self) -> None:
    ...

async def run_now(self) -> WorkerRunResult:
    ...

def status(self) -> WorkerStatus:
    ...
```

Abstract method:

```python
@abstractmethod
async def run_once(self) -> WorkerRunResult:
    ...
```

---

# Chapter 1941 — BackgroundWorker State

State:

```text
_task
_stop_event
_run_lock
_last_started_at
_last_completed_at
_last_error_code
_failure_count
_current_state
```

Only one `run_once()` execution shall occur at a time per worker.

---

# Chapter 1942 — WorkerManager Blueprint

```python
class WorkerManager:
    def __init__(
        self,
        workers: Sequence[BackgroundWorker],
    ) -> None:
        ...
```

Public methods:

```python
async def start(self) -> None:
    ...

async def stop(self) -> None:
    ...

async def run_worker_now(
        self,
        worker_name: str,
    ) -> WorkerRunResult:
    ...

def list_statuses(self) -> list[WorkerStatus]:
    ...
```

Worker names shall be unique.

---

# Chapter 1943 — OutboxPublisherWorker Constructor

```python
class OutboxPublisherWorker(BackgroundWorker):
    def __init__(
        self,
        unit_of_work_factory: UnitOfWorkFactory,
        event_publisher: EventPublisher,
        settings: OutboxSettings,
        retry_policy: RetryPolicy,
        alert_service: SecurityAlertService,
        clock: Clock,
        logger: BoundLogger,
    ) -> None:
        ...
```

---

# Chapter 1944 — OutboxPublisherWorker Run Behaviour

`run_once()` shall:

```text
Create worker identifier

↓

Claim bounded event batch

↓

For each event:

    Decode validated payload

    Publish

    Mark published

    or

    Mark failure and next retry

↓

Commit each safe batch

↓

Return counts
```

One poison event shall not block every later event indefinitely.

---

# Chapter 1945 — ClientContainer Blueprint

```python
class ClientContainer:
    """Owns client dependencies for one application lifecycle stage."""

    def __init__(
        self,
        settings: ClientSettings,
        secure_store: SecureStore,
        api_client: ApiClient,
        services: ClientServices,
        viewmodel_factory: ViewModelFactory,
        websocket_client: WebSocketClient | None = None,
        local_database: LocalDatabaseManager | None = None,
    ) -> None:
        ...
```

Public methods:

```python
async def start(self) -> None:
    ...

async def stop(self) -> None:
    ...
```

An authenticated container shall not be reused for another user.

---

# Chapter 1946 — ClientApplication Constructor

```python
class ClientApplication:
    def __init__(
        self,
        qt_application: QApplication,
        settings: ClientSettings,
        bootstrapper: ClientBootstrapper,
        crash_handler: ClientCrashHandler,
        logger: BoundLogger,
    ) -> None:
        ...
```

State:

```text
_unauthenticated_container
_authenticated_container
_login_window
_main_window
_shutting_down
```

---

# Chapter 1947 — ClientApplication Public Methods

```python
async def initialise(self) -> None:
    ...

async def complete_login(
        self,
        result: ClientAuthenticationResult,
    ) -> None:
        ...

async def logout(self) -> None:
    ...

async def shutdown(self) -> None:
    ...
```

The application class coordinates lifecycle but shall not implement messaging or authentication logic.

---

# Chapter 1948 — SecureStore Blueprint

```python
class SecureStore(Protocol):
    """Stores small protected secrets using operating-system facilities."""

    async def set_secret(
        self,
        key: str,
        value: bytes,
    ) -> None:
        ...

    async def get_secret(
        self,
        key: str,
    ) -> bytes | None:
        ...

    async def delete_secret(
        self,
        key: str,
    ) -> None:
        ...

    async def delete_profile(
        self,
        profile_id: UUID,
    ) -> None:
        ...
```

Secret names shall be namespaced per application and user profile.

---

# Chapter 1949 — WindowsCredentialManagerStore Blueprint

```python
class WindowsCredentialManagerStore:
    def __init__(
        self,
        application_namespace: str,
        logger: BoundLogger,
    ) -> None:
        ...
```

Responsibilities:

* Convert names to safe credential targets.
* Store binary values safely.
* Retrieve exact values.
* Delete values.
* Translate Windows API failures.
* Avoid logging secret contents.

---

# Chapter 1950 — LocalDatabaseManager Blueprint

```python
class LocalDatabaseManager:
    def __init__(
        self,
        database_path: Path,
        encryption_backend: LocalDatabaseEncryptionBackend,
        migration_manager: ClientMigrationManager,
        logger: BoundLogger,
    ) -> None:
        ...
```

Public methods:

```python
async def open(
    self,
    key: bytes,
) -> None:
    ...

async def close(self) -> None:
    ...

async def transaction(self) -> AsyncContextManager[LocalTransaction]:
    ...

async def verify_integrity(self) -> LocalDatabaseIntegrityResult:
    ...
```

---

# Chapter 1951 — LocalDatabaseManager Rules

The manager shall:

* Refuse queries before opening.
* Apply encryption key before reading schema.
* Run migrations once opened.
* Serialise migration execution.
* Close connections on logout.
* Avoid storing the key as printable text.
* Clear key references where possible on close.

---

# Chapter 1952 — ClientAuthenticationService Constructor

```python
class ClientAuthenticationService:
    def __init__(
        self,
        api_client: ApiClient,
        protocol_service: ProtocolNegotiationService,
        secure_store: SecureStore,
        device_service: DeviceIdentityService,
    ) -> None:
        ...
```

Public method:

```python
async def login(
    self,
    request: ClientLoginRequest,
) -> ClientAuthenticationResult:
    ...
```

---

# Chapter 1953 — Client Login Behaviour

```text
Validate local fields

↓

Negotiate protocol

↓

Retrieve or create device ID

↓

Submit credentials

↓

Immediately clear password reference

↓

Store refresh token securely

↓

Hold access token in session service

↓

Return authenticated identity
```

The plaintext password shall not enter the local database.

---

# Chapter 1954 — ClientSessionService Constructor

```python
class ClientSessionService:
    def __init__(
        self,
        api_client: ApiClient,
        secure_store: SecureStore,
        token_refresh_coordinator: TokenRefreshCoordinator,
        clock: Clock,
    ) -> None:
        ...
```

Public methods:

```python
async def get_access_token(self) -> str:
    ...

async def refresh(self) -> str:
    ...

async def logout(self) -> None:
    ...

async def handle_revocation(
        self,
        event: SessionRevokedEventData,
    ) -> None:
        ...
```

---

# Chapter 1955 — ApiClient Constructor

```python
class ApiClient:
    def __init__(
        self,
        settings: ServerConnectionSettings,
        tls_configuration: ClientTLSConfiguration,
        correlation_id_provider: CorrelationIdProvider,
        retry_executor: RetryExecutor,
        error_mapper: ApiErrorMapper,
        logger: BoundLogger,
    ) -> None:
        ...
```

The session-service dependency may be attached after unauthenticated startup to avoid a constructor cycle.

---

# Chapter 1956 — ApiClient Public Methods

```python
async def get(
    self,
    path: str,
    *,
    query: Mapping[str, object] | None = None,
    authenticated: bool = True,
) -> ApiResponse:
    ...

async def post_json(
    self,
    path: str,
    body: BaseModel,
    *,
    authenticated: bool = True,
    idempotency_key: str | None = None,
) -> ApiResponse:
    ...

async def put_stream(
    self,
    path: str,
    stream: AsyncIterator[bytes],
    headers: Mapping[str, str],
) -> ApiResponse:
    ...

async def stream_download(
    self,
    path: str,
) -> AsyncIterator[bytes]:
    ...
```

---

# Chapter 1957 — ApiClient Request Pipeline

```text
Build absolute URL

↓

Create correlation ID

↓

Attach safe headers

↓

Obtain access token if required

↓

Send request

↓

If 401 caused by expiry:

    Coordinate one refresh

    Retry original request once

↓

Parse success or error

↓

Apply retry policy only if safe

↓

Return typed result
```

The client shall never retry an unsafe request without idempotency protection.

---

# Chapter 1958 — TokenRefreshCoordinator Blueprint

```python
class TokenRefreshCoordinator:
    def __init__(
        self,
        refresh_operation: Callable[[], Awaitable[str]],
    ) -> None:
        self._lock = asyncio.Lock()
        self._active_task: asyncio.Task[str] | None = None
```

Public method:

```python
async def refresh(self) -> str:
    ...
```

All waiting callers shall receive the same refresh result.

---

# Chapter 1959 — WebSocketClient Constructor

```python
class WebSocketClient:
    def __init__(
        self,
        settings: ServerConnectionSettings,
        session_service: ClientSessionService,
        event_dispatcher: ClientEventDispatcher,
        connectivity_monitor: ConnectivityMonitor,
        retry_policy: RetryPolicy,
        logger: BoundLogger,
    ) -> None:
        ...
```

State:

```text
_connection
_receive_task
_heartbeat_task
_reconnect_task
_last_event_id
_state
_stop_requested
```

---

# Chapter 1960 — WebSocketClient Public Methods

```python
async def connect(self) -> None:
    ...

async def disconnect(self) -> None:
    ...

async def send_event(
        self,
        event: WebSocketEventEnvelope,
    ) -> None:
        ...

async def wait_until_connected(
        self,
        timeout: float,
    ) -> None:
        ...
```

Only one active connection attempt shall run at a time.

---

# Chapter 1961 — WebSocket Reconnection Behaviour

On unexpected loss:

```text
Mark offline

↓

Stop heartbeat

↓

Notify connectivity monitor

↓

Wait using bounded backoff

↓

Refresh access token if required

↓

Reconnect

↓

Authenticate

↓

Submit last event identifier

↓

Trigger synchronisation

↓

Mark connected
```

Manual logout shall suppress reconnection.

---

# Chapter 1962 — ClientEventDispatcher Blueprint

```python
class ClientEventDispatcher:
    def __init__(
        self,
        handlers: Mapping[WebSocketEventType, ClientEventHandler],
        error_service: ClientErrorService,
    ) -> None:
        ...
```

Public method:

```python
async def dispatch(
    self,
    envelope: WebSocketEventEnvelope,
) -> None:
    ...
```

Duplicate event IDs shall be ignored or reconciled idempotently.

---

# Chapter 1963 — ClientKeyManager Constructor

```python
class ClientKeyManager:
    def __init__(
        self,
        private_key_store: EncryptedPrivateKeyStore,
        public_key_service: ClientPublicKeyService,
        secure_random: SecureRandom,
        clock: Clock,
    ) -> None:
        ...
```

Public methods:

```python
async def ensure_identity_keys(
    self,
        user_id: UUID,
    ) -> PublicIdentityKeys:
        ...

async def get_private_encryption_key(
    self,
    version: int,
) -> PrivateKeyHandle:
    ...

async def get_private_signing_key(
    self,
    version: int,
) -> PrivateKeyHandle:
    ...

async def rotate_keys(self) -> PublicIdentityKeys:
    ...
```

Private-key bytes should be exposed as narrowly as possible.

---

# Chapter 1964 — EncryptedPrivateKeyStore Blueprint

```python
class EncryptedPrivateKeyStore:
    def __init__(
        self,
        storage_path: Path,
        key_protection_service: KeyProtectionService,
        local_encryption_service: LocalEncryptionService,
    ) -> None:
        ...
```

Public methods:

```python
async def unlock(
    self,
    unlock_key: bytes,
) -> None:
    ...

async def lock(self) -> None:
    ...

async def store_key(
    self,
    key: PrivateKeyRecord,
) -> None:
    ...

async def load_key(
    self,
    key_type: PrivateKeyType,
    version: int,
) -> PrivateKeyHandle:
    ...
```

---

# Chapter 1965 — Private-Key Store State

State:

```text
_unlocked
_unlock_key_handle
_loaded_key_handles
_lock
```

On logout:

* Loaded key handles shall be released.
* In-memory references shall be cleared where practical.
* The store shall return to locked state.

---

# Chapter 1966 — MessageEncryptionService Constructor

```python
class MessageEncryptionService:
    def __init__(
        self,
        key_manager: ClientKeyManager,
        canonical_serialiser: MessageCanonicalSerialiser,
        content_cipher: ContentCipher,
        key_envelope_cipher: KeyEnvelopeCipher,
        signature_service: SignatureService,
        secure_random: SecureRandom,
        protocol_version: int,
    ) -> None:
        ...
```

---

# Chapter 1967 — Message Encryption Contract

```python
async def encrypt_message(
    self,
    command: EncryptMessageCommand,
) -> SendMessageRequest:
    ...
```

Command fields:

```text
message ID
conversation ID
sender ID
message type
plaintext content
reply target
recipient public keys
client timestamp
attachment IDs
```

The plaintext shall not be retained after request construction longer than necessary.

---

# Chapter 1968 — Message Encryption Workflow

```text
Serialise plaintext content

↓

Generate random content key

↓

Generate unique nonce

↓

Build authenticated data

↓

Encrypt plaintext

↓

Create recipient key envelope for each participant

↓

Build canonical signed fields

↓

Sign envelope

↓

Return SendMessageRequest
```

The sender shall receive their own key envelope.

---

# Chapter 1969 — Message Decryption Contract

```python
async def decrypt_message(
    self,
    response: EncryptedMessageResponse,
) -> DecryptedMessage:
    ...
```

Workflow:

```text
Retrieve sender signing key

↓

Verify signature

↓

Retrieve recipient key envelope

↓

Load matching private encryption key

↓

Decrypt content key

↓

Rebuild authenticated data

↓

Decrypt payload

↓

Parse validated plaintext structure

↓

Return decrypted model
```

No plaintext shall be returned after failed verification.

---

# Chapter 1970 — SignatureService Blueprint

```python
class SignatureService:
    def sign(
        self,
        private_key: PrivateKeyHandle,
        data: bytes,
    ) -> bytes:
        ...

    def verify(
        self,
        public_key: bytes,
        data: bytes,
        signature: bytes,
    ) -> bool:
        ...
```

The service shall use one configured supported signature construction.

---

# Chapter 1971 — AttachmentEncryptionService Constructor

```python
class AttachmentEncryptionService:
    def __init__(
        self,
        content_cipher: ContentCipher,
        key_envelope_cipher: KeyEnvelopeCipher,
        checksum_service: ChecksumService,
        secure_random: SecureRandom,
        protocol_version: int,
    ) -> None:
        ...
```

Public methods:

```python
def generate_file_key(self) -> bytes:
    ...

async def encrypt_file(
    self,
    command: PrepareAttachmentCommand,
    cancellation_token: CancellationToken,
) -> PreparedUpload:
    ...

async def decrypt_download(
    self,
    command: DecryptAttachmentCommand,
    cancellation_token: CancellationToken,
) -> Path:
    ...
```

---

# Chapter 1972 — Attachment Encryption Memory Rule

`encrypt_file()` shall:

* Open the source file once.
* Read one bounded chunk.
* Update plaintext hash.
* Encrypt chunk.
* Write encrypted temporary output.
* Clear plaintext buffer reference.
* Continue.

It shall not call:

```python
path.read_bytes()
```

for potentially large files.

---

# Chapter 1973 — LocalEncryptionService Blueprint

```python
class LocalEncryptionService:
    def __init__(
        self,
        key_provider: LocalKeyProvider,
        content_cipher: ContentCipher,
        secure_random: SecureRandom,
    ) -> None:
        ...
```

Public methods:

```python
async def encrypt(
    self,
    purpose: LocalEncryptionPurpose,
    plaintext: bytes,
    context: bytes,
) -> EncryptedLocalValue:
    ...

async def decrypt(
    self,
    purpose: LocalEncryptionPurpose,
    value: EncryptedLocalValue,
    context: bytes,
) -> bytes:
    ...
```

Different purposes shall use different keys or derived key contexts.

---

# Chapter 1974 — ClientConversationService Constructor

```python
class ClientConversationService:
    def __init__(
        self,
        api_client: ApiClient,
        conversation_repository: CachedConversationRepository,
        user_repository: CachedUserRepository,
        synchronisation_state_repository: SynchronisationStateRepository,
        clock: Clock,
    ) -> None:
        ...
```

Public methods:

```python
async def load_cached(
    self,
) -> list[ConversationSummaryModel]:
    ...

async def refresh(
    self,
) -> list[ConversationSummaryModel]:
    ...

async def create_direct(
    self,
    target_user_id: UUID,
) -> ConversationModel:
    ...

async def create_group(
    self,
    request: CreateGroupConversationRequest,
) -> ConversationModel:
    ...
```

---

# Chapter 1975 — ClientMessagingService Constructor

```python
class ClientMessagingService:
    def __init__(
        self,
        api_client: ApiClient,
        encryption_service: MessageEncryptionService,
        conversation_service: ClientConversationService,
        message_repository: CachedMessageRepository,
        draft_repository: DraftRepository,
        offline_queue_service: OfflineQueueService,
        search_service: LocalSearchService,
        clock: Clock,
        identifier_generator: IdentifierGenerator,
    ) -> None:
        ...
```

---

# Chapter 1976 — ClientMessagingService Send Contract

```python
async def send_message(
    self,
    command: SendClientMessageCommand,
) -> ClientMessage:
    ...
```

The service shall:

* Validate draft.
* Generate or reuse message UUID.
* Load current members and keys.
* Create local pending model.
* Encrypt request.
* Store pending state.
* Submit immediately or enqueue.
* Reconcile acknowledgement.
* Remove draft only after storage acknowledgement.

---

# Chapter 1977 — Incoming Message Contract

```python
async def process_incoming(
    self,
    response: EncryptedMessageResponse,
) -> ClientMessage:
    ...
```

The service shall:

* Deduplicate.
* Verify and decrypt.
* Save encrypted transport data.
* Save encrypted local display cache if allowed.
* Update conversation summary.
* Update search index.
* Emit message-added event to ViewModels.
* Send delivery acknowledgement.

---

# Chapter 1978 — OfflineQueueService Constructor

```python
class OfflineQueueService:
    def __init__(
        self,
        repository: OfflineActionRepository,
        local_encryption_service: LocalEncryptionService,
        action_executor: OfflineActionExecutor,
        connectivity_monitor: ConnectivityMonitor,
        retry_policy: RetryPolicy,
        clock: Clock,
    ) -> None:
        ...
```

Public methods:

```python
async def enqueue(
    self,
    action: PendingOfflineAction,
) -> OfflineAction:
    ...

async def process_pending(self) -> QueueProcessingResult:
    ...

async def retry_now(
    self,
    action_id: UUID,
) -> None:
    ...

async def cancel(
    self,
    action_id: UUID,
) -> None:
    ...
```

---

# Chapter 1979 — Offline Queue Concurrency

The queue shall prevent two simultaneous processors.

Use:

```text
_processing_lock
```

Processing rules:

* Preserve order within conversation.
* Allow later parallelism only after correctness.
* Stop processing on lost connectivity.
* Continue past permanently failed unrelated actions.
* Persist every state transition.

---

# Chapter 1980 — SynchronisationService Constructor

```python
class SynchronisationService:
    def __init__(
        self,
        api_client: ApiClient,
        conversation_service: ClientConversationService,
        messaging_service: ClientMessagingService,
        public_key_service: ClientPublicKeyService,
        policy_service: ClientPolicyService,
        state_repository: SynchronisationStateRepository,
        offline_queue_service: OfflineQueueService,
        clock: Clock,
    ) -> None:
        ...
```

---

# Chapter 1981 — SynchronisationService Public Methods

```python
async def initial_sync(
    self,
    cancellation_token: CancellationToken,
) -> SynchronisationResult:
    ...

async def reconnect_sync(
    self,
    last_event_id: UUID | None,
) -> SynchronisationResult:
    ...

async def full_resync_scope(
    self,
    scope: SynchronisationScope,
) -> SynchronisationResult:
    ...
```

---

# Chapter 1982 — Synchronisation Ordering

Initial synchronisation shall use this order:

```text
Capabilities and policy

↓

Current user profile

↓

Conversation summaries

↓

Membership changes

↓

Public-key changes

↓

Unread message pages

↓

Announcement state

↓

Offline queue processing
```

The offline queue shall not process until current permissions and membership are refreshed.

---

# Chapter 1983 — FileTransferService Constructor

```python
class FileTransferService:
    def __init__(
        self,
        api_client: ApiClient,
        attachment_crypto: AttachmentEncryptionService,
        transfer_repository: TransferStateRepository,
        transfer_path_service: TransferPathService,
        upload_worker_factory: UploadWorkerFactory,
        download_worker_factory: DownloadWorkerFactory,
        settings: EffectiveClientSettings,
    ) -> None:
        ...
```

Public methods:

```python
async def prepare_upload(
    self,
    path: Path,
    conversation_id: UUID,
) -> PreparedUpload:
    ...

async def start_upload(
    self,
    prepared_upload: PreparedUpload,
) -> FileTransfer:
    ...

async def start_download(
    self,
    attachment_id: UUID,
    destination: Path,
) -> FileTransfer:
    ...

async def pause(
    self,
    transfer_id: UUID,
) -> None:
    ...

async def resume(
    self,
    transfer_id: UUID,
) -> None:
    ...
```

---

# Chapter 1984 — UploadWorker Constructor

```python
class UploadWorker(QObject):
    progress_changed = Signal(object)
    state_changed = Signal(str)
    completed = Signal(object)
    failed = Signal(object)

    def __init__(
        self,
        prepared_upload: PreparedUpload,
        api_client: ApiClient,
        transfer_repository: TransferStateRepository,
        bandwidth_limiter: BandwidthLimiter,
        cancellation_token: CancellationToken,
    ) -> None:
        super().__init__()
```

The worker shall not access UI widgets directly.

---

# Chapter 1985 — UploadWorker Run Contract

```python
async def run(self) -> AttachmentResponse:
    ...
```

Stages:

```text
INITIALISING
RESUMING
UPLOADING
VERIFYING
FINALISING
COMPLETE
```

Every state change shall be persisted before emitting the corresponding signal where practical.

---

# Chapter 1986 — DownloadWorker Constructor

```python
class DownloadWorker(QObject):
    progress_changed = Signal(object)
    state_changed = Signal(str)
    completed = Signal(object)
    failed = Signal(object)

    def __init__(
        self,
        attachment_id: UUID,
        destination: Path,
        api_client: ApiClient,
        attachment_crypto: AttachmentEncryptionService,
        transfer_repository: TransferStateRepository,
        bandwidth_limiter: BandwidthLimiter,
        cancellation_token: CancellationToken,
    ) -> None:
        super().__init__()
```

---

# Chapter 1987 — DownloadWorker Safety

The worker shall:

* Write to a partial file.
* Verify every encrypted chunk.
* Decrypt in order.
* Calculate plaintext hash.
* Compare expected hash.
* Close file handles.
* Rename atomically.
* Remove unsafe partial plaintext after permanent failure.

---

# Chapter 1988 — LocalSearchService Constructor

```python
class LocalSearchService:
    def __init__(
        self,
        search_repository: SearchIndexRepository,
        message_repository: CachedMessageRepository,
        local_encryption_service: LocalEncryptionService,
        search_token_service: SearchTokenService,
    ) -> None:
        ...
```

Public methods:

```python
async def index_message(
    self,
    message: DecryptedMessage,
) -> None:
    ...

async def remove_message(
    self,
    message_id: UUID,
) -> None:
    ...

async def search(
    self,
    query: SearchQuery,
) -> list[SearchResult]:
    ...

async def rebuild(
    self,
    cancellation_token: CancellationToken,
) -> SearchIndexReport:
    ...
```

---

# Chapter 1989 — SearchTokenService Blueprint

```python
class SearchTokenService:
    def __init__(
        self,
        search_key_provider: SearchKeyProvider,
    ) -> None:
        ...

    def normalise(
        self,
        text: str,
    ) -> list[str]:
        ...

    def token_digest(
        self,
        token: str,
    ) -> bytes:
        ...
```

Token digests shall use HMAC-SHA-256 with a user-specific local key.

---

# Chapter 1990 — CacheManager Constructor

```python
class CacheManager:
    def __init__(
        self,
        cache_repository: CacheEntryRepository,
        path_service: ClientPathService,
        settings_provider: EffectiveSettingsProvider,
        clock: Clock,
        logger: BoundLogger,
    ) -> None:
        ...
```

Public methods:

```python
async def calculate_usage(self) -> LocalStorageUsage:
    ...

async def enforce_limits(self) -> CacheCleanupResult:
    ...

async def clear(
        self,
        options: CacheClearOptions,
    ) -> CacheClearResult:
    ...
```

Cache deletion shall update metadata transactionally.

---

# Chapter 1991 — NotificationManager Constructor

```python
class NotificationManager:
    def __init__(
        self,
        platform_notifier: PlatformNotifier,
        preference_service: ClientSettingsService,
        conversation_repository: CachedConversationRepository,
        active_window_tracker: ActiveWindowTracker,
    ) -> None:
        ...
```

Public method:

```python
async def notify_message(
    self,
    message: ClientMessage,
    conversation: ConversationSummaryModel,
) -> None:
    ...
```

The manager shall receive already decrypted authorised display content.

---

# Chapter 1992 — BaseViewModel Blueprint

```python
class BaseViewModel(QObject):
    busy_changed = Signal(bool)
    error_occurred = Signal(object)

    def __init__(
        self,
        error_service: ClientErrorService,
    ) -> None:
        super().__init__()
        self._busy = False
        self._disposed = False
```

Public methods:

```python
def dispose(self) -> None:
    ...

@property
def is_busy(self) -> bool:
    ...
```

ViewModels shall stop responding after disposal.

---

# Chapter 1993 — LoginViewModel Constructor

```python
class LoginViewModel(BaseViewModel):
    login_succeeded = Signal(object)
    connection_status_changed = Signal(str)
    validation_changed = Signal()

    def __init__(
        self,
        authentication_service: ClientAuthenticationService,
        connectivity_service: ClientConnectivityService,
        error_service: ClientErrorService,
    ) -> None:
        ...
```

State:

```text
server_address
username
password
is_busy
validation_errors
connection_status
```

---

# Chapter 1994 — LoginViewModel Public Methods

```python
async def test_connection(self) -> None:
    ...

async def login(self) -> None:
    ...

def clear_password(self) -> None:
    ...

def validate(self) -> bool:
    ...
```

Duplicate login submissions shall be ignored while busy.

---

# Chapter 1995 — MainViewModel Constructor

```python
class MainViewModel(BaseViewModel):
    connection_state_changed = Signal(str)
    navigation_changed = Signal(str)
    unread_count_changed = Signal(int)
    logout_requested = Signal()

    def __init__(
        self,
        current_user: CurrentUserModel,
        connectivity_monitor: ConnectivityMonitor,
        synchronisation_service: SynchronisationService,
        notification_service: NotificationManager,
        error_service: ClientErrorService,
    ) -> None:
        ...
```

---

# Chapter 1996 — ConversationListViewModel Constructor

```python
class ConversationListViewModel(BaseViewModel):
    conversations_changed = Signal()
    selection_changed = Signal(object)

    def __init__(
        self,
        conversation_service: ClientConversationService,
        event_stream: ClientEventStream,
        error_service: ClientErrorService,
    ) -> None:
        ...
```

Public methods:

```python
async def load(self) -> None:
    ...

async def refresh(self) -> None:
    ...

def select(
    self,
    conversation_id: UUID,
) -> None:
    ...

def apply_filter(
    self,
    text: str,
) -> None:
    ...
```

---

# Chapter 1997 — ChatViewModel Constructor

```python
class ChatViewModel(BaseViewModel):
    messages_changed = Signal()
    draft_changed = Signal(str)
    typing_changed = Signal()
    send_state_changed = Signal(str)

    def __init__(
        self,
        conversation_id: UUID,
        messaging_service: ClientMessagingService,
        draft_repository: DraftRepository,
        transfer_service: FileTransferService,
        typing_service: ClientTypingService,
        event_stream: ClientEventStream,
        error_service: ClientErrorService,
    ) -> None:
        ...
```

---

# Chapter 1998 — ChatViewModel State

State:

```text
conversation_id
messages
draft_text
reply_target
editing_message
pending_attachments
has_more_history
loading_history
typing_users
send_state
```

The ViewModel owns presentation state but not permanent storage.

---

# Chapter 1999 — ChatViewModel Public Methods

```python
async def initialise(self) -> None:
    ...

async def load_older_messages(self) -> None:
    ...

async def send(self) -> None:
    ...

async def edit_message(
    self,
    message_id: UUID,
) -> None:
    ...

async def delete_message(
    self,
    message_id: UUID,
) -> None:
    ...

async def attach_files(
    self,
    paths: Sequence[Path],
) -> None:
    ...

def set_reply_target(
    self,
    message_id: UUID | None,
) -> None:
    ...
```

---

# Chapter 2000 — ChatViewModel Send Behaviour

```text
Validate non-empty content or attachment

↓

Set sending state

↓

Call ClientMessagingService

↓

On server acknowledgement:

    Clear draft

    Clear reply target

    Clear completed attachment selection

↓

On retryable failure:

    Keep pending item

↓

On permanent failure:

    Preserve content and display action
```

The ViewModel shall not create encrypted envelopes directly.

---

# Chapter 2001 — TransferListViewModel Blueprint

```python
class TransferListViewModel(BaseViewModel):
    transfers_changed = Signal()

    def __init__(
        self,
        transfer_service: FileTransferService,
        transfer_repository: TransferStateRepository,
        error_service: ClientErrorService,
    ) -> None:
        ...
```

Public methods:

```python
async def load(self) -> None:
    ...

async def pause(
    self,
    transfer_id: UUID,
) -> None:
    ...

async def resume(
    self,
    transfer_id: UUID,
) -> None:
    ...

async def cancel(
    self,
    transfer_id: UUID,
) -> None:
    ...
```

---

# Chapter 2002 — SearchViewModel Blueprint

```python
class SearchViewModel(BaseViewModel):
    results_changed = Signal()
    progress_changed = Signal(int)

    def __init__(
        self,
        search_service: LocalSearchService,
        navigation_service: NavigationService,
        error_service: ClientErrorService,
    ) -> None:
        ...
```

Public methods:

```python
async def search(self) -> None:
    ...

async def rebuild_index(self) -> None:
    ...

async def open_result(
    self,
    result: SearchResult,
) -> None:
    ...
```

Search operations shall be cancellable.

---

# Chapter 2003 — SettingsViewModel Blueprint

```python
class SettingsViewModel(BaseViewModel):
    settings_changed = Signal()
    restart_required_changed = Signal(bool)

    def __init__(
        self,
        settings_service: ClientSettingsService,
        cache_manager: CacheManager,
        session_service: ClientSessionService,
        error_service: ClientErrorService,
    ) -> None:
        ...
```

Public methods:

```python
async def load(self) -> None:
    ...

async def save(self) -> None:
    ...

async def clear_cache(
        self,
        options: CacheClearOptions,
    ) -> None:
        ...

async def revoke_session(
        self,
        session_id: UUID,
    ) -> None:
        ...
```

---

# Chapter 2004 — DashboardViewModel Blueprint

```python
class DashboardViewModel(BaseViewModel):
    dashboard_changed = Signal()
    auto_refresh_changed = Signal(bool)

    def __init__(
        self,
        admin_service: ClientAdminService,
        refresh_scheduler: RefreshScheduler,
        error_service: ClientErrorService,
    ) -> None:
        ...
```

Public methods:

```python
async def refresh(self) -> None:
    ...

def start_auto_refresh(self) -> None:
    ...

def stop_auto_refresh(self) -> None:
    ...
```

The refresh scheduler shall stop when the page is hidden or disposed.

---

# Chapter 2005 — ViewModelFactory Blueprint

```python
class ViewModelFactory:
    def __init__(
        self,
        services: ClientServices,
        repositories: ClientRepositories,
        event_stream: ClientEventStream,
        error_service: ClientErrorService,
    ) -> None:
        ...
```

Factory methods:

```python
def create_login(self) -> LoginViewModel:
    ...

def create_main(self) -> MainViewModel:
    ...

def create_conversation_list(self) -> ConversationListViewModel:
    ...

def create_chat(
    self,
    conversation_id: UUID,
) -> ChatViewModel:
    ...

def create_settings(self) -> SettingsViewModel:
    ...
```

The factory shall not cache disposable conversation-specific ViewModels indefinitely.

---

# Chapter 2006 — View Constructor Rules

A view constructor shall normally receive:

```text
ViewModel
Parent widget
Optional presentation-only dependencies
```

Example:

```python
class ChatPage(QWidget):
    def __init__(
        self,
        viewmodel: ChatViewModel,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
```

Views shall not receive database repositories or cryptographic services.

---

# Chapter 2007 — Signal Connection Rules

Views shall:

* Connect signals during setup.
* Disconnect or dispose cleanly.
* Avoid duplicate signal registration.
* Avoid anonymous lambdas when they prevent cleanup.
* Use queued connections where cross-thread delivery requires it.
* Update widgets only on the GUI thread.

---

# Chapter 2008 — Worker-to-ViewModel Communication

Workers shall emit:

```text
progress
state
completion
failure
```

ViewModels shall translate worker events into UI state.

Views shall observe ViewModels.

Preferred flow:

```text
Worker

↓

Service

↓

ViewModel

↓

View
```

Direct worker-to-widget coupling shall be avoided.

---

# Chapter 2009 — ClientEventStream Blueprint

```python
class ClientEventStream:
    """Provides local publish-subscribe communication between client services."""

    def subscribe(
        self,
        event_type: type[ClientApplicationEvent],
        handler: ClientEventHandler,
    ) -> Subscription:
        ...

    async def publish(
        self,
        event: ClientApplicationEvent,
    ) -> None:
        ...
```

Subscriptions shall be disposable to prevent memory leaks.

---

# Chapter 2010 — ClientErrorService Blueprint

```python
class ClientErrorService:
    def __init__(
        self,
        catalogue: ErrorMessageCatalog,
        logger: BoundLogger,
    ) -> None:
        ...
```

Public methods:

```python
def map_exception(
    self,
    exception: BaseException,
) -> ClientError:
    ...

def log(
    self,
    error: ClientError,
    exception: BaseException | None = None,
) -> None:
    ...
```

The service shall prevent raw exception text being displayed automatically.

---

# Chapter 2011 — DiagnosticPackageService Blueprint

```python
class DiagnosticPackageService:
    def __init__(
        self,
        log_collector: SanitisedLogCollector,
        diagnostic_services: Sequence[ClientDiagnosticCheck],
        archive_writer: DiagnosticArchiveWriter,
        application_info: ApplicationInfo,
    ) -> None:
        ...
```

Public method:

```python
async def create(
    self,
    destination: Path,
    cancellation_token: CancellationToken,
) -> Path:
    ...
```

The generated archive shall be validated before completion.

---

# Chapter 2012 — CircuitBreaker Blueprint

```python
class CircuitBreaker:
    def __init__(
        self,
        settings: CircuitBreakerSettings,
        clock: Clock,
    ) -> None:
        ...
```

Public method:

```python
async def execute(
    self,
    operation: Callable[[], Awaitable[T]],
) -> T:
    ...
```

State:

```text
state
failure_count
opened_at
half_open_attempts
lock
```

Only dependency-classified failures shall increment the circuit failure count.

---

# Chapter 2013 — RetryExecutor Blueprint

```python
class RetryExecutor:
    def __init__(
        self,
        policy_registry: RetryPolicyRegistry,
        sleep: AsyncSleep,
        secure_random: SecureRandom,
    ) -> None:
        ...
```

Public method:

```python
async def execute(
    self,
    operation: Callable[[], Awaitable[T]],
    context: RetryContext,
) -> T:
    ...
```

It shall:

* Check idempotency.
* Check cancellation.
* Classify error.
* Apply bounded delay.
* Respect server retry-after.
* Preserve final exception.

---

# Chapter 2014 — MetricsCollector Blueprint

```python
class MetricsCollector:
    def increment(
        self,
        metric: MetricName,
        value: int = 1,
        labels: Mapping[str, str] | None = None,
    ) -> None:
        ...

    def observe(
        self,
        metric: MetricName,
        value: float,
        labels: Mapping[str, str] | None = None,
    ) -> None:
        ...

    def snapshot(self) -> MetricsSnapshot:
        ...
```

Labels shall not include:

* Message IDs.
* Usernames.
* Full paths.
* Tokens.
* Plaintext values.

---

# Chapter 2015 — Service Thread-Safety

Server services may be application singletons.

Therefore, they shall not store request-specific mutable state such as:

```text
current_user
current_session
current_transaction
current_conversation
```

Such data shall be passed into each method.

Shared mutable caches shall use safe concurrency controls.

---

# Chapter 2016 — Client Thread-Safety

Client services may be called from:

* Qt GUI task context.
* Async workers.
* WebSocket receive tasks.
* Synchronisation tasks.

Mutable shared client state shall be protected through:

* Async locks.
* Serialised repositories.
* Event-loop confinement.
* Qt queued signals.
* Immutable models where practical.

SQLite access shall follow one documented concurrency strategy.

---

# Chapter 2017 — SQLite Concurrency Strategy

Recommended:

```text
One local database manager

One controlled write queue or write lock

Short-lived read operations

WAL mode where compatible

No direct access from arbitrary worker threads
```

Database calls from Qt workers shall be scheduled through the approved async storage layer.

---

# Chapter 2018 — Resource Ownership

Ownership rules:

```text
DatabaseManager owns SQLAlchemy engine.

UnitOfWork owns one database session.

ServerContainer owns managers and workers.

WebSocketConnection owns one socket.

ClientContainer owns authenticated services.

LocalDatabaseManager owns SQLite connections.

Worker owns its cancellation token.

View owns its ViewModel lifecycle where created specifically for that view.
```

Every owned resource shall have a matching cleanup path.

---

# Chapter 2019 — Context Manager Usage

Use async context managers for:

* Unit of Work.
* Database sessions.
* File streams where supported.
* Temporary directories.
* Locks where needed.
* HTTP streaming responses.

Example:

```python
async with self._unit_of_work_factory() as unit_of_work:
    ...
```

Manual cleanup shall be avoided where a context manager provides stronger guarantees.

---

# Chapter 2020 — Important Immutable Models

Prefer frozen dataclasses or immutable Pydantic models for:

```text
AuthenticatedUser
AccessTokenClaims
PublicKeyDescriptor
MessageEncryptionContext
AttachmentEncryptionContext
ServerCapabilities
RetryPolicy
```

Immutable values reduce accidental state modification.

---

# Chapter 2021 — Mutable Domain Models

Mutable domain entities may be used where behaviour changes state explicitly.

Example:

```python
class Session:
    def invalidate(
        self,
        at: datetime,
        reason: str,
    ) -> None:
        ...
```

State-changing methods shall enforce invariants.

Repositories shall persist the resulting entity state.

---

# Chapter 2022 — Domain Method Versus Service Method

Use a domain method when:

* The rule concerns one entity.
* No database query is required.
* No external service is required.

Use a service method when:

* Multiple entities participate.
* Permissions must be checked.
* Repositories are required.
* A transaction is required.
* Events or audits are created.

Example:

```text
Session.invalidate()

Domain method

SessionService.invalidate_all_for_user()

Application service
```

---

# Chapter 2023 — Mapper Blueprint

Example:

```python
class MessageMapper:
    @staticmethod
    def to_domain(
        orm: MessageORM,
    ) -> Message:
        ...

    @staticmethod
    def to_response(
        message: Message,
        recipient_key: MessageRecipientKey,
    ) -> EncryptedMessageResponse:
        ...
```

Mappers shall not:

* Query repositories.
* Perform permission checks.
* Decrypt content.
* Commit transactions.

---

# Chapter 2024 — Factory Blueprint

Factories may construct complex domain objects.

Example:

```python
class MessageFactory:
    def __init__(
        self,
        clock: Clock,
    ) -> None:
        ...

    def create_from_request(
        self,
        sender_id: UUID,
        request: SendMessageRequest,
    ) -> Message:
        ...
```

Factories shall validate object construction invariants but not external authority.

---

# Chapter 2025 — EventFactory Blueprint

```python
class EventFactory:
    def __init__(
        self,
        clock: Clock,
        identifier_generator: IdentifierGenerator,
        protocol_version: int,
    ) -> None:
        ...
```

Public methods:

```python
def message_stored(
    self,
    message: Message,
    recipients: Sequence[UUID],
) -> OutboxEvent:
    ...

def session_revoked(
    self,
    session: Session,
) -> OutboxEvent:
    ...

def group_member_removed(
    self,
    conversation_id: UUID,
    user_id: UUID,
) -> OutboxEvent:
    ...
```

Payloads shall contain no plaintext message content.

---

# Chapter 2026 — State Transition Helper

```python
class StateTransitionValidator(Generic[StateType]):
    def __init__(
        self,
        allowed_transitions: Mapping[
            StateType,
            Collection[StateType],
        ],
    ) -> None:
        ...

    def require_transition(
        self,
        current: StateType,
        target: StateType,
    ) -> None:
        ...
```

This may support:

* File transfers.
* Upload sessions.
* Offline actions.
* Security alerts.
* Export jobs.

---

# Chapter 2027 — Error Translation Boundaries

Translation shall occur at these boundaries:

```text
Infrastructure library error

↓

Repository or infrastructure adapter error

↓

Application service error

↓

API or client error model
```

Example:

```text
OSError ENOSPC

↓

StorageCapacityError

↓

SERVER_STORAGE_FULL

↓

User-facing storage message
```

---

# Chapter 2028 — Method Logging Rules

A service method may log:

* Operation started at debug level.
* Successful significant result at info level.
* Expected degraded result at warning level.
* Unexpected failure at boundary.

It shall not log:

* Plaintext message.
* Plaintext draft.
* Password.
* Secret key.
* Raw token.
* Complete encrypted payload.

---

# Chapter 2029 — Method Metrics Rules

Important methods shall record:

```text
operation count
success count
failure count
duration
retry count where applicable
```

Examples:

```text
AuthenticationService.login
MessagingService.send_message
AttachmentService.complete_upload
SynchronisationService.initial_sync
```

Metrics shall be recorded around the operation boundary rather than inside every private helper.

---

# Chapter 2030 — Method Timeout Rules

External and infrastructure operations shall have bounded timeouts.

Examples:

```text
LDAP search
Redis command
HTTP request
WebSocket authentication
Storage health check
Database statement
```

Business methods shall not wait indefinitely for dependency calls.

---

# Chapter 2031 — Class Test Contract

Every important class shall have tests covering:

```text
Successful operation
Validation failure
Permission failure where applicable
Dependency failure
Cancellation where applicable
State transition
Resource cleanup
Sensitive-data handling
```

Constructor tests shall verify required dependencies and safe initial state where useful.

---

# Chapter 2032 — Service Collaboration Tests

Tests shall verify that:

* `AuthenticationService` calls provider but not LDAP implementation details.
* `MessagingService` uses repository interfaces.
* `AttachmentService` uses `FileStorage`.
* `ChatViewModel` uses client services, not API client directly.
* `MessageWidget` does not decrypt data.
* `AdminService` uses permission service.
* `AuditWriter` shares the business Unit of Work.

---

# Chapter 2033 — Mocking Guidance

Mock:

* External provider boundaries.
* Network clients.
* Operating-system secure store.
* Clock.
* Random provider where deterministic behaviour is needed.

Prefer fakes for:

* Repositories.
* Event publisher.
* File storage.
* Local cache.

Do not mock every internal helper in a way that prevents meaningful behaviour testing.

---

# Chapter 2034 — Method Documentation Contract

Public service methods shall document:

```text
Purpose
Authorisation expectation
Important validation
Return value
Expected application errors
Transactional behaviour
```

Example:

```python
async def send_message(...) -> SendMessageResponse:
    """Store one encrypted message.

    The sender must be an active conversation member. The operation
    validates complete recipient-key coverage and commits the message,
    audit event and outbox event in one transaction.

    Raises:
        NotConversationMemberError
        InvalidRecipientKeysError
        MessageConflictError
    """
```

---

# Chapter 2035 — No Boolean Ambiguity

Avoid methods such as:

```python
update_user(user_id, True, False, True)
```

Prefer:

```python
update_user(
    user_id,
    UserUpdate(
        is_enabled=True,
        is_archived=False,
        revoke_sessions=True,
    ),
)
```

Keyword-only parameters and typed command objects shall be used for complex operations.

---

# Chapter 2036 — Command Objects

Use command objects for complex writes.

Examples:

```text
SendClientMessageCommand
CreateGroupCommand
DisableUserCommand
PrepareAttachmentCommand
PublishAnnouncementCommand
UpdateConfigurationCommand
```

Commands shall be validated before the transaction begins.

---

# Chapter 2037 — Query Objects

Use query objects for complex reads.

Examples:

```text
ConversationListQuery
MessagePageQuery
AuditQuery
UserSearchQuery
SecurityAlertQuery
```

Query objects shall contain validated filters, limits and cursors.

---

# Chapter 2038 — Optional Values

Optional values shall use:

```python
Type | None
```

The meaning of `None` shall be documented.

For updates, distinguish:

```text
Field not supplied

from

Field explicitly cleared
```

Pydantic field-set information or dedicated patch models may be used.

---

# Chapter 2039 — Collection Types

Use:

```text
Sequence
Collection
Mapping
```

in interfaces where mutation is not required.

Return concrete immutable or list types where callers need predictable behaviour.

Avoid passing mutable lists that a callee may retain and modify unexpectedly.

---

# Chapter 2040 — Byte Handling

Binary security fields shall use:

```python
bytes
```

internally.

Base64 encoding and decoding shall occur at protocol boundaries.

Do not repeatedly encode and decode inside business services.

---

# Chapter 2041 — Secret Value Types

Use wrappers such as:

```text
SecretStr
SecretBytes
PrivateKeyHandle
RefreshTokenValue
```

where practical.

Secret wrappers shall prevent accidental representation in logs.

---

# Chapter 2042 — Async Task Ownership

Every created background task shall have an owner.

Examples:

```text
WebSocketClient owns receive and heartbeat tasks.

BackgroundWorker owns its loop task.

ClientApplication owns shutdown tasks.

UploadWorker owns chunk-transfer tasks.
```

Unowned `asyncio.create_task()` calls shall be avoided.

---

# Chapter 2043 — Task Failure Handling

Owned tasks shall:

* Be awaited or monitored.
* Report exceptions.
* Support cancellation.
* Be removed from owner state after completion.
* Not disappear silently.

Task callbacks shall retrieve exceptions to avoid unobserved task warnings.

---

# Chapter 2044 — Lock Ownership

Locks shall belong to the class protecting the state.

Examples:

```text
TokenRefreshCoordinator owns refresh lock.

WebSocketConnection owns send lock.

WebSocketConnectionManager owns registry lock.

OfflineQueueService owns processing lock.

Audit chain transaction owns database row lock.
```

Global unrelated locks shall not be used.

---

# Chapter 2045 — Deadlock Avoidance in Classes

Rules:

* Acquire locks in documented order.
* Do not hold an in-memory lock during slow network I/O unless required.
* Avoid calling unknown external handlers while holding a lock.
* Keep database row-lock transactions short.
* Do not combine Qt thread locks and asyncio locks unnecessarily.

---

# Chapter 2046 — Class Lifecycle Interfaces

Lifecycle-managed classes may implement:

```python
class AsyncLifecycle(Protocol):
    async def start(self) -> None:
        ...

    async def stop(self) -> None:
        ...
```

Examples:

```text
DatabaseManager
RedisManager
WebSocketClient
WebSocketConnectionManager
WorkerManager
ClientContainer
ServerContainer
```

---

# Chapter 2047 — Idempotent Lifecycle Methods

`stop()` should generally be idempotent.

`start()` may:

* Return immediately if already started.
* Raise a clear lifecycle error.
* Be idempotent where safe.

The behaviour shall be documented and tested.

---

# Chapter 2048 — Final Class Dependency Summary

Core server dependency chain:

```text
Routers
↓
Application Services
↓
Domain Rules and Repository Interfaces
↓
Unit of Work
↓
SQLAlchemy Repositories
↓
PostgreSQL
```

Additional infrastructure:

```text
Application Services
↓
AuditService
EventFactory
FileStorage
AuthenticationProvider
WebSocket Manager
```

Core client dependency chain:

```text
Views
↓
ViewModels
↓
Client Services
↓
Networking / Security / Local Repositories
↓
Server APIs / Secure Store / SQLite
```

No layer shall bypass the next appropriate abstraction without a documented reason.

---

# Chapter 2049 — Version 1.0 Mandatory Classes

The coding AI shall implement working versions of at least:

```text
ServerContainer
ClientContainer
DatabaseManager
RedisManager
UnitOfWork
AuthenticationService
SessionService
PermissionService
ConversationService
GroupService
MessagingService
AttachmentService
AuditService
AuditWriter
AuditIntegrityService
AdminService
MonitoringService
WebSocketConnectionManager
WebSocketEventDispatcher
EventPublisher
WorkerManager
OutboxPublisherWorker
ApiClient
WebSocketClient
ClientAuthenticationService
ClientSessionService
ClientConversationService
ClientMessagingService
SynchronisationService
OfflineQueueService
FileTransferService
MessageEncryptionService
AttachmentEncryptionService
LocalEncryptionService
ClientKeyManager
EncryptedPrivateKeyStore
LocalDatabaseManager
CacheManager
LocalSearchService
NotificationManager
LoginViewModel
MainViewModel
ConversationListViewModel
ChatViewModel
TransferListViewModel
SettingsViewModel
DashboardViewModel
```

---

# Chapter 2050 — Deferred Class Restrictions

The coding AI shall not create non-functional classes for:

```text
VoiceCallService
VideoCallService
RemoteDesktopService
FederationService
BotService
CloudSyncService
PluginMarketplaceService
```

Deferred features shall not increase the Version 1.0 maintenance burden.

---

# Chapter 2051 — Class Implementation Order

Recommended class implementation order:

```text
1. Shared value objects and DTOs

2. Domain models

3. Repository interfaces

4. ORM repositories

5. Unit of Work

6. Authentication and session infrastructure

7. Permission and user services

8. Conversation and group services

9. Messaging service

10. Attachment storage and service

11. Audit and outbox services

12. WebSocket infrastructure

13. Workers and monitoring

14. Client secure store and local database

15. Client networking and session management

16. Client key and encryption services

17. Client messaging, transfer and sync services

18. ViewModels

19. Views and widgets

20. Administration client classes
```

Each stage shall be tested before the next depends upon it.

---

# Chapter 2052 — Class Blueprint Summary

BlueBubbles shall use explicit constructor injection and clearly owned state.

Server services shall be stateless across requests except for safe shared caches and managers.

Database work shall use short-lived Units of Work.

Business transactions shall include their audit and outbox records where required.

Authentication providers shall only authenticate identities and shall not issue application sessions.

The server MessagingService shall validate and store encrypted envelopes without decrypting them.

Client encryption services shall own content encryption, recipient key envelopes and signatures.

The client MessagingService shall coordinate local pending state, encryption, offline queueing, server submission and incoming-message processing.

Long-running operations shall support cooperative cancellation.

Workers shall expose progress and shall not manipulate widgets directly.

ViewModels shall own presentation state and call services.

Views shall render state and emit user actions.

Every async task, lock, connection and worker shall have one clear owner and cleanup path.

The coding AI shall implement these class contracts consistently and shall not merge unrelated responsibilities into monolithic classes.

---

# End of Part 22

Part 23 will define the complete user-interface visual specification and interaction contract, including:

* Window dimensions and layouts.
* Navigation behaviour.
* Login interface.
* Conversation list.
* Chat page.
* Message bubbles.
* Composer.
* Contact and group interfaces.
* File-transfer presentation.
* Search interface.
* Settings.
* Administration pages.
* Dialogs.
* Themes.
* Keyboard interaction.
* Accessibility behaviour.
