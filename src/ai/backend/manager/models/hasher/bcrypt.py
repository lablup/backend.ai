"""
Bcrypt password hashing implementation.
"""

from __future__ import annotations

from typing import override

import bcrypt

from ai.backend.common.auth.password import BCRYPT_MAX_PASSWORD_BYTES, HashInfo, PasswordInfo

from .base import PasswordHasher


class BcryptHasher(PasswordHasher):
    """Bcrypt password hashing implementation."""

    @override
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

    @override
    def verify(self, password: str, hash_info: HashInfo) -> bool:
        # A stored hash covers only the bytes bcrypt reads, so a longer password is cut to
        # them: bcrypt 4.x cuts it itself and 5.0 raises instead.
        try:
            # For bcrypt, the full hash is stored in hash_value
            return bcrypt.checkpw(
                password.encode("utf8")[:BCRYPT_MAX_PASSWORD_BYTES],
                hash_info.hash_value.encode("utf8"),
            )
        except (ValueError, Exception):
            # bcrypt.checkpw can raise ValueError or other exceptions
            return False
