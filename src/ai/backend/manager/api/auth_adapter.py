"""
Adapters to convert auth ActionResult objects to Response DTOs.
"""

from __future__ import annotations

from ai.backend.common.dto.manager.auth.response import (
    AuthorizeResponse,
    GetRoleResponse,
    GetSSHKeypairResponse,
    SignupResponse,
    SSHKeypairResponse,
    UpdatePasswordNoAuthResponse,
)
from ai.backend.common.dto.manager.auth.types import (
    AuthResponseType,
    AuthSuccessResponse,
)
from ai.backend.manager.services.auth.actions.authorize import AuthorizeActionResult
from ai.backend.manager.services.auth.actions.generate_ssh_keypair import (
    GenerateSSHKeypairActionResult,
)
from ai.backend.manager.services.auth.actions.get_role import GetRoleActionResult
from ai.backend.manager.services.auth.actions.get_ssh_keypair import GetSSHKeypairActionResult
from ai.backend.manager.services.auth.actions.signup import SignupActionResult
from ai.backend.manager.services.auth.actions.update_password_no_auth import (
    UpdatePasswordNoAuthActionResult,
)
from ai.backend.manager.services.auth.actions.upload_ssh_keypair import UploadSSHKeypairActionResult

__all__ = ("AuthAdapter",)


class AuthAdapter:
    """Adapter for converting auth ActionResult to Response DTO."""

    def convert_authorize_result(self, result: AuthorizeActionResult) -> AuthorizeResponse:
        """Convert AuthorizeActionResult to AuthorizeResponse.

        Note: Caller must check result.stream_response before calling this method.
        This method only handles the keypair authentication case.
        """
        if result.authorization_result is None:
            raise ValueError("authorization_result is required for keypair authentication")
        auth_result = result.authorization_result
        return AuthorizeResponse(
            data=AuthSuccessResponse(
                response_type=AuthResponseType.SUCCESS,
                access_key=auth_result.access_key,
                secret_key=auth_result.secret_key,
                role=auth_result.role,
                status=auth_result.status,
            )
        )

    def convert_get_role_result(self, result: GetRoleActionResult) -> GetRoleResponse:
        """Convert GetRoleActionResult to GetRoleResponse."""
        return GetRoleResponse(
            global_role=result.global_role,
            domain_role=result.domain_role,
            group_role=result.group_role,
        )

    def convert_signup_result(self, result: SignupActionResult) -> SignupResponse:
        """Convert SignupActionResult to SignupResponse."""
        return SignupResponse(
            access_key=result.access_key,
            secret_key=result.secret_key,
        )

    def convert_update_password_no_auth_result(
        self, result: UpdatePasswordNoAuthActionResult
    ) -> UpdatePasswordNoAuthResponse:
        """Convert UpdatePasswordNoAuthActionResult to UpdatePasswordNoAuthResponse."""
        return UpdatePasswordNoAuthResponse(
            password_changed_at=result.password_changed_at,
        )

    def convert_get_ssh_keypair_result(
        self, result: GetSSHKeypairActionResult
    ) -> GetSSHKeypairResponse:
        """Convert GetSSHKeypairActionResult to GetSSHKeypairResponse (public key only)."""
        return GetSSHKeypairResponse(
            ssh_public_key=result.public_key,
        )

    def convert_generate_ssh_keypair_result(
        self, result: GenerateSSHKeypairActionResult
    ) -> SSHKeypairResponse:
        """Convert GenerateSSHKeypairActionResult to SSHKeypairResponse."""
        return SSHKeypairResponse(
            ssh_public_key=result.ssh_keypair.ssh_public_key,
            ssh_private_key=result.ssh_keypair.ssh_private_key,
        )

    def convert_upload_ssh_keypair_result(
        self, result: UploadSSHKeypairActionResult
    ) -> SSHKeypairResponse:
        """Convert UploadSSHKeypairActionResult to SSHKeypairResponse."""
        return SSHKeypairResponse(
            ssh_public_key=result.ssh_keypair.ssh_public_key,
            ssh_private_key=result.ssh_keypair.ssh_private_key,
        )
