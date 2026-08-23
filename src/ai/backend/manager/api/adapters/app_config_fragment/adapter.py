"""App config fragment adapter bridging v2 DTOs and the fragment write/search Processors."""

from __future__ import annotations

from collections.abc import Sequence
from functools import lru_cache

from ai.backend.common.contexts.user import current_user
from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.data.entity.app_config import AppConfigScopeID
from ai.backend.common.data.entity.app_config_fragment import AppConfigFragmentID
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
    AdminSearchAppConfigFragmentInput,
    AppConfigFragmentFilter,
    AppConfigFragmentOrder,
    AppConfigFragmentScope,
    AppConfigFragmentUpsertItem,
    AppConfigScopeRef,
    BulkPurgeAppConfigFragmentInput,
    MyAppConfigFragmentsByNamesInput,
    MyUpsertAppConfigFragmentsInput,
    ScopedAppConfigFragmentsByNamesInput,
    ScopedSearchAppConfigFragmentInput,
    ScopedUpsertAppConfigFragmentsInput,
)
from ai.backend.common.dto.manager.v2.app_config_fragment.response import (
    AppConfigFragmentBulkErrorInfo,
    AppConfigFragmentNode,
    BulkPurgeAppConfigFragmentPayload,
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
from ai.backend.manager.api.adapter_options.pagination.pagination import PaginationSpec
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.data.app_config.types import (
    AppConfigFragmentData,
)
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.models.app_config_fragment.conditions import AppConfigFragmentConditions
from ai.backend.manager.models.app_config_fragment.orders import AppConfigFragmentOrders
from ai.backend.manager.models.app_config_fragment.purgers import AppConfigFragmentPurger
from ai.backend.manager.models.app_config_fragment.queriers import (
    AppConfigFragmentQuerier,
)
from ai.backend.manager.models.app_config_fragment.searchers import (
    AppConfigFragmentSearcher,
)
from ai.backend.manager.models.app_config_fragment.upserters import (
    AppConfigFragmentUpserter,
    PublicAppConfigFragmentUpserter,
)
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.condition_utils import combine_conditions_or, negate_conditions
from ai.backend.manager.services.app_config.actions.fragment.admin_search import (
    AdminSearchAppConfigFragmentAction,
)
from ai.backend.manager.services.app_config.actions.fragment.bulk_purge import (
    BulkPurgeAppConfigFragmentAction,
)
from ai.backend.manager.services.app_config.actions.fragment.bulk_upsert import (
    BulkUpsertAppConfigFragmentsAction,
)
from ai.backend.manager.services.app_config.actions.fragment.get import (
    GetAppConfigFragmentAction,
)
from ai.backend.manager.services.app_config.actions.fragment.global_bulk_upsert import (
    GlobalBulkUpsertAppConfigFragmentsAction,
)
from ai.backend.manager.services.app_config.actions.fragment.purge import (
    PurgeAppConfigFragmentAction,
)
from ai.backend.manager.services.app_config.actions.fragment.scoped_search import (
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
        return await self._upsert(self._ref_owner(input.scope), input.items)

    async def my_upsert_app_config_fragments(
        self, input: MyUpsertAppConfigFragmentsInput
    ) -> UpsertAppConfigFragmentsPayload:
        """Upsert many fragments at the current user's own user scope.

        Calls ``current_user()`` internally — the caller does not pass a scope.
        """
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")
        return await self._upsert(UserID(me.user_id), input.items)

    async def _upsert(
        self,
        owner: EntityIdentifier | None,
        items: Sequence[AppConfigFragmentUpsertItem],
    ) -> UpsertAppConfigFragmentsPayload:
        """Route by who owns the fragments: a public write answers to no scope, so it runs
        behind the SUPERADMIN gate instead."""
        if owner is None:
            written = await self._processors.app_config.fragment_global_bulk_upsert.run(
                GlobalBulkUpsertAppConfigFragmentsAction(
                    upserters=[
                        PublicAppConfigFragmentUpserter(
                            config_name=item.config_name, config=item.config
                        )
                        for item in items
                    ]
                )
            )
        else:
            written = await self._processors.app_config.fragment_bulk_upsert.run(
                BulkUpsertAppConfigFragmentsAction(
                    owner=owner,
                    upserters=[
                        AppConfigFragmentUpserter(
                            config_name=item.config_name, owner=owner, config=item.config
                        )
                        for item in items
                    ],
                )
            )
        return UpsertAppConfigFragmentsPayload(
            items=[self._fragment_to_node(fragment) for fragment in written.items],
            failed=[],
        )

    async def get(self, fragment_id: AppConfigFragmentID) -> AppConfigFragmentNode:
        action_result = await self._processors.app_config.fragment_get.run(
            GetAppConfigFragmentAction(querier=AppConfigFragmentQuerier(fragment_id=fragment_id))
        )
        return self._fragment_to_node(action_result.data)

    async def purge(self, fragment_id: AppConfigFragmentID) -> PurgeAppConfigFragmentPayload:
        action_result = await self._processors.app_config.fragment_purge.run(
            PurgeAppConfigFragmentAction(purger=AppConfigFragmentPurger(fragment_id=fragment_id))
        )
        return PurgeAppConfigFragmentPayload(id=action_result.data.id)

    async def bulk_purge(
        self, input: BulkPurgeAppConfigFragmentInput
    ) -> BulkPurgeAppConfigFragmentPayload:
        action_result = await self._processors.app_config.fragment_bulk_purge.run(
            BulkPurgeAppConfigFragmentAction(
                purgers=[
                    AppConfigFragmentPurger(fragment_id=fragment_id) for fragment_id in input.ids
                ]
            )
        )
        return BulkPurgeAppConfigFragmentPayload(
            items=[fragment.id for fragment in action_result.successes.values()],
            failed=[
                AppConfigFragmentBulkErrorInfo(
                    id=AppConfigFragmentID(entity_id), message=str(error)
                )
                for entity_id, error in action_result.errors.items()
            ],
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
        searcher = self._build_searcher(
            AppConfigFragmentSearcher,
            conditions=[AppConfigFragmentConditions.by_ids(list(fragment_ids))],
            orders=[],
            pagination_spec=_get_app_config_fragment_pagination_spec(),
            limit=len(fragment_ids),
        )
        action_result = await self._processors.app_config.fragment_scoped_search.run(
            ScopedSearchAppConfigFragmentAction(owner=UserID(me.user_id), searcher=searcher)
        )
        node_map = {node.id: node for node in map(self._fragment_to_node, action_result.items)}
        return [node_map.get(fragment_id) for fragment_id in fragment_ids]

    # --- read fragments by config name (one scope, RBAC-authorized) ---

    async def scoped_app_config_fragments_by_names(
        self, input: ScopedAppConfigFragmentsByNamesInput
    ) -> list[AppConfigFragmentNode | None]:
        """The fragments written at one scope for the given config names.

        Meant for fetching the current fragment values before editing them.
        """
        return await self._fragments_by_names(self._ref_owner(input.scope), input.config_names)

    async def my_app_config_fragments_by_names(
        self, input: MyAppConfigFragmentsByNamesInput
    ) -> list[AppConfigFragmentNode | None]:
        """The current user's own ``user``-scope fragments for the given ``config_names``.

        Calls ``current_user()`` internally — the caller does not pass a scope.
        """
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")
        return await self._fragments_by_names(UserID(me.user_id), input.config_names)

    async def _fragments_by_names(
        self, owner: EntityIdentifier | None, config_names: list[str]
    ) -> list[AppConfigFragmentNode | None]:
        if not config_names:
            return []
        # A scope holds at most one fragment per config name, so the result is bounded by the
        # number of names requested.
        searcher = self._build_searcher(
            AppConfigFragmentSearcher,
            conditions=[AppConfigFragmentConditions.by_config_names(config_names)],
            orders=[],
            pagination_spec=_get_app_config_fragment_pagination_spec(),
            limit=len(config_names),
        )
        action_result = await self._processors.app_config.fragment_scoped_search.run(
            ScopedSearchAppConfigFragmentAction(owner=owner, searcher=searcher)
        )
        # Answer at the position each name was asked for, so a name with no fragment at this
        # scope holds its place as a null.
        fragment_map = {fragment.config_name: fragment for fragment in action_result.items}
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
        searcher = self._build_searcher(
            AppConfigFragmentSearcher,
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
        action_result = await self._processors.app_config.fragment_admin_search.run(
            AdminSearchAppConfigFragmentAction(searcher=searcher)
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
        searcher = self._build_searcher(
            AppConfigFragmentSearcher,
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
        action_result = await self._processors.app_config.fragment_scoped_search.run(
            ScopedSearchAppConfigFragmentAction(
                owner=self._scope_owner(input.scope), searcher=searcher
            )
        )
        return SearchAppConfigFragmentPayload(
            items=[self._fragment_to_node(item) for item in action_result.items],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    @staticmethod
    def _ref_owner(ref: AppConfigScopeRef) -> EntityIdentifier | None:
        """The owner a scope reference names; ``public`` names none."""
        return ref.scope_type.to_owner(ref.scope_id)

    @staticmethod
    def _scope_owner(scope: AppConfigFragmentScope) -> EntityIdentifier | None:
        """Reduce the scope item lists to the one owner an action takes; ``None`` is ``public``.

        Both the write and the scoped read act at exactly one scope, so a request carrying
        more than one item is rejected rather than having the rest silently dropped.
        """
        selected: list[EntityIdentifier | None] = [
            DomainID(item.value) for item in scope.domain or []
        ]
        selected += [UserID(item.value) for item in scope.user or []]
        if scope.public:
            selected.append(None)
        if len(selected) != 1:
            raise InvalidAPIParameters("An app config fragment scope names exactly one owner")
        return selected[0]

    # --- converters ---

    @staticmethod
    def _fragment_to_node(data: AppConfigFragmentData) -> AppConfigFragmentNode:
        return AppConfigFragmentNode(
            id=data.id,
            config_name=data.config_name,
            scope_type=AppConfigScopeType.of_owner(data.scope_id),
            scope_id=AppConfigScopeID(data.scope_id) if data.scope_id is not None else None,
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
