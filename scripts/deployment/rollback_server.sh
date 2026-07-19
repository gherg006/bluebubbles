#!/bin/sh
set -eu

if [ "$#" -ne 2 ] || [ "$1" != "--previous-release" ]; then
    echo "Usage: rollback_server.sh --previous-release ABSOLUTE_RELEASE_DIRECTORY" >&2
    exit 2
fi
previous="$2"
case "$previous" in /opt/bluebubbles/releases/*) ;; *) echo "Previous release must be below /opt/bluebubbles/releases." >&2; exit 2 ;; esac
if [ ! -d "$previous" ] || [ ! -f "$previous/pyproject.toml" ] || \
   [ ! -f "$previous/deployment/server-requirements.txt" ]; then
    echo "Previous release is incomplete." >&2
    exit 1
fi
echo "This performs application-only rollback and is unsafe after an incompatible database migration." >&2
systemctl stop bluebubbles.service
ln -sfn "$previous" /opt/bluebubbles/current.new
mv -Tf /opt/bluebubbles/current.new /opt/bluebubbles/current
/opt/bluebubbles/shared/venv/bin/python -m pip install \
    --requirement "$previous/deployment/server-requirements.txt"
/opt/bluebubbles/shared/venv/bin/python -m pip install \
    --no-build-isolation --no-deps "$previous"
/opt/bluebubbles/shared/venv/bin/python -m pip check
systemctl start bluebubbles.service
curl --fail --silent --show-error --max-time 10 http://127.0.0.1:8000/health/live >/dev/null
curl --fail --silent --show-error --max-time 30 http://127.0.0.1:8000/health/ready >/dev/null
echo "Application-only rollback completed; run the authenticated smoke test and record the decision."
