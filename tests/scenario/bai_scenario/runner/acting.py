"""Calling as a user the scenario laid.

Both ways of driving a scenario need this: the table's runner, and a plain test that
seeds through fixtures. It lives apart from either so there is one answer to what a
seeded user looks like to the code under test.
"""

from __future__ import annotations

from contextlib import AbstractContextManager

from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.manager.data.domain.types import UserInfo
from ai.backend.manager.data.user.types import UserData as SeededUser


class ActingAs:
    """One seeded user, in the two shapes the code under test asks for."""

    _user: SeededUser
    _entered: AbstractContextManager[None] | None

    def __init__(self, user: SeededUser) -> None:
        self._user = user
        self._entered = None

    def context(self) -> UserData:
        """What ``with_user`` needs: the request-context view of the user."""
        return UserData(
            user_id=self._user.id,
            is_authorized=True,
            is_admin=self._user.role in (UserRole.ADMIN, UserRole.SUPERADMIN),
            is_superadmin=self._user.role == UserRole.SUPERADMIN,
            role=self._user.role,
            domain_name=self._user.domain_name,
            domain_id=self._user.domain_id,
        )

    def info(self) -> UserInfo:
        """What an adapter method taking the caller beside the DTO wants."""
        return UserInfo(id=self._user.id, role=self._user.role, domain_name=self._user.domain_name)

    def __enter__(self) -> UserInfo:
        entered = with_user(self.context())
        entered.__enter__()
        self._entered = entered
        return self.info()

    def __exit__(self, *exc: object) -> None:
        if self._entered is not None:
            self._entered.__exit__(None, None, None)
            self._entered = None
