# Task 22 — Full testing

> This is a self-contained implementation task split from the complete BlueBubbles Version 1.0 specification. Source requirements below are reproduced verbatim, not summarised. Where a repeated project-wide rule conflicts with a task-local choice, the project-wide rule wins.

## Required predecessors

Task 01, Task 02, Task 03, Task 04, Task 05, Task 06, Task 07, Task 08, Task 09, Task 10, Task 11, Task 12, Task 13, Task 14, Task 15, Task 16, Task 17, Task 18, Task 19, Task 20, Task 21.

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

## Task-specific authoritative source: Part 18

# Part 18 — Testing Strategy and Quality Assurance

---

# Chapter 1132 — Testing Subsystem Purpose

The testing subsystem defines how BlueBubbles shall be verified before release.

It shall ensure that:

* Individual classes behave correctly.
* Components integrate correctly.
* Complete user workflows succeed.
* Security boundaries are enforced.
* Encryption and integrity checks work correctly.
* Performance targets are measured.
* Failures recover safely.
* Previously fixed defects do not return.
* Stakeholder requirements are demonstrated with evidence.
* The final system is suitable for evaluation.

Testing shall be planned alongside implementation rather than added only after development is complete.

---

# Chapter 1133 — Testing Principles

BlueBubbles testing shall follow these principles:

```text
Test behaviour, not implementation details.

Test security-critical paths thoroughly.

Use isolated and repeatable environments.

Keep tests deterministic.

Avoid dependence on the public Internet.

Use production-like infrastructure for integration tests.

Mock only external boundaries when appropriate.

Test both successful and unsuccessful paths.

Preserve evidence of results.

Automate repeatable checks.

Use manual testing where human judgement is required.
```

---

# Chapter 1134 — Testing Layers

The test strategy shall use several layers.

```text
Static analysis

↓

Unit tests

↓

Component tests

↓

Integration tests

↓

End-to-end tests

↓

Security tests

↓

Performance tests

↓

Manual acceptance tests

↓

Stakeholder evaluation
```

Each layer detects different types of defects.

No single layer is sufficient on its own.

---

# Chapter 1135 — Test Directory Structure

Recommended project structure:

```text
tests/
│
├── unit/
│   ├── client/
│   ├── server/
│   ├── security/
│   ├── storage/
│   └── shared/
│
├── integration/
│   ├── api/
│   ├── database/
│   ├── redis/
│   ├── ldap/
│   ├── websocket/
│   └── file_transfer/
│
├── end_to_end/
│   ├── authentication/
│   ├── messaging/
│   ├── groups/
│   ├── attachments/
│   └── administration/
│
├── performance/
│   ├── server/
│   ├── client/
│   ├── messaging/
│   └── file_transfer/
│
├── security/
│   ├── authentication/
│   ├── authorisation/
│   ├── cryptography/
│   ├── storage/
│   └── input_validation/
│
├── fixtures/
├── factories/
├── helpers/
└── conftest.py
```

Tests shall be organised by purpose and subsystem.

---

# Chapter 1136 — Test Frameworks

Recommended Python testing tools:

```text
pytest
pytest-asyncio
pytest-cov
pytest-mock
Hypothesis
httpx
FastAPI TestClient where appropriate
Playwright only if a browser interface is later added
```

PySide6 GUI tests may use:

```text
pytest-qt
Qt Test
```

Performance testing may use:

```text
pytest-benchmark
Locust
Custom timing scripts
```

---

# Chapter 1137 — Static Analysis

Static analysis shall detect defects before tests run.

Recommended tools:

```text
Ruff
mypy
Bandit
Black
isort where not replaced by Ruff
```

Checks shall include:

* Syntax.
* Formatting.
* Import consistency.
* Type errors.
* Unused code.
* Common security mistakes.
* Suspicious exception handling.
* Accidental hard-coded secrets.

---

# Chapter 1138 — Type Checking

The project shall use type hints throughout important application code.

`mypy` or an equivalent checker shall verify:

```text
Service interfaces
Repository interfaces
DTOs
Domain models
Worker results
Cryptographic functions
Configuration models
ViewModel properties
```

Security-sensitive values such as keys and tokens should use distinct types or wrapper classes where practical.

---

# Chapter 1139 — Formatting and Linting

Code formatting shall be automated.

Recommended commands:

```text
ruff check .
ruff format --check .
mypy .
```

Before committing code, developers should run:

```text
ruff check . --fix
ruff format .
```

The continuous-integration pipeline shall reject incorrectly formatted or lint-failing code.

---

# Chapter 1140 — Security Static Analysis

Bandit or similar tooling shall check for:

```text
Use of insecure random generators
Unsafe subprocess execution
Hard-coded passwords
Weak cryptographic algorithms
Unsafe temporary-file creation
Shell injection risks
Insecure deserialisation
Broad exception suppression
```

Automated security analysis supplements manual review.

It does not prove the application is secure.

---

# Chapter 1141 — Secret Scanning

The repository shall be scanned for accidental secrets.

Possible tools:

```text
Gitleaks
TruffleHog
GitHub secret scanning where available
```

The scan shall check for:

```text
Database passwords
Token-signing secrets
LDAP passwords
Private keys
Certificates containing private keys
Access tokens
Refresh tokens
Test production credentials
```

Test fixtures shall use clearly fake values.

---

# Chapter 1142 — Unit Testing Purpose

Unit tests verify one class, function or small behaviour in isolation.

Typical unit-test targets:

```text
Input validators
DTO validation
Permission rules
Username normalisation
Error mapping
Encryption wrappers
Checksum functions
Cache eviction
Retry logic
ViewModel state transitions
```

Unit tests should run quickly and require no external services.

---

# Chapter 1143 — Unit-Test Isolation

Unit tests shall replace external dependencies with:

```text
Mocks
Fakes
In-memory repositories
Temporary files
Deterministic clocks
Test key pairs
```

A unit test should not require:

```text
Real PostgreSQL
Real Redis
Real Active Directory
Real network access
Production certificates
```

---

# Chapter 1144 — Unit-Test Naming

Test names shall describe:

```text
Condition
Action
Expected result
```

Example:

```python
def test_normalise_username_removes_domain_prefix() -> None:
    ...
```

Example:

```python
async def test_send_message_rejects_removed_group_member() -> None:
    ...
```

Names shall make failures understandable without opening the test code.

---

# Chapter 1145 — Arrange, Act, Assert

Unit tests should use the structure:

```text
Arrange

Create inputs, mocks and expected state.

Act

Execute the behaviour being tested.

Assert

Verify the expected result.
```

Example:

```python
def test_password_hasher_rejects_invalid_password(
    password_hasher: PasswordHasher,
) -> None:
    password_hash = password_hasher.hash_password("CorrectPassword123")

    result = password_hasher.verify_password(
        "IncorrectPassword123",
        password_hash,
    )

    assert result is False
```

---

# Chapter 1146 — Test Factories

Factories shall create valid default test objects.

Suggested factories:

```text
UserFactory
SessionFactory
ConversationFactory
MessageFactory
AttachmentFactory
AuditEventFactory
GroupMembershipFactory
ConfigurationFactory
```

Tests may override only the fields relevant to their scenario.

---

# Chapter 1147 — Factory Example

```python
class UserFactory:
    """Creates valid users for automated tests."""

    @staticmethod
    def create(
        *,
        user_id: UUID | None = None,
        username: str = "employee1",
        role: RoleName = RoleName.EMPLOYEE,
        is_enabled: bool = True,
    ) -> User:
        return User(
            id=user_id or uuid4(),
            username=username,
            role=role,
            is_enabled=is_enabled,
        )
```

Factories shall not hide important test conditions.

---

# Chapter 1148 — Test Fixtures

Fixtures shall provide reusable setup.

Examples:

```text
Application settings
Temporary directory
Test database session
Test Redis client
Authenticated user
Administrator user
Test API client
WebSocket client
Mock authentication provider
Encryption key pair
```

Fixture scope shall be chosen carefully to avoid state leaking between tests.

---

# Chapter 1149 — Fixture Scope

Recommended use:

```text
Function scope

For database transactions, users, messages and most mutable objects.

Module scope

For expensive but immutable test setup.

Session scope

For containers or shared infrastructure only when safely reset.
```

Tests shall not depend on execution order.

---

# Chapter 1150 — Deterministic Time

Tests involving time shall use a controllable clock.

Suitable scenarios:

```text
Token expiry
Edit windows
Upload expiry
Retention
Retry scheduling
Presence timeout
Session cleanup
Announcement expiry
```

The application should depend on a clock abstraction where time-sensitive logic is complex.

---

# Chapter 1151 — Clock Interface

```python
class Clock:
    """Provides the current application time."""

    def now(self) -> datetime:
        ...
```

Production implementation:

```python
class SystemClock(Clock):
    def now(self) -> datetime:
        return datetime.now(timezone.utc)
```

Testing implementation:

```python
class FakeClock(Clock):
    def advance(self, duration: timedelta) -> None:
        ...
```

---

# Chapter 1152 — Randomness in Tests

Production code shall use secure randomness.

Tests may use controlled random inputs only where deterministic output is needed.

Cryptographic tests shall not replace secure production randomness globally.

Instead, cryptographic classes may accept an injectable random-byte provider in isolated tests where necessary.

---

# Chapter 1153 — Cryptographic Unit Tests

Cryptographic tests shall verify:

```text
Key generation creates valid key sizes
Encryption and decryption produce identical plaintext
Different nonces produce different ciphertext
Modified ciphertext fails verification
Modified authentication tag fails verification
Modified signature fails verification
Wrong recipient key cannot decrypt
Canonical serialisation is deterministic
Key rotation preserves intended old-message access
Private keys are encrypted at rest
```

Tests shall use official library APIs only.

---

# Chapter 1154 — Cryptographic Test Limitations

Passing encryption tests does not prove a cryptographic design is secure.

Tests can demonstrate:

* Correct use of selected APIs.
* Correct failure behaviour.
* Correct key and nonce handling.
* Correct envelope construction.

The cryptographic architecture should still be reviewed manually against library documentation and accepted practices.

---

# Chapter 1155 — Property-Based Testing

Property-based testing generates many inputs automatically.

Hypothesis may be used for:

```text
Username normalisation
Filename sanitisation
Pagination
Serialisation
Cache-size calculations
Message ordering
State-machine transitions
Input length boundaries
```

This is especially useful for edge cases developers may not think of manually.

---

# Chapter 1156 — Filename Property Tests

Properties may include:

```text
Sanitised names contain no path separators.

Sanitised names contain no null bytes.

Sanitised names remain within length limits.

Sanitising the same name twice gives the same result.

The resulting path remains inside the configured storage root.
```

---

# Chapter 1157 — Serialisation Property Tests

Canonical serialisation shall satisfy:

```text
Same data always produces identical bytes.

Dictionary insertion order does not change output.

UTC-equivalent timestamps serialise identically.

Null values are represented consistently.

Changing a signed field changes the serialised output.
```

These tests are critical for signatures and audit hashes.

---

# Chapter 1158 — State-Machine Property Tests

Property-based tests may verify that invalid transitions are rejected.

Applicable state machines:

```text
File transfer
Offline action
Upload session
Security alert
Data export job
Deletion request
Worker state
```

Example property:

```text
No terminal state may transition back to RUNNING.
```

---

# Chapter 1159 — Component Testing

Component tests verify a complete subsystem with its immediate dependencies.

Examples:

```text
AuthenticationService with fake provider and real repositories
MessagingService with test database
AttachmentService with temporary filesystem
LocalSearchService with temporary SQLite database
OfflineQueueService with fake API client
```

Component tests sit between unit and full integration tests.

---

# Chapter 1160 — Integration Testing Purpose

Integration tests verify that real components work together.

They shall test:

```text
FastAPI and PostgreSQL
FastAPI and Redis
Server and filesystem storage
Server and LDAP test provider
REST routes and services
WebSocket manager and event publisher
Client API service and server
SQLAlchemy models and migrations
```

Mocks shall be reduced at this layer.

---

# Chapter 1161 — Integration Infrastructure

Recommended test services:

```text
PostgreSQL container
Redis container
Temporary attachment volume
Optional LDAP test container
Test certificate authority
FastAPI test server
```

Infrastructure may be started using:

```text
Docker Compose
Testcontainers
Dedicated local test services
```

The environment shall be reproducible.

---

# Chapter 1162 — Test Database Isolation

Each integration test shall use one of:

```text
Transaction rollback
Fresh schema
Dedicated database
Truncated tables
```

Tests shall not leave data that affects later tests.

Running tests in parallel shall not cause identifier or database conflicts.

---

# Chapter 1163 — Database Migration Tests

Migration tests shall verify:

```text
Fresh database upgrades to latest version
Previous schema upgrades correctly
Required indexes exist
Required constraints exist
Audit triggers exist
Downgrade works where supported
Migration failure rolls back safely
Application detects outdated schema
```

Production migrations shall be tested before deployment.

---

# Chapter 1164 — PostgreSQL Constraint Tests

Integration tests shall verify database-level protection.

Examples:

```text
Duplicate message UUID rejected
Duplicate attachment chunk rejected
Invalid foreign key rejected
Only one active group owner where enforced
Audit update rejected
Audit deletion rejected
Null required field rejected
Message version conflict detected
```

Application validation shall not be the only protection.

---

# Chapter 1165 — Redis Integration Tests

Redis tests shall verify:

```text
Presence TTL expiry
Typing-state expiry
Rate-limit counters
Permission-cache invalidation
Pub/Sub event delivery
Namespace separation
Redis reconnect behaviour
Fallback behaviour
```

Tests shall not assume Redis stores permanent records.

---

# Chapter 1166 — LDAP Integration Tests

LDAP integration tests shall verify:

```text
Valid bind
Invalid password
Unknown user
Disabled account
Group membership retrieval
Attribute mapping
Escaped search filter
Directory timeout
TLS connection
Directory recovery
```

Most routine tests may use a mock provider.

A smaller integration suite shall use a real test LDAP service.

---

# Chapter 1167 — REST API Integration Tests

Each endpoint shall be tested for:

```text
Successful request
Missing authentication
Expired authentication
Insufficient permission
Invalid body
Missing resource
Conflict
Rate limit
Expected response schema
Safe error schema
```

OpenAPI documentation shall match the implemented response models.

---

# Chapter 1168 — WebSocket Integration Tests

Tests shall verify:

```text
Successful connection
Authentication timeout
Invalid access token
Session invalidation
Heartbeat
Message event delivery
Group event delivery
Typing indicator
Presence update
Error event
Server shutdown event
Automatic cleanup after disconnect
```

WebSocket tests shall use bounded timeouts to avoid hanging indefinitely.

---

# Chapter 1169 — End-to-End Testing Purpose

End-to-end tests verify complete workflows from the user-facing client boundary through the server and storage layers.

They shall use:

* A real server process.
* Real PostgreSQL.
* Real Redis where enabled.
* Real test client services.
* Temporary file storage.
* Test credentials.
* Real cryptographic operations.

GUI interaction may be included for selected critical workflows.

---

# Chapter 1170 — Critical End-to-End Workflows

Required workflows:

```text
Login
Open conversation
Send direct message
Receive direct message
Create group
Add member
Send group message
Remove member
Upload attachment
Download attachment
Edit message
Delete message
Mark read
Disconnect and reconnect
Logout
Administrator disables user
```

---

# Chapter 1171 — Direct Message End-to-End Test

```text
Create two test users

↓

Authenticate both clients

↓

Create direct conversation

↓

Client A encrypts and sends message

↓

Server stores ciphertext

↓

Client B receives event

↓

Client B verifies and decrypts

↓

Client B sends delivery acknowledgement

↓

Client A shows delivered state

↓

Database is checked for absence of plaintext
```

Success requires exact plaintext equality at the recipient.

---

# Chapter 1172 — Group Message End-to-End Test

```text
Create owner and members

↓

Create group

↓

Distribute public keys

↓

Owner sends encrypted group message

↓

Server validates all recipient envelopes

↓

Every active member receives their key envelope

↓

Members decrypt successfully

↓

Removed user receives no future message
```

The test shall confirm that key-envelope membership changes after removal.

---

# Chapter 1173 — Attachment End-to-End Test

```text
Create test file

↓

Calculate original SHA-256

↓

Encrypt and upload chunks

↓

Link attachment to message

↓

Recipient downloads chunks

↓

Recipient decrypts file

↓

Calculate resulting SHA-256

↓

Compare checksums
```

Success requires the hashes to match exactly.

---

# Chapter 1174 — Offline End-to-End Test

```text
Authenticate client

↓

Disconnect client network service

↓

Create outgoing message

↓

Verify message enters encrypted offline queue

↓

Restore connection

↓

Process queued message

↓

Verify one server record created

↓

Verify recipient receives message

↓

Verify queue item becomes complete
```

The message shall not be duplicated.

---

# Chapter 1175 — Restart Recovery End-to-End Test

```text
Begin incomplete upload

↓

Stop server process

↓

Restart server

↓

Reconnect client

↓

Query upload state

↓

Upload only missing chunks

↓

Complete attachment

↓

Download and verify file
```

This demonstrates resumability and durable state.

---

# Chapter 1176 — GUI Testing Purpose

GUI tests shall verify important PySide6 behaviour that cannot be covered only through ViewModel tests.

Examples:

```text
Login form validation
Navigation changes
Message rendering
Loading indicators
Error banners
Keyboard shortcuts
File drag and drop
Theme switching
Accessibility labels
Dialog confirmation
```

Most business logic shall still be tested outside the GUI.

---

# Chapter 1177 — ViewModel Testing

ViewModel tests shall verify:

```text
Initial state
Loading state
Successful state
Failure state
Signal emission
Validation
Service calls
Cancellation
Navigation
Retry actions
```

Services shall be replaced with mocks or fakes.

No real window needs to be shown for most ViewModel tests.

---

# Chapter 1178 — PySide6 Widget Tests

`pytest-qt` may be used to:

```text
Create widget
Simulate keyboard input
Click buttons
Wait for signals
Inspect visible state
Verify focus
Verify enabled and disabled controls
```

Tests shall clean up all created widgets.

---

# Chapter 1179 — GUI Snapshot Testing

Visual snapshot testing may be used cautiously for:

```text
Login page
Main layout
Chat message styles
Settings page
Error dialogs
Dark theme
High-contrast theme
```

Snapshots can become fragile.

They should support, not replace, behavioural tests.

---

# Chapter 1180 — Accessibility Testing

Manual and automated checks shall verify:

```text
Keyboard-only navigation
Focus order
Visible focus indicators
Screen-reader labels
Colour contrast
High-contrast theme
Reduced-motion behaviour
Text scaling
Errors not communicated by colour alone
```

Accessibility issues shall be recorded like functional defects.

---

# Chapter 1181 — Security Testing Purpose

Security tests shall attempt to violate the system’s trust boundaries.

They shall cover:

```text
Authentication
Authorisation
Input validation
Session handling
Cryptography
Storage
File paths
Rate limiting
Logging
Error responses
Administrative controls
```

Security tests shall include both automated checks and manual review.

---

# Chapter 1182 — Authentication Security Tests

Required tests:

```text
Invalid username and password
User enumeration resistance
Repeated login attempts
Temporary application lockout
Disabled directory account
Expired token
Modified token
Wrong token audience
Invalid session
Revoked session
Refresh-token reuse
Concurrent refresh attempts
Logout invalidation
```

---

# Chapter 1183 — Authorisation Security Tests

Required tests:

```text
Employee accesses admin endpoint
Non-member accesses conversation
Removed member retrieves new message
User edits another user’s message
Moderator removes owner
Helpdesk assigns role
User retrieves another user’s key envelope
User downloads unrelated attachment
Administrator attempts plaintext retrieval
```

Every protected resource shall be tested at both role and resource level.

---

# Chapter 1184 — Input Validation Security Tests

Test input shall include:

```text
Empty values
Maximum lengths
Values one character over limits
Invalid UUIDs
Malformed timestamps
Invalid Base64
Control characters
Unicode edge cases
LDAP filter characters
SQL-like strings
Path traversal strings
Null bytes
Oversized request bodies
Unexpected fields
```

The system shall reject invalid input safely.

---

# Chapter 1185 — Injection Testing

The test suite shall check resistance to:

```text
SQL injection
LDAP injection
Path traversal
Command injection
Header injection
Log injection
JSON structure abuse
```

Use parameterised queries and library escaping rather than custom filtering alone.

---

# Chapter 1186 — Cryptographic Security Tests

Tests shall verify:

```text
Nonce uniqueness within test sample
Wrong key cannot decrypt
Wrong additional authenticated data fails
Modified recipient list invalidates signature
Modified message ID invalidates signature
Modified attachment chunk fails authentication
Revoked key is not used
Private key never sent to server
Server database contains no plaintext
```

Randomness quality itself shall rely on the operating system and selected library.

---

# Chapter 1187 — Storage Security Tests

Tests shall verify:

```text
Attachment filename cannot determine storage path
Temporary files use safe permissions
Client cache is user-specific
Database key is not stored beside database
Clear-all deletes local key
Wrong local key cannot open sensitive cache
Export files require authentication
Expired exports are removed
Audit records cannot be updated normally
```

---

# Chapter 1188 — Logging Security Tests

Tests shall search logs for:

```text
Test password
Test access token
Test refresh token
Test private key
Test plaintext message
Test plaintext attachment content
Test database password
Test LDAP password
```

The test shall fail if any sensitive marker appears.

---

# Chapter 1189 — Dependency Vulnerability Scanning

Dependencies shall be checked for known vulnerabilities.

Possible tools:

```text
pip-audit
Safety
Dependabot where available
```

The scan shall run regularly and before release.

A vulnerability report shall be reviewed rather than ignored automatically.

---

# Chapter 1190 — Performance Testing Purpose

Performance tests shall confirm that BlueBubbles remains responsive under expected workloads.

They shall measure:

```text
Latency
Throughput
Memory usage
CPU usage
Disk usage
Connection capacity
Recovery time
```

Performance targets shall be linked to the success criteria.

---

# Chapter 1191 — Performance Test Environment

The test report shall document:

```text
Server CPU
Server memory
Server storage type
Client CPU
Client memory
Network speed
PostgreSQL version
Redis version
Operating-system version
Application version
```

Performance results without environment details are not meaningful.

---

# Chapter 1192 — Message Performance Tests

Measure:

```text
Single message storage latency
Direct-message end-to-end latency
Group-message delivery latency
Message retrieval latency
Pagination latency
Offline queue processing
WebSocket broadcast time
```

Datasets shall include conversations with more than 500 messages.

---

# Chapter 1193 — Attachment Performance Tests

Measure:

```text
Encryption throughput
Upload throughput
Download throughput
Decryption throughput
Chunk checksum overhead
Resume-state lookup
Memory usage
Finalisation time
```

Test file sizes:

```text
1 MiB
10 MiB
100 MiB
1 GiB where test hardware permits
```

---

# Chapter 1194 — Client Performance Tests

Measure:

```text
Application startup
Cached shell loading
Conversation-list rendering
Message-page rendering
Search response
Theme switching
Large conversation scrolling
Thumbnail loading
Cache maintenance
```

The GUI shall remain responsive during background work.

---

# Chapter 1195 — Load Testing

Load tests may simulate:

```text
50 concurrent users
100 concurrent users
250 WebSocket connections
Messages sent at a controlled rate
Concurrent file transfers
Repeated conversation loading
Administration dashboard refreshes
```

The initial target shall reflect realistic deployment requirements.

---

# Chapter 1196 — Load-Test Scenarios

Example normal-load scenario:

```text
100 connected users
10 messages per second
5 concurrent uploads
10 conversation queries per second
Periodic presence heartbeats
```

Example peak scenario:

```text
250 connected users
30 messages per second
10 concurrent uploads
Administrator dashboard open
```

Targets shall be adjusted to actual stakeholder needs.

---

# Chapter 1197 — Stress Testing

Stress testing intentionally exceeds expected capacity.

Purpose:

* Identify breaking point.
* Observe graceful overload.
* Confirm queue limits.
* Confirm rate limiting.
* Confirm recovery after load falls.

The system should reject excess work safely rather than corrupt data.

---

# Chapter 1198 — Soak Testing

A soak test runs for an extended duration.

Recommended duration:

```text
8 to 24 hours
```

It shall monitor:

```text
Memory growth
Database connections
Redis connections
WebSocket cleanup
Worker reliability
Log growth
Temporary-file cleanup
Transfer recovery
```

A stable application should not continuously leak resources.

---

# Chapter 1199 — Performance Assertions

Performance tests shall allow reasonable tolerance.

Tests shall avoid failing because of tiny timing variation.

Suitable approaches:

```text
Median latency
95th percentile latency
Maximum memory growth
Minimum sustained throughput
```

One unusually slow operation should be investigated but may not alone define failure.

---

# Chapter 1200 — Benchmark Baselines

Benchmark results shall be stored by version.

Example:

```text
Version 0.5.0
Message insert median: 45 ms

Version 0.6.0
Message insert median: 62 ms
```

Significant regressions shall be investigated before release.

---

# Chapter 1201 — Regression Testing

A regression test shall be added when a defect is fixed.

Process:

```text
Reproduce defect with failing test

↓

Fix defect

↓

Confirm test passes

↓

Keep test permanently
```

This prevents the same defect returning later.

---

# Chapter 1202 — Defect Classification

Defects may be classified as:

```text
Critical
High
Medium
Low
Cosmetic
```

Examples:

```text
Plaintext stored on server:

Critical

User cannot send messages:

High

Incorrect unread count:

Medium

Misaligned icon:

Cosmetic
```

Priority shall consider both impact and likelihood.

---

# Chapter 1203 — Defect Record

Each defect shall include:

```text
Defect identifier
Summary
Environment
Application version
Steps to reproduce
Expected result
Actual result
Severity
Evidence
Assigned status
Fix version
Regression-test reference
```

Screenshots and logs shall exclude sensitive data.

---

# Chapter 1204 — Defect Lifecycle

```text
NEW
CONFIRMED
IN_PROGRESS
FIXED
READY_FOR_RETEST
CLOSED
REOPENED
DEFERRED
```

A defect shall not be marked closed until the fix is verified.

---

# Chapter 1205 — Continuous Integration

Every code change shall run an automated pipeline.

Recommended stages:

```text
Install dependencies

↓

Lint

↓

Format check

↓

Type check

↓

Secret scan

↓

Security static analysis

↓

Unit tests

↓

Integration tests

↓

Coverage report

↓

Build package
```

Longer performance and end-to-end suites may run separately.

---

# Chapter 1206 — CI Isolation

The CI environment shall use:

```text
Temporary PostgreSQL
Temporary Redis
Temporary storage directories
Fake credentials
Test signing keys
Mock or test LDAP
```

Production secrets shall never be required.

---

# Chapter 1207 — CI Failure Policy

A merge shall be blocked when:

```text
Lint fails
Formatting fails
Type checking fails
Required tests fail
Coverage falls below the agreed threshold
Secret scan detects a likely secret
Critical dependency vulnerability is unresolved
```

Warnings shall be reviewed rather than ignored permanently.

---

# Chapter 1208 — Test Coverage

Coverage measures which code paths executed during tests.

Recommended initial target:

```text
Overall line coverage:

At least 80%

Security-critical modules:

At least 90%
```

Security-critical modules include:

```text
Authentication
Permissions
Token handling
Encryption wrappers
Attachment validation
Audit hashing
Session invalidation
```

Coverage percentage alone does not prove test quality.

---

# Chapter 1209 — Branch Coverage

Branch coverage shall be measured where practical.

It is especially important for:

```text
Permission decisions
Retry classification
State transitions
Error handling
Configuration validation
Membership rules
Token validation
```

Tests shall cover both allowed and denied branches.

---

# Chapter 1210 — Coverage Exclusions

Reasonable exclusions may include:

```text
Abstract method placeholders
Generated migration boilerplate
Platform-specific unreachable branches
Defensive code requiring process-level failure
```

Exclusions shall be documented.

Important code shall not be excluded merely to increase the percentage.

