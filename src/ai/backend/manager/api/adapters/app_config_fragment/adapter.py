"""App config fragment adapter bridging v2 DTOs and the fragment write/search Processors."""

from __future__ import annotations

from collections.abc import Sequence
from functools import lru_cache

from ai.backend.common.contexts.user import current_user
from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.data.app_config.types import AppConfigScopeType as AppConfigScopeTypeDTO
from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
    AdminSearchAppConfigFragmentInput,
    AppConfigFragmentFilter,
    AppConfigFragmentOrder,
    AppConfigFragmentScope,
    AppConfigFragmentUpsertItem,
    BulkPurgeAppConfigFragmentInput,
    MyAppConfigFragmentsByNamesInput,
    MyBulkPurgeAppConfigFragmentsByNamesInput,
    MyUpsertAppConfigFragmentsInput,
    ScopedAppConfigFragmentsByNamesInput,
    ScopedBulkPurgeAppConfigFragmentsByNamesInput,
    ScopedSearchAppConfigFragmentInput,
    ScopedUpsertAppConfigFragmentsInput,
)
from ai.backend.common.dto.manager.v2.app_config_fragment.response import (
    AppConfigFragmentBulkErrorInfo,
    AppConfigFragmentNode,
    BulkPurgeAppConfigFragmentPayload,
    BulkPurgeAppConfigFragmentsByNamesPayload,
    PurgeAppConfigFragmentPayload,
    SearchAppConfigFragmentPayload,
    UpsertAppConfigFragmentsPayload,
)
from ai.backend.common.dto.manager.v2.app_config_fragment.types import (
    AppConfigFragmentOrderField,
    AppConfigScopeTypeFilter,
)
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.exception import UnreachableError
from ai.backend.common.identifier.app_config import AppConfigScopeID
from ai.backend.common.identifier.app_config_fragment import AppConfigFragmentID
from ai.backend.manager.api.adapter_options.pagination.pagination import PaginationSpec
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.data.app_config_fragment.types import (
    AppConfigFragmentData,
)
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.models.app_config_fragment.conditions import AppConfigFragmentConditions
from ai.backend.manager.models.app_config_fragment.orders import AppConfigFragmentOrders
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.repositories.app_config_fragment.purgers import (
    AppConfigFragmentPurgerSpec,
)
from ai.backend.manager.repositories.app_config_fragment.types import (
    AppConfigFragmentSearchScope,
)
from ai.backend.manager.repositories.app_config_fragment.upserters import (
    AppConfigFragmentUpserterSpec,
)
from ai.backend.manager.repositories.base import (
    combine_conditions_or,
    negate_conditions,
)
from ai.backend.manager.services.app_config_fragment.actions.admin_search import (
    AdminSearchAppConfigFragmentAction,
)
from ai.backend.manager.services.app_config_fragment.actions.bulk_purge import (
    BulkPurgeAppConfigFragmentAction,
)
from ai.backend.manager.services.app_config_fragment.actions.bulk_purge_by_names import (
    BulkPurgeAppConfigFragmentsByNamesAction,
)
from ai.backend.manager.services.app_config_fragment.actions.bulk_upsert import (
    BulkUpsertAppConfigFragmentsAction,
)
from ai.backend.manager.services.app_config_fragment.actions.get import (
    GetAppConfigFragmentAction,
)
from ai.backend.manager.services.app_config_fragment.actions.purge import (
    PurgeAppConfigFragmentAction,
)
from ai.backend.manager.services.app_config_fragment.actions.scoped_search import (
    ScopedSearchAppConfigFragmentAction,
)


@lru_cache(maxsize=1)
def _get_app_config_fragment_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=AppConfigFragmentOrders.created_at(ascending=False),
        backward_order=AppConfigFragmentOrders.created_at(ascending=True),
        forward_condition_factory=AppConfigFragmentConditions.by_cursor_forward,
        backward_condition_factory=AppConfigFragmentConditions.by_cursor_backward,
        tiebreaker_order=AppConfigFragmentOrders.id(ascending=True),
    )


