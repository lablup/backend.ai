"""Login Session adapter bridging DTOs and Processors."""

from __future__ import annotations

from ai.backend.common.contexts.user import current_user
from ai.backend.common.dto.manager.v2.login_session.request import (
    AdminRevokeLoginSessionInput,
    AdminSearchLoginSessionsInput,
    LoginSessionFilter,
    LoginSessionOrder,
    LoginSessionStatusFilter,
    MyRevokeLoginSessionInput,
    MySearchLoginSessionsInput,
)
from ai.backend.common.dto.manager.v2.login_session.response import (
    AdminSearchLoginSessionsPayload,
    LoginSessionNode,
    MySearchLoginSessionsPayload,
    RevokeLoginSessionPayload,
)
from ai.backend.common.dto.manager.v2.login_session.types import (
    LoginSessionOrderField,
    LoginSessionStatus,
    OrderDirection,
)
from ai.backend.common.exception import UnreachableError
from ai.backend.manager.data.auth.login_session_types import LoginSessionData
from ai.backend.manager.models.login_session.row import LoginSessionRow
from ai.backend.manager.repositories.auth.options import LoginSessionConditions, LoginSessionOrders
from ai.backend.manager.repositories.auth.types import MyLoginSessionSearchScope
from ai.backend.manager.repositories.base import (
    QueryCondition,
    QueryOrder,
    combine_conditions_or,
    negate_conditions,
)
from ai.backend.manager.services.auth.actions.revoke_login_session import (
    AdminRevokeLoginSessionAction,
    MyRevokeLoginSessionAction,
)
from ai.backend.manager.services.auth.actions.search_login_sessions import (
    AdminSearchLoginSessionsAction,
    SearchLoginSessionsAction,
)

from .base import BaseAdapter
from .pagination import PaginationSpec

_LOGIN_SESSION_PAGINATION_SPEC = PaginationSpec(
    forward_order=LoginSessionOrders.created_at(ascending=False),
    backward_order=LoginSessionOrders.created_at(ascending=True),
    forward_condition_factory=LoginSessionConditions.by_cursor_forward,
    backward_condition_factory=LoginSessionConditions.by_cursor_backward,
    tiebreaker_order=LoginSessionRow.id.asc(),
)


class LoginSessionAdapter(BaseAdapter):
    """Adapter for login session domain operations."""

    async def admin_search(
        self, input: AdminSearchLoginSessionsInput
    ) -> AdminSearchLoginSessionsPayload:
        """Search login sessions with admin scope (no scope restriction)."""
        conditions = self._convert_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else []
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_LOGIN_SESSION_PAGINATION_SPEC,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        action_result = await self._processors.auth.admin_search_login_sessions.wait_for_complete(
            AdminSearchLoginSessionsAction(querier=querier)
        )
        return AdminSearchLoginSessionsPayload(
            items=[self._data_to_node(item) for item in action_result.result.items],
            total_count=action_result.result.total_count,
            has_next_page=action_result.result.has_next_page,
            has_previous_page=action_result.result.has_previous_page,
        )

    async def my_search(self, input: MySearchLoginSessionsInput) -> MySearchLoginSessionsPayload:
        """Search login sessions owned by the current user.

        Calls current_user() internally -- the caller does not need to pass scope.
        """
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")
        scope = MyLoginSessionSearchScope(user_id=me.user_id)
        conditions = self._convert_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else []
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_LOGIN_SESSION_PAGINATION_SPEC,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        action_result = await self._processors.auth.search_login_sessions.wait_for_complete(
            SearchLoginSessionsAction(scope=scope, querier=querier)
        )
        return MySearchLoginSessionsPayload(
            items=[self._data_to_node(item) for item in action_result.result.items],
            total_count=action_result.result.total_count,
            has_next_page=action_result.result.has_next_page,
            has_previous_page=action_result.result.has_previous_page,
        )

    async def my_revoke(self, input: MyRevokeLoginSessionInput) -> RevokeLoginSessionPayload:
        """Revoke a login session owned by the current user."""
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")
        action_result = await self._processors.auth.my_revoke_login_session.wait_for_complete(
            MyRevokeLoginSessionAction(
                session_id=input.session_id,
                user_id=me.user_id,
            )
        )
        return RevokeLoginSessionPayload(success=action_result.success)

    async def admin_revoke(self, input: AdminRevokeLoginSessionInput) -> RevokeLoginSessionPayload:
        """Revoke any login session (admin, no ownership check)."""
        action_result = await self._processors.auth.admin_revoke_login_session.wait_for_complete(
            AdminRevokeLoginSessionAction(
                session_id=input.session_id,
            )
        )
        return RevokeLoginSessionPayload(success=action_result.success)

    def _convert_filter(self, f: LoginSessionFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if f.status is not None:
            self._apply_status_filter(f.status, conditions)
        if f.access_key is not None:
            condition = self.convert_string_filter(
                f.access_key,
                contains_factory=LoginSessionConditions.by_access_key_contains,
                equals_factory=LoginSessionConditions.by_access_key_equals,
                starts_with_factory=LoginSessionConditions.by_access_key_starts_with,
                ends_with_factory=LoginSessionConditions.by_access_key_ends_with,
            )
            if condition is not None:
                conditions.append(condition)
        if f.created_at is not None:
            condition = f.created_at.build_query_condition(
                before_factory=LoginSessionConditions.by_created_at_before,
                after_factory=LoginSessionConditions.by_created_at_after,
                equals_factory=LoginSessionConditions.by_created_at_equals,
            )
            if condition is not None:
                conditions.append(condition)
        if f.last_accessed_at is not None:
            condition = f.last_accessed_at.build_query_condition(
                before_factory=LoginSessionConditions.by_last_accessed_at_before,
                after_factory=LoginSessionConditions.by_last_accessed_at_after,
                equals_factory=LoginSessionConditions.by_last_accessed_at_equals,
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
    def _apply_status_filter(s: LoginSessionStatusFilter, conditions: list[QueryCondition]) -> None:
        if s.equals is not None:
            conditions.append(LoginSessionConditions.by_status_in([s.equals]))
        elif s.in_ is not None:
            conditions.append(LoginSessionConditions.by_status_in(list(s.in_)))
        elif s.not_in is not None:
            conditions.append(LoginSessionConditions.by_status_not_in(list(s.not_in)))

    @staticmethod
    def _convert_orders(orders: list[LoginSessionOrder]) -> list[QueryOrder]:
        result: list[QueryOrder] = []
        for o in orders:
            ascending = o.direction == OrderDirection.ASC
            match o.field:
                case LoginSessionOrderField.CREATED_AT:
                    result.append(LoginSessionOrders.created_at(ascending))
                case LoginSessionOrderField.STATUS:
                    result.append(LoginSessionOrders.status(ascending))
                case LoginSessionOrderField.LAST_ACCESSED_AT:
                    result.append(LoginSessionOrders.last_accessed_at(ascending))
        return result

    @staticmethod
    def _data_to_node(data: LoginSessionData) -> LoginSessionNode:
        return LoginSessionNode(
            id=data.id,
            user_id=data.user_id,
            access_key=data.access_key,
            status=LoginSessionStatus(data.status.value),
            created_at=data.created_at,
            last_accessed_at=data.last_accessed_at,
            invalidated_at=data.invalidated_at,
        )
