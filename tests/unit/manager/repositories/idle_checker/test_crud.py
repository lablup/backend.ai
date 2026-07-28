from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import replace

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
    Updater,
)
from ai.backend.manager.repositories.idle_checker.creators import IdleCheckerCreatorSpec
from ai.backend.manager.repositories.idle_checker.purgers import IdleCheckerPurgerSpec
from ai.backend.manager.repositories.idle_checker.repository import IdleCheckerRepository
from ai.backend.manager.repositories.idle_checker.updaters import IdleCheckerUpdaterSpec
from ai.backend.manager.repositories.ops import DBOpsProvider
from ai.backend.manager.types import OptionalState
from ai.backend.testutils.db import with_tables


class TestIdleCheckerRepository:
    @pytest.fixture
    async def database(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(database_connection, [IdleCheckerRow]):
            yield database_connection

    @pytest.fixture
    def repository(self, database: ExtendedAsyncSAEngine) -> IdleCheckerRepository:
        return IdleCheckerRepository(DBOpsProvider(database))

    @pytest.fixture
    def creator_spec(self) -> IdleCheckerCreatorSpec:
        return IdleCheckerCreatorSpec(
            name="session lifetime",
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
        self,
        repository: IdleCheckerRepository,
        creator_spec: IdleCheckerCreatorSpec,
    ) -> IdleCheckerData:
        return await repository.create(Creator(spec=creator_spec))

    async def test_create_returns_checker(
        self,
        repository: IdleCheckerRepository,
        creator_spec: IdleCheckerCreatorSpec,
    ) -> None:
        checker = await repository.create(Creator(spec=creator_spec))

        assert checker.name == creator_spec.name
        assert checker.checker_type == creator_spec.checker_type

    async def test_search_returns_all_global_checkers(
        self,
        repository: IdleCheckerRepository,
        creator_spec: IdleCheckerCreatorSpec,
        created_checker: IdleCheckerData,
    ) -> None:
        second_checker = await repository.create(
            Creator(spec=replace(creator_spec, name="second session lifetime"))
        )

        result = await repository.admin_search(BatchQuerier(pagination=NoPagination()))

        assert {checker.id for checker in result.items} == {
            created_checker.id,
            second_checker.id,
        }
        assert result.total_count == 2

    async def test_search_by_id_returns_checker(
        self,
        repository: IdleCheckerRepository,
        created_checker: IdleCheckerData,
    ) -> None:
        result = await repository.admin_search(
            BatchQuerier(
                conditions=[IdleCheckerConditions.by_ids([created_checker.id])],
                pagination=NoPagination(),
            )
        )

        assert result.items == [created_checker]

    async def test_search_by_missing_id_returns_empty(
        self,
        repository: IdleCheckerRepository,
    ) -> None:
        result = await repository.admin_search(
            BatchQuerier(
                conditions=[IdleCheckerConditions.by_ids([IdleCheckerID(uuid.uuid4())])],
                pagination=NoPagination(),
            )
        )

        assert result.items == []

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
        result = await repository.admin_search(
            BatchQuerier(
                conditions=[IdleCheckerConditions.by_ids([created_checker.id])],
                pagination=NoPagination(),
            )
        )

        assert updated.name == "renamed lifetime"
        assert result.items == [updated]

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
                                network=NetworkTimeoutSpec(max_network_inactivity_seconds=1),
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
