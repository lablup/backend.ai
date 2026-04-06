"""
Regression test: agents_v2 must be restricted to superadmin only. (BA-5594)
"""

from __future__ import annotations

import uuid
from enum import Enum, auto
from typing import NamedTuple
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import web

from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.user.types import UserData
from ai.backend.manager.api.gql.agent.resolver import agents_v2
from ai.backend.manager.models.user import UserRole


class ExpectedResult(Enum):
    ALLOWED = auto()
    FORBIDDEN = auto()


class RoleCase(NamedTuple):
    role: UserRole
    is_superadmin: bool
    expected: ExpectedResult


ROLE_CASES: list[RoleCase] = [
    RoleCase(UserRole.USER, is_superadmin=False, expected=ExpectedResult.FORBIDDEN),
    RoleCase(UserRole.ADMIN, is_superadmin=False, expected=ExpectedResult.FORBIDDEN),
    RoleCase(UserRole.MONITOR, is_superadmin=False, expected=ExpectedResult.FORBIDDEN),
    RoleCase(UserRole.SUPERADMIN, is_superadmin=True, expected=ExpectedResult.ALLOWED),
]


class TestAgentsV2AdminOnly:
    @pytest.fixture
    def mock_info(self) -> MagicMock:
        info = MagicMock()
        info.context.adapters.agent = AsyncMock()
        return info

    @pytest.mark.parametrize("case", ROLE_CASES, ids=lambda c: c.role.name)
    async def test_permission_check(
        self,
        mock_info: MagicMock,
        case: RoleCase,
    ) -> None:
        user = UserData(
            user_id=uuid.uuid4(),
            is_authorized=True,
            is_admin=case.is_superadmin,
            is_superadmin=case.is_superadmin,
            role=case.role,
            domain_name="default",
        )
        resolver_fn = agents_v2.base_resolver
        if case.expected == ExpectedResult.FORBIDDEN:
            with with_user(user), pytest.raises(web.HTTPForbidden):
                await resolver_fn(mock_info)
        else:
            with with_user(user):
                await resolver_fn(mock_info)
            mock_info.context.adapters.agent.admin_search.assert_awaited_once()
