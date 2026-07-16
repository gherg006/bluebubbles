# Task 24 — Release candidate

> This is a self-contained implementation task split from the complete BlueBubbles Version 1.0 specification. Source requirements below are reproduced verbatim, not summarised. Where a repeated project-wide rule conflicts with a task-local choice, the project-wide rule wins.

## Required predecessors

Task 21, Task 22, Task 23.

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

## Task-specific authoritative source: Part 29

# Part 29 — Deployment, Installation, Upgrade, Backup, Restore and Operational Runbooks

---

# Chapter 3115 — Deployment Specification Purpose

This section defines how BlueBubbles shall be installed, configured, secured, upgraded, backed up, restored and operated.

It shall ensure that:

* The server can be installed reproducibly on Debian.
* Production services run under restricted accounts.
* PostgreSQL and Redis are not unnecessarily exposed.
* Attachment data uses a controlled storage layout.
* Nginx terminates TLS securely.
* The FastAPI service is managed by systemd.
* Configuration and secrets remain outside source code.
* Windows clients can be packaged and installed consistently.
* Initial administration does not rely on default credentials.
* Backups include every required data component.
* Restore procedures are tested.
* Upgrades can be rehearsed and rolled back.
* Operational failures have documented recovery procedures.
* Emergency actions preserve evidence and data integrity.

The coding AI shall generate deployment assets that match the final implemented application rather than generic placeholder files.

---

# Chapter 3116 — Supported Server Platform

The primary Version 1.0 server platform shall be:

```text
Debian 13 stable
```

A compatible later Debian release may be supported after testing.

The server specification assumes:

* A dedicated Debian virtual machine.
* systemd.
* PostgreSQL.
* Redis.
* Nginx.
* Python 3.13 or a supported packaged Python runtime.
* Local or mounted filesystem attachment storage.
* LAN access only.
* DNS resolution for the chosen internal hostname.
* Reliable time synchronisation.

---

# Chapter 3117 — Supported Client Platform

The primary Version 1.0 client platform shall be:

```text
Windows 11
```

Windows 10 may be supported if testing confirms compatibility.

The packaged client shall not require users to install:

* Python.
* PySide6.
* cryptography.
* SQLCipher libraries separately.
* Development tools.

The installer shall contain or install every approved runtime dependency.

---

# Chapter 3118 — Production Deployment Topology

Recommended topology:

```text
Windows clients
        │
        │ HTTPS / WSS
        ▼
Internal DNS name
        │
        ▼
Nginx reverse proxy
        │
        │ HTTP over loopback or Unix socket
        ▼
BlueBubbles FastAPI application
        │
        ├── PostgreSQL
        ├── Redis
        ├── Attachment storage
        ├── Audit storage in PostgreSQL
        └── Local protected logs
```

PostgreSQL and Redis shall normally remain accessible only from the server host.

---

# Chapter 3119 — Example Production Hostname

Example internal hostname:

```text
bluebubbles.example.internal
```

The real hostname shall:

* Resolve through internal DNS.
* Match the TLS certificate.
* Remain stable for installed clients.
* Avoid use of raw IP addresses where possible.
* Avoid using `.local` where multicast DNS conflicts may occur.
* Be documented in deployment configuration.

---

# Chapter 3120 — Server Resource Planning

Initial small-deployment recommendation:

```text
CPU:

4 virtual cores

RAM:

8 GiB minimum

System disk:

40 GiB or more

Attachment storage:

Sized according to organisational use

Database storage:

Separate or monitored filesystem where practical
```

Higher attachment volume, larger groups or many concurrent clients may require more resources.

Final sizing shall be based on measured tests rather than these starting values alone.

---

# Chapter 3121 — Storage Separation

Recommended storage separation:

```text
System and application:

Fast virtual SSD

PostgreSQL data:

Fast reliable storage

Redis data:

System disk or dedicated small fast storage

Attachment data:

Large dedicated volume

Backups:

Separate storage target
```

The attachment volume shall not be the only location containing attachment backups.

---

# Chapter 3122 — Example Filesystem Layout

Recommended layout:

```text
/opt/bluebubbles/
├── releases/
│   ├── 1.0.0/
│   └── 1.0.1/
├── current -> /opt/bluebubbles/releases/1.0.1
└── shared/
    ├── venv/
    └── runtime/

/etc/bluebubbles/
├── server.yaml
├── environment
└── secrets/

/var/lib/bluebubbles/
├── attachments/
├── uploads/
├── exports/
├── diagnostics/
└── state/

/var/log/bluebubbles/

/var/backups/bluebubbles/
```

The exact paths may differ, but one documented layout shall be authoritative.

---

# Chapter 3123 — Service Account

The application shall run under a dedicated non-login service account.

Example:

```text
bluebubbles
```

Suggested creation:

```bash
sudo useradd \
  --system \
  --home-dir /var/lib/bluebubbles \
  --create-home \
  --shell /usr/sbin/nologin \
  bluebubbles
```

The account shall not have:

* Interactive shell access.
* `sudo`.
* Membership in unrelated privileged groups.
* Access to user home directories.
* Permission to modify application release files.

---

# Chapter 3124 — Service Group

A matching group shall be used:

```text
bluebubbles
```

Nginx may require limited access to a Unix socket or selected exported files.

Where shared access is required, create a narrowly scoped group rather than granting world-readable permissions.

---

# Chapter 3125 — Directory Ownership

Recommended ownership:

```text
/opt/bluebubbles/releases

root:root

/etc/bluebubbles

root:bluebubbles

/etc/bluebubbles/secrets

root:bluebubbles

/var/lib/bluebubbles

bluebubbles:bluebubbles

/var/log/bluebubbles

bluebubbles:bluebubbles
```

The service account shall read configuration but shall not normally modify `/etc/bluebubbles`.

---

# Chapter 3126 — Directory Permissions

Suggested permissions:

```text
/opt/bluebubbles/releases

0755

/etc/bluebubbles

0750

/etc/bluebubbles/server.yaml

0640

/etc/bluebubbles/environment

0640

/etc/bluebubbles/secrets

0750

Secret files

0640

/var/lib/bluebubbles

0750

/var/log/bluebubbles

0750
```

Permissions shall be validated during installation and startup.

---

# Chapter 3127 — Attachment Volume Mount

Recommended mount point:

```text
/var/lib/bluebubbles/attachments
```

A separate large virtual disk may be mounted there.

Example filesystem preparation:

```bash
sudo mkfs.ext4 /dev/disk/by-id/<attachment-disk-id>
sudo mkdir -p /var/lib/bluebubbles/attachments
```

The actual disk identifier shall be verified carefully before formatting.

---

# Chapter 3128 — Persistent Mount Configuration

Example `/etc/fstab` entry:

```text
UUID=<filesystem-uuid> /var/lib/bluebubbles/attachments ext4 defaults,noatime,nodev,nosuid 0 2
```

The deployment shall use the filesystem UUID rather than an unstable `/dev/sdX` name.

`noexec` may be added if application behaviour and maintenance scripts do not require execution from the volume.

---

# Chapter 3129 — Mount Validation

Before starting BlueBubbles, verify:

```bash
findmnt /var/lib/bluebubbles/attachments
df -h /var/lib/bluebubbles/attachments
sudo -u bluebubbles test -r /var/lib/bluebubbles/attachments
sudo -u bluebubbles test -w /var/lib/bluebubbles/attachments
```

The application shall refuse attachment operations if the expected mount is missing.

It shall not silently write large attachment data into the root filesystem beneath an unmounted directory.

---

# Chapter 3130 — Mount Guard

A mount guard may use one or more of:

* `RequiresMountsFor=` in systemd.
* Filesystem identifier check.
* Expected marker file.
* Device comparison.
* Minimum capacity check.
* Startup storage health validation.

Example systemd directive:

```ini
RequiresMountsFor=/var/lib/bluebubbles/attachments
```

---

# Chapter 3131 — Attachment Directory Structure

Physical attachment storage shall use generated identifiers.

Example:

```text
/var/lib/bluebubbles/attachments/
├── objects/
│   └── ab/
│       └── cd/
│           └── <attachment-uuid>/
│               ├── manifest.bin
│               ├── chunk-00000000.bin
│               ├── chunk-00000001.bin
│               └── chunk-00000002.bin
└── lost-and-found/
```

User-supplied filenames shall not become path components.

---

# Chapter 3132 — Temporary Upload Structure

Temporary uploads:

```text
/var/lib/bluebubbles/uploads/
└── <upload-uuid>/
    ├── metadata.json
    ├── chunk-00000000.part
    └── chunk-00000001.part
```

Temporary and permanent storage shall remain separate.

Upload finalisation shall use an atomic rename where both directories are on the same filesystem.

---

# Chapter 3133 — Export and Diagnostic Storage

Recommended:

```text
/var/lib/bluebubbles/exports
/var/lib/bluebubbles/diagnostics
```

Files in these directories shall:

* Use generated names.
* Use restrictive permissions.
* Have expiry metadata.
* Be removed by cleanup workers.
* Never be served as unrestricted static files.

---

# Chapter 3134 — Required Debian Packages

Initial packages may include:

```bash
sudo apt update

sudo apt install -y \
  nginx \
  postgresql \
  postgresql-contrib \
  redis-server \
  python3 \
  python3-venv \
  python3-pip \
  build-essential \
  libpq-dev \
  ca-certificates \
  curl \
  jq \
  openssl \
  rsync \
  acl \
  logrotate
```

The exact package list shall be generated from verified application dependencies.

Unnecessary compilers may be removed from the production server after installation when wheels are available.

---

# Chapter 3135 — Python Runtime

