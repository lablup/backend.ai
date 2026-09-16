"""Tests for the app config purges that clear what a row cascades to, against a real database."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
import sqlalchemy as sa

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.data.entity.app_config_allow_list import (
    AppConfigAllowListEntityType,
    AppConfigAllowListID,
)
from ai.backend.common.data.entity.app_config_definition import (
    AppConfigDefinitionEntityType,
    AppConfigDefinitionID,
)
from ai.backend.common.data.entity.app_config_fragment import (
    AppConfigFragmentEntityType,
    AppConfigFragmentID,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.models.app_config_allow_list.purgers import AppConfigAllowListPurger
from ai.backend.manager.models.app_config_allow_list.row import AppConfigAllowListRow
from ai.backend.manager.models.app_config_definition.purgers import AppConfigDefinitionPurger
from ai.backend.manager.models.app_config_definition.row import AppConfigDefinitionRow
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.entity_label.row import EntityLabelRow
from ai.backend.manager.models.entity_share.row import EntityShareRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.resource_policy import UserResourcePolicyRow
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
from ai.backend.manager.repositories.app_config.repository import AppConfigRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.testutils.db import with_tables
from ai.backend.testutils.virtual_entity import VirtualEntitySeeder

_CONFIG_NAME = "theme"


@pytest.fixture
async def database(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
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
            DomainRow,
            UserResourcePolicyRow,
            UserRow,
            EntityShareRow,
            AppConfigDefinitionRow,
            AppConfigAllowListRow,
            AppConfigFragmentRow,
        ],
    ):
        yield database_connection


@pytest.fixture
def repository(database: ExtendedAsyncSAEngine) -> AppConfigRepository:
    return AppConfigRepository(V2DBOpsProvider(database))


async def _seed(
    database: ExtendedAsyncSAEngine, row: Base, entity_type: EntityType, entity_id: uuid.UUID
) -> None:
    async with database.begin_session() as sess:
        sess.add(row)
        await sess.flush()
        await VirtualEntitySeeder().provision(sess, entity_type, entity_id)


@pytest.fixture
async def definition_id(database: ExtendedAsyncSAEngine) -> AppConfigDefinitionID:
    definition_id = AppConfigDefinitionID(uuid.uuid4())
    await _seed(
        database,
        AppConfigDefinitionRow(id=definition_id, config_name=_CONFIG_NAME),
        AppConfigDefinitionEntityType(),
        definition_id,
    )
    return definition_id


@pytest.fixture
async def allow_list_id(
    database: ExtendedAsyncSAEngine, definition_id: AppConfigDefinitionID
) -> AppConfigAllowListID:
    allow_list_id = AppConfigAllowListID(uuid.uuid4())
    await _seed(
        database,
        AppConfigAllowListRow(
            id=allow_list_id,
            config_name=_CONFIG_NAME,
            scope_type=AppConfigScopeType.PUBLIC,
            rank=0,
        ),
        AppConfigAllowListEntityType(),
        allow_list_id,
    )
    return allow_list_id


@pytest.fixture
async def fragment_id(
    database: ExtendedAsyncSAEngine, allow_list_id: AppConfigAllowListID
) -> AppConfigFragmentID:
    fragment_id = AppConfigFragmentID(uuid.uuid4())
    await _seed(
        database,
        AppConfigFragmentRow(
            id=fragment_id,
            config_name=_CONFIG_NAME,
            scope_type=AppConfigScopeType.PUBLIC,
            scope_id=None,
            config={"color": "dark"},
        ),
        AppConfigFragmentEntityType(),
        fragment_id,
    )
    return fragment_id


async def _nodes(database: ExtendedAsyncSAEngine) -> set[str]:
    """The entity types that still have a node."""
    async with database.begin_readonly_session() as sess:
        rows = await sess.scalars(sa.select(VirtualEntityRow.entity_type).distinct())
        return {str(entity_type) for entity_type in rows.all()}


async def _count(database: ExtendedAsyncSAEngine, row_class: type[Base]) -> int:
    async with database.begin_readonly_session() as sess:
        return int(await sess.scalar(sa.select(sa.func.count()).select_from(row_class)) or 0)


class TestPurgeDefinition:
    async def test_takes_the_allow_list_and_fragments_with_their_nodes(
        self,
        database: ExtendedAsyncSAEngine,
        repository: AppConfigRepository,
        definition_id: AppConfigDefinitionID,
        fragment_id: AppConfigFragmentID,
    ) -> None:
        purged = await repository.purge_definition(
            AppConfigDefinitionPurger(definition_id=definition_id)
        )

        assert purged.id == definition_id
        assert await _count(database, AppConfigDefinitionRow) == 0
        assert await _count(database, AppConfigAllowListRow) == 0
        assert await _count(database, AppConfigFragmentRow) == 0
        assert await _nodes(database) == set()

    async def test_missing_definition_raises(self, repository: AppConfigRepository) -> None:
        with pytest.raises(EntityNotFoundError):
            await repository.purge_definition(
                AppConfigDefinitionPurger(definition_id=AppConfigDefinitionID(uuid.uuid4()))
            )


class TestPurgeAllowList:
    async def test_takes_the_fragments_and_keeps_the_definition(
        self,
        database: ExtendedAsyncSAEngine,
        repository: AppConfigRepository,
        allow_list_id: AppConfigAllowListID,
        fragment_id: AppConfigFragmentID,
    ) -> None:
        purged = await repository.purge_allow_list(
            AppConfigAllowListPurger(allow_list_id=allow_list_id)
        )

        assert purged.id == allow_list_id
        assert await _count(database, AppConfigDefinitionRow) == 1
        assert await _count(database, AppConfigAllowListRow) == 0
        assert await _count(database, AppConfigFragmentRow) == 0
        assert await _nodes(database) == {AppConfigDefinitionEntityType().name()}
