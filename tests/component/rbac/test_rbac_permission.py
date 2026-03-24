from __future__ import annotations

import uuid
from typing import Any

import pytest

from ai.backend.common.data.permission.types import (
    OperationType,
    RBACElementType,
    ScopeType,
)
from ai.backend.manager.data.permission.id import ObjectId, ScopeId
from ai.backend.manager.data.permission.permission import PermissionData
from ai.backend.manager.data.permission.role import (
    BatchEntityPermissionCheckInput,
    ScopePermissionCheckInput,
    SingleEntityPermissionCheckInput,
    UserRoleAssignmentInput,
    UserRoleRevocationInput,
)
from ai.backend.manager.data.permission.types import EntityType
from ai.backend.manager.errors.common import ObjectNotFound
from ai.backend.manager.errors.repository import (
    UniqueConstraintViolationError,
)
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.purger import Purger
from ai.backend.manager.repositories.permission_controller.creators import (
    PermissionCreatorSpec,
)
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)
from ai.backend.manager.services.permission_contoller.actions.assign_role import AssignRoleAction
from ai.backend.manager.services.permission_contoller.actions.permission import (
    CreatePermissionAction,
    DeletePermissionAction,
)
from ai.backend.manager.services.permission_contoller.actions.revoke_role import RevokeRoleAction
from ai.backend.manager.services.permission_contoller.processors import (
    PermissionControllerProcessors,
)

from .conftest import RoleFactory


@pytest.fixture()
def permission_repo(database_engine: ExtendedAsyncSAEngine) -> PermissionControllerRepository:
    """Direct repository fixture for check-permission operations."""
    return PermissionControllerRepository(database_engine)


class TestPermissionCreate:
    """Permission CRUD — create operations at processor level."""

    async def test_create_basic_permission(
        self,
        permission_controller_processors: PermissionControllerProcessors,
        target_role: Any,
        domain_fixture: str,
    ) -> None:
        """S-CREATE-1: Create basic permission with valid params → PermissionData returned."""
        creator = Creator(
            spec=PermissionCreatorSpec(
                role_id=target_role.role.id,
                scope_type=RBACElementType.DOMAIN,
                scope_id=domain_fixture,
                entity_type=RBACElementType.SESSION,
                operation=OperationType.READ,
            )
        )
        result = await permission_controller_processors.create_permission.wait_for_complete(
            CreatePermissionAction(creator=creator)
        )

        assert isinstance(result.data, PermissionData)
        assert result.data.role_id == target_role.role.id
        assert result.data.scope_type == ScopeType.DOMAIN
        assert result.data.entity_type == EntityType.SESSION
        assert result.data.operation == OperationType.READ

        # Cleanup
        await permission_controller_processors.delete_permission.wait_for_complete(
            DeletePermissionAction(purger=Purger(row_class=PermissionRow, pk_value=result.data.id))
        )

    async def test_create_permissions_with_various_combinations(
        self,
        permission_controller_processors: PermissionControllerProcessors,
        target_role: Any,
        domain_fixture: str,
    ) -> None:
        """S-CREATE-2: Create permissions with various scope/entity/operation combinations."""
        combos: list[tuple[RBACElementType, str, RBACElementType, OperationType]] = [
            (RBACElementType.DOMAIN, domain_fixture, RBACElementType.SESSION, OperationType.READ),
            (RBACElementType.DOMAIN, domain_fixture, RBACElementType.IMAGE, OperationType.UPDATE),
            (
                RBACElementType.DOMAIN,
                domain_fixture,
                RBACElementType.VFOLDER,
                OperationType.SOFT_DELETE,
            ),
        ]
        created_ids: list[uuid.UUID] = []

        for scope_type, scope_id, entity_type, operation in combos:
            result = await permission_controller_processors.create_permission.wait_for_complete(
                CreatePermissionAction(
                    creator=Creator(
                        spec=PermissionCreatorSpec(
                            role_id=target_role.role.id,
                            scope_type=scope_type,
                            scope_id=scope_id,
                            entity_type=entity_type,
                            operation=operation,
                        )
                    )
                )
            )
            assert result.data.entity_type == entity_type.to_entity_type()
            assert result.data.operation == operation
            assert result.data.role_id == target_role.role.id
            created_ids.append(result.data.id)

        # Cleanup
        for perm_id in created_ids:
            await permission_controller_processors.delete_permission.wait_for_complete(
                DeletePermissionAction(purger=Purger(row_class=PermissionRow, pk_value=perm_id))
            )

    async def test_create_duplicate_permission_raises_unique_constraint(
        self,
        permission_controller_processors: PermissionControllerProcessors,
        target_role: Any,
        domain_fixture: str,
    ) -> None:
        """F-BIZ-4: Create duplicate permission → unique constraint error."""
        spec = PermissionCreatorSpec(
            role_id=target_role.role.id,
            scope_type=RBACElementType.DOMAIN,
            scope_id=domain_fixture,
            entity_type=RBACElementType.VFOLDER,
            operation=OperationType.READ,
        )

        result = await permission_controller_processors.create_permission.wait_for_complete(
            CreatePermissionAction(creator=Creator(spec=spec))
        )
        perm_id = result.data.id

        try:
            with pytest.raises(UniqueConstraintViolationError):
                await permission_controller_processors.create_permission.wait_for_complete(
                    CreatePermissionAction(creator=Creator(spec=spec))
                )
        finally:
            await permission_controller_processors.delete_permission.wait_for_complete(
                DeletePermissionAction(purger=Purger(row_class=PermissionRow, pk_value=perm_id))
            )


