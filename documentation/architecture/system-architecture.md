# BlueBubbles Version 1.0 architecture

BlueBubbles is a LAN-only encrypted messaging design. PostgreSQL is authoritative,
Redis is transient, the Debian server routes ciphertext and metadata, and plaintext
plus identity private keys belong only to authorised Windows clients. The diagrams
below describe the implemented components and explicitly show the current unbound
desktop-backend seam.

## 1. System context

```mermaid
flowchart LR
    employee["Employee on Windows client"] -->|"HTTPS/WSS over LAN"| server["BlueBubbles Debian server"]
    administrator["Administrator on Windows client"] -->|"HTTPS/WSS over LAN"| server
    server --> ad["Active Directory / LDAP"]
    server --> postgres["PostgreSQL ciphertext and metadata"]
    server --> redis["Redis transient state"]
    server --> storage["Encrypted attachment storage"]
```

Trust boundary: users trust their local Windows profile and server TLS identity;
they do not trust the server with message/file plaintext or identity private keys.

## 2. Deployment

```mermaid
flowchart TB
    client["Windows 11 client\nPySide6 executable"] -->|"TCP 443 HTTPS/WSS"| nginx["Nginx TLS boundary"]
    nginx -->|"loopback 127.0.0.1:8000"| fastapi["FastAPI under systemd"]
    fastapi -->|"loopback 5432"| postgres["PostgreSQL"]
    fastapi -->|"loopback 6379"| redis["Redis"]
    fastapi --> attachments["Persistent encrypted attachment volume"]
    backup["systemd backup timer"] --> postgres
    backup --> attachments
    backup --> vault["Separate backup destination"]
```

Only 443 is required from client networks. SSH is management-only; ports 5432,
6379, and 8000 must not be reachable from the LAN.

## 3. Server components

```mermaid
flowchart LR
    routes["FastAPI routes / WebSocket endpoint"] --> services["Application services"]
    services --> protocols["Repository and provider protocols"]
    protocols --> adapters["SQLAlchemy / LDAP / Redis / file adapters"]
    adapters --> infra["PostgreSQL, AD, Redis, encrypted files"]
    services --> outbox["Durable outbox"]
    workers["Lifecycle-owned workers"] --> services
    monitoring["Health and metrics"] --> infra
```

Routes authenticate and translate transport data; services authorise and commit;
repositories never commit, encrypt, log plaintext, or emit UI.

## 4. Client components

```mermaid
flowchart LR
    widgets["PySide6 windows/widgets"] --> viewmodels["ViewModels"]
    viewmodels --> backend["UiBackend protocol"]
    backend -. "CURRENTLY UNBOUND IN PACKAGED APP" .-> services["Authentication, messaging, transfer, sync services"]
    services --> crypto["Client-only cryptography"]
    services --> network["HTTP/WebSocket adapters required"]
    services --> local["Encrypted SQLite/profile storage"]
    crypto --> keystore["Windows protected secret store"]
```

The dotted edge is release blocker `RC-CLIENT-001`: tests inject callback/fake
backends, but the executable constructs `UnavailableUiBackend`.

## 5. Authentication flow

```mermaid
sequenceDiagram
    participant C as Client
    participant S as FastAPI
    participant A as LDAP/local provider
    participant P as PostgreSQL
    participant R as Redis
    C->>S: POST /api/v1/auth/login
    S->>A: Validate credentials
    A-->>S: Provider-neutral identity
    S->>P: Create hashed-token session and audit/outbox records
    S->>R: Register revocation/rate state
    S-->>C: Access token, refresh token, profile, permissions
    Note over C: Password is discarded; tokens enter protected client storage
```

## 6. Message encryption flow

```mermaid
flowchart TD
    text["Plaintext in sender client"] --> key["Random AES-256-GCM message key + nonce"]
    key --> ciphertext["Encrypt canonical message payload"]
    recipients["Active recipient public-key versions"] --> envelopes["Seal one key envelope per recipient"]
    ciphertext --> signed["Sign canonical ciphertext envelope"]
    envelopes --> signed
    signed --> server["Server stores/forwards ciphertext only"]
    server --> recipient["Recipient verifies signature and tag, opens own envelope"]
    recipient --> output["Plaintext in recipient client"]
```

## 7. Message send sequence

