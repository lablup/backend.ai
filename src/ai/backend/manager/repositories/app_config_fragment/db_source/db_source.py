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
from ai.backend.manager.repositories.app_config_fragment.scope_binders import (
    AppConfigFragmentScopeUnbinder,
    fragment_rbac_scope_ref,
)
from ai.backend.manager.repositories.app_config_fragment.types import (
    AppConfigScopeArguments,
)
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    BulkCreator,
    NoPagination,
    Purger,
    Querier,
    Updater,
)
from ai.backend.manager.repositories.base.rbac.entity_creator import RBACEntityCreator
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
        # The allow-list FK gates existence (no row → ``AppConfigFragmentWriteNotAllowed``),
        # and create binds the fragment to its RBAC scope in the same tx. A ``public``
        # fragment is global-scoped (``scope_ref`` is ``None``) and carries no association.
        rbac_creator = RBACEntityCreator(
            spec=spec,
            element_type=RBACElementType.APP_CONFIG_FRAGMENT,
            scope_ref=fragment_rbac_scope_ref(spec.scope_type, spec.scope_id),
        )
        async with self._rbac_ops_provider.write_ops() as w:
            created = await w.bulk_create_scoped([rbac_creator])
            return created.rows[0].to_data()

    @app_config_fragment_db_source_resilience.apply()
    async def get_by_id(self, fragment_id: AppConfigFragmentID) -> AppConfigFragmentData:
        async with self._rbac_ops_provider.read_ops() as r:
            result = await r.query(Querier(row_class=AppConfigFragmentRow, pk_value=fragment_id))
            if result is None:
                raise AppConfigFragmentNotFound(f"App config fragment {fragment_id} not found")
            return result.row.to_data()

    @app_config_fragment_db_source_resilience.apply()
    async def update(self, updater: Updater[AppConfigFragmentRow]) -> AppConfigFragmentData:
        # No write-gate: the allow-list FK keeps a fragment row alive only while its
        # ``(config_name, scope_type)`` entry exists, so an existing fragment is writable.
        async with self._rbac_ops_provider.write_ops() as w:
            result = await w.update(updater)
            if result is None:
                raise AppConfigFragmentNotFound(f"App config fragment {updater.pk_value} not found")
            return result.row.to_data()

    @app_config_fragment_db_source_resilience.apply()
    async def purge(self, purger: Purger[AppConfigFragmentRow]) -> AppConfigFragmentData:
        # Purge is an RBAC unbind: the row and its scope association are deleted atomically
        # (no FK cascade; a ``public`` fragment has none). Fetch first for its scope and data.
        async with self._rbac_ops_provider.write_ops() as w:
            found = await w.query(Querier(row_class=AppConfigFragmentRow, pk_value=purger.pk_value))
            if found is None:
                raise AppConfigFragmentNotFound(f"App config fragment {purger.pk_value} not found")
            data = found.row.to_data()
            result = await w.unbind_scope_entities(
                AppConfigFragmentScopeUnbinder(
                    fragment_id=data.id,
                    fragment_scope_type=data.scope_type,
                    fragment_scope_id=data.scope_id,
                )
            )
            # Read and delete are separate statements under READ COMMITTED: a zero count
            # means a concurrent purge already removed the row — not-found, not stale success.
            if result.deleted_count == 0:
                raise AppConfigFragmentNotFound(f"App config fragment {purger.pk_value} not found")
            return data

    @app_config_fragment_db_source_resilience.apply()
    async def bulk_create(
        self,
        bulk_creator: BulkCreator[AppConfigFragmentRow],
    ) -> AppConfigFragmentBulkResult:
        """Create many fragments with per-item partial success."""
        async with self._rbac_ops_provider.write_ops() as w:
            result = await w.bulk_create_partial(bulk_creator)
            return AppConfigFragmentBulkResult(
                succeeded=[row.to_data() for row in result.successes],
                failed=[
                    AppConfigFragmentBulkItemError(index=error.index, message=str(error.exception))
                    for error in result.errors
                ],
            )

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
        purgers: Sequence[Purger[AppConfigFragmentRow]],
    ) -> AppConfigFragmentBulkResult:
        """Purge many fragments with per-item partial success."""
        async with self._rbac_ops_provider.write_ops() as w:
            result = await w.bulk_purge_partial(list(purgers))
            succeeded = [row.to_data() for row in result.successes]
            succeeded_ids = {data.id for data in succeeded}
            errors_by_index = {e.index: str(e.exception) for e in result.errors}
            # A missing PK is skipped by the partial op (no row, no error); report as not-found.
            failed = [
                AppConfigFragmentBulkItemError(
                    index=index,
                    message=errors_by_index.get(
                        index, f"App config fragment {purger.pk_value} not found"
                    ),
                )
                for index, purger in enumerate(purgers)
                if index in errors_by_index or purger.pk_value not in succeeded_ids
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
        self, config_names: list[str], scope: AppConfigScopeArguments
    ) -> list[AppConfigFragmentData]:
        """Visible fragments for several ``config_names`` at once, in a single query.

        Selects the requested names AND any one of the principal's visible scopes (public,
        its domain, or its own user). The scope filter is name-independent, so it is a single
        OR group AND-combined with the name membership. Merge priority (``rank``) lives on the
        joined allow-list entry; the result is always ordered by ascending ``rank`` so the
        caller can group by name (each name's subset stays rank-ordered) and deep-merge each
        name's fragments in order.
        """
        if not config_names:
            return []
        scope_visibility = [
            AppConfigFragmentConditions.by_public_visibility(),
            AppConfigFragmentConditions.by_domain_visibility(str(scope.domain_id)),
            AppConfigFragmentConditions.by_user_visibility(str(scope.user_id)),
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
