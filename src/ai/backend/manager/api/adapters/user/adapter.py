"""User domain adapter - Pydantic-in/Pydantic-out transport layer."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, assert_never
from uuid import UUID

from ai.backend.common.contexts.user import current_user
from ai.backend.common.data.entity.domain import DomainID, DomainName
from ai.backend.common.data.entity.keypair import KeyPairID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.filter_specs import StringMatchSpec
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
    ScopedSearchUsersInput,
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
    UserScope,
)
from ai.backend.common.dto.manager.v2.user.types import (
    UserRole as UserRoleDTO,
)
from ai.backend.common.dto.manager.v2.user.types import (
    UserStatus as UserStatusDTO,
)
from ai.backend.common.exception import UnreachableError
from ai.backend.common.tristate.unset import Unset
from ai.backend.common.types import AccessKey, SecretKey
from ai.backend.manager.data.common.types import SearchResult
from ai.backend.manager.data.keypair.types import KeyPairCreator, KeyPairData
from ai.backend.manager.data.user.types import UserData, UserStatus
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.condition_utils import combine_conditions_or, negate_conditions
from ai.backend.manager.models.domain.conditions import DomainConditions
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.keypair.scopes import UserKeypairTarget
from ai.backend.manager.models.keypair.searchable_fields import KeyPairSearchableFields
from ai.backend.manager.models.project.conditions import ProjectConditions
from ai.backend.manager.models.specs.pagination import OffsetPagination
from ai.backend.manager.models.user.creators import UserCreator
from ai.backend.manager.models.user.deprecated_search import (
    DeprecatedUserConditions,
    DeprecatedUserOrders,
)
from ai.backend.manager.models.user.row import UserRole as UserRoleModel
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.models.user.scopes import (
    DomainUserTarget,
    ProjectUserTarget,
    RoleUserTarget,
    UserTarget,
)
from ai.backend.manager.models.user.searchable_fields import UserSearchableFields
from ai.backend.manager.models.user.searchers import UserSearcher
from ai.backend.manager.models.user.updaters import UserUpdater
from ai.backend.manager.services.domain.actions.lookup import LookupDomainAction
from ai.backend.manager.services.user.actions.bulk_get import BulkGetUsersAction
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
from ai.backend.manager.services.user.actions.scoped_search import (
    ScopedSearchUsersAction,
)
from ai.backend.manager.services.user.actions.search_users import GlobalSearchUsersAction
from ai.backend.manager.services.user.actions.update_user import (
    BulkUpdateUserAction,
    UpdateUserAction,
)
from ai.backend.manager.types import OptionalState, TriState

if TYPE_CHECKING:
    from ai.backend.manager.config.unified import AuthConfig

from ai.backend.manager.api.adapter_options.pagination.pagination import PaginationSpec
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.models.keypair.row import KEYPAIR_SECRET_KEY_CONTEXT
from ai.backend.manager.models.keypair.searchers import KeyPairSearcher
from ai.backend.manager.models.specs.searcher import GlobalSearcher
from ai.backend.manager.secret.pool import KeyProviderPool
from ai.backend.manager.services.domain.processors import DomainProcessors
from ai.backend.manager.services.user.processors import UserProcessors

_USER_PAGINATION_SPEC = PaginationSpec(
    forward_order=UserSearchableFields.own.created_at.order.apply(ascending=False),
    cursor_column=UserRow.uuid,
)

_KEYPAIR_PAGINATION_SPEC = PaginationSpec(
    forward_order=KeyPairSearchableFields.own.created_at.order.apply(ascending=False),
    cursor_column=KeyPairRow.id,
)


class UserAdapter(BaseAdapter):
    """Adapter for user domain operations."""

    _user: UserProcessors
    _domain: DomainProcessors
    _auth_config: AuthConfig
    _key_provider_pool: KeyProviderPool

    def __init__(
        self,
        user: UserProcessors,
        domain: DomainProcessors,
        auth_config: AuthConfig,
        key_provider_pool: KeyProviderPool,
    ) -> None:
        self._user = user
        self._domain = domain
        self._auth_config = auth_config
        self._key_provider_pool = key_provider_pool

    async def resolve_domain_id(self, domain_name: str) -> DomainID:
        """The domain's id, for callers that only hold its name."""
        result = await self._domain.lookup.run(LookupDomainAction(name=DomainName(domain_name)))
        return result.entity_id()

    # ------------------------------------------------------------------ batch load (DataLoader)

    async def batch_load_by_ids(
        self, user_ids: Sequence[UserID]
    ) -> list[UserNode | Exception | None]:
        """Batch load users by UUID for DataLoader use, checked per user."""
        if not user_ids:
            return []
        result = await self._user.bulk_get.run(BulkGetUsersAction(ids=list(user_ids)))
        users = [item.value for item in result.items if item.value is not None]
        nodes = iter(await self._user_nodes(users))
        return [
            next(nodes) if item.value is not None else self.batch_load_failure(item.error)
            for item in result.items
        ]

    # ------------------------------------------------------------------ GQL search (cursor-based)

    async def gql_admin_search(
        self,
        input: AdminSearchUsersInput,
    ) -> AdminSearchUsersPayload:
        """Search users with no scope restriction (admin only), cursor-based pagination."""
        conditions = self._convert_user_filter(input.filter) if input.filter else []
        orders = self._convert_user_orders(input.order) if input.order else []
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
        result = await self._user.global_search.run(
            GlobalSearchUsersAction(searcher=GlobalSearcher(used_by=(), searcher=searcher))
        )
        return AdminSearchUsersPayload(
            items=await self._user_nodes(result.items),
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def gql_search_by_domain(
        self,
        domain_name: str,
        input: AdminSearchUsersInput,
    ) -> AdminSearchUsersPayload:
        """Search users within a domain, cursor-based pagination."""
        conditions = self._convert_user_filter(input.filter) if input.filter else []
        orders = self._convert_user_orders(input.order) if input.order else []
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
        result = await self._user.scoped_search.run(
            ScopedSearchUsersAction(
                targets=[DomainUserTarget(domain_id=await self.resolve_domain_id(domain_name))],
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
        project_id: ProjectID,
        input: AdminSearchUsersInput,
    ) -> AdminSearchUsersPayload:
        """Search users within a project, cursor-based pagination."""
        conditions = self._convert_user_filter(input.filter) if input.filter else []
        orders = self._convert_user_orders(input.order) if input.order else []
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
        result = await self._user.scoped_search.run(
            ScopedSearchUsersAction(
                targets=[ProjectUserTarget(project_id=project_id)],
                searcher=searcher,
            )
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
        result = await self._user.global_search.run(
            GlobalSearchUsersAction(searcher=GlobalSearcher(used_by=(), searcher=searcher))
        )
        return SearchUsersPayload(
            items=await self._user_nodes(result.items),
            pagination=PaginationInfo(
                total=result.total_count,
                offset=input.offset,
                limit=input.limit,
            ),
        )

    def _scope_targets(self, scope: UserScope) -> list[UserTarget]:
        """The scope targets the request named, in the order the input lists them."""
        targets: list[UserTarget] = [
            DomainUserTarget(domain_id=DomainID(entry.value)) for entry in scope.domain or ()
        ]
        targets.extend(
            ProjectUserTarget(project_id=ProjectID(entry.value)) for entry in scope.project or ()
        )
        targets.extend(RoleUserTarget(role_id=RoleID(entry.value)) for entry in scope.role or ())
        return targets

    async def scoped_search(
        self,
        input: ScopedSearchUsersInput,
    ) -> SearchUsersPayload:
        """Search the users the named scopes reach, combined with OR."""
        conditions = self._convert_user_filter(input.filter) if input.filter else []
        orders = self._convert_user_orders(input.order) if input.order else []
        result = await self._user.scoped_search.run(
            ScopedSearchUsersAction(
                targets=self._scope_targets(input.scope),
                searcher=UserSearcher(
                    conditions=conditions,
                    orders=orders,
                    pagination=OffsetPagination(limit=input.limit, offset=input.offset),
                ),
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

    async def gql_scoped_search(
        self,
        scope: UserScope,
        input: AdminSearchUsersInput,
    ) -> AdminSearchUsersPayload:
        """Search the users the named scopes reach, cursor-based pagination."""
        conditions = self._convert_user_filter(input.filter) if input.filter else []
        orders = self._convert_user_orders(input.order) if input.order else []
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
        result = await self._user.scoped_search.run(
            ScopedSearchUsersAction(targets=self._scope_targets(scope), searcher=searcher)
        )
        return AdminSearchUsersPayload(
            items=await self._user_nodes(result.items),
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def domain_search(
        self,
        domain_name: str,
        input: SearchUsersRequest,
    ) -> SearchUsersPayload:
        """Search users within a domain."""
        searcher = self._build_search_searcher(input)
        result = await self._user.scoped_search.run(
            ScopedSearchUsersAction(
                targets=[DomainUserTarget(domain_id=await self.resolve_domain_id(domain_name))],
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
        result = await self._user.scoped_search.run(
            ScopedSearchUsersAction(
                targets=[ProjectUserTarget(project_id=ProjectID(project_id))],
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

    async def role_search(
        self,
        role_id: UUID,
        input: SearchUsersRequest,
    ) -> SearchUsersPayload:
        """Search users assigned to a role."""
        searcher = self._build_search_searcher(input)
        role_target = RoleUserTarget(role_id=RoleID(role_id))
        searcher.conditions = [*searcher.conditions, role_target.to_condition()]
        result = await self._user.global_search.run(
            GlobalSearchUsersAction(searcher=GlobalSearcher(used_by=(), searcher=searcher))
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
        action_result = await self._user.get_user.run(GetUserAction(user_id=UserID(user_id)))
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
            role=UserRoleModel(input.role),
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
        result = await self._user.create_user.run(
            CreateUserAction(creator=creator, group_ids=group_ids)
        )
        return CreateUserPayload(
            user=await self._user_node(result.data.user),
            keypair=await self._keypair_data_to_created_payload(result.data.keypair),
        )

    async def update_user_by_id(self, user_id: UUID, input: UpdateUserInput) -> UpdateUserPayload:
        """Update a user by UUID."""
        updater = UserUpdater(
            user_id=UserID(user_id),
            username=OptionalState.from_unset(input.username),
            password=(
                OptionalState.nop()
                if isinstance(input.password, Unset) or input.password is None
                else OptionalState.update(
                    PasswordInfo(
                        password=input.password,
                        algorithm=self._auth_config.password_hash_algorithm,
                        rounds=self._auth_config.password_hash_rounds,
                        salt_size=self._auth_config.password_hash_salt_size,
                    )
                )
            ),
            need_password_change=OptionalState.from_unset(input.need_password_change),
            full_name=TriState.from_unset(input.full_name),
            description=TriState.from_unset(input.description),
            status=(
                OptionalState.nop()
                if isinstance(input.status, Unset) or input.status is None
                else OptionalState.update(UserStatus(input.status))
            ),
            domain_name=OptionalState.from_unset(input.domain_name),
            role=(
                OptionalState.nop()
                if isinstance(input.role, Unset) or input.role is None
                else OptionalState.update(UserRoleModel(input.role))
            ),
            allowed_client_ip=TriState.from_unset(input.allowed_client_ip),
            resource_policy=OptionalState.from_unset(input.resource_policy),
            sudo_session_enabled=OptionalState.from_unset(input.sudo_session_enabled),
            container_uid=TriState.from_unset(input.container_uid),
            container_main_gid=TriState.from_unset(input.container_main_gid),
            container_gids=TriState.from_unset(input.container_gids),
            integration_name=TriState.from_unset(input.integration_name),
            group_ids=(
                OptionalState.nop()
                if isinstance(input.group_ids, Unset) or input.group_ids is None
                else OptionalState.update([str(gid) for gid in input.group_ids])
            ),
        )
        result = await self._user.update_user.run(UpdateUserAction(updater=updater))
        if not isinstance(input.main_access_key, Unset) and input.main_access_key is not None:
            await self.switch_default_access_key(UserID(user_id), AccessKey(input.main_access_key))
        return UpdateUserPayload(user=await self._user_node(result.data))

    async def delete_user_by_id(self, input: DeleteUserInput) -> DeleteUserPayload:
        """Soft-delete a user by UUID."""
        await self._user.delete_user.run(DeleteUserAction(user_id=UserID(input.user_id)))
        return DeleteUserPayload(success=True)

    async def restore_user_by_id(self, input: RestoreUserInput) -> RestoreUserPayload:
        """Restore a soft-deleted user by UUID."""
        await self._user.restore_user.run(RestoreUserAction(user_id=UserID(input.user_id)))
        return RestoreUserPayload(success=True)

    async def purge_user_by_id(
        self, input: PurgeUserInput, admin_user_id: UUID
    ) -> PurgeUserPayload:
        """Permanently purge a user by UUID."""
        await self._user.purge_user.run(
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
        result = await self._user.bulk_create_users.run(action)
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
        result = await self._user.bulk_create_users.run(action)
        created_nodes = await self._user_nodes([item.user for item in result.data.successes])
        created = [
            CreateUserPayload(
                user=node,
                keypair=await self._keypair_data_to_created_payload(item.keypair),
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
        result = await self._user.bulk_modify_users.run(action)
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
        result = await self._user.bulk_purge_users.run(action)
        failed = [
            BulkPurgeUserV2Error(
                user_id=error.user_id,
                message=str(error.exception),
            )
            for error in result.data.failures
        ]
        return BulkPurgeUsersPayload(
            successes=list(result.data.purged_user_ids),
            purged_count=result.data.purged_count(),
            failed=failed,
        )

    async def update_user(self, action: UpdateUserAction) -> UpdateMyAllowedClientIPPayload:
        """Modify a user. Caller is responsible for building the action."""
        await self._user.update_user.run(action)
        return UpdateMyAllowedClientIPPayload(success=True)

    # ------------------------------------------------------------------ keypair operations

    async def issue_my_keypair(self, user_id: UUID) -> IssueMyKeypairPayload:
        """Issue a new keypair for the current user."""
        result = await self._user.issue_my_keypair.run(
            IssueMyKeypairAction(user_id=UserID(user_id))
        )
        return IssueMyKeypairPayload(
            keypair=self._keypair_data_to_node(result.generated_data.keypair),
            secret_key=await self._secret_key_of(result.generated_data.keypair),
        )

    async def revoke_my_keypair(self, access_key: str) -> RevokeMyKeypairPayload:
        """Revoke a keypair owned by the current user."""
        await self._purge_keypair(access_key)
        return RevokeMyKeypairPayload(success=True)

    async def update_my_keypair(self, access_key: str, is_active: bool) -> UpdateMyKeypairPayload:
        """Update a keypair owned by the current user."""
        result = await self._user.update_keypair.run(
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
        result = await self._user.switch_default_access_key.run(
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
        scope = UserKeypairTarget(user_uuid=me.user_id)
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
        action_result = await self._user.search_my_keypairs.run(
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
            field_id=data.id,
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

    async def _secret_key_of(self, data: KeyPairData) -> SecretKey:
        """The keypair's secret key as plaintext, whatever form it is stored in."""
        return SecretKey(
            await self._key_provider_pool.decrypt(data.secret_key, KEYPAIR_SECRET_KEY_CONTEXT)
        )

    async def _keypair_data_to_created_payload(self, data: KeyPairData) -> CreateKeypairPayload:
        """Convert KeyPairData to a CreateKeypairPayload, including the one-time secret key."""
        return CreateKeypairPayload(
            keypair=UserAdapter._keypair_data_to_node(data),
            secret_key=await self._secret_key_of(data),
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
        result = await self._user.admin_create_keypair.run(
            AdminCreateKeypairAction(user_id=UserID(input.user_id), creator=creator)
        )
        return AdminCreateKeypairPayload(
            keypair=self._keypair_data_to_node(result.generated_data.keypair),
            secret_key=await self._secret_key_of(result.generated_data.keypair),
        )

    async def _resolve_keypair_owner(self, access_key: str) -> UserID:
        result = await self._user.lookup_keypair_owner.run(
            LookupKeypairOwnerByAccessKeyAction(access_key=AccessKey(access_key))
        )
        return UserID(result.entity_id())

    async def _resolve_keypair(self, access_key: str) -> KeyPairID:
        """The id of the keypair an access key names, which every operation on that row
        is built from."""
        result = await self._user.lookup_keypair.run(
            LookupKeypairByAccessKeyAction(access_key=AccessKey(access_key))
        )
        return KeyPairID(result.field_id)

    async def _purge_keypair(self, access_key: str) -> str:
        result = await self._user.purge_keypair.run(
            PurgeKeypairAction(keypair_id=await self._resolve_keypair(access_key))
        )
        return str(result.keypair.access_key)

    async def admin_update_keypair(
        self, input: AdminUpdateKeypairInput
    ) -> AdminUpdateKeypairPayload:
        """Admin updates any keypair."""
        result = await self._user.update_keypair.run(
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
        result = await self._user.get_keypair.run(
            GetKeypairAction(keypair_id=await self._resolve_keypair(access_key))
        )
        return self._keypair_data_to_node(result.keypair)

    async def admin_register_ssh_keypair(
        self, input: AdminRegisterSSHKeypairInput
    ) -> AdminRegisterSSHKeypairPayload:
        """Admin registers (overwrites) a user's SSH keypair."""
        result = await self._user.admin_register_ssh_keypair.run(
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
        result = await self._user.admin_delete_ssh_keypair.run(
            AdminDeleteSSHKeypairAction(
                user_id=await self._resolve_keypair_owner(access_key), access_key=access_key
            )
        )
        return AdminDeleteSSHKeypairPayload(access_key=result.access_key)

    async def admin_get_ssh_keypair(self, access_key: str) -> AdminGetSSHKeypairPayload:
        """Admin retrieves a user's SSH public key (never the private key)."""
        result = await self._user.admin_get_ssh_keypair.run(
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
        action_result = await self._user.admin_search_keypairs.run(
            AdminSearchKeypairsAction(
                searcher=GlobalSearcher(
                    used_by=(),
                    searcher=KeyPairSearcher(
                        pagination=querier.pagination,
                        conditions=querier.conditions,
                        orders=querier.orders,
                    ),
                )
            )
        )
        return AdminSearchKeypairsPayload(
            items=[self._keypair_data_to_node(item) for item in action_result.items],
            pagination=PaginationInfo(
                total=action_result.total_count,
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
                KeyPairSearchableFields.own.resource_policy_name.filter.equals(
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
        action_result = await self._user.admin_search_keypairs.run(
            AdminSearchKeypairsAction(
                searcher=GlobalSearcher(
                    used_by=(),
                    searcher=KeyPairSearcher(
                        pagination=querier.pagination,
                        conditions=querier.conditions,
                        orders=querier.orders,
                    ),
                )
            )
        )
        return SearchResult(
            items=[self._keypair_data_to_node(item) for item in action_result.items],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    def _convert_keypair_filter(self, f: KeypairFilter) -> list[QueryCondition]:
        """Conditions matching a single keypair row.

        Used both by the keypair searches and, through ``keypairs``, to narrow a user
        search; one instance narrows one row either way.
        """
        fields = KeyPairSearchableFields.own
        conditions = [
            *self.apply_bool_filter(f.is_active, fields.is_active.filter),
            *self.apply_bool_filter(f.is_admin, fields.is_admin.filter),
            *self.apply_bool_filter(f.is_default, fields.is_default.filter),
            *self.apply_string_filter(f.access_key, fields.access_key.filter),
            *self.apply_string_filter(f.resource_policy, fields.resource_policy_name.filter),
            *self.apply_uuid_filter(f.user_id, fields.user_id.filter),
            *self.apply_datetime_filter(f.created_at, fields.created_at.filter),
            *self.apply_datetime_filter(f.last_used, fields.last_used.filter),
        ]
        if f.AND:
            for sub in f.AND:
                conditions.extend(self._convert_keypair_filter(sub))
        if f.OR:
            or_conditions: list[QueryCondition] = []
            for sub in f.OR:
                or_conditions.extend(self._convert_keypair_filter(sub))
            if or_conditions:
                conditions.append(combine_conditions_or(or_conditions))
        if f.NOT:
            not_conditions: list[QueryCondition] = []
            for sub in f.NOT:
                not_conditions.extend(self._convert_keypair_filter(sub))
            if not_conditions:
                conditions.append(negate_conditions(not_conditions))
        return conditions

    def _convert_keypair_orders(self, orders: list[KeypairOrderBy]) -> list[QueryOrder]:
        return [self._convert_keypair_order(order) for order in orders]

    def _convert_keypair_order(self, order: KeypairOrderBy) -> QueryOrder:
        fields = KeyPairSearchableFields.own
        ascending = order.direction == OrderDirection.ASC
        match order.field:
            case KeypairOrderField.CREATED_AT:
                return fields.created_at.order.apply(ascending)
            case KeypairOrderField.LAST_USED:
                return fields.last_used.order.apply(ascending)
            case KeypairOrderField.ACCESS_KEY:
                return fields.access_key.order.apply(ascending)
            case KeypairOrderField.IS_ACTIVE:
                return fields.is_active.order.apply(ascending)
            case KeypairOrderField.IS_DEFAULT:
                return fields.is_default.order.apply(ascending)
            case KeypairOrderField.RESOURCE_POLICY:
                return fields.resource_policy_name.order.apply(ascending)
            case _:
                assert_never(order.field)

    # ------------------------------------------------------------------ GQL filter/order helpers

    def _convert_user_filter(self, f: UserFilter) -> list[QueryCondition]:
        fields = UserSearchableFields.own
        conditions = [
            *self.apply_uuid_filter(f.uuid, fields.uuid.filter),
            *self.apply_string_filter(f.username, fields.username.filter),
            *self.apply_string_filter(f.email, fields.email.filter),
            *self.apply_string_filter(f.full_name, fields.full_name.filter),
            *self.apply_string_filter(f.description, fields.description.filter),
            *self.apply_enum_filter(f.status, fields.status.filter),
            *self.apply_string_filter(f.status_info, fields.status_info.filter),
            *self.apply_string_filter(f.domain_name, fields.domain_name.filter),
            *self.apply_uuid_filter(f.domain_id, fields.domain_id.filter),
            *self.apply_string_filter(f.integration_name, fields.integration_name.filter),
            *self.apply_string_filter(f.resource_policy, fields.resource_policy.filter),
            *self.apply_enum_filter(f.role, fields.role.filter),
            *self.apply_bool_filter(f.need_password_change, fields.need_password_change.filter),
            *self.apply_bool_filter(f.totp_activated, fields.totp_activated.filter),
            *self.apply_bool_filter(f.sudo_session_enabled, fields.sudo_session_enabled.filter),
            *self.apply_int_filter(f.container_uid, fields.container_uid.filter),
            *self.apply_int_filter(f.container_main_gid, fields.container_main_gid.filter),
            *self.apply_array_filter(f.container_gids, fields.container_gids.filter),
            *self.apply_datetime_filter(f.created_at, fields.created_at.filter),
            *self.apply_datetime_filter(f.modified_at, fields.modified_at.filter),
            *self.apply_to_many_filter(
                f.keypairs,
                UserSearchableFields.nested.keypairs.correlation,
                self._convert_keypair_filter,
            ),
            *self.apply_nullable_datetime_filter(
                f.totp_activated_at, fields.totp_activated_at.filter
            ),
            *self._convert_domain_filter(f.domain),
            *self._convert_project_filter(f.project),
        ]
        if f.AND:
            for sub in f.AND:
                conditions.extend(self._convert_user_filter(sub))
        if f.OR:
            or_conditions: list[QueryCondition] = []
            for sub in f.OR:
                or_conditions.extend(self._convert_user_filter(sub))
            if or_conditions:
                conditions.append(combine_conditions_or(or_conditions))
        if f.NOT:
            not_conditions: list[QueryCondition] = []
            for sub in f.NOT:
                not_conditions.extend(self._convert_user_filter(sub))
            if not_conditions:
                conditions.append(negate_conditions(not_conditions))
        return conditions

    def _convert_domain_filter(self, f: UserDomainFilter | None) -> list[QueryCondition]:
        """Deprecated. Every condition lands in one EXISTS over the user's domain."""
        if f is None:
            return []
        conditions: list[QueryCondition] = []
        if f.name is not None:
            condition = self.convert_string_filter(
                f.name,
                contains_factory=DomainConditions.by_name_contains,
                equals_factory=DomainConditions.by_name_equals,
                starts_with_factory=DomainConditions.by_name_starts_with,
                ends_with_factory=DomainConditions.by_name_ends_with,
                in_factory=DomainConditions.by_name_in,
            )
            if condition is not None:
                conditions.append(condition)
        if f.is_active is not None:
            conditions.append(DomainConditions.by_is_active(f.is_active))
        if not conditions:
            return []
        return [DeprecatedUserConditions.exists_domain_combined(conditions)]

    def _convert_project_filter(self, f: UserProjectFilter | None) -> list[QueryCondition]:
        """Deprecated. Every condition lands in one EXISTS over one of the user's projects."""
        if f is None:
            return []
        conditions: list[QueryCondition] = []
        if f.name is not None:
            condition = self.convert_string_filter(
                f.name,
                contains_factory=ProjectConditions.by_name_contains,
                equals_factory=ProjectConditions.by_name_equals,
                starts_with_factory=ProjectConditions.by_name_starts_with,
                ends_with_factory=ProjectConditions.by_name_ends_with,
                in_factory=ProjectConditions.by_name_in,
            )
            if condition is not None:
                conditions.append(condition)
        if f.is_active is not None:
            conditions.append(ProjectConditions.by_is_active(f.is_active))
        if not conditions:
            return []
        return [DeprecatedUserConditions.exists_project_combined(conditions)]

    def _convert_user_orders(self, orders: list[UserOrder]) -> list[QueryOrder]:
        return [self._convert_user_order(order) for order in orders]

    def _convert_user_order(self, order: UserOrder) -> QueryOrder:
        fields = UserSearchableFields.own
        ascending = order.direction == OrderDirection.ASC
        match order.field:
            case UserOrderField.ENTITY_ID:
                return fields.id.order.apply(ascending)
            case UserOrderField.CREATED_AT:
                return fields.created_at.order.apply(ascending)
            case UserOrderField.MODIFIED_AT:
                return fields.modified_at.order.apply(ascending)
            case UserOrderField.USERNAME:
                return fields.username.order.apply(ascending)
            case UserOrderField.EMAIL:
                return fields.email.order.apply(ascending)
            case UserOrderField.FULL_NAME:
                return fields.full_name.order.apply(ascending)
            case UserOrderField.DESCRIPTION:
                return fields.description.order.apply(ascending)
            case UserOrderField.STATUS:
                return fields.status.order.apply(ascending)
            case UserOrderField.STATUS_INFO:
                return fields.status_info.order.apply(ascending)
            case UserOrderField.ROLE:
                return fields.role.order.apply(ascending)
            case UserOrderField.DOMAIN_NAME:
                return fields.domain_name.order.apply(ascending)
            case UserOrderField.DOMAIN_ID:
                return fields.domain_id.order.apply(ascending)
            case UserOrderField.INTEGRATION_NAME:
                return fields.integration_name.order.apply(ascending)
            case UserOrderField.RESOURCE_POLICY:
                return fields.resource_policy.order.apply(ascending)
            case UserOrderField.NEED_PASSWORD_CHANGE:
                return fields.need_password_change.order.apply(ascending)
            case UserOrderField.TOTP_ACTIVATED:
                return fields.totp_activated.order.apply(ascending)
            case UserOrderField.TOTP_ACTIVATED_AT:
                return fields.totp_activated_at.order.apply(ascending)
            case UserOrderField.SUDO_SESSION_ENABLED:
                return fields.sudo_session_enabled.order.apply(ascending)
            case UserOrderField.CONTAINER_UID:
                return fields.container_uid.order.apply(ascending)
            case UserOrderField.CONTAINER_MAIN_GID:
                return fields.container_main_gid.order.apply(ascending)
            case UserOrderField.PROJECT_NAME:
                return DeprecatedUserOrders.by_project_name(ascending=ascending)
            case _:
                assert_never(order.field)

    def _build_search_searcher(self, input: SearchUsersRequest) -> UserSearcher:
        """Build a user searcher from the search request DTO."""
        conditions = self._convert_user_filter(input.filter) if input.filter else []
        orders = self._convert_user_orders(input.order) if input.order else []
        pagination = OffsetPagination(limit=input.limit, offset=input.offset)
        return UserSearcher(conditions=conditions, orders=orders, pagination=pagination)

    async def _default_access_keys(self, users: Sequence[UserData]) -> Mapping[UserID, AccessKey]:
        """The key each user authorizes with, read for every one of them in one go."""
        if not users:
            return {}
        result = await self._user.get_default_keypairs.run(
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
            entity_id=data.entity_id(),
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
                domain_id=data.domain_id,
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