---

# Chapter 1211 — Test Data Management

Test data shall be synthetic.

It shall not use:

```text
Real employee names
Real passwords
Real messages
Real organisation data
Real private files
Production database copies
```

Example accounts:

```text
employee1
employee2
helpdesk1
hr1
admin1
```

---

# Chapter 1212 — Test Key Material

Automated tests shall use generated test-only keys.

Rules:

```text
Never reuse production keys.

Never commit production certificates.

Clearly label test keys.

Regenerate ephemeral keys where practical.

Keep deterministic fixtures only when required.
```

Test private keys shall not grant access to any real system.

---

# Chapter 1213 — Test Attachment Data

Test files may include:

```text
Small text file
PNG image
PDF fixture
Random binary file
File larger than one chunk
Zero-byte file if policy allows
Blocked-extension fixture
Unicode filename
```

Fixtures shall contain no sensitive content.

---

# Chapter 1214 — Manual Testing Purpose

Manual testing is required for behaviours involving:

* Human usability.
* Visual appearance.
* Accessibility.
* Error clarity.
* Window resizing.
* Notifications.
* Drag and drop.
* Perceived responsiveness.
* Installation.
* Real LAN behaviour.

Manual testing shall use documented scripts.

---

# Chapter 1215 — Manual Test Script Format

Each script shall contain:

```text
Test identifier
Feature
Preconditions
Steps
Expected result
Actual result
Pass or fail
Evidence reference
Tester
Date
Application version
```

This format supports NEA evidence.

---

# Chapter 1216 — Manual Login Test

Example:

```text
Test ID:

MAN-AUTH-001

Preconditions:

Server running.
Valid employee account exists.

Steps:

1. Launch BlueBubbles.
2. Enter server address.
3. Enter valid username and password.
4. Select Login.

Expected result:

The main window opens.
The correct display name appears.
The connection state shows Connected.
The password field is cleared.
```

---

# Chapter 1217 — Manual Messaging Test

```text
Test ID:

MAN-MSG-001

Steps:

1. User A opens a conversation with User B.
2. User A sends a text message.
3. User B observes the conversation.
4. User B opens the message.
5. User A observes delivery and read state.

Expected result:

The message appears once.
The content is correct.
Delivery state updates correctly.
The interface remains responsive.
```

---

# Chapter 1218 — Manual Attachment Test

```text
Test ID:

MAN-FILE-001

Steps:

1. Select a file larger than one chunk.
2. Upload it to a conversation.
3. Observe progress.
4. Download it as another user.
5. Open the downloaded file.

Expected result:

Progress updates.
The file completes.
The downloaded file opens correctly.
The file checksum matches the original.
```

---

# Chapter 1219 — Manual Offline Test

```text
Test ID:

MAN-OFFLINE-001

Steps:

1. Open a conversation.
2. Disconnect the client from the server.
3. Write and send a message.
4. Confirm it shows as pending.
5. Restore connection.

Expected result:

The message is preserved.
The client reconnects.
The message sends once.
The state changes from pending to stored.
```

---

# Chapter 1220 — Manual Accessibility Test

The tester shall verify:

```text
All major controls can be reached by keyboard.

Focus is visible.

Text remains readable at larger font size.

Dark and high-contrast themes remain usable.

Error messages are understandable without colour.

Buttons have descriptive accessible names.
```

Evidence may include screenshots and tester comments.

---

# Chapter 1221 — Stakeholder Testing

Stakeholders shall test the application against their original requirements.

Possible stakeholder groups:

```text
Ordinary employee
Helpdesk technician
Administrator
Teacher or project supervisor
```

Each stakeholder shall receive tasks relevant to their role.

---

# Chapter 1222 — Employee Acceptance Tasks

An employee tester may be asked to:

```text
Log in
Find a contact
Create a conversation
Send a message
Send a file
Search cached messages
Change notification settings
Use offline mode
Log out
```

Feedback shall focus on usability and clarity.

---

# Chapter 1223 — Helpdesk Acceptance Tasks

A helpdesk tester may be asked to:

```text
Find a user
Check account state
View connection status
Run diagnostics
Interpret an error code
Revoke a session where permitted
Confirm no message content is visible
```

This validates the support requirements.

---

# Chapter 1224 — Administrator Acceptance Tasks

An administrator tester may be asked to:

```text
View system health
View storage state
Disable a user
Change a role
Publish an announcement
Review an audit event
Resolve a security alert
Run a background worker
```

Every action shall generate the expected audit metadata.

---

# Chapter 1225 — Stakeholder Feedback Form

Suggested questions:

```text
Was the task easy to complete?

Were instructions clear?

Did any control behave unexpectedly?

Were error messages understandable?

Did the application respond quickly enough?

Did you feel confident that the action succeeded?

What should be improved?
```

Responses may use both ratings and written comments.

---

# Chapter 1226 — Acceptance Criteria

A feature shall be accepted when:

* Required automated tests pass.
* Manual script passes.
* Security requirements are satisfied.
* Performance target is met or justified.
* No critical defect remains.
* Stakeholder feedback is acceptable.
* Evidence is recorded.

Not every cosmetic issue must block acceptance.

---

# Chapter 1227 — Release Test Gates

Before a release candidate:

```text
Static analysis passes
Unit tests pass
Integration tests pass
Critical end-to-end tests pass
Security tests pass
Database migrations pass
No known critical defect remains
Performance tests show no major regression
Manual smoke test passes
```

A failed gate shall block release unless formally accepted and documented.

---

# Chapter 1228 — Smoke Testing

A smoke test verifies that the build is fundamentally usable.

Required smoke checks:

```text
Server starts
Client starts
Login works
Conversation list loads
Message sends
Message receives
Attachment uploads
Attachment downloads
Logout works
```

Smoke tests shall run after deployment to a test environment.

---

# Chapter 1229 — Sanity Testing

Sanity testing verifies a limited area after a small change.

Example:

After fixing message editing:

```text
Send message
Edit message
Receive update
Restart client
Confirm edited version remains
```

A full regression suite should still run before release.

---

# Chapter 1230 — User Acceptance Testing Environment

The UAT environment shall:

* Use isolated test accounts.
* Use synthetic data.
* Resemble the production network.
* Use TLS.
* Use the intended client operating system.
* Contain realistic file sizes.
* Permit reset between sessions.

It shall not share the production database.

---

# Chapter 1231 — Test Evidence for the NEA

Evidence may include:

```text
Test tables
Screenshots
Console output
Coverage reports
Performance graphs
Database queries proving ciphertext storage
Checksum comparisons
Stakeholder feedback
Defect records
Before-and-after results
```

Evidence shall be relevant and readable.

---

# Chapter 1232 — Test Evidence Naming

Recommended naming scheme:

```text
TEST-AUTH-001
TEST-MSG-001
TEST-FILE-001
TEST-GROUP-001
TEST-ADMIN-001
TEST-SEC-001
TEST-PERF-001
```

Evidence files may use:

```text
TEST-MSG-001-result.png
TEST-FILE-001-checksum.txt
TEST-PERF-001-latency.csv
```

---

# Chapter 1233 — Test Matrix

A test matrix shall link:

```text
Requirement

↓

Success criterion

↓

Test identifier

↓

Test method

↓

Expected result

↓

Evidence

↓

Final outcome
```

This demonstrates that every requirement has been evaluated.

---

# Chapter 1234 — Requirements Traceability

Example:

| Requirement                                | Test            | Evidence                       |
| ------------------------------------------ | --------------- | ------------------------------ |
| Messages are encrypted on the server       | SEC-MSG-004     | Database ciphertext screenshot |
| Files transfer without corruption          | E2E-FILE-001    | SHA-256 comparison             |
| Removed members receive no future messages | E2E-GROUP-006   | Event and database results     |
| Client recovers after network loss         | E2E-OFFLINE-002 | Screen recording and logs      |
| Helpdesk cannot view message content       | SEC-ADMIN-008   | API denial result              |

Every major stakeholder requirement shall have at least one test.

---

# Chapter 1235 — Test Result Status

Test results shall use:

```text
PASS
FAIL
BLOCKED
NOT_RUN
PARTIAL
```

`PARTIAL` shall be used only when part of a multi-step test succeeds and the limitation is explained.

---

# Chapter 1236 — Failed-Test Handling

When a test fails:

```text
Record actual result

↓

Create defect

↓

Assign severity

↓

Investigate

↓

Implement fix

↓

Add or update regression test

↓

Retest

↓

Close defect only after verification
```

Failed results shall not be removed from the evidence.

---

# Chapter 1237 — Flaky Tests

A flaky test passes and fails without a real code change.

Flaky tests shall be treated as defects.

The team shall not simply rerun them until they pass.

Common causes:

```text
Timing assumptions
Shared state
Incorrect async waiting
External dependency instability
Random test data
Uncontrolled clock
```

---

# Chapter 1238 — Async Test Rules

Asynchronous tests shall:

* Use bounded timeouts.
* Await background operations properly.
* Avoid arbitrary long sleeps.
* Clean up tasks.
* Close clients.
* Close WebSockets.
* Roll back transactions.
* Report hanging tasks.

Use event or signal waiting rather than guessing timing.

---

# Chapter 1239 — Test Cleanup

Every test shall clean up:

```text
Database rows
Redis keys
Temporary files
WebSocket connections
Background tasks
GUI widgets
Environment-variable changes
Mock patches
```

Fixture finalisers shall run even after assertion failure.

---

# Chapter 1240 — Parallel Test Execution

Tests may run in parallel only when:

* Database namespaces are isolated.
* Redis namespaces are isolated.
* Storage directories are isolated.
* Fixed network ports do not conflict.
* Shared environment variables are controlled.
* Time-based tests do not share global clocks.

Security and end-to-end suites may run sequentially for reliability.

---

# Chapter 1241 — Test Environment Verification

Before running a suite, a pre-test check may verify:

```text
Correct environment selected
Production database not configured
Production LDAP not configured
Temporary storage available
Test signing secret active
Required containers healthy
```

The suite shall stop if production resources are detected.

---

# Chapter 1242 — Destructive Test Protection

Tests that delete, truncate or migrate data shall require:

```text
Environment name = testing

and

Database name contains an approved test marker
```

This protects real data from accidental test execution.

---

# Chapter 1243 — Mutation Testing

Mutation testing intentionally modifies code to see whether tests detect the change.

It may be used selectively for:

```text
Permission checks
Token validation
Cryptographic verification conditions
Retention boundaries
State transitions
```

Possible tool:

```text
mutmut
```

Mutation testing may be deferred if time is limited.

---

# Chapter 1244 — Fuzz Testing

Fuzz testing may target parsers and validation boundaries.

Suitable inputs:

```text
WebSocket event envelopes
Base64 fields
Canonical JSON serialisation
Filename metadata
Protocol negotiation
Pagination cursors
Encrypted message DTOs
```

The system shall reject malformed input without crashing.

---

# Chapter 1245 — Backup and Restore Testing

Backup tests shall verify:

```text
Database backup completes
Attachment backup completes
Backup metadata is recorded
Restore into isolated environment succeeds
Messages remain available
Encrypted attachments remain identical
Audit chain remains valid
```

A backup is not considered verified until a restore test succeeds.

---

# Chapter 1246 — Disaster-Recovery Test

A controlled recovery test may:

```text
Stop server
Replace active database with restored backup
Restore encrypted attachment storage
Start server
Verify migrations
Verify audit chain
Authenticate test client
Retrieve historical messages
Download attachment
```

This shall be performed only in an isolated environment.

---

# Chapter 1247 — Installation Testing

Installation testing shall verify:

```text
Fresh server installation
Fresh client installation
Required directories created
Service account permissions
systemd service startup
Database migration
Redis connection
TLS configuration
Desktop shortcut
Uninstallation
Upgrade from previous version
```

Installation instructions shall be corrected if testers cannot follow them.

---

# Chapter 1248 — Upgrade Testing

Upgrade tests shall verify:

```text
Server upgrade preserves data
Client upgrade preserves settings
Client upgrade preserves drafts
Client upgrade preserves offline queue
Database migration succeeds
Old supported client still connects
Unsupported old client receives clear message
Rollback procedure works where supported
```

---

# Chapter 1249 — Compatibility Testing

Client compatibility shall be tested on:

```text
Windows 10
Windows 11
Supported display scaling levels
Supported Python runtime in development
```

Server compatibility shall be tested on:

```text
Debian 13
Supported PostgreSQL version
Supported Redis version
```

The final documentation shall list exactly supported environments.

---

# Chapter 1250 — Network Testing

LAN testing shall include:

```text
Low latency
Artificial latency
Packet loss
Temporary disconnection
Reduced bandwidth
Server restart
Client IP change
Certificate error
DNS failure
```

The client shall recover or report the problem clearly.

---

# Chapter 1251 — Network Emulation

Network conditions may be simulated using:

```text
Linux tc/netem
Proxy-based latency tools
Virtual-machine network controls
Firewall rules
```

The test setup shall be documented.

---

# Chapter 1252 — Time-Zone Testing

Although timestamps are stored in UTC, display shall be tested with:

```text
UK standard time
UK daylight-saving time
Different configured client zone
Clock near midnight
Date boundary
```

Security calculations shall remain based on UTC.

---

# Chapter 1253 — Unicode Testing

Unicode tests shall include:

```text
Accented names
Polish characters
Emoji
Right-to-left text
Combining characters
Long Unicode filenames
Non-Latin group names
```

The application shall preserve valid Unicode while still enforcing safe limits.

---

# Chapter 1254 — Boundary Testing

Boundary values shall be tested at:

```text
Minimum
Minimum minus one
Typical value
Maximum
Maximum plus one
```

Applicable fields:

```text
Message length
Group member count
Filename length
File size
Chunk size
Page size
Login attempts
Token lifetime
Retention period
```

---

# Chapter 1255 — Test Doubles

Test doubles include:

```text
Dummy
Stub
Spy
Mock
Fake
```

Use the simplest type that supports the test.

An in-memory fake repository is often better than a highly complex mock for service testing.

---

# Chapter 1256 — Mock Authentication Provider

The mock provider shall support:

```text
Valid login
Invalid login
Disabled account
Group mappings
Timeout
Directory outage
Slow response
Attribute changes
```

The provider shall return predictable test data.

---

# Chapter 1257 — Fake Event Publisher

```python
class FakeEventPublisher:
    """Captures published events for test assertions."""

    def __init__(self) -> None:
        self.events: list[ApplicationEvent] = []

    async def publish(
        self,
        event: ApplicationEvent,
    ) -> None:
        self.events.append(event)
```

Tests can verify that events are published only after successful transactions.

---

# Chapter 1258 — Fake File Storage

A fake or temporary filesystem storage implementation shall support:

```text
Write chunk
Read chunk
Simulate missing chunk
Simulate checksum corruption
Simulate disk full
Simulate permission failure
Simulate finalisation failure
```

This enables deterministic attachment tests.

---

# Chapter 1259 — Test Logging

Automated tests shall capture logs where relevant.

Assertions may verify:

```text
Correct error code logged
Correlation ID present
Sensitive values absent
Recovery event recorded
Expected warning emitted
```

Ordinary passing tests should not produce excessive console output.

---

# Chapter 1260 — Test Reporting

Automated reports shall include:

```text
Passed tests
Failed tests
Skipped tests
Execution time
Coverage
Warnings
Environment information
```

Reports may be generated in:

```text
Terminal
JUnit XML
HTML coverage
JSON
```

---

# Chapter 1261 — Skipped Tests

A test may be skipped only with a documented reason.

Examples:

```text
Requires Windows notification system
Requires optional LDAP container
Requires large performance environment
```

Permanent unexplained skips shall not be accepted.

---

# Chapter 1262 — Expected-Failure Tests

An expected-failure marker may be used temporarily for a known defect.

It shall include:

```text
Defect identifier
Reason
Planned resolution
```

Unexpected passes shall be investigated because they may indicate the defect was fixed or the test is incorrect.

---

# Chapter 1263 — Test Review

Critical tests shall be reviewed for:

```text
Correct assertions
Realistic assumptions
Missing negative cases
Sensitive-data handling
Race conditions
False positives
False negatives
```

A test can be incorrect just like production code.

---

# Chapter 1264 — Quality Metrics

Useful quality metrics include:

```text
Test pass rate
Coverage
Open defects by severity
Defect recurrence
Performance regression
Security findings
Mean time to repair
Flaky-test count
Stakeholder acceptance rate
```

Metrics shall support decisions rather than become targets that encourage misleading results.

---

# Chapter 1265 — Definition of Done

A feature is complete when:

```text
Code is implemented
Code is formatted
Type checking passes
Unit tests exist
Integration tests exist where required
Security cases are tested
Documentation is updated
No critical defect remains
Acceptance criteria are met
Evidence is recorded
```

Implementation alone is not completion.

---

# Chapter 1266 — Minimum Version 1.0 Test Suite

Version 1.0 shall include automated coverage for:

```text
Authentication
Session handling
Permission checks
Direct messages
Group messages
Message encryption wrappers
Attachments
File integrity
Offline queue
Local cache
Audit logging
Administration
Configuration
Error handling
Recovery
```

It shall include manual evidence for:

```text
GUI usability
Accessibility
LAN performance
Installation
Notifications
Stakeholder acceptance
```

---

# Chapter 1267 — Deferred Testing Features

The following may be deferred if time is limited:

```text
Large-scale distributed load testing
Advanced mutation testing
Continuous fuzzing
Automated visual-regression infrastructure
Multiple operating-system client platforms
External penetration testing
Formal cryptographic verification
```

Core security and functional tests shall not be deferred.

---

# Chapter 1268 — Testing Strategy Summary

BlueBubbles shall use a layered quality-assurance strategy.

Static analysis shall detect code-quality, type and security issues.

Unit tests shall verify isolated behaviour.

Component tests shall verify complete subsystems.

Integration tests shall use real PostgreSQL, Redis, storage and API components.

End-to-end tests shall verify complete user workflows using real encryption and network communication.

Security tests shall attempt to bypass authentication, permissions, storage controls and cryptographic verification.

Performance tests shall measure message latency, file throughput, resource use and client responsiveness.

Manual testing shall verify usability, accessibility, installation and real LAN behaviour.

Stakeholder testing shall demonstrate that employee, helpdesk and administrator requirements have been satisfied.

Every major requirement shall link to a test and evidence through a traceability matrix.

Critical defects shall block release.

Every fixed defect shall receive a regression test.

Production data, credentials and key material shall never be used in the testing environment.

The final NEA evaluation shall use repeatable evidence rather than unsupported claims.

---

# End of Part 18

Part 19 will define the complete deployment, installation and infrastructure subsystem, including:

* Debian server preparation.
* PostgreSQL installation.
* Redis installation.
* Service-account creation.
* Storage-directory setup.
* TLS certificates.
* Reverse-proxy configuration.
* systemd deployment.
* Firewall rules.
* Client packaging.
* Windows installation.
* Upgrade procedures.
* Rollback procedures.
* Deployment verification.

---

## Task-specific authoritative source: Part 28

# Part 28 — Automated and Manual Testing Specification

---

# Chapter 2919 — Testing Specification Purpose

This section defines the complete testing strategy for BlueBubbles.

Testing shall verify:

* Functional correctness.
* Security boundaries.
* Cryptographic correctness.
* Database integrity.
* Authentication behaviour.
* Authorisation behaviour.
* Message confidentiality.
* Attachment integrity.
* Offline recovery.
* Synchronisation.
* Administrative controls.
* User-interface behaviour.
* Performance.
* Accessibility.
* Deployment reliability.
* Backup and restore.
* Compliance with project requirements.

Testing shall begin during development and shall not be postponed until the application appears complete.

---

# Chapter 2920 — Testing Principles

The project shall follow these principles:

```text
Test behaviour rather than implementation details.

Test critical failures as carefully as successful paths.

Use real infrastructure where behaviour depends on that infrastructure.

Keep tests deterministic.

Use synthetic data.

Do not weaken production security to simplify testing.

Every corrected defect should receive a regression test.

Test boundaries between components.

Verify that sensitive data is absent where it should not exist.

Measure performance rather than assuming it.

Record evidence for important acceptance tests.
```

---

# Chapter 2921 — Test Levels

The complete test programme shall include:

```text
Static checks

Unit tests

Component tests

Repository tests

Integration tests

Contract tests

API tests

WebSocket tests

Cryptographic tests

File-transfer tests

Offline and recovery tests

System tests

End-to-end tests

Security tests

Performance tests

Accessibility tests

Usability tests

Deployment tests

Backup and restore tests

Acceptance tests
```

Each level has a different purpose and shall not be replaced by one large end-to-end suite.

---

# Chapter 2922 — Test Environments

Required environments:

```text
Local unit-test environment

Disposable PostgreSQL integration environment

Disposable Redis integration environment

Temporary attachment filesystem

Mock directory environment

Test LDAP or Active Directory environment

Windows client test environment

Debian server test VM

Network impairment environment

Clean installation environment

Backup and restore environment
```

Tests shall clearly state which environment they require.

---

# Chapter 2923 — Test Data Policy

All automated and manual testing shall use synthetic data.

Synthetic values shall include:

* Fake names.
* Fake usernames.
* Fake departments.
* Fake email addresses.
* Fake message content.
* Fake attachments.
* Fake administrative reasons.
* Fake announcements.
* Fake audit records.

Real passwords, private documents and production directory information shall not appear in tests.

---

# Chapter 2924 — Test Identifier Convention

Every documented test shall receive an identifier.

Recommended format:

```text
TEST-<SUBSYSTEM>-<NUMBER>
```

Examples:

```text
TEST-AUTH-001
TEST-MSG-014
TEST-CRYPTO-008
TEST-ATTACH-021
TEST-OFFLINE-006
TEST-ADMIN-012
TEST-DEPLOY-003
```

Identifiers shall remain stable after evidence has been recorded.

---

# Chapter 2925 — Test Record Structure

Each formal test record shall contain:

```text
Test ID
Requirement IDs
Subsystem
Purpose
Preconditions
Input data
Execution steps
Expected result
Actual result
Pass or fail
Environment
Evidence reference
Defect reference where failed
Retest result
Tester
Date
```

Automated test files may contain the executable details while the test report summarises the important cases.

---

# Chapter 2926 — Requirement Traceability Matrix

The project shall maintain a matrix linking:

```text
Requirement
Design chapter
Implementation module
Automated tests
Manual tests
Acceptance evidence
Final result
```

Example:

```text
Requirement:

NFR-SEC-003

Design:

Part 24, message encryption

Implementation:

client/security/message_crypto.py

Tests:

TEST-CRYPTO-004
TEST-SEC-011
TEST-SERVER-PLAINTEXT-001

Result:

Passed
```

Every mandatory requirement shall have at least one verification method.

---

# Chapter 2927 — Test Naming in Python

Pytest test functions shall use descriptive names.

Example:

```python
def test_refresh_token_reuse_invalidates_session() -> None:
    ...
```

Avoid names such as:

```python
def test_1() -> None:
    ...
```

Test class names may group closely related behaviour.

---

# Chapter 2928 — Test Directory Structure

Recommended layout:

```text
tests/
├── unit/
│   ├── shared/
│   ├── server/
│   └── client/
├── integration/
│   ├── database/
│   ├── redis/
│   ├── ldap/
│   ├── api/
│   ├── websocket/
│   └── storage/
├── end_to_end/
├── security/
├── performance/
├── gui/
├── deployment/
├── factories/
├── fixtures/
├── helpers/
└── test_data/
```

Tests shall mirror production modules where practical.

---

# Chapter 2929 — Test Marker Strategy

Pytest markers may include:

```text
unit
integration
postgres
redis
ldap
api
websocket
crypto
gui
security
performance
slow
deployment
windows
linux
```

The standard fast test command shall exclude long-running infrastructure tests.

The complete release command shall include all required markers.

---

# Chapter 2930 — Static Analysis Tests

Static checks shall include:

```text
Formatting verification
Ruff linting
mypy type checking
Import-boundary checking
Unused-code review
Dependency vulnerability scanning
Secret-pattern scanning
Licence review
Configuration-schema validation
```

Static analysis does not replace runtime tests.

---

# Chapter 2931 — Import Boundary Tests

Tests shall verify:

```text
shared does not import client

shared does not import server

server does not import client

server domain does not import FastAPI

server domain does not import SQLAlchemy sessions

client ViewModels do not import views

client views do not import networking clients directly

routers do not import ORM models directly
```

Violations shall fail the quality gate.

---

# Chapter 2932 — Secret Scan Tests

The repository shall be scanned for patterns resembling:

```text
Private key blocks
Database passwords
LDAP bind passwords
JWT secrets
Access tokens
Refresh tokens
Real email credentials
Production certificates with private keys
```

False positives may be reviewed, but real secrets shall never remain committed.

---

# Chapter 2933 — Unit-Test Scope

Unit tests shall focus on one class or function with controlled dependencies.

Suitable targets:

* Domain rules.
* Validation.
* Canonical serialisation.
* Permission policies.
* State transitions.
* Retry logic.
* Error mapping.
* DTO validation.
* Cryptographic adapters.
* ViewModel behaviour.
* Path construction.

Unit tests should not require external network services.

---

# Chapter 2934 — Unit-Test Isolation

Unit tests shall use:

* Fakes.
* Stubs.
* Deterministic clocks.
* Deterministic identifier generators.
* Temporary directories.
* Test-only random providers where required.
* In-memory event publishers.

Mocks shall be used when interaction verification is important.

---

# Chapter 2935 — Clock Fixtures

A fixed clock fixture shall support:

```python
class FixedClock:
    def __init__(self, current: datetime) -> None:
        self._current = current

    def now(self) -> datetime:
        return self._current

    def advance(self, delta: timedelta) -> None:
        self._current += delta
```

This shall be used for:

* Session expiry.
* Retry timing.
* Edit windows.
* Retention.
* Announcement expiry.
* Offline duration.
* Audit timestamps.

---

# Chapter 2936 — Identifier Fixtures

A deterministic identifier generator may return predefined UUIDs.

This supports:

* Predictable DTO snapshots.
* Idempotency tests.
* Audit-chain tests.
* Message ordering tests.
* Reproducible failure reports.

Production identifier generation shall remain random or otherwise approved.

---

# Chapter 2937 — Domain Model Tests

Required domain tests include:

```text
Session expiry
Session invalidation
Conversation membership activity
Group owner transitions
Message edit eligibility
Message delete eligibility
Delivery-state transitions
Upload-session transitions
Attachment completion rules
Security-alert transitions
Offline-action transitions
```

Invalid transitions shall raise typed errors.

---

# Chapter 2938 — Permission Policy Tests

Test every important permission boundary.

Examples:

```text
Employee cannot enter administration

Helpdesk can view ordinary user account state

Helpdesk cannot assign roles

HR can disable permitted user

Administrator cannot assign SuperAdministrator

Administrator cannot disable final SuperAdministrator

SuperAdministrator can modify approved security settings

Global role does not automatically grant group ownership
```

---

# Chapter 2939 — Error-Mapping Tests

For each public error code, verify:

```text
Correct HTTP status
Correct stable error code
Safe default message
Retry classification
Retry-after handling where relevant
No stack trace
Correlation ID included
Field errors represented correctly
```

Unknown internal exceptions shall map to a generic server error.

---

# Chapter 2940 — Configuration Unit Tests

Required tests:

```text
YAML loads correctly
Environment variables override YAML
Secret files override non-secret values
Unknown keys rejected
Invalid types rejected
Missing required production values rejected
Development defaults allowed only in development
Production mock authentication rejected
Unsafe HTTP configuration rejected
Conflicting settings rejected
Secrets redacted from representation
```

---

# Chapter 2941 — Canonical Serialisation Unit Tests

Verify deterministic output for:

```text
UUIDs
Timestamps
Null values
Integers
Binary values
Ordered arrays
Recipient envelope sorting
Message AAD
Attachment manifest
Audit event content
```

Equivalent logical inputs shall produce identical canonical bytes.

---

# Chapter 2942 — Repository Test Purpose

