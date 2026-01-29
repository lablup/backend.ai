"""Tests for ProjectConfigRepository functionality.

As there is an ongoing migration of renaming group to project,
there are some occurrences where "group" is being used as "project"
(e.g., GroupRow, ProjectType).
It will be fixed in the future; for now understand them as the same concept.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest

from ai.backend.common import msgpack
from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.manager.errors.resource import ProjectNotFound
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group import GroupRow, ProjectType
from ai.backend.manager.models.resource_policy import ProjectResourcePolicyRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.project_config.repository import ProjectConfigRepository
from ai.backend.manager.repositories.project_config.types import DotfileInput
from ai.backend.testutils.db import with_tables


class TestProjectConfigRepository:
    @pytest.fixture
    async def db_with_cleanup(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [DomainRow, ProjectResourcePolicyRow, GroupRow],
        ):
            yield database_connection

    @pytest.fixture
    def repo(self, db_with_cleanup: ExtendedAsyncSAEngine) -> ProjectConfigRepository:
        return ProjectConfigRepository(db_with_cleanup)

    @pytest.fixture
    async def sample_project(
        self, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> tuple[uuid.UUID, str, str]:
        """Returns (project_id, project_name, domain_name)."""
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"
        policy_name = f"policy-{uuid.uuid4().hex[:8]}"
        project_id = uuid.uuid4()
        project_name = f"test-project-{uuid.uuid4().hex[:8]}"
        dotfiles = [{"path": ".bashrc", "perm": "644", "data": "# test"}]

        async with db_with_cleanup.begin_session() as session:
            session.add(
                DomainRow(
                    name=domain_name,
                    is_active=True,
                    total_resource_slots={},
                    allowed_vfolder_hosts={},
                    allowed_docker_registries=[],
                    dotfiles=b"",
                )
            )
            session.add(
                ProjectResourcePolicyRow(
                    name=policy_name,
                    max_vfolder_count=0,
                    max_quota_scope_size=-1,
                    max_network_count=3,
                )
            )
            session.add(
                GroupRow(
                    id=project_id,
                    name=project_name,
                    is_active=True,
                    domain_name=domain_name,
                    total_resource_slots={},
                    allowed_vfolder_hosts={},
                    resource_policy=policy_name,
                    type=ProjectType.GENERAL,
                    dotfiles=msgpack.packb(dotfiles),
                )
            )
            await session.commit()
        return project_id, project_name, domain_name

    @pytest.mark.asyncio
    async def test_resolve_project_by_uuid(
        self, repo: ProjectConfigRepository, sample_project: tuple[uuid.UUID, str, str]
    ) -> None:
        project_id, _, domain_name = sample_project

        result = await repo.resolve_project(None, project_id)

        assert result.id == project_id
        assert result.domain_name == domain_name

    @pytest.mark.asyncio
    async def test_resolve_project_by_name(
        self, repo: ProjectConfigRepository, sample_project: tuple[uuid.UUID, str, str]
    ) -> None:
        project_id, project_name, domain_name = sample_project

        result = await repo.resolve_project(domain_name, project_name)

        assert result.id == project_id
        assert result.domain_name == domain_name

    @pytest.mark.asyncio
    async def test_resolve_project_by_name_missing_domain(
        self, repo: ProjectConfigRepository, sample_project: tuple[uuid.UUID, str, str]
    ) -> None:
        _, project_name, _ = sample_project

        with pytest.raises(InvalidAPIParameters):
            await repo.resolve_project(None, project_name)

    @pytest.mark.asyncio
    async def test_resolve_project_not_found(
        self, repo: ProjectConfigRepository, sample_project: tuple[uuid.UUID, str, str]
    ) -> None:
        with pytest.raises(ProjectNotFound):
            await repo.resolve_project(None, uuid.uuid4())

    @pytest.mark.asyncio
    async def test_get_dotfiles(
        self, repo: ProjectConfigRepository, sample_project: tuple[uuid.UUID, str, str]
    ) -> None:
        project_id, _, _ = sample_project

        result = await repo.get_dotfiles(project_id)

        assert len(result.dotfiles) == 1
        assert result.dotfiles[0]["path"] == ".bashrc"
        assert result.leftover_space > 0

    @pytest.mark.asyncio
    async def test_modify_dotfile(
        self, repo: ProjectConfigRepository, sample_project: tuple[uuid.UUID, str, str]
    ) -> None:
        project_id, _, _ = sample_project

        await repo.modify_dotfile(
            project_id,
            DotfileInput(path=".bashrc", permission="755", data="# updated"),
        )

        result = await repo.get_dotfiles(project_id)
        assert len(result.dotfiles) == 1
        assert result.dotfiles[0]["path"] == ".bashrc"
        assert result.dotfiles[0]["data"] == "# updated"
        assert result.dotfiles[0]["perm"] == "755"
