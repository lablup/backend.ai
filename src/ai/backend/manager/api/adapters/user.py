"""User domain adapter - Pydantic-in/Pydantic-out transport layer."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import TYPE_CHECKING, cast
from uuid import UUID

from ai.backend.common.api_handlers import Sentinel
from ai.backend.common.contexts.user import current_user
from ai.backend.common.data.filter_specs import UUIDInMatchSpec
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.data.user.types import UserRole as DataUserRole
from ai.backend.common.dto.manager.pagination import PaginationInfo
from ai.backend.common.dto.manager.v2.keypair import (
    KeypairFilter,
    KeypairNode,
    KeypairOrderBy,
    KeypairOrderField,
    SearchMyKeypairsRequest,
)
from ai.backend.common.dto.manager.v2.keypair.response import (
    IssueMyKeypairPayload,
    RevokeMyKeypairPayload,
    SwitchMyMainAccessKeyPayload,
    UpdateMyKeypairPayload,
)
from ai.backend.common.dto.manager.v2.user.request import (
    AdminSearchUsersInput,
    CreateUserInput,
    DeleteUserInput,
    PurgeUserInput,
    SearchUsersRequest,
    UpdateUserInput,
    UserFilter,
    UserOrder,
)
from ai.backend.common.dto.manager.v2.user.response import (
    AdminSearchUsersPayload,
    BulkCreateUsersPayload,
    BulkCreateUserV2Error,
    BulkPurgeUsersPayload,
    BulkPurgeUserV2Error,
    BulkUpdateUsersPayload,
    BulkUpdateUserV2Error,
    CreateUserPayload,
    DeleteUserPayload,
    EntityTimestamps,
    PurgeUserPayload,
    SearchUsersPayload,
    UpdateMyAllowedClientIPPayload,
    UpdateUserPayload,
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
from ai.backend.common.exception import UnreachableError
from ai.backend.manager.data.common.types import SearchResult
from ai.backend.manager.data.keypair.types import KeyPairData
from ai.backend.manager.data.user.types import UserData, UserStatus
from ai.backend.manager.data.user.types import UserStatus as DataUserStatus
from ai.backend.manager.models.domain.conditions import DomainConditions
from ai.backend.manager.models.group.conditions import GroupConditions
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.keypair.conditions import KeypairConditions, KeypairOrders
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.user.conditions import UserConditions
from ai.backend.manager.models.user.orders import UserOrders
from ai.backend.manager.models.user.row import UserRole as UserRoleModel
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    NoPagination,
    OffsetPagination,
    QueryCondition,
    QueryOrder,
    combine_conditions_or,
    negate_conditions,
)
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.keypair.types import UserKeypairSearchScope
from ai.backend.manager.repositories.keypair.updaters import KeyPairUpdaterSpec
from ai.backend.manager.repositories.user.creators import UserCreatorSpec
from ai.backend.manager.repositories.user.types import (
    DomainUserSearchScope,
    ProjectUserSearchScope,
    RoleUserSearchScope,
)
from ai.backend.manager.repositories.user.updaters import UserUpdaterSpec
from ai.backend.manager.services.user.actions.create_user import (
    BulkCreateUserAction,
    CreateUserAction,
)
from ai.backend.manager.services.user.actions.delete_user import DeleteUserByIdAction
from ai.backend.manager.services.user.actions.get_user import GetUserAction
from ai.backend.manager.services.user.actions.keypair_ops import (
    IssueMyKeypairAction,
    RevokeMyKeypairAction,
    SearchMyKeypairsAction,
    SwitchMyMainAccessKeyAction,
    UpdateMyKeypairAction,
)
from ai.backend.manager.services.user.actions.modify_user import (
    BulkModifyUserAction,
    ModifyUserAction,
    ModifyUserByIdAction,
)
from ai.backend.manager.services.user.actions.purge_user import (
    BulkPurgeUserAction,
    PurgeUserByIdAction,
)
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
from ai.backend.manager.types import OptionalState, TriState

if TYPE_CHECKING:
    from ai.backend.manager.config.unified import AuthConfig
    from ai.backend.manager.services.processors import Processors

from .base import BaseAdapter
from .pagination import PaginationSpec

_USER_PAGINATION_SPEC = PaginationSpec(
    forward_order=UserOrders.created_at(ascending=False),
    backward_order=UserOrders.created_at(ascending=True),
    forward_condition_factory=UserConditions.by_cursor_forward,
    backward_condition_factory=UserConditions.by_cursor_backward,
    tiebreaker_order=UserRow.uuid.asc(),
)

_KEYPAIR_PAGINATION_SPEC = PaginationSpec(
    forward_order=KeypairOrders.created_at(ascending=False),
    backward_order=KeypairOrders.created_at(ascending=True),
    forward_condition_factory=KeypairConditions.by_cursor_forward,
    backward_condition_factory=KeypairConditions.by_cursor_backward,
    tiebreaker_order=KeyPairRow.access_key.asc(),
)


class UserAdapter(BaseAdapter):
    """Adapter for user domain operations."""

    def __init__(self, processors: Processors, auth_config: AuthConfig) -> None:
        super().__init__(processors)
        self._auth_config = auth_config

    # ------------------------------------------------------------------ batch load (DataLoader)

    async def batch_load_by_ids(self, user_ids: Sequence[uuid.UUID]) -> list[UserNode | None]:
        """Batch load users by UUID for DataLoader use.

        Returns UserNode DTOs in the same order as the input user_ids list.
        """
        if not user_ids:
            return []
        querier = BatchQuerier(
            pagination=NoPagination(),
            conditions=[
                UserConditions.by_uuid_in(UUIDInMatchSpec(values=list(user_ids), negated=False))
            ],
        )
        action_result = await self._processors.user.search_users.wait_for_complete(
            SearchUsersAction(querier=querier)
        )
        user_map = {user.uuid: self._user_data_to_node(user) for user in action_result.users}
        return [user_map.get(user_id) for user_id in user_ids]

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

    # ------------------------------------------------------------------ single CRUD

    async def create_user(self, input: CreateUserInput) -> CreateUserPayload:
        """Create a single user."""
        password_info = PasswordInfo(
            password=input.password,
            algorithm=self._auth_config.password_hash_algorithm,
            rounds=self._auth_config.password_hash_rounds,
            salt_size=self._auth_config.password_hash_salt_size,
        )
        spec = UserCreatorSpec(
            email=input.email,
            username=input.username,
            password=password_info,
            need_password_change=input.need_password_change,
            domain_name=input.domain_name,
            full_name=input.full_name,
            description=input.description,
            status=UserStatus(input.status),
            role=str(UserRoleModel(input.role)),
            allowed_client_ip=input.allowed_client_ip,
            totp_activated=input.totp_activated,
            resource_policy=input.resource_policy,
            sudo_session_enabled=input.sudo_session_enabled,
            container_uid=input.container_uid,
            container_main_gid=input.container_main_gid,
            container_gids=input.container_gids,
        )
        group_ids = [str(gid) for gid in input.group_ids] if input.group_ids else None
        result = await self._processors.user.create_user.wait_for_complete(
            CreateUserAction(creator=Creator(spec=spec), group_ids=group_ids)
        )
        return CreateUserPayload(user=self._user_data_to_node(result.data.user))

    async def modify_user_by_id(self, user_id: UUID, input: UpdateUserInput) -> UpdateUserPayload:
        """Update a user by UUID."""
        updater_spec = UserUpdaterSpec(
            username=(
                OptionalState.update(input.username)
                if input.username is not None
                else OptionalState.nop()
            ),
            password=(
                OptionalState.update(
                    PasswordInfo(
                        password=input.password,
                        algorithm=self._auth_config.password_hash_algorithm,
                        rounds=self._auth_config.password_hash_rounds,
                        salt_size=self._auth_config.password_hash_salt_size,
                    )
                )
                if input.password is not None
                else OptionalState.nop()
            ),
            need_password_change=(
                OptionalState.update(input.need_password_change)
                if input.need_password_change is not None
                else OptionalState.nop()
            ),
            full_name=(
                TriState.nop()
                if isinstance(input.full_name, Sentinel)
                else TriState.nullify()
                if input.full_name is None
                else TriState.update(input.full_name)
            ),
            description=(
                TriState.nop()
                if isinstance(input.description, Sentinel)
                else TriState.nullify()
                if input.description is None
                else TriState.update(input.description)
            ),
            status=(
                OptionalState.update(UserStatus(input.status))
                if input.status is not None
                else OptionalState.nop()
            ),
            domain_name=(
                OptionalState.update(input.domain_name)
                if input.domain_name is not None
                else OptionalState.nop()
            ),
            role=(
                OptionalState.update(UserRoleModel(input.role))
                if input.role is not None
                else OptionalState.nop()
            ),
            allowed_client_ip=(
                TriState.nop()
                if isinstance(input.allowed_client_ip, Sentinel)
                else TriState.from_graphql(input.allowed_client_ip)
            ),
            resource_policy=(
                OptionalState.update(input.resource_policy)
                if input.resource_policy is not None
                else OptionalState.nop()
            ),
            sudo_session_enabled=(
                OptionalState.update(input.sudo_session_enabled)
                if input.sudo_session_enabled is not None
                else OptionalState.nop()
            ),
            main_access_key=(
                TriState.nop()
                if isinstance(input.main_access_key, Sentinel)
                else TriState.from_graphql(input.main_access_key)
            ),
            container_uid=(
                TriState.nop()
                if isinstance(input.container_uid, Sentinel)
                else TriState.from_graphql(input.container_uid)
            ),
            container_main_gid=(
                TriState.nop()
                if isinstance(input.container_main_gid, Sentinel)
                else TriState.from_graphql(input.container_main_gid)
            ),
            container_gids=(
                TriState.nop()
                if isinstance(input.container_gids, Sentinel)
                else TriState.from_graphql(input.container_gids)
            ),
            group_ids=(
                OptionalState.nop()
                if isinstance(input.group_ids, Sentinel) or input.group_ids is None
                else OptionalState.update([str(gid) for gid in input.group_ids])
            ),
        )
        updater: Updater[UserRow] = Updater(spec=updater_spec, pk_value=user_id)
        result = await self._processors.user.modify_user_by_id.wait_for_complete(
            ModifyUserByIdAction(user_id=user_id, updater=updater)
        )
        return UpdateUserPayload(user=self._user_data_to_node(result.data))

    async def delete_user_by_id(self, input: DeleteUserInput) -> DeleteUserPayload:
        """Soft-delete a user by UUID."""
        await self._processors.user.delete_user_by_id.wait_for_complete(
            DeleteUserByIdAction(user_id=input.user_id)
        )
        return DeleteUserPayload(success=True)

    async def purge_user_by_id(
        self, input: PurgeUserInput, admin_user_id: UUID
    ) -> PurgeUserPayload:
        """Permanently purge a user by UUID."""
        await self._processors.user.purge_user_by_id.wait_for_complete(
            PurgeUserByIdAction(
                user_id=input.user_id,
                admin_user_id=admin_user_id,
                purge_shared_vfolders=(
                    OptionalState.update(input.purge_shared_vfolders)
                    if input.purge_shared_vfolders
                    else OptionalState.nop()
                ),
                delegate_endpoint_ownership=(
                    OptionalState.update(input.delegate_endpoint_ownership)
                    if input.delegate_endpoint_ownership
                    else OptionalState.nop()
                ),
            )
        )
        return PurgeUserPayload(success=True)

    # ------------------------------------------------------------------ bulk create/update/purge

    async def bulk_create_users(self, action: BulkCreateUserAction) -> BulkCreateUsersPayload:
        """Bulk-create users. Each item's transformation is the caller's responsibility."""
        result = await self._processors.user.bulk_create_users.wait_for_complete(action)
        created_users = [self._user_data_to_node(u) for u in result.data.successes]
        failed = [
            BulkCreateUserV2Error(
                index=error.index,
                username=cast(UserCreatorSpec, error.spec).username,
                email=cast(UserCreatorSpec, error.spec).email,
                message=str(error.exception),
            )
            for error in result.data.failures
        ]
        return BulkCreateUsersPayload(created_users=created_users, failed=failed)

    async def bulk_modify_users(self, action: BulkModifyUserAction) -> BulkUpdateUsersPayload:
        """Bulk-modify users. Each item's transformation is the caller's responsibility."""
        result = await self._processors.user.bulk_modify_users.wait_for_complete(action)
        updated_users = [self._user_data_to_node(u) for u in result.data.successes]
        failed = [
            BulkUpdateUserV2Error(
                user_id=action.items[error.index].user_id,
                message=str(error.exception),
            )
            for error in result.data.failures
        ]
        return BulkUpdateUsersPayload(updated_users=updated_users, failed=failed)

    async def bulk_purge_users(self, action: BulkPurgeUserAction) -> BulkPurgeUsersPayload:
        """Bulk-purge users permanently."""
        result = await self._processors.user.bulk_purge_users.wait_for_complete(action)
        failed = [
            BulkPurgeUserV2Error(
                user_id=error.user_id,
                message=str(error.exception),
            )
            for error in result.data.failures
        ]
        return BulkPurgeUsersPayload(
            purged_count=result.data.purged_count(),
            failed=failed,
        )

    async def modify_user(self, action: ModifyUserAction) -> UpdateMyAllowedClientIPPayload:
        """Modify a user. Caller is responsible for building the action."""
        await self._processors.user.modify_user.wait_for_complete(action)
        return UpdateMyAllowedClientIPPayload(success=True)

    # ------------------------------------------------------------------ keypair operations

    async def issue_my_keypair(self, user_id: UUID) -> IssueMyKeypairPayload:
        """Issue a new keypair for the current user."""
        result = await self._processors.user.issue_my_keypair.wait_for_complete(
            IssueMyKeypairAction(user_uuid=user_id)
        )
        return IssueMyKeypairPayload(
            keypair=self._keypair_data_to_node(result.generated_data.keypair),
            secret_key=str(result.generated_data.keypair.secret_key),
        )

    async def revoke_my_keypair(self, user_id: UUID, access_key: str) -> RevokeMyKeypairPayload:
        """Revoke a keypair owned by the current user."""
        result = await self._processors.user.revoke_my_keypair.wait_for_complete(
            RevokeMyKeypairAction(user_uuid=user_id, access_key=access_key)
        )
        return RevokeMyKeypairPayload(success=result.success)

    async def update_my_keypair(
        self, user_id: UUID, access_key: str, is_active: bool
    ) -> UpdateMyKeypairPayload:
        """Update a keypair owned by the current user."""
        result = await self._processors.user.update_my_keypair.wait_for_complete(
            UpdateMyKeypairAction(
                user_uuid=user_id,
                updater=Updater(
                    spec=KeyPairUpdaterSpec(is_active=OptionalState.update(is_active)),
                    pk_value=access_key,
                ),
            )
        )
        return UpdateMyKeypairPayload(keypair=self._keypair_data_to_node(result.keypair))

    async def switch_my_main_access_key(
        self, user_id: UUID, access_key: str
    ) -> SwitchMyMainAccessKeyPayload:
        """Switch the main access key for the current user."""
        result = await self._processors.user.switch_my_main_access_key.wait_for_complete(
            SwitchMyMainAccessKeyAction(user_uuid=user_id, access_key=access_key)
        )
        return SwitchMyMainAccessKeyPayload(success=result.success)

    async def search_my_keypairs(
        self,
        input: SearchMyKeypairsRequest,
    ) -> SearchResult[KeypairNode]:
        """Search keypairs owned by the current user.

        Calls current_user() internally — the caller does not need to pass scope.
        Supports both cursor-based and offset-based pagination.
        Used by both GQL and REST layers.
        """
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")
        scope = UserKeypairSearchScope(user_uuid=me.user_id)
        conditions = self._convert_keypair_filter(input.filter) if input.filter else []
        orders = self._convert_keypair_orders(input.order) if input.order else []
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_KEYPAIR_PAGINATION_SPEC,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        action_result = await self._processors.user.search_my_keypairs.wait_for_complete(
            SearchMyKeypairsAction(scope=scope, querier=querier)
        )
        return SearchResult(
            items=[self._keypair_data_to_node(item) for item in action_result.result.items],
            total_count=action_result.result.total_count,
            has_next_page=action_result.result.has_next_page,
            has_previous_page=action_result.result.has_previous_page,
        )

    @staticmethod
    def _keypair_data_to_node(data: KeyPairData) -> KeypairNode:
        """Convert KeyPairData to KeypairNode DTO."""
        return KeypairNode(
            id=str(data.access_key),
            access_key=str(data.access_key),
            is_active=data.is_active,
            is_admin=data.is_admin,
            created_at=data.created_at,
            modified_at=data.modified_at,
            last_used=data.last_used,
            rate_limit=data.rate_limit,
            num_queries=data.num_queries,
            resource_policy=data.resource_policy_name,
            ssh_public_key=data.ssh_public_key,
            user_id=data.user_id,
        )

    def _convert_keypair_filter(self, filter_req: KeypairFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []

        if filter_req.is_active is not None:
            conditions.append(KeypairConditions.by_is_active(filter_req.is_active))

        if filter_req.is_admin is not None:
            conditions.append(KeypairConditions.by_is_admin(filter_req.is_admin))

        if filter_req.access_key is not None:
            condition = self.convert_string_filter(
                filter_req.access_key,
                contains_factory=KeypairConditions.by_access_key_contains,
                equals_factory=KeypairConditions.by_access_key_equals,
                starts_with_factory=KeypairConditions.by_access_key_starts_with,
                ends_with_factory=KeypairConditions.by_access_key_ends_with,
            )
            if condition is not None:
                conditions.append(condition)

        if filter_req.resource_policy is not None:
            condition = self.convert_string_filter(
                filter_req.resource_policy,
                contains_factory=KeypairConditions.by_resource_policy_contains,
                equals_factory=KeypairConditions.by_resource_policy_equals,
                starts_with_factory=KeypairConditions.by_resource_policy_starts_with,
                ends_with_factory=KeypairConditions.by_resource_policy_ends_with,
            )
            if condition is not None:
                conditions.append(condition)

        if filter_req.created_at is not None:
            condition = filter_req.created_at.build_query_condition(
                before_factory=KeypairConditions.by_created_at_before,
                after_factory=KeypairConditions.by_created_at_after,
                equals_factory=KeypairConditions.by_created_at_equals,
            )
            if condition is not None:
                conditions.append(condition)

        if filter_req.last_used is not None:
            condition = filter_req.last_used.build_query_condition(
                before_factory=KeypairConditions.by_last_used_before,
                after_factory=KeypairConditions.by_last_used_after,
                equals_factory=KeypairConditions.by_last_used_equals,
            )
            if condition is not None:
                conditions.append(condition)

        if filter_req.AND:
            for sub_filter in filter_req.AND:
                conditions.extend(self._convert_keypair_filter(sub_filter))

        if filter_req.OR:
            or_sub_conditions: list[QueryCondition] = []
            for sub_filter in filter_req.OR:
                or_sub_conditions.extend(self._convert_keypair_filter(sub_filter))
            if or_sub_conditions:
                conditions.append(combine_conditions_or(or_sub_conditions))

        if filter_req.NOT:
            not_sub_conditions: list[QueryCondition] = []
            for sub_filter in filter_req.NOT:
                not_sub_conditions.extend(self._convert_keypair_filter(sub_filter))
            if not_sub_conditions:
                conditions.append(negate_conditions(not_sub_conditions))

        return conditions

    def _convert_keypair_orders(self, orders: list[KeypairOrderBy]) -> list[QueryOrder]:
        return [self._convert_keypair_order(o) for o in orders]

    @staticmethod
    def _convert_keypair_order(order: KeypairOrderBy) -> QueryOrder:
        ascending = order.direction == OrderDirection.ASC
        match order.field:
            case KeypairOrderField.CREATED_AT:
                return KeypairOrders.created_at(ascending=ascending)
            case KeypairOrderField.LAST_USED:
                return KeypairOrders.last_used(ascending=ascending)
            case KeypairOrderField.ACCESS_KEY:
                return KeypairOrders.access_key(ascending=ascending)
            case KeypairOrderField.IS_ACTIVE:
                return KeypairOrders.is_active(ascending=ascending)
            case KeypairOrderField.RESOURCE_POLICY:
                return KeypairOrders.resource_policy(ascending=ascending)

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
                equals_factory=UserConditions.by_created_at_equals,
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
            case UserOrderField.ROLE:
                return UserOrders.role(ascending=ascending)
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
            case UserOrderField.ROLE:
                return UserOrders.role(ascending=ascending)
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
