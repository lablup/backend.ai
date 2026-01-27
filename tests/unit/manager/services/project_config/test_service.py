"""Tests for ProjectConfigService functionality."""

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
from ai.backend.manager.models.group import GroupDotfile
from ai.backend.manager.repositories.project_config.repository import ProjectConfigRepository
from ai.backend.manager.repositories.project_config.types import (
    ProjectDotfilesResult,
    ResolvedProject,
)
from ai.backend.manager.services.project_config.actions.create_dotfile import CreateDotfileAction
from ai.backend.manager.services.project_config.actions.delete_dotfile import DeleteDotfileAction
from ai.backend.manager.services.project_config.actions.get_dotfile import GetDotfileAction
from ai.backend.manager.services.project_config.actions.list_dotfiles import ListDotfilesAction
from ai.backend.manager.services.project_config.actions.update_dotfile import UpdateDotfileAction
from ai.backend.manager.services.project_config.service import ProjectConfigService


@pytest.fixture
def mock_repo() -> AsyncMock:
    return AsyncMock(spec=ProjectConfigRepository)


@pytest.fixture
def service(mock_repo: AsyncMock) -> ProjectConfigService:
    return ProjectConfigService(mock_repo)


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
def resolved_project(group_id: uuid.UUID, domain_name: str) -> ResolvedProject:
    return ResolvedProject(id=group_id, domain_name=domain_name)


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
        service: ProjectConfigService,
        mock_repo: AsyncMock,
        group_id: uuid.UUID,
        domain_name: str,
        resolved_project: ResolvedProject,
        user_context: UserData,
    ) -> None:
        mock_repo.resolve_group.return_value = resolved_project
        action = CreateDotfileAction(
            group_id_or_name=group_id,
            domain_name=domain_name,
            path=".bashrc",
            data="# test bashrc",
            permission="644",
        )

        result = await service.create_dotfile(action)

        assert result.group_id == group_id
        mock_repo.add_dotfile.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_dotfile_reserved_path(
        self,
        service: ProjectConfigService,
        mock_repo: AsyncMock,
        group_id: uuid.UUID,
        domain_name: str,
        resolved_project: ResolvedProject,
        user_context: UserData,
    ) -> None:
        mock_repo.resolve_group.return_value = resolved_project
        action = CreateDotfileAction(
            group_id_or_name=group_id,
            domain_name=domain_name,
            path=".ssh/authorized_keys",
            data="# test",
            permission="644",
        )

        with pytest.raises(InvalidAPIParameters, match="reserved"):
            await service.create_dotfile(action)

    @pytest.mark.asyncio
    async def test_create_dotfile_no_leftover_space(
        self,
        service: ProjectConfigService,
        mock_repo: AsyncMock,
        group_id: uuid.UUID,
        domain_name: str,
        resolved_project: ResolvedProject,
        user_context: UserData,
    ) -> None:
        mock_repo.resolve_group.return_value = resolved_project
        mock_repo.add_dotfile.side_effect = DotfileCreationFailed(
            "No leftover space for dotfile storage"
        )
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
        service: ProjectConfigService,
        mock_repo: AsyncMock,
        group_id: uuid.UUID,
        domain_name: str,
        resolved_project: ResolvedProject,
        user_context: UserData,
    ) -> None:
        mock_repo.resolve_group.return_value = resolved_project
        mock_repo.add_dotfile.side_effect = DotfileCreationFailed("Dotfile creation limit reached")
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
    async def test_create_dotfile_duplicate_path(
        self,
        service: ProjectConfigService,
        mock_repo: AsyncMock,
        group_id: uuid.UUID,
        domain_name: str,
        resolved_project: ResolvedProject,
        user_context: UserData,
    ) -> None:
        mock_repo.resolve_group.return_value = resolved_project
        mock_repo.add_dotfile.side_effect = DotfileAlreadyExists
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
        service: ProjectConfigService,
        mock_repo: AsyncMock,
        group_id: uuid.UUID,
        domain_name: str,
        resolved_project: ResolvedProject,
        user_context: UserData,
    ) -> None:
        mock_repo.resolve_group.return_value = resolved_project
        mock_repo.add_dotfile.side_effect = DotfileCreationFailed(
            "No leftover space for dotfile storage"
        )
        action = CreateDotfileAction(
            group_id_or_name=group_id,
            domain_name=domain_name,
            path=".bashrc",
            data="x" * 70000,
            permission="644",
        )

        with pytest.raises(DotfileCreationFailed, match="No leftover space"):
            await service.create_dotfile(action)


