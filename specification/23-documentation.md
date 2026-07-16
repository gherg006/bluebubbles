# Task 23 — Documentation

> This is a self-contained implementation task split from the complete BlueBubbles Version 1.0 specification. Source requirements below are reproduced verbatim, not summarised. Where a repeated project-wide rule conflicts with a task-local choice, the project-wide rule wins.

## Required predecessors

Task 22.

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

# Chapter 3415 — Documentation Output

The final delivery shall include:

```text
README.md
Architecture.md
Security.md
Cryptography.md
Database.md
API.md
WebSocket.md
Client.md
Administration.md
Installation.md
Configuration.md
Active-Directory.md
Backup.md
Restore.md
Upgrade.md
Rollback.md
Operations.md
Testing.md
Known-Limitations.md
User-Guide.md
Administrator-Guide.md
Developer-Guide.md
```

Documentation names may vary, but equivalent coverage is mandatory.

---

---

## Task-specific authoritative source: Part 27

# Part 27 — Implementation Roadmap and Development-Phase Plan

---

# Chapter 2758 — Roadmap Purpose

This section defines the order in which BlueBubbles shall be designed, implemented, tested and documented.

The roadmap shall ensure that:

* High-risk architecture decisions are tested early.
* Security-critical foundations exist before dependent features.
* Each milestone produces a working result.
* Database migrations remain controlled.
* Client and server contracts stay aligned.
* Cryptography is tested before production messaging depends upon it.
* Automated tests grow with the implementation.
* Documentation is updated continuously.
* Deferred features do not delay Version 1.0.
* The final application can be demonstrated reliably.

The coding AI shall follow the dependency order defined here rather than implementing visually impressive but unsupported features first.

---

# Chapter 2759 — Development Principles

Development shall follow these principles:

```text
Build vertically in tested increments.

Implement foundations before presentation.

Keep the application executable throughout development.

Write tests with each subsystem.

Do not postpone security until the end.

Do not postpone database migrations until the end.

Do not generate every file before running the project.

Do not build the full interface against imaginary services.

Do not optimise before measuring.

Do not add deferred features during Version 1.0 stabilisation.
```

---

# Chapter 2760 — Development Environments

The project shall use separate environments:

```text
Development

Automated testing

Demonstration

Production
```

Development:

* Local or isolated VM.
* Debug logging.
* Synthetic users.
* Mock or test directory provider.
* Replaceable test data.
* No real organisational data.

Testing:

* Disposable PostgreSQL database.
* Disposable Redis instance.
* Temporary filesystem storage.
* Deterministic configuration.
* Automated setup and cleanup.

Demonstration:

* Stable sample data.
* Production-like deployment.
* Clearly labelled as demonstration.
* No real credentials.
* Reliable scripted scenarios.

Production:

* Secure configuration.
* Real TLS.
* Protected secrets.
* Restricted logging.
* Controlled deployment.

---

# Chapter 2761 — Source-Control Strategy

The project shall use Git.

Recommended branches:

```text
main

Stable and releasable code.

development

Integrated development work where used.

feature/<name>

One feature or subsystem.

fix/<name>

One correction.

release/<version>

Optional release stabilisation.
```

For a single-developer NEA, a simpler structure is acceptable:

```text
main
feature branches
```

The main branch shall remain buildable.

---

# Chapter 2762 — Commit Requirements

Commits shall:

* Contain one coherent change.
* Use clear descriptions.
* Include tests for changed behaviour.
* Avoid committing secrets.
* Avoid committing generated build output unnecessarily.
* Avoid combining unrelated refactoring and features.
* Record migration files with matching model changes.

Example messages:

```text
Add typed server configuration loader

Implement user and session schema

Add message envelope canonicalisation tests

Fix upload resume conflict handling
```

---

# Chapter 2763 — Quality Gate Definition

A development phase shall not be considered complete until its gate passes.

A typical quality gate requires:

```text
Formatting passes

Linting passes

Type checking passes

Unit tests pass

Relevant integration tests pass

Database migrations apply from empty state

Application starts where applicable

Documentation reflects the implementation

No known critical security defect remains
```

---

# Chapter 2764 — Continuous Verification Command

The repository should provide one command or script such as:

```text
python scripts/development/run_quality_checks.py
```

or:

```text
make check
```

It shall run the standard local checks in a deterministic order.

Suggested sequence:

```text
Format verification

Linting

Type checking

Unit tests

Selected integration tests

Architecture boundary tests

Secret-pattern scan
```

---

# Chapter 2765 — Roadmap Phase Overview

The Version 1.0 roadmap shall use these phases:

```text
Phase 0 — Requirements and architecture confirmation

Phase 1 — Repository and development foundations

Phase 2 — Shared contracts and configuration

Phase 3 — Database and persistence foundations

Phase 4 — Server lifecycle and health

Phase 5 — Authentication and session management

Phase 6 — Users, contacts and public keys

Phase 7 — Conversations and groups

Phase 8 — Message cryptography prototype

Phase 9 — Encrypted messaging integration

Phase 10 — WebSocket realtime communication

Phase 11 — Attachment encryption and transfer

Phase 12 — Client local storage and offline queue

Phase 13 — Desktop interface implementation

Phase 14 — Administration, audit and monitoring

Phase 15 — Synchronisation and conflict recovery

Phase 16 — Deployment and packaging

Phase 17 — Security, performance and usability testing

Phase 18 — Documentation and NEA evidence

Phase 19 — Release candidate and Version 1.0 completion
```

---

# Chapter 2766 — Phase 0: Requirements Confirmation

Objectives:

* Confirm the Version 1.0 scope.
* Confirm user roles.
* Confirm LAN-only deployment.
* Confirm supported operating systems.
* Confirm one primary cryptographic device per user.
* Confirm Active Directory availability.
* Confirm attachment size target.
* Confirm group-size target.
* Confirm retention expectations.
* Confirm evaluation criteria.

Outputs:

```text
Final functional requirements

Final non-functional requirements

Scope exclusions

Architecture diagram

Data-flow diagram

Threat model

Initial risk register

Acceptance-test list
```

---

# Chapter 2767 — Phase 0 Exit Gate

Phase 0 passes when:

* Every Version 1.0 feature is named.
* Every deferred feature is recorded.
* The server trust boundary is documented.
* The client trust boundary is documented.
* Encryption limitations are documented.
* Required infrastructure is known.
* No major unresolved requirement blocks implementation.
* The user journeys are sufficient to guide interface work.

---

# Chapter 2768 — Phase 0 Requirement Traceability

Each requirement shall receive an identifier.

Examples:

```text
FR-AUTH-001

User can authenticate using Active Directory.

FR-MSG-004

A sender can send an encrypted direct message.

NFR-SEC-003

The server shall not store plaintext message bodies.

NFR-PERF-002

The conversation list shall load within the defined target.
```

Requirements shall later map to:

* Design sections.
* Source modules.
* Tests.
* Evaluation evidence.

---

# Chapter 2769 — Phase 1: Repository Foundations

Implement:

```text
Repository root files
src package layout
shared package
server package
client package
tests package
pyproject.toml
linting configuration
type-checking configuration
pytest configuration
logging skeleton
version source
development scripts
```

The project shall import successfully before feature implementation begins.

---

# Chapter 2770 — Phase 1 Development Tooling

Configure:

```text
Ruff

Formatting and linting.

mypy

Static type checking.

pytest

Automated testing.

coverage

Test coverage measurement.

Alembic

Database migrations.

pre-commit where used

Local quality hooks.
```

The exact tool versions shall be locked.

---

# Chapter 2771 — Phase 1 Minimal Executables

Server executable:

```text
Starts
Loads minimal development configuration
Exposes one liveness endpoint
Stops cleanly
```

Client executable:

```text
Starts QApplication
Displays a simple development window
Closes cleanly
Logs version safely
```

No database, login or messaging is required yet.

---

# Chapter 2772 — Phase 1 Tests

Required tests:

```text
Shared package imports
Server package imports
Client package imports
Application version resolves
Server application factory returns FastAPI
Client application starts in test mode
Package dependency rules pass
No obvious hard-coded secret markers exist
```

---

# Chapter 2773 — Phase 1 Exit Gate

Phase 1 passes when:

* A clean environment can install dependencies.
* The server starts.
* The client starts.
* Standard quality checks pass.
* The project has no circular imports.
* The version is sourced consistently.
* The repository layout matches the specification.

---

# Chapter 2774 — Phase 2: Shared Contracts

Implement shared:

```text
Enums
Identifiers
Error codes
REST DTOs
WebSocket envelopes
Protocol negotiation models
Cryptographic envelope models
Pagination models
Health models
Canonical serialisation helpers
```

Server and client shall import the same public protocol definitions.

---

# Chapter 2775 — Phase 2 Protocol Decisions

Freeze Version 1.0 identifiers for:

```text
Protocol version
Message types
Conversation types
Delivery states
Attachment states
WebSocket event types
Error codes
Algorithm identifiers
Cryptographic format versions
```

After integration begins, these values shall not change casually.

---

# Chapter 2776 — Phase 2 Canonicalisation Prototype

Before message encryption is implemented fully, create deterministic tests for:

```text
UUID serialisation
Timestamp serialisation
Binary encoding
Object key ordering
Recipient ordering
Message AAD
Signed envelope bytes
```

Canonicalisation defects must be found before encrypted records are stored.

---

# Chapter 2777 — Phase 2 Exit Gate

Phase 2 passes when:

* Client and server can serialise and parse the same DTO fixtures.
* Unknown enum values fail safely.
* Invalid binary lengths fail validation.
* Protocol negotiation tests pass.
* Canonical test vectors are stable.
* Public error mappings are complete enough for the next phases.

---

# Chapter 2778 — Phase 3: Database Foundations

Implement first migrations for:

```text
Roles
Permissions
Role permissions
Users
Local credentials
Sessions
Login attempts
Public keys
Contacts
```

Then add:

