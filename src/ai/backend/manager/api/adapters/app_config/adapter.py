"""App config adapter bridging v2 DTOs and the fragment / merged-config Processors."""

from __future__ import annotations

from functools import lru_cache

from ai.backend.common.contexts.user import current_user
from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.data.app_config.types import AppConfigScopeType as AppConfigScopeTypeDTO
from ai.backend.common.dto.manager.v2.app_config.request import ResolveAppConfigInput
from ai.backend.common.dto.manager.v2.app_config.response import (
    AppConfigNode,
    ResolveAppConfigPayload,
)
from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
    AppConfigFragmentFilter,
    AppConfigFragmentOrder,
    CreateAppConfigFragmentInput,
    PurgeAppConfigFragmentInput,
    ScopedSearchAppConfigFragmentInput,
    SearchAppConfigFragmentInput,
    UpdateAppConfigFragmentInput,
)
from ai.backend.common.dto.manager.v2.app_config_fragment.response import (
    AppConfigFragmentNode,
    CreateAppConfigFragmentPayload,
    PurgeAppConfigFragmentPayload,
    SearchAppConfigFragmentPayload,
    UpdateAppConfigFragmentPayload,
)
from ai.backend.common.dto.manager.v2.app_config_fragment.types import (
    AppConfigFragmentOrderField,
    AppConfigScopeTypeFilter,
)
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.identifier.app_config_fragment import AppConfigFragmentID
from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.user import UserID
from ai.backend.manager.actions.action.types import SearchableActionTarget
from ai.backend.manager.api.adapter_options.pagination.pagination import PaginationSpec
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.data.app_config.types import AppConfigData
from ai.backend.manager.data.app_config_fragment.types import (
    AppConfigFragmentData,
)
from ai.backend.manager.errors.app_config import AppConfigResolveNotAllowed
from ai.backend.manager.models.app_config_fragment.conditions import AppConfigFragmentConditions
from ai.backend.manager.models.app_config_fragment.orders import AppConfigFragmentOrders
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.repositories.app_config_fragment.creators import (
    AppConfigFragmentCreatorSpec,
)
from ai.backend.manager.repositories.app_config_fragment.types import AppConfigScopeArguments
from ai.backend.manager.repositories.app_config_fragment.updaters import (
    AppConfigFragmentUpdaterSpec,
)
from ai.backend.manager.repositories.base import (
    Purger,
    Updater,
)
from ai.backend.manager.services.app_config.actions.resolve import ResolveAppConfigAction
from ai.backend.manager.services.app_config_fragment.actions.admin_search import (
    AdminSearchAppConfigFragmentAction,
)
from ai.backend.manager.services.app_config_fragment.actions.create import (
    CreateAppConfigFragmentAction,
)
from ai.backend.manager.services.app_config_fragment.actions.get import (
    GetAppConfigFragmentAction,
)
from ai.backend.manager.services.app_config_fragment.actions.purge import (
    PurgeAppConfigFragmentAction,
)
from ai.backend.manager.services.app_config_fragment.actions.scoped_search import (
    DomainAppConfigFragmentTarget,
    ScopedSearchAppConfigFragmentAction,
    UserAppConfigFragmentTarget,
)
from ai.backend.manager.services.app_config_fragment.actions.update import (
    UpdateAppConfigFragmentAction,
)
from ai.backend.manager.types import OptionalState


@lru_cache(maxsize=1)
def _get_app_config_fragment_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=AppConfigFragmentOrders.created_at(ascending=False),
        backward_order=AppConfigFragmentOrders.created_at(ascending=True),
        forward_condition_factory=AppConfigFragmentConditions.by_cursor_forward,
        backward_condition_factory=AppConfigFragmentConditions.by_cursor_backward,
        tiebreaker_order=AppConfigFragmentOrders.id(ascending=True),
    )