class TestPermissionDelete:
    """Permission CRUD — delete operations at processor level."""

    async def test_delete_existing_permission(
        self,
        permission_controller_processors: PermissionControllerProcessors,
        target_role: Any,
        domain_fixture: str,
    ) -> None:
        """S-DELETE-1: Delete existing permission → deletion response."""
        create_result = await permission_controller_processors.create_permission.wait_for_complete(
            CreatePermissionAction(
                creator=Creator(
                    spec=PermissionCreatorSpec(
                        role_id=target_role.role.id,
                        scope_type=RBACElementType.DOMAIN,
                        scope_id=domain_fixture,
                        entity_type=RBACElementType.SESSION,
                        operation=OperationType.HARD_DELETE,
                    )
                )
            )
        )
        perm_id = create_result.data.id

        delete_result = await permission_controller_processors.delete_permission.wait_for_complete(
            DeletePermissionAction(purger=Purger(row_class=PermissionRow, pk_value=perm_id))
        )

        assert isinstance(delete_result.data, PermissionData)
        assert delete_result.data.id == perm_id

    async def test_deleted_permission_no_longer_exists(
        self,
        permission_controller_processors: PermissionControllerProcessors,
        target_role: Any,
        domain_fixture: str,
    ) -> None:
        """S-DELETE-2: Verify deleted permission no longer exists."""
        create_result = await permission_controller_processors.create_permission.wait_for_complete(
            CreatePermissionAction(
                creator=Creator(
                    spec=PermissionCreatorSpec(
                        role_id=target_role.role.id,
                        scope_type=RBACElementType.DOMAIN,
                        scope_id=domain_fixture,
                        entity_type=RBACElementType.IMAGE,
                        operation=OperationType.SOFT_DELETE,
                    )
                )
            )
        )
        perm_id = create_result.data.id

        await permission_controller_processors.delete_permission.wait_for_complete(
            DeletePermissionAction(purger=Purger(row_class=PermissionRow, pk_value=perm_id))
        )

        # Second delete must raise ObjectNotFound
        with pytest.raises(ObjectNotFound):
            await permission_controller_processors.delete_permission.wait_for_complete(
                DeletePermissionAction(purger=Purger(row_class=PermissionRow, pk_value=perm_id))
            )

    async def test_delete_nonexistent_permission_raises_not_found(
        self,
        permission_controller_processors: PermissionControllerProcessors,
    ) -> None:
        """F-BIZ-2: Delete non-existent permission_id → ObjectNotFound."""
        with pytest.raises(ObjectNotFound):
            await permission_controller_processors.delete_permission.wait_for_complete(
                DeletePermissionAction(
                    purger=Purger(row_class=PermissionRow, pk_value=uuid.uuid4())
                )
            )