```text
Conversations
Direct conversation pairs
Conversation members
Messages
Recipient keys
Attachments
Audit
Outbox
Administration tables
```

Migrations may be divided into smaller tested steps.

---

# Chapter 2779 — Phase 3 ORM Implementation

Implement:

```text
Declarative base
Naming conventions
ORM models
Async engine
Session factory
Unit of Work
Repository interfaces
SQLAlchemy repositories
ORM-to-domain mappers
Migration revision checks
```

Business services shall not yet contain full feature logic.

---

# Chapter 2780 — Phase 3 Database Test Infrastructure

Automated tests shall:

```text
Create temporary PostgreSQL database

Apply all migrations

Run repository tests

Roll back or destroy database

Repeat from empty state
```

SQLite shall not replace PostgreSQL in server integration tests.

---

# Chapter 2781 — Phase 3 Migration Checks

Verify:

* Empty database upgrades to head.
* Current schema matches ORM expectations.
* Constraints reject invalid records.
* Indexes exist.
* Audit update/delete trigger exists when audit migration is added.
* Downgrade or restore procedure is documented.
* Production startup refuses an incompatible revision.

---

# Chapter 2782 — Phase 3 Repository Milestone

The repository layer shall support:

```text
Create and retrieve user
Create and retrieve session
Register public keys
Create direct conversation
Create group conversation
Add memberships
Store encrypted message record
Store recipient envelopes
Create attachment metadata
Append audit event
Create outbox event
```

These operations may initially be tested without complete API routes.

---

# Chapter 2783 — Phase 3 Exit Gate

Phase 3 passes when:

* All migrations apply from empty PostgreSQL.
* Repository tests pass against PostgreSQL.
* Unit of Work commit and rollback are proven.
* Unique and check constraints behave correctly.
* Concurrent audit append tests pass when audit is present.
* No service imports ORM classes directly outside approved mapping boundaries.

---

# Chapter 2784 — Phase 4: Server Lifecycle

Implement:

```text
Typed settings
YAML loader
Environment overrides
Secret-file loading
Startup validation
ServerContainer
DatabaseManager
RedisManager
Storage health
FastAPI lifespan
Graceful shutdown
Liveness
Readiness
Structured logging
Correlation middleware
```

---

# Chapter 2785 — Phase 4 Configuration Profiles

Create tested configurations:

```text
development.yaml
testing.yaml
demonstration.yaml
production.example.yaml
```

Development may use:

* Local PostgreSQL.
* Local Redis.
* Mock authentication.
* Local temporary storage.

Production validation shall reject development defaults.

---

# Chapter 2786 — Phase 4 Startup Sequence

The server shall now perform:

```text
Load configuration

↓

Configure logging

↓

Validate configuration

↓

Start database

↓

Check schema

↓

Start Redis

↓

Verify storage

↓

Start application

↓

Expose readiness
```

Partial startup failure shall clean up previously started components.

---

# Chapter 2787 — Phase 4 Exit Gate

Phase 4 passes when:

* Server starts from a clean development setup.
* Readiness reflects dependency state.
* PostgreSQL failure blocks readiness.
* Redis failure produces the designed degraded state.
* Storage failure disables or blocks attachment capability.
* SIGTERM causes graceful shutdown.
* Secrets do not appear in logs.
* Production-unsafe configuration is rejected.

---

# Chapter 2788 — Phase 5: Authentication Foundation

Implement authentication provider abstraction.

Initial development provider:

```text
MockAuthenticationProvider
```

Then implement:

```text
LocalAuthenticationProvider where required
LDAPAuthenticationProvider
PasswordHasher
TokenManager
AuthenticationService
SessionService
LoginAttemptService
Authentication dependencies
Auth API routes
```

---

# Chapter 2789 — Phase 5 Mock Authentication

The mock provider shall:

* Exist only in development and testing.
* Use synthetic users.
* Support predictable success and failure.
* Support disabled-user simulation.
* Support role mapping.
* Refuse startup in production.

It shall allow client-server integration before Active Directory is available.

---

# Chapter 2790 — Phase 5 LDAP Prototype

Before full integration, prove:

```text
Secure LDAP connection
User search with escaped filter
User bind
Attribute mapping
Disabled-account detection
Group-membership retrieval
Timeout handling
Invalid credential handling
```

Use a test directory or isolated account.

---

# Chapter 2791 — Phase 5 Token Implementation

Implement and test:

```text
Access-token generation
Access-token validation
Refresh-token generation
Refresh-token hashing
Refresh-token rotation
Reuse detection
Session invalidation
Token expiry
Issuer and audience validation
Algorithm restriction
```

No protected feature shall rely only on client-side token claims without checking current server session state where required.

---

# Chapter 2792 — Phase 5 Client Login Prototype

Implement a minimal client login flow:

```text
Enter server address

↓

Negotiate protocol

↓

Enter credentials

↓

Receive token pair

↓

Store refresh token securely

↓

Display authenticated user name

↓

Log out
```

The full main interface is not yet required.

---

# Chapter 2793 — Phase 5 Authentication Tests

Required:

```text
Successful mock login
Successful LDAP login
Invalid password
Unknown username
Disabled directory account
Disabled application account
Expired access token
Successful refresh rotation
Refresh-token reuse
Logout
All-session revocation
Production mock-provider rejection
```

---

# Chapter 2794 — Phase 5 Exit Gate

Phase 5 passes when:

* A client can log in and log out.
* Sessions persist in PostgreSQL.
* Tokens are stored safely.
* Refresh rotation works.
* Revocation disconnect hooks exist.
* Login audit events are created.
* Active Directory errors are translated safely.
* No password appears in logs or local storage.

---

# Chapter 2795 — Phase 6: Users and Public Keys

Implement:

```text
Current-user profile
User search
Contact relationships
Block relationships
Public-key registration
Public-key retrieval
Key versioning
Key revocation
Key-change events
Client key store
Client identity-key generation
```

---

# Chapter 2796 — Phase 6 Private-Key Storage Prototype

Before messaging, prove that the client can:

```text
Generate X25519 key pair
Generate Ed25519 key pair
Encrypt private keys locally
Close application
Reopen profile
Unlock private-key store
Retrieve matching keys
Verify fingerprints
```

Raw private keys shall not appear in the local database or logs.

---

# Chapter 2797 — Phase 6 Public-Key Registration Flow

```text
Client creates keys

↓

Client calculates fingerprints

↓

Client authenticates

↓

Client registers public keys

↓

Server verifies lengths and fingerprints

↓

Server stores versions

↓

Client retrieves keys and compares
```

---

# Chapter 2798 — Phase 6 Exit Gate

Phase 6 passes when:

* User search works.
* Contacts can be added and removed.
* Blocks are enforced by relevant services.
* Public keys can be registered and retrieved.
* Private keys survive restart securely.
* Revoked keys are excluded from new encryption.
* Key-change cache invalidation works.
* Key tests contain no private material in server records.

---

# Chapter 2799 — Phase 7: Conversations

Implement:

```text
Direct conversation creation
Unique direct pairs
Group creation
Group memberships
Group roles
Add member
Remove member
Leave group
Ownership transfer
Conversation listing
Conversation preferences
Membership events
```

Message sending may still use synthetic encrypted payload fixtures.

---

# Chapter 2800 — Phase 7 Direct Conversation Milestone

Prove:

```text
User A selects User B

↓

Server returns existing or creates direct conversation

↓

Both memberships exist

↓

Both clients list the same conversation

↓

Duplicate creation returns one conversation
```

Concurrent creation shall also produce one result.

---

# Chapter 2801 — Phase 7 Group Milestone

Prove:

```text
Owner creates group

↓

Members are added

↓

Owner and member roles display

↓

Moderator is promoted

↓

Member is removed

↓

Ownership transfers atomically

↓

Old owner becomes moderator

↓

No group exists without one owner
```

---

# Chapter 2802 — Phase 7 Exit Gate

Phase 7 passes when:

* Direct and group conversations work.
* Membership permissions are centralised.
* Membership history is stored.
* Removed members lose future access.
* Group ownership cannot enter an invalid state.
* Conversation pages can display metadata using synthetic message content.

---

# Chapter 2803 — Phase 8: Cryptography Prototype

This phase shall be completed before production message integration.

Implement isolated client cryptography:

```text
Message content encryption
Message AAD
Recipient key envelopes
Message signatures
Message verification
Message decryption
Attachment subkey derivation
Chunk encryption
Manifest signing
Local encryption
```

---

# Chapter 2804 — Phase 8 Cryptographic Test Harness

Create a standalone test harness that:

```text
Creates two synthetic users

Generates keys

Encrypts a message

Serialises the request

Deserialises it

Verifies the signature

Unwraps the recipient key

Decrypts the message

Compares plaintext
```

The server shall not be required for the first test.

---

# Chapter 2805 — Phase 8 Message Test Vectors

Freeze deterministic test vectors for:

* Canonical AAD.
* Recipient envelope derivation.
* Ciphertext and tag.
* Signature bytes.
* Public-key fingerprint.
* Edited-message version.

The random provider shall be deterministic only in tests.

---

# Chapter 2806 — Phase 8 Negative Tests

Required mutations:

```text
Ciphertext changed
Tag changed
Nonce changed
Message ID changed
Conversation ID changed
Recipient changed
Wrapped key changed
Signing key version changed
Signature changed
Attachment ID list changed
```

Every relevant mutation shall fail verification or decryption.

---

# Chapter 2807 — Phase 8 Exit Gate

Phase 8 passes when:

* Two clients can exchange test vectors.
* Wrong recipients cannot decrypt.
* Signature verification is mandatory.
* Authentication failures produce no plaintext.
* Edited messages use new keys and nonces.
* Cryptographic code contains no custom primitive implementation.
* Performance is acceptable for target group sizes.

---

# Chapter 2808 — Phase 9: Encrypted Messaging

Integrate:

```text
MessagingService
MessageRepository
Recipient-key storage
Message API
ClientMessagingService
Local pending messages
Message cache
Message pagination
Delivery states
Read positions
Edit
Delete
Reply
Audit and outbox events
```

