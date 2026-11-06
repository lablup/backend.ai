from __future__ import annotations

from dataclasses import dataclass
from http import HTTPStatus

import pytest

from ai.backend.common.exception import BackendAIError
from ai.backend.manager.errors.auth import AuthenticationRequired, SuperadminRequired


@dataclass(frozen=True)
class _RejectionErrorCase:
    error_class: type[BackendAIError]
    expected_status: HTTPStatus
    expected_code: str


@pytest.mark.parametrize(
    "case",
    [
        _RejectionErrorCase(
            error_class=SuperadminRequired,
            expected_status=HTTPStatus.FORBIDDEN,
            expected_code="user_access_forbidden",
        ),
        _RejectionErrorCase(
            error_class=AuthenticationRequired,
            expected_status=HTTPStatus.UNAUTHORIZED,
            expected_code="user_access_unauthorized",
        ),
    ],
    ids=lambda case: case.error_class.__name__,
)
def test_rejection_error_reports_its_status_and_code(case: _RejectionErrorCase) -> None:
    error = case.error_class()

    assert error.status_code == case.expected_status
    assert str(error.error_code()) == case.expected_code
