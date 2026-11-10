from __future__ import annotations

from collections.abc import Iterator
from uuid import uuid4

import pytest

from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.user.types import UserData, UserRole


@pytest.fixture
def caller_role() -> UserRole:
    return UserRole.SUPERADMIN


@pytest.fixture(autouse=True)
def caller_user_context(caller_role: UserRole) -> Iterator[UserData]:
    caller = UserData(
        user_id=uuid4(),
        is_authorized=True,
        is_admin=caller_role in (UserRole.SUPERADMIN, UserRole.ADMIN),
        is_superadmin=caller_role == UserRole.SUPERADMIN,
        role=caller_role,
        domain_name="default",
    )
    with with_user(caller):
        yield caller
