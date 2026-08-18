"""Tests for AppConfigDefinitionRepository with real database operations."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest

from ai.backend.common.data.entity.app_config_definition import AppConfigDefinitionID
from ai.backend.common.data.filter_specs import StringMatchSpec
from ai.backend.manager.data.app_config.types import AppConfigDefinitionData
from ai.backend.manager.errors.repository import EntityNotFoundError
from ai.backend.manager.models.app_config_definition.conditions import (
    AppConfigDefinitionConditions,
)
from ai.backend.manager.models.app_config_definition.creators import (
    AppConfigDefinitionCreator,
)
from ai.backend.manager.models.app_config_definition.orders import AppConfigDefinitionOrders
from ai.backend.manager.models.app_config_definition.purgers import (
    AppConfigDefinitionPurger,
)
from ai.backend.manager.models.app_config_definition.row import AppConfigDefinitionRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.specs.pagination import CursorForwardPagination, OffsetPagination
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_scope.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_scope.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_scope.virtual_scope import VirtualScopeRow
from ai.backend.manager.repositories.app_config_definition.queriers import (
    AppConfigDefinitionQuerier,
)
from ai.backend.manager.repositories.app_config_definition.searchers import (
    AppConfigDefinitionSearcher,
)
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.testutils.db import with_tables


@pytest.fixture
async def repository(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[OpsRepository[AppConfigDefinitionData], None]:
    async with with_tables(
        database_connection,
        [
            VirtualScopeRow,
            EntityMembershipRow,
            ScopeBindingRow,
            RoleRow,
            PermissionRow,
            AppConfigDefinitionRow,
        ],
    ):
        yield OpsRepository(V2DBOpsProvider(database_connection))


@pytest.fixture
async def existing_definition(
    repository: OpsRepository[AppConfigDefinitionData],
) -> AppConfigDefinitionData:
    return await repository.create_global_entity(AppConfigDefinitionCreator(config_name="menu"))


@pytest.fixture
async def seeded_definitions(
    repository: OpsRepository[AppConfigDefinitionData],
) -> list[AppConfigDefinitionData]:
    definitions: list[AppConfigDefinitionData] = []
    for config_name in ("theme", "menu", "preferences"):
        definition = await repository.create_global_entity(
            AppConfigDefinitionCreator(config_name=config_name)
        )
        definitions.append(definition)
    return definitions


def _missing_id() -> AppConfigDefinitionID:
    return AppConfigDefinitionID(uuid.uuid4())


class TestCreateAndGet:
    async def test_create_then_get_by_id(
        self, repository: OpsRepository[AppConfigDefinitionData]
    ) -> None:
        created = await repository.create_global_entity(
            AppConfigDefinitionCreator(config_name="theme")
        )
        fetched = await repository.get(AppConfigDefinitionQuerier(definition_id=created.id))
        assert fetched.id == created.id
        assert fetched.config_name == "theme"

    async def test_get_by_id_missing_raises(
        self, repository: OpsRepository[AppConfigDefinitionData]
    ) -> None:
        with pytest.raises(EntityNotFoundError):
            await repository.get(AppConfigDefinitionQuerier(definition_id=_missing_id()))


class TestPurge:
    async def test_purge_removes_row(
        self,
        repository: OpsRepository[AppConfigDefinitionData],
        existing_definition: AppConfigDefinitionData,
    ) -> None:
        purged = await repository.purge_entity(
            AppConfigDefinitionPurger(definition_id=existing_definition.id)
        )
        assert purged.id == existing_definition.id
        with pytest.raises(EntityNotFoundError):
            await repository.get(AppConfigDefinitionQuerier(definition_id=existing_definition.id))

    async def test_purge_missing_raises(
        self, repository: OpsRepository[AppConfigDefinitionData]
    ) -> None:
        with pytest.raises(EntityNotFoundError):
            await repository.purge_entity(AppConfigDefinitionPurger(definition_id=_missing_id()))


class TestAdminSearch:
    async def test_admin_search_returns_all_with_total_count(
        self,
        repository: OpsRepository[AppConfigDefinitionData],
        seeded_definitions: list[AppConfigDefinitionData],
    ) -> None:
        result = await repository.search_in_global(
            AppConfigDefinitionSearcher(pagination=OffsetPagination(limit=10, offset=0))
        )
        assert result.total_count == len(seeded_definitions)
        assert {item.config_name for item in result.items} == {
            definition.config_name for definition in seeded_definitions
        }

    async def test_admin_search_respects_pagination(
        self,
        repository: OpsRepository[AppConfigDefinitionData],
        seeded_definitions: list[AppConfigDefinitionData],
    ) -> None:
        result = await repository.search_in_global(
            AppConfigDefinitionSearcher(pagination=OffsetPagination(limit=2, offset=0))
        )
        assert result.total_count == len(seeded_definitions)
        assert len(result.items) == 2
        assert result.has_next_page is True

    async def test_admin_search_filters_by_config_name(
        self,
        repository: OpsRepository[AppConfigDefinitionData],
        seeded_definitions: list[AppConfigDefinitionData],
    ) -> None:
        result = await repository.search_in_global(
            AppConfigDefinitionSearcher(
                pagination=OffsetPagination(limit=10, offset=0),
                conditions=[
                    AppConfigDefinitionConditions.by_config_name_equals(
                        StringMatchSpec("menu", case_insensitive=False, negated=False)
                    )
                ],
            )
        )
        expected = [
            definition.config_name
            for definition in seeded_definitions
            if definition.config_name == "menu"
        ]
        assert result.total_count == len(expected)
        assert [item.config_name for item in result.items] == expected

    async def test_admin_search_orders_by_config_name_desc(
        self,
        repository: OpsRepository[AppConfigDefinitionData],
        seeded_definitions: list[AppConfigDefinitionData],
    ) -> None:
        result = await repository.search_in_global(
            AppConfigDefinitionSearcher(
                pagination=OffsetPagination(limit=10, offset=0),
                orders=[AppConfigDefinitionOrders.config_name(ascending=False)],
            )
        )
        expected = sorted(
            (definition.config_name for definition in seeded_definitions), reverse=True
        )
        assert [item.config_name for item in result.items] == expected

    async def test_admin_search_filters_by_created_at(
        self,
        repository: OpsRepository[AppConfigDefinitionData],
        seeded_definitions: list[AppConfigDefinitionData],
    ) -> None:
        target = seeded_definitions[1]
        result = await repository.search_in_global(
            AppConfigDefinitionSearcher(
                pagination=OffsetPagination(limit=10, offset=0),
                conditions=[AppConfigDefinitionConditions.by_created_at_equals(target.created_at)],
            )
        )
        assert [item.id for item in result.items] == [target.id]

    async def test_admin_search_orders_by_created_at(
        self,
        repository: OpsRepository[AppConfigDefinitionData],
        seeded_definitions: list[AppConfigDefinitionData],
    ) -> None:
        result = await repository.search_in_global(
            AppConfigDefinitionSearcher(
                pagination=OffsetPagination(limit=10, offset=0),
                orders=[AppConfigDefinitionOrders.created_at(ascending=True)],
            )
        )
        expected = [
            definition.id for definition in sorted(seeded_definitions, key=lambda d: d.created_at)
        ]
        assert [item.id for item in result.items] == expected

    async def test_admin_search_cursor_forward(
        self,
        repository: OpsRepository[AppConfigDefinitionData],
        seeded_definitions: list[AppConfigDefinitionData],
    ) -> None:
        by_created_desc = sorted(seeded_definitions, key=lambda d: d.created_at, reverse=True)
        cursor = by_created_desc[0].id
        result = await repository.search_in_global(
            AppConfigDefinitionSearcher(
                pagination=CursorForwardPagination(
                    first=10,
                    cursor_order=AppConfigDefinitionOrders.created_at(ascending=False),
                    cursor_condition=AppConfigDefinitionConditions.by_cursor_forward(str(cursor)),
                )
            )
        )
        assert [item.id for item in result.items] == [d.id for d in by_created_desc[1:]]