Repository tests shall verify real persistence behaviour against PostgreSQL.

They shall test:

* ORM mappings.
* SQL queries.
* Constraints.
* Index-supported ordering.
* Transactions.
* Locking.
* Pagination.
* Concurrency.

Repository tests shall not use SQLite as a replacement.

---

# Chapter 2943 — PostgreSQL Test Lifecycle

For a test session:

```text
Start or connect to disposable PostgreSQL

↓

Create temporary database

↓

Apply migrations to head

↓

Run tests

↓

Drop temporary database
```

Tests may use transaction rollback per case where compatible.

Migration tests shall create fresh databases.

---

# Chapter 2944 — Repository User Tests

Required:

```text
Create user
Retrieve user by ID
Retrieve by normalised username
Unique username enforced
Directory GUID uniqueness enforced
Update profile
Optimistic version conflict
Disable user
Soft-delete user
Search by approved fields
Pagination stable
```

---

# Chapter 2945 — Repository Session Tests

Required:

```text
Create session
Retrieve active session
List user sessions
Rotate refresh-token hash
Invalidate session
Invalidate all user sessions
Find expired sessions
Delete expired records according to policy
Token version increments
Concurrent refresh row locking
```

---

# Chapter 2946 — Repository Conversation Tests

Required:

```text
Create direct conversation
Find canonical direct pair
Concurrent duplicate direct creation
Create group
Add active member
Reject duplicate active member
Remove member
Re-add member with new membership period
List active members
Enforce at most one active owner
Retrieve user conversations
```

---

# Chapter 2947 — Repository Message Tests

Required:

```text
Insert encrypted message
Insert recipient envelopes
Reject duplicate recipient envelope
Retrieve only authorised envelope
Paginate by timestamp and UUID
Retrieve reply target
Update encrypted payload with expected version
Reject stale version
Soft-delete message
Store delivery state
Advance read state
```

---

# Chapter 2948 — Repository Attachment Tests

Required:

```text
Create upload session
Add chunk metadata
Reject duplicate chunk index
Store attachment
Store recipient envelopes
Mark complete
Link attachment to message
Reject invalid sizes
Retrieve authorised metadata
List expired orphan uploads
```

---

# Chapter 2949 — Repository Audit Tests

Required:

```text
Lock audit chain state
Append first event
Append subsequent event
Sequence increments
Previous hash correct
Concurrent append remains continuous
Update rejected
Delete rejected
Application role permission restricted
List by sequence
Filter by category and actor
```

---

# Chapter 2950 — Transaction Tests

Required transactional scenarios:

```text
Message insert failure rolls back recipient keys

Recipient-key failure rolls back message

Audit failure rolls back user disable

Outbox failure rolls back business change

Group creation failure rolls back memberships

Ownership transfer commits atomically

Attachment finalisation failure rolls back metadata

Configuration update and audit commit together
```

---

# Chapter 2951 — Deadlock and Concurrency Tests

Test controlled concurrency for:

```text
Audit append
Group ownership transfer
Refresh-token rotation
Direct conversation creation
Message editing
Outbox claiming
Configuration version update
Final SuperAdministrator protection
```

Expected outcomes shall be deterministic.

---

# Chapter 2952 — Migration Tests

Every migration shall be tested for:

```text
Upgrade from previous revision
Fresh installation to head
Expected columns and constraints
Data backfill correctness
Index creation
Trigger creation
Application startup compatibility
```

Destructive migrations shall be tested using realistic data copies.

---

# Chapter 2953 — Migration Data Preservation Tests

Where schema changes affect existing data, verify:

* Messages remain retrievable.
* Recipient envelopes remain linked.
* Sessions retain correct state.
* Drafts remain readable on client migrations.
* Audit hashes remain valid.
* Attachment references remain valid.
* Configuration history remains complete.

---

# Chapter 2954 — API Test Purpose

API tests shall verify the complete HTTP boundary:

```text
Routing
Authentication
Authorisation
Request validation
Service invocation
Response models
Error responses
Status codes
Headers
Rate limits
Idempotency
Correlation IDs
```

Tests shall use the FastAPI application with controlled dependencies.

---

# Chapter 2955 — API Authentication Tests

Required:

```text
Missing token rejected
Malformed token rejected
Expired token rejected
Wrong issuer rejected
Wrong audience rejected
Unsupported algorithm rejected
Inactive session rejected
Disabled user rejected
Valid token accepted
Role change takes effect without stale permission
```

---

# Chapter 2956 — Login API Tests

Required:

```text
Valid credentials
Invalid credentials
Unknown user
Disabled account
Directory unavailable
Rate-limited login
Malformed request
Unsupported client version
Protocol mismatch
Successful audit event
Failed-attempt record contains no password
```

---

# Chapter 2957 — Refresh API Tests

Required:

```text
Valid refresh
Expired refresh
Revoked session
Wrong token
Token reuse
Concurrent refresh requests
Replacement token stored
Old token rejected
Access token version updated
Session audit event created
```

---

# Chapter 2958 — User API Tests

Required:

```text
Get current profile
Update permitted field
Reject directory-managed field update
Search authorised users
Pagination
Retrieve public keys
Register valid key
Reject private-key field
Reject invalid fingerprint
Revoke key with permission
```

---

# Chapter 2959 — Conversation API Tests

Required:

```text
Create direct conversation
Return existing direct conversation
Create group
List conversations
Retrieve conversation as member
Reject non-member
Update mute preference
Update pin preference
List members
Reject malformed cursor
```

---

# Chapter 2960 — Group API Tests

Required:

```text
Owner adds member
Moderator adds member where permitted
Member cannot add
Owner removes member
Moderator cannot remove owner
Member leaves
Owner cannot leave without transfer
Transfer ownership
Concurrent ownership changes
Removed member denied future access
```

---

# Chapter 2961 — Message API Tests

Required:

```text
Send valid encrypted message
Reject missing recipient envelope
Reject extra recipient envelope
Reject duplicate recipient
Reject unsupported protocol
Reject oversized payload
Reject invalid nonce length
Reject invalid tag length
Reject invalid reply target
Idempotent duplicate accepted
Conflicting duplicate rejected
```

---

# Chapter 2962 — Message Retrieval API Tests

Required:

```text
Member retrieves page
Non-member receives concealed not-found response
Only caller recipient envelope returned
Pagination cursor valid
Deleted placeholder returned
Membership join-time filtering
Membership removal-time filtering
Reply metadata returned
Protocol fields preserved
```

---

# Chapter 2963 — Message Edit API Tests

Required:

```text
Sender edits within window
Non-sender rejected
Expired edit rejected
Stale version rejected
New recipient envelope set required
New message version returned
Audit event created where configured
Recipient event published after commit
```

---

# Chapter 2964 — Message Delete API Tests

Required:

```text
Sender deletes
Non-sender rejected
Moderator path permitted where configured
Already deleted treated correctly
Stale version conflict
Attachment state updated
Deletion event published
Plaintext not logged
```

---

# Chapter 2965 — Attachment API Tests

Required:

```text
Initialise valid upload
Reject excessive size
Reject blocked extension
Reject invalid chunk size
Upload valid chunk
Resume upload
Duplicate identical chunk accepted safely
Conflicting chunk rejected
Complete with all chunks
Reject completion with missing chunk
Authorised download
Unauthorised download concealed
```

---

# Chapter 2966 — Administration API Tests

Required:

```text
Employee denied
Helpdesk limited access
Administrator user search
Disable user
Enable user
Role change
Session revoke
Connection disconnect
Audit query
Alert acknowledge
Worker run
Configuration update
Announcement publish
Export creation
Maintenance entry
```

---

# Chapter 2967 — API Response Schema Tests

Every endpoint shall verify:

* Declared response model.
* No unexpected sensitive fields.
* UUID and timestamp formats.
* Pagination metadata.
* Correct status code.
* Error schema consistency.
* OpenAPI model consistency where practical.

---

# Chapter 2968 — Correlation ID Tests

Required:

```text
Server generates correlation ID when absent
Valid client correlation ID preserved
Malformed client ID replaced
Response header contains correlation ID
Logs contain same ID
Error envelope contains same ID
WebSocket errors include correlation ID
```

---

# Chapter 2969 — Rate-Limit Tests

Required:

```text
Requests below threshold succeed
Threshold exceeded returns 429
Retry-after present
Different users isolated
Unauthenticated source-IP limit works
Redis failure follows configured fallback
Administrative limits stricter where required
Rate-limit response contains no sensitive state
```

---

# Chapter 2970 — WebSocket Test Purpose

WebSocket tests shall verify:

* Connection authentication.
* Protocol validation.
* Heartbeats.
* Event dispatch.
* Event publication.
* Disconnection.
* Session revocation.
* Duplicate handling.
* Reconnection.
* Durable-event recovery.

---

# Chapter 2971 — WebSocket Authentication Tests

Required:

```text
Connect without authentication
Authentication within timeout
Authentication timeout
Invalid token
Expired token
Revoked session
Unsupported protocol
Valid connection registration
Duplicate connection handling
```

---

# Chapter 2972 — WebSocket Heartbeat Tests

Required:

```text
Heartbeat updates timestamp
Missing heartbeat closes connection
Heartbeat rate limit
Malformed heartbeat rejected
Connection manager removes timed-out entry
Presence expiry follows disconnect
```

---

# Chapter 2973 — WebSocket Event Tests

Required:

```text
Message-received event delivered
Message-updated event delivered
Message-deleted event delivered
Group membership event delivered
Session-revoked event delivered
Announcement event delivered
Policy-update event delivered
Unknown event type rejected
Invalid event payload rejected
```

---

# Chapter 2974 — WebSocket Concurrency Tests

Test:

```text
Concurrent sends to one connection
Concurrent register and unregister
Multiple connections for one user
Multiple sessions for one user
Disconnect all connections for session
Failed socket removed safely
Global registry lock not held during slow send
```

---

# Chapter 2975 — WebSocket Reconnection Tests

Required:

```text
Unexpected disconnect triggers retry
Manual logout suppresses reconnect
Access token refresh before reconnect
Last event ID submitted
Missed durable events recovered
Duplicate replay ignored
Expired cursor triggers resync
```

---

# Chapter 2976 — Redis Integration Tests

Required:

```text
Presence set and expires
Typing state set and expires
Pub/Sub event reaches subscriber
Connection failure translated
Reconnect succeeds
Rate-limit storage works
Cache invalidation message delivered
Redis restart produces recovery
```

Tests shall not assume Redis is authoritative for permanent data.

---

# Chapter 2977 — LDAP Integration Tests

Use an isolated test directory.

Required:

```text
Secure bind
User search
Escaped special characters
Valid user authentication
Invalid password
Unknown user
Disabled user
Expired password where detectable
Group mapping
Timeout
Certificate failure
Directory unavailable
```

Submitted passwords shall not appear in logs.

---

# Chapter 2978 — Cryptographic Test Purpose

Cryptographic tests shall verify:

* Exact algorithm use.
* Correct key lengths.
* Correct nonce lengths.
* Correct canonicalisation.
* Recipient isolation.
* Signature verification.
* Authentication-tag handling.
* Key rotation.
* Key revocation.
* Local encryption.
* Attachment encryption.
* Deterministic test vectors.

These tests are release-critical.

---

# Chapter 2979 — Identity Key Tests

Required:

```text
Generate X25519 key pair
Generate Ed25519 key pair
Correct raw key lengths
Public and private keys correspond
Fingerprint stable
Different keys produce different fingerprints
Private key encrypts locally
Private key reloads after restart
Wrong local key cannot decrypt
```

---

# Chapter 2980 — Message Encryption Tests

Required:

```text
Plaintext round trip
Unicode round trip
Empty allowed structure
Maximum-length message
Fresh content key per message
Fresh nonce per message
Sender envelope included
Every recipient decrypts
Unrelated user cannot decrypt
Ciphertext differs for same plaintext
```

---

# Chapter 2981 — Message Signature Tests

Required:

```text
Valid signature verifies
Wrong signing key fails
Modified ciphertext fails
Modified nonce fails
Modified tag fails
Modified message ID fails
Modified conversation ID fails
Modified recipient list fails
Modified recipient envelope fails
Modified attachment list fails
```

---

# Chapter 2982 — Message AAD Tests

Required:

```text
Correct AAD decrypts
Wrong sender fails
Wrong reply target fails
Wrong version fails
Wrong timestamp fails
Wrong protocol fails
Different attachment ordering handled according to canonical rules
Unknown format version rejected
```

---

# Chapter 2983 — Recipient Envelope Tests

Required:

```text
X25519 shared secret matches
HKDF output stable for test vector
Correct recipient unwraps
Wrong recipient fails
Wrong message ID fails
Wrong key version fails
Wrong salt fails
Wrong wrapping nonce fails
Modified wrapped key fails
Modified tag fails
```

---

# Chapter 2984 — Key Rotation Tests

Required:

```text
New encryption key becomes primary
Old encryption key not used for new message
Historical message decrypts with old key
New signing key signs new message
Old signing key verifies historical signature
Revoked key rejected for new encryption
Revoked key metadata preserved
Key-change event invalidates cache
```

---

# Chapter 2985 — Cryptographic Failure-Safety Tests

Verify that failures return no plaintext.

Cases:

```text
Signature failure
GCM tag failure
Wrong private key
Corrupt key store
Unsupported algorithm
Malformed canonical data
Missing recipient envelope
Invalid key length
Invalid nonce length
```

No partial plaintext shall be displayed or returned.

---

# Chapter 2986 — Attachment Cryptographic Tests

Required:

```text
Single-chunk round trip
Multi-chunk round trip
Final short chunk
Empty file where permitted
Large streamed file
Unique nonce per chunk
Wrong chunk order fails
Modified chunk fails
Missing chunk fails
Manifest modification fails
Wrong file key fails
```

---

# Chapter 2987 — Attachment Manifest Tests

Required:

```text
Canonical manifest stable
All chunk hashes included
Recipient envelopes sorted
Signature verifies
Chunk count modification fails
Encrypted metadata modification fails
Uploader ID modification fails
Conversation ID modification fails
Recipient removal fails signature
```

