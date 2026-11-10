"""
Column type that stores a password as its hash.
"""

from __future__ import annotations

from typing import Any, override

from sqlalchemy.types import VARCHAR, TypeDecorator

from ai.backend.common.auth.password import PasswordInfo
from ai.backend.manager.models.hasher.factory import PasswordHasherFactory


class PasswordColumn(TypeDecorator[str]):
    """Custom column type that prevents direct password assignment.

    Passwords should be set using proper functions that have access to config:
    - Use explicit UPDATE queries with pre-hashed passwords

    This column type is kept for backward compatibility but should not be used
    for setting passwords directly.
    """

    impl = VARCHAR
    cache_ok = True

    @override
    def process_bind_param(self, value: Any, _dialect: Any) -> str | None:
        if value is None:
            return None

        if not isinstance(value, PasswordInfo):
            raise ValueError("Password must be set using PasswordInfo for hashing.")

        hash_info = PasswordHasherFactory.get_hasher(value.algorithm).generate_new_hash(value)
        return hash_info.to_string()