The production server shall use the tested Python version.

Where Debian’s default Python is older than the supported application version, use one controlled method:

* Official Debian package from the supported release.
* A trusted internal package.
* A self-contained application build.
* A carefully managed alternate Python installation.

The deployment shall not overwrite Debian’s system Python.

---

# Chapter 3136 — Python Virtual Environment

Recommended virtual environment:

```text
/opt/bluebubbles/shared/venv
```

Creation:

```bash
sudo python3 -m venv /opt/bluebubbles/shared/venv

sudo /opt/bluebubbles/shared/venv/bin/pip install \
  --upgrade pip setuptools wheel
```

Application dependencies shall be installed from locked requirements or the locked project configuration.

---

# Chapter 3137 — Dependency Installation

Preferred release installation:

```bash
sudo /opt/bluebubbles/shared/venv/bin/pip install \
  --require-hashes \
  -r /opt/bluebubbles/current/requirements/server.txt
```

Where a wheel is produced:

```bash
sudo /opt/bluebubbles/shared/venv/bin/pip install \
  --no-deps \
  /opt/bluebubbles/current/dist/bluebubbles-1.0.0-py3-none-any.whl
```

One reproducible dependency method shall be authoritative.

---

# Chapter 3138 — Dependency Verification

After installation:

```bash
sudo -u bluebubbles \
  /opt/bluebubbles/shared/venv/bin/python \
  -m bluebubbles.server.cli verify-installation
```

The command shall verify:

* Package import.
* Version.
* Required dependency versions.
* Configuration readability.
* No development-only provider in production.
* Storage path availability.
* Database driver availability.

---

# Chapter 3139 — PostgreSQL Installation

PostgreSQL shall be installed from the Debian-supported package or an approved PostgreSQL repository.

Verify service:

```bash
sudo systemctl enable --now postgresql
sudo systemctl status postgresql
```

The exact supported PostgreSQL major version shall be documented and tested.

---

# Chapter 3140 — PostgreSQL Database and Role

Create a dedicated database and application role.

Example:

```bash
sudo -u postgres psql
```

```sql
CREATE ROLE bluebubbles_app
    LOGIN
    PASSWORD '<generated-secret>'
    NOSUPERUSER
    NOCREATEDB
    NOCREATEROLE
    NOINHERIT;

CREATE DATABASE bluebubbles
    OWNER bluebubbles_app
    ENCODING 'UTF8';
```

The password shall be generated securely and stored in a protected secret file.

---

# Chapter 3141 — PostgreSQL Network Binding

PostgreSQL should listen only on loopback unless a separate database host is deliberately used.

Example:

```text
listen_addresses = '127.0.0.1,::1'
```

`pg_hba.conf` shall permit only the required role and database.

Example:

```text
host    bluebubbles    bluebubbles_app    127.0.0.1/32    scram-sha-256
host    bluebubbles    bluebubbles_app    ::1/128         scram-sha-256
```

---

# Chapter 3142 — PostgreSQL Authentication

Use:

```text
SCRAM-SHA-256
```

for password authentication.

Confirm:

```text
password_encryption = 'scram-sha-256'
```

The deployment shall not use trust authentication for the production application connection.

---

# Chapter 3143 — PostgreSQL Application Privileges

The application role shall receive only the required privileges.

Where migrations are performed using the same role, it requires schema modification permission.

A stronger production model may use:

```text
Migration role:

Owns schema and migrations.

Runtime role:

Reads and writes application tables but cannot alter schema.
```

Version 1.0 may use one role if complexity must be controlled, but the limitation shall be documented.

---

# Chapter 3144 — Audit Table Privileges

After migrations, restrict audit mutation.

The runtime role shall:

* Insert audit events through the approved database mechanism.
* Select permitted audit records.
* Not update audit events.
* Not delete audit events.

Where direct insert privilege creates integrity risks, use a controlled stored function or a restricted database design.

---

# Chapter 3145 — PostgreSQL Connection Secret

Recommended secret file:

```text
/etc/bluebubbles/secrets/database_url
```

Contents:

```text
postgresql+asyncpg://bluebubbles_app:<encoded-password>@127.0.0.1:5432/bluebubbles
```

Permissions:

```bash
sudo chown root:bluebubbles \
  /etc/bluebubbles/secrets/database_url

sudo chmod 0640 \
  /etc/bluebubbles/secrets/database_url
```

---

# Chapter 3146 — PostgreSQL Initial Validation

Run:

```bash
sudo -u bluebubbles \
  /opt/bluebubbles/shared/venv/bin/python \
  -m bluebubbles.server.cli check-database
```

The command shall verify:

* Connection.
* Database name.
* Server version.
* Required extensions.
* Migration revision.
* Runtime privileges.
* Audit protections.

---

# Chapter 3147 — Database Migrations

Apply migrations explicitly:

```bash
sudo -u bluebubbles \
  /opt/bluebubbles/shared/venv/bin/alembic \
  -c /etc/bluebubbles/alembic.ini \
  upgrade head
```

The service shall not perform uncontrolled schema upgrades automatically during every startup.

---

# Chapter 3148 — Migration Backup Requirement

Before any production migration:

```text
Database backup required.
```

For migrations affecting attachment references or stored formats:

```text
Attachment backup or snapshot required.
```

The upgrade script shall stop if the required pre-upgrade backup fails.

---

# Chapter 3149 — Redis Installation

Enable Redis:

```bash
sudo systemctl enable --now redis-server
sudo systemctl status redis-server
```

Redis shall be used only for transient state such as:

* Presence.
* Typing.
* Rate limiting.
* Pub/Sub.
* Selected short-lived caches.

PostgreSQL remains authoritative.

---

# Chapter 3150 — Redis Network Security

Recommended Redis binding:

```text
bind 127.0.0.1 ::1
protected-mode yes
```

Redis shall not listen on the LAN interface.

Verify:

```bash
ss -lntp | grep 6379
```

---

# Chapter 3151 — Redis Persistence

Redis persistence may be enabled according to operational preference, but application correctness shall not depend on Redis persistence.

A Redis restart may lose:

* Presence.
* Typing.
* Rate-limit counters.
* Transient caches.

It shall not lose:

* Messages.
* Sessions.
* Audit events.
* Attachments.
* Configuration history.

---

# Chapter 3152 — Redis Authentication

Where Redis remains loopback-only on a dedicated server, network isolation may be sufficient.

A password or ACL user may still be configured.

If used, store the credential in:

```text
/etc/bluebubbles/secrets/redis_url
```

The application shall not log the URL.

---

# Chapter 3153 — Redis Validation

Run:

```bash
sudo -u bluebubbles \
  /opt/bluebubbles/shared/venv/bin/python \
  -m bluebubbles.server.cli check-redis
```

The command shall verify:

* Connection.
* PING.
* Required command support.
* Pub/Sub.
* Key expiry.
* Safe namespace.

---

# Chapter 3154 — Active Directory Connectivity

The server shall reach the directory service over:

```text
LDAPS on TCP 636
```

or:

```text
LDAP with StartTLS
```

Plain unauthenticated LDAP shall not be used for credentials in production.

---

# Chapter 3155 — Directory DNS Requirements

Verify:

```bash
getent hosts dc01.example.internal
```

If using domain service records:

```bash
dig _ldap._tcp.example.internal SRV
```

The server shall use internal DNS capable of resolving directory hosts.

Hard-coded IP addresses should be avoided where certificates identify hostnames.

---

# Chapter 3156 — Directory Certificate Trust

The Debian server shall trust the internal certificate authority that issued the directory certificate.

Install the CA certificate:

```bash
sudo cp internal-root-ca.crt \
  /usr/local/share/ca-certificates/internal-root-ca.crt

sudo update-ca-certificates
```

Private CA keys shall never be copied to the BlueBubbles server.

---

# Chapter 3157 — Directory Service Account

If search-before-bind is required, use a dedicated read-only directory account.

It shall have permission only to:

* Search required user containers.
* Read approved profile attributes.
* Read relevant group membership.
* Read account-state attributes.

It shall not have domain-administrator privileges.

---

# Chapter 3158 — Directory Secret Files

Recommended:

```text
/etc/bluebubbles/secrets/ldap_bind_dn
/etc/bluebubbles/secrets/ldap_bind_password
```

Permissions:

```text
root:bluebubbles
0640
```

The bind password shall not appear in YAML, logs or command-line arguments.

---

# Chapter 3159 — Directory Configuration

Example non-secret configuration:

```yaml
directory:
  enabled: true
  mode: ldaps
  servers:
    - dc01.example.internal
    - dc02.example.internal
  port: 636
  base_dn: "DC=example,DC=internal"
  user_search_base: "OU=Users,DC=example,DC=internal"
  user_filter: "(&(objectClass=user)(sAMAccountName={username}))"
  username_attribute: "sAMAccountName"
  display_name_attribute: "displayName"
  email_attribute: "mail"
  department_attribute: "department"
  object_guid_attribute: "objectGUID"
  timeout_seconds: 5
```

The actual filter shall use library-supported escaping rather than raw string substitution.

---

# Chapter 3160 — Directory Group Mapping

Example:

```yaml
directory:
  role_mappings:
    "CN=BlueBubbles-Helpdesk,OU=Groups,DC=example,DC=internal": "Helpdesk"
    "CN=BlueBubbles-HR,OU=Groups,DC=example,DC=internal": "HR"
    "CN=BlueBubbles-Admins,OU=Groups,DC=example,DC=internal": "Administrator"
    "CN=BlueBubbles-SuperAdmins,OU=Groups,DC=example,DC=internal": "SuperAdministrator"
```