---

# Chapter 2809 — Phase 9 First End-to-End Message

Required scenario:

```text
User A logs in

↓

User B logs in

↓

Direct conversation exists

↓

User A encrypts message

↓

Server validates envelope

↓

Server stores ciphertext and envelopes

↓

User B fetches message

↓

User B verifies and decrypts

↓

Both clients show correct state
```

---

# Chapter 2810 — Phase 9 Plaintext Absence Gate

Use a known marker such as:

```text
NEA-PLAINTEXT-CHECK-7F3A
```

After sending, search:

```text
PostgreSQL
Server attachment and temporary paths
Server logs
Audit details
Outbox events
Server diagnostic output
```

The marker shall not appear.

---

# Chapter 2811 — Phase 9 Messaging Features

Implement incrementally:

```text
Send
Retrieve
Pagination
Delivery acknowledgement
Read acknowledgement
Reply
Edit
Delete
Idempotent retry
Conflict response
```

Each feature shall add tests before the next depends on it.

---

# Chapter 2812 — Phase 9 Exit Gate

Phase 9 passes when:

* Direct encrypted messaging works.
* Group encrypted messaging works.
* Recipient coverage is enforced.
* Removed members receive no future keys.
* Pagination has no duplicates or omissions.
* Edits and deletes synchronise correctly.
* Server plaintext absence tests pass.
* Pending and failed client states are accurate.

---

# Chapter 2813 — Phase 10: WebSocket Realtime Layer

Implement:

```text
WebSocket endpoint
Connection authentication
Connection manager
Heartbeat
Event dispatcher
Event publisher
Message-received events
Message-updated events
Message-deleted events
Delivery events
Read events
Typing
Presence
Session-revoked events
```

Durable storage shall remain REST and PostgreSQL based.

---

# Chapter 2814 — Phase 10 Connection Milestone

Prove:

```text
Client connects over WSS

↓

Authenticates connection

↓

Sends heartbeats

↓

Server tracks last heartbeat

↓

Server publishes test event

↓

Client handles event

↓

Session revocation closes connection
```

---

# Chapter 2815 — Phase 10 Realtime Message Milestone

After User A sends through REST:

```text
Transaction commits

↓

Outbox event is published

↓

User B receives WebSocket event

↓

User B fetches or processes encrypted message

↓

Duplicate event is ignored
```

The event shall never be published before commit.

---

# Chapter 2816 — Phase 10 Exit Gate

Phase 10 passes when:

* Multiple connections per session are handled as designed.
* Heartbeat timeout removes stale connections.
* Concurrent sends do not overlap frames unsafely.
* Session revocation disconnects clients.
* Redis outage produces the intended degraded behaviour.
* Durable events remain recoverable after missed WebSocket delivery.

---

# Chapter 2817 — Phase 11: Attachment Foundation

Implement client-side:

```text
File selection validation
Chunked reading
Attachment master-key generation
Subkey derivation
Chunk encryption
Encrypted metadata
Recipient file-key envelopes
Signed manifest
Prepared-upload storage
```

Implement server-side:

```text
Upload initialisation
Temporary storage
Chunk upload
Chunk checksum validation
Resume state
Finalisation
Attachment metadata
Authorised download
Cleanup
```

---

# Chapter 2818 — Phase 11 Small Attachment Milestone

First prove with a small synthetic file:

```text
Sender encrypts file

↓

Uploads chunks

↓

Server stores ciphertext

↓

Recipient downloads chunks

↓

Recipient verifies manifest

↓

Recipient decrypts file

↓

Plaintext SHA-256 matches
```

---

# Chapter 2819 — Phase 11 Large Attachment Milestone

Test a file large enough to prove streaming.

Requirements:

```text
Memory remains bounded
No whole-file read
Progress updates
Cancellation works
Resume works
Final hash matches
Temporary files clean up
```

---

# Chapter 2820 — Phase 11 Failure Testing

Simulate:

```text
Lost network after several chunks
Duplicate chunk
Conflicting chunk
Missing chunk
Modified encrypted chunk
Full server disk
Expired upload session
Client crash
Server restart
Wrong recipient key
```

---

# Chapter 2821 — Phase 11 Exit Gate

Phase 11 passes when:

* Upload and download are streamed.
* Resume avoids re-uploading valid chunks.
* Modified chunks fail.
* Final plaintext checksum is verified.
* Server stores no plaintext file marker.
* Attachment access follows conversation membership.
* Cleanup does not remove active uploads.
* Large-file operations do not freeze the client.

---

# Chapter 2822 — Phase 12: Local Persistence

Implement:

```text
Local profile database
Local migrations
Secure-store integration
Encrypted message cache
Draft repository
Offline action repository
Transfer-state repository
Search index
Cache manager
Profile isolation
Single-instance lock
```

---

# Chapter 2823 — Phase 12 Local Migration Strategy

Create local schema migrations for:

```text
Profile metadata
Cached users
Cached conversations
Cached encrypted messages
Drafts
Offline actions
Transfers
Search tokens
Synchronisation state
Tombstones
```

Migration tests shall preserve unsent work.

---

# Chapter 2824 — Phase 12 Draft Milestone

Prove:

```text
Write draft

↓

Close application

↓

Reopen application

↓

Unlock same profile

↓

Restore draft exactly

↓

Verify SQLite contains no plaintext marker
```

---

# Chapter 2825 — Phase 12 Offline Queue Milestone

Prove:

```text
Disconnect server

↓

Create message

↓

Queue locally

↓

Restart client

↓

Reconnect server

↓

Replay same message ID

↓

Server stores one message

↓

Local action becomes complete
```

---

# Chapter 2826 — Phase 12 Exit Gate

Phase 12 passes when:

* Profiles are isolated.
* Drafts survive restart.
* Queue records survive restart.
* Sensitive local fields are encrypted.
* Corrupted records fail safely.
* Local migrations preserve data.
* Cache limits do not remove unsent work.
* Search index contains no plaintext tokens.

---

# Chapter 2827 — Phase 13: Desktop Interface

Implement interface in dependency order:

```text
Login window
Main window shell
Navigation sidebar
Conversation list
Chat page
Message widgets
Composer
Contacts
Groups
Transfers
Search
Announcements
Settings
Diagnostics
Administration shell
Themes
Accessibility improvements
```

---

# Chapter 2828 — Phase 13 Interface Skeleton

First create pages using ViewModels and synthetic data.

Purpose:

* Validate layout.
* Validate navigation.
* Validate resizing.
* Validate themes.
* Validate keyboard focus.

Do not embed temporary direct API calls inside views.

---

# Chapter 2829 — Phase 13 ViewModel Integration

Replace synthetic state with real services one page at a time.

Recommended order:

```text
Login
Main connectivity state
Conversation list
Chat history
Message send
Transfers
Contacts
Groups
Search
Settings
Diagnostics
Administration
```

---

# Chapter 2830 — Phase 13 Accessibility Gate

Before interface completion, test:

```text
Keyboard-only login
Keyboard-only conversation selection
Keyboard-only message send
Visible focus
Accessible icon names
High-contrast theme
150% font scale
Screen-reader message labels
Dialog focus restoration
```

Accessibility shall not be left as an optional final polish task.

---

# Chapter 2831 — Phase 13 Exit Gate

Phase 13 passes when:

* All Version 1.0 pages exist.
* No required control is non-functional.
* Views contain no business logic.
* Long operations do not block the GUI.
* Loading, empty and error states exist.
* Pending and failed messages are distinguishable.
* Themes work.
* Keyboard access works.
* Destructive actions require confirmation.

---

# Chapter 2832 — Phase 14: Administration and Audit

Implement:

```text
Role permissions
Administrative capabilities
User administration
Session administration
Connection administration
Audit writer
Audit query
Audit integrity verification
Security alerts
Dashboard
Worker controls
Configuration history
Announcements
Exports
Maintenance mode
```

---

# Chapter 2833 — Phase 14 Audit-First Order

Implement in this order:

```text
Audit schema and append protection

↓

AuditWriter

↓

AuditService

↓

Administrative actions

↓

Audit query

↓

Integrity verification

↓

Audit export
```

Administrative mutations shall not be implemented first and audited later.

---

# Chapter 2834 — Phase 14 First Administrative Action

Recommended first action:

```text
Administrator disables test employee.
```

Verify:

* Permission.
* Reason.
* User state.
* Session invalidation.
* WebSocket disconnection.
* Audit event.
* Outbox event.
* Client response.

---

# Chapter 2835 — Phase 14 Audit Tamper Test

In a privileged test environment:

```text
Insert several audit events

↓

Verify chain

↓

Modify one row using privileged test connection

↓

Run verification

↓

Observe critical failure

↓

Create alert
```

The normal application database role shall remain unable to perform the modification.

---

# Chapter 2836 — Phase 14 Exit Gate

Phase 14 passes when:

* Administrative boundaries are enforced.
* Final SuperAdministrator protection works.
* Every administrative write is audited.
* Audit update and deletion are blocked.
* Audit verification detects tampering.
* Dashboard health is accurate.
* Alerts can be acknowledged and resolved.
* Administrative responses expose no plaintext content.

---

# Chapter 2837 — Phase 15: Synchronisation

Implement:

```text
Durable event cursor
Event replay
Scope checkpoints
Aggregate-version handling
Targeted resynchronisation
Full resynchronisation
Queue replay
Conflict records
Membership conflict handling
Key conflict handling
Attachment recovery
Tombstones
```

---

# Chapter 2838 — Phase 15 Incremental Sync Milestone

Scenario:

```text
Client disconnects

↓

Server stores several durable changes

↓

Client reconnects with last event ID

↓

Server returns missed events

↓

Client applies them once

↓

Cursor advances after local commit
```

---

# Chapter 2839 — Phase 15 Full Resync Milestone

Scenario:

