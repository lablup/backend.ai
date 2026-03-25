"""
Auth DTOs v2 for Manager API.
"""

from ai.backend.common.dto.manager.v2.auth.request import (
    AuthorizeInput,
    GetRoleInput,
    RevokeMyKeypairInput,
    SignoutInput,
    SignupInput,
    SwitchMyMainAccessKeyInput,
    UpdateFullNameInput,
    UpdatePasswordInput,
    UpdatePasswordNoAuthInput,
    UploadSSHKeypairInput,
    VerifyAuthInput,
)
from ai.backend.common.dto.manager.v2.auth.response import (
    AuthorizePayload,
    GetRolePayload,
    GetSSHKeypairPayload,
    SignoutPayload,
    SignupPayload,
    SSHKeypairPayload,
    UpdateFullNamePayload,
    UpdatePasswordNoAuthPayload,
    UpdatePasswordPayload,
    VerifyAuthPayload,
)
from ai.backend.common.dto.manager.v2.auth.types import (
    AuthCredentialInfo,
    AuthResponseType,
    AuthTokenType,
    PasswordChangeInfo,
    RoleInfo,
    SSHKeypairInfo,
    TwoFactorInfo,
    TwoFactorType,
)

__all__ = (
    # Types
    "AuthCredentialInfo",
    "AuthResponseType",
    "AuthTokenType",
    "PasswordChangeInfo",
    "RoleInfo",
    "SSHKeypairInfo",
    "TwoFactorInfo",
    "TwoFactorType",
    # Input models (request)
    "AuthorizeInput",
    "GetRoleInput",
    "RevokeMyKeypairInput",
    "SignoutInput",
    "SignupInput",
    "SwitchMyMainAccessKeyInput",
    "UpdateFullNameInput",
    "UpdatePasswordInput",
    "UpdatePasswordNoAuthInput",
    "UploadSSHKeypairInput",
    "VerifyAuthInput",
    # Payload models (response)
    "AuthorizePayload",
    "GetRolePayload",
    "GetSSHKeypairPayload",
    "SignoutPayload",
    "SignupPayload",
    "SSHKeypairPayload",
    "UpdateFullNamePayload",
    "UpdatePasswordNoAuthPayload",
    "UpdatePasswordPayload",
    "VerifyAuthPayload",
)
