"""Tests for GroupConfigService functionality."""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.contexts.user import UserData, with_user
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.errors.resource import ProjectNotFound
from ai.backend.manager.errors.storage import (
    DotfileAlreadyExists,
    DotfileCreationFailed,
    DotfileNotFound,
)
from ai.backend.manager.repositories.group_config.repository import GroupConfigRepository
from ai.backend.manager.services.group_config.actions.create_dotfile import CreateDotfileAction
from ai.backend.manager.services.group_config.actions.delete_dotfile import DeleteDotfileAction
from ai.backend.manager.services.group_config.actions.get_dotfile import GetDotfileAction
from ai.backend.manager.services.group_config.actions.list_dotfiles import ListDotfilesAction
from ai.backend.manager.services.group_config.actions.update_dotfile import UpdateDotfileAction
from ai.backend.manager.services.group_config.service import GroupConfigService


@pytest.fixture
def mock_repo() -> AsyncMock:
    return AsyncMock(spec=GroupConfigRepository)


@pytest.fixture
def service(mock_repo: AsyncMock) -> GroupConfigService:
    return GroupConfigService(mock_repo)


@pytest.fixture
def group_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def domain_name() -> str:
    return "default"


@pytest.fixture
def user_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def user_context(user_id: uuid.UUID, domain_name: str) -> Iterator[UserData]:
    """Set up user context for service tests."""
    user_data = UserData(
        user_id=user_id,
        is_authorized=True,
        is_admin=True,
        is_superadmin=True,
        role="superadmin",
        domain_name=domain_name,
    )
    with with_user(user_data):
        yield user_data


class TestCreateDotfile:
    @pytest.mark.asyncio
    async def test_create_dotfile_success(
        self,
        service: GroupConfigService,
        mock_repo: AsyncMock,
        group_id: uuid.UUID,
        domain_name: str,
        user_context: UserData,
    ) -> None:
        mock_repo.resolve_group_for_admin.return_value = (group_id, domain_name)
        mock_repo.get_dotfiles.return_value = ([], 64000)
        action = CreateDotfileAction(
            group_id_or_name=group_id,
            domain_name=domain_name,
            path=".bashrc",
            data="# test bashrc",
            permission="644",
        )

        result = await service.create_dotfile(action)

        assert result.group_id == group_id
        mock_repo.get_dotfiles.assert_called_once_with(group_id)
        mock_repo.update_dotfiles.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_dotfile_no_leftover_space(
        self,
        service: GroupConfigService,
        mock_repo: AsyncMock,
        group_id: uuid.UUID,
        domain_name: str,
        user_context: UserData,
    ) -> None:
        mock_repo.resolve_group_for_admin.return_value = (group_id, domain_name)
        mock_repo.get_dotfiles.return_value = ([], 0)
        action = CreateDotfileAction(
            group_id_or_name=group_id,
            domain_name=domain_name,
            path=".bashrc",
            data="# test",
            permission="644",
        )

        with pytest.raises(DotfileCreationFailed, match="No leftover space"):
            await service.create_dotfile(action)

    @pytest.mark.asyncio
    async def test_create_dotfile_limit_reached(
        self,
        service: GroupConfigService,
        mock_repo: AsyncMock,
        group_id: uuid.UUID,
        domain_name: str,
        user_context: UserData,
    ) -> None:
        mock_repo.resolve_group_for_admin.return_value = (group_id, domain_name)
        # Create 100 existing dotfiles
        existing_dotfiles = [
            {"path": f".file{i}", "perm": "644", "data": "# test"} for i in range(100)
        ]
        mock_repo.get_dotfiles.return_value = (existing_dotfiles, 64000)
        action = CreateDotfileAction(
            group_id_or_name=group_id,
            domain_name=domain_name,
            path=".bashrc",
            data="# test",
            permission="644",
        )

        with pytest.raises(DotfileCreationFailed, match="limit reached"):
            await service.create_dotfile(action)

    @pytest.mark.asyncio
    async def test_create_dotfile_reserved_path(
        self,
        service: GroupConfigService,
        mock_repo: AsyncMock,
        group_id: uuid.UUID,
        domain_name: str,
        user_context: UserData,
    ) -> None:
        mock_repo.resolve_group_for_admin.return_value = (group_id, domain_name)
        mock_repo.get_dotfiles.return_value = ([], 64000)
        action = CreateDotfileAction(
            group_id_or_name=group_id,
            domain_name=domain_name,
            path=".ssh/authorized_keys",  # Reserved path
            data="# test",
            permission="644",
        )

        with pytest.raises(InvalidAPIParameters, match="reserved"):
            await service.create_dotfile(action)

    @pytest.mark.asyncio
    async def test_create_dotfile_duplicate_path(
        self,
        service: GroupConfigService,
        mock_repo: AsyncMock,
        group_id: uuid.UUID,
        domain_name: str,
        user_context: UserData,
    ) -> None:
        mock_repo.resolve_group_for_admin.return_value = (group_id, domain_name)
        existing_dotfiles = [{"path": ".bashrc", "perm": "644", "data": "# existing"}]
        mock_repo.get_dotfiles.return_value = (existing_dotfiles, 64000)
        action = CreateDotfileAction(
            group_id_or_name=group_id,
            domain_name=domain_name,
            path=".bashrc",
            data="# new",
            permission="644",
        )

        with pytest.raises(DotfileAlreadyExists):
            await service.create_dotfile(action)

    @pytest.mark.asyncio
    async def test_create_dotfile_exceeds_max_size(
        self,
        service: GroupConfigService,
        mock_repo: AsyncMock,
        group_id: uuid.UUID,
        domain_name: str,
        user_context: UserData,
    ) -> None:
        mock_repo.resolve_group_for_admin.return_value = (group_id, domain_name)
        mock_repo.get_dotfiles.return_value = ([], 64000)
        # Create large data that exceeds maximum size
        large_data = "x" * 70000
        action = CreateDotfileAction(
            group_id_or_name=group_id,
            domain_name=domain_name,
            path=".bashrc",
            data=large_data,
            permission="644",
        )

        with pytest.raises(DotfileCreationFailed, match="No leftover space"):
            await service.create_dotfile(action)