---

# Chapter 2988 — Local Encryption Tests

Required:

```text
Draft encryption round trip
Offline action encryption round trip
Message cache encryption round trip
Transfer-state encryption round trip
Different purpose key fails
Different record context fails
Modified ciphertext fails
Modified tag fails
Fresh nonce used
Plaintext marker absent from database
```

---

# Chapter 2989 — Cryptographic Test Vector Storage

Test vectors shall be stored under:

```text
tests/test_data/crypto/
```

They shall contain only synthetic keys and plaintext.

Files shall state:

* Format version.
* Generation method.
* Approved algorithm.
* Expected values.
* Date generated.
* Review status.

Test vectors shall not be regenerated automatically during ordinary test execution.

---

# Chapter 2990 — Server Plaintext Absence Test

A release-critical test shall send known plaintext markers.

Example message marker:

```text
BLUEBUBBLES-MESSAGE-PLAINTEXT-91C2
```

Example attachment marker:

```text
BLUEBUBBLES-ATTACHMENT-PLAINTEXT-64E8
```

The test shall search server-controlled storage after processing.

---

# Chapter 2991 — Plaintext Search Locations

Search:

```text
PostgreSQL text and binary dumps
Message rows
Attachment metadata rows
Outbox payloads
Audit details
Server logs
Rotated logs
Temporary upload directories
Permanent attachment storage
Diagnostic packages
Generated server exports
Test backups
```

The expected result is no unintended plaintext marker.

---

# Chapter 2992 — Plaintext Test Limitations

The plaintext absence test can detect accidental direct storage.

It does not prove:

* Complete absence from process memory.
* Resistance to compromised endpoints.
* Formal cryptographic security.
* Absence from all operating-system swap or crash files.

The test result shall not be overclaimed.

---

# Chapter 2993 — File-Transfer Functional Tests

Required:

```text
Initial upload
Chunk upload
Resume after disconnect
Resume after client restart
Resume after server restart
Cancel upload
Expired upload
Complete upload
Download
Resume download
Cancel download
Overwrite confirmation
Final atomic rename
```

---

# Chapter 2994 — File-Transfer Integrity Tests

Required:

```text
Incorrect encrypted checksum
Incorrect plaintext checksum
Corrupted temporary chunk
Corrupted permanent chunk
Missing database chunk record
Missing filesystem chunk
Duplicate index
Out-of-order chunk retrieval
Wrong attachment manifest
Wrong recipient envelope
```

The client shall never mark a corrupt file complete.

---

# Chapter 2995 — File-Transfer Storage Tests

Required:

```text
Path traversal filename
Absolute filename
Reserved Windows filename
Very long filename
Unicode filename
Duplicate display filename
Storage mount missing
Storage read-only
Disk full
Insufficient reserved space
Atomic move failure
Cleanup after failed finalisation
```

Physical storage paths shall remain generated from safe identifiers.

---

# Chapter 2996 — Large-File Tests

Test representative sizes according to policy.

Example set:

```text
1 byte
1 KiB
1 MiB
One chunk exactly
One chunk plus one byte
100 MiB
Maximum configured size
Over maximum size
```

For very large configured limits, automated test sizes may be scaled while separate performance tests use realistic large files.

---

# Chapter 2997 — Memory-Bound Tests

During large-file encryption and transfer, measure process memory.

Acceptance:

```text
Memory use remains bounded relative to chunk size.

The complete file is not loaded into memory.

No severe growth occurs per additional chunk.
```

Memory thresholds shall be based on the target client environment.

---

# Chapter 2998 — Offline Queue Tests

Required:

```text
Queue message offline
Restart client
Reconnect
Submit once
Cancel pending message
Edit pending message
Queue read update
Coalesce preferences
Queue announcement acknowledgement
Block action on dependency
Recover PROCESSING action after crash
```

---

# Chapter 2999 — Offline Security-State Tests

Required scenarios:

```text
User removed while offline
Account disabled while offline
Session revoked while offline
Recipient key rotated while offline
Recipient key revoked while offline
Conversation deleted while offline
Policy changed while offline
Protocol changed while offline
```

No stale action shall bypass current server state.

---

# Chapter 3000 — Synchronisation Tests

Required:

```text
Initial full sync
Incremental sync
No-change sync
Missed durable events
Duplicate events
Out-of-order events
Expired event cursor
Aggregate version gap
Targeted conversation resync
Full cache resync
Sync cancellation
Sync restart
```

---

# Chapter 3001 — Synchronisation Cursor Tests

Verify:

```text
Cursor not advanced before local commit
Cursor preserved after failed page
Cursor advances after successful page
Duplicate page remains idempotent
Invalid cursor causes safe resync
Scope cursor isolated
Last event ID stored atomically
```

---

# Chapter 3002 — Conflict Tests

Required:

```text
Message edit version conflict
Duplicate message ID conflict
Membership conflict
Key conflict
Policy conflict
Attachment conflict
Deletion conflict
Protocol conflict
Preference conflict
Read-position conflict
```

Each conflict shall have a defined automatic or user-assisted resolution.

---

# Chapter 3003 — Crash Recovery Tests

Simulate process termination during:

```text
Draft save
Queue insert
Message submission
Local completion commit
Attachment preparation
Chunk upload
Download decryption
Synchronisation page commit
Local migration
Cache rebuild
```

After restart, state shall be consistent and recoverable.

---

# Chapter 3004 — Client Local Database Tests

Required:

```text
Create profile database
Apply migrations
Open with correct key
Reject wrong key
Store encrypted cache
Store draft
Store queue action
Store transfer
Store tombstone
Integrity check
Backup before migration
Restore after migration failure
```

---

# Chapter 3005 — Client Migration Tests

For every local migration:

```text
Create previous-version database

Insert representative data

Run migration

Verify schema

Verify drafts

Verify pending actions

Verify encrypted message cache

Verify transfer manifests

Verify search index behaviour
```

No migration shall silently remove unsent work.

---

# Chapter 3006 — GUI Unit-Test Purpose

GUI tests shall verify:

* ViewModel interaction.
* Control state.
* Signals.
* Focus.
* Keyboard shortcuts.
* Validation.
* Loading states.
* Error states.
* Accessibility properties.
* Theme response.

They shall not rely solely on screenshot comparison.

---

# Chapter 3007 — Login GUI Tests

Required:

```text
Username required
Password required
Invalid server URL
Password masked
Show-password toggle
Submit button busy state
Duplicate submission prevented
Authentication error displayed
Connection failure displayed
Password cleared after failure
Keyboard submission
```

---

# Chapter 3008 — Main Navigation GUI Tests

Required:

```text
Chats navigation
Contacts navigation
Groups navigation
Transfers navigation
Search navigation
Settings shortcut
Administration hidden for Employee
Administration shown when authorised
Selection state accessible
Badge updates
```

---

# Chapter 3009 — Conversation List GUI Tests

Required:

```text
Cached conversations displayed
Unread styling
Muted indicator
Pinned ordering
Search filtering
Empty state
Loading state
Refresh failure retains cache
Keyboard selection
Context menu actions
```

---

# Chapter 3010 — Chat GUI Tests

Required:

```text
Message page loads
Older messages load
Own and other messages distinguished
Pending state
Stored state
Delivered state
Read state
Failed state
Reply mode
Edit mode
Delete confirmation
Unread separator
Date separator
```

---

# Chapter 3011 — Composer GUI Tests

Required:

```text
Draft restored
Enter sends
Shift+Enter inserts line
Alternative send mode
Character limit
Attachment selection
Reply banner
Edit banner
Send disabled when empty
Offline placeholder
Failed send preserves text
```

---

# Chapter 3012 — Attachment GUI Tests

Required:

```text
Preparation progress
Upload progress
Pause
Resume
Cancel
Failure
Retry
Download
Verification failure
Completed open action
Long filename elision
Accessible file information
```

---

# Chapter 3013 — Settings GUI Tests

Required:

```text
Theme switch
Font scale
Notification preferences
Storage display
Cache clear confirmation
Draft deletion warning
Session list
Session revoke confirmation
Diagnostics launch
Restart-required indication
```

---

# Chapter 3014 — Administration GUI Tests

Required:

```text
Dashboard loading
User search
Disable confirmation
Role-change warning
Session revoke
Connection disconnect
Audit filters
Alert acknowledgement
Worker manual run
Configuration review
Announcement preview
Export status
```

---

# Chapter 3015 — GUI Focus Tests

Verify:

```text
Initial login focus
Tab order
Dialog focus trap
Focus restored after dialog
First invalid field focused
Message composer shortcut
Conversation-list shortcut
Visible focus indicators
No focus loss after refresh
```

---

# Chapter 3016 — GUI Theme Tests

Test:

```text
Light theme
Dark theme
High-contrast theme
Runtime switching
Dialog theme update
Icon update
Message bubble readability
Error-state contrast
Selected-row contrast
Disabled-control readability
```

---

# Chapter 3017 — Font Scaling Tests

At minimum test:

```text
100%
125%
150%
```

Verify:

* Buttons do not clip.
* Message text wraps.
* Table rows remain readable.
* Dialogs remain usable.
* Composer remains bounded.
* Navigation tooltips remain available.
* No important label disappears.

---

# Chapter 3018 — Accessibility Testing

Accessibility tests shall include:

```text
Keyboard-only operation
Screen-reader labels
Accessible role and state
Colour-independent communication
High contrast
Text scaling
Reduced motion
Error announcements
Progress announcements
Dialog focus management
```

Manual testing may be required because automation cannot validate the full experience.

---

# Chapter 3019 — Screen-Reader Test Scenarios

A screen-reader user shall be able to:

```text
Identify login fields
Submit login
Identify navigation items
Select conversation
Identify sender and timestamp
Read message content
Identify delivery state
Focus composer
Send message
Understand errors
Confirm destructive actions
```

---

# Chapter 3020 — Colour-Independence Tests

Verify that the following remain understandable in greyscale:

```text
Selected navigation
Online and offline state
Unread state
Message failure
Transfer failure
Health state
Audit severity
Security-alert severity
Form validation
```

Text, shapes or icons shall supplement colour.

---

# Chapter 3021 — End-to-End Test Purpose

End-to-end tests shall exercise complete user journeys across:

```text
Windows client
TLS reverse proxy
FastAPI server
PostgreSQL
Redis
Directory provider
Attachment filesystem
```

These tests provide confidence that integrated components work together.

---

# Chapter 3022 — End-to-End Authentication Test

Scenario:

```text
Install or start client

↓

Connect to test server

↓

Authenticate user

↓

Receive token pair

↓

Open main window

↓

Refresh token

↓

Log out

↓

Confirm session invalidated
```

Evidence shall include server audit records.

---

# Chapter 3023 — End-to-End Direct Messaging Test

Scenario:

```text
User A logs in

User B logs in

User A opens direct conversation

User A sends message

Server stores encrypted record

User B receives event

User B verifies and decrypts

User B marks read

User A sees read state
```

---

# Chapter 3024 — End-to-End Group Test

Scenario:

```text
Owner creates group

Adds two members

Sends encrypted group message

Both recipients decrypt

Moderator removes one member

Owner sends another message

Remaining member decrypts

Removed member receives no new envelope
```

---

# Chapter 3025 — End-to-End Attachment Test

Scenario:

```text
User selects file

Client encrypts chunks

Upload completes

Message links attachment

Recipient downloads

Recipient verifies manifest

Recipient decrypts file

Final SHA-256 matches source
```

The server plaintext marker search shall follow.

---

# Chapter 3026 — End-to-End Offline Test

Scenario:

```text
User disconnects client

Writes draft

Queues message

Restarts client

Another user changes group membership

Client reconnects

Synchronisation runs

Invalid message is blocked

Valid direct message sends once
```

---

# Chapter 3027 — End-to-End Administration Test

Scenario:

```text
Administrator logs in

Searches employee

Disables employee

Employee session invalidated

Employee WebSocket closes

Administrator reviews audit event

Administrator re-enables employee

Employee authenticates again
```

---

# Chapter 3028 — End-to-End Audit Integrity Test

Scenario:

```text
Perform several administrative actions

Run audit verification

Confirm valid

Tamper using privileged isolated test connection

Run verification again

Confirm critical failure

Confirm security alert created
```

This shall never run against production data.

---

# Chapter 3029 — Security-Test Purpose

Security tests shall verify resistance to:

* Authentication bypass.
* Authorisation bypass.
* Injection.
* Path traversal.
* Token misuse.
* Replay.
* Oversized requests.
* Malformed encrypted data.
* Sensitive-data exposure.
* Unsafe configuration.
* Session fixation.
* Cross-user data access.

---

# Chapter 3030 — Authentication Security Tests

Required:

```text
Brute-force rate limiting
Username enumeration resistance
Session fixation resistance
Refresh-token replay
Access-token algorithm substitution
Expired token
Modified token
Wrong issuer
Wrong audience
Disabled user
Revoked session
Concurrent refresh race
```

---

# Chapter 3031 — Authorisation Security Tests

Attempt direct object access to:

```text
Another user’s profile fields
Another user’s session
Unrelated conversation
Unrelated message
Another user’s recipient envelope
Unrelated attachment
Administrative endpoint
Audit export
Configuration history
Security alert
```

Every access shall be denied or concealed appropriately.

---

# Chapter 3032 — Injection Tests

Test:

```text
SQL injection strings
LDAP filter injection
Header injection
Log injection
CSV formula injection
Path injection
JSON structure abuse
Unexpected Unicode control characters
```

All persistence queries shall remain parameterised.

LDAP values shall be escaped using approved APIs.

---

# Chapter 3033 — Path Traversal Tests

Attempt filenames and paths such as:

```text
../../secret
..\..\secret
/absolute/path
C:\Windows\file
%2e%2e%2f
Unicode separator variants
Symbolic-link escape
```

The storage layer shall keep every path inside the configured root.

---

# Chapter 3034 — Request-Smuggling and Proxy Tests

Production-like tests shall verify:

* Nginx and Uvicorn agree on body length.
* Unsupported transfer encodings are rejected.
* Duplicate content-length anomalies are handled safely.
* WebSocket upgrade works only on intended route.
* Proxy headers are trusted only from configured proxy addresses.

