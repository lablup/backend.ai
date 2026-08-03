"""Database source for app config fragment repository operations."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.common.exception import BackendAIError
from ai.backend.common.identifier.app_config_fragment import AppConfigFragmentID
from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.user import UserID
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.app_config_fragment.types import (
    AppConfigFragmentBulkItemError,
    AppConfigFragmentBulkResult,
    AppConfigFragmentData,
    AppConfigFragmentSearchResult,
)
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.errors.app_config import (
    AppConfigFragmentNotFound,
)
from ai.backend.manager.models.app_config_allow_list.row import AppConfigAllowListRow
from ai.backend.manager.models.app_config_fragment.conditions import AppConfigFragmentConditions
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.models.scopes import SearchScope
from ai.backend.manager.repositories.app_config_fragment.purgers import (
    AppConfigFragmentPurgerSpec,
)
from ai.backend.manager.repositories.app_config_fragment.upserters import (
    AppConfigFragmentUpserterSpec,
)
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    NoPagination,
    Querier,
)
from ai.backend.manager.repositories.base.rbac.entity_purger import RBACEntityPurger
from ai.backend.manager.repositories.base.rbac.entity_upserter import (
    ConflictTarget,
    RBACEntityUpserter,
)
from ai.backend.manager.repositories.ops.rbac.provider import RBACOpsProvider

__all__ = ("AppConfigFragmentDBSource",)

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


class AppConfigFragmentDBSource:
    """Database source for app config fragment operations."""

    _rbac_ops_provider: RBACOpsProvider

    def __init__(self, rbac_ops_provider: RBACOpsProvider) -> None:
        self._rbac_ops_provider = rbac_ops_provider

    @app_config_fragment_db_source_resilience.apply()
    async def bulk_upsert(
        self, specs: Sequence[AppConfigFragmentUpserterSpec]
    ) -> list[AppConfigFragmentData]:
        """Upsert each fragment at its scope in one transaction (all-or-nothing).

        Each item inserts-or-updates; a newly inserted row binds to its scope, an updated one
        keeps its binding. A ``public`` fragment is GLOBAL, so it binds to no scope.
        """
        async with self._rbac_ops_provider.write_ops() as w:
            results: list[AppConfigFragmentData] = []
            for spec in specs:
                # A public fragment is GLOBAL — no scope element, so it binds to nothing. Its
                # NULL scope_id still keys it like any other row (NULLS NOT DISTINCT), so one
                # conflict target serves every scope.
                element_type = spec.scope_type.to_rbac_element_type()
                upserter = RBACEntityUpserter(
                    spec=spec,
                    element_type=RBACElementType.APP_CONFIG_FRAGMENT,
                    scope_ref=(
                        RBACElementRef(element_type, str(spec.scope_id))
                        if element_type is not None
                        else None
                    ),
                    conflict_target=ConflictTarget(
                        columns=["config_name", "scope_type", "scope_id"]
                    ),
                )
                results.append((await w.upsert_scoped(upserter)).row.to_data())
            return results

    @app_config_fragment_db_source_resilience.apply()
    async def get_by_id(self, fragment_id: AppConfigFragmentID) -> AppConfigFragmentData:
        async with self._rbac_ops_provider.read_ops() as r:
            result = await r.query(Querier(row_class=AppConfigFragmentRow, pk_value=fragment_id))
            if result is None:
                raise AppConfigFragmentNotFound(f"App config fragment {fragment_id} not found")
            return result.row.to_data()

    @app_config_fragment_db_source_resilience.apply()
    async def purge(self, purger_spec: AppConfigFragmentPurgerSpec) -> AppConfigFragmentData:
        rbac_purger = RBACEntityPurger(spec=purger_spec)
        async with self._rbac_ops_provider.write_ops() as w:
            result = await w.purge_scoped(rbac_purger)
            if result is None:
                raise AppConfigFragmentNotFound(
                    f"App config fragment {purger_spec.fragment_id} not found"
                )
            return result.row.to_data()

    @app_config_fragment_db_source_resilience.apply()
    async def bulk_purge(
        self,
        purger_specs: Sequence[AppConfigFragmentPurgerSpec],
    ) -> AppConfigFragmentBulkResult:
        """Purge many fragments with per-item partial success, unbinding each from its scope."""
        purgers = [RBACEntityPurger(spec=spec) for spec in purger_specs]
        async with self._rbac_ops_provider.write_ops() as w:
            result = await w.bulk_purge_scoped_partial(purgers)
            succeeded = [row.to_data() for row in result.successes]
            succeeded_ids = {data.id for data in succeeded}
            errors_by_index = {e.index: str(e.exception) for e in result.errors}
            # A missing PK is skipped by the partial op (no row, no error); report as not-found.
            failed = [
                AppConfigFragmentBulkItemError(
                    id=spec.fragment_id,
                    message=errors_by_index.get(
                        index, f"App config fragment {spec.fragment_id} not found"
                    ),
                )
                for index, spec in enumerate(purger_specs)
                if index in errors_by_index or spec.fragment_id not in succeeded_ids
            ]
            return AppConfigFragmentBulkResult(succeeded=succeeded, failed=failed)

    @app_config_fragment_db_source_resilience.apply()
    async def purge_by_config_names(
        self,
        scope: SearchScope,
        config_names: Sequence[str],
    ) -> list[AppConfigFragmentData]:
        """Purge one scope's fragments for ``config_names``, all-or-nothing.

        A scope holds at most one fragment per config name, so the names resolve to ids inside
        the purging transaction and each row is unbound from its scope as a purge by id is. A
        name the scope holds no fragment for raises before anything is deleted, so a typo
        cannot take a neighbouring config with it.
        """
        # A name repeated in the request still names one fragment.
        requested = list(dict.fromkeys(config_names))
        querier = BatchQuerier(
            pagination=NoPagination(),
            conditions=[AppConfigFragmentConditions.by_config_names(requested)],
        )
        async with self._rbac_ops_provider.write_ops() as w:
            found = await w.batch_query_with_scopes(
                sa.select(AppConfigFragmentRow), querier, [scope]
            )
            rows = {
                row.AppConfigFragmentRow.config_name: row.AppConfigFragmentRow for row in found.rows
            }
            missing = [config_name for config_name in requested if config_name not in rows]
            if missing:
                raise AppConfigFragmentNotFound(
                    f"No app config fragment at this scope for: {', '.join(missing)}"
                )
            purged: list[AppConfigFragmentData] = []
            for config_name in requested:
                fragment_id = AppConfigFragmentID(rows[config_name].id)
                result = await w.purge_scoped(
                    RBACEntityPurger(spec=AppConfigFragmentPurgerSpec(fragment_id=fragment_id))
                )
                if result is None:
                    raise AppConfigFragmentNotFound(f"App config fragment {fragment_id} not found")
                purged.append(result.row.to_data())
            return purged

    @app_config_fragment_db_source_resilience.apply()
    async def admin_search(self, querier: BatchQuerier) -> AppConfigFragmentSearchResult:
        """Superadmin/internal path: query across all fragments with no scope filter."""
        async with self._rbac_ops_provider.read_ops() as r:
            result = await r.batch_query_in_global(sa.select(AppConfigFragmentRow), querier)
            return AppConfigFragmentSearchResult(
                items=[row.AppConfigFragmentRow.to_data() for row in result.rows],
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    @app_config_fragment_db_source_resilience.apply()
    async def scoped_search(
        self,
        querier: BatchQuerier,
        scopes: Sequence[SearchScope],
    ) -> AppConfigFragmentSearchResult:
        """Scoped path: query the fragments written at ``scopes`` (combined with OR)."""
        async with self._rbac_ops_provider.read_ops() as r:
            result = await r.batch_query_with_scopes(
                sa.select(AppConfigFragmentRow), querier, scopes
            )
            return AppConfigFragmentSearchResult(
                items=[row.AppConfigFragmentRow.to_data() for row in result.rows],
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    @app_config_fragment_db_source_resilience.apply()
    async def list_visible_fragments_bulk(
        self, config_names: list[str], user_id: UserID | None, domain_id: DomainID | None
    ) -> list[AppConfigFragmentData]:
        """Visible fragments for several ``config_names``, ordered by ascending ``rank``.

        ``public`` always contributes; a ``user_id`` additionally admits that user's own
        overlay and a ``domain_id`` its domain's, while naming neither (anonymous) sees only
        ``public``. Both come from the session, so neither is looked up here. Rank-ordered so
        the caller can group by name and deep-merge each name's fragments in order.
        """
        if not config_names:
            return []
        # Join each fragment to its allow-list entry (indexed ``(config_name, scope_type)`` FK
        # pair), which carries the merge ``rank`` the result is ordered by.
        selector = sa.select(AppConfigFragmentRow).join(
            AppConfigAllowListRow,
            sa.and_(
                AppConfigAllowListRow.config_name == AppConfigFragmentRow.config_name,
                AppConfigAllowListRow.scope_type == AppConfigFragmentRow.scope_type,
            ),
        )
        async with self._rbac_ops_provider.read_ops() as r:
            scope_visibility = [AppConfigFragmentConditions.by_public_visibility()]
            if user_id is not None:
                scope_visibility.append(AppConfigFragmentConditions.by_user_visibility(user_id))
            if domain_id is not None:
                scope_visibility.append(AppConfigFragmentConditions.by_domain_visibility(domain_id))
            querier = BatchQuerier(
                pagination=NoPagination(),
                conditions=[
                    AppConfigFragmentConditions.by_config_names(config_names),
                    lambda: sa.or_(*(visibility() for visibility in scope_visibility)),
                ],
                orders=[AppConfigAllowListRow.rank.asc()],
            )
            result = await r.batch_query_in_global(selector, querier)
            return [row.AppConfigFragmentRow.to_data() for row in result.rows]
