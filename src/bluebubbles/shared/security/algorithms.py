"""Explicit, versioned cryptographic algorithm identifiers."""

from enum import StrEnum


class ContentEncryptionAlgorithm(StrEnum):
    """Approved algorithms for encrypted content payloads."""

    AES_256_GCM_V1 = "AES-256-GCM-V1"


class KeyEnvelopeAlgorithm(StrEnum):
    """Approved algorithms for per-recipient content-key envelopes."""

    X25519_HKDF_SHA256_AES_256_GCM_V1 = "X25519-HKDF-SHA256-AES-256-GCM-V1"


class SignatureAlgorithm(StrEnum):
    """Approved signature algorithms."""

    ED25519_V1 = "ED25519-V1"


class HashAlgorithm(StrEnum):
    """Approved hashing algorithms."""

    SHA256_V1 = "SHA256-V1"