Unmapped users shall receive the default Employee role unless policy says otherwise.

---

# Chapter 3161 — Directory Connectivity Test

Use the application command:

```bash
sudo -u bluebubbles \
  /opt/bluebubbles/shared/venv/bin/python \
  -m bluebubbles.server.cli check-directory
```

It shall verify:

* DNS.
* TLS.
* Certificate trust.
* Service bind.
* User search.
* Required attributes.
* Group mapping.
* Timeout behaviour.

It shall not print the bind password.

---

# Chapter 3162 — Nginx Purpose

Nginx shall:

* Terminate TLS.
* Redirect HTTP to HTTPS where HTTP is exposed.
* Proxy REST requests.
* Proxy WebSocket upgrades.
* Apply body-size limits.
* Apply timeouts.
* Add security headers.
* Protect the internal application port.
* Optionally provide access logging.

---

# Chapter 3163 — Internal Application Binding

FastAPI/Uvicorn shall bind only to loopback or a Unix socket.

Example:

```text
127.0.0.1:8000
```

It shall not bind directly to:

```text
0.0.0.0:8000
```

in production unless a separate trusted proxy network requires it.

---

# Chapter 3164 — Example Nginx Server Block

Conceptual configuration:

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name bluebubbles.example.internal;

    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    listen [::]:443 ssl;
    server_name bluebubbles.example.internal;

    ssl_certificate     /etc/ssl/bluebubbles/fullchain.pem;
    ssl_certificate_key /etc/ssl/bluebubbles/private.key;

    client_max_body_size 20m;

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }

    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;

        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;

        proxy_read_timeout 75s;
    }
}
```

The final configuration shall match actual route paths and transfer limits.

---

# Chapter 3165 — Nginx Attachment Limits

Chunk upload requests are smaller than the complete attachment.

Therefore:

```text
client_max_body_size
```

shall exceed:

```text
Maximum encrypted chunk size
+
Protocol overhead
```

It does not need to equal the maximum whole-file size.

The application and Nginx limits shall be tested together.

---

# Chapter 3166 — Nginx Proxy Timeouts

Suggested starting values:

```nginx
proxy_connect_timeout 10s;
proxy_send_timeout 60s;
proxy_read_timeout 60s;
send_timeout 60s;
```

WebSocket read timeout shall exceed the heartbeat interval and allowed heartbeat delay.

Large streamed downloads may require a longer read timeout.

---

# Chapter 3167 — Nginx Buffering

For streamed attachment operations, consider:

```nginx
proxy_request_buffering off;
proxy_buffering off;
```

only on the specific routes that benefit from streaming.

Disabling buffering globally is unnecessary.

The final behaviour shall be tested with interruption and large files.

---

# Chapter 3168 — Trusted Proxy Configuration

FastAPI shall trust forwarded headers only from the local Nginx proxy.

The application shall not trust arbitrary client-supplied:

```text
X-Forwarded-For
X-Forwarded-Proto
```

Uvicorn proxy-header configuration shall restrict trusted proxy IPs.

---

# Chapter 3169 — Nginx Security Headers

Recommended headers:

```nginx
add_header X-Content-Type-Options "nosniff" always;
add_header Referrer-Policy "no-referrer" always;
add_header X-Frame-Options "DENY" always;
add_header Permissions-Policy "camera=(), microphone=(), geolocation=()" always;
```

A desktop API application may not need every browser-oriented header, but safe defaults are acceptable.

---

# Chapter 3170 — TLS Certificate

The certificate shall:

* Match the internal hostname.
* Be trusted by client devices.
* Use a valid date range.
* Include required intermediate certificates.
* Use an approved private key.
* Be readable only by Nginx.
* Be renewed before expiry.

---

# Chapter 3171 — TLS Private-Key Permissions

Recommended:

```bash
sudo chown root:root /etc/ssl/bluebubbles/private.key
sudo chmod 0600 /etc/ssl/bluebubbles/private.key
```

Nginx normally starts as root and opens the key before worker privilege reduction.

The BlueBubbles service account shall not require access to the TLS private key.

---

# Chapter 3172 — TLS Protocol Configuration

Recommended:

```nginx
ssl_protocols TLSv1.2 TLSv1.3;
```

Weak and obsolete protocols shall be disabled.

Cipher configuration should follow current Nginx and organisational guidance rather than an outdated static list.

---

# Chapter 3173 — TLS Validation Commands

Run:

```bash
sudo nginx -t
```

Then:

```bash
openssl s_client \
  -connect bluebubbles.example.internal:443 \
  -servername bluebubbles.example.internal
```

Verify:

* Certificate chain.
* Hostname.
* Expiry.
* Negotiated TLS version.
* No unexpected certificate.

---

# Chapter 3174 — systemd Service Purpose

systemd shall manage:

* Startup.
* Shutdown.
* Restart policy.
* Environment.
* Resource limits.
* Filesystem restrictions.
* Service dependencies.
* Logging integration.
* Attachment mount requirement.

---

# Chapter 3175 — Example systemd Unit

Conceptual unit:

```ini
[Unit]
Description=BlueBubbles Messaging Server
After=network-online.target postgresql.service redis-server.service
Wants=network-online.target
RequiresMountsFor=/var/lib/bluebubbles/attachments

[Service]
Type=simple
User=bluebubbles
Group=bluebubbles
WorkingDirectory=/opt/bluebubbles/current

EnvironmentFile=/etc/bluebubbles/environment

ExecStart=/opt/bluebubbles/shared/venv/bin/uvicorn \
    bluebubbles.server.main:app \
    --host 127.0.0.1 \
    --port 8000 \
    --proxy-headers \
    --forwarded-allow-ips 127.0.0.1

ExecReload=/bin/kill -HUP $MAINPID

Restart=on-failure
RestartSec=5s
TimeoutStartSec=60s
TimeoutStopSec=45s
KillSignal=SIGTERM

NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/lib/bluebubbles /var/log/bluebubbles
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
RestrictSUIDSGID=true
LockPersonality=true
MemoryDenyWriteExecute=true

[Install]
WantedBy=multi-user.target
```

The final hardening options shall be tested with all required libraries.

---

# Chapter 3176 — systemd Hardening Review

Use:

```bash
systemd-analyze security bluebubbles.service
```

Review:

* Filesystem access.
* Temporary directory isolation.
* Privilege escalation.
* Kernel access.
* Device access.
* Network restrictions.
* Executable memory requirements.

A high security score is useful, but application functionality must remain tested.

---

# Chapter 3177 — systemd Environment File

Example:

```text
BLUEBUBBLES_ENVIRONMENT=production
BLUEBUBBLES_CONFIG=/etc/bluebubbles/server.yaml
BLUEBUBBLES_DATABASE_URL_FILE=/etc/bluebubbles/secrets/database_url
BLUEBUBBLES_REDIS_URL_FILE=/etc/bluebubbles/secrets/redis_url
BLUEBUBBLES_LDAP_BIND_PASSWORD_FILE=/etc/bluebubbles/secrets/ldap_bind_password
```

The file shall not include secrets directly where file references are supported.

---

# Chapter 3178 — Enabling the Service

After installation:

```bash
sudo systemctl daemon-reload
sudo systemctl enable bluebubbles.service
sudo systemctl start bluebubbles.service
sudo systemctl status bluebubbles.service
```

Logs:

```bash
sudo journalctl -u bluebubbles.service -f
```

Logs shall remain sanitised even when viewed through journald.

---

# Chapter 3179 — Startup Validation

Before declaring the service ready, verify:

```bash
curl -fsS http://127.0.0.1:8000/health/live
curl -fsS http://127.0.0.1:8000/health/ready
curl -fsS https://bluebubbles.example.internal/health/live
```

The final public health path may differ but shall be documented.

---

# Chapter 3180 — Firewall Policy

The server firewall shall allow only required inbound traffic.

Typical inbound:

```text
TCP 443:

BlueBubbles HTTPS and WSS

TCP 22:

SSH from management network only, if required

TCP 80:

Optional redirect to HTTPS
```

Do not expose:

```text
PostgreSQL 5432
Redis 6379
Internal Uvicorn 8000
```

to ordinary LAN clients.

---

# Chapter 3181 — Example nftables or UFW Policy

Where UFW is used:

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing

sudo ufw allow from <management-subnet> to any port 22 proto tcp
sudo ufw allow from <client-subnet> to any port 443 proto tcp

sudo ufw enable
```

The actual subnets shall be documented.

Do not copy placeholder subnet values into production without replacement.

---

# Chapter 3182 — Exposure Verification

From a separate LAN host:

```bash
nmap -sT -p- bluebubbles.example.internal
```

Expected open ports shall match the documented policy.

Unexpected ports shall block deployment completion.

---

# Chapter 3183 — Time Synchronisation

Accurate time is required for:

* Tokens.
* Sessions.
* Audit ordering.
* TLS.
* Announcement expiry.
* Offline-duration checks.
* Message timestamps.
* Retention.

Verify:

```bash
timedatectl status
```

The server shall use an approved NTP source.

---

# Chapter 3184 — Server Configuration File

Example path:

```text
/etc/bluebubbles/server.yaml
```

It shall contain non-secret settings only.

Example categories:

```yaml
application:
network:
database:
redis:
directory:
authentication:
tokens:
storage:
messaging:
attachments:
retention:
rate_limits:
workers:
monitoring:
logging:
features:
protocol:
```

---

# Chapter 3185 — Production Configuration Validation

Run:

```bash
sudo -u bluebubbles \
  /opt/bluebubbles/shared/venv/bin/python \
  -m bluebubbles.server.cli validate-config \
  --environment production
```

The command shall fail on:

* Missing secrets.
* Mock authentication.
* Plain HTTP client URL.
* Writable configuration by service account where prohibited.
* Missing attachment mount.
* Unsupported algorithm.
* Unsafe default token secret.
* Incompatible limits.
* Unknown keys.

---

# Chapter 3186 — Server Secret Inventory

Potential server secrets:

```text
Database password
Redis credential
LDAP bind password
Access-token signing secret or private key
Cursor-signing secret
Diagnostic archive protection key where used
Backup encryption key
```

Each secret shall have:

* Owner.
* Storage location.
* Rotation procedure.
* Backup decision.
* Access policy.

---

# Chapter 3187 — Token-Signing Secret

For HS256, use a cryptographically random secret of sufficient length.

Example generation:

```bash
openssl rand -base64 64
```

Store in:

```text
/etc/bluebubbles/secrets/token_signing_key
```

Do not pass it as a command-line argument.

---

# Chapter 3188 — Secret Rotation

Secret rotation procedures shall define:

* Preparation.
* Activation.
* Overlap where required.
* Client impact.
* Session invalidation.
* Rollback.
* Audit record.
* Backup update.

Rotating a token-signing secret may invalidate active access tokens.

Refresh-token and session policy shall determine the final user impact.

---

# Chapter 3189 — Initial Migration and Seeding

Initial setup shall:

```text
Apply schema migrations.

Create built-in roles.

Create built-in permissions.

Create role-permission mappings.

Create configuration baseline.

Create audit-chain genesis state.
```

It shall not create a universal default password.

---

# Chapter 3190 — Initial SuperAdministrator Setup

Preferred Active Directory approach:

```text
Map a dedicated AD group to SuperAdministrator.
```

Then:

```text
An authorised group member logs in.

The application synchronises the role.

The first administrative login is audited.
```

The deployment shall verify the group mapping before production use.

---

# Chapter 3191 — Local Bootstrap Administrator

Where Active Directory administration is unavailable during setup, use a protected local command.

Example:

```bash
sudo -u bluebubbles \
  /opt/bluebubbles/shared/venv/bin/python \
  -m bluebubbles.server.cli create-bootstrap-admin
```

The command shall:

* Prompt for username.
* Prompt securely for password.
* Use Argon2id.
* Create SuperAdministrator role.
* Require local privileged access.
* Refuse unsafe duplicate creation.
* Audit bootstrap creation.

---

# Chapter 3192 — Bootstrap Account Retirement

After Active Directory administration works:

* Create at least two valid SuperAdministrators.
* Test their login.
* Disable or tightly protect the local bootstrap account.
* Preserve emergency-recovery documentation.
* Audit the retirement action.

A local emergency account may remain only if required by policy.

---

# Chapter 3193 — Initial Functional Verification

After setup:

```text
1. Check public health.

2. Authenticate one administrator.

3. Authenticate two test users.

4. Create a direct conversation.

5. Send an encrypted message.

6. Verify ciphertext-only server storage.

7. Create a group.

8. Upload and download a test attachment.

9. Revoke a session.

10. Verify audit chain.

11. Check backup status.
```

Production acceptance shall not end at a successful login page.

---

# Chapter 3194 — Windows Client Build Strategy

Recommended packaging tools:

```text
PyInstaller
```

or:

```text
Nuitka
```

The selected tool shall be tested with:

* PySide6.
* cryptography.
* Secure-store integration.
* Local database libraries.
* Qt plugins.
* Theme and icon resources.

---

# Chapter 3195 — Client Build Environment

The Windows build shall occur in a controlled environment with:

* Supported Windows version.
* Tested Python version.
* Locked dependencies.
* Clean virtual environment.
* Version metadata.
* Build script.
* No developer credentials.
* No user profile data.

---

# Chapter 3196 — Client Build Command

Example conceptual command:

```powershell
python scripts\client\build_client.py `
    --version 1.0.0 `
    --configuration production
```

The build script shall:

* Clean previous output.
* Validate resources.
* Embed version.
* Include Qt plugins.
* Include trusted CA where managed.
* Produce checksums.
* Produce build report.

---

# Chapter 3197 — Client Resource Packaging

Include:

```text
Application executable
Qt platform plugins
Icons
Themes
Translations
Default managed configuration
Licence notices
Cryptographic library runtime
Local database runtime
```

Do not include:

```text
Development certificates
Private keys
Test accounts
Production passwords
Debug configuration
Source test fixtures
```

---

# Chapter 3198 — Client Production Configuration

Managed client configuration may contain:

```yaml
server:
  base_url: "https://bluebubbles.example.internal"

protocol:
  supported_versions:
    - 1

updates:
  approved_location: "\\fileserver\Software\BlueBubbles"

features:
  allow_server_address_edit: false
```

It shall not contain user credentials or private keys.

---

# Chapter 3199 — Client Certificate Trust

Preferred approaches:

```text
Install internal CA through Group Policy.

or

Install internal CA through the approved installer.
```

Bundling one server certificate for manual trust is less flexible and complicates renewal.

The client shall use the Windows certificate store where practical.

---

# Chapter 3200 — Windows Installer

Recommended installer technologies:

```text
Inno Setup
WiX Toolset
MSIX where environment supports it
```

The installer shall support:

* Per-machine or per-user installation.
* Application shortcuts.
* Upgrade detection.
* Uninstallation.
* Version display.
* Managed configuration.
* Optional internal CA installation where authorised.
* No loss of user profiles during upgrade.

---

# Chapter 3201 — Client Installation Paths

Recommended application path:

```text
C:\Program Files\BlueBubbles\
```

Recommended user-data path:

```text
%LOCALAPPDATA%\BlueBubbles\
```

Recommended logs:

```text
%LOCALAPPDATA%\BlueBubbles\Logs\
```

Secure secrets shall use Windows Credential Manager rather than ordinary files.

---

# Chapter 3202 — Client Profile Layout

Example:

```text
%LOCALAPPDATA%\BlueBubbles\
├── profiles\
│   └── <profile-uuid>\
│       ├── cache.db
│       ├── keys.dat
│       ├── transfers\
│       └── temporary\
├── logs\
├── diagnostics\
└── settings.json
```

Files shall be separated by user profile.

---

# Chapter 3203 — Client File Permissions

The installer and application shall rely on the user’s Windows profile ACLs.

Shared machine-wide directories shall not store user plaintext or private keys.

When a profile is cleared, the client shall remove:

* Local database.
* Private-key store.
* Transfer manifests.
* Prepared attachments.
* Secure-store entries.

---

# Chapter 3204 — Installer Upgrade Behaviour

An installer upgrade shall:

* Stop running client cleanly where possible.
* Replace application binaries.
* Preserve `%LOCALAPPDATA%` profiles.
* Preserve Windows Credential Manager entries.
* Preserve managed server configuration unless versioned replacement is required.
* Start the new client only after successful installation.
* Support repair or rollback according to installer technology.

---

# Chapter 3205 — Client Uninstallation

Default uninstall shall remove:

```text
Application binaries
Shortcuts
Machine-level configuration created by installer
```

It shall ask separately whether to remove:

```text
Local profiles
Drafts
Queued messages
Private keys
Cached attachments
Logs
```

The default should avoid accidental loss of unsent work.

---

# Chapter 3206 — Client Code Signing

Production client executables and installers should be code-signed where an organisational signing certificate is available.

Code signing helps users and administrators verify publisher identity.

The signing private key shall not be stored in the source repository or ordinary build script.

Version 1.0 may operate unsigned in an isolated NEA environment, but Windows warnings and deployment limitations shall be documented.

---

# Chapter 3207 — Release Directory Strategy

Server releases:

```text
/opt/bluebubbles/releases/1.0.0
/opt/bluebubbles/releases/1.0.1
```

Current symlink:

```text
/opt/bluebubbles/current
```

Upgrade process changes the symlink only after:

* Files are installed.
* Dependencies are ready.
* Configuration validates.
* Migrations succeed.
* Smoke checks pass.

---

# Chapter 3208 — Release Package Contents

Server release package shall contain:

```text
Application wheel or source package
Locked requirements
Alembic migrations
Deployment templates
CLI tools
Version metadata
Licence notices
Checksums
Release notes
```

It shall not contain production secrets or writable runtime data.

---

# Chapter 3209 — Release Checksums

Generate:

```bash
sha256sum bluebubbles-server-1.0.0.tar.gz
sha256sum BlueBubbles-Setup-1.0.0.exe
```

Publish checksums through the approved internal distribution channel.

The installation procedure shall verify them.

---

# Chapter 3210 — Upgrade Preconditions

Before upgrade:

* Review release notes.
* Confirm supported source version.
* Confirm target Python version.
* Confirm available disk space.
* Confirm attachment mount health.
* Confirm current audit integrity.
* Confirm no critical backup alert.
* Confirm database backup.
* Confirm attachment backup or snapshot.
* Notify users if downtime is required.
* Record current application and migration versions.

---

# Chapter 3211 — Upgrade Maintenance Mode

For schema or protocol changes:

```text
Enter maintenance mode.
```

Preferred mode:

```text
full_maintenance
```

for changes that make old and new application versions incompatible.

Read-only mode may be sufficient for safer backward-compatible changes.

---

# Chapter 3212 — Upgrade Procedure Overview

```text
1. Notify users.

2. Confirm backup.

3. Enter maintenance mode.

4. Stop background workers or application.

5. Install new release directory.

6. Install or update dependencies.

7. Validate configuration.

8. Apply database migrations.

9. Update current symlink.

10. Start service.

11. Verify readiness.

12. Run smoke tests.

13. Exit maintenance mode.

14. Monitor logs and health.

15. Record completion.
```