```text
Client cursor expires

↓

Server rejects incremental replay

↓

Client refreshes required scopes

↓

Local drafts and queue remain

↓

Server-derived cache is rebuilt

↓

Valid queue actions resume
```

---

# Chapter 2840 — Phase 15 Conflict Milestone

Test at least:

```text
User removed while message queued
Recipient key changed
Edit version conflict
Attachment policy changed
Conversation deleted
```

Every test shall preserve user work where possible and avoid unsafe submission.

---

# Chapter 2841 — Phase 15 Exit Gate

Phase 15 passes when:

* Reconnection recovers missed durable events.
* Event duplicates do not duplicate records.
* Version gaps cause resynchronisation.
* Membership changes block stale sends.
* Key changes rebuild envelopes safely.
* Crashes after server success do not duplicate messages.
* Conflicts survive restart.
* Queue state remains understandable to users.

---

# Chapter 2842 — Phase 16: Deployment

Implement and test:

```text
Debian installation
Service account
Directory permissions
PostgreSQL deployment
Redis deployment
Attachment mount
Nginx configuration
TLS
systemd unit
Firewall rules
Release directories
Upgrade script
Rollback script
Backup scripts
Windows packaging
Windows installer
```

---

# Chapter 2843 — Phase 16 Clean Server Installation

Use a new Debian VM.

The deployment shall start from:

```text
Fresh operating-system installation
```

The installation guide shall not rely on undeclared developer-machine state.

Record:

* Commands.
* Configuration.
* Errors.
* Corrections.
* Final verification.

---

# Chapter 2844 — Phase 16 Windows Packaging

Use a clean Windows build environment.

Verify:

```text
Client runs without Python installed
Qt resources load
Themes load
Secure store works
TLS trust works
Local database works
Installer upgrades preserve profile
Uninstaller behaves correctly
```

---

# Chapter 2845 — Phase 16 Upgrade Rehearsal

Create:

```text
Version A deployment

↓

Create data

↓

Upgrade to Version B test build

↓

Run migration

↓

Verify data

↓

Run smoke tests

↓

Perform rollback rehearsal
```

Rollback must be proven rather than assumed.

---

# Chapter 2846 — Phase 16 Exit Gate

Phase 16 passes when:

* A clean Debian VM can be installed using documentation.
* Service starts automatically.
* Only intended ports are exposed.
* TLS validates on client.
* Windows installer works.
* Upgrade preserves data.
* Rollback procedure works.
* Database and attachment backups can be restored.

---

# Chapter 2847 — Phase 17: Comprehensive Testing

Run the complete test programme:

```text
Unit tests
Repository tests
API integration tests
WebSocket tests
Cryptographic tests
Attachment tests
Offline recovery tests
Administration tests
Deployment tests
Security tests
Performance tests
Accessibility tests
Usability tests
```

---

# Chapter 2848 — Phase 17 Test Environments

Recommended test systems:

```text
Development machine

Fast local iteration.

Debian server VM

Production-like server behaviour.

Windows 10 client VM

Compatibility.

Windows 11 client machine or VM

Primary target.

Network impairment environment

Latency, loss and disconnection.

Restore environment

Backup validation.
```

---

# Chapter 2849 — Phase 17 Defect Severity

Defects shall be classified:

```text
Critical

Content exposure, authentication bypass, data corruption, key loss or unusable release.

High

Major feature failure, incorrect permission, unreliable recovery or significant integrity defect.

Medium

Limited feature defect with workaround.

Low

Minor presentation or documentation issue.
```

No known critical or high defect shall remain at Version 1.0 release.

---

# Chapter 2850 — Phase 17 Regression Rule

Every fixed defect shall receive:

```text
A reproducible test
```

where practical.

The test shall fail before the correction and pass after it.

This prevents the same issue returning during later changes.

---

# Chapter 2851 — Phase 17 Security Gate

Required results:

* No authentication bypass.
* No permission bypass.
* No plaintext marker on server.
* No private key transmitted.
* No secret in diagnostic output.
* TLS validation cannot be bypassed in production.
* Audit tampering is detected.
* Path traversal is rejected.
* Oversized requests are rejected.
* Token reuse is detected.
* Removed group members receive no future key envelopes.

---

# Chapter 2852 — Phase 17 Performance Gate

The project shall define measured targets for:

```text
Login response
Conversation-list load
Message send
Message retrieval
Message encryption
Message decryption
Attachment throughput
Search response
Dashboard response
Initial sync
Reconnect sync
```

Targets shall be based on the actual evaluation environment.

---

# Chapter 2853 — Phase 17 Usability Gate

Representative users shall complete core tasks.

Required success tasks:

```text
Log in
Find contact
Send direct message
Create group
Send attachment
Find old cached message
Resolve failed message
Change notification setting
Run diagnostics
Log out
```

Major recurring confusion shall be corrected before release.

---

# Chapter 2854 — Phase 18: Documentation

Complete:

```text
User guide
Administrator guide
Installation guide
Upgrade guide
Rollback guide
Backup guide
Restore guide
Developer guide
Architecture guide
Cryptography guide
Database guide
API guide
Testing report
Known limitations
```

Documentation shall match the final implementation.

---

# Chapter 2855 — Phase 18 NEA Evidence

The NEA evidence set should include:

```text
Problem definition
Stakeholder requirements
Success criteria
Research
Design alternatives
Chosen architecture
Algorithms
Data structures
Database design
Interface design
Development evidence
Testing evidence
Evaluation
Future improvements
```

Screenshots shall use synthetic data.

---

# Chapter 2856 — Phase 18 Development Evidence

Useful evidence:

```text
Early server health endpoint
Initial database migration
Authentication prototype
First encrypted message
First group conversation
First attachment transfer
Offline queue recovery
Audit tamper detection
Interface iterations
Deployment verification
```

Each item should explain:

* What was implemented.
* Why.
* What problem occurred.
* How it was tested.
* What changed afterwards.

---

# Chapter 2857 — Phase 18 Test Evidence

For selected tests, record:

```text
Test ID
Requirement ID
Purpose
Input
Expected result
Actual result
Pass or fail
Evidence
Correction where failed
Retest result
```

The report shall include both successful and failed development tests.

---

# Chapter 2858 — Phase 18 Evaluation Evidence

Evaluation shall compare the final system against:

* Functional requirements.
* Non-functional requirements.
* Stakeholder expectations.
* Performance targets.
* Security requirements.
* Usability findings.
* Scope limitations.

Claims shall be supported by test results.

---

# Chapter 2859 — Phase 18 Exit Gate

Phase 18 passes when:

* Every implemented feature is documented.
* Every acceptance criterion has evidence.
* Known limitations are stated.
* Diagrams match the final architecture.
* Screenshots contain no sensitive real data.
* Installation instructions have been followed successfully by another person or clean environment.
* The evaluation identifies realistic improvements.

---

# Chapter 2860 — Phase 19: Release Candidate

Create a release candidate only after all previous gates pass.

Release candidate contents:

```text
Server release package
Windows installer
Database migrations
Configuration examples
Deployment files
Checksums
Release notes
User guide
Administrator guide
Known limitations
Test summary
```

---

# Chapter 2861 — Release Candidate Freeze

During the release-candidate period:

```text
No new features.

Only defect corrections.

Every correction receives tests.

Protocol changes require exceptional justification.

Database changes require migration rehearsal.

Interface changes require regression review.
```

This phase focuses on stability.

---

# Chapter 2862 — Release Candidate Smoke Test

Perform on clean infrastructure:

```text
Install server

↓

Install client

↓

Authenticate two users

↓

Create direct conversation

↓

Create group

↓

Send and receive messages

↓

Edit and delete message

↓

Transfer file

↓

Disconnect and recover

↓

Perform admin action

↓

Verify audit chain

↓

Restart server and client

↓

Verify persistence
```

---

# Chapter 2863 — Release Candidate Backup Test

Before release:

```text
Create database and attachment backup

↓

Destroy or isolate test deployment

↓

Restore into clean environment

↓

Start application

↓

Verify users, messages and attachments

↓

Verify audit chain

↓

Run smoke test
```

A successful backup command without a restore is insufficient.

---

# Chapter 2864 — Version 1.0 Completion Criteria

Version 1.0 is complete only when:

```text
All mandatory requirements are implemented.

All critical tests pass.

No known critical or high defects remain.

Server plaintext absence tests pass.

Cryptographic test vectors pass.

Database migrations apply from empty state.

Upgrade and rollback are tested.

Backup and restore are tested.

Windows client installs successfully.

Debian service starts automatically.

Accessibility acceptance checks pass.

Core usability tasks succeed.

Documentation is complete.

Known limitations are published.
```

---

# Chapter 2865 — Mandatory Functional Completion

The release shall include working:

```text
Authentication
Sessions
User profiles
Contacts
Direct conversations
Groups
Encrypted messaging
Replies
Edits
Deletions
Delivery states
Read states
Encrypted attachments
Resumable transfers
Local cache
Drafts
Offline queue
Local search
Announcements
Administration
Audit
Monitoring
Deployment
```

A placeholder screen does not count as completion.

---

# Chapter 2866 — Mandatory Security Completion

The release shall demonstrate:

```text
TLS in production deployment
No plaintext server message storage
No plaintext server attachment storage
Encrypted private-key storage
Versioned public keys
Message signatures
Authenticated encryption
Recipient-specific key envelopes
Refresh-token rotation
Session revocation
Role enforcement
Audit integrity
Secret redaction
Path containment
Production configuration validation
```

---

# Chapter 2867 — Mandatory Reliability Completion

The release shall survive:

```text
Client restart
Server restart
Temporary network loss
Redis restart
Expired access token
Interrupted upload
Interrupted download
Duplicate message submission
Expired event cursor
Recoverable queue conflict
Failed worker iteration
```

Permanent dependency failure may reduce capability but shall fail clearly.

---

# Chapter 2868 — Mandatory Documentation Completion

Required final documentation:

```text
README
Installation
Configuration
User guide
Administrator guide
Security design
Cryptography
Database schema
API reference
Testing report
Evaluation
Known limitations
Recovery guide
```

