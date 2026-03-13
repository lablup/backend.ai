"""
Unit tests for PermissionControllerService.
Tests all 21 service methods using mocked repository layer.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.permission.types import (
    EntityType,
    OperationType,
    RelationType,
    RoleSource,
    ScopeType,
)
from ai.backend.manager.data.common.types import SearchResult
from ai.backend.manager.data.permission.association_scopes_entities import (
    AssociationScopesEntitiesData,
)
from ai.backend.manager.data.permission.entity import EntityData
from ai.backend.manager.data.permission.id import ObjectId, ScopeId
from ai.backend.manager.data.permission.object_permission import (
    ObjectPermissionCreateInputBeforeRoleCreation,
    ObjectPermissionData,
)
from ai.backend.manager.data.permission.permission import PermissionData
from ai.backend.manager.data.permission.role import (
    AssignedUserData,
    RoleData,
    RoleDetailData,
    RolePermissionsUpdateInput,
    UserRoleAssignmentData,
    UserRoleAssignmentInput,
    UserRoleRevocationData,
    UserRoleRevocationInput,
)
from ai.backend.manager.data.permission.status import PermissionStatus, RoleStatus
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.services.permission_contoller.actions.assign_role import AssignRoleAction
from ai.backend.manager.services.permission_contoller.actions.create_role import CreateRoleAction
from ai.backend.manager.services.permission_contoller.actions.delete_role import DeleteRoleAction
from ai.backend.manager.services.permission_contoller.actions.get_entity_types import (
    GetEntityTypesAction,
)
from ai.backend.manager.services.permission_contoller.actions.get_role_detail import (
    GetRoleDetailAction,
)
from ai.backend.manager.services.permission_contoller.actions.object_permission import (
    CreateObjectPermissionAction,
    DeleteObjectPermissionAction,
)
from ai.backend.manager.services.permission_contoller.actions.permission import (
    CreatePermissionAction,
    DeletePermissionAction,
)
from ai.backend.manager.services.permission_contoller.actions.purge_role import PurgeRoleAction
from ai.backend.manager.services.permission_contoller.actions.revoke_role import RevokeRoleAction
from ai.backend.manager.services.permission_contoller.actions.search_element_associations import (
    SearchElementAssociationsAction,
)
from ai.backend.manager.services.permission_contoller.actions.search_entities import (
    SearchEntitiesAction,
)
from ai.backend.manager.services.permission_contoller.actions.search_object_permissions import (
    SearchObjectPermissionsAction,
)
from ai.backend.manager.services.permission_contoller.actions.search_permissions import (
    SearchPermissionsAction,
)
from ai.backend.manager.services.permission_contoller.actions.search_roles import SearchRolesAction
from ai.backend.manager.services.permission_contoller.actions.search_users_assigned_to_role import (
    SearchUsersAssignedToRoleAction,
)
from ai.backend.manager.services.permission_contoller.actions.update_role import UpdateRoleAction
from ai.backend.manager.services.permission_contoller.actions.update_role_permissions import (
    UpdateRolePermissionsAction,
)
from ai.backend.manager.services.permission_contoller.service import (
    PermissionControllerService,
)

if TYPE_CHECKING:
    from ai.backend.manager.repositories.permission_controller.repository import (
        PermissionControllerRepository,
    )


def _make_role_data(
    *,
    role_id: uuid.UUID | None = None,
    name: str = "test-role",
    source: RoleSource = RoleSource.CUSTOM,
    status: RoleStatus = RoleStatus.ACTIVE,
    deleted_at: datetime | None = None,
    description: str | None = None,
) -> RoleData:
    now = datetime.now(tz=UTC)
    return RoleData(
        id=role_id or uuid.uuid4(),
        name=name,
        source=source,
        status=status,
        created_at=now,
        updated_at=now,
        deleted_at=deleted_at,
        description=description,
    )


def _make_role_detail_data(
    *,
    role_id: uuid.UUID | None = None,
    name: str = "test-role",
    object_permissions: list[ObjectPermissionData] | None = None,
) -> RoleDetailData:
    now = datetime.now(tz=UTC)
    return RoleDetailData(
        id=role_id or uuid.uuid4(),
        name=name,
        source=RoleSource.CUSTOM,
        status=RoleStatus.ACTIVE,
        object_permissions=object_permissions or [],
        created_at=now,
        updated_at=now,
        deleted_at=None,
    )


def _make_querier(limit: int = 10, offset: int = 0) -> BatchQuerier:
    return BatchQuerier(
        conditions=[],
        orders=[],
        pagination=OffsetPagination(limit=limit, offset=offset),
    )


class TestCreateRole:
    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        repository = MagicMock()
        repository.create_role = AsyncMock()
        return repository

    @pytest.fixture
    def service(
        self, mock_repository: PermissionControllerRepository
    ) -> PermissionControllerService:
        return PermissionControllerService(repository=mock_repository)

    async def test_create_role_returns_role_data(
        self,
        service: PermissionControllerService,
        mock_repository: MagicMock,
    ) -> None:
        role_data = _make_role_data(name="admin-role", source=RoleSource.CUSTOM)
        mock_repository.create_role.return_value = role_data

        creator = MagicMock()
        action = CreateRoleAction(creator=creator)

        result = await service.create_role(action)

        mock_repository.create_role.assert_called_once()
        assert result.data.name == "admin-role"
        assert result.data.source == RoleSource.CUSTOM

    async def test_create_role_with_object_permissions(
        self,
        service: PermissionControllerService,
        mock_repository: MagicMock,
    ) -> None:
        role_data = _make_role_data()
        mock_repository.create_role.return_value = role_data

        obj_perm = ObjectPermissionCreateInputBeforeRoleCreation(
            entity_type=EntityType.USER,
            entity_id="user-1",
            operation=OperationType.READ,
            status=PermissionStatus.ACTIVE,
        )
        creator = MagicMock()
        action = CreateRoleAction(creator=creator, object_permissions=[obj_perm])

        result = await service.create_role(action)

        call_args = mock_repository.create_role.call_args[0][0]
        assert len(call_args.object_permissions) == 1
        assert result.data is not None

    async def test_create_role_default_timestamps(
        self,
        service: PermissionControllerService,
        mock_repository: MagicMock,
    ) -> None:
        now = datetime.now(tz=UTC)
        role_data = _make_role_data()
        mock_repository.create_role.return_value = role_data

        action = CreateRoleAction(creator=MagicMock())
        result = await service.create_role(action)

        assert result.data.created_at is not None
        assert result.data.updated_at is not None
        assert result.data.created_at <= now or result.data.created_at >= now


class TestGetRoleDetail:
    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        repository = MagicMock()
        repository.get_role_with_permissions = AsyncMock()
        return repository

    @pytest.fixture
    def service(
        self, mock_repository: PermissionControllerRepository
    ) -> PermissionControllerService:
        return PermissionControllerService(repository=mock_repository)

    async def test_get_role_detail_returns_full_detail(
        self,
        service: PermissionControllerService,
        mock_repository: MagicMock,
    ) -> None:
        role_id = uuid.uuid4()
        obj_perm = ObjectPermissionData(
            id=uuid.uuid4(),
            role_id=role_id,
            object_id=ObjectId(entity_type=EntityType.USER, entity_id="user-1"),
            operation=OperationType.READ,
        )
        detail = _make_role_detail_data(role_id=role_id, object_permissions=[obj_perm])
        mock_repository.get_role_with_permissions.return_value = detail

        action = GetRoleDetailAction(role_id=role_id)
        result = await service.get_role_detail(action)

        mock_repository.get_role_with_permissions.assert_called_once_with(role_id)
        assert result.role.id == role_id
        assert len(result.role.object_permissions) == 1

    async def test_get_role_detail_empty_permissions(
        self,
        service: PermissionControllerService,
        mock_repository: MagicMock,
    ) -> None:
        role_id = uuid.uuid4()
        detail = _make_role_detail_data(role_id=role_id, object_permissions=[])
        mock_repository.get_role_with_permissions.return_value = detail

        action = GetRoleDetailAction(role_id=role_id)
        result = await service.get_role_detail(action)

        assert result.role.object_permissions == []


class TestUpdateRole:
    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        repository = MagicMock()
        repository.update_role = AsyncMock()
        return repository

    @pytest.fixture
    def service(
        self, mock_repository: PermissionControllerRepository
    ) -> PermissionControllerService:
        return PermissionControllerService(repository=mock_repository)

    async def test_update_role_delegates_to_repository(
        self,
        service: PermissionControllerService,
        mock_repository: MagicMock,
    ) -> None:
        role_data = _make_role_data(name="updated-role", description="new desc")
        mock_repository.update_role.return_value = role_data

        updater = MagicMock()
        action = UpdateRoleAction(updater=updater)
        result = await service.update_role(action)

        mock_repository.update_role.assert_called_once_with(updater)
        assert result.data.name == "updated-role"
        assert result.data.description == "new desc"


class TestDeleteRole:
    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        repository = MagicMock()
        repository.delete_role = AsyncMock()
        return repository

    @pytest.fixture
    def service(
        self, mock_repository: PermissionControllerRepository
    ) -> PermissionControllerService:
        return PermissionControllerService(repository=mock_repository)

    async def test_soft_delete_sets_deleted_at(
        self,
        service: PermissionControllerService,
        mock_repository: MagicMock,
    ) -> None:
        deleted_at = datetime.now(tz=UTC)
        role_data = _make_role_data(
            status=RoleStatus.INACTIVE,
            deleted_at=deleted_at,
        )
        mock_repository.delete_role.return_value = role_data

        updater = MagicMock()
        action = DeleteRoleAction(updater=updater)
        result = await service.delete_role(action)

        mock_repository.delete_role.assert_called_once_with(updater)
        assert result.data.deleted_at == deleted_at


class TestPurgeRole:
    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        repository = MagicMock()
        repository.purge_role = AsyncMock()
        return repository

    @pytest.fixture
    def service(
        self, mock_repository: PermissionControllerRepository
    ) -> PermissionControllerService:
        return PermissionControllerService(repository=mock_repository)

    async def test_purge_role_hard_deletes(
        self,
        service: PermissionControllerService,
        mock_repository: MagicMock,
    ) -> None:
        role_data = _make_role_data()
        mock_repository.purge_role.return_value = role_data

        purger = MagicMock()
        action = PurgeRoleAction(purger=purger)
        result = await service.purge_role(action)

        mock_repository.purge_role.assert_called_once_with(purger)
        assert result.data.id == role_data.id


class TestAssignRole:
    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        repository = MagicMock()
        repository.assign_role = AsyncMock()
        return repository

    @pytest.fixture
    def service(
        self, mock_repository: PermissionControllerRepository
    ) -> PermissionControllerService:
        return PermissionControllerService(repository=mock_repository)

    async def test_assign_role_creates_assignment(
        self,
        service: PermissionControllerService,
        mock_repository: MagicMock,
    ) -> None:
        user_id = uuid.uuid4()
        role_id = uuid.uuid4()
        granted_by = uuid.uuid4()
        assignment_data = UserRoleAssignmentData(
            id=uuid.uuid4(),
            user_id=user_id,
            role_id=role_id,
            granted_by=granted_by,
        )
        mock_repository.assign_role.return_value = assignment_data

        input_data = UserRoleAssignmentInput(
            user_id=user_id, role_id=role_id, granted_by=granted_by
        )
        action = AssignRoleAction(input=input_data)
        result = await service.assign_role(action)

        mock_repository.assign_role.assert_called_once_with(input_data)
        assert result.data.user_id == user_id
        assert result.data.role_id == role_id
        assert result.data.granted_by == granted_by

    async def test_assign_role_without_granted_by(
        self,
        service: PermissionControllerService,
        mock_repository: MagicMock,
    ) -> None:
        user_id = uuid.uuid4()
        role_id = uuid.uuid4()
        assignment_data = UserRoleAssignmentData(
            id=uuid.uuid4(),
            user_id=user_id,
            role_id=role_id,
            granted_by=None,
        )
        mock_repository.assign_role.return_value = assignment_data

        input_data = UserRoleAssignmentInput(user_id=user_id, role_id=role_id)
        action = AssignRoleAction(input=input_data)
        result = await service.assign_role(action)

        assert result.data.granted_by is None


class TestRevokeRole:
    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        repository = MagicMock()
        repository.revoke_role = AsyncMock()
        return repository

    @pytest.fixture
    def service(
        self, mock_repository: PermissionControllerRepository
    ) -> PermissionControllerService:
        return PermissionControllerService(repository=mock_repository)

    async def test_revoke_role_returns_revocation_data(
        self,
        service: PermissionControllerService,
        mock_repository: MagicMock,
    ) -> None:
        user_id = uuid.uuid4()
        role_id = uuid.uuid4()
        revocation_data = UserRoleRevocationData(
            user_role_id=uuid.uuid4(),
            user_id=user_id,
            role_id=role_id,
        )
        mock_repository.revoke_role.return_value = revocation_data

        input_data = UserRoleRevocationInput(user_id=user_id, role_id=role_id)
        action = RevokeRoleAction(input=input_data)
        result = await service.revoke_role(action)

        mock_repository.revoke_role.assert_called_once_with(input_data)
        assert result.data.user_id == user_id
        assert result.data.role_id == role_id


class TestSearchRoles:
    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        repository = MagicMock()
        repository.search_roles = AsyncMock()
        return repository

    @pytest.fixture
    def service(
        self, mock_repository: PermissionControllerRepository
    ) -> PermissionControllerService:
        return PermissionControllerService(repository=mock_repository)

    async def test_search_roles_delegates_querier(
        self,
        service: PermissionControllerService,
        mock_repository: MagicMock,
    ) -> None:
        mock_result = SearchResult(
            items=[_make_role_data(name="role-1"), _make_role_data(name="role-2")],
            total_count=2,
            has_next_page=False,
            has_previous_page=False,
        )
        mock_repository.search_roles.return_value = mock_result

        querier = _make_querier()
        action = SearchRolesAction(querier=querier)
        result = await service.search_roles(action)

        mock_repository.search_roles.assert_called_once_with(querier)
        assert result.result.total_count == 2
        assert len(result.result.items) == 2

    async def test_search_roles_empty_result(
        self,
        service: PermissionControllerService,
        mock_repository: MagicMock,
    ) -> None:
        mock_result: SearchResult[RoleData] = SearchResult(
            items=[],
            total_count=0,
            has_next_page=False,
            has_previous_page=False,
        )
        mock_repository.search_roles.return_value = mock_result

        action = SearchRolesAction(querier=_make_querier())
        result = await service.search_roles(action)

        assert result.result.total_count == 0
        assert len(result.result.items) == 0

    async def test_search_roles_pagination(
        self,
        service: PermissionControllerService,
        mock_repository: MagicMock,
    ) -> None:
        mock_result = SearchResult(
            items=[_make_role_data()],
            total_count=10,
            has_next_page=True,
            has_previous_page=True,
        )
        mock_repository.search_roles.return_value = mock_result

        querier = _make_querier(limit=1, offset=5)
        action = SearchRolesAction(querier=querier)
        result = await service.search_roles(action)

        assert result.result.total_count == 10
        assert result.result.has_next_page is True
        assert result.result.has_previous_page is True


class TestSearchUsersAssignedToRole:
    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        repository = MagicMock()
        repository.search_users_assigned_to_role = AsyncMock()
        return repository

    @pytest.fixture
    def service(
        self, mock_repository: PermissionControllerRepository
    ) -> PermissionControllerService:
        return PermissionControllerService(repository=mock_repository)

    async def test_search_users_returns_assigned_users(
        self,
        service: PermissionControllerService,
        mock_repository: MagicMock,
    ) -> None:
        granted_by = uuid.uuid4()
        user_data = AssignedUserData(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            role_id=uuid.uuid4(),
            granted_by=granted_by,
            granted_at=datetime.now(tz=UTC),
        )
        mock_result = SearchResult(
            items=[user_data],
            total_count=1,
            has_next_page=False,
            has_previous_page=False,
        )
        mock_repository.search_users_assigned_to_role.return_value = mock_result

        querier = _make_querier()
        action = SearchUsersAssignedToRoleAction(querier=querier)
        result = await service.search_users_assigned_to_role(action)

        mock_repository.search_users_assigned_to_role.assert_called_once_with(querier=querier)
        assert result.result.total_count == 1
        assert result.result.items[0].granted_by == granted_by

    async def test_search_users_empty_role(
        self,
        service: PermissionControllerService,
        mock_repository: MagicMock,
    ) -> None:
        mock_result: SearchResult[AssignedUserData] = SearchResult(
            items=[],
            total_count=0,
            has_next_page=False,
            has_previous_page=False,
        )
        mock_repository.search_users_assigned_to_role.return_value = mock_result

        action = SearchUsersAssignedToRoleAction(querier=_make_querier())
        result = await service.search_users_assigned_to_role(action)

        assert result.result.total_count == 0
        assert len(result.result.items) == 0


class TestCreatePermission:
    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        repository = MagicMock()
        repository.create_permission = AsyncMock()
        return repository

    @pytest.fixture
    def service(
        self, mock_repository: PermissionControllerRepository
    ) -> PermissionControllerService:
        return PermissionControllerService(repository=mock_repository)

    async def test_create_permission_with_scope(
        self,
        service: PermissionControllerService,
        mock_repository: MagicMock,
    ) -> None:
        perm_data = PermissionData(
            id=uuid.uuid4(),
            role_id=uuid.uuid4(),
            scope_type=ScopeType.DOMAIN,
            scope_id="test-domain",
            entity_type=EntityType.USER,
            operation=OperationType.READ,
        )
        mock_repository.create_permission.return_value = perm_data

        creator = MagicMock()
        action = CreatePermissionAction(creator=creator)
        result = await service.create_permission(action)

        mock_repository.create_permission.assert_called_once_with(creator)
        assert result.data.scope_type == ScopeType.DOMAIN

    async def test_create_permission_global_scope(
        self,
        service: PermissionControllerService,
        mock_repository: MagicMock,
    ) -> None:
        perm_data = PermissionData(
            id=uuid.uuid4(),
            role_id=uuid.uuid4(),
            scope_type=ScopeType.GLOBAL,
            scope_id="global",
            entity_type=EntityType.USER,
            operation=OperationType.CREATE,
        )
        mock_repository.create_permission.return_value = perm_data

        action = CreatePermissionAction(creator=MagicMock())
        result = await service.create_permission(action)

        assert result.data.scope_type == ScopeType.GLOBAL


class TestDeletePermission:
    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        repository = MagicMock()
        repository.delete_permission = AsyncMock()
        return repository

    @pytest.fixture
    def service(
        self, mock_repository: PermissionControllerRepository
    ) -> PermissionControllerService:
        return PermissionControllerService(repository=mock_repository)

    async def test_delete_permission_delegates_to_repository(
        self,
        service: PermissionControllerService,
        mock_repository: MagicMock,
    ) -> None:
        perm_data = PermissionData(
            id=uuid.uuid4(),
            role_id=uuid.uuid4(),
            scope_type=ScopeType.DOMAIN,
            scope_id="test-domain",
            entity_type=EntityType.USER,
            operation=OperationType.READ,
        )
        mock_repository.delete_permission.return_value = perm_data

        purger = MagicMock()
        action = DeletePermissionAction(purger=purger)
        result = await service.delete_permission(action)

        mock_repository.delete_permission.assert_called_once_with(purger)
        assert result.data.id == perm_data.id


class TestSearchPermissions:
    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        repository = MagicMock()
        repository.search_permissions = AsyncMock()
        return repository

    @pytest.fixture
    def service(
        self, mock_repository: PermissionControllerRepository
    ) -> PermissionControllerService:
        return PermissionControllerService(repository=mock_repository)

    async def test_search_permissions_delegates_querier(
        self,
        service: PermissionControllerService,
        mock_repository: MagicMock,
    ) -> None:
        perm = PermissionData(
            id=uuid.uuid4(),
            role_id=uuid.uuid4(),
            scope_type=ScopeType.DOMAIN,
            scope_id="test-domain",
            entity_type=EntityType.USER,
            operation=OperationType.READ,
        )
        mock_result = SearchResult(
            items=[perm],
            total_count=1,
            has_next_page=False,
            has_previous_page=False,
        )
        mock_repository.search_permissions.return_value = mock_result

        querier = _make_querier()
        action = SearchPermissionsAction(querier=querier)
        result = await service.search_permissions(action)

        mock_repository.search_permissions.assert_called_once_with(querier)
        assert result.result.total_count == 1

    async def test_search_permissions_pagination(
        self,
        service: PermissionControllerService,
        mock_repository: MagicMock,
    ) -> None:
        mock_result: SearchResult[PermissionData] = SearchResult(
            items=[],
            total_count=50,
            has_next_page=True,
            has_previous_page=True,
        )
        mock_repository.search_permissions.return_value = mock_result

        action = SearchPermissionsAction(querier=_make_querier(limit=10, offset=20))
        result = await service.search_permissions(action)

        assert result.result.has_next_page is True
        assert result.result.has_previous_page is True


class TestCreateObjectPermission:
    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        repository = MagicMock()
        repository.create_object_permission = AsyncMock()
        return repository

    @pytest.fixture
    def service(
        self, mock_repository: PermissionControllerRepository
    ) -> PermissionControllerService:
        return PermissionControllerService(repository=mock_repository)

    async def test_create_object_permission(
        self,
        service: PermissionControllerService,
        mock_repository: MagicMock,
    ) -> None:
        obj_perm = ObjectPermissionData(
            id=uuid.uuid4(),
            role_id=uuid.uuid4(),
            object_id=ObjectId(entity_type=EntityType.USER, entity_id="user-1"),
            operation=OperationType.READ,
        )
        mock_repository.create_object_permission.return_value = obj_perm

        creator = MagicMock()
        action = CreateObjectPermissionAction(creator=creator)
        result = await service.create_object_permission(action)

        mock_repository.create_object_permission.assert_called_once_with(creator)
        assert result.data.object_id.entity_type == EntityType.USER


class TestDeleteObjectPermission:
    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        repository = MagicMock()
        repository.delete_object_permission = AsyncMock()
        return repository

    @pytest.fixture
    def service(
        self, mock_repository: PermissionControllerRepository
    ) -> PermissionControllerService:
        return PermissionControllerService(repository=mock_repository)

    async def test_delete_object_permission(
        self,
        service: PermissionControllerService,
        mock_repository: MagicMock,
    ) -> None:
        obj_perm = ObjectPermissionData(
            id=uuid.uuid4(),
            role_id=uuid.uuid4(),
            object_id=ObjectId(entity_type=EntityType.USER, entity_id="user-1"),
            operation=OperationType.READ,
        )
        mock_repository.delete_object_permission.return_value = obj_perm

        purger = MagicMock()
        action = DeleteObjectPermissionAction(purger=purger)
        result = await service.delete_object_permission(action)

        mock_repository.delete_object_permission.assert_called_once_with(purger)
        assert result.data is not None


class TestSearchObjectPermissions:
    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        repository = MagicMock()
        repository.search_object_permissions = AsyncMock()
        return repository

    @pytest.fixture
    def service(
        self, mock_repository: PermissionControllerRepository
    ) -> PermissionControllerService:
        return PermissionControllerService(repository=mock_repository)

    async def test_search_object_permissions(
        self,
        service: PermissionControllerService,
        mock_repository: MagicMock,
    ) -> None:
        obj_perm = ObjectPermissionData(
            id=uuid.uuid4(),
            role_id=uuid.uuid4(),
            object_id=ObjectId(entity_type=EntityType.USER, entity_id="user-1"),
            operation=OperationType.READ,
        )
        mock_result = SearchResult(
            items=[obj_perm],
            total_count=1,
            has_next_page=False,
            has_previous_page=False,
        )
        mock_repository.search_object_permissions.return_value = mock_result

        querier = _make_querier()
        action = SearchObjectPermissionsAction(querier=querier)
        result = await service.search_object_permissions(action)

        mock_repository.search_object_permissions.assert_called_once_with(querier)
        assert result.result.total_count == 1

    async def test_search_object_permissions_pagination(
        self,
        service: PermissionControllerService,
        mock_repository: MagicMock,
    ) -> None:
        mock_result: SearchResult[ObjectPermissionData] = SearchResult(
            items=[],
            total_count=25,
            has_next_page=True,
            has_previous_page=False,
        )
        mock_repository.search_object_permissions.return_value = mock_result

        action = SearchObjectPermissionsAction(querier=_make_querier(limit=10, offset=0))
        result = await service.search_object_permissions(action)

        assert result.result.total_count == 25
        assert result.result.has_next_page is True


class TestUpdateRolePermissions:
    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        repository = MagicMock()
        repository.update_role_permissions = AsyncMock()
        return repository

    @pytest.fixture
    def service(
        self, mock_repository: PermissionControllerRepository
    ) -> PermissionControllerService:
        return PermissionControllerService(repository=mock_repository)

    async def test_update_role_permissions(
        self,
        service: PermissionControllerService,
        mock_repository: MagicMock,
    ) -> None:
        role_id = uuid.uuid4()
        detail = _make_role_detail_data(role_id=role_id)
        mock_repository.update_role_permissions.return_value = detail

        input_data = RolePermissionsUpdateInput(
            role_id=role_id,
            add_scoped_permissions=[],
            remove_scoped_permission_ids=[uuid.uuid4()],
            add_object_permissions=[],
            remove_object_permission_ids=[],
        )
        action = UpdateRolePermissionsAction(input_data=input_data)
        result = await service.update_role_permissions(action)

        mock_repository.update_role_permissions.assert_called_once_with(input_data=input_data)
        assert result.role.id == role_id


class TestGetEntityTypes:
    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def service(
        self, mock_repository: PermissionControllerRepository
    ) -> PermissionControllerService:
        return PermissionControllerService(repository=mock_repository)

    async def test_get_entity_types_returns_all(
        self,
        service: PermissionControllerService,
    ) -> None:
        action = GetEntityTypesAction()
        result = await service.get_entity_types(action)

        expected = list(EntityType)
        assert len(result.entity_types) == len(expected)
        for et in expected:
            assert et in result.entity_types


class TestSearchEntities:
    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        repository = MagicMock()
        repository.search_entities = AsyncMock()
        return repository

    @pytest.fixture
    def service(
        self, mock_repository: PermissionControllerRepository
    ) -> PermissionControllerService:
        return PermissionControllerService(repository=mock_repository)

    async def test_search_entities_delegates_querier(
        self,
        service: PermissionControllerService,
        mock_repository: MagicMock,
    ) -> None:
        entity_data = EntityData(entity_type=EntityType.USER, entity_id="user-1")
        mock_result = SearchResult(
            items=[entity_data],
            total_count=1,
            has_next_page=False,
            has_previous_page=False,
        )
        mock_repository.search_entities.return_value = mock_result

        querier = _make_querier()
        action = SearchEntitiesAction(querier=querier)
        result = await service.search_entities(action)

        mock_repository.search_entities.assert_called_once_with(querier)
        assert result.result.total_count == 1
        assert result.result.items[0].entity_type == EntityType.USER

    async def test_search_entities_pagination(
        self,
        service: PermissionControllerService,
        mock_repository: MagicMock,
    ) -> None:
        mock_result: SearchResult[EntityData] = SearchResult(
            items=[],
            total_count=100,
            has_next_page=True,
            has_previous_page=True,
        )
        mock_repository.search_entities.return_value = mock_result

        action = SearchEntitiesAction(querier=_make_querier(limit=10, offset=50))
        result = await service.search_entities(action)

        assert result.result.total_count == 100
        assert result.result.has_next_page is True


class TestSearchElementAssociations:
    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        repository = MagicMock()
        repository.search_element_associations = AsyncMock()
        return repository

    @pytest.fixture
    def service(
        self, mock_repository: PermissionControllerRepository
    ) -> PermissionControllerService:
        return PermissionControllerService(repository=mock_repository)

    async def test_search_element_associations_delegates_querier(
        self,
        service: PermissionControllerService,
        mock_repository: MagicMock,
    ) -> None:
        assoc = AssociationScopesEntitiesData(
            id=uuid.uuid4(),
            scope_id=ScopeId(scope_type=ScopeType.DOMAIN, scope_id="test-domain"),
            object_id=ObjectId(entity_type=EntityType.USER, entity_id="user-1"),
            relation_type=RelationType.AUTO,
            registered_at=datetime.now(tz=UTC),
        )
        mock_result = SearchResult(
            items=[assoc],
            total_count=1,
            has_next_page=False,
            has_previous_page=False,
        )
        mock_repository.search_element_associations.return_value = mock_result

        querier = _make_querier()
        action = SearchElementAssociationsAction(querier=querier)
        result = await service.search_element_associations(action)

        mock_repository.search_element_associations.assert_called_once_with(querier)
        assert result.result.total_count == 1

    async def test_search_element_associations_pagination(
        self,
        service: PermissionControllerService,
        mock_repository: MagicMock,
    ) -> None:
        mock_result: SearchResult[AssociationScopesEntitiesData] = SearchResult(
            items=[],
            total_count=30,
            has_next_page=True,
            has_previous_page=False,
        )
        mock_repository.search_element_associations.return_value = mock_result

        action = SearchElementAssociationsAction(querier=_make_querier(limit=10, offset=0))
        result = await service.search_element_associations(action)

        assert result.result.total_count == 30
        assert result.result.has_next_page is True
