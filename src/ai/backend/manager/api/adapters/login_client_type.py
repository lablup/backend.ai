"""Login client type adapter bridging DTOs and Processors."""

from __future__ import annotations

from uuid import UUID

from ai.backend.common.api_handlers import Sentinel
from ai.backend.common.dto.manager.v2.login_client_type.request import (
    CreateLoginClientTypeInput,
    LoginClientTypeFilter,
    LoginClientTypeOrder,
    SearchLoginClientTypesInput,
    UpdateLoginClientTypeInput,
)
from ai.backend.common.dto.manager.v2.login_client_type.response import (
    CreateLoginClientTypePayload,
    DeleteLoginClientTypePayload,
    LoginClientTypeNode,
    SearchLoginClientTypesPayload,
    UpdateLoginClientTypePayload,
)
from ai.backend.common.dto.manager.v2.login_client_type.types import (
    LoginClientTypeOrderField,
    OrderDirection,
)
from ai.backend.manager.data.login_client_type.types import LoginClientTypeData
from ai.backend.manager.models.login_client_type.conditions import LoginClientTypeConditions
from ai.backend.manager.models.login_client_type.orders import LoginClientTypeOrders
from ai.backend.manager.models.login_client_type.row import LoginClientTypeRow
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    OffsetPagination,
    QueryCondition,
    QueryOrder,
)
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.login_client_type.creators import (
    LoginClientTypeCreatorSpec,
)
from ai.backend.manager.repositories.login_client_type.updaters import (
    LoginClientTypeUpdaterSpec,
)
from ai.backend.manager.services.login_client_type.actions.create import (
    CreateLoginClientTypeAction,
)
from ai.backend.manager.services.login_client_type.actions.delete import (
    DeleteLoginClientTypeAction,
)
from ai.backend.manager.services.login_client_type.actions.get import (
    GetLoginClientTypeAction,
)
from ai.backend.manager.services.login_client_type.actions.search import (
    SearchLoginClientTypesAction,
)
from ai.backend.manager.services.login_client_type.actions.update import (
    UpdateLoginClientTypeAction,
)
from ai.backend.manager.types import OptionalState, TriState

from .base import BaseAdapter

DEFAULT_PAGINATION_LIMIT = 50


