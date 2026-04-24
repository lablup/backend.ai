from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import Any, cast

import sqlalchemy as sa
from sqlalchemy.engine.cursor import CursorResult

from ai.backend.manager.data.app_config_policy.types import AppConfigPolicyData
from ai.backend.manager.models.app_config_policy.row import AppConfigPolicyRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.app_config_policy.types import (
    AppConfigPolicySearchResult,
)
from ai.backend.manager.repositories.base.querier import BatchQuerier, execute_batch_querier


class AppConfigPolicyDBSource:
    """Database operations for `app_config_policies`.

    All public methods own their transaction boundary.
    """

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def get(self, config_name: str) -> AppConfigPolicyData | None:
        """Look up a policy by its `config_name` (UNIQUE).

        Returns `None` if no policy exists for `config_name`.
        """
        async with self._db.begin_readonly_session() as db_sess:
            row = await db_sess.scalar(
                sa.select(AppConfigPolicyRow).where(AppConfigPolicyRow.config_name == config_name)
            )
            return row.to_data() if row is not None else None

    async def get_by_id(self, id: uuid.UUID) -> AppConfigPolicyData | None:
        """Look up a policy by row id."""
        async with self._db.begin_readonly_session() as db_sess:
            row = await db_sess.scalar(
                sa.select(AppConfigPolicyRow).where(AppConfigPolicyRow.id == id)
            )
            return row.to_data() if row is not None else None

    async def create(
        self,
        config_name: str,
        scope_sources: Sequence[str],
    ) -> AppConfigPolicyData:
        """Strict insert. Errors if a policy already exists for `config_name`
        (UNIQUE constraint).
        """
        async with self._db.begin_session() as db_sess:
            row = AppConfigPolicyRow(
                config_name=config_name,
                scope_sources=list(scope_sources),
            )
            db_sess.add(row)
            await db_sess.flush()
            await db_sess.refresh(row)
            return row.to_data()

    async def update(
        self,
        config_name: str,
        scope_sources: Sequence[str],
    ) -> AppConfigPolicyData | None:
        """Replace `scope_sources` for the policy identified by `config_name`.

        `config_name` itself is immutable (BEP-1052 §1) and cannot be changed
        through this method. Returns `None` when no row exists for
        `config_name`.
        """
        async with self._db.begin_session() as db_sess:
            row = await db_sess.scalar(
                sa.select(AppConfigPolicyRow).where(AppConfigPolicyRow.config_name == config_name)
            )
            if row is None:
                return None
            row.scope_sources = list(scope_sources)
            await db_sess.flush()
            await db_sess.refresh(row)
            return row.to_data()

    async def purge(self, config_name: str) -> bool:
        """Delete the policy identified by `config_name`. Returns `True`
        when a row was actually removed, `False` otherwise.

        The DB-side FK from `app_config_fragments.name` to
        `app_config_policies.config_name` (NO ACTION) blocks the delete
        when fragments still reference this policy — the service layer
        is expected to reject before this point with a friendlier error.
        """
        async with self._db.begin_session() as db_sess:
            result = await db_sess.execute(
                sa.delete(AppConfigPolicyRow).where(AppConfigPolicyRow.config_name == config_name)
            )
            return cast(CursorResult[Any], result).rowcount > 0

    async def search(self, querier: BatchQuerier) -> AppConfigPolicySearchResult:
        """Paginated search across all policies."""
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(AppConfigPolicyRow)
            result = await execute_batch_querier(db_sess, query, querier)
            items = [row.AppConfigPolicyRow.to_data() for row in result.rows]
            return AppConfigPolicySearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )
