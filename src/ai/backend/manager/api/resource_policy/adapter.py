"""
Adapters to convert resource policy DTOs to repository objects.
"""

from __future__ import annotations

from typing import Any

from ai.backend.common.api_handlers import SENTINEL
from ai.backend.common.dto.manager.resource_policy.request import (
    KeypairResourcePolicyFilter,
    KeypairResourcePolicyOrder,
    ProjectResourcePolicyFilter,
    ProjectResourcePolicyOrder,
    SearchKeypairResourcePoliciesRequest,
    SearchProjectResourcePoliciesRequest,
    SearchUserResourcePoliciesRequest,
    UpdateKeypairResourcePolicyRequest,
    UpdateProjectResourcePolicyRequest,
    UpdateUserResourcePolicyRequest,
    UserResourcePolicyFilter,
    UserResourcePolicyOrder,
)
from ai.backend.common.dto.manager.resource_policy.response import (
    KeypairResourcePolicyDTO,
    ProjectResourcePolicyDTO,
    UserResourcePolicyDTO,
)
from ai.backend.common.dto.manager.resource_policy.types import (
    KeypairResourcePolicyOrderField,
    OrderDirection,
    ProjectResourcePolicyOrderField,
    UserResourcePolicyOrderField,
)
from ai.backend.common.types import DefaultForUnspecified, ResourceSlot
from ai.backend.manager.api.adapter import BaseFilterAdapter
from ai.backend.manager.data.resource.types import (
    KeyPairResourcePolicyData,
    ProjectResourcePolicyData,
    UserResourcePolicyData,
)
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    OffsetPagination,
    QueryCondition,
    QueryOrder,
)
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.keypair_resource_policy.options import (
    KeypairResourcePolicyConditions,
    KeypairResourcePolicyOrders,
)
from ai.backend.manager.repositories.keypair_resource_policy.updaters import (
    KeyPairResourcePolicyUpdaterSpec,
)
from ai.backend.manager.repositories.project_resource_policy.options import (
    ProjectResourcePolicyConditions,
    ProjectResourcePolicyOrders,
)
from ai.backend.manager.repositories.project_resource_policy.updaters import (
    ProjectResourcePolicyUpdaterSpec,
)
from ai.backend.manager.repositories.user_resource_policy.options import (
    UserResourcePolicyConditions,
    UserResourcePolicyOrders,
)
from ai.backend.manager.repositories.user_resource_policy.updaters import (
    UserResourcePolicyUpdaterSpec,
)
from ai.backend.manager.types import OptionalState, TriState

__all__ = ("ResourcePolicyAdapter",)