---

# Chapter 3213 — Upgrade Script

Suggested command:

```bash
sudo /opt/bluebubbles/current/deployment/scripts/upgrade_server.sh \
  /tmp/bluebubbles-server-1.0.1.tar.gz
```

The script shall:

* Use strict shell error handling.
* Verify checksum.
* Verify package version.
* Create release directory.
* Avoid overwriting prior release.
* Back up current version metadata.
* Run validation.
* Stop safely on failure.
* Produce a timestamped log.

---

# Chapter 3214 — Shell Script Safety

Deployment scripts shall begin with:

```bash
set -euo pipefail
```

They shall:

* Quote variables.
* Validate paths.
* Reject empty critical variables.
* Avoid `rm -rf` on unvalidated values.
* Use generated temporary directories.
* Clean temporary resources.
* Print safe progress.
* Never echo secrets.

---

# Chapter 3215 — Migration During Upgrade

Migrations shall run while ordinary application writes are blocked.

The script shall record:

```text
Revision before
Revision after
Migration start
Migration completion
Result
```

If migration fails:

* Do not start the new application.
* Preserve logs.
* Do not automatically retry destructive steps.
* Begin documented rollback or restore procedure.

---

# Chapter 3216 — Backward-Compatible Upgrade

Where migrations and APIs are backward compatible, a lower-downtime upgrade may be possible.

Version 1.0 should prefer:

```text
Simple controlled maintenance
```

over a complex zero-downtime process.

Correctness is more important than eliminating a short planned outage.

---

# Chapter 3217 — Client Compatibility During Upgrade

The server shall report:

```text
Minimum supported client version
Maximum supported protocol version
Current protocol version
```

Before server deployment, verify that installed clients remain compatible or have an approved update available.

---

# Chapter 3218 — Post-Upgrade Smoke Test

Required checks:

```text
Health endpoints
Administrator login
Ordinary user login
Conversation list
Send direct message
Receive message
Attachment metadata access
WebSocket connection
Session refresh
Audit append
Worker status
```

For major upgrades, also test attachment round trip and offline replay.

---

# Chapter 3219 — Upgrade Observation Period

After upgrade, monitor:

```text
Error rate
Database health
Redis health
Directory login
Outbox backlog
WebSocket disconnects
Storage use
Worker failures
Audit integrity
Client compatibility errors
```

The observation period shall be appropriate to deployment size.

---

# Chapter 3220 — Rollback Decision

Rollback may be required when:

* Service cannot reach readiness.
* Authentication fails broadly.
* Migration corrupts or hides required data.
* Messages cannot be stored or retrieved.
* Client compatibility is broken unexpectedly.
* Critical security failure appears.
* Attachment access is broken.
* Audit writer fails.

---

# Chapter 3221 — Application-Only Rollback

Application-only rollback is safe only when:

* Database schema remains compatible.
* Stored protocol formats remain compatible.
* Configuration remains compatible.
* No irreversible data migration occurred.

Procedure:

```text
Stop service.

Point current symlink to previous release.

Start service.

Verify readiness.

Run smoke tests.

Record rollback.
```

---

# Chapter 3222 — Database Rollback

Reverse Alembic downgrade shall be used only if:

* The downgrade path was implemented.
* It was tested.
* It preserves required data.
* No incompatible new records were written.

Otherwise:

```text
Restore the pre-upgrade database backup.
```

---

# Chapter 3223 — Full Rollback

Full rollback may require:

```text
Restore previous application release.

Restore PostgreSQL backup.

Restore attachment snapshot where changed.

Restore configuration version.

Start in maintenance mode.

Verify audit and data consistency.

Run smoke tests.

Return service.
```

The exact restore point shall be communicated because new post-upgrade activity may be lost.

---

# Chapter 3224 — Rollback Logging

Record:

```text
Reason
Decision time
Affected version
Backup used
Application release restored
Database revision restored
Attachment snapshot restored
Validation result
Service return time
Known data loss window
```

The rollback event shall be audited when the application becomes available.

---

# Chapter 3225 — Backup Scope

A complete BlueBubbles backup shall account for:

```text
PostgreSQL database
Attachment object storage
Temporary uploads where recovery policy requires
Server configuration
Secret files according to secure backup policy
TLS certificates where appropriate
Release metadata
Audit records
Backup-status metadata
```

Redis persistence is not required for authoritative recovery.

---

# Chapter 3226 — Backup Categories

Recommended:

```text
Database backup

Attachment backup

Configuration backup

Secret backup

Release metadata backup

Restore-test evidence
```

Each category may use a different method and retention schedule.

---

# Chapter 3227 — Recovery Objectives

The deployment shall define:

```text
Recovery Point Objective

Maximum acceptable data-loss period.

Recovery Time Objective

Maximum acceptable restoration time.
```

For an NEA demonstration environment, values may be modest but shall still be stated.

Example:

```text
RPO:

24 hours

RTO:

4 hours
```

---

# Chapter 3228 — PostgreSQL Logical Backup

Example:

```bash
sudo -u postgres pg_dump \
  --format=custom \
  --file=/var/backups/bluebubbles/db/bluebubbles-$(date -u +%Y%m%dT%H%M%SZ).dump \
  bluebubbles
```

Custom format supports selective and parallel restore options.

---

# Chapter 3229 — PostgreSQL Backup Consistency

`pg_dump` produces a transactionally consistent database snapshot.

However, attachment files are stored separately.

The backup process shall coordinate database and attachment storage to avoid mismatched references.

---

# Chapter 3230 — Attachment Backup Methods

Possible methods:

```text
Filesystem snapshot
ZFS snapshot
LVM snapshot
Storage-system snapshot
rsync into versioned backup directory
Backup application
```

Filesystem snapshots are preferred where available because they create a consistent point-in-time view efficiently.

---

# Chapter 3231 — Coordinated Backup Strategy

Simple Version 1.0 strategy:

```text
Enter short read-only maintenance mode.

↓

Pause attachment finalisation and cleanup workers.

↓

Create PostgreSQL backup.

↓

Create attachment snapshot or synchronised copy.

↓

Back up configuration metadata.

↓

Exit read-only mode.
```

This simplifies consistency.

---

# Chapter 3232 — Online Backup Alternative

A more advanced online strategy may use:

* Database backup timestamp.
* Attachment manifest records.
* Immutable attachment objects.
* Incremental object backup.
* Reconciliation report.

Version 1.0 may prefer brief read-only maintenance rather than complex online consistency.

---

# Chapter 3233 — Configuration Backup

Back up:

```text
/etc/bluebubbles/server.yaml
/etc/bluebubbles/environment
Nginx configuration
systemd unit
Firewall policy export
Mount configuration
Release version metadata
```

Secret files shall follow the separate secret-backup policy.

---

# Chapter 3234 — Secret Backup

Secrets may require encrypted offline backup.

Examples:

```text
Database password
LDAP bind password
Token-signing secret
Backup encryption key metadata
```

Secret backups shall:

* Be encrypted.
* Be access-controlled.
* Be stored separately from ordinary data backup.
* Have a documented recovery owner.
* Never be copied into NEA evidence.

---

# Chapter 3235 — TLS Backup

Back up public certificate and configuration as needed.

The private key may be backed up only through the organisation’s approved key-management process.

If the certificate can be reissued easily, private-key backup may be unnecessary.

---

# Chapter 3236 — Backup Encryption

Backups containing sensitive metadata shall be encrypted.

Possible methods:

* Encrypted backup repository.
* LUKS-encrypted backup disk.
* `restic` repository encryption.
* `borg` repository encryption.
* Encrypted storage appliance.

The encryption key shall not be stored unprotected beside the backup.

---

# Chapter 3237 — Backup Tool Selection

A suitable Version 1.0 approach may use:

```text
pg_dump for PostgreSQL

restic or borg for attachment and configuration files
```

The exact tool shall be selected based on the available environment.

The runbook shall not assume a tool that is not installed and configured.

---

# Chapter 3238 — Backup Directory Layout

Example:

```text
/var/backups/bluebubbles/
├── db/
├── manifests/
├── status/
└── temporary/
```

The actual durable backup destination should be separate from the application server.

Local staging is not a complete backup.

---

# Chapter 3239 — Backup Manifest

Each backup set shall include a manifest.

Fields:

```text
Backup ID
Started at
Completed at
Application version
Database revision
Database backup path
Attachment snapshot identifier
Configuration backup identifier
Checksums
Result
Warnings
Maintenance window
```

---

# Chapter 3240 — Backup Checksums

Calculate SHA-256 for staged backup files.

Example:

```bash
sha256sum bluebubbles-20260716.dump \
  > bluebubbles-20260716.dump.sha256
```

Checksums detect accidental corruption but do not replace encrypted authenticated backup repositories.

---

# Chapter 3241 — Backup Status Record

Backup scripts shall write a protected machine-readable status record.

Example:

```json
{
  "backup_id": "20260716T230000Z",
  "completed_at": "2026-07-16T23:08:12Z",
  "database": "success",
  "attachments": "success",
  "configuration": "success",
  "verification": "success"
}
```

The monitoring service may read this file.

---

# Chapter 3242 — Backup Scheduling

Example schedule:

```text
Database logical backup:

Daily

Attachment incremental backup:

Daily

Configuration backup:

After every change and daily

Restore test:

Monthly or before release

Pre-upgrade backup:

Every upgrade
```

The final schedule shall match the RPO.

---

# Chapter 3243 — systemd Backup Timer

A systemd timer may run the backup script.

Example service:

