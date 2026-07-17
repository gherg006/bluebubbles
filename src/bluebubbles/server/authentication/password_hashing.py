"""Argon2id local-password hashing with injectable security parameters."""

from dataclasses import dataclass

from argon2 import PasswordHasher as Argon2PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from argon2.low_level import Type
from pydantic import SecretStr


@dataclass(frozen=True, slots=True)
class PasswordHashingParameters:
    """Define understandable Argon2id cost and output parameters."""

    time_cost: int = 3
    memory_cost_kib: int = 65_536
    parallelism: int = 4
    hash_length: int = 32
    salt_length: int = 16

    def __post_init__(self) -> None:
        if (
            min(
                self.time_cost,
                self.memory_cost_kib,
                self.parallelism,
                self.hash_length,
                self.salt_length,
            )
            < 1
        ):
            raise ValueError("Argon2id parameters must be positive")


class PasswordHasher:
    """Hash and verify local-account passwords using Argon2id only."""

    def __init__(self, parameters: PasswordHashingParameters | None = None) -> None:
        selected = parameters or PasswordHashingParameters()
        self._hasher = Argon2PasswordHasher(
            time_cost=selected.time_cost,
            memory_cost=selected.memory_cost_kib,
            parallelism=selected.parallelism,
            hash_len=selected.hash_length,
            salt_len=selected.salt_length,
            type=Type.ID,
        )

    def hash_password(self, password: SecretStr) -> str:
        """Return a salted Argon2id verifier without retaining plaintext."""
        return self._hasher.hash(password.get_secret_value())

    def verify_password(self, password: SecretStr, encoded_hash: str) -> bool:
        """Return whether a password matches, treating malformed hashes as failure."""
        try:
            return self._hasher.verify(encoded_hash, password.get_secret_value())
        except (InvalidHashError, VerificationError, VerifyMismatchError):
            return False

    def requires_rehash(self, encoded_hash: str) -> bool:
        """Return whether a valid verifier uses obsolete cost parameters."""
        try:
            return self._hasher.check_needs_rehash(encoded_hash)
        except InvalidHashError:
            return True

    def needs_rehash(self, encoded_hash: str) -> bool:
        """Provide the specification's compatibility spelling."""
        return self.requires_rehash(encoded_hash)

    def rehash_password(self, password: SecretStr) -> str:
        """Create a replacement verifier using current parameters."""
        return self.hash_password(password)
