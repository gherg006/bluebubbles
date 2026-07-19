# Active Directory integration guide

## Prerequisites

Use LDAPS on port 636 with a server certificate chaining to an internal CA trusted
by Debian. Create a dedicated read-only bind account denied interactive login. It
needs only the directory attributes/search bases required for user identity and
group membership. Never use Domain Administrator.

Choose stable values for base DN, user/group search bases, username (`sAMAccountName`
by default), immutable GUID (`objectGUID`), mail, department, title and membership
(`memberOf`). Create explicit security groups for BlueBubbles roles and document
the precedence when a user belongs to more than one mapped group.

## Protected bind secret

Write only the password to `/etc/bluebubbles/secrets/ldap_bind_password` using
`sudoedit`; set owner `root:bluebubbles`, mode `0640`. The environment file maps
`BLUEBUBBLES_LDAP_BIND_PASSWORD_FILE` to it. The DN belongs in YAML because it is
identity metadata, not a password.

## Production configuration

```yaml
directory:
  provider: active_directory
  server: dc01.internal.example
  port: 636
  use_tls: true
  bind_dn: CN=svc-bluebubbles,OU=Service Accounts,DC=internal,DC=example
  base_dn: DC=internal,DC=example
  user_search_base: OU=Users,DC=internal,DC=example
  group_search_base: OU=Groups,DC=internal,DC=example
  username_attribute: sAMAccountName
  guid_attribute: objectGUID
  email_attribute: mail
  department_attribute: department
  job_title_attribute: title
  group_membership_attribute: memberOf
  connection_timeout_seconds: 5
  search_timeout_seconds: 5
authentication:
  provider: directory
  allow_local_accounts: false
  default_role: Employee
  directory_group_role_mapping:
    CN=BlueBubbles-Helpdesk,OU=Groups,DC=internal,DC=example: Helpdesk
    CN=BlueBubbles-Administrators,OU=Groups,DC=internal,DC=example: Administrator
```

Keep a tightly protected local emergency administrator according to policy even
when normal local accounts are disabled. Validate configuration before restarting.

## Certificate and connectivity rehearsal

From Debian, verify DNS, time and the presented chain/hostname without printing the
bind password:

```sh
getent hosts dc01.internal.example
openssl s_client -connect dc01.internal.example:636 \
  -servername dc01.internal.example -verify_return_error </dev/null
```

Test a synthetic ordinary user, mapped helpdesk, mapped administrator, disabled
user, expired password, locked user, invalid password, missing attribute, duplicate
username search, unmapped group, nested-group policy, directory timeout, bad CA,
wrong hostname and server outage. Authentication failure messages must not reveal
whether a username exists or disclose LDAP diagnostics.

## Synchronisation and identity lifecycle

The directory owns mapped identity attributes. BlueBubbles maps the immutable GUID
to one local user and does not silently merge by display name/email. Sync creates or
updates safe profile metadata, records role changes, disables/deprovisions according
to policy, revokes affected sessions, and emits audit/outbox events. Directory
failure preserves the last authoritative local record but must not fabricate a
successful sync.

Review every role mapping before enabling it. An unrecognised group receives only
the configured default role. A group mapping must never grant SuperAdministrator
unless the organisation explicitly accepts that policy and tests lockout/recovery.

## Rotation and incident response

Rotate the bind password in Active Directory, update the protected file, validate,
restart during a controlled window, and verify directory health/login/sync. On
suspected compromise: disable the bind identity, preserve logs/audit metadata,
replace it, rotate the secret, review searches/role changes and sessions, then run a
full sync. Never copy LDAP packet captures containing credentials into project
evidence.