```mermaid
sequenceDiagram
    participant A as Sender client
    participant S as Server service
    participant D as PostgreSQL
    participant O as Outbox worker
    participant B as Recipient client
    A->>A: Encrypt, envelope and sign
    A->>S: Idempotent SendMessageRequest
    S->>D: Lock membership, store ciphertext + outbox, commit
    S-->>A: Stored response
    O->>D: Claim durable outbox event
    O-->>B: Recipient-filtered WebSocket event
    B->>B: Verify, decrypt and cache
    B->>S: Delivery/read acknowledgement
```

## 8. Attachment upload

```mermaid
sequenceDiagram
    participant C as Client
    participant S as Server
    participant F as Encrypted file store
    C->>C: Hash plaintext; create key and per-chunk nonces
    C->>S: Create encrypted upload manifest
    S-->>C: Missing chunk indexes
    loop missing chunks only
        C->>C: Encrypt and authenticate bounded chunk
        C->>S: Upload ciphertext chunk
        S->>F: Atomically store verified ciphertext
    end
    C->>S: Complete upload
    S-->>C: Authoritative encrypted attachment record
```

## 9. Attachment download

```mermaid
sequenceDiagram
    participant C as Authorised client
    participant S as Server
    participant F as Encrypted file store
    C->>S: Request manifest and missing chunks
    S->>S: Recheck active conversation membership
    loop required chunks
        S->>F: Read ciphertext
        S-->>C: Ciphertext chunk
        C->>C: Verify tag, decrypt, stream to temporary file
    end
    C->>C: Verify final plaintext SHA-256
    C->>C: Atomic rename to safe filename
```

## 10. Offline replay

```mermaid
flowchart TD
    action["User action while offline"] --> encrypt["Prepare encrypted payload and stable UUID"]
    encrypt --> queue["Persist ordered encrypted action"]
    queue --> reconnect["Connectivity restored"]
    reconnect --> deps{"Dependencies satisfied?"}
    deps -->|No| blocked["Keep blocked; preserve recovery state"]
    deps -->|Yes| submit["Submit exactly once with idempotency key"]
    submit --> result{"Server result"}
    result -->|Stored/already stored| remove["Commit local state then remove queue item"]
    result -->|Retryable| backoff["Bounded retry schedule"]
    result -->|Conflict/forbidden| preserve["Preserve attempted content and explain recovery"]
```

## 11. Database entity relationships

```mermaid
erDiagram
    USERS ||--o{ SESSIONS : owns
    USERS ||--o{ PUBLIC_KEYS : publishes
    USERS ||--o{ CONTACTS : owns
    USERS ||--o{ CONVERSATION_MEMBERS : joins
    CONVERSATIONS ||--o{ CONVERSATION_MEMBERS : contains
    CONVERSATIONS ||--o{ MESSAGES : contains
    USERS ||--o{ MESSAGES : sends
    MESSAGES ||--o{ MESSAGE_RECIPIENTS : envelopes
    MESSAGES ||--o{ ATTACHMENTS : references
    ATTACHMENTS ||--o{ ATTACHMENT_CHUNKS : contains
    USERS ||--o{ AUDIT_EVENTS : acts
    MESSAGES ||--o{ OUTBOX_EVENTS : publishes
```

The exact columns, constraints, and migration revisions are documented in
`documentation/development/database-schema-and-migrations.md`.

## 12. Audit-chain flow

```mermaid
flowchart LR
    metadata["Canonical safe audit metadata"] --> previous["Previous entry hash"]
    previous --> digest["SHA-256 chain digest"]
    digest --> insert["Append-only audit row"]
    insert --> verify["Recompute sequence and links"]
    verify -->|Mismatch| alert["Critical security alert"]
    verify -->|Valid| healthy["Audit health evidence"]
```

The runtime database role receives `SELECT` and `INSERT`, never audit update/delete.

## 13. Backup and restore

```mermaid
flowchart TD
    quiesce["Coordinate consistent backup window"] --> dump["pg_dump authoritative database"]
    quiesce --> files["Copy encrypted attachments and configuration"]
    dump --> manifest["Sizes + SHA-256 backup manifest"]
    files --> manifest
    manifest --> separate["Transfer to separate protected destination"]
    separate --> clean["Restore into clean isolated environment"]
    clean --> migrations["Confirm database revision compatibility"]
    migrations --> smoke["Audit verification + full smoke test"]
```

Backup command success without clean restore and application verification is not
accepted evidence.
