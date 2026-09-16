"""Tests for PaginationSpec: the cursor condition and orders it derives."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.app_config_definition import AppConfigDefinitionID
from ai.backend.manager.api.adapter_options.cursor.cursor import decode_cursor, encode_cursor
from ai.backend.manager.api.adapter_options.pagination.pagination import (
    PaginationOptions,
    PaginationSpec,
)
from ai.backend.manager.api.gql.adapter import BaseGQLAdapter
from ai.backend.manager.models.app_config_definition.row import AppConfigDefinitionRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base.querier import execute_batch_querier
from ai.backend.testutils.db import with_tables

_TIED_1 = AppConfigDefinitionID(uuid.UUID(int=1))
_TIED_2 = AppConfigDefinitionID(uuid.UUID(int=2))
_TIED_3 = AppConfigDefinitionID(uuid.UUID(int=3))
_OLDER = AppConfigDefinitionID(uuid.UUID(int=4))
_NAMES = {_TIED_1: "tied-1", _TIED_2: "tied-2", _TIED_3: "tied-3", _OLDER: "older"}

_SPEC = PaginationSpec(
    forward_order=AppConfigDefinitionRow.created_at.desc(),
    tiebreaker_order=AppConfigDefinitionRow.id.asc(),
)


@pytest.fixture
async def definitions_sharing_created_at(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[None, None]:
    tied_at = datetime(2026, 1, 1, tzinfo=UTC)
    rows = [
        AppConfigDefinitionRow(
            id=_TIED_1, config_name="tied-1", created_at=tied_at, updated_at=tied_at
        ),
        AppConfigDefinitionRow(
            id=_TIED_2, config_name="tied-2", created_at=tied_at, updated_at=tied_at
        ),
        AppConfigDefinitionRow(
            id=_TIED_3, config_name="tied-3", created_at=tied_at, updated_at=tied_at
        ),
        AppConfigDefinitionRow(
            id=_OLDER,
            config_name="older",
            created_at=tied_at - timedelta(days=1),
            updated_at=tied_at - timedelta(days=1),
        ),
    ]
    async with with_tables(database_connection, [AppConfigDefinitionRow]):
        async with database_connection.begin_session() as db_sess:
            db_sess.add_all(rows)
        yield


@dataclass(frozen=True)
class _CursorPageCase:
    options: PaginationOptions
    expected: list[str]


def _case_id(case: _CursorPageCase) -> str:
    options = case.options
    if options.first is not None:
        cursor = (
            options.after and _NAMES[AppConfigDefinitionID(uuid.UUID(decode_cursor(options.after)))]
        )
        return f"first-{options.first}-after-{cursor or 'start'}"
    cursor = (
        options.before and _NAMES[AppConfigDefinitionID(uuid.UUID(decode_cursor(options.before)))]
    )
    return f"last-{options.last}-before-{cursor or 'end'}"


class TestCursorPage:
    @pytest.mark.parametrize(
        "case",
        [
            _CursorPageCase(PaginationOptions(first=2), ["tied-1", "tied-2"]),
            _CursorPageCase(
                PaginationOptions(first=2, after=encode_cursor(_TIED_2)), ["tied-3", "older"]
            ),
            _CursorPageCase(PaginationOptions(first=2, after=encode_cursor(_TIED_3)), ["older"]),
            _CursorPageCase(PaginationOptions(last=2), ["older", "tied-3"]),
            _CursorPageCase(
                PaginationOptions(last=2, before=encode_cursor(_OLDER)), ["tied-3", "tied-2"]
            ),
            _CursorPageCase(PaginationOptions(last=2, before=encode_cursor(_TIED_2)), ["tied-1"]),
        ],
        ids=_case_id,
    )
    async def test_page_around_tied_sort_values(
        self,
        database_connection: ExtendedAsyncSAEngine,
        definitions_sharing_created_at: None,
        case: _CursorPageCase,
    ) -> None:
        querier = BaseGQLAdapter.build_querier(case.options, _SPEC)
        async with database_connection.begin_readonly_session() as db_sess:
            result = await execute_batch_querier(
                db_sess, sa.select(AppConfigDefinitionRow), querier
            )
        assert [row[0].config_name for row in result.rows] == case.expected
