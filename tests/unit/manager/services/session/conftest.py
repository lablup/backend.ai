from __future__ import annotations

from collections.abc import Iterator
from uuid import uuid4

import pytest

from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.user.types import UserData
from ai.backend.manager.models.user import UserRole


@pytest.fixture(autouse=True)
def _user_context(request: pytest.FixtureRequest) -> Iterator[None]:
    """Set up a default authenticated user in the request context for service tests.

    Session service methods resolve the requester via current_user(); without this
    autouse fixture, tests calling such methods would fail because the auth
    middleware (which normally populates the context) is not exercised in unit
    tests.

    If the test defines a ``sample_user_id`` fixture, that UUID is used so that
    assertions referencing the same value continue to match.
    """
    try:
        user_id = request.getfixturevalue("sample_user_id")
    except pytest.FixtureLookupError:
        user_id = uuid4()
    with with_user(
        UserData(
            user_id=user_id,
            is_authorized=True,
            is_admin=False,
            is_superadmin=False,
            role=UserRole.USER,
            domain_name="default",
        )
    ):
        yield
