"""Command-line entry point for the BlueBubbles application server."""

import argparse
import json
from pathlib import Path

import uvicorn

from bluebubbles.server.application import create_application
from bluebubbles.server.configuration.loader import (
    ConfigurationLoader,
    redacted_server_configuration,
)
from bluebubbles.server.configuration.settings import EnvironmentName
from bluebubbles.shared.configuration import ConfigurationError
from bluebubbles.shared.logging import configure_logging

app = create_application()


def main() -> int:
    """Validate, safely display, or run the server configuration."""
    parser = argparse.ArgumentParser(prog="bluebubbles-server")
    parser.add_argument(
        "command",
        nargs="?",
        choices=("run", "validate-config", "show-config"),
        default="run",
    )
    parser.add_argument(
        "--environment",
        choices=tuple(environment.value for environment in EnvironmentName),
        help="Deployment profile (otherwise BLUEBUBBLES_ENVIRONMENT or development)",
    )
    parser.add_argument(
        "--config-directory",
        type=Path,
        help="Directory containing base.yaml and the selected profile YAML",
    )
    arguments = parser.parse_args()
    loader = ConfigurationLoader(config_directory=arguments.config_directory)
    try:
        settings = loader.load_server_settings(
            environment=(
                EnvironmentName(arguments.environment)
                if arguments.environment
                else None
            ),
            verify_files=arguments.command == "validate-config",
        )
    except ConfigurationError as error:
        parser.exit(2, f"Configuration error: {error}\n")
    configure_logging(settings.logging.level.value)
    if arguments.command == "validate-config":
        print("Server configuration is valid.")
        return 0
    if arguments.command == "show-config":
        print(json.dumps(redacted_server_configuration(settings), indent=2))
        return 0
    uvicorn.run(
        create_application(settings),
        host=settings.network.host,
        port=settings.network.port,
        ssl_certfile=(
            str(settings.tls.certificate_path) if settings.tls.enabled else None
        ),
        ssl_keyfile=(
            str(settings.tls.private_key_path) if settings.tls.enabled else None
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