class TestListDotfiles:
    @pytest.mark.asyncio
    async def test_list_dotfiles_success(
        self,
        service: ProjectConfigService,
        mock_repo: AsyncMock,
        group_id: uuid.UUID,
        domain_name: str,
        resolved_project: ResolvedProject,
        user_context: UserData,
    ) -> None:
        mock_repo.resolve_group.return_value = resolved_project
        expected_dotfiles: list[GroupDotfile] = [
            {"path": ".bashrc", "perm": "644", "data": "# bash"},
            {"path": ".zshrc", "perm": "644", "data": "# zsh"},
        ]
        mock_repo.get_dotfiles.return_value = ProjectDotfilesResult(
            dotfiles=expected_dotfiles, leftover_space=64000
        )
        action = ListDotfilesAction(group_id_or_name=group_id, domain_name=domain_name)

        result = await service.list_dotfiles(action)

        assert result.dotfiles == expected_dotfiles
        mock_repo.get_dotfiles.assert_called_once_with(group_id)

    @pytest.mark.asyncio
    async def test_list_dotfiles_empty(
        self,
        service: ProjectConfigService,
        mock_repo: AsyncMock,
        group_id: uuid.UUID,
        domain_name: str,
        resolved_project: ResolvedProject,
        user_context: UserData,
    ) -> None:
        mock_repo.resolve_group.return_value = resolved_project
        mock_repo.get_dotfiles.return_value = ProjectDotfilesResult(
            dotfiles=[], leftover_space=64000
        )
        action = ListDotfilesAction(group_id_or_name=group_id, domain_name=domain_name)

        result = await service.list_dotfiles(action)

        assert result.dotfiles == []


class TestGetDotfile:
    @pytest.mark.asyncio
    async def test_get_dotfile_success(
        self,
        service: ProjectConfigService,
        mock_repo: AsyncMock,
        group_id: uuid.UUID,
        domain_name: str,
        resolved_project: ResolvedProject,
        user_context: UserData,
    ) -> None:
        mock_repo.resolve_group.return_value = resolved_project
        existing_dotfiles: list[GroupDotfile] = [
            {"path": ".bashrc", "perm": "644", "data": "# bash"},
            {"path": ".zshrc", "perm": "644", "data": "# zsh"},
        ]
        mock_repo.get_dotfiles.return_value = ProjectDotfilesResult(
            dotfiles=existing_dotfiles, leftover_space=64000
        )
        action = GetDotfileAction(
            group_id_or_name=group_id, domain_name=domain_name, path=".bashrc"
        )

        result = await service.get_dotfile(action)

        assert result.dotfile["path"] == ".bashrc"
        assert result.dotfile["data"] == "# bash"

    @pytest.mark.asyncio
    async def test_get_dotfile_not_found(
        self,
        service: ProjectConfigService,
        mock_repo: AsyncMock,
        group_id: uuid.UUID,
        domain_name: str,
        resolved_project: ResolvedProject,
        user_context: UserData,
    ) -> None:
        mock_repo.resolve_group.return_value = resolved_project
        existing_dotfiles: list[GroupDotfile] = [
            {"path": ".bashrc", "perm": "644", "data": "# bash"}
        ]
        mock_repo.get_dotfiles.return_value = ProjectDotfilesResult(
            dotfiles=existing_dotfiles, leftover_space=64000
        )
        action = GetDotfileAction(group_id_or_name=group_id, domain_name=domain_name, path=".zshrc")

        with pytest.raises(DotfileNotFound):
            await service.get_dotfile(action)


