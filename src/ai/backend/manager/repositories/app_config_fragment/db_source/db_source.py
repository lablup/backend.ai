from __future__ import annotations

import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import sqlalchemy as sa

from ai.backend.common.exception import BackendAIError
from ai.backend.common.identifier.app_config_fragment import AppConfigFragmentID
from ai.backend.common.identifier.user import UserID
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.common.utils import deep_merge
from ai.backend.manager.data.app_config_fragment.types import (
    AppConfigData,
    AppConfigFragmentData,
    AppConfigFragmentKey,
    AppConfigFragmentSearchResult,
    AppConfigScopeType,
    ScopedAppConfigSearchResult,
)
from ai.backend.manager.errors.app_config import AppConfigFragmentNotFound
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.app_config_fragment.creators import (
    AppConfigFragmentCreatorSpec,
)
from ai.backend.manager.repositories.base.creator import NextValuePolicy
from ai.backend.manager.repositories.base.purger import Purger, execute_purger
from ai.backend.manager.repositories.base.querier import BatchQuerier, execute_batch_querier
from ai.backend.manager.repositories.base.types import SearchScope
from ai.backend.manager.repositories.base.updater import Updater, execute_updater
from ai.backend.manager.repositories.ops import DBOpsProvider

app_config_fragment_db_source_resilience = Resilience(
    policies=[
        MetricPolicy(
            MetricArgs(
                domain=DomainType.DB_SOURCE,
                layer=LayerType.APP_CONFIG_FRAGMENT_DB_SOURCE,
            )
        ),
        RetryPolicy(
            RetryArgs(
                max_retries=5,
                retry_delay=0.1,
                backoff_strategy=BackoffStrategy.FIXED,
                non_retryable_exceptions=(BackendAIError,),
            )
        ),
    ]
)

