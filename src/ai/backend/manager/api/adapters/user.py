"""User domain adapter - Pydantic-in/Pydantic-out transport layer."""

from __future__ import annotations

from uuid import UUID

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.pagination import PaginationInfo
from ai.backend.common.dto.manager.v2.user.request import (
    SearchUsersRequest,
    UserFilter,
    UserOrder,
)
from ai.backend.common.dto.manager.v2.user.response import (
    EntityTimestamps,
    SearchUsersPayload,
    UserBasicInfo,
    UserContainerSettings,
    UserNode,
    UserOrganizationInfo,
    UserPayload,
    UserSecurityInfo,
    UserStatusInfo,
)
from ai.backend.common.dto.manager.v2.user.types import (
    OrderDirection,
    UserOrderField,
)
from ai.backend.common.dto.manager.v2.user.types import (
    UserRole as UserRoleDTO,
)
from ai.backend.common.dto.manager.v2.user.types import (
    UserStatus as UserStatusDTO,
)
from ai.backend.manager.data.user.types import UserData, UserStatus
from ai.backend.manager.models.user.conditions import UserConditions
from ai.backend.manager.models.user.orders import UserOrders
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    OffsetPagination,
    QueryCondition,
    QueryOrder,
)
from ai.backend.manager.repositories.user.types import (
    DomainUserSearchScope,
    ProjectUserSearchScope,
    RoleUserSearchScope,
)
from ai.backend.manager.services.user.actions.get_user import GetUserAction
from ai.backend.manager.services.user.actions.search_users import SearchUsersAction
from ai.backend.manager.services.user.actions.search_users_by_domain import (
    SearchUsersByDomainAction,
)
from ai.backend.manager.services.user.actions.search_users_by_project import (
    SearchUsersByProjectAction,
)
from ai.backend.manager.services.user.actions.search_users_by_role import (
    SearchUsersByRoleAction,
)

from .base import BaseAdapter


