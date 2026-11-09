"""Tests for the password length ``PasswordInfo`` takes for each hash algorithm."""

from __future__ import annotations

import pytest

from ai.backend.common.auth.password import PasswordHashAlgorithm, PasswordInfo
from ai.backend.common.exception import PasswordTooLong


def _password_info(password: str, algorithm: PasswordHashAlgorithm) -> PasswordInfo:
    return PasswordInfo(password=password, algorithm=algorithm, rounds=4, salt_size=32)


class TestPasswordInfo:
    @pytest.mark.parametrize(
        "password",
        ["a" * 72, "가" * 24],
        ids=["72 ascii bytes", "24 three-byte characters"],
    )
    def test_bcrypt_takes_a_password_of_72_bytes(self, password: str) -> None:
        password_info = _password_info(password, PasswordHashAlgorithm.BCRYPT)

        assert password_info.password == password

    @pytest.mark.parametrize(
        "password",
        ["a" * 73, "가" * 24 + "a"],
        ids=["73 ascii bytes", "24 three-byte characters and one more byte"],
    )
    def test_bcrypt_refuses_a_password_over_72_bytes(self, password: str) -> None:
        with pytest.raises(PasswordTooLong):
            _password_info(password, PasswordHashAlgorithm.BCRYPT)

    @pytest.mark.parametrize(
        "algorithm",
        [
            PasswordHashAlgorithm.SHA256,
            PasswordHashAlgorithm.SHA3_256,
            PasswordHashAlgorithm.PBKDF2_SHA256,
            PasswordHashAlgorithm.PBKDF2_SHA3_256,
        ],
    )
    def test_the_other_algorithms_take_a_password_over_72_bytes(
        self, algorithm: PasswordHashAlgorithm
    ) -> None:
        password_info = _password_info("a" * 200, algorithm)

        assert len(password_info.password) == 200