class AppConfigFragmentAdapter(BaseAdapter):
    """Adapter for raw app config fragment write and search operations."""

    # --- fragment writes and reads (RBAC-gated at the processor) ---

    async def scoped_upsert_app_config_fragments(
        self, input: ScopedUpsertAppConfigFragmentsInput
    ) -> UpsertAppConfigFragmentsPayload:
        """Upsert many fragments at the scope named in ``input`` (RBAC-authorized there)."""
        return await self._upsert(
            AppConfigFragmentSearchScope(
                scope_type=input.scope.scope_type, scope_id=input.scope.scope_id
            ),
            input.items,
        )

    async def my_upsert_app_config_fragments(
        self, input: MyUpsertAppConfigFragmentsInput
    ) -> UpsertAppConfigFragmentsPayload:
        """Upsert many fragments at the current user's own user scope.

        Calls ``current_user()`` internally — the caller does not pass a scope.
        """
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")
        scope = AppConfigFragmentSearchScope(
            scope_type=AppConfigScopeType.USER, scope_id=AppConfigScopeID(me.user_id)
        )
        return await self._upsert(scope, input.items)

    async def _upsert(
        self,
        scope: AppConfigFragmentSearchScope,
        items: Sequence[AppConfigFragmentUpsertItem],
    ) -> UpsertAppConfigFragmentsPayload:
        specs = [
            AppConfigFragmentUpserterSpec(
                config_name=item.config_name,
                scope_type=scope.scope_type,
                scope_id=scope.scope_id,
                config=item.config,
            )
            for item in items
        ]
        action_result = await self._processors.app_config_fragment.bulk_upsert.wait_for_complete(
            BulkUpsertAppConfigFragmentsAction(scope=scope, upserter_specs=specs)
        )
        return UpsertAppConfigFragmentsPayload(
            items=[self._fragment_to_node(fragment) for fragment in action_result.fragments],
        )

    async def get(self, fragment_id: AppConfigFragmentID) -> AppConfigFragmentNode:
        action_result = await self._processors.app_config_fragment.get.wait_for_complete(
            GetAppConfigFragmentAction(fragment_id=fragment_id)
        )
        return self._fragment_to_node(action_result.fragment)

    async def purge(self, fragment_id: AppConfigFragmentID) -> PurgeAppConfigFragmentPayload:
        purger_spec = AppConfigFragmentPurgerSpec(fragment_id=fragment_id)
        action_result = await self._processors.app_config_fragment.purge.wait_for_complete(
            PurgeAppConfigFragmentAction(purger_spec=purger_spec)
        )
        return PurgeAppConfigFragmentPayload(id=action_result.fragment.id)

    async def bulk_purge(
        self, input: BulkPurgeAppConfigFragmentInput
    ) -> BulkPurgeAppConfigFragmentPayload:
        purger_specs = [
            AppConfigFragmentPurgerSpec(fragment_id=fragment_id) for fragment_id in input.ids
        ]
        action_result = await self._processors.app_config_fragment.bulk_purge.wait_for_complete(
            BulkPurgeAppConfigFragmentAction(purger_specs=purger_specs)
        )
        return BulkPurgeAppConfigFragmentPayload(
            items=[fragment.id for fragment in action_result.succeeded],
            failed=[
                AppConfigFragmentBulkErrorInfo(id=error.id, message=error.message)
                for error in action_result.failed
            ],
        )

    async def scoped_bulk_purge_app_config_fragments_by_names(
        self, input: ScopedBulkPurgeAppConfigFragmentsByNamesInput
    ) -> BulkPurgeAppConfigFragmentsByNamesPayload:
        """Purge the fragments written at the scope named in ``input`` for ``config_names``.

        RBAC-authorized at that scope, so a caller purges only a scope they may write.
        """
        scope = AppConfigFragmentSearchScope(
            scope_type=input.scope.scope_type, scope_id=input.scope.scope_id
        )
        action_result = (
            await self._processors.app_config_fragment.bulk_purge_by_names.wait_for_complete(
                BulkPurgeAppConfigFragmentsByNamesAction(
                    scope=scope, config_names=input.config_names
                )
            )
        )
        return BulkPurgeAppConfigFragmentsByNamesPayload(
            items=[fragment.id for fragment in action_result.fragments]
        )

    async def my_bulk_purge_app_config_fragments_by_names(
        self, input: MyBulkPurgeAppConfigFragmentsByNamesInput
    ) -> BulkPurgeAppConfigFragmentsByNamesPayload:
        """Purge the current user's own ``user``-scope fragments for ``config_names``.

        Calls ``current_user()`` internally — the caller does not pass a scope.
        """
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")
        scope = AppConfigFragmentSearchScope(
            scope_type=AppConfigScopeType.USER, scope_id=AppConfigScopeID(me.user_id)
        )
        action_result = (
            await self._processors.app_config_fragment.bulk_purge_by_names.wait_for_complete(
                BulkPurgeAppConfigFragmentsByNamesAction(
                    scope=scope, config_names=input.config_names
                )
            )
        )
        return BulkPurgeAppConfigFragmentsByNamesPayload(
            items=[fragment.id for fragment in action_result.fragments]
        )

    async def batch_load_by_ids(
        self, fragment_ids: Sequence[AppConfigFragmentID]
    ) -> list[AppConfigFragmentNode | None]:
        """Batch load fragments by id for the GraphQL DataLoader, scoped to the current user.

        A scoped search at the caller's own ``user`` scope, narrowed to ``fragment_ids``.
        Returns nodes in the order of ``fragment_ids``, with ``None`` for ids not visible in
        that scope. Calls ``current_user()`` internally — the caller does not pass a scope.
        """
        if not fragment_ids:
            return []
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")
        querier = self._build_querier(
            conditions=[AppConfigFragmentConditions.by_ids(list(fragment_ids))],
            orders=[],
            pagination_spec=_get_app_config_fragment_pagination_spec(),
            limit=len(fragment_ids),
        )
        scope = AppConfigFragmentSearchScope(
            scope_type=AppConfigScopeType.USER,
            scope_id=AppConfigScopeID(me.user_id),
        )
        action_result = await self._processors.app_config_fragment.scoped_search.wait_for_complete(
            ScopedSearchAppConfigFragmentAction(scope=scope, querier=querier)
        )
        node_map = {node.id: node for node in map(self._fragment_to_node, action_result.data)}
        return [node_map.get(fragment_id) for fragment_id in fragment_ids]

    # --- read fragments by config name (one scope, RBAC-authorized) ---

    async def scoped_app_config_fragments_by_names(
        self, input: ScopedAppConfigFragmentsByNamesInput
    ) -> list[AppConfigFragmentNode | None]:
        """The fragments written at one scope for the given config names.

        RBAC-authorized at that scope, so a caller reads only a scope they may read. Meant for
        fetching the current fragment values before editing them.
        """
        return await self._fragments_by_names(
            AppConfigFragmentSearchScope(
                scope_type=input.scope.scope_type, scope_id=input.scope.scope_id
            ),
            input.config_names,
        )

    async def my_app_config_fragments_by_names(
        self, input: MyAppConfigFragmentsByNamesInput
    ) -> list[AppConfigFragmentNode | None]:
        """The current user's own ``user``-scope fragments for the given ``config_names``.

        Calls ``current_user()`` internally — the caller does not pass a scope.
        """
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")
        return await self._fragments_by_names(
            AppConfigFragmentSearchScope(
                scope_type=AppConfigScopeType.USER, scope_id=AppConfigScopeID(me.user_id)
            ),
            input.config_names,
        )

    async def _fragments_by_names(
        self, scope: AppConfigFragmentSearchScope, config_names: list[str]
    ) -> list[AppConfigFragmentNode | None]:
        if not config_names:
            return []
        # A scope holds at most one fragment per config name, so the result is bounded by the
        # number of names requested.
        querier = self._build_querier(
            conditions=[AppConfigFragmentConditions.by_config_names(config_names)],
            orders=[],
            pagination_spec=_get_app_config_fragment_pagination_spec(),
            limit=len(config_names),
        )
        action_result = await self._processors.app_config_fragment.scoped_search.wait_for_complete(
            ScopedSearchAppConfigFragmentAction(scope=scope, querier=querier)
        )
        # Answer at the position each name was asked for, so a name with no fragment at this
        # scope holds its place as a null.
        fragment_map = {fragment.config_name: fragment for fragment in action_result.data}
        return [
            self._fragment_to_node(fragment_map[config_name])
            if config_name in fragment_map
            else None
            for config_name in config_names
        ]

    # --- admin fragment search ---

    async def admin_search(
        self, input: AdminSearchAppConfigFragmentInput
    ) -> SearchAppConfigFragmentPayload:
        conditions = self._convert_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else []
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_get_app_config_fragment_pagination_spec(),
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        action_result = await self._processors.app_config_fragment.admin_search.wait_for_complete(
            AdminSearchAppConfigFragmentAction(querier=querier)
        )
        return SearchAppConfigFragmentPayload(
            items=[self._fragment_to_node(item) for item in action_result.items],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    # --- scoped fragment search (one scope, RBAC-authorized) ---

    async def scoped_search(
        self, input: ScopedSearchAppConfigFragmentInput
    ) -> SearchAppConfigFragmentPayload:
        conditions = self._convert_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else []
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_get_app_config_fragment_pagination_spec(),
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        scope = self._scope_to_search_scope(input.scope)
        action_result = await self._processors.app_config_fragment.scoped_search.wait_for_complete(
            ScopedSearchAppConfigFragmentAction(scope=scope, querier=querier)
        )
        return SearchAppConfigFragmentPayload(
            items=[self._fragment_to_node(item) for item in action_result.data],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    @staticmethod
    def _scope_to_search_scope(scope: AppConfigFragmentScope) -> AppConfigFragmentSearchScope:
        """Reduce the scope item lists to the single scope the scope action takes.

        ``ScopedSearchAppConfigFragmentAction`` is a ``BaseScopeAction``, so it authorizes and
        queries exactly one scope; reject a multi-scope request instead of silently dropping
        the rest.
        """
        selected = [
            AppConfigFragmentSearchScope(
                scope_type=AppConfigScopeType.DOMAIN,
                scope_id=AppConfigScopeID(item.value),
            )
            for item in scope.domain or []
        ]
        selected += [
            AppConfigFragmentSearchScope(
                scope_type=AppConfigScopeType.USER,
                scope_id=AppConfigScopeID(item.value),
            )
            for item in scope.user or []
        ]
        if scope.public:
            selected.append(
                AppConfigFragmentSearchScope(scope_type=AppConfigScopeType.PUBLIC, scope_id=None)
            )
        # TODO(BA-7003): temporary single-scope restriction. The underlying
        # ScopedSearchAppConfigFragmentAction is a single-scope BaseScopeAction, so a request
        # carrying more than one scope item is rejected here rather than silently dropping the
        # rest. Multi-scope scoped search will be implemented in BA-7003.
        if len(selected) > 1:
            raise InvalidAPIParameters(
                "App config fragment scoped search accepts at most one scope item"
            )
        return selected[0]

    # --- converters ---

    @staticmethod
    def _fragment_to_node(data: AppConfigFragmentData) -> AppConfigFragmentNode:
        return AppConfigFragmentNode(
            id=data.id,
            config_name=data.config_name,
            scope_type=AppConfigScopeTypeDTO(data.scope_type.value),
            scope_id=data.scope_id,
            config=data.config,
            created_at=data.created_at,
            updated_at=data.updated_at,
        )

    def _convert_filter(self, filter_: AppConfigFragmentFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if filter_.config_name:
            condition = self.convert_string_filter(
                filter_.config_name,
                contains_factory=AppConfigFragmentConditions.by_config_name_contains,
                equals_factory=AppConfigFragmentConditions.by_config_name_equals,
                starts_with_factory=AppConfigFragmentConditions.by_config_name_starts_with,
                ends_with_factory=AppConfigFragmentConditions.by_config_name_ends_with,
                in_factory=AppConfigFragmentConditions.by_config_name_in,
            )
            if condition:
                conditions.append(condition)
        if filter_.scope_type:
            conditions.extend(self._convert_scope_type_filter(filter_.scope_type))
        if filter_.created_at:
            condition = filter_.created_at.build_query_condition(
                before_factory=AppConfigFragmentConditions.by_created_at_before,
                after_factory=AppConfigFragmentConditions.by_created_at_after,
                equals_factory=AppConfigFragmentConditions.by_created_at_equals,
            )
            if condition:
                conditions.append(condition)
        if filter_.updated_at:
            condition = filter_.updated_at.build_query_condition(
                before_factory=AppConfigFragmentConditions.by_updated_at_before,
                after_factory=AppConfigFragmentConditions.by_updated_at_after,
                equals_factory=AppConfigFragmentConditions.by_updated_at_equals,
            )
            if condition:
                conditions.append(condition)
        if filter_.AND:
            for sub_filter in filter_.AND:
                conditions.extend(self._convert_filter(sub_filter))
        if filter_.OR:
            or_conditions: list[QueryCondition] = []
            for sub_filter in filter_.OR:
                or_conditions.extend(self._convert_filter(sub_filter))
            if or_conditions:
                conditions.append(combine_conditions_or(or_conditions))
        if filter_.NOT:
            not_conditions: list[QueryCondition] = []
            for sub_filter in filter_.NOT:
                not_conditions.extend(self._convert_filter(sub_filter))
            if not_conditions:
                conditions.append(negate_conditions(not_conditions))
        return conditions

    @staticmethod
    def _convert_scope_type_filter(filter_: AppConfigScopeTypeFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if filter_.equals is not None:
            conditions.append(
                AppConfigFragmentConditions.by_scope_type_equals(
                    AppConfigScopeType(filter_.equals.value)
                )
            )
        if filter_.in_ is not None:
            conditions.append(
                AppConfigFragmentConditions.by_scope_type_in([
                    AppConfigScopeType(value.value) for value in filter_.in_
                ])
            )
        if filter_.not_equals is not None:
            conditions.append(
                AppConfigFragmentConditions.by_scope_type_not_equals(
                    AppConfigScopeType(filter_.not_equals.value)
                )
            )
        if filter_.not_in is not None:
            conditions.append(
                AppConfigFragmentConditions.by_scope_type_not_in([
                    AppConfigScopeType(value.value) for value in filter_.not_in
                ])
            )
        return conditions

    def _convert_orders(self, orders: list[AppConfigFragmentOrder]) -> list[QueryOrder]:
        result: list[QueryOrder] = []
        for order in orders:
            ascending = order.direction == OrderDirection.ASC
            match order.field:
                case AppConfigFragmentOrderField.CONFIG_NAME:
                    result.append(AppConfigFragmentOrders.config_name(ascending))
                case AppConfigFragmentOrderField.SCOPE_TYPE:
                    result.append(AppConfigFragmentOrders.scope_type(ascending))
                case AppConfigFragmentOrderField.CREATED_AT:
                    result.append(AppConfigFragmentOrders.created_at(ascending))
                case AppConfigFragmentOrderField.UPDATED_AT:
                    result.append(AppConfigFragmentOrders.updated_at(ascending))
        return result
