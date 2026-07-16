"""Command-line entry point for the BlueBubbles desktop client."""

import sys

from bluebubbles.client.application import create_application
from bluebubbles.client.configuration.loader import ClientConfigurationLoader
from bluebubbles.shared.logging import configure_logging


def main() -> None:
    """Construct the desktop client and exit with its event-loop status."""
    settings = ClientConfigurationLoader().load_client_settings()
    configure_logging(settings.logging.level)
    application = create_application(sys.argv, settings)
    raise SystemExit(application.run())


if __name__ == "__main__":
    main()
