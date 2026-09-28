"""Tests for ContainerRegistryRepository.get_known_registries with a real database."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass

import pytest

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.manager.models.container_registry.row import ContainerRegistryRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.container_registry.repository import (
    ContainerRegistryRepository,
)
from ai.backend.manager.repositories.ops.v2.share.provider import ShareOpsProvider
from ai.backend.testutils.db import with_tables


@dataclass
class _SeededRegistries:
    """The registries seeded for one test run, with the entries they must produce."""

    host_only_key: str
    host_only_url: str
    with_path_key: str
    with_path_url: str


class TestGetKnownRegistries:
    """Integration tests for get_known_registries using a real database."""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                ContainerRegistryRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    def repository(self, db_with_cleanup: ExtendedAsyncSAEngine) -> ContainerRegistryRepository:
        return ContainerRegistryRepository(db_with_cleanup, ShareOpsProvider(db_with_cleanup))

    @pytest.fixture
    async def seeded_registries(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> _SeededRegistries:
        """Two registries carrying a project and one without, which must be skipped."""
        suffix = str(uuid.uuid4())[:8]
        host_only_name = f"harbor-{suffix}.example.com"
        with_path_name = f"harbor2-{suffix}.example.com"
        projectless_name = f"docker-{suffix}.example.com"
        host_only_project = f"project-a-{suffix}"
        with_path_project = f"project-b-{suffix}"

        async with db_with_cleanup.begin_session() as session:
            session.add_all([
                ContainerRegistryRow(
                    id=ContainerRegistryID(uuid.uuid4()),
                    url=f"https://{host_only_name}",
                    registry_name=host_only_name,
                    type=ContainerRegistryType.HARBOR2,
                    project=host_only_project,
                ),
                ContainerRegistryRow(
                    id=ContainerRegistryID(uuid.uuid4()),
                    url=f"https://{with_path_name}/base",
                    registry_name=with_path_name,
                    type=ContainerRegistryType.HARBOR2,
                    project=with_path_project,
                ),
                ContainerRegistryRow(
                    id=ContainerRegistryID(uuid.uuid4()),
                    url=f"https://{projectless_name}",
                    registry_name=projectless_name,
                    type=ContainerRegistryType.DOCKER,
                    project=None,
                ),
            ])
            await session.commit()

        return _SeededRegistries(
            host_only_key=f"{host_only_project}/{host_only_name}",
            # yarl.URL.human_repr() closes a host-only URL with a trailing slash.
            host_only_url=f"https://{host_only_name}/",
            with_path_key=f"{with_path_project}/{with_path_name}",
            with_path_url=f"https://{with_path_name}/base",
        )

    async def test_keys_by_project_and_registry_name(
        self,
        repository: ContainerRegistryRepository,
        seeded_registries: _SeededRegistries,
    ) -> None:
        """Each registry with a project appears once, keyed by project/registry_name."""
        result = await repository.get_known_registries()

        assert result[seeded_registries.host_only_key] == seeded_registries.host_only_url
        assert result[seeded_registries.with_path_key] == seeded_registries.with_path_url

    async def test_skips_rows_without_project(
        self,
        repository: ContainerRegistryRepository,
        seeded_registries: _SeededRegistries,
    ) -> None:
        """A registry whose project is NULL contributes no entry."""
        result = await repository.get_known_registries()

        assert set(result) == {
            seeded_registries.host_only_key,
            seeded_registries.with_path_key,
        }

    async def test_empty_table(
        self,
        repository: ContainerRegistryRepository,
    ) -> None:
        """With no registry rows the result is an empty dict."""
        result = await repository.get_known_registries()

        assert result == {}
