"""Tests for the conditional-bulk WriteOps primitives.

``bulk_conditional_{create,update,purge}_partial`` apply a per-item ``only_if`` existence gate
before each write, with partial success: an item whose gate is not satisfied is reported as
``ConditionalMutationForbidden`` (and a missing update/purge target as a not-found error) while
the rest of the batch proceeds.

The gate models an authorization check: each write carries a *scope*, and an ``_AllowListRow``
entry authorizes writes to that scope. Writes to a non-allow-listed scope are forbidden — this
is the shape a real caller (e.g. a permission/visibility check) would use ``only_if`` for.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Any

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.manager.errors.repository import ConditionalMutationForbidden
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    BulkConditionalCreator,
    BulkConditionalPurger,
    BulkConditionalUpdater,
    ConditionalCreator,
    ConditionalPurger,
    ConditionalUpdater,
    CreatorSpec,
    ExistsQuerier,
    NoPagination,
    Purger,
    Querier,
    Updater,
    UpdaterSpec,
)
from ai.backend.manager.repositories.ops import DBOpsProvider
from ai.backend.testutils.db import with_tables


class _ConfigRow(Base):  # type: ignore[misc]
    """A scoped config row — the entity a conditional bulk write creates / updates / deletes."""

    __tablename__ = "test_cond_config"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    scope: Mapped[str] = mapped_column(sa.String(64), nullable=False)


class _AllowListRow(Base):  # type: ignore[misc]
    """Allow-list of scopes a conditional write may touch — the ``only_if`` gate's table.

    An entry for a scope authorizes writes to that scope; a scope with no entry is not
    authorized, so writes targeting it are reported as ``ConditionalMutationForbidden`` while
    the rest of the batch proceeds. Stands in for a real permission / visibility check.
    """

    __tablename__ = "test_cond_allowlist"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    scope: Mapped[str] = mapped_column(sa.String(64), nullable=False)


@dataclass
class _ConfigCreatorSpec(CreatorSpec[_ConfigRow]):
    name: str
    scope: str

    def build_row(self) -> _ConfigRow:
        return _ConfigRow(name=self.name, scope=self.scope)


@dataclass
class _ConfigRenameSpec(UpdaterSpec[_ConfigRow]):
    new_name: str

    @property
    def row_class(self) -> type[_ConfigRow]:
        return _ConfigRow

    def build_values(self) -> dict[str, Any]:
        return {"name": self.new_name}


@pytest.fixture
async def tables(database_connection: ExtendedAsyncSAEngine) -> AsyncGenerator[None, None]:
    async with with_tables(database_connection, [_ConfigRow, _AllowListRow]):
        yield


@pytest.fixture
def provider(database_connection: ExtendedAsyncSAEngine) -> DBOpsProvider:
    return DBOpsProvider(database_connection)


@pytest.fixture
async def allow_list(
    database_connection: ExtendedAsyncSAEngine,
    tables: None,
) -> None:
    """Allow-list scope "d1": writes targeting "d1" are authorized, any other scope is not."""
    async with database_connection.begin() as conn:
        await conn.execute(sa.insert(_AllowListRow).values(scope="d1"))


@pytest.fixture
async def seeded_configs(
    database_connection: ExtendedAsyncSAEngine,
    tables: None,
) -> dict[str, int]:
    """Seed one config row per scope — "d1" (allow-listed) and "d2" (not) — to update / purge.

    Returns ``{scope: row id}`` so a test can target the authorized vs. unauthorized row.
    """
    async with database_connection.begin() as conn:
        await conn.execute(
            sa.insert(_ConfigRow).values([
                {"name": "cfg-d1", "scope": "d1"},
                {"name": "cfg-d2", "scope": "d2"},
            ])
        )
        result = await conn.execute(
            sa.select(_ConfigRow.id, _ConfigRow.scope).where(
                _ConfigRow.name.in_(["cfg-d1", "cfg-d2"])
            )
        )
        return {row.scope: row.id for row in result}


class TestBulkConditionalCreate:
    async def test_all_authorized_inserts_every_row(
        self, provider: DBOpsProvider, allow_list: None
    ) -> None:
        # Both configs target the allow-listed scope "d1", so every gate is authorized.
        async with provider.write_ops() as w:
            result = await w.bulk_conditional_create_partial(
                BulkConditionalCreator(
                    specs=[
                        ConditionalCreator(
                            spec=_ConfigCreatorSpec(name="cfg-a", scope="d1"),
                            only_if=ExistsQuerier(
                                row_class=_AllowListRow,
                                conditions=[lambda: _AllowListRow.scope == "d1"],
                            ),
                        ),
                        ConditionalCreator(
                            spec=_ConfigCreatorSpec(name="cfg-b", scope="d1"),
                            only_if=ExistsQuerier(
                                row_class=_AllowListRow,
                                conditions=[lambda: _AllowListRow.scope == "d1"],
                            ),
                        ),
                    ]
                )
            )

        assert {row.name for row in result.successes} == {"cfg-a", "cfg-b"}
        assert result.errors == []

    async def test_unauthorized_scope_is_forbidden(
        self, provider: DBOpsProvider, allow_list: None
    ) -> None:
        # "d1" is allow-listed so it is written; "d2" is not, so that item alone is forbidden.
        async with provider.write_ops() as w:
            result = await w.bulk_conditional_create_partial(
                BulkConditionalCreator(
                    specs=[
                        ConditionalCreator(
                            spec=_ConfigCreatorSpec(name="cfg-d1", scope="d1"),
                            only_if=ExistsQuerier(
                                row_class=_AllowListRow,
                                conditions=[lambda: _AllowListRow.scope == "d1"],
                            ),
                        ),
                        ConditionalCreator(
                            spec=_ConfigCreatorSpec(name="cfg-d2", scope="d2"),
                            only_if=ExistsQuerier(
                                row_class=_AllowListRow,
                                conditions=[lambda: _AllowListRow.scope == "d2"],
                            ),
                        ),
                    ]
                )
            )

        # partial: the "d1" config is inserted; the "d2" item (index 1) is forbidden.
        assert {row.name for row in result.successes} == {"cfg-d1"}
        assert [e.index for e in result.errors] == [1]
        assert isinstance(result.errors[0].exception, ConditionalMutationForbidden)
        async with provider.read_ops() as r:
            written = await r.batch_query_in_global(
                sa.select(_ConfigRow), BatchQuerier(pagination=NoPagination())
            )
        assert {row[0].name for row in written.rows} == {"cfg-d1"}

    async def test_empty_specs_returns_empty(self, provider: DBOpsProvider, tables: None) -> None:
        empty: BulkConditionalCreator[_ConfigRow, _AllowListRow] = BulkConditionalCreator(specs=[])
        async with provider.write_ops() as w:
            result = await w.bulk_conditional_create_partial(empty)
        assert result.successes == []
        assert result.errors == []


class TestBulkConditionalUpdate:
    async def test_updates_only_authorized_scopes(
        self, provider: DBOpsProvider, allow_list: None, seeded_configs: dict[str, int]
    ) -> None:
        # Each updater is gated on its config's scope: "d1" is authorized, "d2" is not.
        async with provider.write_ops() as w:
            result = await w.bulk_conditional_update_partial(
                BulkConditionalUpdater(
                    updaters=[
                        ConditionalUpdater(
                            updater=Updater(
                                spec=_ConfigRenameSpec(new_name="cfg-d1-v2"),
                                pk_value=seeded_configs["d1"],
                            ),
                            only_if=ExistsQuerier(
                                row_class=_AllowListRow,
                                conditions=[lambda: _AllowListRow.scope == "d1"],
                            ),
                        ),
                        ConditionalUpdater(
                            updater=Updater(
                                spec=_ConfigRenameSpec(new_name="cfg-d2-v2"),
                                pk_value=seeded_configs["d2"],
                            ),
                            only_if=ExistsQuerier(
                                row_class=_AllowListRow,
                                conditions=[lambda: _AllowListRow.scope == "d2"],
                            ),
                        ),
                    ]
                )
            )

        # partial: the "d1" config is updated; the "d2" item (index 1) is forbidden and left as-is.
        assert [row.name for row in result.successes] == ["cfg-d1-v2"]
        assert [e.index for e in result.errors] == [1]
        assert isinstance(result.errors[0].exception, ConditionalMutationForbidden)
        async with provider.read_ops() as r:
            unauthorized = await r.query(
                Querier(row_class=_ConfigRow, pk_value=seeded_configs["d2"])
            )
        assert unauthorized is not None
        assert unauthorized.row.name == "cfg-d2"

    async def test_missing_target_is_reported(
        self, provider: DBOpsProvider, allow_list: None
    ) -> None:
        # The gate is authorized ("d1") but no such row exists -> reported, not a silent success.
        async with provider.write_ops() as w:
            result = await w.bulk_conditional_update_partial(
                BulkConditionalUpdater(
                    updaters=[
                        ConditionalUpdater(
                            updater=Updater(
                                spec=_ConfigRenameSpec(new_name="nope"), pk_value=999_999
                            ),
                            only_if=ExistsQuerier(
                                row_class=_AllowListRow,
                                conditions=[lambda: _AllowListRow.scope == "d1"],
                            ),
                        ),
                    ]
                )
            )
        assert result.successes == []
        assert [e.index for e in result.errors] == [0]


class TestBulkConditionalPurge:
    async def test_purges_only_authorized_scopes(
        self, provider: DBOpsProvider, allow_list: None, seeded_configs: dict[str, int]
    ) -> None:
        # Each purger is gated on its config's scope: "d1" is authorized (deleted), "d2" is not (kept).
        async with provider.write_ops() as w:
            result = await w.bulk_conditional_purge_partial(
                BulkConditionalPurger(
                    purgers=[
                        ConditionalPurger(
                            purger=Purger(row_class=_ConfigRow, pk_value=seeded_configs["d1"]),
                            only_if=ExistsQuerier(
                                row_class=_AllowListRow,
                                conditions=[lambda: _AllowListRow.scope == "d1"],
                            ),
                        ),
                        ConditionalPurger(
                            purger=Purger(row_class=_ConfigRow, pk_value=seeded_configs["d2"]),
                            only_if=ExistsQuerier(
                                row_class=_AllowListRow,
                                conditions=[lambda: _AllowListRow.scope == "d2"],
                            ),
                        ),
                    ]
                )
            )

        # partial: the "d1" config is deleted; the "d2" item (index 1) is forbidden and kept.
        assert {row.id for row in result.successes} == {seeded_configs["d1"]}
        assert [e.index for e in result.errors] == [1]
        assert isinstance(result.errors[0].exception, ConditionalMutationForbidden)
        async with provider.read_ops() as r:
            deleted = await r.query(Querier(row_class=_ConfigRow, pk_value=seeded_configs["d1"]))
            kept = await r.query(Querier(row_class=_ConfigRow, pk_value=seeded_configs["d2"]))
        assert deleted is None
        assert kept is not None
