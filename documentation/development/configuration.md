# Configuration and LAN deployment

BlueBubbles loads and validates all configuration before either executable
starts. Server code reads only `ServerSettings`; client code reads only
`ClientSettings`. Raw environment variables and YAML files are confined to the
two configuration loaders.

## Deployment split

The Debian virtual machine runs only:

```text
bluebubbles-server validate-config
bluebubbles-server run
```

Windows workstations run only:

```text
bluebubbles-client
```

The default managed client endpoint is `192.168.0.210:8443`. This is a private
LAN address, but the network is still treated as untrusted: production clients
require HTTPS, secure WebSockets, and certificate verification.

## Server configuration on Debian

Server YAML is under `config/server`:

- `base.yaml` contains safe shared values.
- `development.yaml`, `testing.yaml`, and `demonstration.yaml` override a
  selected non-production profile.
- `production.example.yaml` is a non-secret deployment template.

Do not edit the example into a committed production file. Copy it into a
protected deployment directory as `production.yaml`, alongside a reviewed
`base.yaml`, and pass that directory to the command.
Set:

```text
BLUEBUBBLES_ENVIRONMENT=production
```

For example:

```text
bluebubbles-server validate-config --environment production --config-directory /etc/bluebubbles/config
bluebubbles-server run --environment production --config-directory /etc/bluebubbles/config
```

Production validation rejects debug mode, disabled TLS, local/mock
authentication, example signing material, SQL echoing, unsafe Redis namespaces,
and disabled log redaction. Referenced TLS and storage paths can be checked
without starting FastAPI:

```text
bluebubbles-server validate-config
```

The production example binds to `192.168.0.210`. If the VM receives a different
static address, change `network.host`. Keep port `8443` open only on the internal
LAN firewall; no Internet route or cloud dependency is required.

## Windows client configuration

`config/client/default.yaml` is installation configuration and targets:

```text
https://192.168.0.210:8443
wss://192.168.0.210:8443/ws
```

Use `managed.example.yaml` as the basis for an organisation-managed client
file. Distribute the organisation's internal CA certificate to Windows clients
and set `tls.trusted_ca_path`, or configure an administrator-approved SHA-256
certificate fingerprint. The client rejects plaintext production transports
and cannot disable certificate verification in production.

Client environment variables have the separate `BLUEBUBBLES_CLIENT_` prefix,
for example:

```text
BLUEBUBBLES_CLIENT_SERVER_URL=https://192.168.0.210:8443
BLUEBUBBLES_CLIENT_WEBSOCKET_URL=wss://192.168.0.210:8443/ws
BLUEBUBBLES_CLIENT_TRUSTED_CA=C:\ProgramData\BlueBubbles\internal-ca.crt
```

Server credentials are never loaded into the desktop client.

## Source precedence

Server values are resolved in this order, with later sources winning:

1. Model defaults.
2. `base.yaml`.
3. The selected environment YAML.
4. `BLUEBUBBLES_` environment variables.
5. Protected secret files.
6. Explicit startup overrides supplied by trusted application code.

Nested environment names use a double underscore, such as
`BLUEBUBBLES_NETWORK__PORT=8443`. Lists are JSON values and replace the entire
configured list. Unknown keys and invalid types stop startup rather than being
ignored.

Client values use model defaults, client YAML, `BLUEBUBBLES_CLIENT_` variables,
and explicit trusted overrides. User preferences are loaded separately and are
constrained by server policy through `EffectiveSettingsResolver`.

## Secrets

Prefer protected Debian files for secrets:

```text
BLUEBUBBLES_TOKEN_SECRET_FILE=/etc/bluebubbles/secrets/token-secret
BLUEBUBBLES_DATABASE_URL_FILE=/etc/bluebubbles/secrets/database-url
BLUEBUBBLES_REDIS_URL_FILE=/etc/bluebubbles/secrets/redis-url
BLUEBUBBLES_LDAP_BIND_PASSWORD_FILE=/etc/bluebubbles/secrets/ldap-bind-password
```

On Debian, these files must not be readable or writable by group or other users
(mode `0600` is suitable). Empty files are rejected. One trailing newline is
removed; all other content is preserved. Settings reports and validation errors
never include secret values.

To inspect effective non-secret configuration:

```text
bluebubbles-server show-config
```

Every `SecretStr` field is rendered as `**********`.

## Settings implemented in this stage

Server settings cover application identity, listener and WebSocket limits, TLS,
PostgreSQL, Redis, LDAP/Active Directory, authentication, token lifetimes,
storage, messages, attachments, rate limits, retention, logging, monitoring,
workers, fixed feature flags, and protocol compatibility.

Client settings cover application identity, REST/WebSocket endpoints, TLS
trust/pinning, retries, profile/cache storage, transfer limits, logging, local
feature availability, and supported protocols. Authenticated appearance,
notification, and transfer preferences remain separate from installation
configuration.
