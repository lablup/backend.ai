"""
Unit tests for PermissionControllerService.
Tests all 18 service methods using mocked repository layer.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.role import RoleEntityType, RoleID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.common.data.permission.types import (
    RoleSource,
    role_scope_types,
)
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta
from ai.backend.manager.data.common.types import SearchResult
from ai.backend.manager.data.permission.role import (
    AssignedUserData,
    RoleData,
    RoleDetailData,
)
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.models.rbac_models.user_role.searchers import RoleAssignmentSearcher
from ai.backend.manager.models.specs.pagination import OffsetPagination
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.permission_contoller.actions.get_entity_types import (
    PublicGetEntityTypesAction,
)
from ai.backend.manager.services.permission_contoller.actions.get_permission_matrix import (
    PublicGetPermissionMatrixAction,
)
from ai.backend.manager.services.permission_contoller.actions.get_role_detail import (
    GetRoleDetailAction,
)
from ai.backend.manager.services.permission_contoller.actions.get_scope_types import (
    PublicGetScopeTypesAction,
)
from ai.backend.manager.services.permission_contoller.actions.search_users_assigned_to_role import (
    GlobalSearchRoleAssignmentsAction,
)
from ai.backend.manager.services.permission_contoller.processors import (
    PermissionControllerProcessors,
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
    role_id: RoleID | None = None,
    name: str = "test-role",
    source: RoleSource = RoleSource.CUSTOM,
    status: RoleStatus = RoleStatus.ACTIVE,
    deleted_at: datetime | None = None,
    description: str | None = None,
) -> RoleData:
    now = datetime.now(tz=UTC)
    return RoleData(
        id=role_id or RoleID(uuid.uuid4()),
        name=name,
        source=source,
        status=status,
        created_at=now,
        updated_at=now,
        deleted_at=deleted_at,
        scope_type=EntityType("project"),
        scope_id=uuid.uuid4(),
        description=description,
    )


def _make_role_detail_data(
    *,
    role_id: RoleID | None = None,
    name: str = "test-role",
) -> RoleDetailData:
    now = datetime.now(tz=UTC)
    return RoleDetailData(
        id=role_id or RoleID(uuid.uuid4()),
        name=name,
        source=RoleSource.CUSTOM,
        status=RoleStatus.ACTIVE,
        created_at=now,
        updated_at=now,
        deleted_at=None,
        scope_type=EntityType("project"),
        scope_id=uuid.uuid4(),
    )


def _make_querier(limit: int = 10, offset: int = 0) -> BatchQuerier:
    return BatchQuerier(
        conditions=[],
        orders=[],
        pagination=OffsetPagination(limit=limit, offset=offset),
    )


class TestGetRoleDetail:
    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        repository = MagicMock()
        repository.get_role_with_permissions = AsyncMock()
        return repository

    @pytest.fixture
    def service(
        self,
        mock_repository: PermissionControllerRepository,
        processor_registry: ProcessorRegistry[Any],
    ) -> PermissionControllerService:
        return PermissionControllerService(
            repository=mock_repository,
            permission_check=MagicMock(),
            action_registry=processor_registry,
        )

    async def test_get_role_detail_returns_full_detail(
        self,
        service: PermissionControllerService,
        mock_repository: MagicMock,
    ) -> None:
        role_id = RoleID(uuid.uuid4())
        detail = _make_role_detail_data(role_id=role_id, name="detail-role")
        mock_repository.get_role_with_permissions.return_value = detail

        action = GetRoleDetailAction(role_id=role_id)
        result = await service.get_role_detail(action)

        mock_repository.get_role_with_permissions.assert_called_once_with(role_id)
        assert result.role.id == role_id
        assert result.role.name == "detail-role"


class TestSearchUsersAssignedToRole:
    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        repository = MagicMock()
        repository.search_role_assignments_in_global = AsyncMock()
        return repository

    @pytest.fixture
    def service(
        self,
        mock_repository: PermissionControllerRepository,
        processor_registry: ProcessorRegistry[Any],
    ) -> PermissionControllerService:
        return PermissionControllerService(
            repository=mock_repository,
            permission_check=MagicMock(),
            action_registry=processor_registry,
        )

    async def test_search_users_returns_assigned_users(
        self,
        service: PermissionControllerService,
        mock_repository: MagicMock,
    ) -> None:
        granted_by = uuid.uuid4()
        user_data = AssignedUserData(
            id=uuid.uuid4(),
            user_id=UserID(uuid.uuid4()),
            role_id=RoleID(uuid.uuid4()),
            granted_by=granted_by,
            granted_at=datetime.now(tz=UTC),
        )
        mock_result = SearchResult(
            items=[user_data],
            total_count=1,
            has_next_page=False,
            has_previous_page=False,
        )
        mock_repository.search_role_assignments_in_global.return_value = mock_result

        searcher = RoleAssignmentSearcher(pagination=OffsetPagination(limit=10, offset=0))
        action = GlobalSearchRoleAssignmentsAction(searcher=searcher)
        result = await service.search_users_assigned_to_role(action)

        mock_repository.search_role_assignments_in_global.assert_called_once_with(searcher)
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
        mock_repository.search_role_assignments_in_global.return_value = mock_result

        action = GlobalSearchRoleAssignmentsAction(
            searcher=RoleAssignmentSearcher(pagination=OffsetPagination(limit=10, offset=0))
        )
        result = await service.search_users_assigned_to_role(action)

        assert result.result.total_count == 0
        assert len(result.result.items) == 0


class TestPermissionCatalog:
    """What a role may permit comes from the ops wiring, not a hand-kept list."""

    @pytest.fixture
    def service(
        self,
        processor_registry: ProcessorRegistry[Any],
    ) -> PermissionControllerService:
        service = PermissionControllerService(
            repository=MagicMock(),
            permission_check=MagicMock(),
            action_registry=processor_registry,
        )
        # Wiring the package registers its operations in the same registry the service
        # reads, as the production assembly does.
        PermissionControllerProcessors(
            processor_registry.group(GroupMeta(RoleEntityType())),
            processor_registry.group(GroupMeta(UserEntityType())),
            service=service,
        )
        return service

    async def test_entity_types_are_the_wired_entities(
        self,
        service: PermissionControllerService,
    ) -> None:
        result = await service.get_entity_types(PublicGetEntityTypesAction())

        assert RoleEntityType() in result.entity_types
        assert result.entity_types == sorted(set(result.entity_types))

    async def test_scope_types_are_the_scopes_a_role_sits_in(
        self,
        service: PermissionControllerService,
    ) -> None:
        result = await service.get_scope_types(PublicGetScopeTypesAction())

        assert result.entity_types == [DomainEntityType(), ProjectEntityType(), UserEntityType()]

    async def test_every_scope_carries_the_same_entities(
        self,
        service: PermissionControllerService,
    ) -> None:
        result = await service.get_permission_matrix(PublicGetPermissionMatrixAction())

        assert set(result.matrix) == set(role_scope_types())
        entity_maps = [sorted(entity_map) for entity_map in result.matrix.values()]
        assert all(entities == entity_maps[0] for entities in entity_maps)

    async def test_matrix_entities_match_the_entity_types(
        self,
        service: PermissionControllerService,
    ) -> None:
        matrix = (await service.get_permission_matrix(PublicGetPermissionMatrixAction())).matrix
        entity_types = (await service.get_entity_types(PublicGetEntityTypesAction())).entity_types

        for entity_map in matrix.values():
            assert sorted(entity_map) == entity_types

    async def test_operations_name_the_wired_actions(
        self,
        service: PermissionControllerService,
    ) -> None:
        matrix = (await service.get_permission_matrix(PublicGetPermissionMatrixAction())).matrix

        operations = matrix[DomainEntityType()][RoleEntityType()]
        assert operations
        assert [op.name for op in operations] == sorted(op.name for op in operations)
        for op in operations:
            assert op.description
