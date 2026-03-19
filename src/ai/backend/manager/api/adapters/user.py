"""User domain adapter - Pydantic-in/Pydantic-out transport layer."""

from __future__ import annotations

from uuid import UUID

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.data.user.types import UserRole as DataUserRole
from ai.backend.common.dto.manager.pagination import PaginationInfo
from ai.backend.common.dto.manager.v2.user.request import (
    AdminSearchUsersInput,
    SearchUsersRequest,
    UserFilter,
    UserOrder,
)
from ai.backend.common.dto.manager.v2.user.response import (
    AdminSearchUsersPayload,
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
    UserDomainFilter,
    UserOrderField,
    UserProjectFilter,
    UserRoleFilter,
    UserStatusFilter,
)
from ai.backend.common.dto.manager.v2.user.types import (
    UserRole as UserRoleDTO,
)
from ai.backend.common.dto.manager.v2.user.types import (
    UserStatus as UserStatusDTO,
)
from ai.backend.manager.data.user.types import UserData, UserStatus
from ai.backend.manager.data.user.types import UserStatus as DataUserStatus
from ai.backend.manager.models.domain.conditions import DomainConditions
from ai.backend.manager.models.group.conditions import GroupConditions
from ai.backend.manager.models.user.conditions import UserConditions
from ai.backend.manager.models.user.orders import UserOrders
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    OffsetPagination,
    QueryCondition,
    QueryOrder,
    combine_conditions_or,
    negate_conditions,
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
from .pagination import PaginationSpec

_USER_PAGINATION_SPEC = PaginationSpec(
    forward_order=UserOrders.created_at(ascending=False),
    backward_order=UserOrders.created_at(ascending=True),
    forward_condition_factory=UserConditions.by_cursor_forward,
    backward_condition_factory=UserConditions.by_cursor_backward,
    tiebreaker_order=UserRow.uuid.asc(),
)


