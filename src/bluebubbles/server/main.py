"""Command-line entry point for the BlueBubbles application server."""

import uvicorn

from bluebubbles.server.application import create_application
from bluebubbles.shared.logging import configure_logging

app = create_application()


def main() -> None:
    """Run the minimal server on the loopback interface for development."""
    configure_logging()
    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