class TestCheckPermissionOfEntity:
    """Check permission of a specific entity (object-level check)."""

    async def test_user_with_no_roles_returns_false(
        self,
        permission_repo: PermissionControllerRepository,
    ) -> None:
        """S-ENTITY-3: User with no roles → False."""
        has_perm = await permission_repo.check_permission_of_entity(
            SingleEntityPermissionCheckInput(
                user_id=uuid.uuid4(),  # random user with no roles
                target_object_id=ObjectId(
                    entity_type=EntityType.SESSION, entity_id=str(uuid.uuid4())
                ),
                operation=OperationType.READ,
            )
        )
        assert has_perm is False


class TestCheckPermissionInScope:
    """Check permission within a specific scope (scope-level check)."""

    async def test_user_with_permission_in_scope_returns_true(
        self,
        permission_controller_processors: PermissionControllerProcessors,
        permission_repo: PermissionControllerRepository,
        role_factory: RoleFactory,
        admin_user_fixture: Any,
        domain_fixture: str,
    ) -> None:
        """S-SCOPE-1: User has permission in target scope → True."""
        role = await role_factory()
        role_id = role.role.id
        user_id: uuid.UUID = admin_user_fixture.user_uuid

        perm_result = await permission_controller_processors.create_permission.wait_for_complete(
            CreatePermissionAction(
                creator=Creator(
                    spec=PermissionCreatorSpec(
                        role_id=role_id,
                        scope_type=RBACElementType.DOMAIN,
                        scope_id=domain_fixture,
                        entity_type=RBACElementType.SESSION,
                        operation=OperationType.READ,
                    )
                )
            )
        )

        await permission_controller_processors.assign_role.wait_for_complete(
            AssignRoleAction(input=UserRoleAssignmentInput(user_id=user_id, role_id=role_id))
        )

        try:
            has_perm = await permission_repo.check_permission_in_scope(
                ScopePermissionCheckInput(
                    user_id=user_id,
                    target_entity_type=EntityType.SESSION,
                    target_scope_id=ScopeId(scope_type=ScopeType.DOMAIN, scope_id=domain_fixture),
                    operation=OperationType.READ,
                )
            )
            assert has_perm is True
        finally:
            await permission_controller_processors.revoke_role.wait_for_complete(
                RevokeRoleAction(input=UserRoleRevocationInput(user_id=user_id, role_id=role_id))
            )
            await permission_controller_processors.delete_permission.wait_for_complete(
                DeletePermissionAction(
                    purger=Purger(row_class=PermissionRow, pk_value=perm_result.data.id)
                )
            )

    async def test_user_without_permission_in_scope_returns_false(
        self,
        permission_repo: PermissionControllerRepository,
        domain_fixture: str,
    ) -> None:
        """S-SCOPE-2: User lacks permission in target scope → False."""
        has_perm = await permission_repo.check_permission_in_scope(
            ScopePermissionCheckInput(
                user_id=uuid.uuid4(),  # random user with no roles
                target_entity_type=EntityType.SESSION,
                target_scope_id=ScopeId(scope_type=ScopeType.DOMAIN, scope_id=domain_fixture),
                operation=OperationType.READ,
            )
        )
        assert has_perm is False


class TestCheckPermissionBatch:
    """Batch permission check across multiple entities."""

    async def test_batch_check_with_empty_list_returns_empty_mapping(
        self,
        permission_repo: PermissionControllerRepository,
    ) -> None:
        """S-BATCH-4: Empty entity list → empty mapping."""
        result = await permission_repo.check_permission_of_entities(
            BatchEntityPermissionCheckInput(
                user_id=uuid.uuid4(),
                target_object_ids=[],
                operation=OperationType.READ,
            )
        )
        assert result == {}
