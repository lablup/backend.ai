from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.entity.domain import DomainID, DomainName
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.dotfile import InvalidDotfilePath
from ai.backend.manager.data.dotfile.types import DotfileEntries, DotfileEntry
from ai.backend.manager.services.domain.actions.create_domain_dotfile import (
    CreateDomainDotfileAction,
)
from ai.backend.manager.services.domain.actions.delete_domain_dotfile import (
    DeleteDomainDotfileAction,
)
from ai.backend.manager.services.domain.actions.update_domain_dotfile import (
    UpdateDomainDotfileAction,
)
from ai.backend.manager.services.domain.service import DomainService
from ai.backend.manager.services.project.actions.create_project_dotfile import (
    CreateProjectDotfileAction,
)
from ai.backend.manager.services.project.actions.delete_project_dotfile import (
    DeleteProjectDotfileAction,
)
from ai.backend.manager.services.project.actions.update_project_dotfile import (
    UpdateProjectDotfileAction,
)
from ai.backend.manager.services.project.service import ProjectService

STORED_PATH = "/etc/stored"
INVALID_PATHS = [STORED_PATH, "../config/kconfig.dat", "/home/config/x", "kconfig.dat"]
_DOMAIN = DomainName("default")
_PROJECT = ProjectID(uuid.uuid4())


def _entry(path: str) -> DotfileEntry:
    return DotfileEntry(path=path, perm="644", data="x")


@pytest.fixture
def domain_service() -> MagicMock:
    service = MagicMock(spec=DomainService)
    service._read_dotfiles = AsyncMock(
        return_value=(MagicMock(), DotfileEntries(entries=(_entry(STORED_PATH),)))
    )
    service._write_dotfiles = AsyncMock()
    return service


@pytest.fixture
def project_service() -> MagicMock:
    service = MagicMock(spec=ProjectService)
    service._read_dotfiles = AsyncMock(return_value=DotfileEntries(entries=(_entry(STORED_PATH),)))
    service._write_dotfiles = AsyncMock()
    return service


class TestDomainDotfile:
    @pytest.mark.parametrize("path", INVALID_PATHS)
    async def test_create_rejects(self, domain_service: MagicMock, path: str) -> None:
        with pytest.raises(InvalidDotfilePath):
            await DomainService.create_dotfile(
                domain_service,
                CreateDomainDotfileAction(
                    domain_id=DomainID(uuid.uuid4()), name=_DOMAIN, entry=_entry(path)
                ),
            )
        domain_service._write_dotfiles.assert_not_awaited()

    async def test_create_accepts_path_under_work_dir(self, domain_service: MagicMock) -> None:
        await DomainService.create_dotfile(
            domain_service,
            CreateDomainDotfileAction(
                domain_id=DomainID(uuid.uuid4()), name=_DOMAIN, entry=_entry(".aws/config")
            ),
        )
        domain_service._write_dotfiles.assert_awaited_once()

    async def test_update_rejects_stored_path(self, domain_service: MagicMock) -> None:
        with pytest.raises(InvalidDotfilePath):
            await DomainService.update_dotfile(
                domain_service,
                UpdateDomainDotfileAction(
                    domain_id=DomainID(uuid.uuid4()), name=_DOMAIN, entry=_entry(STORED_PATH)
                ),
            )
        domain_service._write_dotfiles.assert_not_awaited()

    async def test_delete_accepts_stored_path(self, domain_service: MagicMock) -> None:
        result = await DomainService.delete_dotfile(
            domain_service,
            DeleteDomainDotfileAction(
                domain_id=DomainID(uuid.uuid4()), name=_DOMAIN, path=STORED_PATH
            ),
        )
        assert result.entries == ()


class TestProjectDotfile:
    @pytest.mark.parametrize("path", INVALID_PATHS)
    async def test_create_rejects(self, project_service: MagicMock, path: str) -> None:
        with pytest.raises(InvalidDotfilePath):
            await ProjectService.create_dotfile(
                project_service, CreateProjectDotfileAction(project_id=_PROJECT, entry=_entry(path))
            )
        project_service._write_dotfiles.assert_not_awaited()

    async def test_create_accepts_path_under_work_dir(self, project_service: MagicMock) -> None:
        await ProjectService.create_dotfile(
            project_service,
            CreateProjectDotfileAction(project_id=_PROJECT, entry=_entry(".aws/config")),
        )
        project_service._write_dotfiles.assert_awaited_once()

    async def test_update_rejects_stored_path(self, project_service: MagicMock) -> None:
        with pytest.raises(InvalidDotfilePath):
            await ProjectService.update_dotfile(
                project_service,
                UpdateProjectDotfileAction(project_id=_PROJECT, entry=_entry(STORED_PATH)),
            )
        project_service._write_dotfiles.assert_not_awaited()

    async def test_delete_accepts_stored_path(self, project_service: MagicMock) -> None:
        result = await ProjectService.delete_dotfile(
            project_service, DeleteProjectDotfileAction(project_id=_PROJECT, path=STORED_PATH)
        )
        assert result.entries == ()