```ini
[Unit]
Description=BlueBubbles Backup

[Service]
Type=oneshot
User=root
ExecStart=/opt/bluebubbles/current/deployment/scripts/backup.sh
```

Example timer:

```ini
[Unit]
Description=Run BlueBubbles Backup Daily

[Timer]
OnCalendar=*-*-* 23:00:00
Persistent=true
RandomizedDelaySec=10m

[Install]
WantedBy=timers.target
```

---

# Chapter 3244 — Backup Script Privileges

The backup process may require broader read access than the application service.

It shall:

* Run under a dedicated backup account or root where necessary.
* Read PostgreSQL safely.
* Read attachment objects.
* Read configuration.
* Write only to backup staging and status paths.
* Avoid modifying application data.

---

# Chapter 3245 — Backup Failure Handling

On failure:

* Exit non-zero.
* Record failed component.
* Preserve logs.
* Do not overwrite the last known valid status as success.
* Create or update a backup alert.
* Avoid deleting the previous good backup.
* Retry according to schedule or operator action.

---

# Chapter 3246 — Backup Retention

Example:

```text
Daily backups:

14 days

Weekly backups:

8 weeks

Monthly backups:

12 months
```

For an NEA environment, a smaller schedule may be acceptable.

Retention shall consider storage capacity and recovery requirements.

---

# Chapter 3247 — Backup Pruning

Pruning shall:

* Follow configured retention.
* Never delete the only valid backup.
* Verify repository integrity first where possible.
* Produce a log.
* Update backup status.
* Avoid running concurrently with restore.

---

# Chapter 3248 — Restore Purpose

The restore procedure shall rebuild a working BlueBubbles deployment from backups.

It shall restore:

* Database.
* Attachment objects.
* Configuration.
* Required secrets.
* Application release.
* Service definitions.
* Audit chain.
* Operational state.

Redis transient state may be recreated.

---

# Chapter 3249 — Restore Preconditions

Before restore:

* Identify target restore point.
* Confirm backup integrity.
* Confirm application version.
* Confirm database revision.
* Confirm attachment snapshot.
* Confirm secret availability.
* Use an isolated environment first where possible.
* Record expected data-loss window.
* Stop ordinary access.

---

# Chapter 3250 — Restore Environment

Preferred:

```text
New clean Debian VM
```

This verifies that the backup does not depend on hidden state from the original server.

For disaster recovery, restoration may occur on replacement hardware or VM.

---

# Chapter 3251 — Database Restore

Example:

```bash
sudo -u postgres createdb \
  --owner=bluebubbles_app \
  bluebubbles_restore
```

```bash
sudo -u postgres pg_restore \
  --clean \
  --if-exists \
  --no-owner \
  --dbname=bluebubbles_restore \
  /path/to/bluebubbles-backup.dump
```

The exact role and ownership steps shall be documented.

---

# Chapter 3252 — Attachment Restore

Restore attachment objects to:

```text
/var/lib/bluebubbles/attachments
```

Then verify:

* Ownership.
* Permissions.
* Object count.
* Manifest presence.
* Random sample checksums.
* Mount identity.
* Free space.

---

# Chapter 3253 — Configuration Restore

Restore:

* Server YAML.
* Environment file.
* Secret files.
* Nginx configuration.
* systemd unit.
* Firewall configuration.
* Mount configuration.

Paths and permissions shall be revalidated rather than assumed.

---

# Chapter 3254 — Restore Version Matching

The restored application release shall support the restored database revision and encrypted data formats.

Do not automatically start the latest release against an older backup without checking migration compatibility.

Suitable process:

```text
Restore matching application version.

↓

Verify data.

↓

Perform a controlled upgrade if desired.
```

---

# Chapter 3255 — Post-Restore Validation

Required:

```text
Database connectivity
Migration revision
Attachment mount
Storage object access
Audit integrity
Configuration validation
TLS
Directory connectivity
Administrator login
Ordinary login
Message retrieval
Attachment download
WebSocket connection
Worker state
Backup-status reset
```

---

# Chapter 3256 — Restore Audit Handling

Restored audit history shall remain intact.

After restoration, create a new audit event stating:

```text
System restored from backup.
```

Include:

* Backup identifier.
* Restore time.
* Operator.
* Reason.
* Data-loss window.
* Validation result.

Do not alter historical event hashes.

---

# Chapter 3257 — Restore Outbox Handling

A restored database may contain unpublished outbox events.

Before enabling clients:

* Review event age.
* Release stale locks.
* Allow idempotent publication.
* Prevent invalid duplicate side effects.
* Monitor backlog.
* Record any discarded poison events through approved recovery procedures.

---

# Chapter 3258 — Restore Session Policy

Restored sessions may no longer be safe or current.

Recommended disaster-restore policy:

```text
Invalidate all existing sessions.
```

Require users to authenticate again.

This avoids accepting tokens issued after or around the restored snapshot inconsistently.

---

# Chapter 3259 — Restore Key Considerations

User private keys are client-held.

Server restore requires only:

* Public keys.
* Key versions.
* Revocation metadata.
* Recipient envelopes.

Clients with matching private keys should decrypt restored historical content.

If server public-key history is missing or corrupted, historical verification may fail.

---

# Chapter 3260 — Restore-Test Schedule

A restore test shall run:

* Before Version 1.0 release.
* After major database changes.
* After backup-tool changes.
* Periodically according to operations policy.
* After storage-layout changes.

The result shall be recorded in backup monitoring.

---

# Chapter 3261 — Log Management

Operational logs may use:

* journald.
* Rotated JSON files.
* Both, where configured.

One authoritative support procedure shall be documented.

Logs shall remain sanitised.

---

# Chapter 3262 — logrotate Configuration

If file logging is used:

```text
/var/log/bluebubbles/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0640 bluebubbles bluebubbles
    sharedscripts
}
```

The application shall reopen files after rotation where required.

---

# Chapter 3263 — Log Retention

Suggested starting retention:

```text
Operational logs:

14 to 30 days

Security-related logs:

According to policy

Audit events:

Separate database retention policy

Diagnostic packages:

Short expiry
```

Audit events shall not be treated as ordinary rotating logs.

---

# Chapter 3264 — Disk Monitoring

Monitor:

```text
Root filesystem
PostgreSQL filesystem
Attachment filesystem
Backup staging
Log filesystem
Export directory
```

Warnings shall occur before applications fail.

---

# Chapter 3265 — Certificate Renewal Runbook

Steps:

```text
1. Review expiry warning.

2. Request or generate replacement certificate.

3. Verify hostname and chain.

4. Install new certificate and private key.

5. Validate permissions.

6. Run nginx -t.

7. Reload Nginx.

8. Test HTTPS and WSS.

9. Confirm clients trust the new certificate.

10. Record renewal.
```

---

# Chapter 3266 — Nginx Reload

Use:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

Do not restart Nginx with an invalid configuration.

A reload should preserve active connections where possible.

---

# Chapter 3267 — Application Restart Runbook

Before restart:

* Check active maintenance state.
* Check workers.
* Check active uploads.
* Notify users if needed.
* Confirm drafts are client-side.
* Confirm database health.

Restart:

```bash
sudo systemctl restart bluebubbles
```

Then verify readiness and WebSocket recovery.

---

# Chapter 3268 — Planned Server Reboot

Procedure:

```text
Notify users.

↓

Check backups.

↓

Enter maintenance mode if required.

↓

Stop BlueBubbles.

↓

Reboot server.

↓

Verify mounts.

↓

Verify PostgreSQL and Redis.

↓

Verify BlueBubbles readiness.

↓

Verify Nginx.

↓

Exit maintenance.

↓

Run smoke test.
```

---

# Chapter 3269 — PostgreSQL Unavailable Runbook

Symptoms:

* Readiness failure.
* Login or messaging failure.
* Database health alert.
* Transaction errors.

Checks:

```bash
sudo systemctl status postgresql
sudo journalctl -u postgresql
sudo -u postgres pg_isready
df -h
```

Recovery shall focus on:

* Service state.
* Disk capacity.
* Connection limits.
* Corruption indicators.
* Recent configuration changes.

Do not initialise a new empty database over the existing one.

---

# Chapter 3270 — Redis Unavailable Runbook

Symptoms:

* Presence unavailable.
* Typing unavailable.
* Rate-limit degradation.
* Pub/Sub delay.
* Redis health alert.

Checks:

```bash
sudo systemctl status redis-server
redis-cli ping
sudo journalctl -u redis-server
df -h
```

PostgreSQL messaging records shall remain intact.

Restarting Redis should not require database restoration.

---

# Chapter 3271 — Active Directory Unavailable Runbook

Symptoms:

* New logins fail.
* Existing sessions may continue according to policy.
* Directory health degraded.
* Directory sync fails.

Checks:

```text
DNS
Network route
LDAPS port
Certificate trust
Directory service account
Directory server status
```

The application shall not automatically switch every user to insecure local authentication.

---

# Chapter 3272 — Attachment Storage Full Runbook

Symptoms:

* Upload initialisation rejected.
* Storage critical alert.
* Attachment health unavailable.
* Disk threshold exceeded.

Actions:

```text
Pause new uploads.

Confirm actual mount.

Review orphaned uploads.

Run safe cleanup.

Expand volume or free approved space.

Verify filesystem.

Resume attachment capability.
```

Do not delete arbitrary attachment objects manually without database reconciliation.

---

# Chapter 3273 — Attachment Storage Missing Runbook

Symptoms:

* Mount path exists but expected device is absent.
* Readiness or attachment health fails.
* Root filesystem usage grows unexpectedly.

Actions:

