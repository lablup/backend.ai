from __future__ import annotations

import uuid
from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.contexts.user import with_user_context
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.common.dto.manager.v2.session_lifecycle_handler.response import (
    ListSessionLifecycleHandlersPayload,
    SessionLifecycleHandlerNode,
)
from ai.backend.manager.api.gql.session_lifecycle_handler.resolver import (
    admin_session_lifecycle_handlers,
)
from ai.backend.manager.errors.auth import InsufficientPrivilege


def _user_with_role(role: UserRole) -> UserData:
    return UserData(
        user_id=uuid.uuid4(),
        is_authorized=True,
        is_admin=role in (UserRole.SUPERADMIN, UserRole.ADMIN),
        is_superadmin=role is UserRole.SUPERADMIN,
        role=role,
        domain_name="default",
        domain_id=DomainID(uuid.uuid4()),
    )


@dataclass(frozen=True)
class _RefusedCallerCase:
    caller_kind: str
    caller: UserData | None


class TestAdminSessionLifecycleHandlers:
    @pytest.fixture
    def handler_nodes(self) -> list[SessionLifecycleHandlerNode]:
        return [
            SessionLifecycleHandlerNode(
                name="check-precondition",
                description="Checks that scheduled sessions are ready to start.",
            ),
            SessionLifecycleHandlerNode(
                name="terminate-sessions",
                description="Terminates the kernels of sessions marked for termination.",
            ),
        ]

    @pytest.fixture
    def info(self, handler_nodes: list[SessionLifecycleHandlerNode]) -> MagicMock:
        info = MagicMock()
        info.context.adapters.session_lifecycle_handler.list_session_lifecycle_handlers = AsyncMock(
            return_value=ListSessionLifecycleHandlersPayload(items=handler_nodes)
        )
        return info

    @pytest.fixture
    def superadmin(self) -> UserData:
        return _user_with_role(UserRole.SUPERADMIN)

    @pytest.mark.parametrize(
        "case",
        [
            _RefusedCallerCase(caller_kind="anonymous", caller=None),
            _RefusedCallerCase(caller_kind="user", caller=_user_with_role(UserRole.USER)),
            _RefusedCallerCase(caller_kind="domain-admin", caller=_user_with_role(UserRole.ADMIN)),
            _RefusedCallerCase(caller_kind="monitor", caller=_user_with_role(UserRole.MONITOR)),
        ],
        ids=lambda case: case.caller_kind,
    )
    async def test_everyone_but_a_superadmin_is_refused_before_the_read(
        self, info: MagicMock, case: _RefusedCallerCase
    ) -> None:
        with with_user_context(case.caller), pytest.raises(InsufficientPrivilege):
            await admin_session_lifecycle_handlers.base_resolver(info)

        info.context.adapters.session_lifecycle_handler.list_session_lifecycle_handlers.assert_not_awaited()

    async def test_a_superadmin_gets_every_handler_as_a_node(
        self,
        info: MagicMock,
        handler_nodes: list[SessionLifecycleHandlerNode],
        superadmin: UserData,
    ) -> None:
        with with_user_context(superadmin):
            result = await admin_session_lifecycle_handlers.base_resolver(info)

        assert result is not None
        assert [
            SessionLifecycleHandlerNode(name=node.name, description=node.description)
            for node in result
        ] == handler_nodes