class TestListDotfiles:
    @pytest.mark.asyncio
    async def test_list_dotfiles_success(
        self,
        service: GroupConfigService,
        mock_repo: AsyncMock,
        group_id: uuid.UUID,
        domain_name: str,
        user_context: UserData,
    ) -> None:
        mock_repo.resolve_group_for_user.return_value = (group_id, domain_name)
        expected_dotfiles = [
            {"path": ".bashrc", "perm": "644", "data": "# bash"},
            {"path": ".zshrc", "perm": "644", "data": "# zsh"},
        ]
        mock_repo.get_dotfiles.return_value = (expected_dotfiles, 64000)
        action = ListDotfilesAction(group_id_or_name=group_id, domain_name=domain_name)

        result = await service.list_dotfiles(action)

        assert result.dotfiles == expected_dotfiles
        mock_repo.get_dotfiles.assert_called_once_with(group_id)

    @pytest.mark.asyncio
    async def test_list_dotfiles_empty(
        self,
        service: GroupConfigService,
        mock_repo: AsyncMock,
        group_id: uuid.UUID,
        domain_name: str,
        user_context: UserData,
    ) -> None:
        mock_repo.resolve_group_for_user.return_value = (group_id, domain_name)
        mock_repo.get_dotfiles.return_value = ([], 64000)
        action = ListDotfilesAction(group_id_or_name=group_id, domain_name=domain_name)

        result = await service.list_dotfiles(action)

        assert result.dotfiles == []


class TestGetDotfile:
    @pytest.mark.asyncio
    async def test_get_dotfile_success(
        self,
        service: GroupConfigService,
        mock_repo: AsyncMock,
        group_id: uuid.UUID,
        domain_name: str,
        user_context: UserData,
    ) -> None:
        mock_repo.resolve_group_for_user.return_value = (group_id, domain_name)
        existing_dotfiles = [
            {"path": ".bashrc", "perm": "644", "data": "# bash"},
            {"path": ".zshrc", "perm": "644", "data": "# zsh"},
        ]
        mock_repo.get_dotfiles.return_value = (existing_dotfiles, 64000)
        action = GetDotfileAction(
            group_id_or_name=group_id, domain_name=domain_name, path=".bashrc"
        )

        result = await service.get_dotfile(action)

        assert result.dotfile["path"] == ".bashrc"
        assert result.dotfile["data"] == "# bash"

    @pytest.mark.asyncio
    async def test_get_dotfile_not_found(
        self,
        service: GroupConfigService,
        mock_repo: AsyncMock,
        group_id: uuid.UUID,
        domain_name: str,
        user_context: UserData,
    ) -> None:
        mock_repo.resolve_group_for_user.return_value = (group_id, domain_name)
        existing_dotfiles = [{"path": ".bashrc", "perm": "644", "data": "# bash"}]
        mock_repo.get_dotfiles.return_value = (existing_dotfiles, 64000)
        action = GetDotfileAction(group_id_or_name=group_id, domain_name=domain_name, path=".zshrc")

        with pytest.raises(DotfileNotFound):
            await service.get_dotfile(action)