class LoginClientTypeAdapter(BaseAdapter):
    """Adapter for login client type domain operations."""

    # --- Static helpers (grouped at top) ---

    @staticmethod
    def _data_to_node(data: LoginClientTypeData) -> LoginClientTypeNode:
        return LoginClientTypeNode(
            id=data.id,
            name=data.name,
            description=data.description,
            created_at=data.created_at,
            modified_at=data.modified_at,
        )

    @staticmethod
    def _convert_orders(orders: list[LoginClientTypeOrder]) -> list[QueryOrder]:
        result: list[QueryOrder] = []
        for order in orders:
            ascending = order.direction == OrderDirection.ASC
            match order.field:
                case LoginClientTypeOrderField.NAME:
                    result.append(LoginClientTypeOrders.name(ascending))
                case LoginClientTypeOrderField.CREATED_AT:
                    result.append(LoginClientTypeOrders.created_at(ascending))
                case LoginClientTypeOrderField.MODIFIED_AT:
                    result.append(LoginClientTypeOrders.modified_at(ascending))
        return result

    # --- Non-admin methods ---

    async def get(self, type_id: UUID) -> LoginClientTypeNode:
        action_result = await self._processors.login_client_type.get.wait_for_complete(
            GetLoginClientTypeAction(id=type_id)
        )
        return self._data_to_node(action_result.login_client_type)

    async def search(self, input: SearchLoginClientTypesInput) -> SearchLoginClientTypesPayload:
        """Search login client types with filter/order/pagination."""
        querier = self._build_search_querier(input)

        action_result = await self._processors.login_client_type.search.wait_for_complete(
            SearchLoginClientTypesAction(querier=querier)
        )

        return SearchLoginClientTypesPayload(
            items=[self._data_to_node(item) for item in action_result.items],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    # --- Admin methods ---

    async def admin_create(self, input: CreateLoginClientTypeInput) -> CreateLoginClientTypePayload:
        creator = Creator[LoginClientTypeRow](
            spec=LoginClientTypeCreatorSpec(
                name=input.name,
                description=input.description,
            ),
        )
        action_result = await self._processors.login_client_type_admin.create.wait_for_complete(
            CreateLoginClientTypeAction(creator=creator)
        )
        return CreateLoginClientTypePayload(
            login_client_type=self._data_to_node(action_result.login_client_type),
        )

    async def admin_update(
        self, type_id: UUID, input: UpdateLoginClientTypeInput
    ) -> UpdateLoginClientTypePayload:
        updater = Updater[LoginClientTypeRow](
            spec=LoginClientTypeUpdaterSpec(
                name=(
                    OptionalState.update(input.name)
                    if input.name is not None
                    else OptionalState.nop()
                ),
                description=(
                    TriState.nop()
                    if isinstance(input.description, Sentinel)
                    else TriState.nullify()
                    if input.description is None
                    else TriState.update(input.description)
                ),
            ),
            pk_value=type_id,
        )
        action_result = await self._processors.login_client_type_admin.update.wait_for_complete(
            UpdateLoginClientTypeAction(updater=updater)
        )
        return UpdateLoginClientTypePayload(
            login_client_type=self._data_to_node(action_result.login_client_type),
        )

    async def admin_delete(self, type_id: UUID) -> DeleteLoginClientTypePayload:
        action_result = await self._processors.login_client_type_admin.delete.wait_for_complete(
            DeleteLoginClientTypeAction(id=type_id)
        )
        return DeleteLoginClientTypePayload(id=action_result.login_client_type.id)

    # --- Private helpers ---

    def _build_search_querier(self, input: SearchLoginClientTypesInput) -> BatchQuerier:
        conditions = self._convert_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else []
        pagination = OffsetPagination(
            limit=input.limit if input.limit is not None else DEFAULT_PAGINATION_LIMIT,
            offset=input.offset if input.offset is not None else 0,
        )
        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def _convert_filter(self, filter: LoginClientTypeFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []

        if filter.name is not None:
            condition = self.convert_string_filter(
                filter.name,
                contains_factory=LoginClientTypeConditions.by_name_contains,
                equals_factory=LoginClientTypeConditions.by_name_equals,
                starts_with_factory=LoginClientTypeConditions.by_name_starts_with,
                ends_with_factory=LoginClientTypeConditions.by_name_ends_with,
                in_factory=LoginClientTypeConditions.by_name_in,
            )
            if condition is not None:
                conditions.append(condition)

        if filter.description is not None:
            condition = self.convert_string_filter(
                filter.description,
                contains_factory=LoginClientTypeConditions.by_description_contains,
                equals_factory=LoginClientTypeConditions.by_description_equals,
                starts_with_factory=LoginClientTypeConditions.by_description_starts_with,
                ends_with_factory=LoginClientTypeConditions.by_description_ends_with,
                in_factory=LoginClientTypeConditions.by_description_in,
            )
            if condition is not None:
                conditions.append(condition)

        if filter.created_at is not None:
            condition = filter.created_at.build_query_condition(
                before_factory=LoginClientTypeConditions.by_created_at_before,
                after_factory=LoginClientTypeConditions.by_created_at_after,
                equals_factory=LoginClientTypeConditions.by_created_at_equals,
            )
            if condition is not None:
                conditions.append(condition)

        if filter.modified_at is not None:
            condition = filter.modified_at.build_query_condition(
                before_factory=LoginClientTypeConditions.by_modified_at_before,
                after_factory=LoginClientTypeConditions.by_modified_at_after,
                equals_factory=LoginClientTypeConditions.by_modified_at_equals,
            )
            if condition is not None:
                conditions.append(condition)

        return conditions
