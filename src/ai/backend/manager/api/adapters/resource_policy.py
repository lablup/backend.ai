"""Resource policy adapter bridging v2 DTOs and Processors.

Unified adapter handling keypair, user, and project resource policies.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from ai.backend.common.api_handlers import Sentinel
from ai.backend.common.contexts.user import current_user
from ai.backend.common.dto.manager.v2.common import (
    ResourceSlotEntryInfo,
    ResourceSlotEntryInput,
    VFolderHostPermissionEntryInfo,
    VFolderHostPermissionEntryInput,
)
from ai.backend.common.dto.manager.v2.resource_policy.request import (
    AdminSearchKeypairResourcePoliciesInput,
    AdminSearchProjectResourcePoliciesInput,
    AdminSearchUserResourcePoliciesInput,
    CreateKeypairResourcePolicyInput,
    CreateProjectResourcePolicyInput,
    CreateUserResourcePolicyInput,
    DeleteKeypairResourcePolicyInput,
    DeleteProjectResourcePolicyInput,
    DeleteUserResourcePolicyInput,
    KeypairResourcePolicyFilter,
    KeypairResourcePolicyOrder,
    ProjectResourcePolicyFilter,
    ProjectResourcePolicyOrder,
    UpdateKeypairResourcePolicyInput,
    UpdateProjectResourcePolicyInput,
    UpdateUserResourcePolicyInput,
    UserResourcePolicyFilter,
    UserResourcePolicyOrder,
)
from ai.backend.common.dto.manager.v2.resource_policy.response import (
    CreateKeypairResourcePolicyPayload,
    CreateProjectResourcePolicyPayload,
    CreateUserResourcePolicyPayload,
    DeleteKeypairResourcePolicyPayload,
    DeleteProjectResourcePolicyPayload,
    DeleteUserResourcePolicyPayload,
    KeypairResourcePolicyNode,
    ProjectResourcePolicyNode,
    SearchKeypairResourcePoliciesPayload,
    SearchProjectResourcePoliciesPayload,
    SearchUserResourcePoliciesPayload,
    UpdateKeypairResourcePolicyPayload,
    UpdateProjectResourcePolicyPayload,
    UpdateUserResourcePolicyPayload,
    UserResourcePolicyNode,
)
from ai.backend.common.dto.manager.v2.resource_policy.types import (
    KeypairResourcePolicyOrderField,
    OrderDirection,
    ProjectResourcePolicyOrderField,
    UserResourcePolicyOrderField,
)
from ai.backend.common.exception import UnreachableError
from ai.backend.common.types import ResourceSlot, VFolderHostPermission
from ai.backend.manager.api.adapters.pagination import PaginationSpec
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
from ai.backend.manager.models.resource_policy.conditions import (
    KeypairResourcePolicyConditions,
    ProjectResourcePolicyConditions,
    UserResourcePolicyConditions,
)
from ai.backend.manager.models.resource_policy.orders import (
    KeypairResourcePolicyOrders,
    ProjectResourcePolicyOrders,
    UserResourcePolicyOrders,
)
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.keypair_resource_policy.creators import (
    KeyPairResourcePolicyCreatorSpec,
)
from ai.backend.manager.repositories.keypair_resource_policy.updaters import (
    KeyPairResourcePolicyUpdaterSpec,
)
from ai.backend.manager.repositories.project_resource_policy.creators import (
    ProjectResourcePolicyCreatorSpec,
)
from ai.backend.manager.repositories.project_resource_policy.updaters import (
    ProjectResourcePolicyUpdaterSpec,
)
from ai.backend.manager.repositories.user_resource_policy.creators import (
    UserResourcePolicyCreatorSpec,
)
from ai.backend.manager.repositories.user_resource_policy.updaters import (
    UserResourcePolicyUpdaterSpec,
)
from ai.backend.manager.services.keypair_resource_policy.actions.create_keypair_resource_policy import (
    CreateKeyPairResourcePolicyAction,
)
from ai.backend.manager.services.keypair_resource_policy.actions.delete_keypair_resource_policy import (
    DeleteKeyPairResourcePolicyAction,
)
from ai.backend.manager.services.keypair_resource_policy.actions.get_keypair_resource_policy import (
    GetKeypairResourcePolicyAction,
)
from ai.backend.manager.services.keypair_resource_policy.actions.get_my_keypair_resource_policy import (
    GetMyKeypairResourcePolicyAction,
)
from ai.backend.manager.services.keypair_resource_policy.actions.modify_keypair_resource_policy import (
    ModifyKeyPairResourcePolicyAction,
)
from ai.backend.manager.services.keypair_resource_policy.actions.search_keypair_resource_policies import (
    SearchKeypairResourcePoliciesAction,
)
from ai.backend.manager.services.project_resource_policy.actions.create_project_resource_policy import (
    CreateProjectResourcePolicyAction,
)
from ai.backend.manager.services.project_resource_policy.actions.delete_project_resource_policy import (
    DeleteProjectResourcePolicyAction,
)
from ai.backend.manager.services.project_resource_policy.actions.get_project_resource_policy import (
    GetProjectResourcePolicyAction,
)
from ai.backend.manager.services.project_resource_policy.actions.modify_project_resource_policy import (
    ModifyProjectResourcePolicyAction,
)
from ai.backend.manager.services.project_resource_policy.actions.search_project_resource_policies import (
    SearchProjectResourcePoliciesAction,
)
from ai.backend.manager.services.user_resource_policy.actions.create_user_resource_policy import (
    CreateUserResourcePolicyAction,
)
from ai.backend.manager.services.user_resource_policy.actions.delete_user_resource_policy import (
    DeleteUserResourcePolicyAction,
)
from ai.backend.manager.services.user_resource_policy.actions.get_my_user_resource_policy import (
    GetMyUserResourcePolicyAction,
)
from ai.backend.manager.services.user_resource_policy.actions.get_user_resource_policy import (
    GetUserResourcePolicyAction,
)
from ai.backend.manager.services.user_resource_policy.actions.modify_user_resource_policy import (
    ModifyUserResourcePolicyAction,
)
from ai.backend.manager.services.user_resource_policy.actions.search_user_resource_policies import (
    SearchUserResourcePoliciesAction,
)
from ai.backend.manager.types import OptionalState, TriState

from .base import BaseAdapter

_KEYPAIR_RP_PAGINATION_SPEC = PaginationSpec(
    forward_order=KeypairResourcePolicyOrders.created_at(ascending=False),
    backward_order=KeypairResourcePolicyOrders.created_at(ascending=True),
    forward_condition_factory=KeypairResourcePolicyConditions.by_cursor_forward,
    backward_condition_factory=KeypairResourcePolicyConditions.by_cursor_backward,
    tiebreaker_order=KeyPairResourcePolicyRow.name.asc(),
)

_USER_RP_PAGINATION_SPEC = PaginationSpec(
    forward_order=UserResourcePolicyOrders.created_at(ascending=False),
    backward_order=UserResourcePolicyOrders.created_at(ascending=True),
    forward_condition_factory=UserResourcePolicyConditions.by_cursor_forward,
    backward_condition_factory=UserResourcePolicyConditions.by_cursor_backward,
    tiebreaker_order=UserResourcePolicyRow.name.asc(),
)

_PROJECT_RP_PAGINATION_SPEC = PaginationSpec(
    forward_order=ProjectResourcePolicyOrders.created_at(ascending=False),
    backward_order=ProjectResourcePolicyOrders.created_at(ascending=True),
    forward_condition_factory=ProjectResourcePolicyConditions.by_cursor_forward,
    backward_condition_factory=ProjectResourcePolicyConditions.by_cursor_backward,
    tiebreaker_order=ProjectResourcePolicyRow.name.asc(),
)


class ResourcePolicyAdapter(BaseAdapter):
    """Unified adapter for keypair, user, and project resource policy operations."""

    # ── Keypair Resource Policy ──

    async def admin_get_keypair_resource_policy(self, name: str) -> KeypairResourcePolicyNode:
        result = await self._processors.keypair_resource_policy.get_keypair_resource_policy.wait_for_complete(
            GetKeypairResourcePolicyAction(name=name)
        )
        return self._keypair_policy_data_to_node(result.data)

    async def admin_search_keypair_resource_policies(
        self,
        input: AdminSearchKeypairResourcePoliciesInput,
    ) -> SearchKeypairResourcePoliciesPayload:
        conditions = self._convert_keypair_filter(input.filter) if input.filter else []
        orders = self._resolve_keypair_orders(input.order) if input.order else []
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_KEYPAIR_RP_PAGINATION_SPEC,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        result = await self._processors.keypair_resource_policy.search_keypair_resource_policies.wait_for_complete(
            SearchKeypairResourcePoliciesAction(querier=querier)
        )
        items = [self._keypair_policy_data_to_node(d) for d in result.items]
        return SearchKeypairResourcePoliciesPayload(items=items, total_count=result.total_count)

    async def admin_create_keypair_resource_policy(
        self, input: CreateKeypairResourcePolicyInput
    ) -> CreateKeypairResourcePolicyPayload:
        spec = KeyPairResourcePolicyCreatorSpec(
            name=input.name,
            default_for_unspecified=input.default_for_unspecified,
            total_resource_slots=self._entries_to_resource_slot(input.total_resource_slots),
            max_session_lifetime=input.max_session_lifetime,
            max_concurrent_sessions=input.max_concurrent_sessions,
            max_pending_session_count=input.max_pending_session_count,
            max_pending_session_resource_slots=(
                self._entries_to_resource_slot(input.max_pending_session_resource_slots)
                if input.max_pending_session_resource_slots is not None
                else None
            ),
            max_concurrent_sftp_sessions=input.max_concurrent_sftp_sessions,
            max_containers_per_session=input.max_containers_per_session,
            idle_timeout=input.idle_timeout,
            allowed_vfolder_hosts=self._entries_to_vfolder_hosts(input.allowed_vfolder_hosts),
            max_quota_scope_size=None,
            max_vfolder_count=None,
            max_vfolder_size=None,
        )
        result = await self._processors.keypair_resource_policy.create_keypair_resource_policy.wait_for_complete(
            CreateKeyPairResourcePolicyAction(creator=Creator(spec=spec))
        )
        return CreateKeypairResourcePolicyPayload(
            keypair_resource_policy=self._keypair_policy_data_to_node(
                result.keypair_resource_policy
            )
        )

    async def admin_update_keypair_resource_policy(
        self, name: str, input: UpdateKeypairResourcePolicyInput
    ) -> UpdateKeypairResourcePolicyPayload:
        spec = KeyPairResourcePolicyUpdaterSpec(
            default_for_unspecified=(
                OptionalState.update(input.default_for_unspecified)
                if input.default_for_unspecified is not None
                else OptionalState.nop()
            ),
            total_resource_slots=(
                OptionalState.nop()
                if isinstance(input.total_resource_slots, Sentinel)
                else OptionalState.update(
                    self._entries_to_resource_slot(input.total_resource_slots)
                )
                if input.total_resource_slots is not None
                else OptionalState.nop()
            ),
            max_session_lifetime=(
                OptionalState.update(input.max_session_lifetime)
                if input.max_session_lifetime is not None
                else OptionalState.nop()
            ),
            max_concurrent_sessions=(
                OptionalState.update(input.max_concurrent_sessions)
                if input.max_concurrent_sessions is not None
                else OptionalState.nop()
            ),
            max_pending_session_count=(
                TriState.nop()
                if isinstance(input.max_pending_session_count, Sentinel)
                else TriState.nullify()
                if input.max_pending_session_count is None
                else TriState.update(input.max_pending_session_count)
            ),
            max_pending_session_resource_slots=(
                TriState.nop()
                if isinstance(input.max_pending_session_resource_slots, Sentinel)
                else TriState.nullify()
                if input.max_pending_session_resource_slots is None
                else TriState.update(
                    self._entries_to_resource_slot_dict(input.max_pending_session_resource_slots)
                )
            ),
            max_concurrent_sftp_sessions=(
                OptionalState.update(input.max_concurrent_sftp_sessions)
                if input.max_concurrent_sftp_sessions is not None
                else OptionalState.nop()
            ),
            max_containers_per_session=(
                OptionalState.update(input.max_containers_per_session)
                if input.max_containers_per_session is not None
                else OptionalState.nop()
            ),
            idle_timeout=(
                OptionalState.update(input.idle_timeout)
                if input.idle_timeout is not None
                else OptionalState.nop()
            ),
            allowed_vfolder_hosts=(
                OptionalState.nop()
                if isinstance(input.allowed_vfolder_hosts, Sentinel)
                else OptionalState.update(
                    self._entries_to_vfolder_hosts(input.allowed_vfolder_hosts)
                )
                if input.allowed_vfolder_hosts is not None
                else OptionalState.nop()
            ),
        )
        updater: Updater[KeyPairResourcePolicyRow] = Updater(spec=spec, pk_value=name)
        result = await self._processors.keypair_resource_policy.modify_keypair_resource_policy.wait_for_complete(
            ModifyKeyPairResourcePolicyAction(name=name, updater=updater)
        )
        return UpdateKeypairResourcePolicyPayload(
            keypair_resource_policy=self._keypair_policy_data_to_node(
                result.keypair_resource_policy
            )
        )

    async def admin_delete_keypair_resource_policy(
        self, input: DeleteKeypairResourcePolicyInput
    ) -> DeleteKeypairResourcePolicyPayload:
        await self._processors.keypair_resource_policy.delete_keypair_resource_policy.wait_for_complete(
            DeleteKeyPairResourcePolicyAction(name=input.name)
        )
        return DeleteKeypairResourcePolicyPayload(name=input.name)

    async def get_my_keypair_resource_policy(self) -> KeypairResourcePolicyNode:
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available.")
        result = await self._processors.keypair_resource_policy.get_my_keypair_resource_policy.wait_for_complete(
            GetMyKeypairResourcePolicyAction(user_id=me.user_id)
        )
        return self._keypair_policy_data_to_node(result.data)

    # ── User Resource Policy ──

    async def admin_get_user_resource_policy(self, name: str) -> UserResourcePolicyNode:
        result = (
            await self._processors.user_resource_policy.get_user_resource_policy.wait_for_complete(
                GetUserResourcePolicyAction(name=name)
            )
        )
        return self._user_policy_data_to_node(result.data)

    async def admin_search_user_resource_policies(
        self,
        input: AdminSearchUserResourcePoliciesInput,
    ) -> SearchUserResourcePoliciesPayload:
        conditions = self._convert_user_filter(input.filter) if input.filter else []
        orders = self._resolve_user_orders(input.order) if input.order else []
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_USER_RP_PAGINATION_SPEC,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        result = await self._processors.user_resource_policy.search_user_resource_policies.wait_for_complete(
            SearchUserResourcePoliciesAction(querier=querier)
        )
        items = [self._user_policy_data_to_node(d) for d in result.items]
        return SearchUserResourcePoliciesPayload(items=items, total_count=result.total_count)

    async def admin_create_user_resource_policy(
        self, input: CreateUserResourcePolicyInput
    ) -> CreateUserResourcePolicyPayload:
        spec = UserResourcePolicyCreatorSpec(
            name=input.name,
            max_vfolder_count=input.max_vfolder_count,
            max_quota_scope_size=input.max_quota_scope_size,
            max_session_count_per_model_session=input.max_session_count_per_model_session,
            max_customized_image_count=input.max_customized_image_count,
        )
        result = await self._processors.user_resource_policy.create_user_resource_policy.wait_for_complete(
            CreateUserResourcePolicyAction(creator=Creator(spec=spec))
        )
        return CreateUserResourcePolicyPayload(
            user_resource_policy=self._user_policy_data_to_node(result.user_resource_policy)
        )

    async def admin_update_user_resource_policy(
        self, name: str, input: UpdateUserResourcePolicyInput
    ) -> UpdateUserResourcePolicyPayload:
        spec = UserResourcePolicyUpdaterSpec(
            max_vfolder_count=(
                OptionalState.nop()
                if isinstance(input.max_vfolder_count, Sentinel)
                else OptionalState.update(input.max_vfolder_count)
                if input.max_vfolder_count is not None
                else OptionalState.nop()
            ),
            max_quota_scope_size=(
                OptionalState.nop()
                if isinstance(input.max_quota_scope_size, Sentinel)
                else OptionalState.update(input.max_quota_scope_size)
                if input.max_quota_scope_size is not None
                else OptionalState.nop()
            ),
            max_session_count_per_model_session=(
                OptionalState.update(input.max_session_count_per_model_session)
                if input.max_session_count_per_model_session is not None
                else OptionalState.nop()
            ),
            max_customized_image_count=(
                OptionalState.update(input.max_customized_image_count)
                if input.max_customized_image_count is not None
                else OptionalState.nop()
            ),
        )
        updater: Updater[UserResourcePolicyRow] = Updater(spec=spec, pk_value=name)
        result = await self._processors.user_resource_policy.modify_user_resource_policy.wait_for_complete(
            ModifyUserResourcePolicyAction(name=name, updater=updater)
        )
        return UpdateUserResourcePolicyPayload(
            user_resource_policy=self._user_policy_data_to_node(result.user_resource_policy)
        )

    async def admin_delete_user_resource_policy(
        self, input: DeleteUserResourcePolicyInput
    ) -> DeleteUserResourcePolicyPayload:
        await self._processors.user_resource_policy.delete_user_resource_policy.wait_for_complete(
            DeleteUserResourcePolicyAction(name=input.name)
        )
        return DeleteUserResourcePolicyPayload(name=input.name)

    async def get_my_user_resource_policy(self) -> UserResourcePolicyNode:
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available.")
        result = await self._processors.user_resource_policy.get_my_user_resource_policy.wait_for_complete(
            GetMyUserResourcePolicyAction(user_id=me.user_id)
        )
        return self._user_policy_data_to_node(result.data)

    # ── Project Resource Policy ──

    async def admin_get_project_resource_policy(self, name: str) -> ProjectResourcePolicyNode:
        result = await self._processors.project_resource_policy.get_project_resource_policy.wait_for_complete(
            GetProjectResourcePolicyAction(name=name)
        )
        return self._project_policy_data_to_node(result.data)

    async def admin_search_project_resource_policies(
        self,
        input: AdminSearchProjectResourcePoliciesInput,
    ) -> SearchProjectResourcePoliciesPayload:
        conditions = self._convert_project_filter(input.filter) if input.filter else []
        orders = self._resolve_project_orders(input.order) if input.order else []
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_PROJECT_RP_PAGINATION_SPEC,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        result = await self._processors.project_resource_policy.search_project_resource_policies.wait_for_complete(
            SearchProjectResourcePoliciesAction(querier=querier)
        )
        items = [self._project_policy_data_to_node(d) for d in result.items]
        return SearchProjectResourcePoliciesPayload(items=items, total_count=result.total_count)

    async def admin_create_project_resource_policy(
        self, input: CreateProjectResourcePolicyInput
    ) -> CreateProjectResourcePolicyPayload:
        spec = ProjectResourcePolicyCreatorSpec(
            name=input.name,
            max_vfolder_count=input.max_vfolder_count,
            max_quota_scope_size=input.max_quota_scope_size,
            max_network_count=input.max_network_count,
        )
        result = await self._processors.project_resource_policy.create_project_resource_policy.wait_for_complete(
            CreateProjectResourcePolicyAction(creator=Creator(spec=spec))
        )
        return CreateProjectResourcePolicyPayload(
            project_resource_policy=self._project_policy_data_to_node(
                result.project_resource_policy
            )
        )

    async def admin_update_project_resource_policy(
        self, name: str, input: UpdateProjectResourcePolicyInput
    ) -> UpdateProjectResourcePolicyPayload:
        spec = ProjectResourcePolicyUpdaterSpec(
            max_vfolder_count=(
                OptionalState.nop()
                if isinstance(input.max_vfolder_count, Sentinel)
                else OptionalState.update(input.max_vfolder_count)
                if input.max_vfolder_count is not None
                else OptionalState.nop()
            ),
            max_quota_scope_size=(
                OptionalState.nop()
                if isinstance(input.max_quota_scope_size, Sentinel)
                else OptionalState.update(input.max_quota_scope_size)
                if input.max_quota_scope_size is not None
                else OptionalState.nop()
            ),
            max_network_count=(
                OptionalState.update(input.max_network_count)
                if input.max_network_count is not None
                else OptionalState.nop()
            ),
        )
        updater: Updater[ProjectResourcePolicyRow] = Updater(spec=spec, pk_value=name)
        result = await self._processors.project_resource_policy.modify_project_resource_policy.wait_for_complete(
            ModifyProjectResourcePolicyAction(name=name, updater=updater)
        )
        return UpdateProjectResourcePolicyPayload(
            project_resource_policy=self._project_policy_data_to_node(
                result.project_resource_policy
            )
        )

    async def admin_delete_project_resource_policy(
        self, input: DeleteProjectResourcePolicyInput
    ) -> DeleteProjectResourcePolicyPayload:
        await self._processors.project_resource_policy.delete_project_resource_policy.wait_for_complete(
            DeleteProjectResourcePolicyAction(name=input.name)
        )
        return DeleteProjectResourcePolicyPayload(name=input.name)

    # ── Conversion helpers ──

    @staticmethod
    def _entries_to_resource_slot(
        entries: list[ResourceSlotEntryInput],
    ) -> ResourceSlot:
        return ResourceSlot({e.resource_type: Decimal(e.quantity) for e in entries})

    @staticmethod
    def _entries_to_resource_slot_dict(
        entries: list[ResourceSlotEntryInput],
    ) -> dict[str, Any]:
        return {e.resource_type: str(Decimal(e.quantity)) for e in entries}

    @staticmethod
    def _resource_slot_to_entries(
        slot: ResourceSlot,
    ) -> list[ResourceSlotEntryInfo]:
        return [ResourceSlotEntryInfo(resource_type=k, quantity=v) for k, v in slot.items()]

    @staticmethod
    def _entries_to_vfolder_hosts(
        entries: list[VFolderHostPermissionEntryInput],
    ) -> dict[str, Any]:
        return {e.host: {VFolderHostPermission(p) for p in e.permissions} for e in entries}

    @staticmethod
    def _vfolder_hosts_to_entries(
        hosts: dict[str, Any],
    ) -> list[VFolderHostPermissionEntryInfo]:
        return [
            VFolderHostPermissionEntryInfo(
                host=h,
                permissions=[p.value if hasattr(p, "value") else str(p) for p in perms],
            )
            for h, perms in hosts.items()
        ]

    @classmethod
    def _keypair_policy_data_to_node(
        cls, data: KeyPairResourcePolicyData
    ) -> KeypairResourcePolicyNode:
        return KeypairResourcePolicyNode(
            id=data.name,
            name=data.name,
            created_at=data.created_at,
            default_for_unspecified=data.default_for_unspecified,
            total_resource_slots=cls._resource_slot_to_entries(data.total_resource_slots),
            max_session_lifetime=data.max_session_lifetime,
            max_concurrent_sessions=data.max_concurrent_sessions,
            max_pending_session_count=data.max_pending_session_count,
            max_pending_session_resource_slots=(
                cls._resource_slot_to_entries(data.max_pending_session_resource_slots)
                if data.max_pending_session_resource_slots is not None
                else None
            ),
            max_concurrent_sftp_sessions=data.max_concurrent_sftp_sessions,
            max_containers_per_session=data.max_containers_per_session,
            idle_timeout=data.idle_timeout,
            allowed_vfolder_hosts=cls._vfolder_hosts_to_entries(data.allowed_vfolder_hosts),
        )

    @staticmethod
    def _user_policy_data_to_node(
        data: UserResourcePolicyData,
    ) -> UserResourcePolicyNode:
        return UserResourcePolicyNode(
            id=data.name,
            name=data.name,
            max_vfolder_count=data.max_vfolder_count,
            max_quota_scope_size=data.max_quota_scope_size,
            max_session_count_per_model_session=data.max_session_count_per_model_session,
            max_customized_image_count=data.max_customized_image_count,
        )

    @staticmethod
    def _project_policy_data_to_node(
        data: ProjectResourcePolicyData,
    ) -> ProjectResourcePolicyNode:
        return ProjectResourcePolicyNode(
            id=data.name,
            name=data.name,
            max_vfolder_count=data.max_vfolder_count,
            max_quota_scope_size=data.max_quota_scope_size,
            max_network_count=data.max_network_count,
        )

    # ── Filter converters ──

    def _convert_keypair_filter(self, filter: KeypairResourcePolicyFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if filter.name is not None:
            cond = self.convert_string_filter(
                filter.name,
                contains_factory=KeypairResourcePolicyConditions.by_name_contains,
                equals_factory=KeypairResourcePolicyConditions.by_name_equals,
                starts_with_factory=KeypairResourcePolicyConditions.by_name_starts_with,
                ends_with_factory=KeypairResourcePolicyConditions.by_name_ends_with,
            )
            if cond is not None:
                conditions.append(cond)
        if filter.created_at is not None:
            cond = filter.created_at.build_query_condition(
                before_factory=KeypairResourcePolicyConditions.by_created_at_before,
                after_factory=KeypairResourcePolicyConditions.by_created_at_after,
                equals_factory=KeypairResourcePolicyConditions.by_created_at_equals,
            )
            if cond is not None:
                conditions.append(cond)
        if filter.max_session_lifetime is not None:
            cond = self.convert_int_filter(
                filter.max_session_lifetime,
                KeypairResourcePolicyConditions.by_max_session_lifetime,
            )
            if cond is not None:
                conditions.append(cond)
        if filter.max_concurrent_sessions is not None:
            cond = self.convert_int_filter(
                filter.max_concurrent_sessions,
                KeypairResourcePolicyConditions.by_max_concurrent_sessions,
            )
            if cond is not None:
                conditions.append(cond)
        if filter.max_containers_per_session is not None:
            cond = self.convert_int_filter(
                filter.max_containers_per_session,
                KeypairResourcePolicyConditions.by_max_containers_per_session,
            )
            if cond is not None:
                conditions.append(cond)
        if filter.idle_timeout is not None:
            cond = self.convert_int_filter(
                filter.idle_timeout,
                KeypairResourcePolicyConditions.by_idle_timeout,
            )
            if cond is not None:
                conditions.append(cond)
        if filter.max_concurrent_sftp_sessions is not None:
            cond = self.convert_int_filter(
                filter.max_concurrent_sftp_sessions,
                KeypairResourcePolicyConditions.by_max_concurrent_sftp_sessions,
            )
            if cond is not None:
                conditions.append(cond)
        if filter.max_pending_session_count is not None:
            cond = self.convert_int_filter(
                filter.max_pending_session_count,
                KeypairResourcePolicyConditions.by_max_pending_session_count,
            )
            if cond is not None:
                conditions.append(cond)
        return conditions

    def _convert_user_filter(self, filter: UserResourcePolicyFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if filter.name is not None:
            cond = self.convert_string_filter(
                filter.name,
                contains_factory=UserResourcePolicyConditions.by_name_contains,
                equals_factory=UserResourcePolicyConditions.by_name_equals,
                starts_with_factory=UserResourcePolicyConditions.by_name_starts_with,
                ends_with_factory=UserResourcePolicyConditions.by_name_ends_with,
            )
            if cond is not None:
                conditions.append(cond)
        if filter.created_at is not None:
            cond = filter.created_at.build_query_condition(
                before_factory=UserResourcePolicyConditions.by_created_at_before,
                after_factory=UserResourcePolicyConditions.by_created_at_after,
                equals_factory=UserResourcePolicyConditions.by_created_at_equals,
            )
            if cond is not None:
                conditions.append(cond)
        if filter.max_vfolder_count is not None:
            cond = self.convert_int_filter(
                filter.max_vfolder_count,
                UserResourcePolicyConditions.by_max_vfolder_count,
            )
            if cond is not None:
                conditions.append(cond)
        if filter.max_quota_scope_size is not None:
            cond = self.convert_int_filter(
                filter.max_quota_scope_size,
                UserResourcePolicyConditions.by_max_quota_scope_size,
            )
            if cond is not None:
                conditions.append(cond)
        if filter.max_session_count_per_model_session is not None:
            cond = self.convert_int_filter(
                filter.max_session_count_per_model_session,
                UserResourcePolicyConditions.by_max_session_count_per_model_session,
            )
            if cond is not None:
                conditions.append(cond)
        if filter.max_customized_image_count is not None:
            cond = self.convert_int_filter(
                filter.max_customized_image_count,
                UserResourcePolicyConditions.by_max_customized_image_count,
            )
            if cond is not None:
                conditions.append(cond)
        return conditions

    def _convert_project_filter(self, filter: ProjectResourcePolicyFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if filter.name is not None:
            cond = self.convert_string_filter(
                filter.name,
                contains_factory=ProjectResourcePolicyConditions.by_name_contains,
                equals_factory=ProjectResourcePolicyConditions.by_name_equals,
                starts_with_factory=ProjectResourcePolicyConditions.by_name_starts_with,
                ends_with_factory=ProjectResourcePolicyConditions.by_name_ends_with,
            )
            if cond is not None:
                conditions.append(cond)
        if filter.created_at is not None:
            cond = filter.created_at.build_query_condition(
                before_factory=ProjectResourcePolicyConditions.by_created_at_before,
                after_factory=ProjectResourcePolicyConditions.by_created_at_after,
                equals_factory=ProjectResourcePolicyConditions.by_created_at_equals,
            )
            if cond is not None:
                conditions.append(cond)
        if filter.max_vfolder_count is not None:
            cond = self.convert_int_filter(
                filter.max_vfolder_count,
                ProjectResourcePolicyConditions.by_max_vfolder_count,
            )
            if cond is not None:
                conditions.append(cond)
        if filter.max_quota_scope_size is not None:
            cond = self.convert_int_filter(
                filter.max_quota_scope_size,
                ProjectResourcePolicyConditions.by_max_quota_scope_size,
            )
            if cond is not None:
                conditions.append(cond)
        if filter.max_network_count is not None:
            cond = self.convert_int_filter(
                filter.max_network_count,
                ProjectResourcePolicyConditions.by_max_network_count,
            )
            if cond is not None:
                conditions.append(cond)
        return conditions

    # ── Order resolvers ──

    @staticmethod
    def _resolve_keypair_orders(
        order: list[KeypairResourcePolicyOrder],
    ) -> list[QueryOrder]:
        return [_resolve_keypair_order(o.field, o.direction) for o in order]

    @staticmethod
    def _resolve_user_orders(
        order: list[UserResourcePolicyOrder],
    ) -> list[QueryOrder]:
        return [_resolve_user_order(o.field, o.direction) for o in order]

    @staticmethod
    def _resolve_project_orders(
        order: list[ProjectResourcePolicyOrder],
    ) -> list[QueryOrder]:
        return [_resolve_project_order(o.field, o.direction) for o in order]


def _resolve_keypair_order(
    field: KeypairResourcePolicyOrderField, direction: OrderDirection
) -> QueryOrder:
    ascending = direction == OrderDirection.ASC
    match field:
        case KeypairResourcePolicyOrderField.NAME:
            return KeypairResourcePolicyOrders.name(ascending)
        case KeypairResourcePolicyOrderField.CREATED_AT:
            return KeypairResourcePolicyOrders.created_at(ascending)
        case KeypairResourcePolicyOrderField.MAX_SESSION_LIFETIME:
            return KeypairResourcePolicyOrders.max_session_lifetime(ascending)
        case KeypairResourcePolicyOrderField.MAX_CONCURRENT_SESSIONS:
            return KeypairResourcePolicyOrders.max_concurrent_sessions(ascending)
        case KeypairResourcePolicyOrderField.MAX_CONTAINERS_PER_SESSION:
            return KeypairResourcePolicyOrders.max_containers_per_session(ascending)
        case KeypairResourcePolicyOrderField.IDLE_TIMEOUT:
            return KeypairResourcePolicyOrders.idle_timeout(ascending)
        case KeypairResourcePolicyOrderField.MAX_CONCURRENT_SFTP_SESSIONS:
            return KeypairResourcePolicyOrders.max_concurrent_sftp_sessions(ascending)
        case KeypairResourcePolicyOrderField.MAX_PENDING_SESSION_COUNT:
            return KeypairResourcePolicyOrders.max_pending_session_count(ascending)


def _resolve_user_order(
    field: UserResourcePolicyOrderField, direction: OrderDirection
) -> QueryOrder:
    ascending = direction == OrderDirection.ASC
    match field:
        case UserResourcePolicyOrderField.NAME:
            return UserResourcePolicyOrders.name(ascending)
        case UserResourcePolicyOrderField.CREATED_AT:
            return UserResourcePolicyOrders.created_at(ascending)
        case UserResourcePolicyOrderField.MAX_VFOLDER_COUNT:
            return UserResourcePolicyOrders.max_vfolder_count(ascending)
        case UserResourcePolicyOrderField.MAX_QUOTA_SCOPE_SIZE:
            return UserResourcePolicyOrders.max_quota_scope_size(ascending)
        case UserResourcePolicyOrderField.MAX_SESSION_COUNT_PER_MODEL_SESSION:
            return UserResourcePolicyOrders.max_session_count_per_model_session(ascending)
        case UserResourcePolicyOrderField.MAX_CUSTOMIZED_IMAGE_COUNT:
            return UserResourcePolicyOrders.max_customized_image_count(ascending)


def _resolve_project_order(
    field: ProjectResourcePolicyOrderField, direction: OrderDirection
) -> QueryOrder:
    ascending = direction == OrderDirection.ASC
    match field:
        case ProjectResourcePolicyOrderField.NAME:
            return ProjectResourcePolicyOrders.name(ascending)
        case ProjectResourcePolicyOrderField.CREATED_AT:
            return ProjectResourcePolicyOrders.created_at(ascending)
        case ProjectResourcePolicyOrderField.MAX_VFOLDER_COUNT:
            return ProjectResourcePolicyOrders.max_vfolder_count(ascending)
        case ProjectResourcePolicyOrderField.MAX_QUOTA_SCOPE_SIZE:
            return ProjectResourcePolicyOrders.max_quota_scope_size(ascending)
        case ProjectResourcePolicyOrderField.MAX_NETWORK_COUNT:
            return ProjectResourcePolicyOrders.max_network_count(ascending)
