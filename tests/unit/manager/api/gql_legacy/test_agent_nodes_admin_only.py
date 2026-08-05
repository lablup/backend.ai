"""
Regression test: agent_nodes must be restricted to superadmin only. (BA-5594)
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from enum import Enum, auto
from unittest.mock import MagicMock

import graphene
import pytest

from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.user import UserID
from ai.backend.manager.api.gql_legacy.agent import AgentNode
from ai.backend.manager.data.auth.types import AuthenticatedUser
from ai.backend.manager.data.permission.permission_defs import AgentPermission
from ai.backend.manager.data.resource.types import UserResourcePolicyData
from ai.backend.manager.models.rbac import SystemScope
from ai.backend.manager.models.user import UserRole


def _authenticated_user(role: UserRole) -> AuthenticatedUser:
    return AuthenticatedUser(
        uuid=UserID(uuid.uuid4()),
        email="test@example.com",
        role=role,
        domain_name="default",
        domain_id=DomainID(uuid.uuid4()),
        sudo_session_enabled=False,
        main_access_key=None,
        allowed_client_ip=None,
        resource_policy=UserResourcePolicyData(name="default"),
    )


class ExpectedResult(Enum):
    ALLOWED = auto()
    EMPTY = auto()


class TestAgentNodesAdminOnly:
    @pytest.fixture
    def make_info(self) -> Callable[..., MagicMock]:
        def _make(role: UserRole) -> graphene.ResolveInfo:
            ctx = MagicMock()
            ctx.user = _authenticated_user(role)
            info = MagicMock(spec=graphene.ResolveInfo)
            info.context = ctx
            return info

        return _make

    @pytest.mark.parametrize(
        ("role", "expected_result"),
        [
            (UserRole.USER, ExpectedResult.EMPTY),
            (UserRole.ADMIN, ExpectedResult.EMPTY),
            (UserRole.MONITOR, ExpectedResult.EMPTY),
        ],
    )
    async def test_non_superadmin_gets_empty_results(
        self,
        make_info: Callable[..., MagicMock],
        role: UserRole,
        expected_result: ExpectedResult,
    ) -> None:
        info = make_info(role)
        result = await AgentNode.get_connection(
            info,
            SystemScope(),
            AgentPermission.CREATE_COMPUTE_SESSION,
        )
        if expected_result == ExpectedResult.EMPTY:
            assert result.node_list == []
            assert result.total_count == 0
