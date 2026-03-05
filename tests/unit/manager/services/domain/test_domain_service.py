"""
Unit tests for DomainService.
Tests all 9 service methods using mocked repository layer.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.exception import DomainNotFound, InvalidAPIParameters
from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.data.domain.types import DomainData, UserInfo
from ai.backend.manager.errors.resource import (
    DomainHasActiveKernels,
    DomainHasGroups,
    DomainHasUsers,
)
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.domain.creators import DomainCreatorSpec
from ai.backend.manager.repositories.domain.types import DomainSearchResult, DomainSearchScope
from ai.backend.manager.services.domain.actions.create_domain import CreateDomainAction
from ai.backend.manager.services.domain.actions.create_domain_node import CreateDomainNodeAction
from ai.backend.manager.services.domain.actions.delete_domain import DeleteDomainAction
from ai.backend.manager.services.domain.actions.get_domain import GetDomainAction
from ai.backend.manager.services.domain.actions.modify_domain import ModifyDomainAction
from ai.backend.manager.services.domain.actions.modify_domain_node import ModifyDomainNodeAction
from ai.backend.manager.services.domain.actions.purge_domain import PurgeDomainAction
from ai.backend.manager.services.domain.actions.search_domains import SearchDomainsAction
from ai.backend.manager.services.domain.actions.search_rg_domains import SearchRGDomainsAction
from ai.backend.manager.services.domain.service import DomainService

if TYPE_CHECKING:
    from ai.backend.manager.repositories.domain.repository import DomainRepository


def _make_domain_data(
    *,
    name: str = "test-domain",
    description: str | None = None,
    is_active: bool = True,
) -> DomainData:
    now = datetime.now(tz=UTC)
    return DomainData(
        name=name,
        description=description,
        is_active=is_active,
        created_at=now,
        modified_at=now,
        total_resource_slots=ResourceSlot(),
        allowed_vfolder_hosts=VFolderHostPermissionMap(),
        allowed_docker_registries=[],
        dotfiles=b"\x90",
        integration_id=None,
    )


def _make_user_info(
    *,
    role: UserRole = UserRole.ADMIN,
    domain_name: str = "test-domain",
) -> UserInfo:
    return UserInfo(
        id=uuid.uuid4(),
        role=role,
        domain_name=domain_name,
    )


def _make_creator(name: str = "test-domain") -> MagicMock:
    spec = DomainCreatorSpec(name=name)
    creator = MagicMock()
    creator.spec = spec
    return creator


def _make_querier(limit: int = 10, offset: int = 0) -> BatchQuerier:
    return BatchQuerier(
        conditions=[],
        orders=[],
        pagination=OffsetPagination(limit=limit, offset=offset),
    )


class TestCreateDomain:
    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        repository = MagicMock()
        repository.create_domain = AsyncMock()
        return repository

    @pytest.fixture
    def service(self, mock_repository: DomainRepository) -> DomainService:
        return DomainService(repository=mock_repository)

    async def test_valid_name_creates_domain(
        self,
        service: DomainService,
        mock_repository: MagicMock,
    ) -> None:
        domain_data = _make_domain_data(name="new-domain")
        mock_repository.create_domain.return_value = domain_data

        creator = _make_creator("new-domain")
        action = CreateDomainAction(creator=creator, user_info=_make_user_info())

        result = await service.create_domain(action)

        mock_repository.create_domain.assert_called_once_with(creator)
        assert result.domain_data.name == "new-domain"
        assert result.domain_data.is_active is True

    async def test_empty_name_raises_invalid_api_parameters(
        self,
        service: DomainService,
        mock_repository: MagicMock,
    ) -> None:
        creator = _make_creator("")
        action = CreateDomainAction(creator=creator, user_info=_make_user_info())

        with pytest.raises(InvalidAPIParameters):
            await service.create_domain(action)

        mock_repository.create_domain.assert_not_called()

    async def test_whitespace_only_name_raises_invalid_api_parameters(
        self,
        service: DomainService,
        mock_repository: MagicMock,
    ) -> None:
        creator = _make_creator("   ")
        action = CreateDomainAction(creator=creator, user_info=_make_user_info())

        with pytest.raises(InvalidAPIParameters):
            await service.create_domain(action)

        mock_repository.create_domain.assert_not_called()

    async def test_name_exceeding_64_chars_raises_invalid_api_parameters(
        self,
        service: DomainService,
        mock_repository: MagicMock,
    ) -> None:
        long_name = "x" * 65
        creator = _make_creator(long_name)
        action = CreateDomainAction(creator=creator, user_info=_make_user_info())

        with pytest.raises(InvalidAPIParameters):
            await service.create_domain(action)

        mock_repository.create_domain.assert_not_called()

    async def test_name_exactly_64_chars_succeeds(
        self,
        service: DomainService,
        mock_repository: MagicMock,
    ) -> None:
        name_64 = "x" * 64
        domain_data = _make_domain_data(name=name_64)
        mock_repository.create_domain.return_value = domain_data

        creator = _make_creator(name_64)
        action = CreateDomainAction(creator=creator, user_info=_make_user_info())

        result = await service.create_domain(action)

        assert result.domain_data.name == name_64

    async def test_timestamps_set_on_creation(
        self,
        service: DomainService,
        mock_repository: MagicMock,
    ) -> None:
        domain_data = _make_domain_data()
        mock_repository.create_domain.return_value = domain_data

        creator = _make_creator()
        action = CreateDomainAction(creator=creator, user_info=_make_user_info())

        result = await service.create_domain(action)

        assert result.domain_data.created_at is not None
        assert result.domain_data.modified_at is not None


class TestGetDomain:
    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        repository = MagicMock()
        repository.get_domain = AsyncMock()
        return repository

    @pytest.fixture
    def service(self, mock_repository: DomainRepository) -> DomainService:
        return DomainService(repository=mock_repository)

    async def test_existing_domain_returns_domain_data(
        self,
        service: DomainService,
        mock_repository: MagicMock,
    ) -> None:
        domain_data = _make_domain_data(name="my-domain")
        mock_repository.get_domain.return_value = domain_data

        action = GetDomainAction(domain_name="my-domain")

        result = await service.get_domain(action)

        mock_repository.get_domain.assert_called_once_with("my-domain")
        assert result.data.name == "my-domain"

    async def test_nonexistent_domain_propagates_repository_error(
        self,
        service: DomainService,
        mock_repository: MagicMock,
    ) -> None:
        mock_repository.get_domain.side_effect = DomainNotFound

        action = GetDomainAction(domain_name="nonexistent")

        with pytest.raises(DomainNotFound):
            await service.get_domain(action)


class TestSearchDomains:
    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        repository = MagicMock()
        repository.search_domains = AsyncMock()
        return repository

    @pytest.fixture
    def service(self, mock_repository: DomainRepository) -> DomainService:
        return DomainService(repository=mock_repository)

    async def test_returns_all_active_domains(
        self,
        service: DomainService,
        mock_repository: MagicMock,
    ) -> None:
        domains = [_make_domain_data(name="dom-1"), _make_domain_data(name="dom-2")]
        mock_repository.search_domains.return_value = DomainSearchResult(
            items=domains,
            total_count=2,
            has_next_page=False,
            has_previous_page=False,
        )

        querier = _make_querier()
        action = SearchDomainsAction(querier=querier)

        result = await service.search_domains(action)

        mock_repository.search_domains.assert_called_once_with(querier=querier)
        assert len(result.items) == 2
        assert result.total_count == 2
        assert result.has_next_page is False
        assert result.has_previous_page is False

    async def test_pagination_returns_correct_subset(
        self,
        service: DomainService,
        mock_repository: MagicMock,
    ) -> None:
        domains = [_make_domain_data(name="dom-1")]
        mock_repository.search_domains.return_value = DomainSearchResult(
            items=domains,
            total_count=5,
            has_next_page=True,
            has_previous_page=True,
        )

        querier = _make_querier(limit=1, offset=2)
        action = SearchDomainsAction(querier=querier)

        result = await service.search_domains(action)

        assert len(result.items) == 1
        assert result.total_count == 5
        assert result.has_next_page is True
        assert result.has_previous_page is True

    async def test_empty_result(
        self,
        service: DomainService,
        mock_repository: MagicMock,
    ) -> None:
        mock_repository.search_domains.return_value = DomainSearchResult(
            items=[],
            total_count=0,
            has_next_page=False,
            has_previous_page=False,
        )

        action = SearchDomainsAction(querier=_make_querier())

        result = await service.search_domains(action)

        assert len(result.items) == 0
        assert result.total_count == 0


class TestModifyDomain:
    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        repository = MagicMock()
        repository.modify_domain = AsyncMock()
        return repository

    @pytest.fixture
    def service(self, mock_repository: DomainRepository) -> DomainService:
        return DomainService(repository=mock_repository)

    async def test_modify_succeeds(
        self,
        service: DomainService,
        mock_repository: MagicMock,
    ) -> None:
        updated = _make_domain_data(name="updated-domain", description="new desc")
        mock_repository.modify_domain.return_value = updated

        updater = MagicMock()
        action = ModifyDomainAction(updater=updater, user_info=_make_user_info())

        result = await service.modify_domain(action)

        mock_repository.modify_domain.assert_called_once_with(updater)
        assert result.domain_data.name == "updated-domain"
        assert result.domain_data.description == "new desc"

    async def test_nonexistent_domain_propagates_error(
        self,
        service: DomainService,
        mock_repository: MagicMock,
    ) -> None:
        mock_repository.modify_domain.side_effect = DomainNotFound

        updater = MagicMock()
        action = ModifyDomainAction(updater=updater, user_info=_make_user_info())

        with pytest.raises(DomainNotFound):
            await service.modify_domain(action)


class TestDeleteDomain:
    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        repository = MagicMock()
        repository.soft_delete_domain = AsyncMock()
        return repository

    @pytest.fixture
    def service(self, mock_repository: DomainRepository) -> DomainService:
        return DomainService(repository=mock_repository)

    async def test_soft_delete_succeeds(
        self,
        service: DomainService,
        mock_repository: MagicMock,
    ) -> None:
        action = DeleteDomainAction(name="target-domain", user_info=_make_user_info())

        result = await service.delete_domain(action)

        mock_repository.soft_delete_domain.assert_called_once_with("target-domain")
        assert result.name == "target-domain"

    async def test_nonexistent_domain_propagates_error(
        self,
        service: DomainService,
        mock_repository: MagicMock,
    ) -> None:
        mock_repository.soft_delete_domain.side_effect = DomainNotFound

        action = DeleteDomainAction(name="nonexistent", user_info=_make_user_info())

        with pytest.raises(DomainNotFound):
            await service.delete_domain(action)


class TestPurgeDomain:
    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        repository = MagicMock()
        repository.purge_domain = AsyncMock()
        return repository

    @pytest.fixture
    def service(self, mock_repository: DomainRepository) -> DomainService:
        return DomainService(repository=mock_repository)

    async def test_purge_succeeds(
        self,
        service: DomainService,
        mock_repository: MagicMock,
    ) -> None:
        action = PurgeDomainAction(name="purge-me", user_info=_make_user_info())

        result = await service.purge_domain(action)

        mock_repository.purge_domain.assert_called_once_with("purge-me")
        assert result.name == "purge-me"

    async def test_active_kernels_propagates_error(
        self,
        service: DomainService,
        mock_repository: MagicMock,
    ) -> None:
        mock_repository.purge_domain.side_effect = DomainHasActiveKernels

        action = PurgeDomainAction(name="busy-domain", user_info=_make_user_info())

        with pytest.raises(DomainHasActiveKernels):
            await service.purge_domain(action)

    async def test_bound_users_propagates_error(
        self,
        service: DomainService,
        mock_repository: MagicMock,
    ) -> None:
        mock_repository.purge_domain.side_effect = DomainHasUsers

        action = PurgeDomainAction(name="user-domain", user_info=_make_user_info())

        with pytest.raises(DomainHasUsers):
            await service.purge_domain(action)

    async def test_bound_groups_propagates_error(
        self,
        service: DomainService,
        mock_repository: MagicMock,
    ) -> None:
        mock_repository.purge_domain.side_effect = DomainHasGroups

        action = PurgeDomainAction(name="group-domain", user_info=_make_user_info())

        with pytest.raises(DomainHasGroups):
            await service.purge_domain(action)


class TestCreateDomainNode:
    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        repository = MagicMock()
        repository.create_domain_node_with_permissions = AsyncMock()
        return repository

    @pytest.fixture
    def service(self, mock_repository: DomainRepository) -> DomainService:
        return DomainService(repository=mock_repository)

    async def test_valid_name_with_scaling_groups_creates_node(
        self,
        service: DomainService,
        mock_repository: MagicMock,
    ) -> None:
        domain_data = _make_domain_data(name="node-domain")
        mock_repository.create_domain_node_with_permissions.return_value = domain_data

        user_info = _make_user_info()
        creator = _make_creator("node-domain")
        scaling_groups = ["sg-1", "sg-2"]
        action = CreateDomainNodeAction(
            user_info=user_info,
            creator=creator,
            scaling_groups=scaling_groups,
        )

        result = await service.create_domain_node(action)

        mock_repository.create_domain_node_with_permissions.assert_called_once_with(
            creator,
            user_info,
            scaling_groups,
        )
        assert result.domain_data.name == "node-domain"

    async def test_empty_name_raises_invalid_api_parameters(
        self,
        service: DomainService,
        mock_repository: MagicMock,
    ) -> None:
        creator = _make_creator("")
        action = CreateDomainNodeAction(
            user_info=_make_user_info(),
            creator=creator,
            scaling_groups=["sg-1"],
        )

        with pytest.raises(InvalidAPIParameters):
            await service.create_domain_node(action)

        mock_repository.create_domain_node_with_permissions.assert_not_called()

    async def test_name_exceeding_64_chars_raises_invalid_api_parameters(
        self,
        service: DomainService,
        mock_repository: MagicMock,
    ) -> None:
        creator = _make_creator("x" * 65)
        action = CreateDomainNodeAction(
            user_info=_make_user_info(),
            creator=creator,
        )

        with pytest.raises(InvalidAPIParameters):
            await service.create_domain_node(action)

    async def test_none_scaling_groups_passes_none_to_repository(
        self,
        service: DomainService,
        mock_repository: MagicMock,
    ) -> None:
        domain_data = _make_domain_data(name="no-sg-domain")
        mock_repository.create_domain_node_with_permissions.return_value = domain_data

        user_info = _make_user_info()
        creator = _make_creator("no-sg-domain")
        action = CreateDomainNodeAction(
            user_info=user_info,
            creator=creator,
            scaling_groups=None,
        )

        result = await service.create_domain_node(action)

        mock_repository.create_domain_node_with_permissions.assert_called_once_with(
            creator,
            user_info,
            None,
        )
        assert result.domain_data.name == "no-sg-domain"


class TestModifyDomainNode:
    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        repository = MagicMock()
        repository.modify_domain_node_with_permissions = AsyncMock()
        return repository

    @pytest.fixture
    def service(self, mock_repository: DomainRepository) -> DomainService:
        return DomainService(repository=mock_repository)

    async def test_add_and_remove_scaling_groups_succeeds(
        self,
        service: DomainService,
        mock_repository: MagicMock,
    ) -> None:
        domain_data = _make_domain_data(name="mod-node")
        mock_repository.modify_domain_node_with_permissions.return_value = domain_data

        user_info = _make_user_info()
        updater = MagicMock()
        sgroups_to_add = {"sg-new"}
        sgroups_to_remove = {"sg-old"}
        action = ModifyDomainNodeAction(
            user_info=user_info,
            updater=updater,
            sgroups_to_add=sgroups_to_add,
            sgroups_to_remove=sgroups_to_remove,
        )

        result = await service.modify_domain_node(action)

        mock_repository.modify_domain_node_with_permissions.assert_called_once_with(
            updater,
            user_info,
            sgroups_to_add,
            sgroups_to_remove,
        )
        assert result.domain_data.name == "mod-node"

    async def test_overlapping_scaling_groups_raises_invalid_api_parameters(
        self,
        service: DomainService,
        mock_repository: MagicMock,
    ) -> None:
        updater = MagicMock()
        action = ModifyDomainNodeAction(
            user_info=_make_user_info(),
            updater=updater,
            sgroups_to_add={"sg-overlap", "sg-ok"},
            sgroups_to_remove={"sg-overlap"},
        )

        with pytest.raises(InvalidAPIParameters):
            await service.modify_domain_node(action)

        mock_repository.modify_domain_node_with_permissions.assert_not_called()

    async def test_none_scaling_groups_passes_none_to_repository(
        self,
        service: DomainService,
        mock_repository: MagicMock,
    ) -> None:
        domain_data = _make_domain_data(name="no-change")
        mock_repository.modify_domain_node_with_permissions.return_value = domain_data

        user_info = _make_user_info()
        updater = MagicMock()
        action = ModifyDomainNodeAction(
            user_info=user_info,
            updater=updater,
            sgroups_to_add=None,
            sgroups_to_remove=None,
        )

        result = await service.modify_domain_node(action)

        mock_repository.modify_domain_node_with_permissions.assert_called_once_with(
            updater,
            user_info,
            None,
            None,
        )
        assert result.domain_data.name == "no-change"

    async def test_only_add_scaling_groups_with_none_remove(
        self,
        service: DomainService,
        mock_repository: MagicMock,
    ) -> None:
        domain_data = _make_domain_data()
        mock_repository.modify_domain_node_with_permissions.return_value = domain_data

        updater = MagicMock()
        action = ModifyDomainNodeAction(
            user_info=_make_user_info(),
            updater=updater,
            sgroups_to_add={"sg-1"},
            sgroups_to_remove=None,
        )

        await service.modify_domain_node(action)

        mock_repository.modify_domain_node_with_permissions.assert_called_once()


class TestSearchRGDomains:
    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        repository = MagicMock()
        repository.search_rg_domains = AsyncMock()
        return repository

    @pytest.fixture
    def service(self, mock_repository: DomainRepository) -> DomainService:
        return DomainService(repository=mock_repository)

    async def test_returns_associated_domains(
        self,
        service: DomainService,
        mock_repository: MagicMock,
    ) -> None:
        domains = [_make_domain_data(name="rg-dom-1")]
        mock_repository.search_rg_domains.return_value = DomainSearchResult(
            items=domains,
            total_count=1,
            has_next_page=False,
            has_previous_page=False,
        )

        scope = DomainSearchScope(resource_group="rg-1")
        querier = _make_querier()
        action = SearchRGDomainsAction(scope=scope, querier=querier)

        result = await service.search_rg_domains(action)

        mock_repository.search_rg_domains.assert_called_once_with(
            scope=scope,
            querier=querier,
        )
        assert len(result.items) == 1
        assert result.items[0].name == "rg-dom-1"
        assert result.total_count == 1

    async def test_no_associations_returns_empty_result(
        self,
        service: DomainService,
        mock_repository: MagicMock,
    ) -> None:
        mock_repository.search_rg_domains.return_value = DomainSearchResult(
            items=[],
            total_count=0,
            has_next_page=False,
            has_previous_page=False,
        )

        scope = DomainSearchScope(resource_group="empty-rg")
        action = SearchRGDomainsAction(scope=scope, querier=_make_querier())

        result = await service.search_rg_domains(action)

        assert len(result.items) == 0
        assert result.total_count == 0
        assert result.has_next_page is False
        assert result.has_previous_page is False
