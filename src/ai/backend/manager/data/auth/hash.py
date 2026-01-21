"""
Password hash algorithm enum definition.
"""

import enum


class PasswordHashAlgorithm(enum.StrEnum):
    """Supported password hash algorithms."""

    BCRYPT = "bcrypt"
    SHA256 = "sha256"
    SHA3_256 = "sha3_256"
    PBKDF2_SHA256 = "pbkdf2_sha256"
    PBKDF2_SHA3_256 = "pbkdf2_sha3_256"