---

# Chapter 2869 — Scope-Control Rule

During development, a proposed new feature shall be evaluated by asking:

```text
Is it required by a Version 1.0 requirement?

Does another required feature depend upon it?

Can it be implemented and tested without delaying critical work?

Does it introduce new security or recovery complexity?

Can it be deferred honestly?
```

If not essential, it shall be added to the future-improvements list.

---

# Chapter 2870 — Features to Reject During Version 1.0

The roadmap shall reject unplanned implementation of:

```text
Voice calling
Video calling
Screen sharing
Remote desktop
Bots
Plugins
Public federation
Cloud deployment
Mobile clients
Message reactions if not already approved
GIF services
Public link previews
Automatic external update service
Multiple independent cryptographic devices
Double-ratchet encryption
```

These features would add substantial complexity and risk.

---

# Chapter 2871 — Risk Register Purpose

The project shall maintain a risk register throughout development.

Each risk shall include:

```text
Risk ID
Description
Likelihood
Impact
Mitigation
Trigger
Owner
Current state
Review date
```

Risks shall be reviewed at each major milestone.

---

# Chapter 2872 — Critical Technical Risks

Likely critical risks:

```text
Incorrect cryptographic envelope design
Private-key loss
Active Directory integration failure
Qt and asyncio integration defects
Database migration corruption
Attachment resume inconsistency
Offline duplicate submission
Audit-chain concurrency defect
Packaging dependency failure
Insufficient development time
```

---

# Chapter 2873 — Cryptography Risk Mitigation

Mitigation:

* Use approved library.
* Implement deterministic test vectors.
* Separate signing and encryption keys.
* Review nonce use.
* Test wrong-key and tamper failures.
* Keep scope to one primary device.
* Avoid ratchet protocols in Version 1.0.
* Document key-loss limitation.
* Perform dedicated code review before integration.

---

# Chapter 2874 — Active Directory Risk Mitigation

Mitigation:

* Use provider abstraction.
* Build mock provider first.
* Test with isolated directory.
* Keep optional local emergency authentication.
* Apply timeouts and circuit breaker.
* Treat directory outage as a defined capability failure.
* Document required attributes and groups.

---

# Chapter 2875 — Interface Risk Mitigation

Mitigation:

* Build ViewModels before final styling.
* Prototype navigation early.
* Test Qt event-loop integration.
* Keep long work off GUI thread.
* Test accessibility continuously.
* Avoid custom complex widgets unless required.
* Use synthetic data during layout work.

---

# Chapter 2876 — Attachment Risk Mitigation

Mitigation:

* Use bounded chunks.
* Encrypt independently.
* Persist manifests.
* Verify hashes.
* Separate temporary and permanent paths.
* Test full disk.
* Test restart.
* Test expired sessions.
* Avoid whole-file memory loading.

---

# Chapter 2877 — Offline Risk Mitigation

Mitigation:

* Stable message UUIDs.
* Server idempotency.
* Serial Version 1.0 queue.
* Transactional local state.
* Refresh security state before replay.
* Persist conflicts.
* Preserve drafts separately.
* Test crash after server commit.

---

# Chapter 2878 — Schedule Risk Mitigation

If development time becomes limited, prioritise:

```text
1. Authentication

2. Direct encrypted messaging

3. Group encrypted messaging

4. Reliable persistence

5. Essential interface

6. Attachments

7. Offline queue

8. Audit and administration

9. Secondary visual enhancements
```

Required correctness shall take priority over decorative complexity.

---

# Chapter 2879 — Minimum Demonstrable Product

The minimum demonstrable product is not the final release.

It shall include:

```text
Two authenticated users
One direct conversation
Client-side encrypted message
Server ciphertext storage
Recipient decryption
Basic message interface
Database persistence
TLS or isolated development equivalent
```

This milestone proves the central concept early.

---

# Chapter 2880 — Expanded Demonstrable Product

The next demonstration shall add:

```text
Groups
Key versioning
Message signatures
Attachments
WebSocket notification
Session revocation
Audit event
```

This proves the most important system interactions.

---

# Chapter 2881 — Final Demonstration Scenario

Recommended final presentation:

```text
1. Administrator starts server and checks health.

2. Two users log in.

3. User A creates a direct conversation with User B.

4. User A sends an encrypted message.

5. Database inspection shows ciphertext only.

6. User B receives and decrypts the message.

7. User A creates a group and adds User B.

8. User A sends an encrypted attachment.

9. User B downloads and verifies it.

10. Network connection is interrupted.

11. User A creates a queued message.

12. Connection returns and the message is sent once.

13. Administrator revokes User B’s session.

14. User B is disconnected.

15. Audit records show the administrative action.

16. Audit integrity verification passes.
```

---

# Chapter 2882 — Demonstration Data

Use synthetic:

```text
Names
Departments
Messages
Files
Accounts
Audit reasons
Announcements
```

Do not use:

* Real employee credentials.
* Real private documents.
* Real organisational messages.
* Real production directory data.

---

# Chapter 2883 — Milestone Tracking Table

Each milestone should record:

```text
Milestone
Planned date
Actual date
Required features
Required tests
Status
Known issues
Evidence reference
```

Suggested statuses:

```text
Not started
In progress
Blocked
Testing
Complete
```

---

# Chapter 2884 — Definition of Done for a Feature

A feature is complete when:

```text
Requirement is identified.

Design is documented.

Implementation exists.

Validation exists.

Permission checks exist.

Error handling exists.

Logging is safe.

Tests pass.

Interface state exists where applicable.

Documentation is updated.

No placeholder remains.
```

Code that merely works once manually is not complete.

---

# Chapter 2885 — Definition of Done for a Database Change

A database change is complete when:

* ORM model updated.
* Migration created.
* Migration applies from previous revision.
* Empty install reaches head.
* Constraints tested.
* Indexes reviewed.
* Repository updated.
* Rollback or restore impact documented.
* Test fixtures updated.
* Schema documentation updated.

---

# Chapter 2886 — Definition of Done for an API Endpoint

An endpoint is complete when:

* Route documented.
* Request model validated.
* Response model defined.
* Authentication applied.
* Permission applied.
* Service method used.
* Errors mapped.
* Rate limit applied where required.
* Integration tests pass.
* OpenAPI output is correct.
* Sensitive values are excluded.

---

# Chapter 2887 — Definition of Done for a Client Page

A client page is complete when:

* ViewModel exists.
* Loading state exists.
* Empty state exists.
* Error state exists.
* Keyboard navigation works.
* Accessibility names exist.
* Long work is asynchronous.
* Theme support works.
* Disposal works.
* Automated or manual tests exist.
* No direct database or network access occurs in the view.

---

# Chapter 2888 — Definition of Done for Cryptographic Code

Cryptographic code is complete when:

* Approved algorithm is used.
* Key purpose is explicit.
* Nonce rules are correct.
* AAD is defined.
* Canonicalisation is tested.
* Positive test vector passes.
* Tamper tests fail safely.
* Wrong-key test fails safely.
* No plaintext logging exists.
* No private-key transmission exists.
* Performance is measured.
* Limitations are documented.

---

# Chapter 2889 — Definition of Done for a Worker

A worker is complete when:

* Name is unique.
* Schedule is configurable.
* One-run behaviour is tested.
* Cancellation works.
* Duplicate execution is prevented.
* Failure is classified.
* Retry is bounded.
* Health state is reported.
* Execution result is stored.
* Manual-run policy is defined.
* Shutdown is clean.

---

# Chapter 2890 — Documentation Update Cadence

Documentation shall be updated:

```text
When a public interface changes
When a migration is added
When configuration changes
When a security assumption changes
When a test reveals a limitation
When a deployment step changes
At every milestone gate
```

Documentation shall not be reconstructed entirely from memory at the end.

---

# Chapter 2891 — Architecture Decision Records

Important decisions should use Architecture Decision Records.

Suggested ADRs:

```text
ADR-001 Use FastAPI modular monolith

ADR-002 Use PostgreSQL as authoritative store

ADR-003 Use Redis for transient state

ADR-004 Use PySide6 desktop client

ADR-005 Use X25519 and Ed25519 identity keys

ADR-006 Use AES-256-GCM content encryption

ADR-007 Use one primary cryptographic device

ADR-008 Use REST for durable writes and WebSocket for events

ADR-009 Use filesystem attachment storage

ADR-010 Use local encrypted offline queue
```

---

# Chapter 2892 — ADR Structure

Each ADR shall include:

```text
Title
Status
Context
Decision
Alternatives
Consequences
Security impact
Date
```

Accepted decisions shall not be changed silently.

A replacement ADR may supersede an earlier one.

---

# Chapter 2893 — Dependency Upgrade Strategy

Dependencies shall be upgraded deliberately.

Before upgrading a major dependency:

* Read release notes.
* Check Python compatibility.
* Run complete tests.
* Rebuild Windows package.
* Recheck migrations where relevant.
* Recheck cryptographic behaviour.
* Recheck Qt interface.
* Update lock file.
* Record change.

Dependency upgrades shall not be combined casually with unrelated feature work.

---

# Chapter 2894 — Security Patch Strategy

A security patch may override ordinary feature scheduling.

Process:

```text
Assess affected component

↓

Create isolated fix

↓

Add regression test

↓

Run focused and full security tests

↓

Build release

↓

Document impact

↓

Deploy using controlled update procedure
```

Sensitive vulnerability details shall not be placed in public demonstration data.

---

# Chapter 2895 — Prototype Disposal Rule

Temporary prototypes shall not automatically become production code.

Before retaining prototype code, review:

* Architecture.
* Error handling.
* Type safety.
* Security.
* Tests.
* Logging.
* Configuration.
* Resource cleanup.

A successful proof of concept may still need a clean implementation.

---

# Chapter 2896 — No Parallel Incomplete Foundations

The coding AI shall not leave many foundational subsystems half implemented simultaneously.

Preferred:

