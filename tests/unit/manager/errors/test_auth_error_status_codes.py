"""Verify that manager auth error classes return correct HTTP status codes."""

from __future__ import annotations

import pytest

from ai.backend.manager.errors.auth import (
    AuthorizationFailed,
    EmailAlreadyExistsError,
    GroupMembershipNotFoundError,
    InsufficientPrivilege,
    InvalidAuthParameters,
    InvalidClientIPConfig,
    InvalidCredentials,
    LoginBlockedError,
    LoginClientTypeConflict,
    LoginClientTypeNotFound,
    LoginSessionExpiredError,
    LoginSessionNotFoundError,
    PasswordExpired,
    TooManyConcurrentLoginSessions,
    UserCreationError,
    UserNotFound,
)


@pytest.mark.parametrize(
    "error_cls, expected_status",
    [
        (InvalidCredentials, 400),
        (InsufficientPrivilege, 403),
        (InvalidAuthParameters, 400),
        (AuthorizationFailed, 401),
        (PasswordExpired, 401),
        (EmailAlreadyExistsError, 400),
        (UserCreationError, 500),
        (UserNotFound, 404),
        (GroupMembershipNotFoundError, 404),
        (InvalidClientIPConfig, 403),
        (LoginSessionNotFoundError, 404),
        (LoginSessionExpiredError, 401),
        (LoginBlockedError, 429),
        (LoginClientTypeNotFound, 404),
        (LoginClientTypeConflict, 409),
        (TooManyConcurrentLoginSessions, 409),
    ],
)
def test_auth_error_status_codes(error_cls: type, expected_status: int) -> None:
    err = error_cls()
    assert err.status_code == expected_status, (
        f"{error_cls.__name__} has status_code={err.status_code}, expected {expected_status}"
    )
