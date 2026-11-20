"""ComputeSessionNode reads `compute_session_node(s)` within a scope through the new RBAC."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from unittest.mock import AsyncMock, MagicMock

import graphene
import pytest
import sqlalchemy as sa
from sqlalchemy.sql import visitors

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.permission.types import Permission
from ai.backend.manager.api.gql_legacy.session import ComputeSessionNode
from ai.backend.manager.data.permission.permission_defs import ComputeSessionPermission
from ai.backend.manager.models.endpoint.row import EndpointRow
from ai.backend.manager.models.rbac.base import DomainScope, ProjectScope, ScopeType, SystemScope
from ai.backend.manager.models.session.scopes import (
    DomainSessionTarget,
    ProjectSessionTarget,
    SessionTarget,
    UserSessionTarget,
)
from ai.backend.manager.models.user.row import UserRole
from ai.backend.manager.services.permission_contoller.actions.get_held_permissions import (
    ScopedGetHeldPermissionsAction,
    ScopedGetHeldPermissionsActionResult,
)

# Reachable only through string relationships of the session row's eager loads.
_ORM_CLUSTER = (EndpointRow,)

_CALLER_ID = UserID(uuid.UUID("00000000-0000-0000-0000-0000000000c1"))
_DOMAIN_ID = DomainID(uuid.UUID("00000000-0000-0000-0000-0000000000d1"))
_PROJECT_ID = ProjectID(uuid.UUID("00000000-0000-0000-0000-0000000000e1"))
_SESSION_ID = uuid.UUID("00000000-0000-0000-0000-0000000000a1")


def _bound_values(clause: sa.ColumnElement[bool]) -> set[object]:
    """The values a WHERE clause binds, so a scope is found by the id it names."""
    return {
        element.value
        for element in visitors.iterate(clause)
        if isinstance(element, sa.BindParameter)
    }


class TestComputeSessionNodeScopeCondition:
    @pytest.fixture
    def db_session(self) -> MagicMock:
        session = MagicMock()
        session.scalar = AsyncMock(return_value=None)
        session.scalars = AsyncMock(return_value=MagicMock(all=MagicMock(return_value=[])))
        return session

    @pytest.fixture
    def held_permissions(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def enforcement_enabled(self) -> bool:
        return True

    @pytest.fixture
    def make_info(
        self, db_session: MagicMock, held_permissions: AsyncMock, enforcement_enabled: bool
    ) -> Callable[[UserRole], graphene.ResolveInfo]:
        def _make(role: UserRole) -> graphene.ResolveInfo:
            ctx = MagicMock()
            ctx.user = {"role": role, "domain_name": "default", "uuid": _CALLER_ID}
            ctx.db.begin_readonly_session_read_committed = MagicMock(
                return_value=AsyncMock(
                    __aenter__=AsyncMock(return_value=db_session),
                    __aexit__=AsyncMock(return_value=None),
                )
            )
            ctx.scheduler_repository.get_domain_id_by_name = AsyncMock(return_value=_DOMAIN_ID)
            ctx.processors.permission_controller.scoped_get_held_permissions.run = held_permissions
            ctx.config_provider.config.manager.rbac.enforcement_enabled = enforcement_enabled
            ctx.config_provider.config.api.max_gql_connection_page_size = None
            info = MagicMock(spec=graphene.ResolveInfo)
            info.context = ctx
            return info

        return _make

    def _grant(self, held_permissions: AsyncMock, held: dict[SessionTarget, Permission]) -> None:
        async def _run(
            action: ScopedGetHeldPermissionsAction,
        ) -> ScopedGetHeldPermissionsActionResult:
            by_scope = {target.scope_id(): bits for target, bits in held.items()}
            return ScopedGetHeldPermissionsActionResult(
                granted={key: by_scope.get(key.scope, Permission.NONE) for key in action.keys}
            )

        held_permissions.side_effect = _run

    async def _where(
        self,
        make_info: Callable[[UserRole], graphene.ResolveInfo],
        db_session: MagicMock,
        role: UserRole,
        scope_id: ScopeType,
    ) -> sa.ColumnElement[bool]:
        node = await ComputeSessionNode.get_accessible_node(
            make_info(role),
            ("ComputeSessionNode", str(_SESSION_ID)),
            scope_id,
            ComputeSessionPermission.READ_ATTRIBUTE,
        )
        assert node is None
        stmt: sa.Select[tuple[object]] = db_session.scalar.await_args.args[0]
        assert stmt.whereclause is not None
        return stmt.whereclause

    async def test_a_superadmin_in_the_system_scope_reads_every_session(
        self,
        make_info: Callable[[UserRole], graphene.ResolveInfo],
        db_session: MagicMock,
        held_permissions: AsyncMock,
    ) -> None:
        where = await self._where(make_info, db_session, UserRole.SUPERADMIN, SystemScope())

        assert "EXISTS" not in str(where)

    async def test_a_superadmin_in_a_domain_reads_the_domain_sessions(
        self,
        make_info: Callable[[UserRole], graphene.ResolveInfo],
        db_session: MagicMock,
        held_permissions: AsyncMock,
    ) -> None:
        where = await self._where(
            make_info, db_session, UserRole.SUPERADMIN, DomainScope("default")
        )

        assert _DOMAIN_ID in _bound_values(where)

    async def test_the_system_scope_of_a_non_superadmin_is_their_own_domain(
        self,
        make_info: Callable[[UserRole], graphene.ResolveInfo],
        db_session: MagicMock,
        held_permissions: AsyncMock,
    ) -> None:
        domain = DomainSessionTarget(domain_id=_DOMAIN_ID)
        self._grant(held_permissions, {domain: Permission.READ})

        where = await self._where(make_info, db_session, UserRole.ADMIN, SystemScope())

        assert _DOMAIN_ID in _bound_values(where)
        assert _CALLER_ID not in _bound_values(where)

    async def test_a_reader_of_the_project_reads_the_project_sessions(
        self,
        make_info: Callable[[UserRole], graphene.ResolveInfo],
        db_session: MagicMock,
        held_permissions: AsyncMock,
    ) -> None:
        project = ProjectSessionTarget(project_id=_PROJECT_ID)
        self._grant(held_permissions, {project: Permission.READ})

        where = await self._where(make_info, db_session, UserRole.ADMIN, ProjectScope(_PROJECT_ID))

        assert _PROJECT_ID in _bound_values(where)
        assert _CALLER_ID not in _bound_values(where)

    async def test_a_non_reader_of_the_project_reads_only_their_own_sessions_in_it(
        self,
        make_info: Callable[[UserRole], graphene.ResolveInfo],
        db_session: MagicMock,
        held_permissions: AsyncMock,
    ) -> None:
        own = UserSessionTarget(user_id=_CALLER_ID)
        self._grant(held_permissions, {own: Permission.READ})

        where = await self._where(make_info, db_session, UserRole.USER, ProjectScope(_PROJECT_ID))

        assert _PROJECT_ID in _bound_values(where)
        assert _CALLER_ID in _bound_values(where)

    async def test_a_caller_reading_nothing_in_the_scope_reads_no_session(
        self,
        make_info: Callable[[UserRole], graphene.ResolveInfo],
        db_session: MagicMock,
        held_permissions: AsyncMock,
    ) -> None:
        self._grant(held_permissions, {})

        where = await self._where(make_info, db_session, UserRole.MONITOR, DomainScope("default"))

        assert "false" in str(where).lower()

    async def test_the_scope_is_checked_in_one_action_run(
        self,
        make_info: Callable[[UserRole], graphene.ResolveInfo],
        db_session: MagicMock,
        held_permissions: AsyncMock,
    ) -> None:
        self._grant(held_permissions, {DomainSessionTarget(domain_id=_DOMAIN_ID): Permission.READ})

        await self._where(make_info, db_session, UserRole.ADMIN, DomainScope("default"))

        held_permissions.assert_awaited_once()

    @pytest.mark.parametrize("enforcement_enabled", [False])
    @pytest.mark.parametrize(
        ("role", "role_bound"),
        [
            (UserRole.ADMIN, "default"),
            (UserRole.MONITOR, "default"),
            (UserRole.USER, _CALLER_ID),
        ],
        ids=["admin-within-domain", "monitor-within-domain", "user-own-sessions"],
    )
    async def test_with_enforcement_off_the_role_bounds_the_scope(
        self,
        make_info: Callable[[UserRole], graphene.ResolveInfo],
        db_session: MagicMock,
        role: UserRole,
        role_bound: object,
    ) -> None:
        where = await self._where(make_info, db_session, role, ProjectScope(_PROJECT_ID))

        assert _PROJECT_ID in _bound_values(where)
        assert role_bound in _bound_values(where)

    async def test_a_permission_other_than_read_attribute_reads_no_session(
        self,
        make_info: Callable[[UserRole], graphene.ResolveInfo],
        db_session: MagicMock,
        held_permissions: AsyncMock,
    ) -> None:
        node = await ComputeSessionNode.get_accessible_node(
            make_info(UserRole.ADMIN),
            ("ComputeSessionNode", str(_SESSION_ID)),
            DomainScope("default"),
            ComputeSessionPermission.DELETE_SESSION,
        )

        assert node is None

    async def test_the_scope_bounds_both_the_page_and_the_count(
        self,
        make_info: Callable[[UserRole], graphene.ResolveInfo],
        db_session: MagicMock,
        held_permissions: AsyncMock,
    ) -> None:
        self._grant(
            held_permissions, {ProjectSessionTarget(project_id=_PROJECT_ID): Permission.READ}
        )

        await ComputeSessionNode.get_accessible_connection(
            make_info(UserRole.ADMIN),
            ProjectScope(_PROJECT_ID),
            ComputeSessionPermission.READ_ATTRIBUTE,
            offset=0,
            first=10,
        )

        page: sa.Select[tuple[object]] = db_session.scalars.await_args.args[0]
        count: sa.Select[tuple[object]] = db_session.scalar.await_args.args[0]
        for stmt in (page, count):
            assert stmt.whereclause is not None
            assert _PROJECT_ID in _bound_values(stmt.whereclause)

    async def test_a_permission_other_than_read_attribute_returns_an_empty_page(
        self,
        make_info: Callable[[UserRole], graphene.ResolveInfo],
        db_session: MagicMock,
        held_permissions: AsyncMock,
    ) -> None:
        result = await ComputeSessionNode.get_accessible_connection(
            make_info(UserRole.ADMIN),
            DomainScope("default"),
            ComputeSessionPermission.DELETE_SESSION,
            offset=0,
            first=10,
        )

        assert result.node_list == []
        assert result.total_count == 0
        db_session.scalars.assert_not_awaited()
