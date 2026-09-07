"""Tests for the ops-backed idle checker catalog against a real database."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import replace

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.idle_checker import IdleCheckerID
from ai.backend.common.data.idle_checker.types import (
    CheckerType,
    IdleCheckerSpec,
    NetworkTimeoutSpec,
    SessionLifetimeSpec,
)
from ai.backend.common.types import SessionTypes
from ai.backend.manager.data.idle_checker.types import IdleCheckerData
from ai.backend.manager.errors.repository import EntityNotFoundError
from ai.backend.manager.models.entity_label.row import EntityLabelRow
from ai.backend.manager.models.idle_checker.conditions import IdleCheckerConditions
from ai.backend.manager.models.idle_checker.creators import IdleCheckerCreator
from ai.backend.manager.models.idle_checker.orders import IdleCheckerOrders
from ai.backend.manager.models.idle_checker.purgers import IdleCheckerPurger
from ai.backend.manager.models.idle_checker.row import IdleCheckerRow
from ai.backend.manager.models.idle_checker.searchers import IdleCheckerSearcher
from ai.backend.manager.models.idle_checker.updaters import IdleCheckerUpdater
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.specs.pagination import NoPagination
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
from ai.backend.manager.types import OptionalState
from ai.backend.testutils.db import with_tables


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
            IdleCheckerRow,
        ],
    ):
        yield database_connection


@pytest.fixture
def repository(database: ExtendedAsyncSAEngine) -> OpsRepository[IdleCheckerData]:
    return OpsRepository(V2DBOpsProvider(database))


@pytest.fixture
def creator() -> IdleCheckerCreator:
    return IdleCheckerCreator(
        name="session lifetime",
        description=None,
        target_session_types=[SessionTypes.INTERACTIVE],
        initial_grace_period_seconds=30,
        spec=IdleCheckerSpec(
            type=CheckerType.SESSION_LIFETIME,
            session_lifetime=SessionLifetimeSpec(max_lifetime_seconds=3600),
        ),
    )


def _missing_id() -> IdleCheckerID:
    return IdleCheckerID(uuid.uuid4())


@pytest.fixture
async def created_checker(
    repository: OpsRepository[IdleCheckerData],
    creator: IdleCheckerCreator,
) -> IdleCheckerData:
    return await repository.create_global_entity(creator)


@pytest.fixture
async def network_checker(
    repository: OpsRepository[IdleCheckerData],
    creator: IdleCheckerCreator,
) -> IdleCheckerData:
    return await repository.create_global_entity(
        replace(
            creator,
            name="network timeout",
            spec=IdleCheckerSpec(
                type=CheckerType.NETWORK_TIMEOUT,
                network=NetworkTimeoutSpec(max_network_inactivity_seconds=60),
            ),
        )
    )


class TestCreate:
    async def test_create_returns_checker(
        self,
        repository: OpsRepository[IdleCheckerData],
        creator: IdleCheckerCreator,
    ) -> None:
        checker = await repository.create_global_entity(creator)

        assert checker.name == creator.name
        assert checker.checker_type == creator.spec.type

    async def test_create_provisions_the_virtual_entity(
        self,
        database: ExtendedAsyncSAEngine,
        created_checker: IdleCheckerData,
    ) -> None:
        async with database.begin_readonly_session() as db_sess:
            node = await db_sess.scalar(
                sa.select(VirtualEntityRow).where(
                    VirtualEntityRow.entity_type == created_checker.id.entity_type(),
                    VirtualEntityRow.entity_id == created_checker.id,
                )
            )

        assert node is not None


class TestSearch:
    async def test_search_returns_all_global_checkers(
        self,
        repository: OpsRepository[IdleCheckerData],
        creator: IdleCheckerCreator,
        created_checker: IdleCheckerData,
    ) -> None:
        second_checker = await repository.create_global_entity(
            replace(creator, name="second session lifetime")
        )

        result = await repository.search_in_global(IdleCheckerSearcher(pagination=NoPagination()))

        assert {checker.id for checker in result.items} == {
            created_checker.id,
            second_checker.id,
        }
        assert result.total_count == 2

    async def test_search_by_id_returns_checker(
        self,
        repository: OpsRepository[IdleCheckerData],
        created_checker: IdleCheckerData,
    ) -> None:
        result = await repository.search_in_global(
            IdleCheckerSearcher(
                conditions=[IdleCheckerConditions.by_ids([created_checker.id])],
                pagination=NoPagination(),
            )
        )

        assert result.items == [created_checker]

    async def test_search_by_missing_id_returns_empty(
        self,
        repository: OpsRepository[IdleCheckerData],
    ) -> None:
        result = await repository.search_in_global(
            IdleCheckerSearcher(
                conditions=[IdleCheckerConditions.by_ids([_missing_id()])],
                pagination=NoPagination(),
            )
        )

        assert result.items == []

    async def test_search_by_checker_type(
        self,
        repository: OpsRepository[IdleCheckerData],
        created_checker: IdleCheckerData,
        network_checker: IdleCheckerData,
    ) -> None:
        result = await repository.search_in_global(
            IdleCheckerSearcher(
                conditions=[
                    IdleCheckerConditions.by_checker_type_equals(CheckerType.NETWORK_TIMEOUT)
                ],
                pagination=NoPagination(),
            )
        )

        assert result.items == [network_checker]
        assert created_checker not in result.items

    async def test_search_orders_by_checker_type(
        self,
        repository: OpsRepository[IdleCheckerData],
        created_checker: IdleCheckerData,
        network_checker: IdleCheckerData,
    ) -> None:
        result = await repository.search_in_global(
            IdleCheckerSearcher(
                orders=[IdleCheckerOrders.checker_type(ascending=True)],
                pagination=NoPagination(),
            )
        )

        assert result.items == [network_checker, created_checker]


class TestUpdate:
    async def test_update_changes_mutable_fields(
        self,
        repository: OpsRepository[IdleCheckerData],
        created_checker: IdleCheckerData,
    ) -> None:
        updated = await repository.update(
            IdleCheckerUpdater(
                checker_id=created_checker.id,
                name=OptionalState.update("renamed lifetime"),
            )
        )
        result = await repository.search_in_global(
            IdleCheckerSearcher(
                conditions=[IdleCheckerConditions.by_ids([created_checker.id])],
                pagination=NoPagination(),
            )
        )

        assert updated.name == "renamed lifetime"
        assert result.items == [updated]

    async def test_update_spec_updates_checker_type(
        self,
        repository: OpsRepository[IdleCheckerData],
        created_checker: IdleCheckerData,
    ) -> None:
        network_spec = IdleCheckerSpec(
            type=CheckerType.NETWORK_TIMEOUT,
            network=NetworkTimeoutSpec(max_network_inactivity_seconds=1),
        )

        updated = await repository.update(
            IdleCheckerUpdater(
                checker_id=created_checker.id,
                spec=OptionalState.update(network_spec),
            )
        )

        assert updated.spec == network_spec
        assert updated.checker_type == CheckerType.NETWORK_TIMEOUT

    async def test_update_missing_checker_raises(
        self,
        repository: OpsRepository[IdleCheckerData],
    ) -> None:
        with pytest.raises(EntityNotFoundError):
            await repository.update(
                IdleCheckerUpdater(
                    checker_id=_missing_id(),
                    name=OptionalState.update("renamed lifetime"),
                )
            )


class TestPurge:
    async def test_purge_removes_checker(
        self,
        database: ExtendedAsyncSAEngine,
        repository: OpsRepository[IdleCheckerData],
        created_checker: IdleCheckerData,
    ) -> None:
        result = await repository.partial_bulk_purge_entities({
            created_checker.id: IdleCheckerPurger(checker_id=created_checker.id)
        })

        async with database.begin_readonly_session() as db_sess:
            checker = await db_sess.get(IdleCheckerRow, created_checker.id)

        assert result.successes == {created_checker.id: created_checker}
        assert checker is None

    async def test_purge_missing_checker_reports_the_failure(
        self,
        repository: OpsRepository[IdleCheckerData],
    ) -> None:
        missing_id = _missing_id()

        result = await repository.partial_bulk_purge_entities({
            missing_id: IdleCheckerPurger(checker_id=missing_id)
        })

        assert not result.successes
        assert isinstance(result.errors[missing_id], EntityNotFoundError)

    async def test_purge_answers_for_every_named_checker(
        self,
        repository: OpsRepository[IdleCheckerData],
        created_checker: IdleCheckerData,
    ) -> None:
        """A missing id fails on its own; the checker beside it is still removed."""
        missing_id = _missing_id()

        result = await repository.partial_bulk_purge_entities({
            created_checker.id: IdleCheckerPurger(checker_id=created_checker.id),
            missing_id: IdleCheckerPurger(checker_id=missing_id),
        })

        assert set(result.successes) == {created_checker.id}
        assert set(result.errors) == {missing_id}
