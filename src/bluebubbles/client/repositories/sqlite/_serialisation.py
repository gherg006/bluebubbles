"""Canonical JSON helpers for locally encrypted repository payloads."""

import json
from typing import Any


def encode_json(value: dict[str, Any]) -> bytes:
    """Return stable UTF-8 JSON bytes for encryption."""
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def decode_json(value: bytes) -> dict[str, Any]:
    """Decode a validated JSON object after authenticated decryption."""
    parsed = json.loads(value.decode("utf-8"))
    if not isinstance(parsed, dict):
        raise ValueError("Encrypted local record must contain a JSON object")
    return parsed
