"""
PBKDF2-based password hashing implementation.
"""

from __future__ import annotations

import hashlib
import secrets

from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm

from .base import PasswordHasher
from .types import HashInfo, PasswordInfo


class PBKDF2_SHA256Hasher(PasswordHasher):
    """PBKDF2-SHA256 password hashing implementation."""

    def generate_new_hash(self, password_info: PasswordInfo) -> HashInfo:
        salt = secrets.token_bytes(password_info.salt_size)
        # Use hashlib.pbkdf2_hmac for standard PBKDF2
        hashed = hashlib.pbkdf2_hmac(
            "sha256", password_info.password.encode("utf-8"), salt, password_info.rounds
        )

        return HashInfo(
            algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
            rounds=password_info.rounds,
            salt=salt.hex(),
            hash_value=hashed.hex(),
        )

    def verify(self, password: str, hash_info: HashInfo) -> bool:
        if hash_info.algorithm != PasswordHashAlgorithm.PBKDF2_SHA256:
            return False
        if hash_info.rounds is None or hash_info.salt is None:
            return False

        try:
            salt = bytes.fromhex(hash_info.salt)
        except (ValueError, TypeError):
            return False

        # Hash the password with the same salt and rounds
        test_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, hash_info.rounds)

        return test_hash.hex() == hash_info.hash_value


class PBKDF2_SHA3_256Hasher(PasswordHasher):
    """PBKDF2-SHA3-256 password hashing implementation."""

    def generate_new_hash(self, password_info: PasswordInfo) -> HashInfo:
        salt = secrets.token_bytes(password_info.salt_size)
        # Use hashlib.pbkdf2_hmac with SHA3-256
        hashed = hashlib.pbkdf2_hmac(
            "sha3_256", password_info.password.encode("utf-8"), salt, password_info.rounds
        )

        return HashInfo(
            algorithm=PasswordHashAlgorithm.PBKDF2_SHA3_256,
            rounds=password_info.rounds,
            salt=salt.hex(),
            hash_value=hashed.hex(),
        )

    def verify(self, password: str, hash_info: HashInfo) -> bool:
        if hash_info.algorithm != PasswordHashAlgorithm.PBKDF2_SHA3_256:
            return False
        if hash_info.rounds is None or hash_info.salt is None:
            return False

        try:
            salt = bytes.fromhex(hash_info.salt)
        except (ValueError, TypeError):
            return False

        # Hash the password with the same salt and rounds
        test_hash = hashlib.pbkdf2_hmac(
            "sha3_256", password.encode("utf-8"), salt, hash_info.rounds
        )

        return test_hash.hex() == hash_info.hash_value
