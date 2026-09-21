"""Tests for the scope-permission path of RBACAdapter."""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import ValidationError

from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.entity.domain import DomainEntityType, DomainID
from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.entity.scope_admin import ScopeAdminEntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.common.dto.manager.query import StringFilter, UUIDFilter
from ai.backend.common.dto.manager.v2.rbac.request import (
    MAX_SCOPE_PERMISSION_TARGETS,
    MappedScopeNestedFilter,
    MyAtomicBulkScopePermissionsInput,
    MyScopePermissionsInput,
    PermissionNestedFilter,
    PermissionTarget,
    RoleAssignmentFilter,
    RoleFilter,
    RoleNestedFilter,
)
from ai.backend.common.dto.manager.v2.rbac.types import PermissionBitDTO, PermissionBitFilter
from ai.backend.manager.api.adapters.rbac.adapter import RBACAdapter
from ai.backend.manager.data.permission.virtual_entity import GovernCheckKey
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.services.permission_contoller.actions.get_held_permissions import (
    ScopedGetHeldPermissionsActionResult,
)

_SCOPE_ADMIN = ScopeAdminEntityType.name()
_CALLER_ID = uuid.uuid4()


@pytest.fixture
def caller() -> Iterator[UserID]:
    user = UserData(
        user_id=_CALLER_ID,
        is_authorized=True,
        is_admin=False,
        is_superadmin=False,
        role=UserRole.USER,
        domain_name="default",
        domain_id=DomainID(uuid.uuid4()),
    )
    with with_user(user):
        yield UserID(_CALLER_ID)


@pytest.fixture
def permission_controller() -> MagicMock:
    controller = MagicMock()
    controller.scoped_get_held_permissions.run = AsyncMock(
        return_value=ScopedGetHeldPermissionsActionResult(granted={})
    )
    return controller


@pytest.fixture
def adapter(permission_controller: MagicMock) -> RBACAdapter:
    return RBACAdapter(MagicMock(), permission_controller)


def _target(scope_type: str, scope_id: uuid.UUID, entity_type: str) -> PermissionTarget:
    return PermissionTarget(scope_type=scope_type, scope_id=scope_id, entity_type=entity_type)


class TestMyScopePermissions:
    async def test_it_answers_the_bits_the_govern_walk_found(
        self,
        adapter: RBACAdapter,
        permission_controller: MagicMock,
        caller: UserID,
    ) -> None:
        project_id = uuid.uuid4()
        key = GovernCheckKey(
            user_id=caller,
            scope=ProjectID(project_id),
            entity_type=ProjectEntityType(),
        )
        permission_controller.scoped_get_held_permissions.run.return_value = (
            ScopedGetHeldPermissionsActionResult(granted={key: Permission.READ})
        )

        payload = await adapter.my_scope_permissions(
            MyScopePermissionsInput(target=_target("project", project_id, "project"))
        )

        assert payload.item.permissions == [PermissionBitDTO.READ]
        assert payload.item.scope_id == project_id

    async def test_a_scope_the_caller_reaches_nothing_on_answers_with_no_bits(
        self, adapter: RBACAdapter, caller: UserID
    ) -> None:
        payload = await adapter.my_scope_permissions(
            MyScopePermissionsInput(target=_target("project", uuid.uuid4(), _SCOPE_ADMIN))
        )

        assert payload.item.permissions == []

    async def test_an_entity_type_no_build_declares_answers_with_no_bits(
        self, adapter: RBACAdapter, caller: UserID
    ) -> None:
        payload = await adapter.my_scope_permissions(
            MyScopePermissionsInput(target=_target("project", uuid.uuid4(), "no_such_entity"))
        )

        assert payload.item.permissions == []


class TestMyAtomicBulkScopePermissions:
    async def test_it_echoes_one_item_per_target_in_order(
        self, adapter: RBACAdapter, caller: UserID
    ) -> None:
        targets = [
            _target("project", uuid.uuid4(), _SCOPE_ADMIN),
            _target("domain", uuid.uuid4(), _SCOPE_ADMIN),
        ]

        payload = await adapter.my_atomic_bulk_scope_permissions(
            MyAtomicBulkScopePermissionsInput(targets=targets)
        )

        assert [(item.scope_type, item.scope_id, item.entity_type) for item in payload.items] == [
            (t.scope_type, t.scope_id, t.entity_type) for t in targets
        ]

    async def test_every_target_reaches_the_action_in_one_call(
        self,
        adapter: RBACAdapter,
        permission_controller: MagicMock,
        caller: UserID,
    ) -> None:
        domain_id = uuid.uuid4()
        targets = [
            _target("project", uuid.uuid4(), _SCOPE_ADMIN),
            _target("project", uuid.uuid4(), _SCOPE_ADMIN),
            _target("domain", domain_id, _SCOPE_ADMIN),
        ]

        await adapter.my_atomic_bulk_scope_permissions(
            MyAtomicBulkScopePermissionsInput(targets=targets)
        )

        permission_controller.scoped_get_held_permissions.run.assert_awaited_once()
        action = permission_controller.scoped_get_held_permissions.run.await_args.args[0]
        assert action.scope_targets() == [caller]
        assert len(action.keys) == len(targets)
        assert action.keys[-1] == GovernCheckKey(
            user_id=caller,
            scope=DomainID(domain_id),
            entity_type=ScopeAdminEntityType(),
        )
        assert {key.scope.entity_type() for key in action.keys} == {
            ProjectEntityType(),
            DomainEntityType(),
        }

    def test_targets_beyond_the_limit_are_refused(self) -> None:
        targets = [
            _target("project", uuid.uuid4(), _SCOPE_ADMIN)
            for _ in range(MAX_SCOPE_PERMISSION_TARGETS + 1)
        ]

        with pytest.raises(ValidationError):
            MyAtomicBulkScopePermissionsInput(targets=targets)


def _compiled(conditions: list[QueryCondition]) -> str:
    return " ".join(str(condition().compile()) for condition in conditions)


class TestRoleListingFilters:
    def test_a_role_filter_reads_the_scope_off_the_role_row(self, adapter: RBACAdapter) -> None:
        scope_id = uuid.uuid4()
        conditions = adapter._convert_role_filter_gql(
            RoleFilter(
                mapped_scope=MappedScopeNestedFilter(
                    scope_type=StringFilter(equals="project"),
                    scope_id=UUIDFilter(equals=scope_id),
                ),
            )
        )

        compiled = _compiled(conditions)
        assert "roles.scope_type" in compiled
        assert "roles.scope_id" in compiled

    def test_an_assignment_filter_expresses_role_and_permission_together(
        self, adapter: RBACAdapter
    ) -> None:
        conditions = adapter._convert_assignment_filter(
            RoleAssignmentFilter(
                role=RoleNestedFilter(name=StringFilter(equals="admin")),
                permission=PermissionNestedFilter(
                    permission=PermissionBitFilter(equals=PermissionBitDTO.READ)
                ),
            )
        )

        compiled = _compiled(conditions)
        assert "roles.id = user_roles.role_id" in compiled
        assert "roles.name" in compiled
        assert "permissions.role_id = user_roles.role_id" in compiled