---

# Chapter 3035 — Oversized Input Tests

Test limits for:

```text
Login fields
Display name
Status message
Group title
Group description
Message payload
Recipient list
Attachment size
Chunk size
Announcement body
Administrative reason
Audit filters
Pagination limit
```

Oversized inputs shall fail before excessive memory use.

---

# Chapter 3036 — Malformed Binary Tests

Submit:

```text
Invalid Base64
Incorrect decoded key length
Incorrect nonce length
Incorrect tag length
Huge binary field
Missing binary field
Duplicate recipient envelope
Unsupported algorithm
Unsupported format version
```

The server shall reject safely without attempting decryption.

---

# Chapter 3037 — Sensitive Logging Tests

Inject known secret markers into:

```text
Password
Access token
Refresh token
Private key
Message plaintext
Draft
Search query
Attachment plaintext
LDAP bind password
Database password
```

Trigger errors.

Search logs and diagnostics.

No prohibited marker shall appear.

---

# Chapter 3038 — Diagnostic Package Security Tests

Verify that packages exclude:

```text
Passwords
Tokens
Private keys
Plaintext messages
Plaintext attachments
Drafts
Search terms
Raw secure-store contents
Database credentials
LDAP credentials
```

The package manifest shall list included files accurately.

---

# Chapter 3039 — TLS Tests

Required:

```text
Valid certificate succeeds
Expired certificate fails
Wrong hostname fails
Untrusted issuer fails
Missing intermediate fails
HTTP rejected in production
Certificate pin or managed trust works where configured
WebSocket uses WSS
```

There shall be no production bypass button.

---

# Chapter 3040 — Session Security Tests

Required:

```text
Logout invalidates session
Revoke session disconnects socket
Revoke all invalidates every target session
Access token rejected after session invalidation
Role change invalidates permission state
Disabled account cannot refresh
Refresh reuse creates alert
Current session correctly identified
```

---

# Chapter 3041 — Administrative Security Tests

Required:

```text
Client-forged capability ignored
Hidden button does not grant access
Missing reason rejected
Stale expected version rejected
Final SuperAdministrator protected
Lower role cannot manage higher role
Step-up authentication required where configured
Audit export permission enforced
Configuration secret fields inaccessible
```

---

# Chapter 3042 — Cryptographic Misuse Review

A manual code review shall verify:

```text
No ECB
No unauthenticated encryption
No nonce reuse pattern
No static content keys
No hard-coded keys
No private-key upload
No signature bypass
No tag-failure ignore
No insecure random source
No algorithm fallback
```

This review shall be recorded separately from automated tests.

---

# Chapter 3043 — Dependency Security Testing

Before release:

* Scan Python dependencies for known vulnerabilities.
* Review direct dependency versions.
* Review abandoned packages.
* Remove unused dependencies.
* Confirm cryptography library version.
* Confirm Qt packaging dependencies.
* Record accepted risks.

Automated vulnerability results shall be manually reviewed.

---

# Chapter 3044 — Fuzz Testing

Fuzz or property-based testing is recommended for:

```text
DTO parsing
Cursor parsing
Canonical serialisation
Message envelope validation
Attachment manifest parsing
Error response parsing
Path validation
State-transition validation
```

Hypothesis may be used for Python property-based tests.

---

# Chapter 3045 — Property-Based Test Examples

Properties:

```text
Serialising then parsing preserves valid DTO data.

Canonical serialisation is deterministic.

Invalid nonce lengths are always rejected.

Recipient ordering does not change the canonical recipient set.

Message pagination never duplicates an ID.

State-transition validator rejects every unlisted transition.
```

---

# Chapter 3046 — Performance-Test Purpose

Performance tests shall determine whether the system meets practical targets on the selected hardware.

They shall measure:

* Latency.
* Throughput.
* Memory.
* CPU.
* Storage use.
* Database load.
* Client responsiveness.

Performance testing shall use production-like settings where possible.

---

# Chapter 3047 — Performance Environment Recording

Every result shall record:

```text
Client CPU
Client RAM
Client storage
Server CPU
Server RAM
Database storage
Network speed
Latency
Operating systems
Application version
Database version
Redis version
Dataset size
```

Results without environment information are not comparable.

---

# Chapter 3048 — Login Performance Tests

Measure:

```text
Directory authentication latency
Session creation latency
Token generation latency
Complete login API latency
Client time to main window
```

Test:

* Warm directory connection.
* Cold directory connection.
* Concurrent logins.
* Directory delay.
* Database pool pressure.

---

# Chapter 3049 — Message Performance Tests

Measure:

```text
Client encryption time
Recipient-envelope generation
REST request time
Database transaction time
Outbox publication delay
WebSocket delivery delay
Recipient verification time
Recipient decryption time
```

Test direct and group conversations.

---

# Chapter 3050 — Group Scaling Tests

Test group sizes:

```text
2
10
25
50
100
```

Measure:

* Key-envelope generation.
* Request size.
* Server validation.
* Database insert time.
* Recipient event publication.
* Client memory.

The configured group maximum shall reflect tested limits.

---

# Chapter 3051 — Message History Performance Tests

Datasets:

```text
1,000 messages
10,000 messages
100,000 messages
```

Measure:

* First page.
* Older page.
* Conversation list.
* Unread count.
* Search result navigation.
* Local message rendering.

Pagination shall remain stable as data grows.

---

# Chapter 3052 — Attachment Performance Tests

Measure:

```text
Local encryption throughput
Upload throughput
Server disk write throughput
Download throughput
Local decryption throughput
Resume overhead
CPU use
Memory use
```

Test multiple chunk sizes before selecting the default.

---

# Chapter 3053 — Database Performance Tests

Use:

```sql
EXPLAIN ANALYZE
```

for important queries.

Required query categories:

```text
Conversation list
Message pagination
User search
Active memberships
Unread count
Audit filtering
Outbox claim
Session cleanup
Attachment lookup
```

Query plans shall use intended indexes.

---

# Chapter 3054 — WebSocket Performance Tests

Measure:

```text
Maximum practical concurrent test connections
Connection establishment rate
Heartbeat processing
Event fan-out latency
Memory per connection
Send-failure recovery
```

The target shall reflect the expected small organisational deployment rather than Internet-scale assumptions.

---

# Chapter 3055 — Synchronisation Performance Tests

Measure:

```text
Initial sync with 100 conversations
Initial sync with 1,000 conversations
Incremental sync with 100 events
Replay with 10,000 events
Full resync with 100,000 cached messages
Queue replay with 100 actions
```

The GUI shall remain responsive.

---

# Chapter 3056 — Performance Acceptance Targets

Final targets shall be defined after baseline measurement.

Example starting targets:

```text
Typical login:

Under 3 seconds on LAN

Direct message stored:

Under 1 second

Realtime recipient event:

Under 1 second after commit

Conversation first page:

Under 500 milliseconds server-side

Local cached search:

Under 1 second for typical query

Dashboard:

Under 2 seconds

Client GUI blocking:

No visible freeze longer than 100 milliseconds for normal interaction
```

These values shall be adjusted to the actual environment and justified.

---

# Chapter 3057 — Load-Test Safety

Load tests shall run only in isolated environments.

They shall not:

* Use production directory accounts.
* Fill production storage.
* Trigger production rate limits.
* Pollute production audit records.
* Expose synthetic passwords publicly.
* Cause denial of service to real users.

---

# Chapter 3058 — Reliability-Test Purpose

Reliability tests shall verify behaviour during:

* Dependency restart.
* Process crash.
* Network loss.
* Disk pressure.
* Timeouts.
* Partial writes.
* Duplicate delivery.
* Long offline periods.
* Clock changes.
* Worker failures.

---

# Chapter 3059 — Dependency Restart Tests

Restart individually:

```text
PostgreSQL
Redis
Nginx
FastAPI service
Attachment mount
Directory service where possible
```

Verify:

* Health state.
* User-visible state.
* Retry behaviour.
* Recovery.
* No data corruption.
* No duplicate message.
* No lost draft.

---

# Chapter 3060 — Server Process Crash Tests

Simulate crash:

```text
Before transaction commit
After transaction commit
Before outbox publication
During worker batch
During upload
During graceful-shutdown timeout
```

Verify PostgreSQL transaction guarantees and recovery.

---

# Chapter 3061 — Client Process Crash Tests

Simulate crash:

```text
During login
During draft save
During send
After server acknowledgement
During upload
During download
During sync
During local migration
```

Verify local recovery and idempotency.

---

# Chapter 3062 — Disk-Full Tests

Simulate full or nearly full:

```text
Server attachment storage
Server root filesystem
PostgreSQL storage
Client cache storage
Client download destination
Client temporary preparation directory
```

Expected behaviour:

* Safe error.
* No corrupt completion.
* No uncontrolled crash.
* Clear health state.
* Recoverable pending work where possible.

---

# Chapter 3063 — Time-Related Tests

Test:

```text
Access-token expiry
Refresh-token expiry
Edit-window boundary
Announcement expiry
Upload-session expiry
Retention boundary
Offline-duration expiry
Certificate expiry warning
Clock moving backwards
Clock moving forwards
```

Use injected clocks where possible.

---

# Chapter 3064 — Backup-Test Purpose

Backups are valid only if restoration succeeds.

Testing shall cover:

```text
PostgreSQL backup
Attachment backup
Configuration backup
Secret-backup procedure where applicable
Restore
Consistency validation
Audit-chain validation
```

---

# Chapter 3065 — Backup Creation Tests

Verify:

* Backup command exits successfully.
* Output exists.
* Output checksum recorded.
* Output is protected.
* Expected tables included.
* Attachment files included.
* Configuration included without unsafe exposure.
* Failure is reported accurately.

---

# Chapter 3066 — Restore Tests

Restore into a clean isolated environment.

Verify:

```text
Schema revision
Users
Sessions according to restore policy
Conversations
Messages
Recipient envelopes
Attachments
Audit chain
Outbox records
Configuration versions
Announcements
```

Run the release smoke test afterwards.

---

# Chapter 3067 — Point-in-Time Consistency Tests

Where database and attachment backups are separate, verify that restored metadata does not reference missing attachment files unexpectedly.

The backup procedure shall define:

* Ordering.
* Snapshot method.
* Maintenance requirements.
* Reconciliation after restore.

---

# Chapter 3068 — Deployment-Test Purpose

Deployment tests shall verify the documented installation and operational procedures.

They shall use clean environments.

Required areas:

* Server installation.
* Client installation.
* Upgrade.
* Rollback.
* Service startup.
* Firewall.
* TLS.
* Permissions.
* Uninstallation.

---

# Chapter 3069 — Clean Debian Installation Test

Starting from a clean Debian VM:

```text
Follow installation guide exactly

Install PostgreSQL

Install Redis

Create service account

Create directories

Install application

Apply migrations

Configure Nginx

Configure TLS

Start service

Run health checks

Connect client
```

Every undocumented prerequisite shall be treated as a documentation defect.

---

# Chapter 3070 — systemd Tests

Verify:

```text
Starts on boot
Stops cleanly
Restarts after configured failure
Runs as dedicated user
Uses expected working directory
Reads expected environment files
Cannot write outside required paths where hardening applies
Logs to intended destination
```

---

# Chapter 3071 — Firewall and Exposure Tests

From another LAN device, scan the server.

Expected:

```text
HTTPS exposed
Optional SSH exposed only according to deployment
PostgreSQL not exposed
Redis not exposed
Internal FastAPI port not exposed
Unexpected development ports closed
```

---

# Chapter 3072 — Windows Installer Tests

Verify on clean Windows:

```text
Installs without Python
Creates application shortcut
Installs required resources
Starts client
Stores profile in correct location
Uses Windows Credential Manager
Uninstaller works
Upgrade preserves profile
Repair behaves correctly where supported
```

---

# Chapter 3073 — Upgrade Tests

Required:

```text
Install Version A
Create representative data
Upgrade to Version B
Apply server migrations
Open client profile
Apply client migrations
Send message
Download attachment
Verify audit
Verify offline queue
```

No supported data shall be lost.

---

# Chapter 3074 — Rollback Tests

Rollback procedure shall verify:

* Previous application starts.
* Database compatibility is understood.
* Backup restore works where reverse migration is unsafe.
* Attachment data remains consistent.
* Client compatibility is documented.
* Audit history remains intact.

Rollback shall not be claimed unless tested.

---

# Chapter 3075 — Usability-Test Purpose

Usability testing shall determine whether representative users can complete common tasks effectively.

It shall measure:

* Task success.
* Time.
* Errors.
* Requests for help.
* Misunderstandings.
* Satisfaction.
* Accessibility barriers.

---

# Chapter 3076 — Usability Participants

Where possible, include:

```text
A typical employee user
A technically confident user
A less technically confident user
A helpdesk-style administrator
An accessibility-focused tester
```

Participants shall use synthetic accounts and data.

---

# Chapter 3077 — Usability Test Tasks

Core tasks:

```text
Log in
Find a contact
Start direct conversation
Send message
Reply
Edit message
Create group
Send attachment
Find old message
Mute conversation
Resolve failed message
Run diagnostics
Manage session
Log out
```

Administrative tasks shall be tested separately.

---

# Chapter 3078 — Usability Observation Record

Record:

```text
Task
Completed without help
Time taken
Incorrect actions
Points of hesitation
Error messages encountered
User comments
Suggested change
Priority
```

Observers shall avoid helping unless the test protocol allows it.

---

# Chapter 3079 — Usability Acceptance

The release shall not require all users to be perfect.

However:

* Core tasks should be discoverable.
* Error recovery should be understandable.
* Terminology should remain consistent.
* Destructive actions should be clear.
* Security warnings should be comprehensible.
* Repeated major confusion shall be corrected.

---

# Chapter 3080 — Manual Security Review

A manual reviewer shall inspect:

```text
Authentication flow
Token lifecycle
Permission enforcement
Cryptographic boundaries
Private-key storage
Logging
File paths
Configuration
Audit integrity
Offline limitations
Administrative controls
Deployment exposure
```

The review shall produce findings and resolutions.

---

