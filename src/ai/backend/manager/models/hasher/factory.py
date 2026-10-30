"""
Factory for creating password hasher instances.
"""

from __future__ import annotations

import logging

from ai.backend.common.auth.password import HashInfo, PasswordHashAlgorithm
from ai.backend.logging.structured import StructuredLogger

from .base import PasswordHasher
from .bcrypt import BcryptHasher
from .pbkdf2 import PBKDF2_SHA3_256Hasher, PBKDF2_SHA256Hasher
from .sha import SHA3_256Hasher, SHA256Hasher

log = StructuredLogger(logging.getLogger(__spec__.name))


class PasswordHasherFactory:
    """Factory for creating password hasher instances."""

    _hashers: dict[PasswordHashAlgorithm, PasswordHasher] = {
        PasswordHashAlgorithm.BCRYPT: BcryptHasher(),
        PasswordHashAlgorithm.SHA256: SHA256Hasher(),
        PasswordHashAlgorithm.SHA3_256: SHA3_256Hasher(),
        PasswordHashAlgorithm.PBKDF2_SHA256: PBKDF2_SHA256Hasher(),
        PasswordHashAlgorithm.PBKDF2_SHA3_256: PBKDF2_SHA3_256Hasher(),
    }

    @classmethod
    def get_hasher(cls, algorithm: PasswordHashAlgorithm) -> PasswordHasher:
        """Get a hasher instance for the specified algorithm."""
        hasher = cls._hashers.get(algorithm)
        if hasher is None:
            raise ValueError(f"Unsupported password hash algorithm: {algorithm}")
        return hasher


def compare_to_hashed_password(raw_password: str, hashed_password: str) -> bool:
    """Compare a raw string password value to hashed password."""
    hash_info = HashInfo.from_hash_string(hashed_password)
    hasher = PasswordHasherFactory.get_hasher(hash_info.algorithm)
    return hasher.verify(raw_password, hash_info)
