"""Database source for app config fragment repository operations."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.common.exception import BackendAIError
from ai.backend.common.identifier.app_config_fragment import AppConfigFragmentID
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
from ai.backend.manager.repositories.app_config_fragment.creators import (
    AppConfigFragmentCreatorSpec,
)
from ai.backend.manager.repositories.app_config_fragment.purgers import (
    AppConfigFragmentPurgerSpec,
)
from ai.backend.manager.repositories.app_config_fragment.types import (
    ResolvedAppConfigScope,
)
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    NoPagination,
    Querier,
    Updater,
)
from ai.backend.manager.repositories.base.rbac.entity_creator import RBACEntityCreator
from ai.backend.manager.repositories.base.rbac.entity_purger import RBACEntityPurger
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
    async def create(self, spec: AppConfigFragmentCreatorSpec) -> AppConfigFragmentData:
        # A public fragment is GLOBAL — outside the RBAC scope hierarchy — so it has no scope
        # element and binds to no scope, making its create a plain insert.
        element_type = spec.scope_type.to_rbac_element_type()
        rbac_creator = RBACEntityCreator(
            spec=spec,
            element_type=RBACElementType.APP_CONFIG_FRAGMENT,
            scope_ref=(
                RBACElementRef(element_type, str(spec.scope_id))
                if element_type is not None
                else None
            ),
        )
        async with self._rbac_ops_provider.write_ops() as w:
            return (await w.create_scoped(rbac_creator)).row.to_data()

    @app_config_fragment_db_source_resilience.apply()
    async def get_by_id(self, fragment_id: AppConfigFragmentID) -> AppConfigFragmentData:
        async with self._rbac_ops_provider.read_ops() as r:
            result = await r.query(Querier(row_class=AppConfigFragmentRow, pk_value=fragment_id))
            if result is None:
                raise AppConfigFragmentNotFound(f"App config fragment {fragment_id} not found")
            return result.row.to_data()

    @app_config_fragment_db_source_resilience.apply()
    async def update(self, updater: Updater[AppConfigFragmentRow]) -> AppConfigFragmentData:
        async with self._rbac_ops_provider.write_ops() as w:
            result = await w.update(updater)
            if result is None:
                raise AppConfigFragmentNotFound(f"App config fragment {updater.pk_value} not found")
            return result.row.to_data()

    @app_config_fragment_db_source_resilience.apply()
    async def purge(self, purger_spec: AppConfigFragmentPurgerSpec) -> AppConfigFragmentData:
        rbac_purger = RBACEntityPurger(
            row_class=AppConfigFragmentRow,
            pk_value=purger_spec.fragment_id,
            spec=purger_spec,
        )
        async with self._rbac_ops_provider.write_ops() as w:
            result = await w.purge_scoped(rbac_purger)
            if result is None:
                raise AppConfigFragmentNotFound(
                    f"App config fragment {purger_spec.fragment_id} not found"
                )
            return result.row.to_data()

    @app_config_fragment_db_source_resilience.apply()
    async def bulk_update(
        self,
        updaters: Sequence[Updater[AppConfigFragmentRow]],
    ) -> AppConfigFragmentBulkResult:
        """Update many fragments with per-item partial success."""
        async with self._rbac_ops_provider.write_ops() as w:
            result = await w.bulk_update_partial(updaters)
            succeeded = [row.to_data() for row in result.successes]
            succeeded_ids = {data.id for data in succeeded}
            errors_by_index = {e.index: str(e.exception) for e in result.errors}
            # A missing PK is skipped by the partial op (no row, no error); report as not-found.
            failed = [
                AppConfigFragmentBulkItemError(
                    index=index,
                    message=errors_by_index.get(
                        index, f"App config fragment {updater.pk_value} not found"
                    ),
                )
                for index, updater in enumerate(updaters)
                if index in errors_by_index or updater.pk_value not in succeeded_ids
            ]
            return AppConfigFragmentBulkResult(succeeded=succeeded, failed=failed)

    @app_config_fragment_db_source_resilience.apply()
    async def bulk_purge(
        self,
        purger_specs: Sequence[AppConfigFragmentPurgerSpec],
    ) -> AppConfigFragmentBulkResult:
        """Purge many fragments with per-item partial success, unbinding each from its scope."""
        purgers = [
            RBACEntityPurger(
                row_class=AppConfigFragmentRow,
                pk_value=spec.fragment_id,
                spec=spec,
            )
            for spec in purger_specs
        ]
        async with self._rbac_ops_provider.write_ops() as w:
            result = await w.bulk_purge_scoped_partial(purgers)
            succeeded = [row.to_data() for row in result.successes]
            succeeded_ids = {data.id for data in succeeded}
            errors_by_index = {e.index: str(e.exception) for e in result.errors}
            # A missing PK is skipped by the partial op (no row, no error); report as not-found.
            failed = [
                AppConfigFragmentBulkItemError(
                    index=index,
                    message=errors_by_index.get(
                        index, f"App config fragment {spec.fragment_id} not found"
                    ),
                )
                for index, spec in enumerate(purger_specs)
                if index in errors_by_index or spec.fragment_id not in succeeded_ids
            ]
            return AppConfigFragmentBulkResult(succeeded=succeeded, failed=failed)

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
        """Scoped path: query fragments restricted to ``scopes`` (combined with OR)."""
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
        self, config_names: list[str], scope: ResolvedAppConfigScope | None = None
    ) -> list[AppConfigFragmentData]:
        """Visible fragments for several ``config_names`` in one query, ordered by ascending ``rank``.

        ``public`` always contributes; a ``scope`` additionally admits its domain and user
        overlay, while ``scope=None`` (anonymous) sees only ``public``. Rank-ordered so the
        caller can group by name and deep-merge each name's fragments in order.
        """
        if not config_names:
            return []
        scope_visibility = [AppConfigFragmentConditions.by_public_visibility()]
        if scope is not None:
            scope_visibility += [
                AppConfigFragmentConditions.by_domain_visibility(scope.domain_id),
                AppConfigFragmentConditions.by_user_visibility(scope.user_id),
            ]
        querier = BatchQuerier(
            pagination=NoPagination(),
            conditions=[
                AppConfigFragmentConditions.by_config_names(config_names),
                lambda: sa.or_(*(visibility() for visibility in scope_visibility)),
            ],
            orders=[AppConfigAllowListRow.rank.asc()],
        )
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
            result = await r.batch_query_in_global(selector, querier)
            return [row.AppConfigFragmentRow.to_data() for row in result.rows]
