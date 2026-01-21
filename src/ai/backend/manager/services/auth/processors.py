from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
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
    signout: ActionProcessor[SignoutAction, SignoutActionResult]
    update_full_name: ActionProcessor[UpdateFullNameAction, UpdateFullNameActionResult]
    get_ssh_keypair: ActionProcessor[GetSSHKeypairAction, GetSSHKeypairActionResult]
    generate_ssh_keypair: ActionProcessor[GenerateSSHKeypairAction, GenerateSSHKeypairActionResult]
    upload_ssh_keypair: ActionProcessor[UploadSSHKeypairAction, UploadSSHKeypairActionResult]
    get_role: ActionProcessor[GetRoleAction, GetRoleActionResult]
    authorize: ActionProcessor[AuthorizeAction, AuthorizeActionResult]
    signup: ActionProcessor[SignupAction, SignupActionResult]
    update_password: ActionProcessor[UpdatePasswordAction, UpdatePasswordActionResult]
    update_password_no_auth: ActionProcessor[
        UpdatePasswordNoAuthAction, UpdatePasswordNoAuthActionResult
    ]

    def __init__(self, service: AuthService, action_monitors: list[ActionMonitor]) -> None:
        self.signout = ActionProcessor(service.signout, action_monitors)
        self.update_full_name = ActionProcessor(service.update_full_name, action_monitors)
        self.get_ssh_keypair = ActionProcessor(service.get_ssh_keypair, action_monitors)
        self.generate_ssh_keypair = ActionProcessor(service.generate_ssh_keypair, action_monitors)
        self.upload_ssh_keypair = ActionProcessor(service.upload_ssh_keypair, action_monitors)
        self.get_role = ActionProcessor(service.get_role, action_monitors)
        self.authorize = ActionProcessor(service.authorize, action_monitors)
        self.signup = ActionProcessor(service.signup, action_monitors)
        self.update_password = ActionProcessor(service.update_password, action_monitors)
        self.update_password_no_auth = ActionProcessor(
            service.update_password_no_auth, action_monitors
        )

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
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
        ]
