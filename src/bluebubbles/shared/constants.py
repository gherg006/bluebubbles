"""Stable, non-secret constants shared by the client and server."""

from typing import Final

APPLICATION_NAME: Final = "BlueBubbles"
PROTOCOL_IDENTIFIER: Final = "bluebubbles"
DEFAULT_PROTOCOL_VERSION: Final = 1
SUPPORTED_PROTOCOL_VERSIONS: Final = (1,)
UUID_STRING_LENGTH: Final = 36
TIMESTAMP_FORMAT: Final = "RFC3339"
JSON_CONTENT_TYPE: Final = "application/json"
ENCRYPTED_BINARY_CONTENT_TYPE: Final = "application/octet-stream"
DEFAULT_PAGE_SIZE: Final = 50
MAX_PAGE_SIZE: Final = 250
MAX_DISPLAY_NAME_LENGTH: Final = 100
MAX_STATUS_LENGTH: Final = 280
MAX_GROUP_NAME_LENGTH: Final = 100
MAX_ANNOUNCEMENT_LENGTH: Final = 10_000
MAX_FILENAME_LENGTH: Final = 255
