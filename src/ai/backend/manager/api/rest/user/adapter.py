"""
Adapters to convert user admin DTOs to repository query objects.
Handles conversion of filter, order, and pagination parameters,
as well as data-to-DTO conversion.
"""

from __future__ import annotations

from typing import assert_never

from ai.backend.common.data.entity.user import UserID
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
from ai.backend.common.types import AccessKey
from ai.backend.manager.data.user.types import UserData, UserStatus
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.specs.pagination import OffsetPagination
from ai.backend.manager.models.user.searchable_fields import UserSearchableFields
from ai.backend.manager.models.user.searchers import UserSearcher
from ai.backend.manager.models.user.updaters import UserUpdater
from ai.backend.manager.repositories.base.filter_adapter import BaseFilterAdapter
from ai.backend.manager.types import OptionalState, TriState

__all__ = ("UserAdapter",)


class UserAdapter(BaseFilterAdapter):
    """Adapter for converting user admin requests to repository queries."""

    def convert_to_dto(self, data: UserData, main_access_key: AccessKey | None) -> UserDTO:
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
            main_access_key=main_access_key,
            container_uid=data.container_uid,
            container_main_gid=data.container_main_gid,
            container_gids=data.container_gids,
        )

    def build_updater(
        self,
        request: UpdateUserRequest,
        user_id: UserID,
        password_info: PasswordInfo | None = None,
    ) -> UserUpdater:
        """Convert update request to updater."""
        username = OptionalState[str].nop()
        password = OptionalState[PasswordInfo].nop()
        need_password_change = OptionalState[bool].nop()
        full_name = TriState[str].nop()
        description = TriState[str].nop()
        status = OptionalState[UserStatus].nop()
        domain_name = OptionalState[str].nop()
        role: OptionalState[UserRole] = OptionalState.nop()
        allowed_client_ip = TriState[list[str]].nop()
        totp_activated = OptionalState[bool].nop()
        resource_policy = OptionalState[str].nop()
        sudo_session_enabled = OptionalState[bool].nop()
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
            full_name = TriState.update(request.full_name)
        if request.description is not None:
            description = TriState.update(request.description)
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
        if request.container_uid is not None:
            container_uid = TriState.update(request.container_uid)
        if request.container_main_gid is not None:
            container_main_gid = TriState.update(request.container_main_gid)
        if request.container_gids is not None:
            container_gids = TriState.update(request.container_gids)
        if request.group_ids is not None:
            group_ids = OptionalState.update(request.group_ids)

        return UserUpdater(
            user_id=user_id,
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
            container_uid=container_uid,
            container_main_gid=container_main_gid,
            container_gids=container_gids,
            group_ids=group_ids,
        )

    def build_searcher(self, request: SearchUsersRequest) -> UserSearcher:
        """Build a user searcher from the search request."""
        conditions = self._convert_filter(request.filter) if request.filter else []
        orders = [self._convert_order(o) for o in request.order] if request.order else []
        pagination = OffsetPagination(limit=request.limit, offset=request.offset)
        return UserSearcher(conditions=conditions, orders=orders, pagination=pagination)

    def _convert_filter(self, f: UserFilter) -> list[QueryCondition]:
        """Convert user filter to query conditions."""
        fields = UserSearchableFields.own
        conditions = [
            *self.apply_uuid_filter(f.uuid, fields.uuid.filter),
            *self.apply_string_filter(f.email, fields.email.filter),
            *self.apply_string_filter(f.username, fields.username.filter),
            *self.apply_string_filter(f.domain_name, fields.domain_name.filter),
            *self.apply_string_filter(f.integration_name, fields.integration_name.filter),
        ]
        if f.status:
            conditions.append(fields.status.filter.in_([UserStatus(s.value) for s in f.status]))
        if f.role:
            conditions.append(fields.role.filter.in_([UserRole(r.value) for r in f.role]))
        return conditions

    def _convert_order(self, order: UserOrder) -> QueryOrder:
        """Convert user order specification to query order."""
        fields = UserSearchableFields.own
        ascending = order.direction == OrderDirection.ASC
        match order.field:
            case UserOrderField.CREATED_AT:
                return fields.created_at.order.apply(ascending)
            case UserOrderField.MODIFIED_AT:
                return fields.modified_at.order.apply(ascending)
            case UserOrderField.USERNAME:
                return fields.username.order.apply(ascending)
            case UserOrderField.EMAIL:
                return fields.email.order.apply(ascending)
            case UserOrderField.STATUS:
                return fields.status.order.apply(ascending)
            case UserOrderField.DOMAIN_NAME:
                return fields.domain_name.order.apply(ascending)
            case _:
                assert_never(order.field)