# Chapter 3081 — Manual Database Review

Review:

```text
Foreign keys
Delete behaviour
Unique constraints
Check constraints
Indexes
Soft deletion
Audit restrictions
Role privileges
Migration order
Outbox consistency
Attachment references
```

---

# Chapter 3082 — Manual Interface Review

Review:

```text
All buttons functional
No placeholder controls
No clipped text
No inaccessible icon-only buttons
No plaintext in debug widgets
Consistent terminology
Accurate connection state
Accurate pending state
Clear destructive confirmations
Correct role visibility
```

---

# Chapter 3083 — Manual Deployment Review

Review:

```text
Service permissions
Secret-file permissions
Database network binding
Redis network binding
Nginx proxy headers
TLS settings
Firewall
Backup destination
Log permissions
Attachment mount ownership
Upgrade documentation
Emergency recovery
```

---

# Chapter 3084 — Acceptance-Test Categories

Final acceptance shall include:

```text
Functional acceptance
Security acceptance
Reliability acceptance
Performance acceptance
Usability acceptance
Accessibility acceptance
Operational acceptance
Documentation acceptance
```

Failure in a critical category blocks release.

---

# Chapter 3085 — Functional Acceptance Matrix

Mandatory functional scenarios:

```text
AUTH-01

User authenticates.

AUTH-02

User logs out and session becomes invalid.

CONTACT-01

User finds and adds contact.

CONV-01

Direct conversation created without duplicate.

GROUP-01

Group created with owner.

GROUP-02

Ownership transfers safely.

MSG-01

Direct encrypted message sent and received.

MSG-02

Group encrypted message sent and received.

MSG-03

Message edited.

MSG-04

Message deleted.

MSG-05

Read state updates.

ATTACH-01

Encrypted attachment transfers.

OFFLINE-01

Queued message sends once after reconnect.

SEARCH-01

Cached message search returns result.

ADMIN-01

Administrator disables user.

AUDIT-01

Administrative action appears in audit.

MONITOR-01

Dashboard reports dependency failure.
```

---

# Chapter 3086 — Security Acceptance Matrix

Mandatory:

```text
SEC-01

Server message plaintext marker absent.

SEC-02

Server attachment plaintext marker absent.

SEC-03

Private key never transmitted.

SEC-04

Wrong recipient cannot decrypt.

SEC-05

Modified message fails verification.

SEC-06

Revoked session rejected.

SEC-07

Employee denied admin route.

SEC-08

Path traversal rejected.

SEC-09

Secrets absent from diagnostic package.

SEC-10

Audit tampering detected.

SEC-11

TLS certificate failure blocks connection.

SEC-12

Removed member receives no future envelope.
```

---

# Chapter 3087 — Reliability Acceptance Matrix

Mandatory:

```text
REL-01

Client restart preserves draft.

REL-02

Client crash after server commit creates no duplicate.

REL-03

Server restart preserves messages.

REL-04

Interrupted upload resumes.

REL-05

Interrupted download resumes.

REL-06

Redis restart recovers transient features.

REL-07

Expired event cursor triggers resync.

REL-08

Migration preserves data.

REL-09

Backup restores successfully.

REL-10

Graceful shutdown completes.
```

---

# Chapter 3088 — Accessibility Acceptance Matrix

Mandatory:

```text
ACC-01

Login works by keyboard.

ACC-02

Conversation can be selected by keyboard.

ACC-03

Message can be sent by keyboard.

ACC-04

Icon controls have accessible names.

ACC-05

Focus indicator visible.

ACC-06

High-contrast theme usable.

ACC-07

150% font scale usable.

ACC-08

Errors move focus appropriately.

ACC-09

Colour is not sole state indicator.

ACC-10

Dialogs maintain correct focus.
```

---

# Chapter 3089 — Performance Acceptance Matrix

Final measured criteria shall include:

```text
PERF-01

Login within target.

PERF-02

Direct message send within target.

PERF-03

Recipient event within target.

PERF-04

Conversation page within target.

PERF-05

Search within target.

PERF-06

Attachment throughput acceptable.

PERF-07

Memory remains bounded during large transfer.

PERF-08

Dashboard within target.

PERF-09

Reconnect sync within target.

PERF-10

GUI remains responsive.
```

---

# Chapter 3090 — Operational Acceptance Matrix

Mandatory:

```text
OPS-01

Clean server install succeeds.

OPS-02

Service starts on boot.

OPS-03

Only intended ports exposed.

OPS-04

Health endpoints accurate.

OPS-05

Backup succeeds.

OPS-06

Restore succeeds.

OPS-07

Upgrade succeeds.

OPS-08

Rollback procedure succeeds.

OPS-09

Certificate warning works.

OPS-10

Emergency administrator recovery documented and tested.
```

---

# Chapter 3091 — Test Evidence Types

Suitable evidence:

```text
Automated test output
Coverage report
Screenshots
Screen recordings
Database query result
Audit record
Network trace with sensitive values redacted
Performance graph
Log excerpt
Hash comparison
Installation transcript
User observation form
```

Evidence shall not expose real secrets or private data.

---

# Chapter 3092 — Screenshot Evidence Rules

Screenshots shall:

* Use synthetic data.
* Hide passwords.
* Hide tokens.
* Hide private keys.
* Hide real IP addresses where unnecessary.
* Include enough context to understand the result.
* Be labelled with test ID.
* Avoid excessive cropping that removes relevant state.

---

# Chapter 3093 — Log Evidence Rules

Log extracts shall:

* Include timestamp.
* Include correlation ID where relevant.
* Include safe event code.
* Exclude secrets.
* Exclude plaintext messages.
* Exclude private paths where unnecessary.
* State the environment.

---

# Chapter 3094 — Failed Test Handling

When a test fails:

```text
Record actual result.

Create defect reference.

Classify severity.

Identify root cause.

Correct implementation or requirement.

Add regression test.

Rerun failed test.

Run affected regression suite.

Record retest evidence.
```

A failed result shall not be removed from the development record.

---

# Chapter 3095 — Defect Identifier Convention

Recommended:

```text
DEF-<SUBSYSTEM>-<NUMBER>
```

Examples:

```text
DEF-AUTH-003
DEF-GUI-011
DEF-ATTACH-007
```

A defect record shall include:

* Description.
* Severity.
* Reproduction.
* Cause.
* Correction.
* Test added.
* Retest result.

---

# Chapter 3096 — Regression Suite

The regression suite shall always include:

```text
Authentication
Token refresh
Permission enforcement
Direct message
Group message
Message edit and delete
Attachment round trip
Offline queue replay
Audit append
Audit verification
User disable
Client draft persistence
Configuration loading
```

Critical regression tests shall run before every release candidate.

---

# Chapter 3097 — Release-Test Order

Recommended release verification order:

```text
Static checks

↓

Unit tests

↓

Repository tests

↓

Integration tests

↓

Cryptographic tests

↓

Security tests

↓

GUI tests

↓

End-to-end tests

↓

Performance tests

↓

Deployment tests

↓

Backup and restore

↓

Manual acceptance
```

A critical failure stops release preparation until corrected.

---

# Chapter 3098 — Fast Developer Test Set

The fast local test set should include:

```text
Unit tests
Shared contract tests
Domain tests
Configuration tests
Cryptographic unit tests
ViewModel tests
Architecture tests
```

Target execution time should remain short enough for frequent use.

---

# Chapter 3099 — Continuous Integration Test Set

A CI environment should run:

```text
Static checks
Unit tests
PostgreSQL repository tests
Redis integration tests
API tests
Cryptographic tests
Security-pattern scans
Package build
```

GUI and full deployment tests may run in dedicated jobs.

---

# Chapter 3100 — Nightly or Scheduled Test Set

Suitable scheduled tests:

```text
Full integration suite
LDAP tests
GUI suite
Large-file tests
Performance baselines
Long offline recovery
Audit full verification
Backup and restore
Dependency vulnerability scan
```

For a single-developer NEA, these may be run manually on a defined schedule.

---

# Chapter 3101 — Test Flakiness Policy

A flaky test shall not be ignored.

Process:

* Record frequency.
* Identify race or environmental cause.
* Remove dependence on arbitrary sleeps.
* Use deterministic synchronisation.
* Improve cleanup.
* Fix or temporarily quarantine with documented defect.
* Restore before release.

Repeated rerunning until success is not acceptable evidence.

---

# Chapter 3102 — Async Test Rules

Async tests shall:

* Use one supported event-loop test approach.
* Await all created tasks.
* Cancel owned tasks during cleanup.
* Avoid arbitrary long sleeps.
* Use events or barriers for concurrency.
* Detect unhandled task exceptions.
* Close clients and connections.

---

# Chapter 3103 — Timeouts in Tests

Every infrastructure test shall have a bounded timeout.

A hanging test is a failure.

Timeouts shall be generous enough for the environment but shall not mask deadlocks.

---

# Chapter 3104 — Temporary Resource Cleanup

Tests shall clean:

```text
Temporary databases
Redis keys
Temporary files
Upload directories
Download files
Windows credentials created for tests
Background tasks
WebSocket connections
Test users
```

Cleanup shall run even after test failure where possible.

---

# Chapter 3105 — Test Account Isolation

Each test should use unique identifiers or a clean dataset.

Tests shall not depend on execution order.

Parallel tests shall not share mutable user or conversation records unless testing concurrency intentionally.

---

# Chapter 3106 — Mocking External Services

Mock only the external boundary when testing service logic.

Examples:

```text
Mock LDAP provider, not AuthenticationService internals.

Mock FileStorage, not every private AttachmentService helper.

Mock WebSocket publisher, not MessagingService validation.

Mock operating-system secure store in client unit tests.
```

Integration tests shall use real adapters.

---

# Chapter 3107 — Test Coverage Reports

Coverage reports shall identify:

* Untested files.
* Untested branches.
* Security-critical gaps.
* Error-handling gaps.
* Deferred code.

Coverage exclusions shall be documented and minimal.

---

# Chapter 3108 — Branch Coverage

Branch coverage is particularly important for:

```text
Permission rules
Error mapping
State transitions
Retry classification
Conflict resolution
Key selection
Health-state calculation
Maintenance guards
```

High line coverage with untested error branches is insufficient.

---

# Chapter 3109 — Mutation Testing

Mutation testing is recommended for critical modules:

```text
Permissions
State transitions
Canonicalisation
Cryptographic validation
Token validation
Idempotency
Audit-chain verification
```

Surviving mutations shall be reviewed to identify weak assertions.

---

# Chapter 3110 — Test Documentation

The testing documentation shall include:

```text
Testing strategy
Environment setup
How to run tests
Fixture design
Test-data policy
Coverage summary
Acceptance matrix
Performance results
Security results
Usability results
Known untested areas
```

---

# Chapter 3111 — Known Untested Areas

Any area not fully tested shall be listed explicitly.

Example:

```text
Hardware-backed key protection not implemented.

Very large 2 GiB file tested only through scaled automated case and one manual full-size test.

Multi-device behaviour excluded from Version 1.0.

Public Internet deployment not supported or tested.
```

No untested limitation shall be hidden.

---

# Chapter 3112 — Testing Completion Criteria

Testing is complete for Version 1.0 when:

```text
All mandatory automated suites pass.

All release-critical security tests pass.

All cryptographic vectors pass.

Server plaintext absence tests pass.

All mandatory acceptance scenarios pass.

No critical or high defect remains.

Performance targets are measured and acceptable.

Accessibility acceptance tests pass.

Clean installation succeeds.

Upgrade and rollback succeed.

Backup and restore succeed.

Test evidence is recorded.

Known limitations are documented.
```

---

# Chapter 3113 — Simplified Version 1.0 Test Scope

Version 1.0 shall include automated coverage for:

```text
Configuration
Domain models
Repositories
Transactions
Authentication
Sessions
Permissions
Users
Contacts
Public keys
Conversations
Groups
Messages
Cryptography
Attachments
WebSockets
Redis
Offline queue
Synchronisation
Conflict handling
Audit
Administration
Monitoring
Workers
Client storage
ViewModels
Core GUI interaction
Deployment validation
```

Manual coverage shall include:

```text
Accessibility
Usability
Clean installation
Windows packaging
Backup restore
Performance
Final acceptance
```

---

# Chapter 3114 — Testing Summary

BlueBubbles shall use a layered testing strategy rather than relying on one demonstration.

Unit tests shall verify domain rules, validation, permissions, cryptographic helpers, state transitions and ViewModels.

Repository and migration tests shall use real PostgreSQL.

Redis and LDAP behaviour shall be tested against controlled integration environments.

REST and WebSocket tests shall verify authentication, authorisation, schemas, errors, rate limits, event delivery and reconnection.

Cryptographic tests shall verify:

* Approved algorithms.
* Correct key and nonce sizes.
* Canonical serialisation.
* Recipient isolation.
* Signatures.
* Authentication tags.
* Key rotation.
* Local encryption.
* Attachment manifests.
* Deterministic test vectors.

Release-critical plaintext-marker tests shall confirm that message and attachment plaintext does not appear in server-controlled persistence, logs, diagnostics, exports or test backups.

Offline and synchronisation tests shall verify idempotency, crash recovery, membership changes, key changes, event gaps and conflict preservation.

GUI testing shall cover controls, focus, keyboard use, themes, scaling, loading, errors and administrative visibility.

Performance tests shall record hardware, dataset and measured results.

Deployment tests shall prove installation, upgrade, rollback, firewall, service startup and Windows packaging.

Backup testing shall include restoration into a clean environment.

Every mandatory requirement shall map to at least one test and final evidence item.

Version 1.0 shall not be released with known critical or high defects or with failed security, backup, migration or acceptance gates.

---

# End of Part 28

Part 29 will define the complete deployment, installation, upgrade, backup, restore and operational runbook specification, including:

* Debian server preparation.
* PostgreSQL and Redis installation.
* Service-account creation.
* Storage layout.
* Nginx and TLS.
* systemd.
* Firewall rules.
* Active Directory connectivity.
* Windows client packaging.
* Initial administrator setup.
* Backup jobs.
* Restore procedures.
* Upgrade and rollback.
* Maintenance.
* Emergency recovery.
