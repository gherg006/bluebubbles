#!/bin/sh
set -eu

if [ "$#" -ne 4 ] || [ "$1" != "--archive" ] || [ "$3" != "--sha256" ]; then
    echo "Usage: upgrade_server.sh --archive ABSOLUTE_ARCHIVE --sha256 EXPECTED_SHA256" >&2
    exit 2
fi
archive="$2"
expected="$4"
case "$archive" in /*) ;; *) echo "Archive path must be absolute." >&2; exit 2 ;; esac
case "$expected" in *[!0-9a-f]*|'') echo "Expected SHA-256 must be lower-case hexadecimal." >&2; exit 2 ;; esac
if [ "${#expected}" -ne 64 ] || [ ! -f "$archive" ]; then
    echo "Archive or checksum is invalid." >&2
    exit 1
fi
actual="$(sha256sum "$archive" | cut -d ' ' -f 1)"
if [ "$actual" != "$expected" ]; then
    echo "Release checksum mismatch." >&2
    exit 1
fi
if ! python3 -c 'import json; from pathlib import Path; p=json.loads(Path("/var/lib/bluebubbles/state/backup-status.json").read_text()); raise SystemExit(not (p["successful"] and p["checksum_valid"]))'; then
    echo "A verified successful backup is required before upgrade." >&2
    exit 1
fi
version="$(basename "$archive" .tar.gz | sed 's/^bluebubbles-server-//')"
case "$version" in *[!A-Za-z0-9._-]*|'') echo "Unsafe release version." >&2; exit 1 ;; esac
destination="/opt/bluebubbles/releases/$version"
if [ -e "$destination" ]; then
    echo "Release destination already exists; refusing to overwrite it." >&2
    exit 1
fi
mkdir -m 0750 "$destination"
tar -xzf "$archive" --strip-components=1 -C "$destination"
/opt/bluebubbles/shared/venv/bin/python -m pip install \
    --requirement "$destination/deployment/server-requirements.txt"
/opt/bluebubbles/shared/venv/bin/python -m pip install \
    --no-build-isolation --no-deps "$destination"
/opt/bluebubbles/shared/venv/bin/python -m pip check
/opt/bluebubbles/shared/venv/bin/bluebubbles-server validate-config --environment production --config-directory /etc/bluebubbles
systemctl stop bluebubbles.service
if ! BLUEBUBBLES_DATABASE_URL_FILE=/etc/bluebubbles/secrets/database_url /opt/bluebubbles/shared/venv/bin/alembic -c "$destination/alembic.ini" upgrade head; then
    systemctl start bluebubbles.service || true
    echo "Migration failed; previous release remains selected." >&2
    exit 1
fi
ln -sfn "$destination" /opt/bluebubbles/current.new
mv -Tf /opt/bluebubbles/current.new /opt/bluebubbles/current
systemctl start bluebubbles.service
curl --fail --silent --show-error --max-time 10 http://127.0.0.1:8000/health/live >/dev/null
curl --fail --silent --show-error --max-time 30 http://127.0.0.1:8000/health/ready >/dev/null
echo "Upgrade activated. Complete the documented authenticated smoke test and observation period."
