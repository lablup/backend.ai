"""
Mock-based unit tests for GroupService.

Tests verify service layer business logic using mocked repositories.
Repository tests verify actual DB operations separately.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.data.group.types import GroupData
from ai.backend.manager.errors.resource import ProjectNotFound
from ai.backend.manager.models.group import ProjectType
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.group.admin_repository import AdminGroupRepository
from ai.backend.manager.repositories.group.creators import GroupCreatorSpec
from ai.backend.manager.repositories.group.repositories import GroupRepositories
from ai.backend.manager.repositories.group.repository import GroupRepository
from ai.backend.manager.repositories.group.updaters import GroupUpdaterSpec
from ai.backend.manager.services.group.actions.create_group import (
    CreateGroupAction,
)
from ai.backend.manager.services.group.actions.delete_group import (
    DeleteGroupAction,
)
from ai.backend.manager.services.group.actions.modify_group import (
    ModifyGroupAction,
)
from ai.backend.manager.services.group.actions.purge_group import (
    PurgeGroupAction,
)
from ai.backend.manager.services.group.service import GroupService
from ai.backend.manager.types import OptionalState, TriState


class TestCreateGroup:
    """Tests for GroupService.create_group"""

    @pytest.fixture
    def mock_group_repository(self) -> MagicMock:
        return MagicMock(spec=GroupRepository)

    @pytest.fixture
    def mock_admin_group_repository(self) -> MagicMock:
        return MagicMock(spec=AdminGroupRepository)

    @pytest.fixture
    def service(
        self,
        mock_group_repository: MagicMock,
        mock_admin_group_repository: MagicMock,
    ) -> GroupService:
        group_repositories = GroupRepositories(
            repository=mock_group_repository,
            admin_repository=mock_admin_group_repository,
        )
        return GroupService(
            storage_manager=MagicMock(),
            config_provider=MagicMock(),
            valkey_stat_client=MagicMock(),
            group_repositories=group_repositories,
        )

    @pytest.fixture
    def sample_group_data(self) -> GroupData:
        return GroupData(
            id=uuid.uuid4(),
            name="test_create_group",
            description="test group description",
            is_active=True,
            created_at=datetime.now(),
            modified_at=datetime.now(),
            integration_id=None,
            domain_name="default",
            total_resource_slots=ResourceSlot.from_user_input({}, None),
            allowed_vfolder_hosts=VFolderHostPermissionMap({}),
            dotfiles=b"\x90",
            resource_policy="default",
            type=ProjectType.GENERAL,
            container_registry={},
        )

    async def test_create_with_valid_data_returns_group(
        self,
        service: GroupService,
        mock_group_repository: MagicMock,
        sample_group_data: GroupData,
    ) -> None:
        """Create group with valid data should return created group."""
        mock_group_repository.create = AsyncMock(return_value=sample_group_data)

        action = CreateGroupAction(
            creator=Creator(
                spec=GroupCreatorSpec(
                    name=sample_group_data.name,
                    type=sample_group_data.type,
                    description=sample_group_data.description,
                    resource_policy=sample_group_data.resource_policy,
                    total_resource_slots=sample_group_data.total_resource_slots,
                    domain_name=sample_group_data.domain_name,
                    is_active=sample_group_data.is_active,
                )
            ),
        )

        result = await service.create_group(action)

        assert result.data is not None
        assert result.data.name == sample_group_data.name
        assert result.data.description == sample_group_data.description
        mock_group_repository.create.assert_called_once_with(action.creator)

    async def test_create_with_duplicate_name_raises_error(
        self,
        service: GroupService,
        mock_group_repository: MagicMock,
    ) -> None:
        """Create group with duplicate name should raise InvalidAPIParameters."""
        mock_group_repository.create = AsyncMock(
            side_effect=InvalidAPIParameters("Group name already exists")
        )

        action = CreateGroupAction(
            creator=Creator(
                spec=GroupCreatorSpec(
                    name="default",
                    type=ProjectType.GENERAL,
                    description="duplicate group",
                    resource_policy="default",
                    total_resource_slots=ResourceSlot.from_user_input({}, None),
                    domain_name="default",
                )
            ),
        )

        with pytest.raises(InvalidAPIParameters):
            await service.create_group(action)

    async def test_create_with_invalid_resource_policy_raises_error(
        self,
        service: GroupService,
        mock_group_repository: MagicMock,
    ) -> None:
        """Create group with invalid resource policy should raise InvalidAPIParameters."""
        mock_group_repository.create = AsyncMock(
            side_effect=InvalidAPIParameters("Invalid resource policy")
        )

        action = CreateGroupAction(
            creator=Creator(
                spec=GroupCreatorSpec(
                    name="test_create_group_without_resource_policy",
                    type=ProjectType.GENERAL,
                    description="test group description",
                    resource_policy="",
                    total_resource_slots=ResourceSlot.from_user_input({}, None),
                    domain_name="default",
                )
            )
        )

        with pytest.raises(InvalidAPIParameters):
            await service.create_group(action)


class TestModifyGroup:
    """Tests for GroupService.modify_group"""

    @pytest.fixture
    def mock_group_repository(self) -> MagicMock:
        return MagicMock(spec=GroupRepository)

    @pytest.fixture
    def mock_admin_group_repository(self) -> MagicMock:
        return MagicMock(spec=AdminGroupRepository)

    @pytest.fixture
    def service(
        self,
        mock_group_repository: MagicMock,
        mock_admin_group_repository: MagicMock,
    ) -> GroupService:
        group_repositories = GroupRepositories(
            repository=mock_group_repository,
            admin_repository=mock_admin_group_repository,
        )
        return GroupService(
            storage_manager=MagicMock(),
            config_provider=MagicMock(),
            valkey_stat_client=MagicMock(),
            group_repositories=group_repositories,
        )

    @pytest.fixture
    def modified_group_data(self) -> GroupData:
        return GroupData(
            id=uuid.uuid4(),
            name="modified_name",
            description="modified description",
            is_active=False,
            created_at=datetime.now(),
            modified_at=datetime.now(),
            integration_id=None,
            domain_name="default",
            total_resource_slots=ResourceSlot.from_user_input({}, None),
            allowed_vfolder_hosts=VFolderHostPermissionMap({}),
            dotfiles=b"\x90",
            resource_policy="default",
            type=ProjectType.GENERAL,
            container_registry={},
        )

    async def test_modify_with_valid_data_returns_updated_group(
        self,
        service: GroupService,
        mock_group_repository: MagicMock,
        modified_group_data: GroupData,
    ) -> None:
        """Modify group with valid data should return updated group."""
        mock_group_repository.modify_validated = AsyncMock(return_value=modified_group_data)
        assert modified_group_data.description is not None

        action = ModifyGroupAction(
            updater=Updater(
                spec=GroupUpdaterSpec(
                    name=OptionalState.update(modified_group_data.name),
                    description=TriState.update(modified_group_data.description),
                    is_active=OptionalState.update(modified_group_data.is_active),
                ),
                pk_value=modified_group_data.id,
            ),
        )

        result = await service.modify_group(action)

        assert result.data is not None
        assert result.data.name == modified_group_data.name
        assert result.data.description == modified_group_data.description
        assert result.data.is_active == modified_group_data.is_active

    async def test_modify_nonexistent_group_raises_not_found(
        self,
        service: GroupService,
        mock_group_repository: MagicMock,
    ) -> None:
        """Modify non-existent group should raise ProjectNotFound."""
        mock_group_repository.modify_validated = AsyncMock(
            side_effect=ProjectNotFound("Group not found")
        )

        action = ModifyGroupAction(
            updater=Updater(
                spec=GroupUpdaterSpec(
                    name=OptionalState.update("modified_name"),
                    description=TriState.update("modified description"),
                    is_active=OptionalState.update(False),
                ),
                pk_value=uuid.UUID("00000000-0000-0000-0000-000000000000"),
            ),
        )

        with pytest.raises(ProjectNotFound):
            await service.modify_group(action)


class TestDeleteGroup:
    """Tests for GroupService.delete_group"""

    @pytest.fixture
    def mock_group_repository(self) -> MagicMock:
        return MagicMock(spec=GroupRepository)

    @pytest.fixture
    def mock_admin_group_repository(self) -> MagicMock:
        return MagicMock(spec=AdminGroupRepository)

    @pytest.fixture
    def service(
        self,
        mock_group_repository: MagicMock,
        mock_admin_group_repository: MagicMock,
    ) -> GroupService:
        group_repositories = GroupRepositories(
            repository=mock_group_repository,
            admin_repository=mock_admin_group_repository,
        )
        return GroupService(
            storage_manager=MagicMock(),
            config_provider=MagicMock(),
            valkey_stat_client=MagicMock(),
            group_repositories=group_repositories,
        )

    async def test_delete_existing_group_returns_group_id(
        self,
        service: GroupService,
        mock_group_repository: MagicMock,
    ) -> None:
        """Delete existing group should return the group id."""
        group_id = uuid.uuid4()
        mock_group_repository.mark_inactive = AsyncMock(return_value=None)

        action = DeleteGroupAction(group_id=group_id)

        result = await service.delete_group(action)

        assert result.group_id == group_id
        mock_group_repository.mark_inactive.assert_called_once_with(group_id)


class TestPurgeGroup:
    """Tests for GroupService.purge_group"""

    @pytest.fixture
    def mock_group_repository(self) -> MagicMock:
        return MagicMock(spec=GroupRepository)

    @pytest.fixture
    def mock_admin_group_repository(self) -> MagicMock:
        return MagicMock(spec=AdminGroupRepository)

    @pytest.fixture
    def service(
        self,
        mock_group_repository: MagicMock,
        mock_admin_group_repository: MagicMock,
    ) -> GroupService:
        group_repositories = GroupRepositories(
            repository=mock_group_repository,
            admin_repository=mock_admin_group_repository,
        )
        return GroupService(
            storage_manager=MagicMock(),
            config_provider=MagicMock(),
            valkey_stat_client=MagicMock(),
            group_repositories=group_repositories,
        )

    async def test_purge_group_calls_admin_repository(
        self,
        service: GroupService,
        mock_admin_group_repository: MagicMock,
    ) -> None:
        """Purge group should call admin repository purge_group_force."""
        group_id = uuid.uuid4()
        mock_admin_group_repository.purge_group_force = AsyncMock(return_value=None)

        action = PurgeGroupAction(group_id=group_id)

        result = await service.purge_group(action)

        assert result.group_id == group_id
        mock_admin_group_repository.purge_group_force.assert_called_once_with(group_id)