class AppConfigAdapter(BaseAdapter):
    """Adapter for app config fragment (write/search) and merged AppConfig (read) operations."""

    # --- admin fragment CRUD ---

    async def admin_create(
        self, input: CreateAppConfigFragmentInput
    ) -> CreateAppConfigFragmentPayload:
        spec = AppConfigFragmentCreatorSpec(
            config_name=input.config_name,
            scope_type=AppConfigScopeType(input.scope_type.value),
            scope_id=input.scope_id,
            config=input.config,
        )
        action_result = await self._processors.app_config_fragment.create.wait_for_complete(
            CreateAppConfigFragmentAction(creator_spec=spec)
        )
        return CreateAppConfigFragmentPayload(
            app_config_fragment=self._fragment_to_node(action_result.fragment),
        )

    async def admin_get(self, fragment_id: AppConfigFragmentID) -> AppConfigFragmentNode:
        action_result = await self._processors.app_config_fragment.get.wait_for_complete(
            GetAppConfigFragmentAction(fragment_id=fragment_id)
        )
        return self._fragment_to_node(action_result.fragment)

    async def admin_update(
        self, fragment_id: AppConfigFragmentID, input: UpdateAppConfigFragmentInput
    ) -> UpdateAppConfigFragmentPayload:
        updater = Updater(
            spec=AppConfigFragmentUpdaterSpec(config=OptionalState.update(input.config)),
            pk_value=fragment_id,
        )
        # No allow-list gate: a fragment row exists only while its entry does (FK with
        # cascade), so an existing fragment is always writable at its own scope.
        action_result = await self._processors.app_config_fragment.update.wait_for_complete(
            UpdateAppConfigFragmentAction(updater=updater)
        )
        return UpdateAppConfigFragmentPayload(
            app_config_fragment=self._fragment_to_node(action_result.fragment),
        )

    async def admin_purge(
        self, input: PurgeAppConfigFragmentInput
    ) -> PurgeAppConfigFragmentPayload:
        fragment_id = AppConfigFragmentID(input.id)
        purger = Purger(row_class=AppConfigFragmentRow, pk_value=fragment_id)
        # No allow-list gate — see ``admin_update``.
        action_result = await self._processors.app_config_fragment.purge.wait_for_complete(
            PurgeAppConfigFragmentAction(purger=purger)
        )
        return PurgeAppConfigFragmentPayload(id=action_result.fragment.id)

    async def admin_search(
        self, input: SearchAppConfigFragmentInput
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
            items=[self._fragment_to_node(item) for item in action_result.data],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    # --- scoped fragment search (principal-visibility) ---

    async def scoped_search(
        self, input: ScopedSearchAppConfigFragmentInput
    ) -> SearchAppConfigFragmentPayload:
        orders = self._convert_orders(input.order) if input.order else []
        querier = self._build_querier(
            conditions=[],
            orders=orders,
            pagination_spec=_get_app_config_fragment_pagination_spec(),
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        targets: list[SearchableActionTarget] = [
            DomainAppConfigFragmentTarget(domain_id=DomainID(domain_id))
            for domain_id in (input.scope.domain or [])
        ]
        targets += [
            UserAppConfigFragmentTarget(user_id=UserID(user_id))
            for user_id in (input.scope.user or [])
        ]
        action_result = await self._processors.app_config_fragment.scoped_search.wait_for_complete(
            ScopedSearchAppConfigFragmentAction(items=targets, querier=querier)
        )
        return SearchAppConfigFragmentPayload(
            items=[self._fragment_to_node(item) for item in action_result.data],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    # --- merged AppConfig read ---

    async def resolve(self, input: ResolveAppConfigInput) -> ResolveAppConfigPayload:
        self._ensure_caller(input.user_id)
        action_result = await self._processors.app_config.resolve_app_config.wait_for_complete(
            ResolveAppConfigAction(
                config_name=input.config_name,
                scope=AppConfigScopeArguments(
                    domain_id=DomainID(input.domain_id), user_id=UserID(input.user_id)
                ),
            )
        )
        return ResolveAppConfigPayload(
            app_config=self._app_config_to_node(action_result.app_config)
        )

    async def resolve_public(self, config_name: str) -> ResolveAppConfigPayload:
        # Anonymous, pre-login read: no principal (``scope=None``), so only public fragments
        # contribute. Reuses the standard resolve action rather than a separate public one.
        action_result = await self._processors.app_config.resolve_app_config.wait_for_complete(
            ResolveAppConfigAction(config_name=config_name)
        )
        return ResolveAppConfigPayload(
            app_config=self._app_config_to_node(action_result.app_config)
        )

    # --- guards / converters ---

    @staticmethod
    def _ensure_caller(user_id: object) -> None:
        """Reject a request whose ``user_id`` is not the authenticated caller.

        Temporary stand-in for an RBAC validator: the processors carry no validator, so the
        only principal check happens here.
        """
        me = current_user()
        if me is None or user_id != me.user_id:
            raise AppConfigResolveNotAllowed(
                "App config resolve is only allowed for the authenticated caller."
            )

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

    @classmethod
    def _app_config_to_node(cls, data: AppConfigData) -> AppConfigNode:
        return AppConfigNode(
            config_name=data.config_name,
            merged_config=data.merged_config,
            fragments=[cls._fragment_to_node(fragment) for fragment in data.fragments],
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