class UserAdapter(BaseAdapter):
    """Adapter for user domain operations.

    Intentionally omits: create, update, delete, purge.
    - create: requires PasswordInfo (password hashing) from auth config (caller responsibility)
    - update/delete/purge: require email-based action signatures not yet bridged;
      the corresponding GQL mutations currently raise NotImplementedError
    """

    # ------------------------------------------------------------------ search

    async def admin_search(
        self,
        input: SearchUsersRequest,
    ) -> SearchUsersPayload:
        """Search users with no scope restriction (admin only)."""
        querier = self._build_search_querier(input)
        action_result = await self._processors.user.search_users.wait_for_complete(
            SearchUsersAction(querier=querier)
        )
        return SearchUsersPayload(
            items=[self._user_data_to_node(u) for u in action_result.users],
            pagination=PaginationInfo(
                total=action_result.total_count,
                offset=input.offset,
                limit=input.limit,
            ),
        )

    async def domain_search(
        self,
        domain_name: str,
        input: SearchUsersRequest,
    ) -> SearchUsersPayload:
        """Search users within a domain."""
        querier = self._build_search_querier(input)
        scope = DomainUserSearchScope(domain_name=domain_name)
        action_result = await self._processors.user.search_users_by_domain.wait_for_complete(
            SearchUsersByDomainAction(scope=scope, querier=querier)
        )
        return SearchUsersPayload(
            items=[self._user_data_to_node(u) for u in action_result.users],
            pagination=PaginationInfo(
                total=action_result.total_count,
                offset=input.offset,
                limit=input.limit,
            ),
        )

    async def project_search(
        self,
        project_id: UUID,
        input: SearchUsersRequest,
    ) -> SearchUsersPayload:
        """Search users within a project."""
        querier = self._build_search_querier(input)
        scope = ProjectUserSearchScope(project_id=project_id)
        action_result = await self._processors.user.search_users_by_project.wait_for_complete(
            SearchUsersByProjectAction(scope=scope, querier=querier)
        )
        return SearchUsersPayload(
            items=[self._user_data_to_node(u) for u in action_result.users],
            pagination=PaginationInfo(
                total=action_result.total_count,
                offset=input.offset,
                limit=input.limit,
            ),
        )

    async def role_search(
        self,
        role_id: UUID,
        input: SearchUsersRequest,
    ) -> SearchUsersPayload:
        """Search users assigned to a role."""
        querier = self._build_search_querier(input)
        scope = RoleUserSearchScope(role_id=role_id)
        action_result = await self._processors.user.search_users_by_role.wait_for_complete(
            SearchUsersByRoleAction(scope=scope, querier=querier)
        )
        return SearchUsersPayload(
            items=[self._user_data_to_node(u) for u in action_result.users],
            pagination=PaginationInfo(
                total=action_result.total_count,
                offset=input.offset,
                limit=input.limit,
            ),
        )

    # ------------------------------------------------------------------ get

    async def get(self, user_id: UUID) -> UserPayload:
        """Get a user by UUID."""
        action_result = await self._processors.user.get_user.wait_for_complete(
            GetUserAction(user_uuid=user_id)
        )
        return UserPayload(user=self._user_data_to_node(action_result.user))

    # ------------------------------------------------------------------ helpers

    def _build_search_querier(self, input: SearchUsersRequest) -> BatchQuerier:
        """Build a BatchQuerier from the search request DTO."""
        conditions = self._convert_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else []
        pagination = OffsetPagination(limit=input.limit, offset=input.offset)
        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def _convert_filter(self, filter_req: UserFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []

        if filter_req.uuid is not None:
            condition = self.convert_uuid_filter(
                filter_req.uuid,
                equals_factory=UserConditions.by_uuid_equals,
                in_factory=UserConditions.by_uuid_in,
            )
            if condition is not None:
                conditions.append(condition)

        if filter_req.email is not None:
            condition = self.convert_string_filter(
                filter_req.email,
                contains_factory=UserConditions.by_email_contains,
                equals_factory=UserConditions.by_email_equals,
                starts_with_factory=UserConditions.by_email_starts_with,
                ends_with_factory=UserConditions.by_email_ends_with,
            )
            if condition is not None:
                conditions.append(condition)

        if filter_req.username is not None:
            condition = self.convert_string_filter(
                filter_req.username,
                contains_factory=UserConditions.by_username_contains,
                equals_factory=UserConditions.by_username_equals,
                starts_with_factory=UserConditions.by_username_starts_with,
                ends_with_factory=UserConditions.by_username_ends_with,
            )
            if condition is not None:
                conditions.append(condition)

        if filter_req.domain_name is not None:
            condition = self.convert_string_filter(
                filter_req.domain_name,
                contains_factory=UserConditions.by_domain_name_contains,
                equals_factory=UserConditions.by_domain_name_equals,
                starts_with_factory=UserConditions.by_domain_name_starts_with,
                ends_with_factory=UserConditions.by_domain_name_ends_with,
            )
            if condition is not None:
                conditions.append(condition)

        if filter_req.status is not None and len(filter_req.status) > 0:
            conditions.append(
                UserConditions.by_status_in([UserStatus(s.value) for s in filter_req.status])
            )

        if filter_req.role is not None and len(filter_req.role) > 0:
            conditions.append(
                UserConditions.by_role_in([UserRole(r.value) for r in filter_req.role])
            )

        return conditions

    def _convert_orders(self, orders: list[UserOrder]) -> list[QueryOrder]:
        return [self._convert_order(o) for o in orders]

    @staticmethod
    def _convert_order(order: UserOrder) -> QueryOrder:
        ascending = order.direction == OrderDirection.ASC
        match order.field:
            case UserOrderField.CREATED_AT:
                return UserOrders.created_at(ascending=ascending)
            case UserOrderField.MODIFIED_AT:
                return UserOrders.modified_at(ascending=ascending)
            case UserOrderField.USERNAME:
                return UserOrders.username(ascending=ascending)
            case UserOrderField.EMAIL:
                return UserOrders.email(ascending=ascending)
            case UserOrderField.STATUS:
                return UserOrders.status(ascending=ascending)
            case UserOrderField.DOMAIN_NAME:
                return UserOrders.domain_name(ascending=ascending)
        raise ValueError(f"Unknown order field: {order.field}")

    @staticmethod
    def _user_data_to_node(data: UserData) -> UserNode:
        """Convert UserData to UserNode DTO."""
        return UserNode(
            id=data.id,
            basic_info=UserBasicInfo(
                username=data.username,
                email=data.email,
                full_name=data.full_name,
                description=data.description,
            ),
            status=UserStatusInfo(
                status=UserStatusDTO(data.status),
                status_info=data.status_info,
                need_password_change=data.need_password_change,
            ),
            organization=UserOrganizationInfo(
                domain_name=data.domain_name,
                role=UserRoleDTO(data.role.value) if data.role is not None else None,
                resource_policy=data.resource_policy,
                main_access_key=data.main_access_key,
            ),
            security=UserSecurityInfo(
                allowed_client_ip=data.allowed_client_ip,
                totp_activated=data.totp_activated,
                totp_activated_at=data.totp_activated_at,
                sudo_session_enabled=data.sudo_session_enabled,
            ),
            container=UserContainerSettings(
                container_uid=data.container_uid,
                container_main_gid=data.container_main_gid,
                container_gids=data.container_gids,
            ),
            timestamps=EntityTimestamps(
                created_at=data.created_at,
                modified_at=data.modified_at,
            ),
        )
