#!/bin/sh
set -eu

usage() {
    echo "Usage: install_server.sh --check | --apply --release-root ABSOLUTE_PATH" >&2
}

mode=""
release_root=""
while [ "$#" -gt 0 ]; do
    case "$1" in
        --check) mode="check" ;;
        --apply) mode="apply" ;;
        --release-root) shift; release_root="${1:-}" ;;
        *) usage; exit 2 ;;
    esac
    shift
done

if [ "$(id -u)" -ne 0 ]; then
    echo "Installation must run as root." >&2
    exit 1
fi
if [ "$mode" = "check" ]; then
    command -v python3 >/dev/null
    command -v psql >/dev/null
    command -v redis-cli >/dev/null
    command -v nginx >/dev/null
    command -v curl >/dev/null
    python3 -c 'import sys; raise SystemExit(sys.version_info < (3, 13))'
    echo "Deployment prerequisites are present."
    exit 0
fi
if [ "$mode" != "apply" ] || [ -z "$release_root" ] || [ "${release_root#/}" = "$release_root" ]; then
    usage
    exit 2
fi
case "$release_root" in
    /opt/bluebubbles/releases/*) ;;
    *) echo "Release root must be below /opt/bluebubbles/releases." >&2; exit 2 ;;
esac
if [ ! -f "$release_root/pyproject.toml" ] || \
   [ ! -f "$release_root/deployment/server-requirements.txt" ] || \
   [ ! -d "$release_root/deployment/templates" ]; then
    echo "Release root is incomplete." >&2
    exit 1
fi

getent group bluebubbles >/dev/null 2>&1 || groupadd --system bluebubbles
id bluebubbles >/dev/null 2>&1 || useradd --system --gid bluebubbles --home-dir /opt/bluebubbles --shell /usr/sbin/nologin bluebubbles

install -d -o root -g bluebubbles -m 0750 /opt/bluebubbles /opt/bluebubbles/releases /opt/bluebubbles/shared
install -d -o root -g bluebubbles -m 0750 /etc/bluebubbles /etc/bluebubbles/secrets
install -d -o bluebubbles -g bluebubbles -m 0750 /var/lib/bluebubbles/attachments /var/lib/bluebubbles/temporary /var/lib/bluebubbles/exports /var/lib/bluebubbles/state
install -d -o bluebubbles -g bluebubbles -m 0750 /var/log/bluebubbles
install -d -o root -g root -m 0700 /var/backups/bluebubbles

if [ ! -x /opt/bluebubbles/shared/venv/bin/python ]; then
    python3 -m venv /opt/bluebubbles/shared/venv
fi
/opt/bluebubbles/shared/venv/bin/python -m pip install \
    --requirement "$release_root/deployment/server-requirements.txt"
/opt/bluebubbles/shared/venv/bin/python -m pip install \
    --no-build-isolation --no-deps "$release_root"
/opt/bluebubbles/shared/venv/bin/python -m pip check
ln -sfn "$release_root" /opt/bluebubbles/current.new
mv -Tf /opt/bluebubbles/current.new /opt/bluebubbles/current
install -o root -g bluebubbles -m 0640 "$release_root/deployment/templates/environment" /etc/bluebubbles/environment
if [ ! -e /etc/bluebubbles/production.yaml.example ]; then
    install -o root -g bluebubbles -m 0640 \
        "$release_root/config/server/production.example.yaml" \
        /etc/bluebubbles/production.yaml.example
fi
install -o root -g root -m 0644 "$release_root/deployment/templates/bluebubbles.service" /etc/systemd/system/bluebubbles.service
install -o root -g root -m 0644 "$release_root/deployment/templates/bluebubbles-backup.service" /etc/systemd/system/bluebubbles-backup.service
install -o root -g root -m 0644 "$release_root/deployment/templates/bluebubbles-backup.timer" /etc/systemd/system/bluebubbles-backup.timer
install -o root -g root -m 0644 "$release_root/deployment/templates/bluebubbles.logrotate" /etc/logrotate.d/bluebubbles
systemctl daemon-reload
systemctl enable bluebubbles.service bluebubbles-backup.timer
echo "Base installation complete. Configure protected secrets, PostgreSQL, Redis, Nginx, TLS, and production YAML before startup."
