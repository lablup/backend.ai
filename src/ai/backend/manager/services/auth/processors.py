from typing import Any

from ai.backend.common.data.entity.login_history import LOGIN_HISTORY_FIELD_TYPE
from ai.backend.common.data.entity.login_session import LOGIN_SESSION_FIELD_TYPE
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.actions.registry.field import LookupFieldGroup
from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.registry.types import FieldGroupMeta
from ai.backend.manager.actions.v2.field.processor import SingleFieldActionProcessor
from ai.backend.manager.actions.v2.global_scope.processor import (
    AnonymousGlobalActionProcessor,
    GlobalActionProcessor,
    PublicActionProcessor,
)
from ai.backend.manager.actions.v2.lookup.processor import LookupActionProcessor
from ai.backend.manager.actions.v2.ops.result import (
    BatchOpsResult,
    LookupOpsResult,
    ScopedFieldsOpsResult,
)
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor
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
    PublicGetRoleAction,
    PublicGetRoleActionResult,
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
from ai.backend.manager.services.auth.actions.resolve_user_id_by_access_key import (
    ResolveUserIDByAccessKeyAction,
)
from ai.backend.manager.services.auth.actions.resolve_user_scope import (
    PublicResolveUserScopeAction,
    PublicResolveUserScopeResult,
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

    ``auth_group`` holds the credential and login-session state that names no entity:
    the caller of a sign-in, a sign-out or a password reset holds no principal yet, and
    an administrator reaching every session names none either. ``user_group`` holds what
    one user's row, credentials or login rows answer for.

    The three anonymous wirings are the sign-in path itself. Each authenticates its caller
    inside the service, against the password the row stores or the hook plugins' verdict,
    which is what a gate would otherwise have done.
    """

    authorize: AnonymousGlobalActionProcessor[AuthorizeAction, AuthorizeActionResult]
    signup: AnonymousGlobalActionProcessor[SignupAction, SignupActionResult]
    update_password_no_auth: AnonymousGlobalActionProcessor[
        UpdatePasswordNoAuthAction, UpdatePasswordNoAuthActionResult
    ]
    public_get_role: PublicActionProcessor[PublicGetRoleAction, PublicGetRoleActionResult]
    public_resolve_access_key_scope: PublicActionProcessor[
        PublicResolveAccessKeyScopeAction, PublicResolveAccessKeyScopeResult
    ]
    public_resolve_user_scope: PublicActionProcessor[
        PublicResolveUserScopeAction, PublicResolveUserScopeResult
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
    resolve_user_id_by_access_key: LookupActionProcessor[
        ResolveUserIDByAccessKeyAction, LookupOpsResult[UserID]
    ]
    login_sessions: LookupFieldGroup[LoginSessionData]
    login_history: LookupFieldGroup[LoginHistoryData]
    search_login_sessions: ScopeActionProcessor[
        SearchLoginSessionsAction, ScopedFieldsOpsResult[LoginSessionData]
    ]
    search_login_history: ScopeActionProcessor[
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
        auth_group: ProcessorGroup[Any],
        user_group: ProcessorGroup[Any],
        service: AuthService,
    ) -> None:
        self.authorize = auth_group.anonymous_global(AuthorizeAction, service.authorize)
        self.update_password_no_auth = auth_group.anonymous_global(
            UpdatePasswordNoAuthAction, service.update_password_no_auth
        )
        self.public_get_role = auth_group.public(PublicGetRoleAction, service.get_role)
        self.public_resolve_access_key_scope = auth_group.public(
            PublicResolveAccessKeyScopeAction, service.resolve_access_key_scope
        )
        self.public_resolve_user_scope = auth_group.public(
            PublicResolveUserScopeAction, service.resolve_user_scope
        )
        self.global_revoke_login_session = auth_group.global_scope(
            GlobalRevokeLoginSessionAction, service.global_revoke_login_session
        )
        self.global_unblock_user = auth_group.global_scope(
            GlobalUnblockUserAction, service.global_unblock_user
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
        self.resolve_user_id_by_access_key = user_group.lookup_ops(ResolveUserIDByAccessKeyAction)
        self.login_sessions = user_group.field_group(
            FieldGroupMeta(LOGIN_SESSION_FIELD_TYPE),
            LoginSessionData,
            LookupLoginSessionOwnerAction,
            LookupBulkLoginSessionOwnerAction,
        )
        self.login_history = user_group.field_group(
            FieldGroupMeta(LOGIN_HISTORY_FIELD_TYPE),
            LoginHistoryData,
            LookupLoginHistoryOwnerAction,
            LookupBulkLoginHistoryOwnerAction,
        )
        self.revoke_login_session = self.login_sessions.single_field(
            RevokeLoginSessionAction, service.revoke_login_session
        )
        self.search_login_sessions = self.login_sessions.search_ops(SearchLoginSessionsAction)
        self.search_login_history = self.login_history.search_ops(SearchLoginHistoryAction)
        self.global_search_login_sessions = self.login_sessions.global_search_ops(
            GlobalSearchLoginSessionsAction
        )
        self.global_search_login_history = self.login_history.global_search_ops(
            GlobalSearchLoginHistoryAction
        )