class ResourcePolicyAdapter(BaseFilterAdapter):
    """Adapter for converting resource policy requests to repository queries."""

    # ---- Keypair Resource Policy ----

    def convert_keypair_to_dto(self, data: KeyPairResourcePolicyData) -> KeypairResourcePolicyDTO:
        return KeypairResourcePolicyDTO(
            name=data.name,
            created_at=data.created_at,
            default_for_unspecified=data.default_for_unspecified,
            total_resource_slots=dict(data.total_resource_slots),
            max_session_lifetime=data.max_session_lifetime,
            max_concurrent_sessions=data.max_concurrent_sessions,
            max_pending_session_count=data.max_pending_session_count,
            max_pending_session_resource_slots=data.max_pending_session_resource_slots,
            max_concurrent_sftp_sessions=data.max_concurrent_sftp_sessions,
            max_containers_per_session=data.max_containers_per_session,
            idle_timeout=data.idle_timeout,
            allowed_vfolder_hosts=data.allowed_vfolder_hosts,
        )

    def build_keypair_updater(
        self, request: UpdateKeypairResourcePolicyRequest, policy_name: str
    ) -> Updater[KeyPairResourcePolicyRow]:
        default_for_unspecified: OptionalState[DefaultForUnspecified] = OptionalState.nop()
        total_resource_slots: OptionalState[ResourceSlot] = OptionalState.nop()
        max_session_lifetime: OptionalState[int] = OptionalState.nop()
        max_concurrent_sessions: OptionalState[int] = OptionalState.nop()
        max_pending_session_count: TriState[int] = TriState.nop()
        max_pending_session_resource_slots: TriState[dict[str, Any]] = TriState.nop()
        max_concurrent_sftp_sessions: OptionalState[int] = OptionalState.nop()
        max_containers_per_session: OptionalState[int] = OptionalState.nop()
        idle_timeout: OptionalState[int] = OptionalState.nop()
        allowed_vfolder_hosts: OptionalState[dict[str, Any]] = OptionalState.nop()

        if not isinstance(request.default_for_unspecified, type(SENTINEL)):
            default_for_unspecified = OptionalState.update(request.default_for_unspecified)
        if not isinstance(request.total_resource_slots, type(SENTINEL)):
            total_resource_slots = OptionalState.update(ResourceSlot(request.total_resource_slots))
        if not isinstance(request.max_session_lifetime, type(SENTINEL)):
            max_session_lifetime = OptionalState.update(request.max_session_lifetime)
        if not isinstance(request.max_concurrent_sessions, type(SENTINEL)):
            max_concurrent_sessions = OptionalState.update(request.max_concurrent_sessions)
        if request.max_pending_session_count is not SENTINEL:
            if request.max_pending_session_count is None:
                max_pending_session_count = TriState.nullify()
            else:
                max_pending_session_count = TriState.update(request.max_pending_session_count)
        if request.max_pending_session_resource_slots is not SENTINEL:
            if request.max_pending_session_resource_slots is None:
                max_pending_session_resource_slots = TriState.nullify()
            else:
                max_pending_session_resource_slots = TriState.update(
                    request.max_pending_session_resource_slots
                )
        if not isinstance(request.max_concurrent_sftp_sessions, type(SENTINEL)):
            max_concurrent_sftp_sessions = OptionalState.update(
                request.max_concurrent_sftp_sessions
            )
        if not isinstance(request.max_containers_per_session, type(SENTINEL)):
            max_containers_per_session = OptionalState.update(request.max_containers_per_session)
        if not isinstance(request.idle_timeout, type(SENTINEL)):
            idle_timeout = OptionalState.update(request.idle_timeout)
        if not isinstance(request.allowed_vfolder_hosts, type(SENTINEL)):
            allowed_vfolder_hosts = OptionalState.update(request.allowed_vfolder_hosts)

        updater_spec = KeyPairResourcePolicyUpdaterSpec(
            allowed_vfolder_hosts=allowed_vfolder_hosts,
            default_for_unspecified=default_for_unspecified,
            idle_timeout=idle_timeout,
            max_concurrent_sessions=max_concurrent_sessions,
            max_containers_per_session=max_containers_per_session,
            max_pending_session_count=max_pending_session_count,
            max_pending_session_resource_slots=max_pending_session_resource_slots,
            max_concurrent_sftp_sessions=max_concurrent_sftp_sessions,
            max_session_lifetime=max_session_lifetime,
            total_resource_slots=total_resource_slots,
        )
        return Updater(spec=updater_spec, pk_value=policy_name)

    def build_keypair_querier(self, request: SearchKeypairResourcePoliciesRequest) -> BatchQuerier:
        conditions = self._convert_keypair_filter(request.filter) if request.filter else []
        orders = [self._convert_keypair_order(o) for o in request.order] if request.order else []
        pagination = OffsetPagination(limit=request.limit, offset=request.offset)
        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def _convert_keypair_filter(self, filter: KeypairResourcePolicyFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if filter.name is not None:
            condition = self.convert_string_filter(
                filter.name,
                contains_factory=KeypairResourcePolicyConditions.by_name_contains,
                equals_factory=KeypairResourcePolicyConditions.by_name_equals,
                starts_with_factory=KeypairResourcePolicyConditions.by_name_starts_with,
                ends_with_factory=KeypairResourcePolicyConditions.by_name_ends_with,
            )
            if condition is not None:
                conditions.append(condition)
        return conditions

    def _convert_keypair_order(self, order: KeypairResourcePolicyOrder) -> QueryOrder:
        ascending = order.direction == OrderDirection.ASC
        if order.field == KeypairResourcePolicyOrderField.NAME:
            return KeypairResourcePolicyOrders.name(ascending=ascending)
        if order.field == KeypairResourcePolicyOrderField.CREATED_AT:
            return KeypairResourcePolicyOrders.created_at(ascending=ascending)
        raise ValueError(f"Unknown order field: {order.field}")

    # ---- User Resource Policy ----

    def convert_user_to_dto(self, data: UserResourcePolicyData) -> UserResourcePolicyDTO:
        return UserResourcePolicyDTO(
            name=data.name,
            created_at=None,
            max_vfolder_count=data.max_vfolder_count,
            max_quota_scope_size=data.max_quota_scope_size,
            max_session_count_per_model_session=data.max_session_count_per_model_session,
            max_customized_image_count=data.max_customized_image_count,
        )

    def build_user_updater(
        self, request: UpdateUserResourcePolicyRequest, policy_name: str
    ) -> Updater[UserResourcePolicyRow]:
        max_vfolder_count: OptionalState[int] = OptionalState.nop()
        max_quota_scope_size: OptionalState[int] = OptionalState.nop()
        max_session_count_per_model_session: OptionalState[int] = OptionalState.nop()
        max_customized_image_count: OptionalState[int] = OptionalState.nop()

        if not isinstance(request.max_vfolder_count, type(SENTINEL)):
            max_vfolder_count = OptionalState.update(request.max_vfolder_count)
        if not isinstance(request.max_quota_scope_size, type(SENTINEL)):
            max_quota_scope_size = OptionalState.update(request.max_quota_scope_size)
        if not isinstance(request.max_session_count_per_model_session, type(SENTINEL)):
            max_session_count_per_model_session = OptionalState.update(
                request.max_session_count_per_model_session
            )
        if not isinstance(request.max_customized_image_count, type(SENTINEL)):
            max_customized_image_count = OptionalState.update(request.max_customized_image_count)

        updater_spec = UserResourcePolicyUpdaterSpec(
            max_vfolder_count=max_vfolder_count,
            max_quota_scope_size=max_quota_scope_size,
            max_session_count_per_model_session=max_session_count_per_model_session,
            max_customized_image_count=max_customized_image_count,
        )
        return Updater(spec=updater_spec, pk_value=policy_name)

    def build_user_querier(self, request: SearchUserResourcePoliciesRequest) -> BatchQuerier:
        conditions = self._convert_user_filter(request.filter) if request.filter else []
        orders = [self._convert_user_order(o) for o in request.order] if request.order else []
        pagination = OffsetPagination(limit=request.limit, offset=request.offset)
        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def _convert_user_filter(self, filter: UserResourcePolicyFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if filter.name is not None:
            condition = self.convert_string_filter(
                filter.name,
                contains_factory=UserResourcePolicyConditions.by_name_contains,
                equals_factory=UserResourcePolicyConditions.by_name_equals,
                starts_with_factory=UserResourcePolicyConditions.by_name_starts_with,
                ends_with_factory=UserResourcePolicyConditions.by_name_ends_with,
            )
            if condition is not None:
                conditions.append(condition)
        return conditions

    def _convert_user_order(self, order: UserResourcePolicyOrder) -> QueryOrder:
        ascending = order.direction == OrderDirection.ASC
        if order.field == UserResourcePolicyOrderField.NAME:
            return UserResourcePolicyOrders.name(ascending=ascending)
        if order.field == UserResourcePolicyOrderField.CREATED_AT:
            return UserResourcePolicyOrders.created_at(ascending=ascending)
        raise ValueError(f"Unknown order field: {order.field}")

    # ---- Project Resource Policy ----

    def convert_project_to_dto(self, data: ProjectResourcePolicyData) -> ProjectResourcePolicyDTO:
        return ProjectResourcePolicyDTO(
            name=data.name,
            created_at=None,
            max_vfolder_count=data.max_vfolder_count,
            max_quota_scope_size=data.max_quota_scope_size,
            max_network_count=data.max_network_count,
        )

    def build_project_updater(
        self, request: UpdateProjectResourcePolicyRequest, policy_name: str
    ) -> Updater[ProjectResourcePolicyRow]:
        max_vfolder_count: OptionalState[int] = OptionalState.nop()
        max_quota_scope_size: OptionalState[int] = OptionalState.nop()
        max_network_count: OptionalState[int] = OptionalState.nop()

        if not isinstance(request.max_vfolder_count, type(SENTINEL)):
            max_vfolder_count = OptionalState.update(request.max_vfolder_count)
        if not isinstance(request.max_quota_scope_size, type(SENTINEL)):
            max_quota_scope_size = OptionalState.update(request.max_quota_scope_size)
        if not isinstance(request.max_network_count, type(SENTINEL)):
            max_network_count = OptionalState.update(request.max_network_count)

        updater_spec = ProjectResourcePolicyUpdaterSpec(
            max_vfolder_count=max_vfolder_count,
            max_quota_scope_size=max_quota_scope_size,
            max_network_count=max_network_count,
        )
        return Updater(spec=updater_spec, pk_value=policy_name)

    def build_project_querier(self, request: SearchProjectResourcePoliciesRequest) -> BatchQuerier:
        conditions = self._convert_project_filter(request.filter) if request.filter else []
        orders = [self._convert_project_order(o) for o in request.order] if request.order else []
        pagination = OffsetPagination(limit=request.limit, offset=request.offset)
        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def _convert_project_filter(self, filter: ProjectResourcePolicyFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if filter.name is not None:
            condition = self.convert_string_filter(
                filter.name,
                contains_factory=ProjectResourcePolicyConditions.by_name_contains,
                equals_factory=ProjectResourcePolicyConditions.by_name_equals,
                starts_with_factory=ProjectResourcePolicyConditions.by_name_starts_with,
                ends_with_factory=ProjectResourcePolicyConditions.by_name_ends_with,
            )
            if condition is not None:
                conditions.append(condition)
        return conditions

    def _convert_project_order(self, order: ProjectResourcePolicyOrder) -> QueryOrder:
        ascending = order.direction == OrderDirection.ASC
        if order.field == ProjectResourcePolicyOrderField.NAME:
            return ProjectResourcePolicyOrders.name(ascending=ascending)
        if order.field == ProjectResourcePolicyOrderField.CREATED_AT:
            return ProjectResourcePolicyOrders.created_at(ascending=ascending)
        raise ValueError(f"Unknown order field: {order.field}")