_RANK_GAP = 100


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
    1. Raw CRUD on `(scope_type, scope_id, name)` rows.
    2. Merge-side reads that resolve a user's `AppConfig` view by ordering
       the applicable fragments by `rank` (low → high) and deep-merging.
    """

    _db: ExtendedAsyncSAEngine
    _ops: DBOpsProvider

    def __init__(self, db: ExtendedAsyncSAEngine, ops_provider: DBOpsProvider) -> None:
        self._db = db
        self._ops = ops_provider

    # ── Raw fragment CRUD ──────────────────────────────────────────

    @app_config_fragment_db_source_resilience.apply()
    async def get_by_key(self, key: AppConfigFragmentKey) -> AppConfigFragmentData:
        """Look up a fragment by natural key. Raises
        :class:`AppConfigFragmentNotFound` when no row matches."""
        async with self._db.begin_readonly_session() as db_sess:
            row = await db_sess.scalar(
                sa.select(AppConfigFragmentRow).where(
                    AppConfigFragmentRow.scope_type == key.scope_type,
                    AppConfigFragmentRow.scope_id == key.scope_id,
                    AppConfigFragmentRow.name == key.name,
                )
            )
            if row is None:
                raise AppConfigFragmentNotFound(
                    extra_msg=(
                        f"scope_type={key.scope_type.value!r}, "
                        f"scope_id={key.scope_id!r}, name={key.name!r}"
                    ),
                )
            return row.to_data()

    @app_config_fragment_db_source_resilience.apply()
    async def get_by_id(self, id: AppConfigFragmentID) -> AppConfigFragmentData:
        """Look up a fragment by id. Raises
        :class:`AppConfigFragmentNotFound` when no row matches."""
        async with self._db.begin_readonly_session() as db_sess:
            row = await db_sess.scalar(
                sa.select(AppConfigFragmentRow).where(AppConfigFragmentRow.id == id)
            )
            if row is None:
                raise AppConfigFragmentNotFound(extra_msg=f"id={id!r}")
            return row.to_data()

    @app_config_fragment_db_source_resilience.apply()
    async def get_user_domain_name(self, user_id: uuid.UUID) -> str | None:
        """Single-column lookup of a user's `domain_name`.

        Used by the cache layer to tag merged-view entries with their
        owning domain so domain-scoped fragment writes can target a
        bounded user set during invalidation.
        """
        async with self._db.begin_readonly_session() as db_sess:
            domain_name: str | None = await db_sess.scalar(
                sa.select(UserRow.domain_name).where(UserRow.uuid == user_id)
            )
            return domain_name

    @app_config_fragment_db_source_resilience.apply()
    async def create(self, spec: AppConfigFragmentCreatorSpec) -> AppConfigFragmentData:
        """Insert a fragment, assigning the next-value `rank`
        (``MAX(rank) + gap`` within the `name`) race-free — the same
        pattern as DeploymentRevisionPreset.

        Concurrent inserts for an existing `name` are serialized by
        locking that name's rows. The natural-key UNIQUE violation
        translates to :class:`AppConfigFragmentConflict` via the spec's
        ``integrity_error_checks``.
        """
        policy = NextValuePolicy(
            column=AppConfigFragmentRow.rank,
            scope_condition=lambda: AppConfigFragmentRow.name == spec.name,
            lock_selector=sa.select(AppConfigFragmentRow).where(
                AppConfigFragmentRow.name == spec.name
            ),
            gap=_RANK_GAP,
        )
        async with self._ops.write_ops() as w:
            created = await w.create_with_next_value(policy, spec)
            return created.row.to_data()

    @app_config_fragment_db_source_resilience.apply()
    async def resolve_pk_by_key(
        self,
        key: AppConfigFragmentKey,
    ) -> AppConfigFragmentID | None:
        """Resolve the natural key ``(scope_type, scope_id, name)`` to
        the row's ``id``. Returns ``None`` when no row matches —
        callers translate to a domain-appropriate response."""
        async with self._db.begin_readonly_session() as db_sess:
            pk: AppConfigFragmentID | None = await db_sess.scalar(
                sa.select(AppConfigFragmentRow.id).where(
                    AppConfigFragmentRow.scope_type == key.scope_type,
                    AppConfigFragmentRow.scope_id == key.scope_id,
                    AppConfigFragmentRow.name == key.name,
                )
            )
            return pk

    @app_config_fragment_db_source_resilience.apply()
    async def update(self, updater: Updater[AppConfigFragmentRow]) -> AppConfigFragmentData:
        """Apply a pre-built Updater. Raises
        :class:`AppConfigFragmentNotFound` when the row vanished between
        PK resolution and write."""
        async with self._db.begin_session() as db_sess:
            result = await execute_updater(db_sess, updater)
            if result is None:
                raise AppConfigFragmentNotFound(extra_msg=f"id={updater.pk_value!r}")
            return result.row.to_data()

    @app_config_fragment_db_source_resilience.apply()
    async def purge(self, purger: Purger[AppConfigFragmentRow]) -> bool:
        """Apply a pre-built Purger. Returns ``True`` when a row was
        actually removed (``False`` if the row vanished concurrently)."""
        async with self._db.begin_session() as db_sess:
            result = await execute_purger(db_sess, purger)
            return result is not None

    @app_config_fragment_db_source_resilience.apply()
    async def scoped_search(
        self,
        querier: BatchQuerier,
        scopes: Sequence[SearchScope],
    ) -> AppConfigFragmentSearchResult:
        """Paginated search over fragment rows matching any of ``scopes`` (OR),
        narrowed by ``querier``."""
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(AppConfigFragmentRow)
            result = await execute_batch_querier(db_sess, query, querier, scopes=scopes)
            items = [row.AppConfigFragmentRow.to_data() for row in result.rows]
            return AppConfigFragmentSearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    @app_config_fragment_db_source_resilience.apply()
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

    # ── Merged-view reads (AppConfig) ─────────────────────────────

    @staticmethod
    def _merge_chain(rows: Sequence[AppConfigFragmentRow]) -> _MergedChain:
        """Order `rows` by `rank` (low → high) and deep-merge their
        `config` in that order. Empty result projects to `None`.

        Shared by the single-doc and search merge methods so both paths
        produce the same shape.
        """
        ordered = sorted(rows, key=lambda row: row.rank)
        merged: Mapping[str, Any] = {}
        for row in ordered:
            if row.config is None:
                continue
            merged = deep_merge(merged, row.config)
        return _MergedChain(
            fragments=[row.to_data() for row in ordered],
            config=(merged or None),
        )

    @app_config_fragment_db_source_resilience.apply()
    async def get_user_app_config(
        self,
        user_id: UserID,
        config_name: str,
    ) -> AppConfigData:
        """Resolve a single AppConfig view for `(user_id, config_name)`.

        One SQL: resolves `domain_name` via a `users` subquery and fetches
        the fragments applicable to the caller (`scope_id_match` gates
        PUBLIC / the user's DOMAIN / the user's USER rows). Ordering and
        deep-merge happen by `rank` in `_merge_chain`.
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
        query = sa.select(AppConfigFragmentRow).where(
            AppConfigFragmentRow.name == config_name,
            AppConfigFragmentRow.scope_id == scope_id_match,
        )
        async with self._db.begin_readonly_session() as db_sess:
            rows = (await db_sess.execute(query)).scalars().all()

        if not rows:
            return AppConfigData(
                user_id=user_id,
                name=config_name,
                fragments=[],
                config=None,
            )

        merged = self._merge_chain(rows)
        return AppConfigData(
            user_id=user_id,
            name=config_name,
            fragments=merged.fragments,
            config=merged.config,
        )

    async def _search_merged_app_configs(
        self,
        querier: BatchQuerier,
        scopes: Sequence[SearchScope] | None,
    ) -> ScopedAppConfigSearchResult:
        """Cross-user merged search shared by the scoped and admin paths.

        Joins `users` so each `(user_id, name)` view is produced, then
        groups the scoped page of applicable fragments by `(user_id, name)`
        and feeds each group through `_merge_chain` (rank-ordered) to
        produce one `AppConfigData`.

        When `scopes` is given the user set is the OR-union of those scopes
        (each `UserAppConfigSearchScope` matches `UserRow.uuid`); `None` is
        the global admin path. `execute_batch_querier` ORs the scopes and
        the `(user_id, name)` grouping deduplicates any overlap — a user
        reached via two scopes still yields exactly one AppConfig.

        Filtering / ordering / pagination run through the shared
        scoped-search helper (`execute_batch_querier`).
        """
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
                UserRow.domain_name,
            ),
            (
                AppConfigFragmentRow.scope_type == AppConfigScopeType.USER,
                sa.cast(UserRow.uuid, sa.Text),
            ),
        )
        query = (
            sa.select(
                UserRow.uuid.label("user_id"),
                AppConfigFragmentRow,
            )
            .select_from(UserRow)
            .join(
                AppConfigFragmentRow,
                AppConfigFragmentRow.scope_id == scope_id_match,
            )
        )
        async with self._db.begin_readonly_session() as db_sess:
            if scopes is not None:
                result = await execute_batch_querier(db_sess, query, querier, scopes=scopes)
            else:
                result = await execute_batch_querier(db_sess, query, querier)

        groups: dict[tuple[uuid.UUID, str], list[AppConfigFragmentRow]] = {}
        for row in result.rows:
            fragment_row = row.AppConfigFragmentRow
            groups.setdefault((row.user_id, fragment_row.name), []).append(fragment_row)

        items: list[AppConfigData] = []
        for (user_id, name), rows in groups.items():
            merged = self._merge_chain(rows)
            items.append(
                AppConfigData(
                    user_id=UserID(user_id),
                    name=name,
                    fragments=merged.fragments,
                    config=merged.config,
                )
            )

        return ScopedAppConfigSearchResult(
            items=items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    @app_config_fragment_db_source_resilience.apply()
    async def scoped_search_app_configs(
        self,
        querier: BatchQuerier,
        scopes: Sequence[SearchScope],
    ) -> ScopedAppConfigSearchResult:
        """Merged-view search restricted to `scopes` (OR across users)."""
        return await self._search_merged_app_configs(querier, scopes)

    @app_config_fragment_db_source_resilience.apply()
    async def admin_search_app_configs(
        self,
        querier: BatchQuerier,
    ) -> ScopedAppConfigSearchResult:
        """Cross-user merged search (admin only) — no scope restriction."""
        return await self._search_merged_app_configs(querier, None)
