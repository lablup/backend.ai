"""A global read answered by the `global` singleton's bits, over the real graph.

The delegated role, its permission row and its assignment are all written through the
product paths a superadmin would use, so a graph edge the product forgets to write is a
failure here rather than something a fixture supplies.
"""

from __future__ import annotations

import secrets
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable, Iterator
from typing import TYPE_CHECKING, Any

import pytest

from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.role import RoleEntityType, RoleID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import UserEntityType
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import ProcessorDependencies
from ai.backend.manager.actions.validators.build import build_action_validators
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.data.permission.role import UserRoleAssignmentInput
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.rbac_models.permission.creators import RolePermissionCreator
from ai.backend.manager.models.rbac_models.role.creators import RoleCreator
from ai.backend.manager.models.rbac_models.role.searchers import RoleSearcher
from ai.backend.manager.models.specs.pagination import NoPagination
from ai.backend.manager.models.specs.searcher import GlobalSearcher
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.permission.provider import PermissionOpsProvider
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)
from ai.backend.manager.services.permission_contoller.actions.add_role_permission import (
    AddRolePermissionAction,
)
from ai.backend.manager.services.permission_contoller.actions.create_role import CreateRoleAction
from ai.backend.manager.services.permission_contoller.actions.purge_role import PurgeRoleAction
from ai.backend.manager.services.permission_contoller.actions.search_roles import (
    GlobalSearchRolesAction,
)
from ai.backend.manager.services.permission_contoller.processors import (
    PermissionControllerProcessors,
)
from ai.backend.manager.services.rbac.actions.role.assign import AssignRoleAction
from ai.backend.manager.services.rbac.processors import RbacProcessors
from ai.backend.testutils.fixtures import DomainFixtureData

if TYPE_CHECKING:
    from tests.component.conftest import UserFixtureData

GrantGlobalRole = Callable[[EntityType, Permission], Awaitable[RoleID]]


@pytest.fixture()
def processor_registry(
    database_engine: ExtendedAsyncSAEngine,
    config_provider: ManagerConfigProvider,
) -> ProcessorRegistry[Any]:
    """The registry with the production validators, the global gate among them."""
    return ProcessorRegistry(
        ProcessorDependencies(
            monitors=ActionMonitors(),
            validators=build_action_validators(
                RbacPermissionCheckRepository(
                    PermissionOpsProvider(database_engine), config_provider
                ),
                config_provider,
            ),
            repository=OpsRepository(V2DBOpsProvider(database_engine)),
        )
    )


def _acting(user_id: uuid.UUID, domain_fixture: DomainFixtureData, role: UserRole) -> UserData:
    return UserData(
        user_id=user_id,
        is_authorized=True,
        is_admin=role in (UserRole.ADMIN, UserRole.SUPERADMIN),
        is_superadmin=role == UserRole.SUPERADMIN,
        role=role,
        domain_name=domain_fixture.domain_name,
        domain_id=domain_fixture.domain_id,
    )


@pytest.fixture()
def superadmin(admin_user_fixture: UserFixtureData, domain_fixture: DomainFixtureData) -> UserData:
    return _acting(admin_user_fixture.user_uuid, domain_fixture, UserRole.SUPERADMIN)


@pytest.fixture()
def regular_user(
    regular_user_fixture: UserFixtureData, domain_fixture: DomainFixtureData
) -> UserData:
    return _acting(regular_user_fixture.user_uuid, domain_fixture, UserRole.USER)


@pytest.fixture()
def monitor_user(
    regular_user_fixture: UserFixtureData, domain_fixture: DomainFixtureData
) -> UserData:
    return _acting(regular_user_fixture.user_uuid, domain_fixture, UserRole.MONITOR)


@pytest.fixture()
def superadmin_context(superadmin: UserData) -> Iterator[None]:
    with with_user(superadmin):
        yield


def _search_roles() -> GlobalSearchRolesAction:
    return GlobalSearchRolesAction(
        searcher=GlobalSearcher(used_by=(), searcher=RoleSearcher(pagination=NoPagination()))
    )


@pytest.fixture()
async def grant_global_role(
    permission_controller_processors: PermissionControllerProcessors,
    rbac_processors: RbacProcessors,
    regular_user_fixture: UserFixtureData,
    superadmin: UserData,
) -> AsyncIterator[GrantGlobalRole]:
    """Give the regular user a role in the `global` singleton for one entity type.

    The role, its permission row and the assignment all run through the processors a
    superadmin calls.
    """
    created: list[RoleID] = []

    async def _grant(entity_type: EntityType, permission: Permission) -> RoleID:
        with with_user(superadmin):
            created_role = await permission_controller_processors.create_role.run(
                CreateRoleAction(
                    creator=RoleCreator(
                        name=f"global-{entity_type}-{secrets.token_hex(4)}",
                        scope=global_entity_id(GlobalEntityName.GLOBAL),
                    )
                )
            )
            role_id = RoleID(created_role.data.id)
            created.append(role_id)
            await permission_controller_processors.add_role_permission.run(
                AddRolePermissionAction(
                    role_id=role_id,
                    creator=RolePermissionCreator(entity_type=entity_type, permission=permission),
                )
            )
            await rbac_processors.assign_role.run(
                AssignRoleAction(
                    input=UserRoleAssignmentInput(
                        user_id=regular_user_fixture.user_uuid, role_id=role_id
                    )
                )
            )
            return role_id

    yield _grant

    with with_user(superadmin):
        for role_id in reversed(created):
            await permission_controller_processors.purge_role.run(PurgeRoleAction(role_id=role_id))


class TestGlobalReadGate:
    @pytest.mark.usefixtures("superadmin_context")
    async def test_a_superadmin_passes(
        self, permission_controller_processors: PermissionControllerProcessors
    ) -> None:
        result = await permission_controller_processors.global_search_roles.run(_search_roles())

        assert result.total_count >= 0

    async def test_a_monitor_passes_the_read(
        self,
        permission_controller_processors: PermissionControllerProcessors,
        monitor_user: UserData,
    ) -> None:
        with with_user(monitor_user):
            result = await permission_controller_processors.global_search_roles.run(_search_roles())

        assert result.total_count >= 0

    async def test_a_user_holding_no_global_role_is_refused(
        self,
        permission_controller_processors: PermissionControllerProcessors,
        regular_user: UserData,
    ) -> None:
        with with_user(regular_user):
            with pytest.raises(InsufficientPrivilege):
                await permission_controller_processors.global_search_roles.run(_search_roles())

    async def test_the_delegated_user_passes(
        self,
        permission_controller_processors: PermissionControllerProcessors,
        grant_global_role: GrantGlobalRole,
        regular_user: UserData,
    ) -> None:
        granted_role = await grant_global_role(RoleEntityType(), Permission.READ)

        with with_user(regular_user):
            result = await permission_controller_processors.global_search_roles.run(_search_roles())

        assert granted_role in {RoleID(item.id) for item in result.items}

    async def test_another_types_grant_does_not_reach_this_read(
        self,
        permission_controller_processors: PermissionControllerProcessors,
        grant_global_role: GrantGlobalRole,
        regular_user: UserData,
    ) -> None:
        await grant_global_role(UserEntityType(), Permission.READ)

        with with_user(regular_user):
            with pytest.raises(InsufficientPrivilege):
                await permission_controller_processors.global_search_roles.run(_search_roles())