```text
Stop BlueBubbles if unsafe fallback writing occurred.

Verify findmnt.

Verify /etc/fstab.

Verify device availability.

Remount.

Validate ownership.

Run storage reconciliation.

Restart or restore capability.
```

---

# Chapter 3274 — Outbox Backlog Runbook

Symptoms:

* Delayed realtime events.
* Increasing unpublished count.
* Oldest event age warning.
* Worker failure.

Checks:

* Redis or event publisher state.
* Worker status.
* Poison event.
* Database locks.
* Connection errors.
* Retry schedule.

Durable messages remain in PostgreSQL even if notifications are delayed.

---

# Chapter 3275 — Audit Integrity Failure Runbook

Immediate actions:

```text
Do not alter audit rows.

Preserve database and logs.

Create database backup or snapshot.

Restrict high-risk administrative changes if required.

Run range verification.

Identify first failed sequence.

Review database privileges.

Review recent restoration or migration.

Escalate.
```

Do not attempt automatic hash recalculation to hide the failure.

---

# Chapter 3276 — Repeated Authentication Failure Runbook

Review:

* Alert source.
* Username enumeration risk.
* Source IP.
* Affected users.
* Directory state.
* Rate-limit effectiveness.
* Possible misconfigured client.
* Possible attack.

Do not reveal whether an account exists to unauthenticated sources.

---

# Chapter 3277 — Refresh-Token Reuse Runbook

Actions:

```text
Confirm alert.

Review affected user and session.

Revoke affected session.

Consider revoking all user sessions.

Contact user through approved method.

Review device loss or compromise.

Review related IPs and audit events.

Require reauthentication.

Document resolution.
```

---

# Chapter 3278 — Worker Failure Runbook

For a failed worker:

* Identify worker.
* Review last error code.
* Check dependency health.
* Confirm duplicate run is not active.
* Correct underlying issue.
* Run manually if permitted.
* Confirm success.
* Resolve alert.

Do not repeatedly press `Run now` without understanding a destructive failure.

---

# Chapter 3279 — Backup Failure Runbook

Checks:

```text
Backup destination availability
Credentials
Free space
Database connectivity
Snapshot support
Encryption repository
Lock files
Previous incomplete job
```

Actions:

* Preserve last valid backup.
* Correct failure.
* Run backup manually.
* Verify checksum.
* Update status.
* Resolve alert only after success.

---

# Chapter 3280 — Client Cannot Connect Runbook

Client-side checks:

```text
LAN connectivity
DNS resolution
HTTPS URL
Certificate trust
System clock
Server health
Firewall
Proxy or VPN interference
```

Server-side checks:

```text
Nginx
BlueBubbles readiness
TLS certificate
Firewall
DNS record
```

The client diagnostic package shall exclude credentials.

---

# Chapter 3281 — Client Cannot Decrypt Historical Message

Possible causes:

* Missing old private key.
* Wrong local profile.
* Corrupted key store.
* Key version mismatch.
* Modified ciphertext.
* Missing recipient envelope.

Recovery:

* Confirm correct user profile.
* Check key version.
* Restore encrypted key backup if supported.
* Re-fetch envelope.
* Verify signature.
* Preserve evidence.

The server cannot recreate a lost private key.

---

# Chapter 3282 — Client Local Database Corruption Runbook

Actions:

```text
Stop client writes.

Create protected copy.

Run integrity check.

Preserve drafts and queue where recoverable.

Rebuild server-derived cache.

Restore local backup where available.

Reimport keys if required.

Require login.

Verify queue and drafts.
```

Do not delete the database immediately before preserving evidence and unsent work.

---

# Chapter 3283 — Emergency Administrator Recovery

Use only when normal administration is unavailable.

Example command:

```bash
sudo -u bluebubbles \
  /opt/bluebubbles/shared/venv/bin/python \
  -m bluebubbles.server.cli emergency-admin-recovery
```

Capabilities may include:

* List SuperAdministrators.
* Enable one account.
* Restore one role.
* Invalidate all sessions.
* Validate directory mapping.
* Enter maintenance mode.

---

# Chapter 3284 — Emergency Recovery Controls

The recovery command shall:

* Require local root or equivalent access.
* Require explicit confirmation.
* Show target account clearly.
* Prevent accidental broad changes.
* Write protected recovery log.
* Append audit event if possible.
* Never print password hashes or private keys.

---

# Chapter 3285 — Emergency Session Revocation

Command:

```bash
sudo -u bluebubbles \
  /opt/bluebubbles/shared/venv/bin/python \
  -m bluebubbles.server.cli revoke-all-sessions \
  --reason "Emergency security response"
```

The command shall:

* Invalidate sessions transactionally.
* Record count.
* Append audit or recovery record.
* Not expose token hashes.
* Require confirmation.

---

# Chapter 3286 — Emergency Maintenance Mode

Where the application API is unavailable, an offline command may set maintenance state directly through an approved database operation.

It shall:

* Validate database schema.
* Record reason.
* Record operator.
* Avoid modifying unrelated state.
* Create a recovery record.
* Require later reconciliation.

---

# Chapter 3287 — Database Corruption Response

If PostgreSQL reports corruption:

* Stop application writes.
* Preserve server state.
* Do not repeatedly restart.
* Collect PostgreSQL logs.
* Check hardware and filesystem.
* Use PostgreSQL recovery guidance.
* Restore from known good backup if necessary.
* Verify audit and attachments after restore.

Improvised table-level deletion is not acceptable.

---

# Chapter 3288 — Attachment Reconciliation Tool

A maintenance command may compare:

```text
Database attachment records

against

Filesystem attachment objects
```

It shall identify:

* Database record missing file.
* File missing database record.
* Missing chunk.
* Extra chunk.
* Size mismatch.
* Hash mismatch.
* Orphan upload.
* Invalid path.

---

# Chapter 3289 — Reconciliation Safety

Default reconciliation mode shall be read-only.

Example:

```bash
python -m bluebubbles.server.cli reconcile-storage --report-only
```

Deletion or repair shall require:

* Explicit mode.
* Backup.
* Confirmation.
* Audit reason.
* Generated report.

---

# Chapter 3290 — Storage Repair Limits

The server cannot reconstruct:

* Missing encrypted chunks.
* Missing message content keys.
* Missing recipient envelopes.
* Lost client private keys.

The repair tool shall report unrecoverable state honestly.

It shall not generate replacement ciphertext pretending to be original content.

---

# Chapter 3291 — Audit Verification Command

Example:

```bash
sudo -u bluebubbles \
  /opt/bluebubbles/shared/venv/bin/python \
  -m bluebubbles.server.cli verify-audit \
  --full
```

Output shall include:

* Range.
* Count.
* Duration.
* Valid or invalid result.
* First failed sequence.
* Safe failure code.

---

# Chapter 3292 — Configuration Rollback Runbook

Procedure:

```text
Review configuration history.

Select previous valid version.

Validate against current software.

Create backup.

Require reason.

Apply rollback as new version.

Restart if required.

Run health checks.

Monitor clients.
```

Do not edit the configuration-history table manually.

---

# Chapter 3293 — Secret Compromise Response

If a server secret is compromised:

```text
Identify secret and affected scope.

Enter maintenance if required.

Rotate secret.

Invalidate affected sessions or credentials.

Update protected backups.

Restart affected services.

Review logs and audit.

Notify authorised personnel.

Document incident.
```

The response differs by secret type.

---

# Chapter 3294 — Database Password Rotation

Procedure:

```text
Create new password.

Update protected secret file.

Update PostgreSQL role password.

Restart or reload application safely.

Verify database connectivity.

Remove old secret from backup staging and temporary locations.

Audit rotation without recording password.
```

Order may use a temporary overlap strategy if supported.

---

# Chapter 3295 — LDAP Bind Password Rotation

Procedure:

* Change directory account password.
* Update secret file securely.
* Restart or reload BlueBubbles.
* Run directory health check.
* Confirm user login.
* Remove old temporary records.
* Audit the rotation.

The service-account password shall not be exposed through command history.

---

# Chapter 3296 — Token-Signing Secret Rotation

Simplified Version 1.0 procedure:

```text
Enter maintenance.

Rotate signing secret.

Invalidate all sessions.

Restart application.

Require all users to log in again.

Verify token issuance.

Exit maintenance.
```

A multi-key overlap system may reduce disruption but adds complexity.

---

# Chapter 3297 — Client Key Loss Response

When a user loses their only private keys:

* Revoke old public keys for new use.
* Generate new client identity keys.
* Register new versions.
* Warn the user that historical content may be unreadable.
* Preserve server ciphertext.
* Notify contacts of key change where designed.
* Audit administrative assistance.

No administrator shall claim to recover lost plaintext without an actual encrypted backup.

---

# Chapter 3298 — User Offboarding Runbook

Process may include:

```text
Disable directory account.

Synchronise BlueBubbles account.

Disable application account.

Revoke sessions.

Remove future group memberships where policy requires.

Revoke active public keys for future use.

Handle data retention or anonymisation.

Preserve mandatory audit events.

Record reason.
```

Previously decrypted content on offline devices cannot be remotely erased immediately.

---

# Chapter 3299 — Server Decommissioning

Before decommissioning:

* Notify users.
* Stop new writes.
* Create final backup.
* Verify restore.
* Export required audit records.
* Decide retention.
* Revoke certificates.
* Remove DNS.
* Disable directory service account.
* Securely remove secret files.
* Securely dispose of storage according to policy.
* Document completion.

---

# Chapter 3300 — Secure Data Removal

Logical deletion does not guarantee physical erasure on all storage.

For decommissioning:

