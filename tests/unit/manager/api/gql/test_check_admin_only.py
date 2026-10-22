from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ai.backend.common.exception import BackendAIError
from ai.backend.manager.api.gql.utils import check_admin_only
from ai.backend.manager.errors.auth import InsufficientPrivilege


def _user(*, is_superadmin: bool) -> MagicMock:
    me = MagicMock()
    me.is_superadmin = is_superadmin
    return me


def test_a_superadmin_passes() -> None:
    with patch(
        "ai.backend.manager.api.gql.utils.current_user", return_value=_user(is_superadmin=True)
    ):
        check_admin_only()


@pytest.mark.parametrize(
    "caller",
    [
        pytest.param(None, id="anonymous"),
        pytest.param(_user(is_superadmin=False), id="non-admin"),
    ],
)
def test_everyone_else_is_refused(caller: MagicMock | None) -> None:
    with patch("ai.backend.manager.api.gql.utils.current_user", return_value=caller):
        with pytest.raises(InsufficientPrivilege):
            check_admin_only()


def test_the_refusal_is_a_client_error_the_handler_can_recognise() -> None:
    """The GraphQL handler logs 4xx quietly only for `BackendAIError`.

    Refusing with anything else lands in its catch-all, where an ordinary
    permission check is recorded as an unexpected error, stack trace and all.
    """
    with patch("ai.backend.manager.api.gql.utils.current_user", return_value=None):
        with pytest.raises(BackendAIError) as exc_info:
            check_admin_only()

    assert exc_info.value.status_code // 100 == 4
