from __future__ import annotations

import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, cast

import sqlalchemy as sa
from sqlalchemy.engine.cursor import CursorResult

from ai.backend.common.utils import deep_merge
from ai.backend.manager.data.app_config_fragment.types import (
    AppConfigFragmentData,
    AppConfigFragmentKey,
    AppConfigScopeType,
)
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.models.app_config_policy.row import AppConfigPolicyRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.app_config_fragment.types import (
    AppConfigData,
    AppConfigFragmentSearchResult,
    AppConfigFragmentSearchScope,
    AppConfigSearchResult,
    UserAppConfigSearchScope,
)
from ai.backend.manager.repositories.base.querier import BatchQuerier, execute_batch_querier


@dataclass(frozen=True, slots=True)
class _MergedChain:
    """Internal return type of `_merge_chain` — the ordered fragments
    that contributed to the merge plus the deep-merged config (or
    `None` when every contributing fragment is empty).

    Re-shaped into `AppConfigData` by callers that also know the
    `(user_id, name)` they were resolving for.
    """

    fragments: list[AppConfigFragmentData]
    config: Mapping[str, Any] | None


class AppConfigFragmentDBSource:
    """Database operations for `app_config_fragments`.

    Two roles:
    1. Raw CRUD on `(scope_type, scope_id, name)` rows (BEP-1052 §2).
    2. Merge-side reads that resolve a user's `AppConfig` view by joining
       `app_config_policies` to derive the chain (BEP-1052 §5).
    """

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    # ── Raw fragment CRUD ──────────────────────────────────────────

    async def get(self, key: AppConfigFragmentKey) -> AppConfigFragmentData | None:
        async with self._db.begin_readonly_session() as db_sess:
            row = await db_sess.scalar(
                sa.select(AppConfigFragmentRow).where(
                    AppConfigFragmentRow.scope_type == key.scope_type,
                    AppConfigFragmentRow.scope_id == key.scope_id,
                    AppConfigFragmentRow.name == key.name,
                )
            )
            return row.to_data() if row is not None else None

    async def get_by_id(self, id: uuid.UUID) -> AppConfigFragmentData | None:
        async with self._db.begin_readonly_session() as db_sess:
            row = await db_sess.scalar(
                sa.select(AppConfigFragmentRow).where(AppConfigFragmentRow.id == id)
            )
            return row.to_data() if row is not None else None

    async def create(
        self,
        key: AppConfigFragmentKey,
        extra_config: Mapping[str, Any],
    ) -> AppConfigFragmentData:
        """Strict insert. Errors if a row already exists for the natural key."""
        async with self._db.begin_session() as db_sess:
            row = AppConfigFragmentRow(
                scope_type=key.scope_type,
                scope_id=key.scope_id,
                name=key.name,
                extra_config=dict(extra_config),
            )
            db_sess.add(row)
            await db_sess.flush()
            await db_sess.refresh(row)
            return row.to_data()

    async def update(
        self,
        key: AppConfigFragmentKey,
        extra_config: Mapping[str, Any],
    ) -> AppConfigFragmentData | None:
        """Wholesale-replace the stored value. Returns `None` when the
        natural key does not exist."""
        async with self._db.begin_session() as db_sess:
            row = await db_sess.scalar(
                sa.select(AppConfigFragmentRow).where(
                    AppConfigFragmentRow.scope_type == key.scope_type,
                    AppConfigFragmentRow.scope_id == key.scope_id,
                    AppConfigFragmentRow.name == key.name,
                )
            )
            if row is None:
                return None
            row.extra_config = dict(extra_config)
            await db_sess.flush()
            await db_sess.refresh(row)
            return row.to_data()

    async def purge(self, key: AppConfigFragmentKey) -> bool:
        """Delete the fragment identified by the natural key. Returns
        `True` when a row was actually removed."""
        async with self._db.begin_session() as db_sess:
            result = await db_sess.execute(
                sa.delete(AppConfigFragmentRow).where(
                    AppConfigFragmentRow.scope_type == key.scope_type,
                    AppConfigFragmentRow.scope_id == key.scope_id,
                    AppConfigFragmentRow.name == key.name,
                )
            )
            return cast(CursorResult[Any], result).rowcount > 0

    async def search(
        self,
        scope: AppConfigFragmentSearchScope,
        querier: BatchQuerier,
    ) -> AppConfigFragmentSearchResult:
        """Scope-bound search (per `(scope_type, scope_id)`)."""
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(AppConfigFragmentRow)
            result = await execute_batch_querier(db_sess, query, querier, scope=scope)
            items = [row.AppConfigFragmentRow.to_data() for row in result.rows]
            return AppConfigFragmentSearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    async def admin_search(
        self,
        querier: BatchQuerier,
    ) -> AppConfigFragmentSearchResult:
        """Cross-scope admin search — no scope binding. Authorization
        is enforced at the service layer before this is reached."""
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(AppConfigFragmentRow)
            result = await execute_batch_querier(db_sess, query, querier)
            items = [row.AppConfigFragmentRow.to_data() for row in result.rows]
            return AppConfigFragmentSearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    # ── Merged-view reads (AppConfig, BEP-1052 §5) ────────────────

    @staticmethod
    def _merge_chain(
        rows: Sequence[AppConfigFragmentRow],
        chain: Sequence[str],
    ) -> _MergedChain:
        """Order `rows` by `chain` (low → high) and deep-merge their
        `extra_config` in that order. Empty result projects to `None`
        per BEP-1052 §3 null projection.

        Shared by the single-doc and search merge methods so both paths
        produce the same shape.
        """
        by_scope = {row.scope_type: row for row in rows}
        ordered = [
            by_scope[AppConfigScopeType(s)] for s in chain if AppConfigScopeType(s) in by_scope
        ]
        merged: Mapping[str, Any] = {}
        for row in ordered:
            if row.extra_config is None:
                continue
            merged = deep_merge(merged, row.extra_config)
        return _MergedChain(
            fragments=[row.to_data() for row in ordered],
            config=(merged or None),
        )

    async def get_user_app_config(
        self,
        user_id: uuid.UUID,
        config_name: str,
    ) -> AppConfigData:
        """Resolve a single AppConfig view for `(user_id, config_name)`.

        One SQL: resolves `domain_name` via a `users` subquery, joins
        `app_config_policies` to derive the chain (`scope_sources`), and
        fetches only the scope rows that participate in that chain. The
        natural-key UniqueConstraint bounds the result.
        """
        user_domain_sq = (
            sa.select(UserRow.domain_name).where(UserRow.uuid == user_id).scalar_subquery()
        )
        scope_id_match = sa.case(
            (
                AppConfigFragmentRow.scope_type == AppConfigScopeType.PUBLIC,
                sa.literal("public"),
            ),
            (
                AppConfigFragmentRow.scope_type.in_([
                    AppConfigScopeType.DOMAIN,
                    AppConfigScopeType.DOMAIN_USER_DEFAULTS,
                ]),
                user_domain_sq,
            ),
            (
                AppConfigFragmentRow.scope_type == AppConfigScopeType.USER,
                sa.literal(str(user_id)),
            ),
        )
        query = (
            sa.select(AppConfigFragmentRow, AppConfigPolicyRow.scope_sources)
            .join(
                AppConfigPolicyRow,
                AppConfigPolicyRow.config_name == AppConfigFragmentRow.name,
            )
            .where(
                AppConfigFragmentRow.name == config_name,
                AppConfigFragmentRow.scope_id == scope_id_match,
                sa.cast(AppConfigFragmentRow.scope_type, sa.Text)
                == sa.func.any(AppConfigPolicyRow.scope_sources),
            )
        )
        async with self._db.begin_readonly_session() as db_sess:
            result = (await db_sess.execute(query)).all()

        if not result:
            return AppConfigData(
                user_id=user_id,
                name=config_name,
                fragments=[],
                config=None,
            )

        # `config_name` is UNIQUE and we filtered on a single value, so
        # every result row carries the same `scope_sources`.
        chain = result[0].scope_sources
        rows = [r.AppConfigFragmentRow for r in result]
        merged = self._merge_chain(rows, chain)
        return AppConfigData(
            user_id=user_id,
            name=config_name,
            fragments=merged.fragments,
            config=merged.config,
        )

    async def search_user_app_configs(
        self,
        scope: UserAppConfigSearchScope,
        querier: BatchQuerier,
    ) -> AppConfigSearchResult:
        """Connection counterpart of `get_user_app_config`. Joins
        `app_config_policies` and groups by `name`; each group is fed
        through `_merge_chain` to produce one `AppConfigData`.

        Implementation is left as a placeholder until the GraphQL surface
        for `myAppConfigs` lands — the single-doc path above already
        exercises the merge SQL contract.
        """
        raise NotImplementedError("search_user_app_configs lands with the AppConfig GQL surface")

    async def admin_search_app_configs(
        self,
        querier: BatchQuerier,
    ) -> AppConfigSearchResult:
        """Cross-user merged search (admin only). Same SQL pattern as
        `search_user_app_configs` joined with `users` to drop the user
        binding — placeholder until the admin GQL surface lands.
        """
        raise NotImplementedError("admin_search_app_configs lands with the admin GQL surface")
