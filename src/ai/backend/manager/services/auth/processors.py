from typing import Any

from ai.backend.common.data.entity.login_history import LoginHistoryFieldType
from ai.backend.common.data.entity.login_session import LoginSessionFieldType
from ai.backend.manager.actions.registry.field import LookupFieldGroup
from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.registry.types import FieldGroupMeta
from ai.backend.manager.actions.v2.bulk.processor import BulkActionProcessor
from ai.backend.manager.actions.v2.field.processor import SingleFieldActionProcessor
from ai.backend.manager.actions.v2.global_scope.processor import (
    AnonymousGlobalActionProcessor,
    GlobalActionProcessor,
    PublicActionProcessor,
)
from ai.backend.manager.actions.v2.ops.result import (
    BatchOpsResult,
    ScopedFieldsOpsResult,
)
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
from ai.backend.manager.data.auth.login_session_types import LoginHistoryData, LoginSessionData
from ai.backend.manager.services.auth.actions.authorize import (
    AuthorizeAction,
    AuthorizeActionResult,
)
from ai.backend.manager.services.auth.actions.generate_ssh_keypair import (
    GenerateSSHKeypairAction,
    GenerateSSHKeypairActionResult,
)
from ai.backend.manager.services.auth.actions.get_role import (
    GetRoleAction,
    GetRoleActionResult,
)
from ai.backend.manager.services.auth.actions.get_ssh_keypair import (
    GetSSHKeypairAction,
    GetSSHKeypairActionResult,
)
from ai.backend.manager.services.auth.actions.logout import LogoutAction, LogoutActionResult
from ai.backend.manager.services.auth.actions.lookup_login_history_owner import (
    LookupBulkLoginHistoryOwnerAction,
    LookupLoginHistoryOwnerAction,
)
from ai.backend.manager.services.auth.actions.lookup_login_session_owner import (
    LookupBulkLoginSessionOwnerAction,
    LookupLoginSessionOwnerAction,
)
from ai.backend.manager.services.auth.actions.resolve_access_key_scope import (
    PublicResolveAccessKeyScopeAction,
    PublicResolveAccessKeyScopeResult,
)
from ai.backend.manager.services.auth.actions.revoke_login_session import (
    GlobalRevokeLoginSessionAction,
    RevokeLoginSessionAction,
    RevokeLoginSessionActionResult,
)
from ai.backend.manager.services.auth.actions.search_login_history import (
    GlobalSearchLoginHistoryAction,
    SearchLoginHistoryAction,
)
from ai.backend.manager.services.auth.actions.search_login_sessions import (
    GlobalSearchLoginSessionsAction,
    SearchLoginSessionsAction,
)
from ai.backend.manager.services.auth.actions.signout import SignoutAction, SignoutActionResult
from ai.backend.manager.services.auth.actions.signup import SignupAction, SignupActionResult
from ai.backend.manager.services.auth.actions.unblock_user import (
    GlobalUnblockUserAction,
    GlobalUnblockUserActionResult,
)
from ai.backend.manager.services.auth.actions.update_full_name import (
    UpdateFullNameAction,
    UpdateFullNameActionResult,
)
from ai.backend.manager.services.auth.actions.update_password import (
    UpdatePasswordAction,
    UpdatePasswordActionResult,
)
from ai.backend.manager.services.auth.actions.update_password_no_auth import (
    UpdatePasswordNoAuthAction,
    UpdatePasswordNoAuthActionResult,
)
from ai.backend.manager.services.auth.actions.upload_ssh_keypair import (
    UploadSSHKeypairAction,
    UploadSSHKeypairActionResult,
)
from ai.backend.manager.services.auth.service import AuthService


