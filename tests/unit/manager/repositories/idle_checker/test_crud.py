from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest

from ai.backend.common.data.idle_checker.types import (
    CheckerType,
    IdleCheckerSpec,
    NetworkTimeoutSpec,
    SessionLifetimeSpec,
)
from ai.backend.common.identifier.idle_checker import IdleCheckerID
from ai.backend.common.types import SessionTypes
from ai.backend.manager.data.idle_checker.types import IdleCheckerData
from ai.backend.manager.errors.idle_checker import (
    IdleCheckerNotFound,
    IdleCheckerTypeChangeNotAllowed,
)
from ai.backend.manager.models.idle_checker.conditions import IdleCheckerConditions
from ai.backend.manager.models.idle_checker.row import IdleCheckerRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    Creator,
    NoPagination,
    Purger,
    Querier,
    Updater,
)
from ai.backend.manager.repositories.idle_checker.creators import IdleCheckerCreatorSpec
from ai.backend.manager.repositories.idle_checker.purgers import IdleCheckerPurgerSpec
from ai.backend.manager.repositories.idle_checker.repository import IdleCheckerRepository
from ai.backend.manager.repositories.idle_checker.updaters import IdleCheckerUpdaterSpec
from ai.backend.manager.repositories.ops import DBOpsProvider
from ai.backend.manager.types import OptionalState
from ai.backend.testutils.db import with_tables


@pytest.fixture
async def database(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(
        database_connection,
        [IdleCheckerRow],
    ):
        yield database_connection


@pytest.fixture
def repository(database: ExtendedAsyncSAEngine) -> IdleCheckerRepository:
    return IdleCheckerRepository(DBOpsProvider(database))


@pytest.fixture
def creator_spec() -> IdleCheckerCreatorSpec:
    return IdleCheckerCreatorSpec(
        name="personal lifetime",
        description=None,
        checker_type=CheckerType.SESSION_LIFETIME,
        target_session_types=[SessionTypes.INTERACTIVE],
        initial_grace_period_seconds=30,
        spec=IdleCheckerSpec(
            type=CheckerType.SESSION_LIFETIME,
            session_lifetime=SessionLifetimeSpec(max_lifetime_seconds=3600),
        ),
    )


@pytest.fixture
async def created_checker(
    repository: IdleCheckerRepository,
    creator_spec: IdleCheckerCreatorSpec,
) -> IdleCheckerData:
    return await repository.create(Creator(spec=creator_spec))


class TestCreate:
    async def test_create_returns_checker(
        self,
        repository: IdleCheckerRepository,
        creator_spec: IdleCheckerCreatorSpec,
    ) -> None:
        checker = await repository.create(Creator(spec=creator_spec))

        assert checker.name == creator_spec.name
        assert checker.checker_type == creator_spec.checker_type


class TestGet:
    async def test_get_returns_checker(
        self,
        repository: IdleCheckerRepository,
        created_checker: IdleCheckerData,
    ) -> None:
        fetched = await repository.get(
            Querier(row_class=IdleCheckerRow, pk_value=created_checker.id)
        )

        assert fetched == created_checker

    async def test_get_missing_checker_raises(
        self,
        repository: IdleCheckerRepository,
    ) -> None:
        with pytest.raises(IdleCheckerNotFound):
            await repository.get(
                Querier(row_class=IdleCheckerRow, pk_value=IdleCheckerID(uuid.uuid4()))
            )


class TestSearch:
    async def test_search_returns_matching_checker(
        self,
        repository: IdleCheckerRepository,
        created_checker: IdleCheckerData,
    ) -> None:
        result = await repository.search(
            BatchQuerier(
                conditions=[IdleCheckerConditions.by_ids([created_checker.id])],
                pagination=NoPagination(),
            )
        )

        assert result.items == [created_checker]
        assert result.total_count == 1


class TestUpdate:
    async def test_update_changes_mutable_fields(
        self,
        repository: IdleCheckerRepository,
        created_checker: IdleCheckerData,
    ) -> None:
        updated = await repository.update(
            Updater(
                spec=IdleCheckerUpdaterSpec(name=OptionalState.update("renamed lifetime")),
                pk_value=created_checker.id,
            )
        )

        assert updated.name == "renamed lifetime"
        fetched = await repository.get(
            Querier(row_class=IdleCheckerRow, pk_value=created_checker.id)
        )
        assert fetched.name == "renamed lifetime"

    async def test_rejects_checker_type_change(
        self,
        repository: IdleCheckerRepository,
        created_checker: IdleCheckerData,
    ) -> None:
        with pytest.raises(IdleCheckerTypeChangeNotAllowed):
            await repository.update(
                Updater(
                    spec=IdleCheckerUpdaterSpec(
                        spec=OptionalState.update(
                            IdleCheckerSpec(
                                type=CheckerType.NETWORK_TIMEOUT,
                                network=NetworkTimeoutSpec(),
                            )
                        )
                    ),
                    pk_value=created_checker.id,
                )
            )

    async def test_update_missing_checker_raises(
        self,
        repository: IdleCheckerRepository,
    ) -> None:
        with pytest.raises(IdleCheckerNotFound):
            await repository.update(
                Updater(
                    spec=IdleCheckerUpdaterSpec(name=OptionalState.update("renamed lifetime")),
                    pk_value=IdleCheckerID(uuid.uuid4()),
                )
            )


class TestPurge:
    async def test_purge_removes_checker(
        self,
        database: ExtendedAsyncSAEngine,
        repository: IdleCheckerRepository,
        created_checker: IdleCheckerData,
    ) -> None:
        purged = await repository.purge(Purger(spec=IdleCheckerPurgerSpec(created_checker.id)))

        async with database.begin_readonly_session() as db_sess:
            checker = await db_sess.get(IdleCheckerRow, created_checker.id)

        assert purged == created_checker
        assert checker is None

    async def test_purge_missing_checker_raises(
        self,
        repository: IdleCheckerRepository,
    ) -> None:
        with pytest.raises(IdleCheckerNotFound):
            await repository.purge(Purger(spec=IdleCheckerPurgerSpec(IdleCheckerID(uuid.uuid4()))))
