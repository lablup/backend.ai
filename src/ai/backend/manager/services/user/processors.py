from ai.backend.common.data.entity.error_log import ERROR_LOG_FIELD_TYPE
from ai.backend.common.data.entity.keypair import KEYPAIR_FIELD_TYPE
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.actions.registry.field import LookupFieldGroup
from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.registry.types import FieldGroupMeta
from ai.backend.manager.actions.v2.bulk.processor import BulkActionProcessor
from ai.backend.manager.actions.v2.field.processor import SingleFieldActionProcessor
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.lookup.processor import LookupActionProcessor
from ai.backend.manager.actions.v2.ops.result import (
    BatchOpsResult,
    FieldKeyLookupOpsResult,
    FieldOwnerLookupOpsResult,
    LookupOpsResult,
    OwnedFieldsOpsResult,
    ScopedBatchOpsResult,
)
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
from ai.backend.manager.data.error_log.types import ErrorLogData
from ai.backend.manager.data.keypair.types import KeyPairData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.services.user.actions.admin_month_stats import (
    AdminMonthStatsAction,
    AdminMonthStatsActionResult,
)
from ai.backend.manager.services.user.actions.bootstrap_script import (
    GetBootstrapScriptAction,
    GetBootstrapScriptActionResult,
    UpdateBootstrapScriptAction,
    UpdateBootstrapScriptActionResult,
)
from ai.backend.manager.services.user.actions.create_keypair_dotfile import (
    CreateKeypairDotfileAction,
    CreateKeypairDotfileActionResult,
)
from ai.backend.manager.services.user.actions.create_user import (
    BulkCreateUserAction,
    BulkCreateUserActionResult,
    CreateUserAction,
    CreateUserActionResult,
)
from ai.backend.manager.services.user.actions.delete_keypair_dotfile import (
    DeleteKeypairDotfileAction,
    DeleteKeypairDotfileActionResult,
)
from ai.backend.manager.services.user.actions.delete_user import (
    DeleteUserAction,
    DeleteUserActionResult,
)
from ai.backend.manager.services.user.actions.get_user import (
    GetUserAction,
    GetUserActionResult,
)
from ai.backend.manager.services.user.actions.keypair_ops import (
    AdminCreateKeypairAction,
    AdminCreateKeypairActionResult,
    AdminDeleteSSHKeypairAction,
    AdminDeleteSSHKeypairActionResult,
    AdminGetSSHKeypairAction,
    AdminGetSSHKeypairActionResult,
    AdminRegisterSSHKeypairAction,
    AdminRegisterSSHKeypairActionResult,
    AdminSearchKeypairsAction,
    AdminSearchKeypairsActionResult,
    GetDefaultKeypairsAction,
    GetKeypairAction,
    GetKeypairActionResult,
    IssueMyKeypairAction,
    IssueMyKeypairActionResult,
    PurgeKeypairAction,
    PurgeKeypairActionResult,
    SearchMyKeypairsAction,
    SearchMyKeypairsActionResult,
    SwitchDefaultAccessKeyAction,
    SwitchDefaultAccessKeyActionResult,
    UpdateKeypairAction,
    UpdateKeypairActionResult,
)
from ai.backend.manager.services.user.actions.lookup import LookupUserAction
from ai.backend.manager.services.user.actions.lookup_keypair import (
    LookupKeypairByAccessKeyAction,
)
from ai.backend.manager.services.user.actions.lookup_keypair_owner import (
    LookupBulkKeypairOwnerAction,
    LookupKeypairOwnerAction,
    LookupKeypairOwnerByAccessKeyAction,
)
from ai.backend.manager.services.user.actions.purge_user import (
    BulkPurgeUserAction,
    BulkPurgeUserActionResult,
    PurgeUserAction,
    PurgeUserActionResult,
)
from ai.backend.manager.services.user.actions.restore_user import (
    RestoreUserAction,
    RestoreUserActionResult,
)
from ai.backend.manager.services.user.actions.search_users import GlobalSearchUsersAction
from ai.backend.manager.services.user.actions.search_users_by_domain import (
    SearchUsersByDomainAction,
)
from ai.backend.manager.services.user.actions.search_users_by_project import (
    SearchUsersByProjectAction,
)
from ai.backend.manager.services.user.actions.search_users_by_role import SearchUsersByRoleAction
from ai.backend.manager.services.user.actions.update_keypair_dotfile import (
    UpdateKeypairDotfileAction,
    UpdateKeypairDotfileActionResult,
)
from ai.backend.manager.services.user.actions.update_user import (
    BulkUpdateUserAction,
    BulkUpdateUserActionResult,
    UpdateUserAction,
    UpdateUserActionResult,
)
from ai.backend.manager.services.user.actions.user_month_stats import (
    UserMonthStatsAction,
    UserMonthStatsActionResult,
)
from ai.backend.manager.services.user.error_log.actions.lookup_owner import (
    LookupBulkErrorLogOwnerAction,
    LookupErrorLogOwnerAction,
)
from ai.backend.manager.services.user.error_log.processors import ErrorLogProcessors
from ai.backend.manager.services.user.service import UserService