class AuthProcessors:
    """Every auth operation, split by what answers for it.

    Neither group is typed on one ``EntityData``: the login rows a user owns are read
    through the user group, so its ops wirings answer with more than one kind.

    ``global_group`` holds what names no entity: the caller of a sign-in or a password
    reset holds no principal yet, and an administrator reaching every session or login
    block names none either. ``user_group`` holds what one user's row, credentials or
    login rows answer for.

    The three anonymous wirings are the sign-in path itself. Each authenticates its caller
    inside the service, against the password the row stores or the hook plugins' verdict,
    which is what a gate would otherwise have done.
    """

    authorize: AnonymousGlobalActionProcessor[AuthorizeAction, AuthorizeActionResult]
    signup: AnonymousGlobalActionProcessor[SignupAction, SignupActionResult]
    update_password_no_auth: AnonymousGlobalActionProcessor[
        UpdatePasswordNoAuthAction, UpdatePasswordNoAuthActionResult
    ]
    get_role: SingleEntityActionProcessor[GetRoleAction, GetRoleActionResult]
    public_resolve_access_key_scope: PublicActionProcessor[
        PublicResolveAccessKeyScopeAction, PublicResolveAccessKeyScopeResult
    ]
    global_revoke_login_session: GlobalActionProcessor[
        GlobalRevokeLoginSessionAction, RevokeLoginSessionActionResult
    ]
    global_unblock_user: GlobalActionProcessor[
        GlobalUnblockUserAction, GlobalUnblockUserActionResult
    ]
    logout: SingleEntityActionProcessor[LogoutAction, LogoutActionResult]
    signout: SingleEntityActionProcessor[SignoutAction, SignoutActionResult]
    update_full_name: SingleEntityActionProcessor[UpdateFullNameAction, UpdateFullNameActionResult]
    update_password: SingleEntityActionProcessor[UpdatePasswordAction, UpdatePasswordActionResult]
    get_ssh_keypair: SingleEntityActionProcessor[GetSSHKeypairAction, GetSSHKeypairActionResult]
    generate_ssh_keypair: SingleEntityActionProcessor[
        GenerateSSHKeypairAction, GenerateSSHKeypairActionResult
    ]
    upload_ssh_keypair: SingleEntityActionProcessor[
        UploadSSHKeypairAction, UploadSSHKeypairActionResult
    ]
    revoke_login_session: SingleFieldActionProcessor[
        RevokeLoginSessionAction, RevokeLoginSessionActionResult
    ]
    login_sessions: LookupFieldGroup[LoginSessionData]
    login_history: LookupFieldGroup[LoginHistoryData]
    search_login_sessions: BulkActionProcessor[
        SearchLoginSessionsAction, ScopedFieldsOpsResult[LoginSessionData]
    ]
    search_login_history: BulkActionProcessor[
        SearchLoginHistoryAction, ScopedFieldsOpsResult[LoginHistoryData]
    ]
    global_search_login_sessions: GlobalActionProcessor[
        GlobalSearchLoginSessionsAction, BatchOpsResult[LoginSessionData]
    ]
    global_search_login_history: GlobalActionProcessor[
        GlobalSearchLoginHistoryAction, BatchOpsResult[LoginHistoryData]
    ]

    def __init__(
        self,
        global_group: ProcessorGroup[Any],
        user_group: ProcessorGroup[Any],
        service: AuthService,
    ) -> None:
        self.authorize = global_group.anonymous_global(AuthorizeAction, service.authorize)
        self.update_password_no_auth = global_group.anonymous_global(
            UpdatePasswordNoAuthAction, service.update_password_no_auth
        )
        self.global_revoke_login_session = global_group.global_scope(
            GlobalRevokeLoginSessionAction, service.global_revoke_login_session
        )
        self.global_unblock_user = global_group.global_scope(
            GlobalUnblockUserAction, service.global_unblock_user
        )
        self.get_role = user_group.single_entity(GetRoleAction, service.get_role)
        self.public_resolve_access_key_scope = user_group.public(
            PublicResolveAccessKeyScopeAction, service.resolve_access_key_scope
        )
        self.signup = user_group.anonymous_global(SignupAction, service.signup)
        self.logout = user_group.single_entity(LogoutAction, service.logout)
        self.signout = user_group.single_entity(SignoutAction, service.signout)
        self.update_full_name = user_group.single_entity(
            UpdateFullNameAction, service.update_full_name
        )
        self.update_password = user_group.single_entity(
            UpdatePasswordAction, service.update_password
        )
        self.get_ssh_keypair = user_group.single_entity(
            GetSSHKeypairAction, service.get_ssh_keypair
        )
        self.generate_ssh_keypair = user_group.single_entity(
            GenerateSSHKeypairAction, service.generate_ssh_keypair
        )
        self.upload_ssh_keypair = user_group.single_entity(
            UploadSSHKeypairAction, service.upload_ssh_keypair
        )
        self.login_sessions = user_group.field_group(
            FieldGroupMeta(LoginSessionFieldType()),
            LoginSessionData,
            LookupLoginSessionOwnerAction,
            LookupBulkLoginSessionOwnerAction,
        )
        self.login_history = user_group.field_group(
            FieldGroupMeta(LoginHistoryFieldType()),
            LoginHistoryData,
            LookupLoginHistoryOwnerAction,
            LookupBulkLoginHistoryOwnerAction,
        )
        self.revoke_login_session = self.login_sessions.single_field(
            RevokeLoginSessionAction, service.revoke_login_session
        )
        self.search_login_sessions = self.login_sessions.atomic_bulk_scoped_search_ops(
            SearchLoginSessionsAction
        )
        self.search_login_history = self.login_history.atomic_bulk_scoped_search_ops(
            SearchLoginHistoryAction
        )
        self.global_search_login_sessions = self.login_sessions.global_searcher_ops(
            GlobalSearchLoginSessionsAction
        )
        self.global_search_login_history = self.login_history.global_searcher_ops(
            GlobalSearchLoginHistoryAction
        )