```text
Complete and test configuration

then

Complete and test database foundation

then

Complete and test authentication
```

Avoid:

```text
Partially build authentication
Partially build messaging
Partially build interface
Partially build attachments
without one working vertical path
```

---

# Chapter 2897 — First Vertical Slice

The first complete vertical slice shall be:

```text
Client login form

↓

Authentication API

↓

Authentication provider

↓

User repository

↓

PostgreSQL

↓

Session creation

↓

Token return

↓

Authenticated client state

↓

Logout
```

This proves client, server, database and network integration.

---

# Chapter 2898 — Second Vertical Slice

The second complete vertical slice shall be:

```text
Client composer

↓

Message encryption

↓

Send API

↓

MessagingService

↓

Message repository

↓

PostgreSQL ciphertext

↓

Recipient retrieval

↓

Client decryption

↓

Message widget
```

This proves the central application purpose.

---

# Chapter 2899 — Third Vertical Slice

The third vertical slice shall be:

```text
Client file picker

↓

Chunk encryption

↓

Upload API

↓

File storage

↓

Attachment metadata

↓

Recipient download

↓

Verification and decryption

↓

Open completed file
```

---

# Chapter 2900 — Fourth Vertical Slice

The fourth vertical slice shall be:

```text
Admin user page

↓

Disable action

↓

Permission service

↓

User update

↓

Session invalidation

↓

Audit append

↓

Outbox event

↓

WebSocket disconnect

↓

Client logout state
```

---

# Chapter 2901 — Feature Flag Use During Development

Feature flags may protect incomplete integrated features.

Examples:

```text
attachments_enabled
offline_queue_enabled
administration_enabled
announcements_enabled
```

Rules:

* Disabled features shall not appear functional.
* Flags shall not weaken permission checks.
* Security-critical checks shall not be bypassable.
* Completed Version 1.0 features shall be enabled in the release configuration.
* Old temporary flags shall be removed after stabilisation.

---

# Chapter 2902 — Test Coverage Guidance

Coverage shall identify untested areas but shall not become the only quality measure.

Priority coverage:

```text
Domain rules
Permissions
Cryptography
Token handling
Transactions
Conflict handling
Path validation
Audit chain
Queue replay
Migration logic
```

Simple presentation getters may receive lower priority.

---

# Chapter 2903 — Suggested Coverage Targets

Suggested project targets:

```text
Overall line coverage:

At least 80%

Security-critical modules:

At least 90%

Domain and service modules:

At least 90%
```

These are targets, not proof of correctness.

Mutation and behavioural tests remain important.

---

# Chapter 2904 — Manual Review Checkpoints

Manual code review shall occur after:

```text
Cryptography prototype
Authentication completion
Messaging completion
Attachment completion
Administration completion
Deployment completion
Release candidate
```

The review shall use subsystem-specific checklists.

---

# Chapter 2905 — Stakeholder Review Checkpoints

Stakeholder feedback should be gathered after:

```text
Requirements confirmation
Interface prototype
Basic messaging milestone
Attachment milestone
Administration prototype
Release candidate
```

Feedback shall be recorded and prioritised.

Not every request must enter Version 1.0.

---

# Chapter 2906 — Change Request Evaluation

Each significant change request shall record:

```text
Requested change
Reason
Affected requirements
Affected modules
Security impact
Schedule impact
Testing impact
Decision
```

This supports controlled scope and NEA evaluation evidence.

---

# Chapter 2907 — Roadmap Failure Response

If a milestone fails its gate:

```text
Do not declare it complete.

Record the failure.

Identify root cause.

Correct design or implementation.

Add or update tests.

Repeat the gate.
```

The next dependent milestone shall not proceed using known broken foundations.

---

# Chapter 2908 — Partial Progress Handling

If development time becomes constrained:

* Preserve working secure features.
* Remove incomplete controls.
* Disable unfinished routes.
* Document deferred requirements.
* Avoid shipping placeholder implementations.
* Keep data migrations valid.
* Keep tests passing.

A smaller correct release is preferable to a larger unreliable one.

---

# Chapter 2909 — Final Code Freeze Checklist

Before final code freeze:

```text
All requirements reviewed
All tests run
All migrations reviewed
All TODO markers reviewed
All feature flags reviewed
All debug endpoints reviewed
All mock providers disabled in production
All secrets removed from repository
All logs reviewed for plaintext
All dependencies locked
All documentation updated
All known issues classified
```

---

# Chapter 2910 — Final Repository Scan

Search for patterns such as:

```text
TODO
FIXME
pass
NotImplementedError
localhost production defaults
test passwords
private key headers
database passwords
print(
except Exception:
```

Every match shall be reviewed.

Some may be legitimate in tests or abstract classes, but none shall be ignored.

---

# Chapter 2911 — Final Database Review

Verify:

* Head migration matches release.
* No development-only tables remain.
* Seed data is appropriate.
* Constraints are enabled.
* Audit trigger is enabled.
* Application role permissions are restricted.
* Backup succeeds.
* Restore succeeds.
* Production database URL is secret-managed.
* Migration instructions are included.

---

# Chapter 2912 — Final Client Review

Verify:

* Installer contains no credentials.
* Server address is correct.
* Version is correct.
* Themes and resources load.
* Secure store works.
* Local migrations work.
* Drafts survive upgrade.
* Queue survives upgrade.
* Crash handling is safe.
* Production certificate validation cannot be bypassed.
* No debug console opens unexpectedly.

---

# Chapter 2913 — Final Server Review

Verify:

* Runs as dedicated user.
* Binds only to intended interface.
* Nginx handles TLS.
* PostgreSQL is not LAN-exposed.
* Redis is not LAN-exposed.
* Storage mount is required.
* systemd hardening works.
* Readiness is accurate.
* Workers start once.
* Shutdown is graceful.
* Secret values are redacted.

---

# Chapter 2914 — Release Notes Requirements

Release notes shall include:

```text
Version
Release date
Main features
Security design summary
Installation requirements
Upgrade instructions
Database migration note
Known limitations
Compatibility
Backup warning
Rollback note
```

They shall not expose vulnerabilities unnecessarily.

---

# Chapter 2915 — Version 1.0 Known Limitations

At minimum, document:

```text
LAN-only design
Windows desktop client only
One primary cryptographic device per user
No automatic private-key recovery
No full forward secrecy
No voice or video
No public federation
Server can observe metadata
Offline revocation is delayed until reconnect
Previously decrypted content cannot be remotely revoked
Search covers locally cached messages
```

---

# Chapter 2916 — Post-Version 1.0 Backlog

Future work may include:

```text
Secure multi-device support
Encrypted key recovery
Independent key verification
Improved forward secrecy
Mobile client
Linux client packaging
Advanced high availability
PostgreSQL replication
Distributed application servers
External monitoring integration
Improved message-list virtualisation
Optional reactions
Advanced retention tooling
```

Future work shall not be represented as already implemented.

---

# Chapter 2917 — Roadmap Acceptance Criteria

The roadmap is acceptable when:

* Every major subsystem has a dependency-aware phase.
* Every phase has outputs.
* Every phase has tests.
* Every phase has an exit gate.
* Security-critical work occurs early enough.
* Deployment is tested before final release.
* Documentation and evaluation are included.
* Version 1.0 scope is protected.
* Final completion criteria are measurable.

---

# Chapter 2918 — Implementation Roadmap Summary

BlueBubbles shall be implemented as a sequence of tested vertical and foundational milestones.

The project shall begin with requirements, repository structure, shared contracts, configuration and PostgreSQL persistence.

Authentication and secure local key storage shall be completed before messaging.

Cryptographic primitives, canonical serialisation and deterministic test vectors shall be proven before encrypted messaging is integrated with the server.

Direct and group messaging shall then be implemented as an end-to-end vertical slice.

Realtime WebSocket events shall be added only after durable REST and database operations work correctly.

Attachments shall use a separate streamed and resumable milestone.

Local caching, drafts and offline queueing shall be added after server-authoritative messaging is stable.

The interface shall be connected through ViewModels rather than direct infrastructure calls.

Administrative actions shall be built only after the audit writer can record them transactionally.

Synchronisation and conflict recovery shall be tested using disconnections, expired cursors, key changes and membership changes.

Deployment shall be rehearsed on clean Debian and Windows environments.

Version 1.0 shall not be released until security, recovery, accessibility, usability, upgrade, rollback and backup gates pass.

The roadmap shall favour a smaller complete and secure implementation over an unfinished collection of additional features.

---

# End of Part 27

Part 28 will define the complete automated and manual testing specification, including:

* Test strategy.
* Test identifiers.
* Unit testing.
* Integration testing.
* End-to-end testing.
* Security testing.
* Cryptographic testing.
* Database testing.
* API testing.
* WebSocket testing.
* File-transfer testing.
* Offline recovery testing.
* Interface testing.
* Performance testing.
* Usability testing.
* Acceptance-test matrices.

---

## Task-specific authoritative source: Part 30

# Part 30 — Final Coding-AI Execution Contract and Version 1.0 Delivery Definition

---

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

# Chapter 3399 — Shared Contract Output

The coding AI shall then produce:

```text
Protocol version models
Error envelopes
Pagination models
Authentication DTOs
Conversation DTOs
Message DTOs
Attachment DTOs
WebSocket envelopes
Health DTOs
Administrative DTOs
Algorithm identifiers
```

All models shall include validation and tests.

---

# Chapter 3400 — Configuration Output

Required:

```text
ServerSettings
ClientSettings
Nested setting models
YAML loader
Environment override loader
Secret-file loader
Validation command
Example configurations
Redaction tests
Production safety tests
```

The client and server shall not read unrelated configuration directly throughout the codebase.

---

# Chapter 3401 — Database Output

Required:

```text
SQLAlchemy declarative base
ORM tables
Naming convention
Alembic configuration
Initial migrations
Seed logic for roles and permissions
Repository implementations
Unit of Work
Database health check
Migration revision check
Repository tests
```

---