class UserAdapter(BaseAdapter):
    """Adapter for user domain operations.

    Intentionally omits: create, update, delete, purge.
    - create: requires PasswordInfo (password hashing) from auth config (caller responsibility)
    - update/delete/purge: require email-based action signatures not yet bridged;
      the corresponding GQL mutations currently raise NotImplementedError
    """

    # ------------------------------------------------------------------ GQL search (cursor-based)

    async def gql_admin_search(
        self,
        input: AdminSearchUsersInput,
    ) -> AdminSearchUsersPayload:
        """Search users with no scope restriction (admin only), cursor-based pagination."""
        conditions = self._convert_gql_filter(input.filter) if input.filter else []
        orders = self._convert_gql_orders(input.order) if input.order else []
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_USER_PAGINATION_SPEC,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        action_result = await self._processors.user.search_users.wait_for_complete(
            SearchUsersAction(querier=querier)
        )
        return AdminSearchUsersPayload(
            items=[self._user_data_to_node(u) for u in action_result.users],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def gql_search_by_domain(
        self,
        scope: DomainUserSearchScope,
        input: AdminSearchUsersInput,
    ) -> AdminSearchUsersPayload:
        """Search users within a domain, cursor-based pagination."""
        conditions = self._convert_gql_filter(input.filter) if input.filter else []
        orders = self._convert_gql_orders(input.order) if input.order else []
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_USER_PAGINATION_SPEC,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        action_result = await self._processors.user.search_users_by_domain.wait_for_complete(
            SearchUsersByDomainAction(scope=scope, querier=querier)
        )
        return AdminSearchUsersPayload(
            items=[self._user_data_to_node(u) for u in action_result.users],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def gql_search_by_project(
        self,
        scope: ProjectUserSearchScope,
        input: AdminSearchUsersInput,
    ) -> AdminSearchUsersPayload:
        """Search users within a project, cursor-based pagination."""
        conditions = self._convert_gql_filter(input.filter) if input.filter else []
        orders = self._convert_gql_orders(input.order) if input.order else []
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_USER_PAGINATION_SPEC,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        action_result = await self._processors.user.search_users_by_project.wait_for_complete(
            SearchUsersByProjectAction(scope=scope, querier=querier)
        )
        return AdminSearchUsersPayload(
            items=[self._user_data_to_node(u) for u in action_result.users],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

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

    # ------------------------------------------------------------------ GQL filter/order helpers

    def _convert_gql_filter(self, filter_req: UserFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []

        if filter_req.uuid is not None:
            condition = self.convert_uuid_filter(
                filter_req.uuid,
                equals_factory=UserConditions.by_uuid_equals,
                in_factory=UserConditions.by_uuid_in,
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

        if filter_req.status is not None:
            conditions.extend(self._convert_status_filter(filter_req.status))

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

        if filter_req.role is not None:
            conditions.extend(self._convert_role_filter(filter_req.role))

        if filter_req.created_at is not None:
            condition = filter_req.created_at.build_query_condition(
                before_factory=UserConditions.by_created_at_before,
                after_factory=UserConditions.by_created_at_after,
            )
            if condition is not None:
                conditions.append(condition)

        if filter_req.domain is not None:
            conditions.extend(self._convert_domain_nested_filter(filter_req.domain))

        if filter_req.project is not None:
            conditions.extend(self._convert_project_nested_filter(filter_req.project))

        if filter_req.AND:
            for sub_filter in filter_req.AND:
                conditions.extend(self._convert_gql_filter(sub_filter))

        if filter_req.OR:
            or_sub_conditions: list[QueryCondition] = []
            for sub_filter in filter_req.OR:
                or_sub_conditions.extend(self._convert_gql_filter(sub_filter))
            if or_sub_conditions:
                conditions.append(combine_conditions_or(or_sub_conditions))

        if filter_req.NOT:
            not_sub_conditions: list[QueryCondition] = []
            for sub_filter in filter_req.NOT:
                not_sub_conditions.extend(self._convert_gql_filter(sub_filter))
            if not_sub_conditions:
                conditions.append(negate_conditions(not_sub_conditions))

        return conditions

    @staticmethod
    def _convert_status_filter(sf: UserStatusFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if sf.equals is not None:
            conditions.append(UserConditions.by_status_equals(DataUserStatus(sf.equals.value)))
        if sf.in_ is not None:
            conditions.append(
                UserConditions.by_status_in([DataUserStatus(s.value) for s in sf.in_])
            )
        return conditions

    @staticmethod
    def _convert_role_filter(rf: UserRoleFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if rf.equals is not None:
            conditions.append(UserConditions.by_role_equals(DataUserRole(rf.equals.value)))
        if rf.in_ is not None:
            conditions.append(UserConditions.by_role_in([DataUserRole(r.value) for r in rf.in_]))
        return conditions

    def _convert_domain_nested_filter(
        self, domain_filter: UserDomainFilter
    ) -> list[QueryCondition]:
        raw_conditions: list[QueryCondition] = []
        if domain_filter.name is not None:
            condition = self.convert_string_filter(
                domain_filter.name,
                contains_factory=DomainConditions.by_name_contains,
                equals_factory=DomainConditions.by_name_equals,
                starts_with_factory=DomainConditions.by_name_starts_with,
                ends_with_factory=DomainConditions.by_name_ends_with,
            )
            if condition is not None:
                raw_conditions.append(condition)
        if domain_filter.is_active is not None:
            raw_conditions.append(DomainConditions.by_is_active(domain_filter.is_active))
        if not raw_conditions:
            return []
        return [UserConditions.exists_domain_combined(raw_conditions)]

    def _convert_project_nested_filter(
        self, project_filter: UserProjectFilter
    ) -> list[QueryCondition]:
        raw_conditions: list[QueryCondition] = []
        if project_filter.name is not None:
            condition = self.convert_string_filter(
                project_filter.name,
                contains_factory=GroupConditions.by_name_contains,
                equals_factory=GroupConditions.by_name_equals,
                starts_with_factory=GroupConditions.by_name_starts_with,
                ends_with_factory=GroupConditions.by_name_ends_with,
            )
            if condition is not None:
                raw_conditions.append(condition)
        if project_filter.is_active is not None:
            raw_conditions.append(GroupConditions.by_is_active(project_filter.is_active))
        if not raw_conditions:
            return []
        return [UserConditions.exists_project_combined(raw_conditions)]

    def _convert_gql_orders(self, orders: list[UserOrder]) -> list[QueryOrder]:
        return [self._convert_gql_order(o) for o in orders]

    @staticmethod
    def _convert_gql_order(order: UserOrder) -> QueryOrder:
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
            case UserOrderField.PROJECT_NAME:
                return UserOrders.by_project_name(ascending=ascending)

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

        if filter_req.status is not None:
            status_f = filter_req.status
            if status_f.equals is not None:
                conditions.append(
                    UserConditions.by_status_equals(UserStatus(status_f.equals.value))
                )
            if status_f.in_ is not None and len(status_f.in_) > 0:
                conditions.append(
                    UserConditions.by_status_in([UserStatus(s.value) for s in status_f.in_])
                )
            if status_f.not_equals is not None:
                conditions.append(
                    negate_conditions([
                        UserConditions.by_status_equals(UserStatus(status_f.not_equals.value))
                    ])
                )
            if status_f.not_in is not None and len(status_f.not_in) > 0:
                conditions.append(
                    negate_conditions([
                        UserConditions.by_status_in([UserStatus(s.value) for s in status_f.not_in])
                    ])
                )

        if filter_req.role is not None:
            role_f = filter_req.role
            if role_f.equals is not None:
                conditions.append(UserConditions.by_role_equals(UserRole(role_f.equals.value)))
            if role_f.in_ is not None and len(role_f.in_) > 0:
                conditions.append(
                    UserConditions.by_role_in([UserRole(r.value) for r in role_f.in_])
                )
            if role_f.not_equals is not None:
                conditions.append(
                    negate_conditions([
                        UserConditions.by_role_equals(UserRole(role_f.not_equals.value))
                    ])
                )
            if role_f.not_in is not None and len(role_f.not_in) > 0:
                conditions.append(
                    negate_conditions([
                        UserConditions.by_role_in([UserRole(r.value) for r in role_f.not_in])
                    ])
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
