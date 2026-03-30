"""Login History adapter bridging DTOs and Processors."""

from __future__ import annotations

from ai.backend.common.contexts.user import current_user
from ai.backend.common.dto.manager.v2.login_history.request import (
    AdminSearchLoginHistoryInput,
    LoginHistoryFilter,
    LoginHistoryOrder,
    LoginHistoryResultFilter,
    MySearchLoginHistoryInput,
)
from ai.backend.common.dto.manager.v2.login_history.response import (
    AdminSearchLoginHistoryPayload,
    LoginHistoryNode,
    MySearchLoginHistoryPayload,
)
from ai.backend.common.dto.manager.v2.login_history.types import (
    LoginAttemptResult,
    LoginHistoryOrderField,
    OrderDirection,
)
from ai.backend.common.exception import UnreachableError
from ai.backend.manager.data.auth.login_session_types import LoginHistoryData
from ai.backend.manager.models.login_session.row import LoginHistoryRow
from ai.backend.manager.repositories.auth.options import LoginHistoryConditions, LoginHistoryOrders
from ai.backend.manager.repositories.auth.types import MyLoginHistorySearchScope
from ai.backend.manager.repositories.base import (
    QueryCondition,
    QueryOrder,
    combine_conditions_or,
    negate_conditions,
)
from ai.backend.manager.services.auth.actions.search_login_history import (
    AdminSearchLoginHistoryAction,
    SearchLoginHistoryAction,
)

from .base import BaseAdapter
from .pagination import PaginationSpec

_LOGIN_HISTORY_PAGINATION_SPEC = PaginationSpec(
    forward_order=LoginHistoryOrders.created_at(ascending=False),
    backward_order=LoginHistoryOrders.created_at(ascending=True),
    forward_condition_factory=LoginHistoryConditions.by_cursor_forward,
    backward_condition_factory=LoginHistoryConditions.by_cursor_backward,
    tiebreaker_order=LoginHistoryRow.id.asc(),
)


class LoginHistoryAdapter(BaseAdapter):
    """Adapter for login history domain operations."""

    async def admin_search(
        self, input: AdminSearchLoginHistoryInput
    ) -> AdminSearchLoginHistoryPayload:
        """Search login history with admin scope (no scope restriction)."""
        conditions = self._convert_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else []
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_LOGIN_HISTORY_PAGINATION_SPEC,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        action_result = await self._processors.auth.admin_search_login_history.wait_for_complete(
            AdminSearchLoginHistoryAction(querier=querier)
        )
        return AdminSearchLoginHistoryPayload(
            items=[self._data_to_node(item) for item in action_result.result.items],
            total_count=action_result.result.total_count,
            has_next_page=action_result.result.has_next_page,
            has_previous_page=action_result.result.has_previous_page,
        )

    async def my_search(self, input: MySearchLoginHistoryInput) -> MySearchLoginHistoryPayload:
        """Search login history of the current user.

        Calls current_user() internally -- the caller does not need to pass scope.
        """
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")
        scope = MyLoginHistorySearchScope(user_id=me.user_id)
        conditions = self._convert_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else []
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_LOGIN_HISTORY_PAGINATION_SPEC,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        action_result = await self._processors.auth.search_login_history.wait_for_complete(
            SearchLoginHistoryAction(scope=scope, querier=querier)
        )
        return MySearchLoginHistoryPayload(
            items=[self._data_to_node(item) for item in action_result.result.items],
            total_count=action_result.result.total_count,
            has_next_page=action_result.result.has_next_page,
            has_previous_page=action_result.result.has_previous_page,
        )

    def _convert_filter(self, f: LoginHistoryFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if f.domain_name is not None:
            condition = self.convert_string_filter(
                f.domain_name,
                contains_factory=LoginHistoryConditions.by_domain_name_contains,
                equals_factory=LoginHistoryConditions.by_domain_name_equals,
                starts_with_factory=LoginHistoryConditions.by_domain_name_starts_with,
                ends_with_factory=LoginHistoryConditions.by_domain_name_ends_with,
            )
            if condition is not None:
                conditions.append(condition)
        if f.result is not None:
            self._apply_result_filter(f.result, conditions)
        if f.created_at is not None:
            condition = f.created_at.build_query_condition(
                before_factory=LoginHistoryConditions.by_created_at_before,
                after_factory=LoginHistoryConditions.by_created_at_after,
                equals_factory=LoginHistoryConditions.by_created_at_equals,
            )
            if condition is not None:
                conditions.append(condition)
        if f.AND:
            for sub_filter in f.AND:
                conditions.extend(self._convert_filter(sub_filter))
        if f.OR:
            or_conditions: list[QueryCondition] = []
            for sub_filter in f.OR:
                or_conditions.extend(self._convert_filter(sub_filter))
            if or_conditions:
                conditions.append(combine_conditions_or(or_conditions))
        if f.NOT:
            not_conditions: list[QueryCondition] = []
            for sub_filter in f.NOT:
                not_conditions.extend(self._convert_filter(sub_filter))
            if not_conditions:
                conditions.append(negate_conditions(not_conditions))
        return conditions

    @staticmethod
    def _apply_result_filter(r: LoginHistoryResultFilter, conditions: list[QueryCondition]) -> None:
        if r.equals is not None:
            conditions.append(LoginHistoryConditions.by_result_in([r.equals]))
        elif r.in_ is not None:
            conditions.append(LoginHistoryConditions.by_result_in(list(r.in_)))
        elif r.not_in is not None:
            conditions.append(LoginHistoryConditions.by_result_not_in(list(r.not_in)))

    @staticmethod
    def _convert_orders(orders: list[LoginHistoryOrder]) -> list[QueryOrder]:
        result: list[QueryOrder] = []
        for o in orders:
            ascending = o.direction == OrderDirection.ASC
            match o.field:
                case LoginHistoryOrderField.CREATED_AT:
                    result.append(LoginHistoryOrders.created_at(ascending))
                case LoginHistoryOrderField.RESULT:
                    result.append(LoginHistoryOrders.result(ascending))
                case LoginHistoryOrderField.DOMAIN_NAME:
                    result.append(LoginHistoryOrders.domain_name(ascending))
        return result

    @staticmethod
    def _data_to_node(data: LoginHistoryData) -> LoginHistoryNode:
        return LoginHistoryNode(
            id=data.id,
            user_id=data.user_id,
            domain_name=data.domain_name,
            result=LoginAttemptResult(data.result.value),
            fail_reason=data.fail_reason,
            created_at=data.created_at,
        )
