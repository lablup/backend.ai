from __future__ import annotations

import secrets
import uuid
from collections.abc import AsyncIterator, Callable, Coroutine
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.role import RoleEntityType
from ai.backend.common.data.entity.user import UserEntityType
from ai.backend.common.dto.manager.rbac.request import (
    CreateRoleRequest,
    PurgeRoleRequest,
)
from ai.backend.common.dto.manager.rbac.response import CreateRoleResponse
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import Concern, ConcernMeta, GroupMeta
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.actions.validators.rbac import RBACValidators
from ai.backend.manager.api.rest.admin.handler import AdminHandler
from ai.backend.manager.api.rest.admin.registry import register_admin_routes
from ai.backend.manager.api.rest.rbac.handler import RBACHandler
from ai.backend.manager.api.rest.rbac.registry import register_rbac_routes
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.v2.roster.provider import RosterOpsProvider
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)
from ai.backend.manager.repositories.rbac.roster_repository import RbacRosterRepository
from ai.backend.manager.services.permission_contoller.processors import (
    PermissionControllerProcessors,
)
from ai.backend.manager.services.permission_contoller.service import PermissionControllerService
from ai.backend.manager.services.rbac.processors import RbacProcessors
from ai.backend.manager.services.rbac.service import RbacRoleService
from ai.backend.testutils.action_validators import mock_virtual_entity_rbac_validators

RoleFactory = Callable[..., Coroutine[Any, Any, CreateRoleResponse]]


@pytest.fixture()
def permission_controller_processors(
    database_engine: ExtendedAsyncSAEngine,
    processor_registry: ProcessorRegistry[Any],
) -> PermissionControllerProcessors:
    repo = PermissionControllerRepository(database_engine)
    service = PermissionControllerService(
        repo,
        rbac_action_registry=[],
    )
    validators = ActionValidators(
        virtual_entity_rbac=mock_virtual_entity_rbac_validators(),
        rbac=RBACValidators(scope=AsyncMock()),
    )
    return PermissionControllerProcessors(
        processor_registry.group(GroupMeta(RoleEntityType())),
        service=service,
        action_monitors=[],
        validators=validators,
    )


@pytest.fixture()
def rbac_processors(
    database_engine: ExtendedAsyncSAEngine,
    processor_registry: ProcessorRegistry[Any],
) -> RbacProcessors:
    """Real RbacProcessors for the role grants these tests make."""
    rbac_groups = processor_registry.concern(ConcernMeta(Concern.RBAC))
    return RbacProcessors(
        rbac_groups.relation_group(),
        rbac_groups.group(GroupMeta(UserEntityType())),
        MagicMock(),
        MagicMock(),
        RbacRoleService(
            PermissionControllerRepository(database_engine),
            RbacRosterRepository(RosterOpsProvider(database_engine)),
        ),
        [],
    )


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    permission_controller_processors: PermissionControllerProcessors,
    rbac_processors: RbacProcessors,
) -> list[RouteRegistry]:
    """Load only the modules required for RBAC-domain tests."""
    rbac_registry = register_rbac_routes(
        RBACHandler(permission_controller=permission_controller_processors, rbac=rbac_processors),
        route_deps,
    )
    return [
        register_admin_routes(
            AdminHandler(
                gql_schema=MagicMock(),
                gql_deps=MagicMock(),
                strawberry_schema=MagicMock(),
                public_strawberry_schema=MagicMock(),
            ),
            route_deps,
            sub_registries=[rbac_registry],
            gql_ws_handler=MagicMock(),
        ),
    ]


@pytest.fixture()
async def role_factory(
    admin_registry: BackendAIClientRegistry,
    group_fixture: uuid.UUID,
) -> AsyncIterator[RoleFactory]:
    """Factory fixture that creates roles in the test project via SDK and purges them
    on teardown."""
    created_ids: list[uuid.UUID] = []

    async def _create(**overrides: Any) -> CreateRoleResponse:
        unique = secrets.token_hex(4)
        params: dict[str, Any] = {
            "name": f"test-role-{unique}",
            "scope_type": ProjectEntityType(),
            "scope_id": group_fixture,
            "description": f"Test role {unique}",
        }
        params.update(overrides)
        result = await admin_registry.rbac.create_role(CreateRoleRequest(**params))
        created_ids.append(result.role.id)
        return result

    yield _create

    for role_id in reversed(created_ids):
        try:
            await admin_registry.rbac.purge_role(PurgeRoleRequest(role_id=role_id))
        except Exception:
            pass


@pytest.fixture()
async def target_role(
    role_factory: RoleFactory,
) -> CreateRoleResponse:
    """Pre-created role for tests that need an existing role."""
    return await role_factory()