# Chapter 3402 — Authentication Output

Required:

```text
AuthenticationProvider protocol
Mock provider
LDAP provider
Optional local provider
PasswordHasher
TokenManager
SessionService
AuthenticationService
LoginAttemptService
Authentication routes
Client login service
Client secure-token storage
Tests
```

---

# Chapter 3403 — Public-Key Output

Required:

```text
ClientKeyManager
IdentityKeyGenerator
EncryptedPrivateKeyStore
KeyProtectionService
Public-key API
Public-key repository
Key version models
Fingerprint calculation
Revocation
Rotation
Key-change events
Test vectors
```

---

# Chapter 3404 — Conversation Output

Required:

```text
Conversation domain entities
Membership entities
Direct pair constraint
Conversation repositories
ConversationService
GroupService
Conversation routes
Group routes
Conversation client service
Group client service
Membership tests
```

---

# Chapter 3405 — Messaging Output

Required:

```text
MessageEncryptionService
MessageEnvelopeValidator
MessagingService
MessageRepository
Recipient-key repository
Message routes
Delivery and read services
ClientMessagingService
Pending-message models
Message cache
Reply
Edit
Delete
Idempotency
Tests
```

---

# Chapter 3406 — WebSocket Output

Required:

```text
WebSocket endpoint
WebSocketConnection
WebSocketConnectionManager
Authentication handshake
Heartbeat
Server event dispatcher
Client WebSocket client
Client event dispatcher
EventPublisher
Transactional outbox worker
Reconnect logic
Event cursor
Tests
```

---

# Chapter 3407 — Attachment Output

Required:

```text
AttachmentEncryptionService
AttachmentPathBuilder
FileStorage abstraction
LocalFileStorage
AttachmentService
AttachmentRepository
Upload session routes
Chunk routes
Completion route
Download route
Prepared-upload client storage
UploadWorker
DownloadWorker
Transfer page ViewModel
Tests
```

---

# Chapter 3408 — Offline Output

Required:

```text
OfflineAction model
OfflineActionRepository
OfflineQueueService
OfflineActionExecutor
SynchronizationService
SynchronizationStateRepository
ConflictResolver
Conflict persistence
Tombstones
Queue interface
Reconnection integration
Tests
```

---

# Chapter 3409 — Client Storage Output

Required:

```text
LocalDatabaseManager
Client migrations
SecureStore abstraction
Windows Credential Manager implementation
Encrypted local repositories
Draft repository
Message cache
Search index
Cache manager
Transfer-state repository
Profile lock
Migration tests
```

---

# Chapter 3410 — Interface Output

Required pages:

```text
Login
Main shell
Chats
Contacts
Groups
Transfers
Search
Announcements
Settings
Sessions
Diagnostics
Administration dashboard
Users
Connections
Audit
Alerts
Workers
Configuration
Exports
```

Every required page shall have:

* View.
* ViewModel.
* Loading state.
* Empty state.
* Error state.
* Accessible controls.
* Tests.

---

# Chapter 3411 — Administration Output

Required:

```text
Permission catalogue
Role mappings
Admin capability response
UserAdministrationService
SessionAdministrationService
ConnectionAdministrationService
AdminDashboardService
SecurityAlertService
ConfigurationService
AnnouncementService
WorkerAdministrationService
MaintenanceService
Audit query and export
Tests
```

---

# Chapter 3412 — Audit Output

Required:

```text
Audit ORM model
Audit chain-state model
AuditWriter
Canonical serialiser
Hash service
Append-only database protections
AuditService
AuditVisibilityFilter
AuditIntegrityService
Verification worker
Audit routes
Audit GUI
Tamper tests
```

---

# Chapter 3413 — Monitoring Output

Required:

```text
Liveness
Readiness
Component health
Capability health
PostgreSQL check
Redis check
Directory check
Storage check
TLS check
Outbox check
Worker check
Metrics
Dashboard aggregation
Backup-status check
Alerts
```

---

# Chapter 3414 — Deployment Output

Required server files:

```text
systemd unit
Nginx site configuration
Production configuration example
Secret-file documentation
Directory creation script
Install script
Upgrade script
Rollback script
Backup script
Restore guide
Firewall guide
Active Directory guide
Health-verification script
```

Required client files:

```text
Build script
PyInstaller or selected packaging configuration
Installer definition
Managed configuration example
Upgrade guide
Uninstallation behaviour
```

---

# Chapter 3415 — Documentation Output

The final delivery shall include:

```text
README.md
Architecture.md
Security.md
Cryptography.md
Database.md
API.md
WebSocket.md
Client.md
Administration.md
Installation.md
Configuration.md
Active-Directory.md
Backup.md
Restore.md
Upgrade.md
Rollback.md
Operations.md
Testing.md
Known-Limitations.md
User-Guide.md
Administrator-Guide.md
Developer-Guide.md
```

Documentation names may vary, but equivalent coverage is mandatory.

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

# Chapter 3458 — Version 1.0 Mandatory Feature Definition

BlueBubbles Version 1.0 shall contain all of the following:

```text
Active Directory or approved local authentication

Application sessions

Access and refresh tokens

Session revocation

Role-based permissions

Employee, Helpdesk, HR, Administrator and SuperAdministrator roles

Contacts

Direct conversations

Group conversations

Group ownership and moderation

End-to-end encrypted messages

Message signatures

Replies

Message editing

Message deletion

Delivery and read states

Encrypted attachments

Resumable uploads and downloads

Encrypted private-key storage

Encrypted local cache

Draft persistence

Offline queue

Event replay and synchronisation

Local search

Announcements

Desktop notifications

System tray

Administration dashboard

User administration

Session administration

Connection administration

Tamper-evident audit

Security alerts

Worker monitoring

Configuration history

Maintenance mode

Debian deployment

Windows installer

Backup and restore

Upgrade and rollback

Testing and documentation
```

---

# Chapter 3459 — Version 1.0 Exclusion Definition

Version 1.0 shall not be required to provide:

```text
Voice calls

Video calls

Screen sharing

Remote desktop

Public Internet federation

Mobile applications

Browser client

Multiple independent cryptographic devices

Double-ratchet encryption

Automatic private-key cloud recovery

Bots

Plugins

Public link previews

GIF services

Kubernetes

Multi-node high availability

Automatic zero-downtime upgrades

Plaintext server moderation
```

No placeholder controls for these features shall appear.

---

# Chapter 3460 — Release Blockers

The release shall be blocked by any known:

```text
Authentication bypass

Authorisation bypass

Plaintext server storage

Private-key transmission

Cryptographic verification bypass

Data-corrupting migration

Unrecoverable routine client crash

Duplicate message under normal retry

Audit-chain failure

Broken backup restore

Broken TLS validation

Exposed PostgreSQL or Redis

Final SuperAdministrator lockout defect

Critical accessibility failure in core workflow

Required page containing non-functional controls
```

---

# Chapter 3461 — Defect Acceptance Rule

Version 1.0 may contain known low or limited medium defects only when:

* They do not affect security.
* They do not risk data loss.
* A workaround exists.
* They are documented.
* They do not invalidate mandatory acceptance criteria.
* They have a planned correction.

No known critical or high defect is acceptable.

---

# Chapter 3462 — Final Release Package

The final delivery package shall include:

```text
BlueBubbles source repository

Server release archive

Windows client installer

Release checksums

Database migrations

Configuration templates

Deployment scripts

Backup scripts

Documentation

Test report

Coverage report

Performance report

Known limitations

Release notes

Licence notices
```

---

# Chapter 3463 — Final Source Repository State

Before delivery:

```text
Main branch passes quality checks.

No uncommitted generated changes remain.

Version tag exists.

Release notes match version.

No secrets exist in history where preventable.

Dependencies are locked.

Migrations are at the release head.

Documentation links work.

Build scripts succeed.

Test evidence is archived.
```

---

# Chapter 3464 — Final Server Archive Contents

The server archive shall include only required release files.

It shall not include:

* Local virtual environment.
* Developer `.env`.
* Database dumps.
* Test credentials.
* Private certificates.
* Client profile data.
* IDE settings unless intentionally shared.
* Cache directories.
* Temporary files.

---

# Chapter 3465 — Final Client Installer Contents

The client installer shall include:

* Application executable.
* Required libraries.
* Qt plugins.
* Themes.
* Icons.
* Managed configuration.
* Licence notices.
* Version metadata.
* Uninstaller.

It shall not include:

* User private keys.
* Server secrets.
* Test accounts.
* Debug-only endpoints.
* Synthetic message databases.
* Development certificates.

---

# Chapter 3466 — Release Checksum Requirement

SHA-256 checksums shall be generated for:

```text
Server archive

Windows installer

Optional documentation archive

Optional source archive
```

The checksum file shall include exact filenames and release version.

---

# Chapter 3467 — Release Signing

Where signing infrastructure is available:

* Sign Windows installer.
* Sign application executable.
* Sign release manifest.
* Protect signing key.
* Record signature validation procedure.

Unsigned NEA builds shall state that limitation clearly.

---

# Chapter 3468 — Final Clean-Environment Verification

Before delivery, perform:

```text
Clean Debian installation

Clean PostgreSQL migration

Clean Redis configuration

Clean Nginx and TLS setup

Clean Windows client installation

Two-user encrypted message test

Group test

Attachment test

Offline test

Administration test

Audit verification

Backup and restore test
```

---

# Chapter 3469 — Final Smoke-Test Sequence

Final smoke test:

```text
1. Start all services.

2. Confirm liveness and readiness.

3. Authenticate administrator.

4. Authenticate two ordinary users.

5. Create direct conversation.

6. Send and receive encrypted message.

7. Verify read state.

8. Edit message.

9. Delete message.

10. Create group.

11. Send group message.

12. Transfer attachment.

13. Disconnect one client.

14. Queue message.

15. Reconnect and submit once.

16. Revoke one session.

17. Review audit event.

18. Verify audit chain.

19. Restart server.

20. Confirm persistence.
```

