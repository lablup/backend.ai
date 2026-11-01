from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from ai.backend.common.dotfile import InvalidDotfilePath
from ai.backend.common.dto.manager.config.types import MAXIMUM_DOTFILE_SIZE
from ai.backend.manager.data.dotfile.types import DotfileEntry, DotfileQueryResult, DotfileScope
from ai.backend.manager.repositories.dotfile.repository import DotfileRepository
from ai.backend.manager.services.dotfile.actions.create import CreateDotfileAction
from ai.backend.manager.services.dotfile.actions.update import UpdateDotfileAction
from ai.backend.manager.services.dotfile.service import DotfileService

STORED_PATH = "/etc/stored"
INVALID_PATHS = [STORED_PATH, "../config/kconfig.dat", "/home/config/x", "kconfig.dat"]
_USER_KEY = "user-access-key"
_EXISTING = DotfileEntry(path=".zshrc", perm="600", data="existing")


def _query_result(entries: list[DotfileEntry]) -> DotfileQueryResult:
    return DotfileQueryResult(
        entries=entries,
        leftover_space=MAXIMUM_DOTFILE_SIZE - 256,
    )


def _create_action(path: str) -> CreateDotfileAction:
    return CreateDotfileAction(
        scope=DotfileScope.USER,
        entity_key=_USER_KEY,
        path=path,
        data="x",
        permission="644",
    )


def _update_action(path: str) -> UpdateDotfileAction:
    return UpdateDotfileAction(
        scope=DotfileScope.USER,
        entity_key=_USER_KEY,
        path=path,
        data="x",
        permission="644",
    )


@pytest.fixture
def repository() -> AsyncMock:
    repo = AsyncMock(spec=DotfileRepository)
    repo.get_user_dotfiles.return_value = _query_result([_EXISTING])
    repo.check_vfolder_conflict.return_value = False
    return repo


@pytest.fixture
def service(repository: AsyncMock) -> DotfileService:
    return DotfileService(repository=repository)


class TestDotfilePathRule:
    @pytest.mark.parametrize("path", INVALID_PATHS)
    async def test_create_rejects(
        self, service: DotfileService, repository: AsyncMock, path: str
    ) -> None:
        with pytest.raises(InvalidDotfilePath):
            await service.create_dotfile(_create_action(path))
        repository.save_user_dotfiles.assert_not_awaited()

    async def test_create_accepts_path_under_work_dir(
        self, service: DotfileService, repository: AsyncMock
    ) -> None:
        await service.create_dotfile(_create_action(".bashrc"))
        repository.save_user_dotfiles.assert_awaited_once()

    @pytest.mark.parametrize("path", INVALID_PATHS)
    async def test_update_rejects(
        self, service: DotfileService, repository: AsyncMock, path: str
    ) -> None:
        with pytest.raises(InvalidDotfilePath):
            await service.update_dotfile(_update_action(path))
        repository.save_user_dotfiles.assert_not_awaited()

    async def test_update_accepts_path_under_work_dir(
        self, service: DotfileService, repository: AsyncMock
    ) -> None:
        await service.update_dotfile(_update_action(".zshrc"))
        repository.save_user_dotfiles.assert_awaited_once()
