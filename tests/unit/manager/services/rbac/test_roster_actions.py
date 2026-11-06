"""A roster join that names a role puts that role before the scope gate as a granted
target, so the gate asks CREATE on the role beside the ``user`` permission at the project."""

from __future__ import annotations

import uuid
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.contexts.user import with_user_context
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.manager.actions.v2.scope.validator.rbac import VirtualEntityScopeActionRBACValidator
from ai.backend.manager.actions.v2.trigger import ActionTriggerMeta
from ai.backend.manager.data.permission.virtual_entity import (
    GovernCheckKey,
    OwnCheckKey,
    PermissionCheckResult,
)
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)
from ai.backend.manager.services.rbac.actions.roster.join_project import JoinProjectAction

_USER = UserData(
    user_id=uuid.uuid4(),
    is_authorized=True,
    is_admin=True,
    is_superadmin=False,
    role=UserRole.ADMIN,
    domain_name="default",
    domain_id=DomainID(uuid.uuid4()),
)


def _answering(role_permission: Permission) -> MagicMock:
    """A repository granting CREATE at every scope and ``role_permission`` on every entity."""

    async def checked(
        govern_keys: Sequence[GovernCheckKey], own_keys: Sequence[OwnCheckKey]
    ) -> PermissionCheckResult:
        governed: Mapping[GovernCheckKey, Permission] = dict.fromkeys(
            govern_keys, Permission.CREATE
        )
        owned: Mapping[OwnCheckKey, Permission] = dict.fromkeys(own_keys, role_permission)
        return PermissionCheckResult(governed=governed, owned=owned)

    repository = MagicMock(spec=RbacPermissionCheckRepository)
    repository.checked_permissions = AsyncMock(side_effect=checked)
    return repository


def _validator(repository: MagicMock) -> VirtualEntityScopeActionRBACValidator:
    config_provider = MagicMock()
    config_provider.config.manager.rbac.enforcement_enabled = True
    return VirtualEntityScopeActionRBACValidator(repository, config_provider)


@pytest.fixture
def trigger_meta() -> ActionTriggerMeta:
    return ActionTriggerMeta(action_id=uuid.uuid4(), started_at=datetime.now(UTC))


@pytest.fixture
def join_naming_a_role() -> JoinProjectAction:
    return JoinProjectAction(
        project_id=ProjectID(uuid.uuid4()),
        user_ids=[UserID(uuid.uuid4())],
        role_id=RoleID(uuid.uuid4()),
    )


@pytest.fixture
def join_without_a_role() -> JoinProjectAction:
    return JoinProjectAction(project_id=ProjectID(uuid.uuid4()), user_ids=[UserID(uuid.uuid4())])


class TestJoinProjectActionGrantedRole:
    async def test_a_named_role_without_create_on_it_is_refused(
        self, join_naming_a_role: JoinProjectAction, trigger_meta: ActionTriggerMeta
    ) -> None:
        validator = _validator(_answering(Permission.READ))
        with with_user_context(_USER):
            with pytest.raises(NotEnoughPermission, match="to grant"):
                await validator.validate(join_naming_a_role, trigger_meta)

    async def test_a_named_role_with_create_on_it_passes(
        self, join_naming_a_role: JoinProjectAction, trigger_meta: ActionTriggerMeta
    ) -> None:
        validator = _validator(_answering(Permission.CREATE))
        with with_user_context(_USER):
            await validator.validate(join_naming_a_role, trigger_meta)

    async def test_a_join_without_a_role_asks_only_the_scope(
        self, join_without_a_role: JoinProjectAction, trigger_meta: ActionTriggerMeta
    ) -> None:
        validator = _validator(_answering(Permission.NONE))
        with with_user_context(_USER):
            await validator.validate(join_without_a_role, trigger_meta)