class TestUpdateDotfile:
    @pytest.mark.asyncio
    async def test_update_dotfile_success(
        self,
        service: ProjectConfigService,
        mock_repo: AsyncMock,
        group_id: uuid.UUID,
        domain_name: str,
        resolved_project: ResolvedProject,
        user_context: UserData,
    ) -> None:
        mock_repo.resolve_group.return_value = resolved_project
        action = UpdateDotfileAction(
            group_id_or_name=group_id,
            domain_name=domain_name,
            path=".bashrc",
            data="# new",
            permission="755",
        )

        result = await service.update_dotfile(action)

        assert result.group_id == group_id
        mock_repo.modify_dotfile.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_dotfile_not_found(
        self,
        service: ProjectConfigService,
        mock_repo: AsyncMock,
        group_id: uuid.UUID,
        domain_name: str,
        resolved_project: ResolvedProject,
        user_context: UserData,
    ) -> None:
        mock_repo.resolve_group.return_value = resolved_project
        mock_repo.modify_dotfile.side_effect = DotfileNotFound
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
        service: ProjectConfigService,
        mock_repo: AsyncMock,
        group_id: uuid.UUID,
        domain_name: str,
        resolved_project: ResolvedProject,
        user_context: UserData,
    ) -> None:
        mock_repo.resolve_group.return_value = resolved_project
        mock_repo.modify_dotfile.side_effect = DotfileCreationFailed(
            "No leftover space for dotfile storage"
        )
        action = UpdateDotfileAction(
            group_id_or_name=group_id,
            domain_name=domain_name,
            path=".bashrc",
            data="x" * 70000,
            permission="644",
        )

        with pytest.raises(DotfileCreationFailed, match="No leftover space"):
            await service.update_dotfile(action)


class TestDeleteDotfile:
    @pytest.mark.asyncio
    async def test_delete_dotfile_success(
        self,
        service: ProjectConfigService,
        mock_repo: AsyncMock,
        group_id: uuid.UUID,
        domain_name: str,
        resolved_project: ResolvedProject,
        user_context: UserData,
    ) -> None:
        mock_repo.resolve_group.return_value = resolved_project
        action = DeleteDotfileAction(
            group_id_or_name=group_id, domain_name=domain_name, path=".bashrc"
        )

        result = await service.delete_dotfile(action)

        assert result.success is True
        mock_repo.remove_dotfile.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_dotfile_not_found(
        self,
        service: ProjectConfigService,
        mock_repo: AsyncMock,
        group_id: uuid.UUID,
        domain_name: str,
        resolved_project: ResolvedProject,
        user_context: UserData,
    ) -> None:
        mock_repo.resolve_group.return_value = resolved_project
        mock_repo.remove_dotfile.side_effect = DotfileNotFound
        action = DeleteDotfileAction(
            group_id_or_name=group_id, domain_name=domain_name, path=".zshrc"
        )

        with pytest.raises(DotfileNotFound):
            await service.delete_dotfile(action)

    @pytest.mark.asyncio
    async def test_delete_dotfile_group_not_found(
        self,
        service: ProjectConfigService,
        mock_repo: AsyncMock,
        group_id: uuid.UUID,
        domain_name: str,
        resolved_project: ResolvedProject,
        user_context: UserData,
    ) -> None:
        mock_repo.resolve_group.return_value = resolved_project
        mock_repo.remove_dotfile.side_effect = ProjectNotFound
        action = DeleteDotfileAction(
            group_id_or_name=group_id, domain_name=domain_name, path=".bashrc"
        )

        with pytest.raises(ProjectNotFound):
            await service.delete_dotfile(action)
