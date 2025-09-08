"""
Bcrypt password hashing implementation.
"""

from __future__ import annotations

import bcrypt

from .base import PasswordHasher
from .types import HashInfo, PasswordInfo


class BcryptHasher(PasswordHasher):
    """Bcrypt password hashing implementation."""

    def generate_new_hash(self, password_info: PasswordInfo) -> HashInfo:
        # Note: bcrypt generates its own salt, so salt_size is ignored
        hash_value = bcrypt.hashpw(
            password_info.password.encode("utf8"), bcrypt.gensalt(rounds=password_info.rounds)
        ).decode("utf8")

        return HashInfo(
            algorithm=password_info.algorithm,
            rounds=password_info.rounds,
            salt=None,  # bcrypt includes salt in the hash
            hash_value=hash_value,
        )

    def verify(self, password: str, hash_info: HashInfo) -> bool:
        try:
            # For bcrypt, the full hash is stored in hash_value
            return bcrypt.checkpw(password.encode("utf8"), hash_info.hash_value.encode("utf8"))
        except (ValueError, Exception):
            # bcrypt.checkpw can raise ValueError or other exceptions
            return False