* Use encrypted storage and destroy encryption keys where appropriate.
* Follow storage-device sanitisation policy.
* Remove backups according to retention.
* Remove VM snapshots.
* Remove cloud or hypervisor copies.
* Remove client distribution secrets.

---

# Chapter 3301 — Operations Checklist: Daily

Suggested daily checks:

```text
Dashboard health
Open critical alerts
Backup status
Storage thresholds
Database availability
Outbox backlog
Failed workers
Certificate warnings
```

Small environments may automate these checks and review alerts rather than perform a manual checklist every day.

---

# Chapter 3302 — Operations Checklist: Weekly

Suggested weekly tasks:

```text
Review high alerts
Review failed logins
Review disk growth
Review worker history
Review backup checksums
Review expired exports and diagnostics
Review disabled or stale accounts
Run recent audit verification
```

---

# Chapter 3303 — Operations Checklist: Monthly

Suggested monthly tasks:

```text
Run full audit verification
Perform restore test or scheduled rehearsal
Review dependency updates
Review certificate expiry
Review administrator accounts
Review retention jobs
Review storage reconciliation report
Review operational runbooks
```

---

# Chapter 3304 — Operations Checklist: Before Upgrade

```text
Review release notes
Review compatibility
Confirm backup
Verify audit
Confirm free space
Check attachment mount
Notify users
Test upgrade in staging
Confirm rollback
Record current versions
```

---

# Chapter 3305 — Operations Checklist: After Upgrade

```text
Verify service version
Verify migration revision
Verify health
Verify login
Verify messaging
Verify attachment
Verify WebSocket
Verify audit append
Verify workers
Monitor alerts
Update documentation
```

---

# Chapter 3306 — Monitoring Without External Platforms

Version 1.0 shall remain operable using:

* Administrative dashboard.
* Health endpoints.
* journald or local logs.
* Security alerts.
* Backup status.
* Worker state.
* Diagnostic commands.

Prometheus, Grafana or an external SIEM may be added later but shall not be required for basic operation.

---

# Chapter 3307 — External Monitoring Integration

Where Prometheus is used:

* Bind metrics to management interface or loopback.
* Avoid sensitive labels.
* Protect endpoint.
* Monitor component health, latency and capacity.
* Do not export message content or usernames as labels.

Grafana dashboards may visualise aggregate metrics.

---

# Chapter 3308 — Operational Documentation Set

Required documents:

```text
Server installation guide
Client installation guide
Configuration reference
TLS guide
Active Directory guide
Backup guide
Restore guide
Upgrade guide
Rollback guide
Administrator guide
Operational runbooks
Emergency recovery guide
Decommissioning guide
```

---

# Chapter 3309 — Command Accuracy Requirement

Every command in deployment documentation shall be:

* Tested.
* Appropriate for the supported Debian version.
* Written with required privileges.
* Clear about placeholder replacement.
* Safe against accidental destructive use.
* Consistent with actual paths.

Commands shall not mix incompatible package versions or service names.

---

# Chapter 3310 — Placeholder Formatting

Placeholders shall be visibly marked.

Examples:

```text
<server-hostname>
<management-subnet>
<database-password>
<attachment-disk-id>
```

Documentation shall state:

```text
Replace every placeholder before execution.
```

Real secrets shall never be included as examples.

---

# Chapter 3311 — Destructive Command Warnings

Commands that can destroy data shall include a warning immediately before them.

Examples:

```text
mkfs
DROP DATABASE
rm -rf
restore --clean
disk repartitioning
secret removal
```

The documentation shall require the operator to verify the target.

---

# Chapter 3312 — Installation Automation

A server installation script may automate repeatable steps.

It shall not:

* Invent secrets silently without recording their storage location.
* Format disks automatically by default.
* Disable the firewall broadly.
* Expose PostgreSQL or Redis.
* Skip TLS validation.
* Create default credentials.
* Ignore failed commands.

---

# Chapter 3313 — Installation Script Modes

Possible modes:

```text
--check

Validate prerequisites without changes.

--install

Install application files and service.

--configure

Install configuration templates.

--verify

Run post-installation checks.

--uninstall

Remove application binaries without deleting data by default.
```

---

# Chapter 3314 — Idempotent Installation

Repeated execution should:

* Detect existing service account.
* Detect existing directories.
* Preserve configuration.
* Avoid regenerating secrets unexpectedly.
* Avoid recreating database destructively.
* Upgrade only when explicitly requested.
* Report existing state.

---

# Chapter 3315 — Server Uninstallation

Default server uninstall shall remove:

```text
Application release files
systemd unit
Optional Nginx site configuration
```

It shall preserve unless explicitly requested:

```text
PostgreSQL database
Attachment storage
Backups
Configuration
Secrets
Logs
```

Data destruction shall require a separate confirmed command.

---

# Chapter 3316 — Production Readiness Checklist

Before production use:

```text
Production configuration validated
TLS trusted
Nginx tested
Firewall tested
PostgreSQL loopback-only
Redis loopback-only
Service account restricted
Attachment mount guarded
Backup completed
Restore tested
Initial administrators verified
Mock providers disabled
Debug routes disabled
Audit verification valid
Client installer tested
Known limitations communicated
```

---

# Chapter 3317 — Deployment Acceptance Tests

Required:

```text
Fresh Debian install succeeds
Fresh PostgreSQL migration succeeds
Redis remains private
Nginx proxies REST
Nginx proxies WebSocket
TLS validation succeeds
Invalid certificate fails
systemd starts on boot
Attachment mount requirement works
Firewall exposes only approved ports
Administrator bootstrap succeeds
Windows installer succeeds
```

---

# Chapter 3318 — Upgrade Acceptance Tests

Required:

```text
Pre-upgrade backup succeeds
Upgrade script verifies package
Migration succeeds
Application starts
Client remains compatible
Messages remain readable
Attachments remain downloadable
Audit chain remains valid
Workers resume
Rollback rehearsal succeeds
```

---

# Chapter 3319 — Backup Acceptance Tests

Required:

```text
Database backup created
Attachment backup created
Configuration backup created
Checksums recorded
Status file updated
Failure returns non-zero
Old valid backup preserved
Retention prunes correctly
Backup alert created on failure
```

---

# Chapter 3320 — Restore Acceptance Tests

Required:

```text
Restore to clean VM succeeds
Correct application version starts
Database revision correct
Users restored
Conversations restored
Ciphertext messages restored
Attachments restored
Clients decrypt historical data
Audit verification passes
Existing sessions invalidated
Smoke test passes
```

---

# Chapter 3321 — Operational Runbook Acceptance

An administrator unfamiliar with the development environment shall be able to follow runbooks for:

```text
Server restart
Database outage
Redis outage
Directory outage
Storage full
Certificate renewal
Backup failure
Restore
User disable
Emergency administrator recovery
```

Undocumented assumptions shall be corrected.

---

# Chapter 3322 — Version 1.0 Deployment Scope

Version 1.0 shall provide:

```text
Debian server deployment
PostgreSQL
Redis
Nginx
TLS
systemd
Dedicated service account
Restricted filesystem layout
Separate attachment storage support
Active Directory connectivity
Windows client build
Windows installer
Initial administrator setup
Configuration validation
Database migrations
Backup scripts
Backup monitoring
Restore procedure
Upgrade script
Rollback procedure
Maintenance mode
Emergency recovery commands
Operational runbooks
```

---

# Chapter 3323 — Deferred Deployment Features

The following may be deferred:

```text
Kubernetes
Docker Swarm
Multi-node FastAPI cluster
PostgreSQL automatic failover
Redis cluster
Object-storage attachment backend
Cloud deployment
Automatic public certificate issuance
Mobile-device management deployment
Automatic client updater
Hardware security module
Zero-downtime schema migration
Multi-region backup
```

These shall not be required for Version 1.0 completion.

---

# Chapter 3324 — Deployment and Operations Summary

BlueBubbles shall be deployed on a dedicated Debian server using PostgreSQL, Redis, Nginx and systemd.

The application shall run under a restricted non-login service account.

PostgreSQL, Redis and the internal Uvicorn port shall remain inaccessible to ordinary LAN clients.

Nginx shall terminate trusted TLS and proxy HTTPS and WebSocket traffic.

Attachment data shall use generated paths on a monitored dedicated volume.

The service shall refuse unsafe operation when the expected attachment mount is absent.

Production configuration and secrets shall remain outside the source repository.

Active Directory connectivity shall use LDAPS or StartTLS with validated certificates and a least-privileged service account where required.

The Windows client shall be built reproducibly, installed without a separate Python runtime and preserve encrypted user profiles during upgrades.

No default administrative password shall be shipped.

Every upgrade shall require compatibility review, a verified backup, controlled migration, smoke testing and a rollback plan.

A complete backup shall include PostgreSQL, encrypted attachment objects, configuration and required protected secrets.

Backups shall be considered valid only after successful restore testing.

Disaster restoration shall use a compatible application version, verify the audit chain and normally invalidate restored sessions.

Operational runbooks shall cover database, Redis, directory, storage, certificate, backup, audit, worker, client and administrator failures.

Emergency recovery shall require local privileged access, preserve evidence and never provide a route to decrypt user content.

The production deployment shall not be accepted until installation, upgrade, rollback, backup, restore, firewall, TLS, systemd and client packaging tests pass.

---

# End of Part 29

Part 30 will complete the specification with the final coding-AI execution contract, including:

* Mandatory implementation rules.
* Prohibited shortcuts.
* Required outputs.
* File-generation sequence.
* Verification after each stage.
* Security invariants.
* Database invariants.
* Client and server completion checks.
* Final acceptance checklist.
* Required documentation.
* Final project-delivery format.
* Complete Version 1.0 definition.

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
