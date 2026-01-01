"""
Mock-based unit tests for DomainService.

Tests verify service layer business logic using mocked repositories.
Repository tests verify actual DB operations separately.
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest

from ai.backend.common.exception import DomainNotFound, InvalidAPIParameters
from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.data.domain.types import DomainData, UserInfo
from ai.backend.manager.errors.resource import (
    DomainDeletionFailed,
    DomainHasActiveKernels,
    DomainHasGroups,
    DomainHasUsers,
    DomainUpdateNotAllowed,
)
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.domain.admin_repository import AdminDomainRepository
from ai.backend.manager.repositories.domain.creators import DomainCreatorSpec
from ai.backend.manager.repositories.domain.repository import DomainRepository
from ai.backend.manager.repositories.domain.updaters import (
    DomainNodeUpdaterSpec,
    DomainUpdaterSpec,
)
from ai.backend.manager.services.domain.actions.create_domain import CreateDomainAction
from ai.backend.manager.services.domain.actions.create_domain_node import CreateDomainNodeAction
from ai.backend.manager.services.domain.actions.delete_domain import DeleteDomainAction
from ai.backend.manager.services.domain.actions.modify_domain import ModifyDomainAction
from ai.backend.manager.services.domain.actions.modify_domain_node import ModifyDomainNodeAction
from ai.backend.manager.services.domain.actions.purge_domain import PurgeDomainAction
from ai.backend.manager.services.domain.service import DomainService
from ai.backend.manager.types import OptionalState, TriState


@pytest.fixture
def admin_user() -> UserInfo:
    return UserInfo(
        id=UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4"),
        role=UserRole.ADMIN,
        domain_name="default",
    )


@pytest.fixture
def superadmin_user() -> UserInfo:
    return UserInfo(
        id=UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4"),
        role=UserRole.SUPERADMIN,
        domain_name="default",
    )


@pytest.fixture
def regular_user() -> UserInfo:
    return UserInfo(
        id=UUID("dfa9da54-4b28-432f-be29-c0d680c7a412"),
        role=UserRole.USER,
        domain_name="default",
    )


class TestCreateDomain:
    """Tests for DomainService.create_domain"""

    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        return MagicMock(spec=DomainRepository)

    @pytest.fixture
    def mock_admin_repository(self) -> MagicMock:
        return MagicMock(spec=AdminDomainRepository)

    @pytest.fixture
    def service(
        self,
        mock_repository: MagicMock,
        mock_admin_repository: MagicMock,
    ) -> DomainService:
        return DomainService(
            repository=mock_repository,
            admin_repository=mock_admin_repository,
        )

    @pytest.fixture
    def sample_domain_data(self) -> DomainData:
        return DomainData(
            name="test-create-domain",
            description="Test domain",
            is_active=True,
            created_at=datetime.now(),
            modified_at=datetime.now(),
            total_resource_slots=ResourceSlot.from_user_input({}, None),
            allowed_vfolder_hosts=VFolderHostPermissionMap({}),
            allowed_docker_registries=[],
            dotfiles=b"\x90",
            integration_id=None,
        )

    @pytest.fixture
    def complex_resource_domain_data(self) -> DomainData:
        return DomainData(
            name="test-complex-resources",
            description="Test domain with complex resource slots",
            is_active=True,
            created_at=datetime.now(),
            modified_at=datetime.now(),
            total_resource_slots=ResourceSlot.from_user_input(
                {"cpu": "10", "mem": "64G", "cuda.device": "2"}, None
            ),
            allowed_vfolder_hosts=VFolderHostPermissionMap({
                "host1": {"upload-file", "download-file", "mount-in-session"},
                "host2": {"download-file", "mount-in-session"},
            }),
            allowed_docker_registries=["docker.io", "registry.example.com"],
            dotfiles=b"\x90",
            integration_id=None,
        )

    async def test_create_with_valid_data_as_admin_returns_domain(
        self,
        service: DomainService,
        mock_repository: MagicMock,
        admin_user: UserInfo,
        sample_domain_data: DomainData,
    ) -> None:
        """Create domain with valid data as admin should return created domain."""
        mock_repository.create_domain_validated = AsyncMock(return_value=sample_domain_data)

        action = CreateDomainAction(
            creator=Creator(
                spec=DomainCreatorSpec(
                    name=sample_domain_data.name,
                    description=sample_domain_data.description,
                )
            ),
            user_info=admin_user,
        )

        result = await service.create_domain(action)

        assert result.domain_data.name == sample_domain_data.name
        mock_repository.create_domain_validated.assert_called_once()

    async def test_create_with_valid_data_as_superadmin_uses_force(
        self,
        service: DomainService,
        mock_admin_repository: MagicMock,
        superadmin_user: UserInfo,
        sample_domain_data: DomainData,
    ) -> None:
        """Create domain as superadmin should use force method."""
        mock_admin_repository.create_domain_force = AsyncMock(return_value=sample_domain_data)

        action = CreateDomainAction(
            creator=Creator(
                spec=DomainCreatorSpec(
                    name=sample_domain_data.name,
                    description=sample_domain_data.description,
                )
            ),
            user_info=superadmin_user,
        )

        result = await service.create_domain(action)

        assert result.domain_data.name == sample_domain_data.name
        mock_admin_repository.create_domain_force.assert_called_once()

    async def test_create_with_duplicate_name_raises_error(
        self,
        service: DomainService,
        mock_repository: MagicMock,
        admin_user: UserInfo,
    ) -> None:
        """Create domain with duplicate name should raise InvalidAPIParameters."""
        mock_repository.create_domain_validated = AsyncMock(
            side_effect=InvalidAPIParameters("Domain already exists")
        )

        action = CreateDomainAction(
            creator=Creator(
                spec=DomainCreatorSpec(
                    name="default",
                    description="Duplicate domain",
                )
            ),
            user_info=admin_user,
        )

        with pytest.raises(InvalidAPIParameters):
            await service.create_domain(action)

    async def test_create_with_empty_name_raises_error(
        self,
        service: DomainService,
        admin_user: UserInfo,
    ) -> None:
        """Create domain with empty name should raise InvalidAPIParameters."""
        action = CreateDomainAction(
            creator=Creator(
                spec=DomainCreatorSpec(
                    name="",
                    description="Test domain with empty name",
                )
            ),
            user_info=admin_user,
        )

        with pytest.raises(InvalidAPIParameters):
            await service.create_domain(action)

    async def test_create_with_complex_resource_slots(
        self,
        service: DomainService,
        mock_repository: MagicMock,
        admin_user: UserInfo,
        complex_resource_domain_data: DomainData,
    ) -> None:
        """Create domain with complex resource slots should succeed."""
        mock_repository.create_domain_validated = AsyncMock(
            return_value=complex_resource_domain_data
        )

        action = CreateDomainAction(
            creator=Creator(
                spec=DomainCreatorSpec(
                    name=complex_resource_domain_data.name,
                    description=complex_resource_domain_data.description,
                    total_resource_slots=complex_resource_domain_data.total_resource_slots,
                    allowed_vfolder_hosts={
                        "host1": ["upload-file", "download-file", "mount-in-session"],
                        "host2": ["download-file", "mount-in-session"],
                    },
                    allowed_docker_registries=complex_resource_domain_data.allowed_docker_registries,
                )
            ),
            user_info=admin_user,
        )

        result = await service.create_domain(action)

        assert result.domain_data.name == complex_resource_domain_data.name


class TestModifyDomain:
    """Tests for DomainService.modify_domain"""

    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        return MagicMock(spec=DomainRepository)

    @pytest.fixture
    def mock_admin_repository(self) -> MagicMock:
        return MagicMock(spec=AdminDomainRepository)

    @pytest.fixture
    def service(
        self,
        mock_repository: MagicMock,
        mock_admin_repository: MagicMock,
    ) -> DomainService:
        return DomainService(
            repository=mock_repository,
            admin_repository=mock_admin_repository,
        )

    @pytest.fixture
    def modified_domain_data(self) -> DomainData:
        return DomainData(
            name="test-modify-domain",
            description="Domain Description Modified",
            is_active=True,
            created_at=datetime.now(),
            modified_at=datetime.now(),
            total_resource_slots=ResourceSlot.from_user_input({}, None),
            allowed_vfolder_hosts=VFolderHostPermissionMap({}),
            allowed_docker_registries=[],
            dotfiles=b"\x90",
            integration_id=None,
        )

    @pytest.fixture
    def deactivated_domain_data(self) -> DomainData:
        return DomainData(
            name="test-domain",
            description="Test domain",
            is_active=False,
            created_at=datetime.now(),
            modified_at=datetime.now(),
            total_resource_slots=ResourceSlot.from_user_input({}, None),
            allowed_vfolder_hosts=VFolderHostPermissionMap({}),
            allowed_docker_registries=[],
            dotfiles=b"\x90",
            integration_id=None,
        )

    @pytest.fixture
    def nullified_domain_data(self) -> DomainData:
        return DomainData(
            name="test-nullify-domain",
            description=None,
            is_active=True,
            created_at=datetime.now(),
            modified_at=datetime.now(),
            total_resource_slots=ResourceSlot.from_user_input({}, None),
            allowed_vfolder_hosts=VFolderHostPermissionMap({}),
            allowed_docker_registries=[],
            dotfiles=b"\x90",
            integration_id=None,
        )

    async def test_modify_with_valid_data_returns_updated_domain(
        self,
        service: DomainService,
        mock_repository: MagicMock,
        admin_user: UserInfo,
        modified_domain_data: DomainData,
    ) -> None:
        """Modify domain with valid data should return updated domain."""
        mock_repository.modify_domain_validated = AsyncMock(return_value=modified_domain_data)
        assert modified_domain_data.description is not None

        action = ModifyDomainAction(
            user_info=admin_user,
            updater=Updater(
                spec=DomainUpdaterSpec(
                    description=TriState.update(modified_domain_data.description),
                ),
                pk_value=modified_domain_data.name,
            ),
        )

        result = await service.modify_domain(action)

        assert result.domain_data.description == modified_domain_data.description
        mock_repository.modify_domain_validated.assert_called_once()

    async def test_modify_as_superadmin_uses_force(
        self,
        service: DomainService,
        mock_admin_repository: MagicMock,
        superadmin_user: UserInfo,
        modified_domain_data: DomainData,
    ) -> None:
        """Modify domain as superadmin should use force method."""
        mock_admin_repository.modify_domain_force = AsyncMock(return_value=modified_domain_data)
        assert modified_domain_data.description is not None

        action = ModifyDomainAction(
            user_info=superadmin_user,
            updater=Updater(
                spec=DomainUpdaterSpec(
                    description=TriState.update(modified_domain_data.description),
                ),
                pk_value=modified_domain_data.name,
            ),
        )

        result = await service.modify_domain(action)

        assert result.domain_data.description == modified_domain_data.description
        mock_admin_repository.modify_domain_force.assert_called_once()

    async def test_modify_nonexistent_domain_raises_not_found(
        self,
        service: DomainService,
        mock_repository: MagicMock,
        admin_user: UserInfo,
    ) -> None:
        """Modify non-existent domain should raise DomainNotFound."""
        mock_repository.modify_domain_validated = AsyncMock(
            side_effect=DomainNotFound("Domain not found")
        )

        action = ModifyDomainAction(
            user_info=admin_user,
            updater=Updater(
                spec=DomainUpdaterSpec(
                    description=TriState.update("Modified description"),
                ),
                pk_value="not-exist-domain",
            ),
        )

        with pytest.raises(DomainNotFound):
            await service.modify_domain(action)

    async def test_modify_deactivation(
        self,
        service: DomainService,
        mock_repository: MagicMock,
        admin_user: UserInfo,
        deactivated_domain_data: DomainData,
    ) -> None:
        """Modify domain to deactivate should succeed."""
        mock_repository.modify_domain_validated = AsyncMock(return_value=deactivated_domain_data)

        action = ModifyDomainAction(
            user_info=admin_user,
            updater=Updater(
                spec=DomainUpdaterSpec(
                    is_active=OptionalState.update(deactivated_domain_data.is_active),
                ),
                pk_value=deactivated_domain_data.name,
            ),
        )

        result = await service.modify_domain(action)

        assert result.domain_data.is_active == deactivated_domain_data.is_active

    async def test_modify_with_nullify_fields(
        self,
        service: DomainService,
        mock_repository: MagicMock,
        admin_user: UserInfo,
        nullified_domain_data: DomainData,
    ) -> None:
        """Modify domain with tristate nullify should set fields to None."""
        mock_repository.modify_domain_validated = AsyncMock(return_value=nullified_domain_data)

        action = ModifyDomainAction(
            user_info=admin_user,
            updater=Updater(
                spec=DomainUpdaterSpec(
                    description=TriState.nullify(),
                    integration_id=TriState.nullify(),
                ),
                pk_value=nullified_domain_data.name,
            ),
        )

        result = await service.modify_domain(action)

        assert result.domain_data.description == nullified_domain_data.description


class TestDeleteDomain:
    """Tests for DomainService.delete_domain"""

    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        return MagicMock(spec=DomainRepository)

    @pytest.fixture
    def mock_admin_repository(self) -> MagicMock:
        return MagicMock(spec=AdminDomainRepository)

    @pytest.fixture
    def service(
        self,
        mock_repository: MagicMock,
        mock_admin_repository: MagicMock,
    ) -> DomainService:
        return DomainService(
            repository=mock_repository,
            admin_repository=mock_admin_repository,
        )

    async def test_delete_existing_domain_returns_name(
        self,
        service: DomainService,
        mock_repository: MagicMock,
        admin_user: UserInfo,
    ) -> None:
        """Delete existing domain should return domain name."""
        mock_repository.soft_delete_domain_validated = AsyncMock(return_value=None)

        action = DeleteDomainAction(name="test-delete-domain", user_info=admin_user)

        result = await service.delete_domain(action)

        assert result.name == "test-delete-domain"
        mock_repository.soft_delete_domain_validated.assert_called_once_with("test-delete-domain")

    async def test_delete_as_superadmin_uses_force(
        self,
        service: DomainService,
        mock_admin_repository: MagicMock,
        superadmin_user: UserInfo,
    ) -> None:
        """Delete domain as superadmin should use force method."""
        mock_admin_repository.soft_delete_domain_force = AsyncMock(return_value=None)

        action = DeleteDomainAction(name="test-delete-domain", user_info=superadmin_user)

        result = await service.delete_domain(action)

        assert result.name == "test-delete-domain"
        mock_admin_repository.soft_delete_domain_force.assert_called_once()

    async def test_delete_nonexistent_domain_raises_not_found(
        self,
        service: DomainService,
        mock_repository: MagicMock,
        admin_user: UserInfo,
    ) -> None:
        """Delete non-existent domain should raise DomainNotFound."""
        mock_repository.soft_delete_domain_validated = AsyncMock(
            side_effect=DomainNotFound("Domain not found")
        )

        action = DeleteDomainAction(name="not-exist-domain", user_info=admin_user)

        with pytest.raises(DomainNotFound):
            await service.delete_domain(action)


class TestPurgeDomain:
    """Tests for DomainService.purge_domain"""

    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        return MagicMock(spec=DomainRepository)

    @pytest.fixture
    def mock_admin_repository(self) -> MagicMock:
        return MagicMock(spec=AdminDomainRepository)

    @pytest.fixture
    def service(
        self,
        mock_repository: MagicMock,
        mock_admin_repository: MagicMock,
    ) -> DomainService:
        return DomainService(
            repository=mock_repository,
            admin_repository=mock_admin_repository,
        )

    async def test_purge_existing_domain_as_admin(
        self,
        service: DomainService,
        mock_repository: MagicMock,
        admin_user: UserInfo,
    ) -> None:
        """Purge existing domain as admin should call validated method."""
        mock_repository.purge_domain_validated = AsyncMock(return_value=None)

        action = PurgeDomainAction(name="test-purge-domain", user_info=admin_user)

        result = await service.purge_domain(action)

        assert result.name == "test-purge-domain"
        mock_repository.purge_domain_validated.assert_called_once_with("test-purge-domain")

    async def test_purge_as_superadmin_uses_force(
        self,
        service: DomainService,
        mock_admin_repository: MagicMock,
        superadmin_user: UserInfo,
    ) -> None:
        """Purge domain as superadmin should use force method."""
        mock_admin_repository.purge_domain_force = AsyncMock(return_value=None)

        action = PurgeDomainAction(name="test-purge-domain", user_info=superadmin_user)

        result = await service.purge_domain(action)

        assert result.name == "test-purge-domain"
        mock_admin_repository.purge_domain_force.assert_called_once()

    async def test_purge_nonexistent_domain_raises_error(
        self,
        service: DomainService,
        mock_repository: MagicMock,
        admin_user: UserInfo,
    ) -> None:
        """Purge non-existent domain should raise DomainDeletionFailed."""
        mock_repository.purge_domain_validated = AsyncMock(
            side_effect=DomainDeletionFailed("Domain not found")
        )

        action = PurgeDomainAction(name="not-exist-domain", user_info=admin_user)

        with pytest.raises(DomainDeletionFailed):
            await service.purge_domain(action)

    async def test_purge_with_active_kernels_raises_error(
        self,
        service: DomainService,
        mock_repository: MagicMock,
        admin_user: UserInfo,
    ) -> None:
        """Purge domain with active kernels should raise DomainHasActiveKernels."""
        mock_repository.purge_domain_validated = AsyncMock(
            side_effect=DomainHasActiveKernels("Domain has active kernels")
        )

        action = PurgeDomainAction(name="test-domain", user_info=admin_user)

        with pytest.raises(DomainHasActiveKernels):
            await service.purge_domain(action)

    async def test_purge_with_users_raises_error(
        self,
        service: DomainService,
        mock_repository: MagicMock,
        admin_user: UserInfo,
    ) -> None:
        """Purge domain with users should raise DomainHasUsers."""
        mock_repository.purge_domain_validated = AsyncMock(
            side_effect=DomainHasUsers("Domain has users")
        )

        action = PurgeDomainAction(name="test-domain", user_info=admin_user)

        with pytest.raises(DomainHasUsers):
            await service.purge_domain(action)

    async def test_purge_with_groups_raises_error(
        self,
        service: DomainService,
        mock_repository: MagicMock,
        admin_user: UserInfo,
    ) -> None:
        """Purge domain with groups should raise DomainHasGroups."""
        mock_repository.purge_domain_validated = AsyncMock(
            side_effect=DomainHasGroups("Domain has groups")
        )

        action = PurgeDomainAction(name="test-domain", user_info=admin_user)

        with pytest.raises(DomainHasGroups):
            await service.purge_domain(action)


class TestCreateDomainNode:
    """Tests for DomainService.create_domain_node"""

    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        return MagicMock(spec=DomainRepository)

    @pytest.fixture
    def mock_admin_repository(self) -> MagicMock:
        return MagicMock(spec=AdminDomainRepository)

    @pytest.fixture
    def service(
        self,
        mock_repository: MagicMock,
        mock_admin_repository: MagicMock,
    ) -> DomainService:
        return DomainService(
            repository=mock_repository,
            admin_repository=mock_admin_repository,
        )

    @pytest.fixture
    def sample_domain_node_data(self) -> DomainData:
        return DomainData(
            name="test-domain-node",
            description="Test domain node",
            is_active=True,
            created_at=datetime.now(),
            modified_at=datetime.now(),
            total_resource_slots=ResourceSlot.from_user_input({}, None),
            allowed_vfolder_hosts=VFolderHostPermissionMap({}),
            allowed_docker_registries=[],
            dotfiles=b"\x90",
            integration_id=None,
        )

    async def test_create_domain_node_as_admin(
        self,
        service: DomainService,
        mock_repository: MagicMock,
        admin_user: UserInfo,
        sample_domain_node_data: DomainData,
    ) -> None:
        """Create domain node as admin should call validated method."""
        mock_repository.create_domain_node_with_permissions = AsyncMock(
            return_value=sample_domain_node_data
        )

        action = CreateDomainNodeAction(
            creator=Creator(
                spec=DomainCreatorSpec(
                    name=sample_domain_node_data.name,
                    description=sample_domain_node_data.description,
                )
            ),
            user_info=admin_user,
            scaling_groups=None,
        )

        result = await service.create_domain_node(action)

        assert result.domain_data.name == sample_domain_node_data.name
        mock_repository.create_domain_node_with_permissions.assert_called_once()

    async def test_create_domain_node_as_superadmin_uses_force(
        self,
        service: DomainService,
        mock_admin_repository: MagicMock,
        superadmin_user: UserInfo,
        sample_domain_node_data: DomainData,
    ) -> None:
        """Create domain node as superadmin should use force method."""
        mock_admin_repository.create_domain_node_with_permissions_force = AsyncMock(
            return_value=sample_domain_node_data
        )

        action = CreateDomainNodeAction(
            creator=Creator(
                spec=DomainCreatorSpec(
                    name=sample_domain_node_data.name,
                    description=sample_domain_node_data.description,
                )
            ),
            user_info=superadmin_user,
            scaling_groups=["sg1", "sg2"],
        )

        result = await service.create_domain_node(action)

        assert result.domain_data.name == sample_domain_node_data.name
        mock_admin_repository.create_domain_node_with_permissions_force.assert_called_once()

    async def test_create_domain_node_with_empty_name_raises_error(
        self,
        service: DomainService,
        admin_user: UserInfo,
    ) -> None:
        """Create domain node with empty name should raise InvalidAPIParameters."""
        action = CreateDomainNodeAction(
            creator=Creator(
                spec=DomainCreatorSpec(
                    name="",
                    description="Test domain node",
                )
            ),
            user_info=admin_user,
        )

        with pytest.raises(InvalidAPIParameters):
            await service.create_domain_node(action)

    async def test_create_domain_node_with_duplicate_name_raises_error(
        self,
        service: DomainService,
        mock_repository: MagicMock,
        admin_user: UserInfo,
    ) -> None:
        """Create domain node with duplicate name should raise error."""
        mock_repository.create_domain_node_with_permissions = AsyncMock(
            side_effect=InvalidAPIParameters("Domain already exists")
        )

        action = CreateDomainNodeAction(
            creator=Creator(
                spec=DomainCreatorSpec(
                    name="default",
                    description="Duplicate domain",
                )
            ),
            user_info=admin_user,
        )

        with pytest.raises(InvalidAPIParameters):
            await service.create_domain_node(action)


class TestModifyDomainNode:
    """Tests for DomainService.modify_domain_node"""

    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        return MagicMock(spec=DomainRepository)

    @pytest.fixture
    def mock_admin_repository(self) -> MagicMock:
        return MagicMock(spec=AdminDomainRepository)

    @pytest.fixture
    def service(
        self,
        mock_repository: MagicMock,
        mock_admin_repository: MagicMock,
    ) -> DomainService:
        return DomainService(
            repository=mock_repository,
            admin_repository=mock_admin_repository,
        )

    @pytest.fixture
    def modified_domain_node_data(self) -> DomainData:
        return DomainData(
            name="test-domain-node",
            description="Modified description",
            is_active=True,
            created_at=datetime.now(),
            modified_at=datetime.now(),
            total_resource_slots=ResourceSlot.from_user_input({}, None),
            allowed_vfolder_hosts=VFolderHostPermissionMap({}),
            allowed_docker_registries=[],
            dotfiles=b"\x90",
            integration_id=None,
        )

    @pytest.fixture
    def sample_domain_data(self) -> DomainData:
        return DomainData(
            name="test-domain",
            description="Test domain",
            is_active=True,
            created_at=datetime.now(),
            modified_at=datetime.now(),
            total_resource_slots=ResourceSlot.from_user_input({}, None),
            allowed_vfolder_hosts=VFolderHostPermissionMap({}),
            allowed_docker_registries=[],
            dotfiles=b"\x90",
            integration_id=None,
        )

    async def test_modify_domain_node_as_admin(
        self,
        service: DomainService,
        mock_repository: MagicMock,
        admin_user: UserInfo,
        modified_domain_node_data: DomainData,
    ) -> None:
        """Modify domain node as admin should call validated method."""
        mock_repository.modify_domain_node_with_permissions = AsyncMock(
            return_value=modified_domain_node_data
        )
        assert modified_domain_node_data.description is not None

        action = ModifyDomainNodeAction(
            user_info=admin_user,
            updater=Updater(
                spec=DomainNodeUpdaterSpec(
                    description=TriState.update(modified_domain_node_data.description),
                ),
                pk_value=modified_domain_node_data.name,
            ),
        )

        result = await service.modify_domain_node(action)

        assert result.domain_data.description == modified_domain_node_data.description
        mock_repository.modify_domain_node_with_permissions.assert_called_once()

    async def test_modify_domain_node_as_superadmin_uses_force(
        self,
        service: DomainService,
        mock_admin_repository: MagicMock,
        superadmin_user: UserInfo,
        modified_domain_node_data: DomainData,
    ) -> None:
        """Modify domain node as superadmin should use force method."""
        mock_admin_repository.modify_domain_node_with_permissions_force = AsyncMock(
            return_value=modified_domain_node_data
        )
        assert modified_domain_node_data.description is not None

        action = ModifyDomainNodeAction(
            user_info=superadmin_user,
            updater=Updater(
                spec=DomainNodeUpdaterSpec(
                    description=TriState.update(modified_domain_node_data.description),
                ),
                pk_value=modified_domain_node_data.name,
            ),
        )

        result = await service.modify_domain_node(action)

        assert result.domain_data.description == modified_domain_node_data.description
        mock_admin_repository.modify_domain_node_with_permissions_force.assert_called_once()

    async def test_modify_domain_node_nonexistent_raises_not_found(
        self,
        service: DomainService,
        mock_repository: MagicMock,
        admin_user: UserInfo,
    ) -> None:
        """Modify non-existent domain node should raise DomainNotFound."""
        mock_repository.modify_domain_node_with_permissions = AsyncMock(
            side_effect=DomainNotFound("Domain not found")
        )

        action = ModifyDomainNodeAction(
            user_info=admin_user,
            updater=Updater(
                spec=DomainNodeUpdaterSpec(
                    description=TriState.update("Modified description"),
                ),
                pk_value="not-exist-domain",
            ),
        )

        with pytest.raises(DomainNotFound):
            await service.modify_domain_node(action)

    async def test_modify_domain_node_without_permission_raises_error(
        self,
        service: DomainService,
        mock_repository: MagicMock,
        regular_user: UserInfo,
    ) -> None:
        """Modify domain node without permission should raise DomainUpdateNotAllowed."""
        mock_repository.modify_domain_node_with_permissions = AsyncMock(
            side_effect=DomainUpdateNotAllowed("Permission denied")
        )

        action = ModifyDomainNodeAction(
            user_info=regular_user,
            updater=Updater(
                spec=DomainNodeUpdaterSpec(
                    description=TriState.update("Modified description"),
                ),
                pk_value="test-domain",
            ),
        )

        with pytest.raises(DomainUpdateNotAllowed):
            await service.modify_domain_node(action)

    async def test_modify_domain_node_with_overlapping_scaling_groups_raises_error(
        self,
        service: DomainService,
        superadmin_user: UserInfo,
    ) -> None:
        """Modify domain node with overlapping add/remove scaling groups should raise error."""
        action = ModifyDomainNodeAction(
            user_info=superadmin_user,
            updater=Updater(
                spec=DomainNodeUpdaterSpec(),
                pk_value="test-domain",
            ),
            sgroups_to_add={"sg1", "sg2"},
            sgroups_to_remove={"sg1", "sg3"},  # sg1 overlaps
        )

        with pytest.raises(InvalidAPIParameters):
            await service.modify_domain_node(action)

    async def test_modify_domain_node_with_scaling_groups_to_add(
        self,
        service: DomainService,
        mock_admin_repository: MagicMock,
        superadmin_user: UserInfo,
        sample_domain_data: DomainData,
    ) -> None:
        """Modify domain node with scaling groups to add should pass them to repository."""
        mock_admin_repository.modify_domain_node_with_permissions_force = AsyncMock(
            return_value=sample_domain_data
        )

        action = ModifyDomainNodeAction(
            user_info=superadmin_user,
            updater=Updater(
                spec=DomainNodeUpdaterSpec(),
                pk_value="test-domain",
            ),
            sgroups_to_add={"sg1", "sg2"},
            sgroups_to_remove=None,
        )

        result = await service.modify_domain_node(action)

        assert result.domain_data is not None
        mock_admin_repository.modify_domain_node_with_permissions_force.assert_called_once()

    async def test_modify_domain_node_with_scaling_groups_to_remove(
        self,
        service: DomainService,
        mock_admin_repository: MagicMock,
        superadmin_user: UserInfo,
        sample_domain_data: DomainData,
    ) -> None:
        """Modify domain node with scaling groups to remove should pass them to repository."""
        mock_admin_repository.modify_domain_node_with_permissions_force = AsyncMock(
            return_value=sample_domain_data
        )

        action = ModifyDomainNodeAction(
            user_info=superadmin_user,
            updater=Updater(
                spec=DomainNodeUpdaterSpec(),
                pk_value="test-domain",
            ),
            sgroups_to_add=None,
            sgroups_to_remove={"sg3"},
        )

        result = await service.modify_domain_node(action)

        assert result.domain_data is not None
        mock_admin_repository.modify_domain_node_with_permissions_force.assert_called_once()
