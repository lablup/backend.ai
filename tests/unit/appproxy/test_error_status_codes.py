"""
Verify that AppProxy error classes return correct HTTP status codes.

BackendAIError inherits from aiohttp.web.HTTPException which defaults
to status_code = -1. Each error class must also inherit from a concrete
HTTP exception (e.g. web.HTTPNotFound) to get a valid status code.
"""

import pytest

from ai.backend.appproxy.common.errors import (
    AuthorizationFailed,
    GenericBadRequest,
    GenericForbidden,
    InsufficientPrivilege,
    InternalServerError,
    InvalidAPIParameters,
    InvalidAuthParameters,
    InvalidCredentials,
    MethodNotAllowed,
    ObjectNotFound,
    PasswordExpired,
    QueryNotImplemented,
    ServerMisconfiguredError,
    ServiceUnavailable,
    URLNotFound,
)


@pytest.mark.parametrize(
    "error_cls, expected_status",
    [
        (URLNotFound, 404),
        (ObjectNotFound, 404),
        (GenericBadRequest, 400),
        (InvalidCredentials, 401),
        (AuthorizationFailed, 401),
        (PasswordExpired, 401),
        (GenericForbidden, 403),
        (InsufficientPrivilege, 403),
        (InvalidAuthParameters, 400),
        (InvalidAPIParameters, 400),
        (InternalServerError, 500),
        (ServerMisconfiguredError, 500),
        (ServiceUnavailable, 503),
        (QueryNotImplemented, 501),
    ],
)
def test_error_status_codes(error_cls: type, expected_status: int) -> None:
    err = error_cls()
    assert err.status_code == expected_status, (
        f"{error_cls.__name__} has status_code={err.status_code}, expected {expected_status}"
    )


def test_error_status_code_not_negative_one() -> None:
    """No AppProxy error should have the default -1 status code."""
    err = URLNotFound()
    assert err.status_code != -1


def test_method_not_allowed_with_extra_msg() -> None:
    err = MethodNotAllowed(
        extra_msg="Method GET not allowed",
        extra_data={"allowed_methods": ["POST"]},
    )
    assert err.status_code == 405
