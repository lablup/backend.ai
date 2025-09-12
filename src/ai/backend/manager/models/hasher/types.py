"""
Common types and data structures for password hashers.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Final, Optional

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

HASH_DELIMITER: Final[str] = "$"


@dataclass(frozen=True)
class HashInfo:
    """Parsed hash information from existing hashes."""

    algorithm: PasswordHashAlgorithm
    rounds: int
    salt: Optional[str]  # bcrypt includes salt in hash_value
    hash_value: str

    @classmethod
    def from_hash_string(cls, hashed: str) -> HashInfo:
        """
        Parse a hash string and detect its algorithm automatically.

        Args:
            hashed: The full hash string

        Returns:
            HashInfo if parsing successful, None otherwise
        """
        # Check if it's a bcrypt hash (Legacy compatibility)
        if hashed.startswith("$2"):
            return cls._parse_bcrypt(hashed)

        parts = hashed.split(HASH_DELIMITER)
        if len(parts) != 4:
            raise ValueError(f"Invalid hash format, expected 4 parts but got {len(parts)}...")
        algorithm_str = parts[0]
        algorithm = PasswordHashAlgorithm(algorithm_str)
        return cls._parse_delimited(parts, algorithm)

    @classmethod
    def _parse_delimited(cls, parts: list[str], algorithm: PasswordHashAlgorithm) -> HashInfo:
        rounds = int(parts[1])
        salt = parts[2]
        hash_value = parts[3]

        return HashInfo(algorithm=algorithm, rounds=rounds, salt=salt, hash_value=hash_value)

    @classmethod
    def _parse_bcrypt(cls, hashed: str) -> HashInfo:
        # Parse bcrypt format: $2b$12$salt...hash...
        # Split by $ to extract rounds properly
        parts = hashed.split(HASH_DELIMITER)
        if len(parts) < 4:
            raise ValueError(f"Invalid bcrypt format: {hashed[:20]}...")

        # parts[0] is empty (before first $)
        # parts[1] is version (2a, 2b, etc.)
        # parts[2] is rounds
        # parts[3] is salt+hash combined
        rounds = int(parts[2])

        # The full hash contains salt internally (bcrypt manages this)
        return HashInfo(
            algorithm=PasswordHashAlgorithm.BCRYPT, rounds=rounds, salt=None, hash_value=hashed
        )

    def to_string(self) -> str:
        """
        Convert HashInfo back to string format.

        Returns:
            Formatted hash string
        """
        if self.algorithm == PasswordHashAlgorithm.BCRYPT:
            # Bcrypt has its own format (Legacy compatibility)
            return self.hash_value

        # Build parts: algorithm$rounds$salt$hash
        parts = [self.algorithm.value, str(self.rounds), self.salt or "", self.hash_value]
        return HASH_DELIMITER.join(parts)


@dataclass(frozen=True)
class PasswordInfo:
    """
    Information required to hash a password.
    """

    password: str
    algorithm: PasswordHashAlgorithm
    rounds: int
    salt_size: int

    def generate_new_hash(self) -> HashInfo:
        from .factory import PasswordHasherFactory

        hasher = PasswordHasherFactory.get_hasher(self.algorithm)
        return hasher.generate_new_hash(self)

    def need_migration(self, hash_info: HashInfo) -> bool:
        """
        Determine if the current password info requires migration from existing hash info.

        Args:
            hash_info: Existing hash information to compare against

        Returns:
            True if migration is needed, False otherwise
        """
        if self.algorithm != hash_info.algorithm:
            return True
        if self.rounds != hash_info.rounds:
            return True
        return False
