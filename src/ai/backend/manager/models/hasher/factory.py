"""
Factory for creating password hasher instances.
"""

from __future__ import annotations

import logging

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm

from .base import PasswordHasher
from .bcrypt import BcryptHasher
from .pbkdf2 import PBKDF2_SHA3_256Hasher, PBKDF2_SHA256Hasher
from .sha import SHA3_256Hasher, SHA256Hasher

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


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
