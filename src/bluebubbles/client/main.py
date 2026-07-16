"""Command-line entry point for the BlueBubbles desktop client."""

import sys

from bluebubbles.client.application import create_application
from bluebubbles.shared.logging import configure_logging


def main() -> None:
    """Construct the desktop client and exit with its event-loop status."""
    configure_logging()
    application = create_application(sys.argv)
    raise SystemExit(application.run())


if __name__ == "__main__":
    main()
