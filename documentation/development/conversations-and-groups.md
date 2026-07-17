# Conversations and groups

Task 11 activates direct and group conversation metadata on the Task 10 identity
boundary. It deliberately does not store, inspect, or route message payloads; that
belongs to the encrypted messaging stage.

## Direct conversations

`ConversationService` creates exactly two active memberships, rejects self or
disabled targets, checks both directional contact blocks, and uses the canonical
pair table to guarantee one direct thread per user pair. An existing thread is
returned. If two creation requests race, the losing transaction rolls back and
retrieves the committed winner through a fresh Unit of Work.

Application permission is checked through `PermissionService`; request bodies never
supply the creator. Creation, memberships, structured activity, immutable audit
metadata, and a durable post-commit publication fact share one transaction.

## Groups and membership hierarchy

Groups require a validated name, at least two active members including the creator,
and no more than `messaging.maximum_group_members`. The creator is the sole owner.
Version 1 group roles are Owner, Moderator, and Member; organisational application
roles do not bypass this hierarchy.

`GroupService` enforces these rules:

- Owners and moderators may add enabled members, subject to the configured limit.
- A requester may remove only a strictly lower role; moderators can remove members
  but never an owner or another moderator.
- Only the owner may promote or demote moderators.
- Owners must explicitly transfer ownership before leaving.
- Ownership transfer demotes the old owner and promotes an active target in one
  committed transaction.
- Renaming and description changes require owner or moderator authority.

Migration `0004_group_moderator` changes the legacy persisted `admin` spelling to
the specification's `moderator` spelling while preserving a source-level enum alias
for compatibility.

Every group mutation writes both a safe structured conversation event and an
immutable audit-chain event. The same transaction writes a durable outbox fact for
later `GROUP_MEMBER_ADDED`, `GROUP_MEMBER_REMOVED`, `GROUP_ROLE_UPDATED`, or
`GROUP_UPDATED` publication. A removed member therefore disappears immediately
from PostgreSQL-authoritative access checks and cannot receive future events or
future message-key envelopes.

## Retrieval and preferences

Conversation retrieval requires active membership and returns bounded metadata and
participant summaries only. Lists use descending activity plus UUID cursor ordering
and never contain plaintext message previews. Archive state is stored per member,
so one user's archive choice cannot affect another participant.

The API surface is:

```text
GET  /api/v1/conversations
POST /api/v1/conversations/direct
POST /api/v1/conversations/group
GET  /api/v1/conversations/{conversation_id}
POST /api/v1/conversations/{conversation_id}/archive

PATCH  /api/v1/groups/{group_id}
POST   /api/v1/groups/{group_id}/members
DELETE /api/v1/groups/{group_id}/members/{user_id}
PATCH  /api/v1/groups/{group_id}/roles
POST   /api/v1/groups/{group_id}/leave
POST   /api/v1/groups/{group_id}/owner
```

## Verification

Tests cover new/reused direct threads, self/unknown/disabled/blocked rejection,
valid and oversized groups, membership-scoped retrieval, cursor lists, private
archiving, add/remove/leave, owner restrictions, moderator promotion/demotion,
strict removal hierarchy, ownership transfer, metadata updates, routes, repository
mapping, migrations, and durable event ordering. Encrypted message envelopes,
message history, recipient-key exclusion, WebSocket workers, and client storage are
verified in their later implementation stages.
