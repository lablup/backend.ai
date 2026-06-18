"""Tests for AppConfigDefinitionRepository with real database operations."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest

from ai.backend.common.identifier.app_config_definition import AppConfigDefinitionID
from ai.backend.manager.data.app_config_definition.types import AppConfigDefinitionData
from ai.backend.manager.errors.app_config import AppConfigDefinitionNotFound
from ai.backend.manager.models.app_config_definition.row import AppConfigDefinitionRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.app_config_definition.creators import (
    AppConfigDefinitionCreatorSpec,
)
from ai.backend.manager.repositories.app_config_definition.repository import (
    AppConfigDefinitionRepository,
)
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    Creator,
    OffsetPagination,
    Purger,
)
from ai.backend.manager.repositories.ops import DBOpsProvider
from ai.backend.testutils.db import with_tables


@pytest.fixture
async def repository(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[AppConfigDefinitionRepository, None]:
    async with with_tables(database_connection, [AppConfigDefinitionRow]):
        yield AppConfigDefinitionRepository(DBOpsProvider(database_connection))


@pytest.fixture
async def existing_definition(
    repository: AppConfigDefinitionRepository,
) -> AppConfigDefinitionData:
    return await repository.create(Creator(spec=AppConfigDefinitionCreatorSpec(config_name="menu")))


@pytest.fixture
async def seeded_definitions(
    repository: AppConfigDefinitionRepository,
) -> list[AppConfigDefinitionData]:
    definitions: list[AppConfigDefinitionData] = []
    for config_name in ("theme", "menu", "preferences"):
        definition = await repository.create(
            Creator(spec=AppConfigDefinitionCreatorSpec(config_name=config_name))
        )
        definitions.append(definition)
    return definitions


def _missing_id() -> AppConfigDefinitionID:
    return AppConfigDefinitionID(uuid.uuid4())


class TestCreateAndGet:
    async def test_create_then_get_by_id(self, repository: AppConfigDefinitionRepository) -> None:
        created = await repository.create(
            Creator(spec=AppConfigDefinitionCreatorSpec(config_name="theme"))
        )
        fetched = await repository.get_by_id(created.id)
        assert fetched.id == created.id
        assert fetched.config_name == "theme"

    async def test_get_by_id_missing_raises(
        self, repository: AppConfigDefinitionRepository
    ) -> None:
        with pytest.raises(AppConfigDefinitionNotFound):
            await repository.get_by_id(_missing_id())


class TestPurge:
    async def test_purge_removes_row(
        self,
        repository: AppConfigDefinitionRepository,
        existing_definition: AppConfigDefinitionData,
    ) -> None:
        purged = await repository.purge(
            Purger(row_class=AppConfigDefinitionRow, pk_value=existing_definition.id)
        )
        assert purged.id == existing_definition.id
        with pytest.raises(AppConfigDefinitionNotFound):
            await repository.get_by_id(existing_definition.id)

    async def test_purge_missing_raises(self, repository: AppConfigDefinitionRepository) -> None:
        with pytest.raises(AppConfigDefinitionNotFound):
            await repository.purge(Purger(row_class=AppConfigDefinitionRow, pk_value=_missing_id()))


class TestSearch:
    async def test_search_returns_all_with_total_count(
        self,
        repository: AppConfigDefinitionRepository,
        seeded_definitions: list[AppConfigDefinitionData],
    ) -> None:
        result = await repository.search(
            BatchQuerier(pagination=OffsetPagination(limit=10, offset=0))
        )
        assert result.total_count == len(seeded_definitions)
        assert {item.config_name for item in result.items} == {
            definition.config_name for definition in seeded_definitions
        }

    async def test_search_respects_pagination(
        self,
        repository: AppConfigDefinitionRepository,
        seeded_definitions: list[AppConfigDefinitionData],
    ) -> None:
        result = await repository.search(
            BatchQuerier(pagination=OffsetPagination(limit=2, offset=0))
        )
        assert result.total_count == len(seeded_definitions)
        assert len(result.items) == 2
        assert result.has_next_page is True
