"""Tests for ``BcryptHasher.verify`` on a password longer than bcrypt reads."""

from __future__ import annotations

from unittest.mock import patch

import bcrypt
import pytest

from ai.backend.common.auth.password import HashInfo
from ai.backend.manager.models.hasher.bcrypt import BcryptHasher

_LONG_PASSWORD = "a" * 72 + "tail"


def _checkpw_refusing_long_passwords(password: bytes, hashed_password: bytes) -> bool:
    """``bcrypt.checkpw`` as bcrypt 5.0 answers: more than 72 bytes raise."""
    if len(password) > 72:
        raise ValueError("password cannot be longer than 72 bytes")
    return bcrypt.hashpw(password, hashed_password) == hashed_password


class TestBcryptHasherVerify:
    @pytest.fixture
    def hasher(self) -> BcryptHasher:
        return BcryptHasher()

    @pytest.fixture
    def hash_of_long_password(self) -> HashInfo:
        """A hash bcrypt 4.x stored for a password over 72 bytes."""
        stored = bcrypt.hashpw(_LONG_PASSWORD.encode("utf8")[:72], bcrypt.gensalt(rounds=4))
        return HashInfo.from_hash_string(stored.decode("utf8"))

    def test_a_password_over_72_bytes_matches_the_hash_stored_for_it(
        self, hasher: BcryptHasher, hash_of_long_password: HashInfo
    ) -> None:
        assert hasher.verify(_LONG_PASSWORD, hash_of_long_password)

    def test_it_still_matches_under_a_bcrypt_that_refuses_long_passwords(
        self, hasher: BcryptHasher, hash_of_long_password: HashInfo
    ) -> None:
        with patch.object(bcrypt, "checkpw", _checkpw_refusing_long_passwords):
            matched = hasher.verify(_LONG_PASSWORD, hash_of_long_password)

        assert matched

    def test_a_password_differing_within_72_bytes_does_not_match(
        self, hasher: BcryptHasher, hash_of_long_password: HashInfo
    ) -> None:
        assert not hasher.verify("b" + _LONG_PASSWORD[1:], hash_of_long_password)