---

# Chapter 3470 — Final Plaintext Inspection

After the final smoke test, search for known plaintext markers in:

```text
PostgreSQL dump

Server logs

Audit records

Outbox payloads

Attachment storage

Temporary upload storage

Exports

Diagnostics

Backup set
```

Any unexpected occurrence shall block release.

---

# Chapter 3471 — Final Network Inspection

From a separate client host, verify:

```text
HTTPS open

WSS functional

HTTP redirects or remains closed according to policy

SSH restricted

PostgreSQL closed

Redis closed

Internal Uvicorn port closed

No development server port exposed
```

---

# Chapter 3472 — Final Permission Inspection

Verify:

* Service account cannot use interactive shell.
* Service account cannot modify release files.
* Service account can read configuration.
* Service account can write required state paths.
* Nginx can read TLS key.
* BlueBubbles cannot read TLS private key unless explicitly required.
* Runtime database role cannot modify audit history.
* Secret files are not world-readable.

---

# Chapter 3473 — Final Key Inspection

Verify:

```text
No private identity key in PostgreSQL.

No private identity key in Redis.

No private identity key in server logs.

No private identity key in server backups.

Client private key file is encrypted.

Wrong local key fails decryption.

Historical key version remains available after rotation.

Revoked key is not used for new messages.
```

---

# Chapter 3474 — Final Session Inspection

Verify:

```text
Refresh tokens are hashed server-side.

Access tokens expire.

Refresh tokens rotate.

Old refresh token reuse is detected.

Logout invalidates session.

Administrative revocation invalidates session.

WebSocket disconnect follows revocation.

Disabled user cannot refresh.
```

---

# Chapter 3475 — Final Audit Inspection

Verify:

```text
Sequence starts correctly.

Events append in order.

Previous hash links correctly.

Entry hash reproduces.

Runtime role cannot update row.

Runtime role cannot delete row.

Full verification succeeds.

Privileged test tamper causes failure.

Failure creates critical alert.
```

---

# Chapter 3476 — Final Offline Inspection

Verify:

```text
Draft stored encrypted.

Queue stored encrypted.

Pending item survives restart.

Valid action sends once.

Removed-member action is blocked.

Edit conflict preserves attempted text.

Expired cursor triggers resync.

Local cursor advances only after commit.
```

---

# Chapter 3477 — Final Attachment Inspection

Verify:

```text
Large file processed in chunks.

Memory remains bounded.

Every chunk has unique nonce.

Modified chunk fails.

Upload resumes.

Download resumes.

Final plaintext hash matches.

Server storage contains no plaintext marker.

Unauthorised user cannot download.
```

---

# Chapter 3478 — Final UI Inspection

Verify:

```text
All required pages open.

No required button is inactive without explanation.

Keyboard navigation works.

Focus remains visible.

Messages wrap.

Long filenames elide.

High-contrast theme works.

150% font scale works.

Offline state is clear.

Pending and stored states differ.

Destructive actions require confirmation.

Administration visibility follows capability.
```

---

# Chapter 3479 — Final Documentation Inspection

Verify:

* Commands match final paths.
* Package names are correct.
* Service names are correct.
* Screenshots use current interface.
* API paths are current.
* Configuration fields are current.
* Default limits match code.
* Known limitations are honest.
* Recovery instructions were tested.
* No secret appears in documentation.

---

# Chapter 3480 — Coding-AI Final Response Requirements

When the coding AI completes the project, its final response shall include:

```text
Completion summary

Repository location

Server build location

Client installer location

Documentation location

Test result summary

Known limitations

Deployment prerequisites

Exact next action for the operator
```

It shall not include unsupported claims.

---

# Chapter 3481 — Coding-AI Progress Reporting

During generation, progress reports shall identify:

```text
Current phase

Files created or changed

Verification performed

Tests passed

Tests failed

Corrections made

Remaining work
```

Reports shall remain concise and factual.

---

# Chapter 3482 — Coding-AI Uncertainty Rule

When uncertain about:

* Library behaviour.
* Operating-system command.
* Security property.
* Protocol compatibility.
* Migration safety.
* Packaging behaviour.

The coding AI shall verify through documentation, tests or controlled execution rather than guessing.

---

# Chapter 3483 — Coding-AI Dependency Rule

The coding AI shall not add a dependency merely because it simplifies one function.

Before adding a dependency, verify:

* Maintenance status.
* Licence.
* Python compatibility.
* Security history.
* Packaging compatibility.
* Necessity.
* Whether standard library or existing dependency suffices.

---

# Chapter 3484 — Coding-AI Refactoring Rule

Refactoring shall preserve:

* Public behaviour.
* Database compatibility.
* Protocol compatibility.
* Cryptographic canonicalisation.
* Audit history.
* Queue recovery.
* Test coverage.

Cryptographic serialisation shall not change during casual refactoring.

---

# Chapter 3485 — Coding-AI Security Review Trigger

A dedicated security review shall occur after changes to:

```text
Authentication
Token handling
Permissions
Cryptography
Private-key storage
Message envelope
Attachment manifest
File paths
Audit
Deployment exposure
Secret handling
Offline replay
```

---

# Chapter 3486 — Coding-AI Migration Review Trigger

A dedicated migration review shall occur after:

* Column removal.
* Type change.
* Constraint addition.
* Primary-key change.
* Foreign-key change.
* Message format change.
* Recipient-envelope change.
* Audit model change.
* Client encrypted-record change.

---

# Chapter 3487 — Coding-AI Compatibility Review Trigger

Compatibility review shall occur after changes to:

```text
REST DTO
WebSocket event
Error code
Protocol version
Algorithm identifier
Canonical timestamp format
Pagination cursor
Attachment manifest
Client local schema
Required client version
```

---

# Chapter 3488 — No Automatic Scope Expansion

The coding AI shall not add:

* Reactions.
* Calls.
* Stickers.
* External integrations.
* Cloud features.
* Multi-device key sharing.
* Public registration.
* Anonymous access.
* Browser administration.
* Bot APIs.

unless the specification is formally amended.

---

# Chapter 3489 — No Automatic Scope Reduction

The coding AI shall not remove difficult required features such as:

* Audit integrity.
* Offline idempotency.
* Attachment resume.
* Public-key versioning.
* Session revocation.
* Role boundaries.
* Backup restore.
* Accessibility.
* Deployment validation.

Complexity alone is not a valid reason to omit a mandatory requirement.

---

# Chapter 3490 — Simplification Rule

Where implementation complexity must be reduced, simplify through approved methods.

Examples:

```text
Use one primary cryptographic device.

Use serial offline queue processing.

Use controlled maintenance upgrades.

Use local filesystem attachment storage.

Use one FastAPI application instance.

Use one PostgreSQL server.

Use one Redis server.

Use explicit limited roles.

Use plain-text message rendering.
```

Do not simplify by weakening security or correctness.

---

# Chapter 3491 — Evidence Preservation Rule

During development, preserve:

```text
Test outputs
Migration logs
Performance results
Screenshots
User feedback
Defect records
Architecture decisions
Deployment transcripts
Backup restore evidence
Security review findings
```

This evidence supports both release confidence and NEA evaluation.

---

# Chapter 3492 — Final Definition of Done

BlueBubbles Version 1.0 is done only when:

```text
The complete required source code exists.

The server installs on clean Debian.

The client installs on clean Windows.

Two users can exchange encrypted messages.

Groups enforce membership.

Attachments transfer securely.

Offline actions recover safely.

Administration works within role boundaries.

Audit history is tamper-evident.

Server plaintext inspections pass.

Backups restore successfully.

Upgrades and rollbacks are tested.

Core accessibility checks pass.

Documentation matches the release.

No critical or high defect remains.

Known limitations are published.
```

---

# Chapter 3493 — Final Delivery Statement

The final BlueBubbles delivery shall be a complete, tested and documented LAN-only encrypted messaging system.

It shall consist of:

```text
A FastAPI server

A PySide6 Windows client

A PostgreSQL authoritative database

A Redis transient-state service

An Nginx TLS reverse proxy

A systemd-managed Debian deployment

Client-side end-to-end message encryption

Client-side encrypted attachment transfer

Encrypted client local storage

Offline queueing and synchronisation

Role-based administration

Tamper-evident audit

Monitoring, backup, restore and recovery procedures
```

The server shall route and retain encrypted records without requiring user private keys.

The client shall protect user private keys, verify signatures and decrypt authorised content.

Administrative power shall remain separate from content decryption.

The implementation shall favour correctness, evidence and recoverability over unnecessary feature breadth.

---

# Chapter 3494 — Complete Version 1.0 Acceptance Declaration

Version 1.0 may be declared accepted only when the project owner can truthfully state:

```text
The implemented system meets the mandatory functional requirements.

The server stores encrypted message and attachment content rather than plaintext.

Authentication, sessions and role permissions have been tested.

Messages and attachments are authenticated cryptographically.

Private keys remain client-side and encrypted at rest.

Offline retries do not duplicate accepted messages.

Membership changes prevent stale future access.

Administrative actions are auditable.

Audit tampering is detectable.

The server and client can be installed from clean environments.

The system can be backed up and restored.

The upgrade and rollback procedures have been rehearsed.

Core user workflows are usable and accessible.

Known limitations are documented clearly.
```

---

# Chapter 3495 — Specification Completion

This chapter completes the BlueBubbles Version 1.0 specification.

The complete specification now defines:

```text
Requirements

Architecture

Database

Authentication

Authorisation

Cryptography

Messaging

Groups

Attachments

Networking

REST APIs

WebSockets

Desktop interface

Local storage

Offline operation

Synchronisation

Administration

Audit

Monitoring

Testing

Deployment

Backup

Restore

Upgrade

Rollback

Operational recovery

Implementation order

Final delivery
```

No additional part is required to define Version 1.0.

Implementation may now proceed using Parts 1 through 30 as the authoritative project contract.

---

# End of Part 30

# End of the Complete BlueBubbles Version 1.0 Specification
