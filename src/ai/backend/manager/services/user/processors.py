from ai.backend.common.data.entity.bootstrap_script import BootstrapScriptFieldType
from ai.backend.common.data.entity.error_log import ErrorLogFieldType
from ai.backend.common.data.entity.keypair import KeyPairFieldType, KeyPairID
from ai.backend.common.data.entity.ssh_keypair import SSHKeypairFieldType
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.registry.field import LookupFieldGroup
from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.registry.types import FieldGroupMeta
from ai.backend.manager.actions.v2.bulk.partial_processor import PartialBulkActionProcessor
from ai.backend.manager.actions.v2.bulk.processor import BulkActionProcessor
from ai.backend.manager.actions.v2.field.bulk_lookup import BulkFieldKeyLookupOpsResult
from ai.backend.manager.actions.v2.field.bulk_processor import PartialBulkFieldActionProcessor
from ai.backend.manager.actions.v2.field.processor import SingleFieldActionProcessor
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.lookup.bulk_processor import BulkLookupActionProcessor
from ai.backend.manager.actions.v2.lookup.partial_bulk_processor import (
    PartialBulkLookupActionProcessor,
)
from ai.backend.manager.actions.v2.lookup.processor import LookupActionProcessor
from ai.backend.manager.actions.v2.ops.result import (
    BatchOpsResult,
    FieldKeyLookupOpsResult,
    FieldOwnerLookupOpsResult,
    LookupOpsResult,
    OwnedFieldsOpsResult,
    ScopedBatchOpsResult,
    ScopedFieldsOpsResult,
)
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
from ai.backend.manager.data.bootstrap_script.types import BootstrapScriptData
from ai.backend.manager.data.error_log.types import ErrorLogData
from ai.backend.manager.data.keypair.types import KeyPairData
from ai.backend.manager.data.ssh_keypair.types import SSHKeypairData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.services.user.actions.admin_month_stats import (
    AdminMonthStatsAction,
    AdminMonthStatsActionResult,
)
from ai.backend.manager.services.user.actions.bootstrap_script import (
    GetDefaultBootstrapScriptAction,
    GetDefaultBootstrapScriptActionResult,
    UpdateDefaultBootstrapScriptAction,
    UpdateDefaultBootstrapScriptActionResult,
)
from ai.backend.manager.services.user.actions.bulk_get import BulkGetUsersAction
from ai.backend.manager.services.user.actions.bulk_get_keypairs import BulkGetKeypairsAction
from ai.backend.manager.services.user.actions.bulk_lookup import BulkLookupUsersAction
from ai.backend.manager.services.user.actions.bulk_lookup_keypairs import BulkLookupKeypairsAction
from ai.backend.manager.services.user.actions.create_dotfile import (
    CreateDotfileAction,
    CreateDotfileActionResult,
)
from ai.backend.manager.services.user.actions.create_user import (
    BulkCreateUserAction,
    BulkCreateUserActionResult,
    CreateUserAction,
    CreateUserActionResult,
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
    GetDefaultKeypairsAction,
    GetKeypairAction,
    GetKeypairActionResult,
    IssueMyKeypairAction,
    IssueMyKeypairActionResult,
    PurgeKeypairAction,
    PurgeKeypairActionResult,
    SearchMyKeypairsAction,
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
from ai.backend.manager.services.user.actions.scoped_search import (
    ScopedSearchUsersAction,
)
from ai.backend.manager.services.user.actions.search_users import GlobalSearchUsersAction
from ai.backend.manager.services.user.actions.ssh_keypair_ops import (
    LookupBulkSSHKeypairOwnerAction,
    LookupSSHKeypairOwnerAction,
    SearchSSHKeypairsAction,
)
from ai.backend.manager.services.user.actions.switch_default_dotfile import (
    SwitchDefaultDotfileAction,
    SwitchDefaultDotfileActionResult,
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
from ai.backend.manager.services.user.bootstrap_script.actions.lookup_owner import (
    LookupBootstrapScriptOwnerAction,
    LookupBulkBootstrapScriptOwnerAction,
)
from ai.backend.manager.services.user.bootstrap_script.processors import BootstrapScriptProcessors
from ai.backend.manager.services.user.error_log.actions.lookup_owner import (
    LookupBulkErrorLogOwnerAction,
    LookupErrorLogOwnerAction,
)
from ai.backend.manager.services.user.error_log.processors import ErrorLogProcessors
from ai.backend.manager.services.user.service import UserService


class UserProcessors:
    lookup: LookupActionProcessor[LookupUserAction, LookupOpsResult[UserID]]
    bulk_lookup: PartialBulkLookupActionProcessor[BulkLookupUsersAction]
    lookup_keypair_owner: LookupActionProcessor[
        LookupKeypairOwnerByAccessKeyAction, FieldOwnerLookupOpsResult
    ]
    keypair_group: LookupFieldGroup[KeyPairData]
    ssh_keypair_group: LookupFieldGroup[SSHKeypairData]
    error_log: ErrorLogProcessors
    bootstrap_script: BootstrapScriptProcessors
    bulk_get: PartialBulkActionProcessor[BulkGetUsersAction, UserData]
    global_search: GlobalActionProcessor[GlobalSearchUsersAction, BatchOpsResult[UserData]]
    scoped_search: ScopeActionProcessor[ScopedSearchUsersAction, ScopedBatchOpsResult[UserData]]
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
    bulk_lookup_keypairs: BulkLookupActionProcessor[
        BulkLookupKeypairsAction, BulkFieldKeyLookupOpsResult[AccessKey, KeyPairID]
    ]
    bulk_get_keypairs: PartialBulkFieldActionProcessor[BulkGetKeypairsAction, KeyPairData]
    lookup_keypair: LookupActionProcessor[LookupKeypairByAccessKeyAction, FieldKeyLookupOpsResult]
    get_keypair: SingleFieldActionProcessor[GetKeypairAction, GetKeypairActionResult]
    purge_keypair: SingleFieldActionProcessor[PurgeKeypairAction, PurgeKeypairActionResult]
    switch_default_access_key: SingleEntityActionProcessor[
        SwitchDefaultAccessKeyAction, SwitchDefaultAccessKeyActionResult
    ]
    get_default_keypairs: BulkActionProcessor[
        GetDefaultKeypairsAction, OwnedFieldsOpsResult[UserID, KeyPairData]
    ]
    search_ssh_keypairs: BulkActionProcessor[
        SearchSSHKeypairsAction, ScopedFieldsOpsResult[SSHKeypairData]
    ]
    update_keypair: SingleFieldActionProcessor[UpdateKeypairAction, UpdateKeypairActionResult]
    search_my_keypairs: ScopeActionProcessor[
        SearchMyKeypairsAction, ScopedFieldsOpsResult[KeyPairData]
    ]
    admin_create_keypair: SingleEntityActionProcessor[
        AdminCreateKeypairAction, AdminCreateKeypairActionResult
    ]
    admin_search_keypairs: GlobalActionProcessor[
        AdminSearchKeypairsAction, BatchOpsResult[KeyPairData]
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
    create_dotfile: SingleEntityActionProcessor[CreateDotfileAction, CreateDotfileActionResult]
    switch_default_dotfile: SingleEntityActionProcessor[
        SwitchDefaultDotfileAction, SwitchDefaultDotfileActionResult
    ]
    get_default_bootstrap_script: SingleEntityActionProcessor[
        GetDefaultBootstrapScriptAction, GetDefaultBootstrapScriptActionResult
    ]
    update_default_bootstrap_script: SingleEntityActionProcessor[
        UpdateDefaultBootstrapScriptAction, UpdateDefaultBootstrapScriptActionResult
    ]

    def __init__(
        self,
        group: ProcessorGroup[UserData],
        user_service: UserService,
    ) -> None:
        self.lookup = group.lookup_ops(LookupUserAction)
        self.bulk_lookup = group.bulk_lookup_ops(BulkLookupUsersAction)
        self.lookup_keypair_owner = group.key_owner_lookup_ops(LookupKeypairOwnerByAccessKeyAction)
        self.bulk_get = group.partial_bulk_get_ops(BulkGetUsersAction)
        self.global_search = group.global_searcher_ops(GlobalSearchUsersAction)
        self.scoped_search = group.scoped_search_ops(ScopedSearchUsersAction)
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
        self.admin_create_keypair = group.single_entity(
            AdminCreateKeypairAction, user_service.admin_create_keypair
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
        self.create_dotfile = group.single_entity(CreateDotfileAction, user_service.create_dotfile)
        self.switch_default_dotfile = group.single_entity(
            SwitchDefaultDotfileAction, user_service.switch_default_dotfile
        )
        self.get_default_bootstrap_script = group.single_entity(
            GetDefaultBootstrapScriptAction, user_service.get_default_bootstrap_script
        )
        self.update_default_bootstrap_script = group.single_entity(
            UpdateDefaultBootstrapScriptAction, user_service.update_default_bootstrap_script
        )

        self.keypair_group = group.field_group(
            FieldGroupMeta(KeyPairFieldType()),
            KeyPairData,
            LookupKeypairOwnerAction,
            LookupBulkKeypairOwnerAction,
        )
        self.admin_search_keypairs = self.keypair_group.global_searcher_ops(
            AdminSearchKeypairsAction
        )
        self.search_my_keypairs = self.keypair_group.search_ops(SearchMyKeypairsAction)
        self.get_default_keypairs = self.keypair_group.atomic_bulk_get_ops(GetDefaultKeypairsAction)
        self.ssh_keypair_group = group.field_group(
            FieldGroupMeta(SSHKeypairFieldType()),
            SSHKeypairData,
            LookupSSHKeypairOwnerAction,
            LookupBulkSSHKeypairOwnerAction,
        )
        self.search_ssh_keypairs = self.ssh_keypair_group.atomic_bulk_scoped_search_ops(
            SearchSSHKeypairsAction
        )
        self.lookup_keypair = group.key_field_lookup_ops(LookupKeypairByAccessKeyAction)
        self.bulk_lookup_keypairs = group.public_bulk_key_field_lookup_ops(BulkLookupKeypairsAction)
        self.bulk_get_keypairs = self.keypair_group.partial_bulk_get_ops(BulkGetKeypairsAction)
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
                FieldGroupMeta(ErrorLogFieldType()),
                ErrorLogData,
                LookupErrorLogOwnerAction,
                LookupBulkErrorLogOwnerAction,
            )
        )
        self.bootstrap_script = BootstrapScriptProcessors(
            group,
            group.field_group(
                FieldGroupMeta(BootstrapScriptFieldType()),
                BootstrapScriptData,
                LookupBootstrapScriptOwnerAction,
                LookupBulkBootstrapScriptOwnerAction,
            ),
            user_service,
        )
