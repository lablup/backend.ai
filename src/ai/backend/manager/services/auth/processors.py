from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.processor.scope import ScopeActionProcessor
from ai.backend.manager.actions.processor.single_entity import SingleEntityActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.services.auth.actions.authorize import (
    AuthorizeAction,
    AuthorizeActionResult,
)
from ai.backend.manager.services.auth.actions.generate_ssh_keypair import (
    GenerateSSHKeypairAction,
    GenerateSSHKeypairActionResult,
)
from ai.backend.manager.services.auth.actions.get_role import GetRoleAction, GetRoleActionResult
from ai.backend.manager.services.auth.actions.get_ssh_keypair import (
    GetSSHKeypairAction,
    GetSSHKeypairActionResult,
)
from ai.backend.manager.services.auth.actions.logout import LogoutAction, LogoutActionResult
from ai.backend.manager.services.auth.actions.resolve_access_key_scope import (
    ResolveAccessKeyScopeAction,
    ResolveAccessKeyScopeResult,
)
from ai.backend.manager.services.auth.actions.resolve_user_scope import (
    ResolveUserScopeAction,
    ResolveUserScopeResult,
)
from ai.backend.manager.services.auth.actions.search_login_history import (
    SearchLoginHistoryAction,
    SearchLoginHistoryActionResult,
)
from ai.backend.manager.services.auth.actions.search_login_sessions import (
    SearchLoginSessionsAction,
    SearchLoginSessionsActionResult,
)
from ai.backend.manager.services.auth.actions.signout import SignoutAction, SignoutActionResult
from ai.backend.manager.services.auth.actions.signup import SignupAction, SignupActionResult
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


class AuthProcessors(AbstractProcessorPackage):
    logout: ActionProcessor[LogoutAction, LogoutActionResult]
    signout: ActionProcessor[SignoutAction, SignoutActionResult]
    update_full_name: ActionProcessor[UpdateFullNameAction, UpdateFullNameActionResult]
    get_ssh_keypair: SingleEntityActionProcessor[GetSSHKeypairAction, GetSSHKeypairActionResult]
    generate_ssh_keypair: ScopeActionProcessor[
        GenerateSSHKeypairAction, GenerateSSHKeypairActionResult
    ]
    upload_ssh_keypair: ScopeActionProcessor[UploadSSHKeypairAction, UploadSSHKeypairActionResult]
    get_role: ActionProcessor[GetRoleAction, GetRoleActionResult]
    authorize: ActionProcessor[AuthorizeAction, AuthorizeActionResult]
    signup: ActionProcessor[SignupAction, SignupActionResult]
    update_password: ActionProcessor[UpdatePasswordAction, UpdatePasswordActionResult]
    update_password_no_auth: ActionProcessor[
        UpdatePasswordNoAuthAction, UpdatePasswordNoAuthActionResult
    ]
    resolve_access_key_scope: ActionProcessor[
        ResolveAccessKeyScopeAction, ResolveAccessKeyScopeResult
    ]
    resolve_user_scope: ActionProcessor[ResolveUserScopeAction, ResolveUserScopeResult]
    search_login_sessions: ActionProcessor[
        SearchLoginSessionsAction, SearchLoginSessionsActionResult
    ]
    search_login_history: ActionProcessor[SearchLoginHistoryAction, SearchLoginHistoryActionResult]

    def __init__(
        self,
        service: AuthService,
        action_monitors: list[ActionMonitor],
        validators: ActionValidators,
    ) -> None:
        self.logout = ActionProcessor(service.logout, action_monitors)
        self.signout = ActionProcessor(service.signout, action_monitors)
        self.update_full_name = ActionProcessor(service.update_full_name, action_monitors)
        self.get_ssh_keypair = SingleEntityActionProcessor(
            service.get_ssh_keypair, action_monitors, validators=[validators.rbac.single_entity]
        )
        self.generate_ssh_keypair = ScopeActionProcessor(
            service.generate_ssh_keypair, action_monitors, validators=[validators.rbac.scope]
        )
        self.upload_ssh_keypair = ScopeActionProcessor(
            service.upload_ssh_keypair, action_monitors, validators=[validators.rbac.scope]
        )
        self.get_role = ActionProcessor(service.get_role, action_monitors)
        self.authorize = ActionProcessor(service.authorize, action_monitors)
        self.signup = ActionProcessor(service.signup, action_monitors)
        self.update_password = ActionProcessor(service.update_password, action_monitors)
        self.update_password_no_auth = ActionProcessor(
            service.update_password_no_auth, action_monitors
        )
        self.resolve_access_key_scope = ActionProcessor(
            service.resolve_access_key_scope, action_monitors
        )
        self.resolve_user_scope = ActionProcessor(service.resolve_user_scope, action_monitors)
        self.search_login_sessions = ActionProcessor(service.search_login_sessions, action_monitors)
        self.search_login_history = ActionProcessor(service.search_login_history, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            LogoutAction.spec(),
            SignoutAction.spec(),
            UpdateFullNameAction.spec(),
            GetSSHKeypairAction.spec(),
            GenerateSSHKeypairAction.spec(),
            UploadSSHKeypairAction.spec(),
            GetRoleAction.spec(),
            AuthorizeAction.spec(),
            SignupAction.spec(),
            UpdatePasswordAction.spec(),
            UpdatePasswordNoAuthAction.spec(),
            ResolveAccessKeyScopeAction.spec(),
            ResolveUserScopeAction.spec(),
            SearchLoginSessionsAction.spec(),
            SearchLoginHistoryAction.spec(),
        ]
