"""Tests for GroupConfigRepository functionality."""

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
from ai.backend.manager.repositories.group_config.repository import GroupConfigRepository
from ai.backend.testutils.db import with_tables


class TestGroupConfigRepository:
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
    def repo(self, db_with_cleanup: ExtendedAsyncSAEngine) -> GroupConfigRepository:
        return GroupConfigRepository(db_with_cleanup)

    @pytest.fixture
    async def sample_group(
        self, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> tuple[uuid.UUID, str, str]:
        """Returns (group_id, group_name, domain_name)."""
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"
        policy_name = f"policy-{uuid.uuid4().hex[:8]}"
        group_id = uuid.uuid4()
        group_name = f"test-group-{uuid.uuid4().hex[:8]}"
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
                    id=group_id,
                    name=group_name,
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
        return group_id, group_name, domain_name

    @pytest.mark.asyncio
    async def test_resolve_group_id_by_uuid(
        self, repo: GroupConfigRepository, sample_group: tuple[uuid.UUID, str, str]
    ) -> None:
        group_id, _, domain_name = sample_group

        result_id, result_domain = await repo.resolve_group_id_and_domain(group_id, None)

        assert result_id == group_id
        assert result_domain == domain_name

    @pytest.mark.asyncio
    async def test_resolve_group_id_by_name(
        self, repo: GroupConfigRepository, sample_group: tuple[uuid.UUID, str, str]
    ) -> None:
        group_id, group_name, domain_name = sample_group

        result_id, result_domain = await repo.resolve_group_id_and_domain(group_name, domain_name)

        assert result_id == group_id
        assert result_domain == domain_name

    @pytest.mark.asyncio
    async def test_resolve_group_id_by_name_missing_domain(
        self, repo: GroupConfigRepository, sample_group: tuple[uuid.UUID, str, str]
    ) -> None:
        _, group_name, _ = sample_group

        with pytest.raises(InvalidAPIParameters):
            await repo.resolve_group_id_and_domain(group_name, None)

    @pytest.mark.asyncio
    async def test_resolve_group_not_found(
        self, repo: GroupConfigRepository, sample_group: tuple[uuid.UUID, str, str]
    ) -> None:
        with pytest.raises(ProjectNotFound):
            await repo.resolve_group_id_and_domain(uuid.uuid4(), None)

    @pytest.mark.asyncio
    async def test_get_dotfiles(
        self, repo: GroupConfigRepository, sample_group: tuple[uuid.UUID, str, str]
    ) -> None:
        group_id, _, _ = sample_group

        dotfiles, leftover = await repo.get_dotfiles(group_id)

        assert len(dotfiles) == 1
        assert dotfiles[0]["path"] == ".bashrc"
        assert leftover > 0

    @pytest.mark.asyncio
    async def test_update_dotfiles(
        self, repo: GroupConfigRepository, sample_group: tuple[uuid.UUID, str, str]
    ) -> None:
        group_id, _, _ = sample_group
        new_dotfiles = [{"path": ".zshrc", "perm": "644", "data": "# zsh"}]

        await repo.update_dotfiles(group_id, msgpack.packb(new_dotfiles))

        dotfiles, _ = await repo.get_dotfiles(group_id)
        assert len(dotfiles) == 1
        assert dotfiles[0]["path"] == ".zshrc"