class UserProcessors:
    lookup: LookupActionProcessor[LookupUserAction, LookupOpsResult[UserID]]
    lookup_keypair_owner: LookupActionProcessor[
        LookupKeypairOwnerByAccessKeyAction, FieldOwnerLookupOpsResult
    ]
    keypair_group: LookupFieldGroup[KeyPairData]
    error_log: ErrorLogProcessors
    global_search: GlobalActionProcessor[GlobalSearchUsersAction, BatchOpsResult[UserData]]
    search_users_by_domain: ScopeActionProcessor[
        SearchUsersByDomainAction, ScopedBatchOpsResult[UserData]
    ]
    search_users_by_project: ScopeActionProcessor[
        SearchUsersByProjectAction, ScopedBatchOpsResult[UserData]
    ]
    search_users_by_role: GlobalActionProcessor[SearchUsersByRoleAction, BatchOpsResult[UserData]]
    create_user: ScopeActionProcessor[CreateUserAction, CreateUserActionResult]
    get_user: SingleEntityActionProcessor[GetUserAction, GetUserActionResult]
    update_user: SingleEntityActionProcessor[UpdateUserAction, UpdateUserActionResult]
    delete_user: SingleEntityActionProcessor[DeleteUserAction, DeleteUserActionResult]
    restore_user: SingleEntityActionProcessor[RestoreUserAction, RestoreUserActionResult]
    purge_user: SingleEntityActionProcessor[PurgeUserAction, PurgeUserActionResult]
    bulk_create_users: GlobalActionProcessor[BulkCreateUserAction, BulkCreateUserActionResult]
    bulk_modify_users: GlobalActionProcessor[BulkUpdateUserAction, BulkUpdateUserActionResult]
    bulk_purge_users: GlobalActionProcessor[BulkPurgeUserAction, BulkPurgeUserActionResult]
    user_month_stats: SingleEntityActionProcessor[UserMonthStatsAction, UserMonthStatsActionResult]
    admin_month_stats: GlobalActionProcessor[AdminMonthStatsAction, AdminMonthStatsActionResult]
    issue_my_keypair: SingleEntityActionProcessor[IssueMyKeypairAction, IssueMyKeypairActionResult]
    lookup_keypair: LookupActionProcessor[LookupKeypairByAccessKeyAction, FieldKeyLookupOpsResult]
    get_keypair: SingleFieldActionProcessor[GetKeypairAction, GetKeypairActionResult]
    purge_keypair: SingleFieldActionProcessor[PurgeKeypairAction, PurgeKeypairActionResult]
    switch_default_access_key: SingleEntityActionProcessor[
        SwitchDefaultAccessKeyAction, SwitchDefaultAccessKeyActionResult
    ]
    get_default_keypairs: BulkActionProcessor[
        GetDefaultKeypairsAction, OwnedFieldsOpsResult[UserID, KeyPairData]
    ]
    update_keypair: SingleFieldActionProcessor[UpdateKeypairAction, UpdateKeypairActionResult]
    search_my_keypairs: ScopeActionProcessor[SearchMyKeypairsAction, SearchMyKeypairsActionResult]
    admin_create_keypair: SingleEntityActionProcessor[
        AdminCreateKeypairAction, AdminCreateKeypairActionResult
    ]
    admin_search_keypairs: GlobalActionProcessor[
        AdminSearchKeypairsAction, AdminSearchKeypairsActionResult
    ]
    admin_register_ssh_keypair: SingleEntityActionProcessor[
        AdminRegisterSSHKeypairAction, AdminRegisterSSHKeypairActionResult
    ]
    admin_delete_ssh_keypair: SingleEntityActionProcessor[
        AdminDeleteSSHKeypairAction, AdminDeleteSSHKeypairActionResult
    ]
    admin_get_ssh_keypair: SingleEntityActionProcessor[
        AdminGetSSHKeypairAction, AdminGetSSHKeypairActionResult
    ]
    create_dotfile: SingleEntityActionProcessor[
        CreateKeypairDotfileAction, CreateKeypairDotfileActionResult
    ]
    update_dotfile: SingleEntityActionProcessor[
        UpdateKeypairDotfileAction, UpdateKeypairDotfileActionResult
    ]
    delete_dotfile: SingleEntityActionProcessor[
        DeleteKeypairDotfileAction, DeleteKeypairDotfileActionResult
    ]
    get_bootstrap_script: SingleEntityActionProcessor[
        GetBootstrapScriptAction, GetBootstrapScriptActionResult
    ]
    update_bootstrap_script: SingleEntityActionProcessor[
        UpdateBootstrapScriptAction, UpdateBootstrapScriptActionResult
    ]

    def __init__(
        self,
        group: ProcessorGroup[UserData],
        user_service: UserService,
    ) -> None:
        self.lookup = group.public_lookup_ops(LookupUserAction)
        self.lookup_keypair_owner = group.key_owner_lookup_ops(LookupKeypairOwnerByAccessKeyAction)
        self.global_search = group.global_search_ops(GlobalSearchUsersAction)
        self.search_users_by_domain = group.scope_search_ops(SearchUsersByDomainAction)
        self.search_users_by_project = group.scope_search_ops(SearchUsersByProjectAction)
        self.search_users_by_role = group.global_search_ops(SearchUsersByRoleAction)
        self.create_user = group.scope(CreateUserAction, user_service.create_user)
        self.get_user = group.single_entity(GetUserAction, user_service.get_user)
        self.update_user = group.single_entity(UpdateUserAction, user_service.update_user)
        self.delete_user = group.single_entity(DeleteUserAction, user_service.delete_user)
        self.restore_user = group.single_entity(RestoreUserAction, user_service.restore_user)
        self.purge_user = group.single_entity(PurgeUserAction, user_service.purge_user)
        self.bulk_create_users = group.global_scope(
            BulkCreateUserAction, user_service.bulk_create_users
        )
        self.bulk_modify_users = group.global_scope(
            BulkUpdateUserAction, user_service.bulk_modify_users
        )
        self.bulk_purge_users = group.global_scope(
            BulkPurgeUserAction, user_service.bulk_purge_users
        )
        self.user_month_stats = group.single_entity(
            UserMonthStatsAction, user_service.user_month_stats
        )
        self.admin_month_stats = group.global_scope(
            AdminMonthStatsAction, user_service.admin_month_stats
        )
        self.issue_my_keypair = group.single_entity(
            IssueMyKeypairAction, user_service.issue_my_keypair
        )
        self.switch_default_access_key = group.single_entity(
            SwitchDefaultAccessKeyAction, user_service.switch_default_access_key
        )
        self.search_my_keypairs = group.scope(
            SearchMyKeypairsAction, user_service.search_my_keypairs
        )
        self.admin_create_keypair = group.single_entity(
            AdminCreateKeypairAction, user_service.admin_create_keypair
        )
        self.admin_search_keypairs = group.global_scope(
            AdminSearchKeypairsAction, user_service.admin_search_keypairs
        )
        self.admin_register_ssh_keypair = group.single_entity(
            AdminRegisterSSHKeypairAction, user_service.admin_register_ssh_keypair
        )
        self.admin_delete_ssh_keypair = group.single_entity(
            AdminDeleteSSHKeypairAction, user_service.admin_delete_ssh_keypair
        )
        self.admin_get_ssh_keypair = group.single_entity(
            AdminGetSSHKeypairAction, user_service.admin_get_ssh_keypair
        )
        self.create_dotfile = group.single_entity(
            CreateKeypairDotfileAction, user_service.create_dotfile
        )
        self.update_dotfile = group.single_entity(
            UpdateKeypairDotfileAction, user_service.update_dotfile
        )
        self.delete_dotfile = group.single_entity(
            DeleteKeypairDotfileAction, user_service.delete_dotfile
        )
        self.get_bootstrap_script = group.single_entity(
            GetBootstrapScriptAction, user_service.get_bootstrap_script
        )
        self.update_bootstrap_script = group.single_entity(
            UpdateBootstrapScriptAction, user_service.update_bootstrap_script
        )

        self.keypair_group = group.field_group(
            FieldGroupMeta(KEYPAIR_FIELD_TYPE),
            KeyPairData,
            LookupKeypairOwnerAction,
            LookupBulkKeypairOwnerAction,
        )
        self.get_default_keypairs = self.keypair_group.atomic_bulk_get_ops(GetDefaultKeypairsAction)
        self.lookup_keypair = group.key_field_lookup_ops(LookupKeypairByAccessKeyAction)
        self.get_keypair = self.keypair_group.single_field(
            GetKeypairAction, user_service.get_keypair
        )
        self.update_keypair = self.keypair_group.single_field(
            UpdateKeypairAction, user_service.update_keypair
        )
        self.purge_keypair = self.keypair_group.single_field(
            PurgeKeypairAction, user_service.purge_keypair
        )
        self.error_log = ErrorLogProcessors(
            group.field_group(
                FieldGroupMeta(ERROR_LOG_FIELD_TYPE),
                ErrorLogData,
                LookupErrorLogOwnerAction,
                LookupBulkErrorLogOwnerAction,
            )
        )
