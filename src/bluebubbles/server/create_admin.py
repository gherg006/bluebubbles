"""Interactive, password-safe initial administrator setup command."""

import argparse
import asyncio
from getpass import getpass
from pathlib import Path

from pydantic import SecretStr

from bluebubbles.server.authentication.ldap_provider import LDAPAuthenticationProvider
from bluebubbles.server.authentication.providers import LoginCredentials
from bluebubbles.server.bootstrap import build_server_container
from bluebubbles.server.configuration.loader import ConfigurationLoader
from bluebubbles.server.configuration.settings import (
    AuthenticationProviderName,
    EnvironmentName,
)
from bluebubbles.server.services.bootstrap_administration import (
    InitialAdministratorService,
)
from bluebubbles.shared.configuration import ConfigurationError


def main() -> int:
    """Collect confirmation and a hidden password before creating one account."""
    parser = argparse.ArgumentParser(prog="bluebubbles-create-admin")
    parser.add_argument(
        "--environment", choices=tuple(item.value for item in EnvironmentName)
    )
    parser.add_argument("--config-directory", type=Path)
    arguments = parser.parse_args()
    try:
        settings = ConfigurationLoader(
            config_directory=arguments.config_directory
        ).load_server_settings(
            environment=(
                EnvironmentName(arguments.environment)
                if arguments.environment
                else None
            ),
            verify_files=True,
        )
    except ConfigurationError as error:
        parser.exit(2, f"Configuration error: {error}\n")
    username = input("Username: ").strip()
    display_name = input("Display name: ").strip()
    password = getpass("Password (12+ characters): ")
    confirmation = getpass("Confirm password: ")
    if password != confirmation:
        parser.exit(2, "Passwords did not match.\n")
    if input(f"Type CREATE to create administrator {username!r}: ").strip() != "CREATE":
        parser.exit(2, "Creation cancelled.\n")

    async def create() -> str:
        container = build_server_container(settings)
        await container.database_manager.start()
        try:
            service = InitialAdministratorService(container.unit_of_work_factory)
            secret = SecretStr(password)
            if settings.authentication.provider is AuthenticationProviderName.DIRECTORY:
                identity = await LDAPAuthenticationProvider(
                    settings.directory
                ).authenticate(LoginCredentials(username=username, password=secret))
                return str(
                    await service.create_directory(identity, settings.authentication)
                )
            return str(
                await service.create_local(
                    username=username, display_name=display_name, password=secret
                )
            )
        finally:
            await container.database_manager.stop()

    identifier = asyncio.run(create())
    print(f"Initial administrator created with ID {identifier}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
