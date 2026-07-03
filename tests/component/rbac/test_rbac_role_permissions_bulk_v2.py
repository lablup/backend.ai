"""Component tests for bulk role-permission operations via v2 REST API.

Covers:
- POST /v2/rbac/permissions/bulk-add
- POST /v2/rbac/permissions/bulk-remove
- POST /v2/rbac/permissions/replace
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
import yarl

from ai.backend.client.v2.auth import HMACAuth
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.exceptions import InvalidRequestError, PermissionDeniedError
from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.dto.manager.query import StringFilter, UUIDFilter
from ai.backend.common.dto.manager.v2.rbac.request import (
    AdminSearchPermissionsGQLInput,
    BulkAddRolePermissionsInput,
    BulkRemoveRolePermissionsInput,
    CreatePermissionInput,
    PermissionFilter,
    ReplaceRolePermissionsInput,
)
from ai.backend.common.dto.manager.v2.rbac.response import (
    BulkAddRolePermissionsPayload,
    BulkRemoveRolePermissionsPayload,
    ReplaceRolePermissionsPayload,
)
from ai.backend.common.dto.manager.v2.rbac.types import (
    RBACElementTypeDTO,
    RBACElementTypeFilter,
)
from ai.backend.manager.api.adapters.rbac.adapter import RBACAdapter
from ai.backend.manager.api.rest.admin.handler import AdminHandler
from ai.backend.manager.api.rest.admin.registry import register_admin_routes
from ai.backend.manager.api.rest.rbac.handler import RBACHandler
from ai.backend.manager.api.rest.rbac.registry import register_rbac_routes
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.api.rest.v2.rbac.handler import V2RBACHandler
from ai.backend.manager.api.rest.v2.rbac.registry import register_v2_rbac_routes
from ai.backend.manager.services.permission_contoller.processors import (
    PermissionControllerProcessors,
)
from ai.backend.testutils.fixtures import DomainFixtureData

if TYPE_CHECKING:
    from tests.component.conftest import ServerInfo, UserFixtureData

    from ai.backend.common.dto.manager.rbac.response import CreateRoleResponse


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    permission_controller_processors: PermissionControllerProcessors,
) -> list[RouteRegistry]:
    """Register both v1 RBAC (for role/permission setup) and v2 RBAC routes."""
    rbac_registry = register_rbac_routes(
        RBACHandler(permission_controller=permission_controller_processors), route_deps
    )
    admin_registry = register_admin_routes(
        AdminHandler(
            gql_schema=MagicMock(),
            gql_deps=MagicMock(),
            strawberry_schema=MagicMock(),
            public_strawberry_schema=MagicMock(),
        ),
        route_deps,
        sub_registries=[rbac_registry],
        gql_ws_handler=MagicMock(),
    )

    processors = MagicMock()
    processors.permission_controller = permission_controller_processors
    adapter = RBACAdapter(processors)
    handler = V2RBACHandler(adapter=adapter)
    v2_reg = RouteRegistry.create("v2", route_deps.cors_options)
    v2_reg.add_subregistry(register_v2_rbac_routes(handler, route_deps))

    return [admin_registry, v2_reg]


@pytest.fixture()
async def admin_v2_registry(
    server: ServerInfo,
    admin_user_fixture: UserFixtureData,
) -> AsyncIterator[V2ClientRegistry]:
    registry = await V2ClientRegistry.create(
        ClientConfig(endpoint=yarl.URL(server.url)),
        HMACAuth(
            access_key=admin_user_fixture.keypair.access_key,
            secret_key=admin_user_fixture.keypair.secret_key,
        ),
    )
    try:
        yield registry
    finally:
        await registry.close()


@pytest.fixture()
async def user_v2_registry(
    server: ServerInfo,
    regular_user_fixture: UserFixtureData,
) -> AsyncIterator[V2ClientRegistry]:
    registry = await V2ClientRegistry.create(
        ClientConfig(endpoint=yarl.URL(server.url)),
        HMACAuth(
            access_key=regular_user_fixture.keypair.access_key,
            secret_key=regular_user_fixture.keypair.secret_key,
        ),
    )
    try:
        yield registry
    finally:
        await registry.close()


def _entry(
    role_id: uuid.UUID,
    domain_name: str,
    entity_type: str,
    operation: str,
) -> CreatePermissionInput:
    return CreatePermissionInput(
        role_id=role_id,
        scope_type="domain",
        scope_id=domain_name,
        entity_type=entity_type,
        operation=operation,
    )


class TestBulkAddRolePermissionsV2:
    """POST /v2/rbac/permissions/bulk-add."""

    async def test_admin_adds_two_entries(
        self,
        admin_v2_registry: V2ClientRegistry,
        target_role: CreateRoleResponse,
        domain_fixture: DomainFixtureData,
    ) -> None:
        result = await admin_v2_registry.rbac.bulk_add_role_permissions(
            BulkAddRolePermissionsInput(
                permissions=[
                    _entry(target_role.role.id, domain_fixture.domain_name, "session", "read"),
                    _entry(target_role.role.id, domain_fixture.domain_name, "image", "read"),
                ],
            ),
        )
        assert isinstance(result, BulkAddRolePermissionsPayload)
        assert len(result.items) == 2
        assert result.failed == []
        entity_ops = {(item.entity_type.value, item.operation.value) for item in result.items}
        assert entity_ops == {("session", "read"), ("image", "read")}

    async def test_duplicate_entry_appears_in_failed(
        self,
        admin_v2_registry: V2ClientRegistry,
        target_role: CreateRoleResponse,
        domain_fixture: DomainFixtureData,
    ) -> None:
        # Seed one entry first
        first = await admin_v2_registry.rbac.bulk_add_role_permissions(
            BulkAddRolePermissionsInput(
                permissions=[
                    _entry(target_role.role.id, domain_fixture.domain_name, "vfolder", "read"),
                ],
            ),
        )
        assert len(first.items) == 1

        # Re-submit the same entry alongside a new one
        result = await admin_v2_registry.rbac.bulk_add_role_permissions(
            BulkAddRolePermissionsInput(
                permissions=[
                    _entry(target_role.role.id, domain_fixture.domain_name, "vfolder", "read"),
                    _entry(target_role.role.id, domain_fixture.domain_name, "agent", "read"),
                ],
            ),
        )
        assert len(result.items) == 1
        assert result.items[0].entity_type.value == "agent"
        assert len(result.failed) == 1
        assert result.failed[0].entity_type == "vfolder"
        assert result.failed[0].operation == "read"

    async def test_empty_input_is_ok(
        self,
        admin_v2_registry: V2ClientRegistry,
    ) -> None:
        result = await admin_v2_registry.rbac.bulk_add_role_permissions(
            BulkAddRolePermissionsInput(permissions=[]),
        )
        assert isinstance(result, BulkAddRolePermissionsPayload)
        assert result.items == []
        assert result.failed == []

    async def test_regular_user_is_denied(
        self,
        user_v2_registry: V2ClientRegistry,
        target_role: CreateRoleResponse,
        domain_fixture: DomainFixtureData,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_v2_registry.rbac.bulk_add_role_permissions(
                BulkAddRolePermissionsInput(
                    permissions=[
                        _entry(target_role.role.id, domain_fixture.domain_name, "session", "read"),
                    ],
                ),
            )


class TestBulkRemoveRolePermissionsV2:
    """POST /v2/rbac/permissions/bulk-remove."""

    async def test_admin_removes_existing_ids(
        self,
        admin_v2_registry: V2ClientRegistry,
        target_role: CreateRoleResponse,
        domain_fixture: DomainFixtureData,
    ) -> None:
        added = await admin_v2_registry.rbac.bulk_add_role_permissions(
            BulkAddRolePermissionsInput(
                permissions=[
                    _entry(target_role.role.id, domain_fixture.domain_name, "session", "read"),
                    _entry(target_role.role.id, domain_fixture.domain_name, "image", "read"),
                ],
            ),
        )
        ids = [item.id for item in added.items]

        result = await admin_v2_registry.rbac.bulk_remove_role_permissions(
            BulkRemoveRolePermissionsInput(permission_ids=ids),
        )
        assert isinstance(result, BulkRemoveRolePermissionsPayload)
        assert {item.id for item in result.items} == set(ids)
        assert result.failed == []

    async def test_unknown_ids_are_silently_ignored(
        self,
        admin_v2_registry: V2ClientRegistry,
    ) -> None:
        unknown = [uuid.uuid4(), uuid.uuid4()]
        result = await admin_v2_registry.rbac.bulk_remove_role_permissions(
            BulkRemoveRolePermissionsInput(permission_ids=unknown),
        )
        assert result.items == []
        assert result.failed == []

    async def test_mix_of_known_and_unknown(
        self,
        admin_v2_registry: V2ClientRegistry,
        target_role: CreateRoleResponse,
        domain_fixture: DomainFixtureData,
    ) -> None:
        added = await admin_v2_registry.rbac.bulk_add_role_permissions(
            BulkAddRolePermissionsInput(
                permissions=[
                    _entry(target_role.role.id, domain_fixture.domain_name, "session", "read"),
                ],
            ),
        )
        known_id = added.items[0].id
        unknown_id = uuid.uuid4()

        result = await admin_v2_registry.rbac.bulk_remove_role_permissions(
            BulkRemoveRolePermissionsInput(permission_ids=[known_id, unknown_id]),
        )
        assert {item.id for item in result.items} == {known_id}

    async def test_empty_input_is_ok(
        self,
        admin_v2_registry: V2ClientRegistry,
    ) -> None:
        result = await admin_v2_registry.rbac.bulk_remove_role_permissions(
            BulkRemoveRolePermissionsInput(permission_ids=[]),
        )
        assert result.items == []
        assert result.failed == []

    async def test_regular_user_is_denied(
        self,
        user_v2_registry: V2ClientRegistry,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_v2_registry.rbac.bulk_remove_role_permissions(
                BulkRemoveRolePermissionsInput(permission_ids=[uuid.uuid4()]),
            )


class TestReplaceRolePermissionsV2:
    """POST /v2/rbac/permissions/replace."""

    async def test_admin_replaces_full_set(
        self,
        admin_v2_registry: V2ClientRegistry,
        target_role: CreateRoleResponse,
        domain_fixture: DomainFixtureData,
    ) -> None:
        # Seed prior set
        await admin_v2_registry.rbac.bulk_add_role_permissions(
            BulkAddRolePermissionsInput(
                permissions=[
                    _entry(target_role.role.id, domain_fixture.domain_name, "session", "read"),
                    _entry(target_role.role.id, domain_fixture.domain_name, "image", "read"),
                ],
            ),
        )

        # Replace with a different two-entry set
        result = await admin_v2_registry.rbac.replace_role_permissions(
            ReplaceRolePermissionsInput(
                role_id=target_role.role.id,
                permissions=[
                    _entry(target_role.role.id, domain_fixture.domain_name, "vfolder", "read"),
                    _entry(target_role.role.id, domain_fixture.domain_name, "agent", "read"),
                ],
            ),
        )
        assert isinstance(result, ReplaceRolePermissionsPayload)
        assert {(it.entity_type.value, it.operation.value) for it in result.items} == {
            ("vfolder", "read"),
            ("agent", "read"),
        }
        assert result.failed == []

    async def test_replace_with_empty_clears_all(
        self,
        admin_v2_registry: V2ClientRegistry,
        target_role: CreateRoleResponse,
        domain_fixture: DomainFixtureData,
    ) -> None:
        await admin_v2_registry.rbac.bulk_add_role_permissions(
            BulkAddRolePermissionsInput(
                permissions=[
                    _entry(target_role.role.id, domain_fixture.domain_name, "session", "read"),
                ],
            ),
        )
        result = await admin_v2_registry.rbac.replace_role_permissions(
            ReplaceRolePermissionsInput(role_id=target_role.role.id, permissions=[]),
        )
        assert result.items == []
        assert result.failed == []

    async def test_role_id_mismatch_is_rejected(
        self,
        admin_v2_registry: V2ClientRegistry,
        target_role: CreateRoleResponse,
        domain_fixture: DomainFixtureData,
    ) -> None:
        wrong_role_id = uuid.uuid4()
        with pytest.raises(InvalidRequestError):
            await admin_v2_registry.rbac.replace_role_permissions(
                ReplaceRolePermissionsInput(
                    role_id=target_role.role.id,
                    permissions=[
                        _entry(wrong_role_id, domain_fixture.domain_name, "session", "read"),
                    ],
                ),
            )

    async def test_regular_user_is_denied(
        self,
        user_v2_registry: V2ClientRegistry,
        target_role: CreateRoleResponse,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_v2_registry.rbac.replace_role_permissions(
                ReplaceRolePermissionsInput(
                    role_id=target_role.role.id,
                    permissions=[],
                ),
            )


class TestPermissionFilterScopeIdNarrowing:
    """Verify the new ``PermissionFilter.scope_id`` narrows search results server-side.

    Regression coverage for the wiring chain
    ``PermissionFilter.scope_id`` → ``ScopedPermissionConditions.by_scope_id_*``.
    """

    async def test_scope_id_equals_narrows_results(
        self,
        admin_v2_registry: V2ClientRegistry,
        target_role: CreateRoleResponse,
        domain_fixture: DomainFixtureData,
    ) -> None:
        # Seed two permissions in the same scope and an unrelated one in another scope.
        scope_b = f"{domain_fixture.domain_name}-other"
        await admin_v2_registry.rbac.bulk_add_role_permissions(
            BulkAddRolePermissionsInput(
                permissions=[
                    _entry(target_role.role.id, domain_fixture.domain_name, "session", "read"),
                    _entry(target_role.role.id, domain_fixture.domain_name, "image", "read"),
                    CreatePermissionInput(
                        role_id=target_role.role.id,
                        scope_type="domain",
                        scope_id=scope_b,
                        entity_type="session",
                        operation="read",
                    ),
                ],
            ),
        )

        result = await admin_v2_registry.rbac.search_permissions(
            AdminSearchPermissionsGQLInput(
                filter=PermissionFilter(
                    role_id=UUIDFilter(equals=target_role.role.id),
                    scope_id=StringFilter(equals=domain_fixture.domain_name),
                ),
                limit=100,
            ),
        )
        assert {item.scope_id for item in result.items} == {domain_fixture.domain_name}
        assert len(result.items) == 2

    async def test_role_id_in_filter_returns_matching_rows(
        self,
        admin_v2_registry: V2ClientRegistry,
        target_role: CreateRoleResponse,
        domain_fixture: DomainFixtureData,
    ) -> None:
        await admin_v2_registry.rbac.bulk_add_role_permissions(
            BulkAddRolePermissionsInput(
                permissions=[
                    _entry(target_role.role.id, domain_fixture.domain_name, "session", "read"),
                ],
            ),
        )
        result = await admin_v2_registry.rbac.search_permissions(
            AdminSearchPermissionsGQLInput(
                filter=PermissionFilter(role_id=UUIDFilter(in_=[target_role.role.id])),
                limit=100,
            ),
        )
        assert any(item.role_id == target_role.role.id for item in result.items)
        assert all(item.role_id == target_role.role.id for item in result.items)

    async def test_entity_type_equals_on_strenum_column(
        self,
        admin_v2_registry: V2ClientRegistry,
        target_role: CreateRoleResponse,
        domain_fixture: DomainFixtureData,
    ) -> None:
        """``PermissionRow.entity_type`` is a ``StrEnumType``-wrapped column.

        ``RBACElementTypeFilter.equals`` carries an ``RBACElementTypeDTO`` enum
        instance, which lets ``StrEnumType.process_bind_param`` accept the value
        as-is without any column-cast workaround.
        """
        await admin_v2_registry.rbac.bulk_add_role_permissions(
            BulkAddRolePermissionsInput(
                permissions=[
                    _entry(target_role.role.id, domain_fixture.domain_name, "session", "read"),
                    _entry(target_role.role.id, domain_fixture.domain_name, "image", "read"),
                ],
            ),
        )
        result = await admin_v2_registry.rbac.search_permissions(
            AdminSearchPermissionsGQLInput(
                filter=PermissionFilter(
                    role_id=UUIDFilter(equals=target_role.role.id),
                    entity_type=RBACElementTypeFilter(equals=RBACElementTypeDTO.SESSION),
                ),
                limit=100,
            ),
        )
        assert {item.entity_type.value for item in result.items} == {"session"}

    async def test_entity_type_in_filter(
        self,
        admin_v2_registry: V2ClientRegistry,
        target_role: CreateRoleResponse,
        domain_fixture: DomainFixtureData,
    ) -> None:
        """``RBACElementTypeFilter.in_`` returns rows whose entity_type is in the list."""
        await admin_v2_registry.rbac.bulk_add_role_permissions(
            BulkAddRolePermissionsInput(
                permissions=[
                    _entry(target_role.role.id, domain_fixture.domain_name, "session", "read"),
                    _entry(target_role.role.id, domain_fixture.domain_name, "image", "read"),
                    _entry(target_role.role.id, domain_fixture.domain_name, "vfolder", "read"),
                ],
            ),
        )
        result = await admin_v2_registry.rbac.search_permissions(
            AdminSearchPermissionsGQLInput(
                filter=PermissionFilter(
                    role_id=UUIDFilter(equals=target_role.role.id),
                    entity_type=RBACElementTypeFilter(
                        in_=[RBACElementTypeDTO.SESSION, RBACElementTypeDTO.IMAGE]
                    ),
                ),
                limit=100,
            ),
        )
        assert {item.entity_type.value for item in result.items} == {"session", "image"}
