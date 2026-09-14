"""Tests for AppConfigDefinitionRepository with real database operations."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import pytest

from ai.backend.common.data.entity.app_config_definition import AppConfigDefinitionID
from ai.backend.common.data.filter_specs import StringMatchSpec
from ai.backend.manager.data.app_config.types import AppConfigDefinitionData
from ai.backend.manager.errors.base.entity import EntityNotFoundError
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
from ai.backend.manager.models.app_config_definition.queriers import (
    AppConfigDefinitionQuerier,
)
from ai.backend.manager.models.app_config_definition.row import AppConfigDefinitionRow
from ai.backend.manager.models.app_config_definition.searchers import (
    AppConfigDefinitionSearcher,
)
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.entity_label.row import EntityLabelRow
from ai.backend.manager.models.entity_share.row import EntityShareRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.resource_policy import UserResourcePolicyRow
from ai.backend.manager.models.specs.pagination import (
    CursorBackwardPagination,
    CursorForwardPagination,
    OffsetPagination,
)
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.entity_membership_cap import (
    EntityMembershipCapRow,
)
from ai.backend.manager.models.virtual_entity.entity_membership_field import (
    EntityMembershipFieldRow,
)
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
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
            VirtualEntityRow,
            EntityMembershipRow,
            EntityMembershipCapRow,
            EntityMembershipFieldRow,
            ScopeBindingRow,
            EntityLabelRow,
            RoleRow,
            PermissionRow,
            AppConfigDefinitionRow,
            DomainRow,
            UserResourcePolicyRow,
            UserRow,
            EntityShareRow,
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


@pytest.fixture
async def definitions_sharing_created_at(
    database_connection: ExtendedAsyncSAEngine,
    repository: OpsRepository[AppConfigDefinitionData],
) -> list[AppConfigDefinitionID]:
    """Three rows at one ``created_at`` and one older row, in ``(created_at DESC, id ASC)``
    order — the order the adapter pages in."""
    tied_at = datetime(2026, 1, 1, tzinfo=UTC)
    rows = [
        AppConfigDefinitionRow(
            id=AppConfigDefinitionID(uuid.UUID(int=1)),
            config_name="tied-1",
            created_at=tied_at,
            updated_at=tied_at,
        ),
        AppConfigDefinitionRow(
            id=AppConfigDefinitionID(uuid.UUID(int=2)),
            config_name="tied-2",
            created_at=tied_at,
            updated_at=tied_at,
        ),
        AppConfigDefinitionRow(
            id=AppConfigDefinitionID(uuid.UUID(int=3)),
            config_name="tied-3",
            created_at=tied_at,
            updated_at=tied_at,
        ),
        AppConfigDefinitionRow(
            id=AppConfigDefinitionID(uuid.UUID(int=4)),
            config_name="older",
            created_at=tied_at - timedelta(days=1),
            updated_at=tied_at - timedelta(days=1),
        ),
    ]
    async with database_connection.begin_session() as db_sess:
        db_sess.add_all(rows)
    return [row.id for row in rows]


@dataclass(frozen=True)
class _CursorWalkCase:
    cursor: int
    expected: list[int]


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

    @pytest.mark.parametrize(
        "case",
        [
            _CursorWalkCase(cursor=0, expected=[1, 2, 3]),
            _CursorWalkCase(cursor=1, expected=[2, 3]),
            _CursorWalkCase(cursor=2, expected=[3]),
            _CursorWalkCase(cursor=3, expected=[]),
        ],
        ids=lambda case: f"after-{case.cursor}",
    )
    async def test_admin_search_cursor_forward_continues_past_tied_created_at(
        self,
        repository: OpsRepository[AppConfigDefinitionData],
        definitions_sharing_created_at: list[AppConfigDefinitionID],
        case: _CursorWalkCase,
    ) -> None:
        cursor = definitions_sharing_created_at[case.cursor]
        result = await repository.search_in_global(
            AppConfigDefinitionSearcher(
                pagination=CursorForwardPagination(
                    first=10,
                    cursor_order=AppConfigDefinitionOrders.created_at(ascending=False),
                    cursor_condition=AppConfigDefinitionConditions.by_cursor_forward(str(cursor)),
                ),
                orders=[AppConfigDefinitionOrders.id(ascending=True)],
            )
        )
        assert [item.id for item in result.items] == [
            definitions_sharing_created_at[index] for index in case.expected
        ]

    @pytest.mark.parametrize(
        "case",
        [
            _CursorWalkCase(cursor=0, expected=[]),
            _CursorWalkCase(cursor=1, expected=[0]),
            _CursorWalkCase(cursor=2, expected=[0, 1]),
            _CursorWalkCase(cursor=3, expected=[0, 1, 2]),
        ],
        ids=lambda case: f"before-{case.cursor}",
    )
    async def test_admin_search_cursor_backward_keeps_tied_created_at(
        self,
        repository: OpsRepository[AppConfigDefinitionData],
        definitions_sharing_created_at: list[AppConfigDefinitionID],
        case: _CursorWalkCase,
    ) -> None:
        cursor = definitions_sharing_created_at[case.cursor]
        result = await repository.search_in_global(
            AppConfigDefinitionSearcher(
                pagination=CursorBackwardPagination(
                    last=10,
                    cursor_order=AppConfigDefinitionOrders.created_at(ascending=True),
                    cursor_condition=AppConfigDefinitionConditions.by_cursor_backward(str(cursor)),
                ),
                orders=[AppConfigDefinitionOrders.id(ascending=True)],
            )
        )
        assert [item.id for item in result.items] == [
            definitions_sharing_created_at[index] for index in case.expected
        ]
