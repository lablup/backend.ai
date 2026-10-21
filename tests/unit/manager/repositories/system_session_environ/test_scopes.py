from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass

import pytest

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.system_session_environ import (
    SystemSessionEnvironID,
    SystemSessionEnvironScopeID,
)
from ai.backend.common.data.system_session_environ.types import (
    SystemSessionEnvironScopeType,
    SystemSessionEnvironValueSource,
)
from ai.backend.manager.data.system_session_environ.types import SystemSessionEnvironData
from ai.backend.manager.models.specs.pagination import NoPagination
from ai.backend.manager.models.system_session_environ.row import SystemSessionEnvironRow
from ai.backend.manager.models.system_session_environ.scopes import (
    SessionSystemSessionEnvironScope,
)
from ai.backend.manager.models.system_session_environ.searchers import (
    SystemSessionEnvironSearcher,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.testutils.db import with_tables

_DOMAIN_ID = DomainID(uuid.UUID("7a2d3b1f-0000-4000-8000-000000000001"))
_PROJECT_ID = ProjectID(uuid.UUID("7a2d3b1f-0000-4000-8000-000000000002"))


@dataclass(frozen=True)
class _SeededRows:
    global_row: SystemSessionEnvironID
    domain_row: SystemSessionEnvironID
    project_row: SystemSessionEnvironID


@pytest.fixture
async def database(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(database_connection, [SystemSessionEnvironRow]):
        yield database_connection


@pytest.fixture
def repository(database: ExtendedAsyncSAEngine) -> OpsRepository[SystemSessionEnvironData]:
    return OpsRepository[SystemSessionEnvironData](V2DBOpsProvider(database))


@pytest.fixture
def searcher() -> SystemSessionEnvironSearcher:
    return SystemSessionEnvironSearcher(pagination=NoPagination(), conditions=[])


@pytest.fixture
async def seeded_rows(database: ExtendedAsyncSAEngine) -> _SeededRows:
    global_row = SystemSessionEnvironRow(
        value_source=SystemSessionEnvironValueSource.SESSION_ID,
        key="BACKENDAI_SESSION_ID",
        scope_type=SystemSessionEnvironScopeType.GLOBAL,
        scope_id=None,
    )
    domain_row = SystemSessionEnvironRow(
        value_source=SystemSessionEnvironValueSource.USER_EMAIL,
        key="BACKENDAI_USER_EMAIL",
        scope_type=SystemSessionEnvironScopeType.DOMAIN,
        scope_id=SystemSessionEnvironScopeID(_DOMAIN_ID),
    )
    project_row = SystemSessionEnvironRow(
        value_source=SystemSessionEnvironValueSource.USER_NAME,
        key="BACKENDAI_USER_NAME",
        scope_type=SystemSessionEnvironScopeType.PROJECT,
        scope_id=SystemSessionEnvironScopeID(_PROJECT_ID),
    )
    async with database.begin_session() as db_sess:
        db_sess.add_all([
            global_row,
            domain_row,
            project_row,
            SystemSessionEnvironRow(
                value_source=SystemSessionEnvironValueSource.USER_UUID,
                key="BACKENDAI_USER_UUID",
                scope_type=SystemSessionEnvironScopeType.DOMAIN,
                scope_id=SystemSessionEnvironScopeID(uuid.uuid4()),
            ),
            SystemSessionEnvironRow(
                value_source=SystemSessionEnvironValueSource.ACCESS_KEY,
                key="BACKENDAI_ACCESS_KEY",
                scope_type=SystemSessionEnvironScopeType.PROJECT,
                scope_id=SystemSessionEnvironScopeID(uuid.uuid4()),
            ),
        ])
        await db_sess.flush()
        return _SeededRows(
            global_row=global_row.id,
            domain_row=domain_row.id,
            project_row=project_row.id,
        )


class TestSessionSystemSessionEnvironScope:
    async def test_returns_the_global_rows_and_the_rows_at_the_given_scopes(
        self,
        repository: OpsRepository[SystemSessionEnvironData],
        searcher: SystemSessionEnvironSearcher,
        seeded_rows: _SeededRows,
    ) -> None:
        result = await repository.search_in_scopes(
            [SessionSystemSessionEnvironScope(domain_id=_DOMAIN_ID, project_id=_PROJECT_ID)],
            searcher,
        )

        assert {row.id for row in result.items} == {
            seeded_rows.global_row,
            seeded_rows.domain_row,
            seeded_rows.project_row,
        }

    async def test_returns_only_the_global_rows_at_a_scope_with_no_rows(
        self,
        repository: OpsRepository[SystemSessionEnvironData],
        searcher: SystemSessionEnvironSearcher,
        seeded_rows: _SeededRows,
    ) -> None:
        result = await repository.search_in_scopes(
            [
                SessionSystemSessionEnvironScope(
                    domain_id=DomainID(uuid.uuid4()), project_id=ProjectID(uuid.uuid4())
                )
            ],
            searcher,
        )

        assert {row.id for row in result.items} == {seeded_rows.global_row}

    async def test_names_the_scope_by_its_entity(
        self,
        repository: OpsRepository[SystemSessionEnvironData],
        searcher: SystemSessionEnvironSearcher,
        seeded_rows: _SeededRows,
    ) -> None:
        result = await repository.search_in_scopes(
            [SessionSystemSessionEnvironScope(domain_id=_DOMAIN_ID, project_id=_PROJECT_ID)],
            searcher,
        )

        assert {row.id: row.scope_id for row in result.items} == {
            seeded_rows.global_row: None,
            seeded_rows.domain_row: _DOMAIN_ID,
            seeded_rows.project_row: _PROJECT_ID,
        }
