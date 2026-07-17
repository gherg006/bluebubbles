# Users, contacts, and public keys

Task 10 activates the existing user, contact, and public-key persistence through
authenticated services and thin REST routes. The server remains authoritative for
identity and key metadata, while private keys remain exclusively client-side.

## User profiles and search

`UserService` returns enabled, non-deleted profiles, performs bounded
case-insensitive directory searches, applies optional department filtering, and
updates only the authenticated user's display name, status message, and avatar
reference. Search uses opaque stable cursors. Role names are resolved from the
database and routes never compare role strings.

The API surface is:

```text
GET   /api/v1/users/search
GET   /api/v1/users/{user_id}
PATCH /api/v1/users/profile
GET   /api/v1/users/{user_id}/keys
```

## Directional contacts

Contacts are private, directional relationships. `ContactService` prevents self
contacts and duplicates, resolves additions by canonical username, and owns list,
nickname, favourite, block, unblock, and removal behavior. Blocking clears the
owner's favourite flag. Lists are ordered by favourite state, interaction weight,
and stable identity at the repository boundary.

Contact nicknames are owner-specific and are added by migration
`0003_contact_nicknames`. They are never copied to the target user's profile.

## Public identity keys

`PublicKeyService` accepts one public-only key revision at a time. Encryption and
signing keys rotate independently and permit only the Version 1 algorithms:

- X25519-V1 for encryption keys.
- ED25519-V1 for signing keys.

The service validates strict Base64 decoding, exact 32-byte key length, purpose to
algorithm matching, monotonically increasing versions, duplicate-version
conflicts, and the submitted fingerprint. The canonical fingerprint input is the
ASCII algorithm identifier, a zero byte, the ASCII key-purpose identifier, a zero
byte, the positive version encoded as an unsigned eight-byte big-endian integer, a
zero byte, and the raw public-key bytes; SHA-256 is formatted as sixteen uppercase
four-hexadecimal groups.

Only public key material is accepted or returned. Registration demotes the old
primary revision while retaining it for historical operations. Revocation marks a
revision unavailable for future use without deleting it. Expired or revoked keys
are excluded from active-key selection. Registration and revocation append safe
audit metadata and a `KEY_CHANGED` durable outbox fact in the same transaction, so
later WebSocket publication can occur only after commit.

```text
POST /api/v1/keys
POST /api/v1/keys/{key_id}/revoke
```

Private-key generation, encrypted local private-key storage, message encryption,
and client key-cache presentation remain in their later numbered stages.

## Verification

Deterministic tests cover safe profile retrieval and mutation, cursor search,
directional contact lifecycle and ownership, block behavior, fingerprint binding,
algorithm and version rejection, key rotation/history/revocation, durable facts,
route delegation, and SQLAlchemy persistence behavior. Real PostgreSQL migration
verification remains opt-in through `BLUEBUBBLES_TEST_DATABASE_URL`.
