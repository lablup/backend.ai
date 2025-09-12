"""
Base classes for password hashing algorithms.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .types import HashInfo, PasswordInfo


class PasswordHasher(ABC):
    """Abstract base class for password hashing algorithms."""

    @abstractmethod
    def generate_new_hash(self, password_info: PasswordInfo) -> HashInfo:
        """Generate a new hash for a password with the given information.

        Args:
            password_info: Contains password, algorithm, rounds, and salt_size

        Returns:
            HashInfo containing the algorithm, rounds, salt, and hash value
        """
        raise NotImplementedError

    @abstractmethod
    def verify(self, password: str, hash_info: HashInfo) -> bool:
        """Verify a password against stored hash information.

        Args:
            password: Plain text password to verify
            hash_info: Parsed information from stored hash

        Returns:
            True if password matches, False otherwise
        """
        raise NotImplementedError
