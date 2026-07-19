# User guide

> The current 0.1.0 packaged client cannot authenticate because its production UI
> backend is not connected. This guide describes the implemented interface and
> required accepted behaviour, but it must not be issued to users until
> `RC-CLIENT-001` is closed and the release-candidate smoke test passes.

## Sign in safely

Start BlueBubbles from the Start menu. Confirm the server address is the approved
HTTPS hostname and Windows reports no certificate warning. Enter the organisation
username and password; BlueBubbles must never ask you to disable certificate
validation. Report unexpected fingerprint changes to support.

The login button becomes busy once. An error keeps the password field local and
does not reveal server internals. After successful authentication the password is
discarded; session secrets belong to Windows-protected storage.

## Contacts and conversations

Use Contacts to find an enabled directory user and add/remove the contact. Creating
a direct chat with the same user returns the existing canonical conversation. The
Chats list shows title, safe preview policy, timestamp, unread state, mute/pin, and
an explicit connectivity label.

For a group, supply a unique name and active members within the configured maximum.
The creator is owner. Owners can add/remove members, promote moderators, transfer
ownership, and leave only after another owner exists. Removed members receive no
future message envelopes or attachment access.

## Messages

Open a chat, type up to the organisation limit, and send. Pending, stored, failed,
delivered, and read states have text/icons rather than colour alone. A failed send
remains recoverable and retry uses the same identity to prevent duplicates.

Reply selects a target preview. Edit and delete are limited by server policy and
version checks; conflicts preserve attempted text. Deleted messages show a stable
placeholder. Never paste passwords, private keys, recovery codes, or unrelated
sensitive data into chat.

## Attachments

Select an allowed file within the configured maximum. The client encrypts and
uploads in bounded chunks. Transfer status distinguishes queued, active, paused,
failed, verifying, and complete. Interrupted transfers resume verified missing
chunks. Open a download only after the final checksum succeeds. Executable types
may be blocked by policy.

## Offline work

The connectivity banner shows starting, online, degraded, reconnecting, or offline.
Drafts and prepared actions are encrypted locally. On reconnect, actions replay in
order and only once. Membership changes, deleted resources, or edit conflicts may
require manual recovery; BlueBubbles must explain the outcome and preserve useful
attempted text.

## Search, settings and sessions

Search covers only authorised messages cached in the active local profile. It is
not a server-wide search and results can be incomplete after cache cleanup.
Settings include theme, high contrast, font scale, notification/privacy choices,
cache policy, transfer limits, and diagnostics. Server policy can override local
preferences and should explain the override.

The Sessions page lists devices without tokens. Revoke an unfamiliar session and
report it. Logout invalidates the server session before local in-memory secrets are
cleared. Logout does not necessarily erase encrypted cache unless the selected
policy says so.

## Accessibility

All core actions must be keyboard reachable with visible focus. Controls need
accessible names; errors must not rely on colour. Light, dark and high-contrast
themes and 100/125/150% scale must preserve readable dialogs, message wrapping,
composer controls, transfer progress, and administration tables. Report any core
workflow that cannot be completed using the keyboard or configured assistive tool.

## When to contact support

Stop and report: certificate warnings; unexpected key/fingerprint changes;
repeated refresh/login prompts; another user's content; missing queued work;
duplicate messages; successful download with wrong content; unexplained role/admin
access; or a request to send a password/private key. Diagnostics must be reviewed
for sensitive content before sharing.
