"""User domain adapter - Pydantic-in/Pydantic-out transport layer."""

from __future__ import annotations

import uuid
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING
from uuid import UUID

from ai.backend.common.api_handlers import Sentinel
from ai.backend.common.contexts.user import current_user
from ai.backend.common.data.entity.domain import DomainID, DomainName
from ai.backend.common.data.entity.keypair import KeyPairID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.filter_specs import StringMatchSpec, UUIDInMatchSpec
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.data.user.types import UserRole as DataUserRole
from ai.backend.common.dto.manager.pagination import PaginationInfo
from ai.backend.common.dto.manager.v2.keypair import (
    AdminSearchKeypairsInput,
    CreateKeypairPayload,
    KeypairFilter,
    KeypairNode,
    KeypairOrderBy,
    KeypairOrderField,
    SearchMyKeypairsRequest,
)
from ai.backend.common.dto.manager.v2.keypair.request import (
    AdminCreateKeypairInput,
    AdminRegisterSSHKeypairInput,
    AdminUpdateKeypairInput,
)
from ai.backend.common.dto.manager.v2.keypair.response import (
    AdminCreateKeypairPayload,
    AdminDeleteKeypairPayload,
    AdminDeleteSSHKeypairPayload,
    AdminGetSSHKeypairPayload,
    AdminRegisterSSHKeypairPayload,
    AdminSearchKeypairsPayload,
    AdminUpdateKeypairPayload,
    IssueMyKeypairPayload,
    RevokeMyKeypairPayload,
    SSHKeypairNode,
    SwitchMyMainAccessKeyPayload,
    UpdateMyKeypairPayload,
)
from ai.backend.common.dto.manager.v2.user.request import (
    AdminSearchUsersInput,
    CreateUserInput,
    DeleteUserInput,
    PurgeUserInput,
    RestoreUserInput,
    SearchUsersRequest,
    UpdateUserInput,
    UserFilter,
    UserOrder,
)
from ai.backend.common.dto.manager.v2.user.response import (
    AdminSearchUsersPayload,
    BulkCreateUsersPayload,
    BulkCreateUsersWithKeypairPayload,
    BulkCreateUserV2Error,
    BulkPurgeUsersPayload,
    BulkPurgeUserV2Error,
    BulkUpdateUsersPayload,
    BulkUpdateUserV2Error,
    CreateUserPayload,
    DeleteUserPayload,
    EntityTimestamps,
    PurgeUserPayload,
    RestoreUserPayload,
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
from ai.backend.common.types import AccessKey
from ai.backend.manager.data.common.types import SearchResult
from ai.backend.manager.data.keypair.types import KeyPairCreator, KeyPairData
from ai.backend.manager.data.user.types import UserData, UserStatus
from ai.backend.manager.data.user.types import UserStatus as DataUserStatus
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.condition_utils import combine_conditions_or, negate_conditions
from ai.backend.manager.models.domain.conditions import DomainConditions
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.keypair.conditions import KeypairConditions
from ai.backend.manager.models.keypair.orders import KeypairOrders
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.keypair.scopes import UserKeypairOperationScope
from ai.backend.manager.models.project.conditions import ProjectConditions
from ai.backend.manager.models.specs.pagination import NoPagination, OffsetPagination
from ai.backend.manager.models.user.conditions import UserConditions
from ai.backend.manager.models.user.creators import UserCreator
from ai.backend.manager.models.user.orders import UserOrders
from ai.backend.manager.models.user.row import UserRole as UserRoleModel
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.models.user.scopes import (
    DomainUserOperationScope,
    ProjectUserOperationScope,
)
from ai.backend.manager.models.user.searchers import UserSearcher
from ai.backend.manager.models.user.updaters import UserUpdater
from ai.backend.manager.services.domain.actions.lookup import LookupDomainAction
from ai.backend.manager.services.user.actions.create_user import (
    BulkCreateUserAction,
    CreateUserAction,
)
from ai.backend.manager.services.user.actions.delete_user import DeleteUserAction
from ai.backend.manager.services.user.actions.get_user import GetUserAction
from ai.backend.manager.services.user.actions.keypair_ops import (
    AdminCreateKeypairAction,
    AdminDeleteSSHKeypairAction,
    AdminGetSSHKeypairAction,
    AdminRegisterSSHKeypairAction,
    AdminSearchKeypairsAction,
    GetDefaultKeypairsAction,
    GetKeypairAction,
    IssueMyKeypairAction,
    PurgeKeypairAction,
    SearchMyKeypairsAction,
    SwitchDefaultAccessKeyAction,
    UpdateKeypairAction,
)
from ai.backend.manager.services.user.actions.lookup_keypair import (
    LookupKeypairByAccessKeyAction,
)
from ai.backend.manager.services.user.actions.lookup_keypair_owner import (
    LookupKeypairOwnerByAccessKeyAction,
)
from ai.backend.manager.services.user.actions.purge_user import (
    BulkPurgeUserAction,
    PurgeUserAction,
)
from ai.backend.manager.services.user.actions.restore_user import RestoreUserAction
from ai.backend.manager.services.user.actions.search_users import GlobalSearchUsersAction
from ai.backend.manager.services.user.actions.search_users_by_domain import (
    SearchUsersByDomainAction,
)
from ai.backend.manager.services.user.actions.search_users_by_project import (
    SearchUsersByProjectAction,
)
from ai.backend.manager.services.user.actions.search_users_by_role import (
    SearchUsersByRoleAction,
)
from ai.backend.manager.services.user.actions.update_user import (
    BulkUpdateUserAction,
    UpdateUserAction,
)
from ai.backend.manager.types import OptionalState, TriState

if TYPE_CHECKING:
    from ai.backend.manager.config.unified import AuthConfig
    from ai.backend.manager.services.processors import Processors

from ai.backend.manager.api.adapter_options.pagination.pagination import PaginationSpec
from ai.backend.manager.api.adapters.base import BaseAdapter

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

    async def resolve_domain_id(self, domain_name: str) -> DomainID:
        """The domain's id, for callers that only hold its name."""
        result = await self._processors.domain.lookup.run(
            LookupDomainAction(name=DomainName(domain_name))
        )
        return result.entity_id()

    # ------------------------------------------------------------------ batch load (DataLoader)

    async def batch_load_by_ids(self, user_ids: Sequence[uuid.UUID]) -> list[UserNode | None]:
        """Batch load users by UUID for DataLoader use.

        Returns UserNode DTOs in the same order as the input user_ids list.
        """
        if not user_ids:
            return []
        searcher = UserSearcher(
            pagination=NoPagination(),
            conditions=[
                UserConditions.by_uuid_in(UUIDInMatchSpec(values=list(user_ids), negated=False))
            ],
        )
        result = await self._processors.user.global_search.run(
            GlobalSearchUsersAction(searcher=searcher)
        )
        nodes = await self._user_nodes(result.items)
        user_map = {user.uuid: node for user, node in zip(result.items, nodes, strict=True)}
        return [user_map.get(user_id) for user_id in user_ids]

    # ------------------------------------------------------------------ GQL search (cursor-based)

    async def gql_admin_search(
        self,
        input: AdminSearchUsersInput,
    ) -> AdminSearchUsersPayload:
        """Search users with no scope restriction (admin only), cursor-based pagination."""
        conditions = self._convert_gql_filter(input.filter) if input.filter else []
        orders = self._convert_gql_orders(input.order) if input.order else []
        searcher = self._build_searcher(
            UserSearcher,
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
        result = await self._processors.user.global_search.run(
            GlobalSearchUsersAction(searcher=searcher)
        )
        return AdminSearchUsersPayload(
            items=await self._user_nodes(result.items),
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def gql_search_by_domain(
        self,
        scope: DomainUserOperationScope,
        input: AdminSearchUsersInput,
    ) -> AdminSearchUsersPayload:
        """Search users within a domain, cursor-based pagination."""
        conditions = self._convert_gql_filter(input.filter) if input.filter else []
        orders = self._convert_gql_orders(input.order) if input.order else []
        searcher = self._build_searcher(
            UserSearcher,
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
        result = await self._processors.user.search_users_by_domain.run(
            SearchUsersByDomainAction(
                domain_id=await self.resolve_domain_id(scope.domain_name),
                domain_name=scope.domain_name,
                searcher=searcher,
            )
        )
        return AdminSearchUsersPayload(
            items=await self._user_nodes(result.items),
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def gql_search_by_project(
        self,
        scope: ProjectUserOperationScope,
        input: AdminSearchUsersInput,
    ) -> AdminSearchUsersPayload:
        """Search users within a project, cursor-based pagination."""
        conditions = self._convert_gql_filter(input.filter) if input.filter else []
        orders = self._convert_gql_orders(input.order) if input.order else []
        searcher = self._build_searcher(
            UserSearcher,
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
        result = await self._processors.user.search_users_by_project.run(
            SearchUsersByProjectAction(project_id=ProjectID(scope.project_id), searcher=searcher)
        )
        return AdminSearchUsersPayload(
            items=await self._user_nodes(result.items),
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    # ------------------------------------------------------------------ search

    async def admin_search(
        self,
        input: SearchUsersRequest,
    ) -> SearchUsersPayload:
        """Search users with no scope restriction (admin only)."""
        searcher = self._build_search_searcher(input)
        result = await self._processors.user.global_search.run(
            GlobalSearchUsersAction(searcher=searcher)
        )
        return SearchUsersPayload(
            items=await self._user_nodes(result.items),
            pagination=PaginationInfo(
                total=result.total_count,
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
        searcher = self._build_search_searcher(input)
        result = await self._processors.user.search_users_by_domain.run(
            SearchUsersByDomainAction(
                domain_id=await self.resolve_domain_id(domain_name),
                domain_name=domain_name,
                searcher=searcher,
            )
        )
        return SearchUsersPayload(
            items=await self._user_nodes(result.items),
            pagination=PaginationInfo(
                total=result.total_count,
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
        searcher = self._build_search_searcher(input)
        result = await self._processors.user.search_users_by_project.run(
            SearchUsersByProjectAction(project_id=ProjectID(project_id), searcher=searcher)
        )
        return SearchUsersPayload(
            items=await self._user_nodes(result.items),
            pagination=PaginationInfo(
                total=result.total_count,
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
        searcher = self._build_search_searcher(input)
        searcher.conditions = [*searcher.conditions, UserConditions.by_role_id(role_id)]
        result = await self._processors.user.search_users_by_role.run(
            SearchUsersByRoleAction(role_id=role_id, searcher=searcher)
        )
        return SearchUsersPayload(
            items=await self._user_nodes(result.items),
            pagination=PaginationInfo(
                total=result.total_count,
                offset=input.offset,
                limit=input.limit,
            ),
        )

    # ------------------------------------------------------------------ get

    async def get(self, user_id: UUID) -> UserPayload:
        """Get a user by UUID."""
        action_result = await self._processors.user.get_user.run(
            GetUserAction(user_id=UserID(user_id))
        )
        return UserPayload(user=await self._user_node(action_result.user))

    # ------------------------------------------------------------------ single CRUD

    async def create_user(self, input: CreateUserInput) -> CreateUserPayload:
        """Create a single user."""
        password_info = PasswordInfo(
            password=input.password,
            algorithm=self._auth_config.password_hash_algorithm,
            rounds=self._auth_config.password_hash_rounds,
            salt_size=self._auth_config.password_hash_salt_size,
        )
        creator = UserCreator(
            domain_id=await self.resolve_domain_id(input.domain_name),
            email=input.email,
            username=input.username,
            password=password_info,
            need_password_change=input.need_password_change,
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
            integration_name=input.integration_name,
        )
        group_ids = [str(gid) for gid in input.group_ids] if input.group_ids else None
        result = await self._processors.user.create_user.run(
            CreateUserAction(creator=creator, group_ids=group_ids)
        )
        return CreateUserPayload(
            user=await self._user_node(result.data.user),
            keypair=self._keypair_data_to_created_payload(result.data.keypair),
        )

    async def update_user_by_id(self, user_id: UUID, input: UpdateUserInput) -> UpdateUserPayload:
        """Update a user by UUID."""
        updater = UserUpdater(
            user_id=UserID(user_id),
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
            integration_name=(
                TriState.nop()
                if isinstance(input.integration_name, Sentinel)
                else TriState.from_graphql(input.integration_name)
            ),
            group_ids=(
                OptionalState.nop()
                if isinstance(input.group_ids, Sentinel) or input.group_ids is None
                else OptionalState.update([str(gid) for gid in input.group_ids])
            ),
        )
        result = await self._processors.user.update_user.run(UpdateUserAction(updater=updater))
        if not isinstance(input.main_access_key, Sentinel) and input.main_access_key is not None:
            await self.switch_default_access_key(UserID(user_id), AccessKey(input.main_access_key))
        return UpdateUserPayload(user=await self._user_node(result.data))

    async def delete_user_by_id(self, input: DeleteUserInput) -> DeleteUserPayload:
        """Soft-delete a user by UUID."""
        await self._processors.user.delete_user.run(DeleteUserAction(user_id=UserID(input.user_id)))
        return DeleteUserPayload(success=True)

    async def restore_user_by_id(self, input: RestoreUserInput) -> RestoreUserPayload:
        """Restore a soft-deleted user by UUID."""
        await self._processors.user.restore_user.run(
            RestoreUserAction(user_id=UserID(input.user_id))
        )
        return RestoreUserPayload(success=True)

    async def purge_user_by_id(
        self, input: PurgeUserInput, admin_user_id: UUID
    ) -> PurgeUserPayload:
        """Permanently purge a user by UUID."""
        await self._processors.user.purge_user.run(
            PurgeUserAction(
                user_id=UserID(input.user_id),
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
        """Bulk-create users. Each item's transformation is the caller's responsibility.

        Deprecated: the generated keypairs are not returned. Use
        :meth:`bulk_create_users_with_keypair` instead.
        """
        result = await self._processors.user.bulk_create_users.run(action)
        created_users = await self._user_nodes([item.user for item in result.data.successes])
        failed = [
            BulkCreateUserV2Error(
                index=error.index,
                username=(creator := action.items[error.index].creator).username,
                email=creator.email,
                message=str(error.exception),
            )
            for error in result.data.failures
        ]
        return BulkCreateUsersPayload(created_users=created_users, failed=failed)

    async def bulk_create_users_with_keypair(
        self, action: BulkCreateUserAction
    ) -> BulkCreateUsersWithKeypairPayload:
        """Bulk-create users, returning each user's generated default keypair.

        The secret key of each keypair is only returned here at creation time.
        """
        result = await self._processors.user.bulk_create_users.run(action)
        created_nodes = await self._user_nodes([item.user for item in result.data.successes])
        created = [
            CreateUserPayload(
                user=node,
                keypair=self._keypair_data_to_created_payload(item.keypair),
            )
            for item, node in zip(result.data.successes, created_nodes, strict=True)
        ]
        failed = [
            BulkCreateUserV2Error(
                index=error.index,
                username=(creator := action.items[error.index].creator).username,
                email=creator.email,
                message=str(error.exception),
            )
            for error in result.data.failures
        ]
        return BulkCreateUsersWithKeypairPayload(created=created, failed=failed)

    async def bulk_modify_users(
        self,
        action: BulkUpdateUserAction,
        default_key_switches: Mapping[UserID, AccessKey],
    ) -> BulkUpdateUsersPayload:
        """Bulk-modify users. Each item's transformation is the caller's responsibility.

        A switch runs only for a user whose own update went through, and a switch that
        fails turns that user into a failure instead of aborting the whole batch.
        """
        result = await self._processors.user.bulk_modify_users.run(action)
        failed = [
            BulkUpdateUserV2Error(
                user_id=action.items[error.index].user_id,
                message=str(error.exception),
            )
            for error in result.data.failures
        ]
        updated: list[UserData] = []
        for user in result.data.successes:
            access_key = default_key_switches.get(UserID(user.id))
            if access_key is not None:
                try:
                    await self.switch_default_access_key(UserID(user.id), access_key)
                except Exception as e:
                    failed.append(BulkUpdateUserV2Error(user_id=user.id, message=str(e)))
                    continue
            updated.append(user)
        return BulkUpdateUsersPayload(updated_users=await self._user_nodes(updated), failed=failed)

    async def bulk_purge_users(self, action: BulkPurgeUserAction) -> BulkPurgeUsersPayload:
        """Bulk-purge users permanently."""
        result = await self._processors.user.bulk_purge_users.run(action)
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

    async def update_user(self, action: UpdateUserAction) -> UpdateMyAllowedClientIPPayload:
        """Modify a user. Caller is responsible for building the action."""
        await self._processors.user.update_user.run(action)
        return UpdateMyAllowedClientIPPayload(success=True)

    # ------------------------------------------------------------------ keypair operations

    async def issue_my_keypair(self, user_id: UUID) -> IssueMyKeypairPayload:
        """Issue a new keypair for the current user."""
        result = await self._processors.user.issue_my_keypair.run(
            IssueMyKeypairAction(user_id=UserID(user_id))
        )
        return IssueMyKeypairPayload(
            keypair=self._keypair_data_to_node(result.generated_data.keypair),
            secret_key=str(result.generated_data.keypair.secret_key),
        )

    async def revoke_my_keypair(self, access_key: str) -> RevokeMyKeypairPayload:
        """Revoke a keypair owned by the current user."""
        await self._purge_keypair(access_key)
        return RevokeMyKeypairPayload(success=True)

    async def update_my_keypair(self, access_key: str, is_active: bool) -> UpdateMyKeypairPayload:
        """Update a keypair owned by the current user."""
        result = await self._processors.user.update_keypair.run(
            UpdateKeypairAction(
                keypair_id=await self._resolve_keypair(access_key),
                is_active=OptionalState.update(is_active),
            )
        )
        return UpdateMyKeypairPayload(keypair=self._keypair_data_to_node(result.keypair))

    async def switch_default_access_key(
        self, user_id: UserID, access_key: AccessKey
    ) -> SwitchMyMainAccessKeyPayload:
        """Move the ``is_default`` marker among the user's keypairs onto ``access_key``."""
        result = await self._processors.user.switch_default_access_key.run(
            SwitchDefaultAccessKeyAction(user_id=user_id, access_key=access_key)
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
        scope = UserKeypairOperationScope(user_uuid=me.user_id)
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
        action_result = await self._processors.user.search_my_keypairs.run(
            SearchMyKeypairsAction(user_id=UserID(scope.user_uuid), querier=querier)
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
            is_default=data.is_default,
            created_at=data.created_at,
            modified_at=data.modified_at,
            last_used=data.last_used,
            rate_limit=data.rate_limit,
            num_queries=data.num_queries,
            resource_policy=data.resource_policy_name,
            ssh_public_key=data.ssh_public_key,
            user_id=data.user_id,
        )

    @staticmethod
    def _keypair_data_to_created_payload(data: KeyPairData) -> CreateKeypairPayload:
        """Convert KeyPairData to a CreateKeypairPayload, including the one-time secret key."""
        return CreateKeypairPayload(
            keypair=UserAdapter._keypair_data_to_node(data),
            secret_key=data.secret_key,
        )

    # ------------------------------------------------------------------ admin keypair operations

    async def admin_create_keypair(
        self, input: AdminCreateKeypairInput
    ) -> AdminCreateKeypairPayload:
        """Admin creates a keypair for a given user."""
        creator = KeyPairCreator(
            is_active=input.is_active,
            is_admin=input.is_admin,
            resource_policy=input.resource_policy,
            rate_limit=input.rate_limit,
        )
        result = await self._processors.user.admin_create_keypair.run(
            AdminCreateKeypairAction(user_id=UserID(input.user_id), creator=creator)
        )
        return AdminCreateKeypairPayload(
            keypair=self._keypair_data_to_node(result.generated_data.keypair),
            secret_key=str(result.generated_data.keypair.secret_key),
        )

    async def _resolve_keypair_owner(self, access_key: str) -> UserID:
        result = await self._processors.user.lookup_keypair_owner.run(
            LookupKeypairOwnerByAccessKeyAction(access_key=AccessKey(access_key))
        )
        return UserID(result.entity_id())

    async def _resolve_keypair(self, access_key: str) -> KeyPairID:
        """The id of the keypair an access key names, which every operation on that row
        is built from."""
        result = await self._processors.user.lookup_keypair.run(
            LookupKeypairByAccessKeyAction(access_key=AccessKey(access_key))
        )
        return KeyPairID(result.field_id)

    async def _purge_keypair(self, access_key: str) -> str:
        result = await self._processors.user.purge_keypair.run(
            PurgeKeypairAction(keypair_id=await self._resolve_keypair(access_key))
        )
        return str(result.keypair.access_key)

    async def admin_update_keypair(
        self, input: AdminUpdateKeypairInput
    ) -> AdminUpdateKeypairPayload:
        """Admin updates any keypair."""
        result = await self._processors.user.update_keypair.run(
            UpdateKeypairAction(
                keypair_id=await self._resolve_keypair(input.access_key),
                is_active=OptionalState.from_nullable(input.is_active),
                is_admin=OptionalState.from_nullable(input.is_admin),
                resource_policy=OptionalState.from_nullable(input.resource_policy),
                rate_limit=OptionalState.from_nullable(input.rate_limit),
            )
        )
        return AdminUpdateKeypairPayload(keypair=self._keypair_data_to_node(result.keypair))

    async def admin_delete_keypair(self, access_key: str) -> AdminDeleteKeypairPayload:
        """Admin deletes any keypair."""
        return AdminDeleteKeypairPayload(access_key=await self._purge_keypair(access_key))

    async def admin_get_keypair(self, access_key: str) -> KeypairNode:
        """Admin retrieves a single keypair by access key."""
        result = await self._processors.user.get_keypair.run(
            GetKeypairAction(keypair_id=await self._resolve_keypair(access_key))
        )
        return self._keypair_data_to_node(result.keypair)

    async def admin_register_ssh_keypair(
        self, input: AdminRegisterSSHKeypairInput
    ) -> AdminRegisterSSHKeypairPayload:
        """Admin registers (overwrites) a user's SSH keypair."""
        result = await self._processors.user.admin_register_ssh_keypair.run(
            AdminRegisterSSHKeypairAction(
                user_id=await self._resolve_keypair_owner(input.access_key),
                access_key=input.access_key,
                ssh_public_key=input.ssh_public_key,
                ssh_private_key=input.ssh_private_key,
            )
        )
        return AdminRegisterSSHKeypairPayload(access_key=result.access_key)

    async def admin_delete_ssh_keypair(self, access_key: str) -> AdminDeleteSSHKeypairPayload:
        """Admin clears a user's SSH keypair."""
        result = await self._processors.user.admin_delete_ssh_keypair.run(
            AdminDeleteSSHKeypairAction(
                user_id=await self._resolve_keypair_owner(access_key), access_key=access_key
            )
        )
        return AdminDeleteSSHKeypairPayload(access_key=result.access_key)

    async def admin_get_ssh_keypair(self, access_key: str) -> AdminGetSSHKeypairPayload:
        """Admin retrieves a user's SSH public key (never the private key)."""
        result = await self._processors.user.admin_get_ssh_keypair.run(
            AdminGetSSHKeypairAction(
                user_id=await self._resolve_keypair_owner(access_key), access_key=access_key
            )
        )
        return AdminGetSSHKeypairPayload(
            keypair=SSHKeypairNode(
                access_key=result.access_key,
                ssh_public_key=result.ssh_public_key,
            )
        )

    async def admin_search_keypairs(
        self,
        input: AdminSearchKeypairsInput,
    ) -> AdminSearchKeypairsPayload:
        """Admin search all keypairs (REST)."""
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
        action_result = await self._processors.user.admin_search_keypairs.run(
            AdminSearchKeypairsAction(querier=querier)
        )
        return AdminSearchKeypairsPayload(
            items=[self._keypair_data_to_node(item) for item in action_result.result.items],
            pagination=PaginationInfo(
                total=action_result.result.total_count,
                offset=input.offset or 0,
                limit=input.limit,
            ),
        )

    async def gql_admin_search_keypairs(
        self,
        input: AdminSearchKeypairsInput,
        *,
        resource_policy_name: str | None = None,
    ) -> SearchResult[KeypairNode]:
        """Admin search across every keypair (GQL, returns SearchResult for connection).

        ``resource_policy_name`` narrows the same admin read to one policy for the
        resource policy node's ``keypairs`` connection. A filter, not a second path.
        """
        conditions = self._convert_keypair_filter(input.filter) if input.filter else []
        if resource_policy_name is not None:
            conditions.append(
                KeypairConditions.by_resource_policy_equals(
                    StringMatchSpec(resource_policy_name, case_insensitive=False, negated=False)
                )
            )
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
        action_result = await self._processors.user.admin_search_keypairs.run(
            AdminSearchKeypairsAction(querier=querier)
        )
        return SearchResult(
            items=[self._keypair_data_to_node(item) for item in action_result.result.items],
            total_count=action_result.result.total_count,
            has_next_page=action_result.result.has_next_page,
            has_previous_page=action_result.result.has_previous_page,
        )

    def _convert_keypair_filter(self, filter_req: KeypairFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []

        if filter_req.is_active is not None:
            conditions.append(KeypairConditions.by_is_active(filter_req.is_active))

        if filter_req.is_admin is not None:
            conditions.append(KeypairConditions.by_is_admin(filter_req.is_admin))

        if filter_req.is_default is not None:
            conditions.append(KeypairConditions.by_is_default(filter_req.is_default))

        if filter_req.access_key is not None:
            condition = self.convert_string_filter(
                filter_req.access_key,
                contains_factory=KeypairConditions.by_access_key_contains,
                equals_factory=KeypairConditions.by_access_key_equals,
                starts_with_factory=KeypairConditions.by_access_key_starts_with,
                ends_with_factory=KeypairConditions.by_access_key_ends_with,
                in_factory=KeypairConditions.by_access_key_in,
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
                in_factory=KeypairConditions.by_resource_policy_in,
            )
            if condition is not None:
                conditions.append(condition)

        if filter_req.user_id is not None:
            condition = self.convert_uuid_filter(
                filter_req.user_id,
                equals_factory=KeypairConditions.by_user_id_equals,
                in_factory=KeypairConditions.by_user_id_in,
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
            case KeypairOrderField.IS_DEFAULT:
                return KeypairOrders.is_default(ascending=ascending)
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
                in_factory=UserConditions.by_username_in,
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
                in_factory=UserConditions.by_email_in,
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
                in_factory=UserConditions.by_domain_name_in,
            )
            if condition is not None:
                conditions.append(condition)

        if filter_req.integration_name is not None:
            condition = self.convert_string_filter(
                filter_req.integration_name,
                contains_factory=UserConditions.by_integration_name_contains,
                equals_factory=UserConditions.by_integration_name_equals,
                starts_with_factory=UserConditions.by_integration_name_starts_with,
                ends_with_factory=UserConditions.by_integration_name_ends_with,
                in_factory=UserConditions.by_integration_name_in,
            )
            if condition is not None:
                conditions.append(condition)

        if filter_req.full_name is not None:
            condition = self.convert_string_filter(
                filter_req.full_name,
                contains_factory=UserConditions.by_full_name_contains,
                equals_factory=UserConditions.by_full_name_equals,
                starts_with_factory=UserConditions.by_full_name_starts_with,
                ends_with_factory=UserConditions.by_full_name_ends_with,
                in_factory=UserConditions.by_full_name_in,
            )
            if condition is not None:
                conditions.append(condition)

        if filter_req.description is not None:
            condition = self.convert_string_filter(
                filter_req.description,
                contains_factory=UserConditions.by_description_contains,
                equals_factory=UserConditions.by_description_equals,
                starts_with_factory=UserConditions.by_description_starts_with,
                ends_with_factory=UserConditions.by_description_ends_with,
                in_factory=UserConditions.by_description_in,
            )
            if condition is not None:
                conditions.append(condition)

        if filter_req.status_info is not None:
            condition = self.convert_string_filter(
                filter_req.status_info,
                contains_factory=UserConditions.by_status_info_contains,
                equals_factory=UserConditions.by_status_info_equals,
                starts_with_factory=UserConditions.by_status_info_starts_with,
                ends_with_factory=UserConditions.by_status_info_ends_with,
                in_factory=UserConditions.by_status_info_in,
            )
            if condition is not None:
                conditions.append(condition)

        if filter_req.resource_policy is not None:
            condition = self.convert_string_filter(
                filter_req.resource_policy,
                contains_factory=UserConditions.by_resource_policy_contains,
                equals_factory=UserConditions.by_resource_policy_equals,
                starts_with_factory=UserConditions.by_resource_policy_starts_with,
                ends_with_factory=UserConditions.by_resource_policy_ends_with,
                in_factory=UserConditions.by_resource_policy_in,
            )
            if condition is not None:
                conditions.append(condition)

        if filter_req.role is not None:
            conditions.extend(self._convert_role_filter(filter_req.role))

        if filter_req.need_password_change is not None:
            conditions.append(
                UserConditions.by_need_password_change(filter_req.need_password_change)
            )

        if filter_req.totp_activated is not None:
            conditions.append(UserConditions.by_totp_activated(filter_req.totp_activated))

        if filter_req.sudo_session_enabled is not None:
            conditions.append(
                UserConditions.by_sudo_session_enabled(filter_req.sudo_session_enabled)
            )

        if filter_req.container_uid is not None:
            condition = self.convert_int_filter(
                filter_req.container_uid,
                UserConditions.by_container_uid,
            )
            if condition is not None:
                conditions.append(condition)

        if filter_req.container_main_gid is not None:
            condition = self.convert_int_filter(
                filter_req.container_main_gid,
                UserConditions.by_container_main_gid,
            )
            if condition is not None:
                conditions.append(condition)

        if filter_req.container_gids is not None:
            condition = self.convert_array_filter(
                filter_req.container_gids,
                contains_factory=UserConditions.by_container_gids_contains,
                contains_any_factory=UserConditions.by_container_gids_any,
                contains_all_factory=UserConditions.by_container_gids_all,
            )
            if condition is not None:
                conditions.append(condition)

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
        if sf.not_equals is not None:
            conditions.append(
                negate_conditions([
                    UserConditions.by_status_equals(DataUserStatus(sf.not_equals.value))
                ])
            )
        if sf.not_in is not None:
            conditions.append(
                negate_conditions([
                    UserConditions.by_status_in([DataUserStatus(s.value) for s in sf.not_in])
                ])
            )
        return conditions

    @staticmethod
    def _convert_role_filter(rf: UserRoleFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if rf.equals is not None:
            conditions.append(UserConditions.by_role_equals(DataUserRole(rf.equals.value)))
        if rf.in_ is not None:
            conditions.append(UserConditions.by_role_in([DataUserRole(r.value) for r in rf.in_]))
        if rf.not_equals is not None:
            conditions.append(
                negate_conditions([
                    UserConditions.by_role_equals(DataUserRole(rf.not_equals.value))
                ])
            )
        if rf.not_in is not None and len(rf.not_in) > 0:
            conditions.append(
                negate_conditions([
                    UserConditions.by_role_in([DataUserRole(r.value) for r in rf.not_in])
                ])
            )
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
                in_factory=DomainConditions.by_name_in,
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
                contains_factory=ProjectConditions.by_name_contains,
                equals_factory=ProjectConditions.by_name_equals,
                starts_with_factory=ProjectConditions.by_name_starts_with,
                ends_with_factory=ProjectConditions.by_name_ends_with,
                in_factory=ProjectConditions.by_name_in,
            )
            if condition is not None:
                raw_conditions.append(condition)
        if project_filter.is_active is not None:
            raw_conditions.append(ProjectConditions.by_is_active(project_filter.is_active))
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

    def _build_search_searcher(self, input: SearchUsersRequest) -> UserSearcher:
        """Build a user searcher from the search request DTO."""
        conditions = self._convert_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else []
        pagination = OffsetPagination(limit=input.limit, offset=input.offset)
        return UserSearcher(conditions=conditions, orders=orders, pagination=pagination)

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
                in_factory=UserConditions.by_email_in,
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
                in_factory=UserConditions.by_username_in,
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
                in_factory=UserConditions.by_domain_name_in,
            )
            if condition is not None:
                conditions.append(condition)

        if filter_req.integration_name is not None:
            condition = self.convert_string_filter(
                filter_req.integration_name,
                contains_factory=UserConditions.by_integration_name_contains,
                equals_factory=UserConditions.by_integration_name_equals,
                starts_with_factory=UserConditions.by_integration_name_starts_with,
                ends_with_factory=UserConditions.by_integration_name_ends_with,
                in_factory=UserConditions.by_integration_name_in,
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

        if filter_req.container_uid is not None:
            condition = self.convert_int_filter(
                filter_req.container_uid,
                UserConditions.by_container_uid,
            )
            if condition is not None:
                conditions.append(condition)

        if filter_req.container_main_gid is not None:
            condition = self.convert_int_filter(
                filter_req.container_main_gid,
                UserConditions.by_container_main_gid,
            )
            if condition is not None:
                conditions.append(condition)

        if filter_req.container_gids is not None:
            condition = self.convert_array_filter(
                filter_req.container_gids,
                contains_factory=UserConditions.by_container_gids_contains,
                contains_any_factory=UserConditions.by_container_gids_any,
                contains_all_factory=UserConditions.by_container_gids_all,
            )
            if condition is not None:
                conditions.append(condition)

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
                conditions.extend(self._convert_filter(sub_filter))
        if filter_req.OR:
            or_sub_conditions: list[QueryCondition] = []
            for sub_filter in filter_req.OR:
                or_sub_conditions.extend(self._convert_filter(sub_filter))
            if or_sub_conditions:
                conditions.append(combine_conditions_or(or_sub_conditions))
        if filter_req.NOT:
            not_sub_conditions: list[QueryCondition] = []
            for sub_filter in filter_req.NOT:
                not_sub_conditions.extend(self._convert_filter(sub_filter))
            if not_sub_conditions:
                conditions.append(negate_conditions(not_sub_conditions))

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

    async def _default_access_keys(self, users: Sequence[UserData]) -> Mapping[UserID, AccessKey]:
        """The key each user authorizes with, read for every one of them in one go."""
        if not users:
            return {}
        result = await self._processors.user.get_default_keypairs.run(
            GetDefaultKeypairsAction(user_ids=[UserID(user.id) for user in users])
        )
        return {
            owner: AccessKey(keypair.access_key) for owner, keypair in result.designated.items()
        }

    async def _user_nodes(self, users: Sequence[UserData]) -> list[UserNode]:
        access_keys = await self._default_access_keys(users)
        return [self._user_data_to_node(user, access_keys.get(UserID(user.id))) for user in users]

    async def _user_node(self, user: UserData) -> UserNode:
        return (await self._user_nodes([user]))[0]

    @staticmethod
    def _user_data_to_node(data: UserData, main_access_key: AccessKey | None) -> UserNode:
        """Convert UserData to UserNode DTO."""
        return UserNode(
            id=data.id,
            basic_info=UserBasicInfo(
                username=data.username,
                email=data.email,
                full_name=data.full_name,
                description=data.description,
                integration_name=data.integration_name,
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
                main_access_key=main_access_key,
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