class TestUpdateDotfile:
    @pytest.mark.asyncio
    async def test_update_dotfile_success(
        self,
        service: GroupConfigService,
        mock_repo: AsyncMock,
        group_id: uuid.UUID,
        domain_name: str,
        user_context: UserData,
    ) -> None:
        mock_repo.resolve_group_for_admin.return_value = (group_id, domain_name)
        existing_dotfiles = [{"path": ".bashrc", "perm": "644", "data": "# old"}]
        mock_repo.get_dotfiles.return_value = (existing_dotfiles, 64000)
        action = UpdateDotfileAction(
            group_id_or_name=group_id,
            domain_name=domain_name,
            path=".bashrc",
            data="# new",
            permission="755",
        )

        result = await service.update_dotfile(action)

        assert result.group_id == group_id
        mock_repo.update_dotfiles.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_dotfile_not_found(
        self,
        service: GroupConfigService,
        mock_repo: AsyncMock,
        group_id: uuid.UUID,
        domain_name: str,
        user_context: UserData,
    ) -> None:
        mock_repo.resolve_group_for_admin.return_value = (group_id, domain_name)
        existing_dotfiles = [{"path": ".bashrc", "perm": "644", "data": "# old"}]
        mock_repo.get_dotfiles.return_value = (existing_dotfiles, 64000)
        action = UpdateDotfileAction(
            group_id_or_name=group_id,
            domain_name=domain_name,
            path=".zshrc",
            data="# new",
            permission="755",
        )

        with pytest.raises(DotfileNotFound):
            await service.update_dotfile(action)

    @pytest.mark.asyncio
    async def test_update_dotfile_exceeds_max_size(
        self,
        service: GroupConfigService,
        mock_repo: AsyncMock,
        group_id: uuid.UUID,
        domain_name: str,
        user_context: UserData,
    ) -> None:
        mock_repo.resolve_group_for_admin.return_value = (group_id, domain_name)
        existing_dotfiles = [{"path": ".bashrc", "perm": "644", "data": "# old"}]
        mock_repo.get_dotfiles.return_value = (existing_dotfiles, 64000)
        large_data = "x" * 70000
        action = UpdateDotfileAction(
            group_id_or_name=group_id,
            domain_name=domain_name,
            path=".bashrc",
            data=large_data,
            permission="644",
        )

        with pytest.raises(DotfileCreationFailed, match="No leftover space"):
            await service.update_dotfile(action)


class TestDeleteDotfile:
    @pytest.mark.asyncio
    async def test_delete_dotfile_success(
        self,
        service: GroupConfigService,
        mock_repo: AsyncMock,
        group_id: uuid.UUID,
        domain_name: str,
        user_context: UserData,
    ) -> None:
        mock_repo.resolve_group_for_admin.return_value = (group_id, domain_name)
        existing_dotfiles = [{"path": ".bashrc", "perm": "644", "data": "# test"}]
        mock_repo.get_dotfiles.return_value = (existing_dotfiles, 64000)
        action = DeleteDotfileAction(
            group_id_or_name=group_id, domain_name=domain_name, path=".bashrc"
        )

        result = await service.delete_dotfile(action)

        assert result.success is True
        mock_repo.update_dotfiles.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_dotfile_not_found(
        self,
        service: GroupConfigService,
        mock_repo: AsyncMock,
        group_id: uuid.UUID,
        domain_name: str,
        user_context: UserData,
    ) -> None:
        mock_repo.resolve_group_for_admin.return_value = (group_id, domain_name)
        existing_dotfiles = [{"path": ".bashrc", "perm": "644", "data": "# test"}]
        mock_repo.get_dotfiles.return_value = (existing_dotfiles, 64000)
        action = DeleteDotfileAction(
            group_id_or_name=group_id, domain_name=domain_name, path=".zshrc"
        )

        with pytest.raises(DotfileNotFound):
            await service.delete_dotfile(action)

    @pytest.mark.asyncio
    async def test_delete_dotfile_group_not_found(
        self,
        service: GroupConfigService,
        mock_repo: AsyncMock,
        group_id: uuid.UUID,
        domain_name: str,
        user_context: UserData,
    ) -> None:
        mock_repo.resolve_group_for_admin.return_value = (group_id, domain_name)
        mock_repo.get_dotfiles.side_effect = ProjectNotFound
        action = DeleteDotfileAction(
            group_id_or_name=group_id, domain_name=domain_name, path=".bashrc"
        )

        # delete_dotfile converts ProjectNotFound to DotfileNotFound
        with pytest.raises(DotfileNotFound):
            await service.delete_dotfile(action)
