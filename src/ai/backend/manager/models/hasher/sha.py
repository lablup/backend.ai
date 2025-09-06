"""
SHA-based password hashing implementations.
"""

from __future__ import annotations

import hashlib
import secrets

from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm

from .base import PasswordHasher
from .types import HashInfo, PasswordInfo


class SHA256Hasher(PasswordHasher):
    """SHA-256 password hashing implementation with PBKDF2-like iterations."""

    def generate_new_hash(self, password_info: PasswordInfo) -> HashInfo:
        salt = secrets.token_bytes(password_info.salt_size).hex()
        hashed = password_info.password
        for _ in range(password_info.rounds):
            hashed = hashlib.sha256(f"{salt}{hashed}".encode()).hexdigest()

        return HashInfo(
            algorithm=PasswordHashAlgorithm.SHA256,
            rounds=password_info.rounds,
            salt=salt,
            hash_value=hashed,
        )

    def verify(self, password: str, hash_info: HashInfo) -> bool:
        if hash_info.algorithm != PasswordHashAlgorithm.SHA256:
            return False
        if hash_info.rounds is None or hash_info.salt is None:
            return False

        # Hash the password with the same salt and rounds
        test_password = password
        for _ in range(hash_info.rounds):
            test_password = hashlib.sha256(f"{hash_info.salt}{test_password}".encode()).hexdigest()

        return test_password == hash_info.hash_value


class SHA3_256Hasher(PasswordHasher):
    """SHA3-256 password hashing implementation with PBKDF2-like iterations."""

    def generate_new_hash(self, password_info: PasswordInfo) -> HashInfo:
        salt = secrets.token_bytes(password_info.salt_size).hex()
        hashed = password_info.password
        for _ in range(password_info.rounds):
            hashed = hashlib.sha3_256(f"{salt}{hashed}".encode()).hexdigest()

        return HashInfo(
            algorithm=PasswordHashAlgorithm.SHA3_256,
            rounds=password_info.rounds,
            salt=salt,
            hash_value=hashed,
        )

    def verify(self, password: str, hash_info: HashInfo) -> bool:
        if hash_info.algorithm != PasswordHashAlgorithm.SHA3_256:
            return False
        if hash_info.rounds is None or hash_info.salt is None:
            return False

        # Hash the password with the same salt and rounds
        test_password = password
        for _ in range(hash_info.rounds):
            test_password = hashlib.sha3_256(
                f"{hash_info.salt}{test_password}".encode()
            ).hexdigest()

        return test_password == hash_info.hash_value
