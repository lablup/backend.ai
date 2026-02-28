"""
Adapters to convert user admin DTOs to repository query objects.
Handles conversion of filter, order, and pagination parameters,
as well as data-to-DTO conversion.
"""

from __future__ import annotations

from uuid import UUID

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.user import (
    OrderDirection,
    SearchUsersRequest,
    UpdateUserRequest,
    UserDTO,
    UserFilter,
    UserOrder,
    UserOrderField,
)
from ai.backend.common.dto.manager.user.types import UserRole as UserRoleDTO
from ai.backend.common.dto.manager.user.types import UserStatus as UserStatusDTO
from ai.backend.manager.api.adapter import BaseFilterAdapter
from ai.backend.manager.data.user.types import UserData, UserStatus
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    OffsetPagination,
    QueryCondition,
    QueryOrder,
)
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.user.options import UserConditions, UserOrders
from ai.backend.manager.repositories.user.updaters import UserUpdaterSpec
from ai.backend.manager.types import OptionalState, TriState

__all__ = ("UserAdapter",)


class UserAdapter(BaseFilterAdapter):
    """Adapter for converting user admin requests to repository queries."""

    def convert_to_dto(self, data: UserData) -> UserDTO:
        """Convert UserData to DTO for REST response."""
        return UserDTO(
            id=data.id,
            username=data.username,
            email=data.email,
            need_password_change=data.need_password_change,
            full_name=data.full_name,
            description=data.description,
            status=UserStatusDTO(data.status),
            status_info=data.status_info,
            created_at=data.created_at,
            modified_at=data.modified_at,
            domain_name=data.domain_name,
            role=UserRoleDTO(data.role.value) if data.role is not None else None,
            resource_policy=data.resource_policy,
            allowed_client_ip=data.allowed_client_ip,
            totp_activated=data.totp_activated,
            sudo_session_enabled=data.sudo_session_enabled,
            main_access_key=data.main_access_key,
            container_uid=data.container_uid,
            container_main_gid=data.container_main_gid,
            container_gids=data.container_gids,
        )

    def build_updater(
        self,
        request: UpdateUserRequest,
        email: str,
        password_info: PasswordInfo | None = None,
    ) -> Updater[UserRow]:
        """Convert update request to updater."""
        username = OptionalState[str].nop()
        password = OptionalState[PasswordInfo].nop()
        need_password_change = OptionalState[bool].nop()
        full_name = OptionalState[str].nop()
        description = OptionalState[str].nop()
        status = OptionalState[UserStatus].nop()
        domain_name = OptionalState[str].nop()
        role: OptionalState[UserRole] = OptionalState.nop()
        allowed_client_ip = TriState[list[str]].nop()
        totp_activated = OptionalState[bool].nop()
        resource_policy = OptionalState[str].nop()
        sudo_session_enabled = OptionalState[bool].nop()
        main_access_key = TriState[str].nop()
        container_uid = TriState[int].nop()
        container_main_gid = TriState[int].nop()
        container_gids = TriState[list[int]].nop()
        group_ids = OptionalState[list[str]].nop()

        if request.username is not None:
            username = OptionalState.update(request.username)
        if password_info is not None:
            password = OptionalState.update(password_info)
        if request.need_password_change is not None:
            need_password_change = OptionalState.update(request.need_password_change)
        if request.full_name is not None:
            full_name = OptionalState.update(request.full_name)
        if request.description is not None:
            description = OptionalState.update(request.description)
        if request.status is not None:
            status = OptionalState.update(UserStatus(request.status.value))
        if request.domain_name is not None:
            domain_name = OptionalState.update(request.domain_name)
        if request.role is not None:
            role = OptionalState.update(UserRole(request.role.value))
        if request.allowed_client_ip is not None:
            allowed_client_ip = TriState.update(request.allowed_client_ip)
        if request.totp_activated is not None:
            totp_activated = OptionalState.update(request.totp_activated)
        if request.resource_policy is not None:
            resource_policy = OptionalState.update(request.resource_policy)
        if request.sudo_session_enabled is not None:
            sudo_session_enabled = OptionalState.update(request.sudo_session_enabled)
        if request.main_access_key is not None:
            main_access_key = TriState.update(request.main_access_key)
        if request.container_uid is not None:
            container_uid = TriState.update(request.container_uid)
        if request.container_main_gid is not None:
            container_main_gid = TriState.update(request.container_main_gid)
        if request.container_gids is not None:
            container_gids = TriState.update(request.container_gids)
        if request.group_ids is not None:
            group_ids = OptionalState.update(request.group_ids)

        updater_spec = UserUpdaterSpec(
            username=username,
            password=password,
            need_password_change=need_password_change,
            full_name=full_name,
            description=description,
            status=status,
            domain_name=domain_name,
            role=role,
            allowed_client_ip=allowed_client_ip,
            totp_activated=totp_activated,
            resource_policy=resource_policy,
            sudo_session_enabled=sudo_session_enabled,
            main_access_key=main_access_key,
            container_uid=container_uid,
            container_main_gid=container_main_gid,
            container_gids=container_gids,
            group_ids=group_ids,
        )
        return Updater(
            spec=updater_spec, pk_value=UUID(int=0)
        )  # pk_value unused; email-based lookup

    def build_querier(self, request: SearchUsersRequest) -> BatchQuerier:
        """Build a BatchQuerier from search request."""
        conditions = self._convert_filter(request.filter) if request.filter else []
        orders = [self._convert_order(o) for o in request.order] if request.order else []
        pagination = OffsetPagination(limit=request.limit, offset=request.offset)
        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def _convert_filter(self, filter_req: UserFilter) -> list[QueryCondition]:
        """Convert user filter to query conditions."""
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

    def _convert_order(self, order: UserOrder) -> QueryOrder:
        """Convert user order specification to query order."""
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
