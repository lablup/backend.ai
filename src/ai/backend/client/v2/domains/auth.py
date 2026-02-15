from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.auth.request import (
    AuthorizeRequest,
    GetRoleRequest,
    SignoutRequest,
    SignupRequest,
    UpdateFullNameRequest,
    UpdatePasswordNoAuthRequest,
    UpdatePasswordRequest,
    UploadSSHKeypairRequest,
    VerifyAuthRequest,
)
from ai.backend.common.dto.manager.auth.response import (
    AuthorizeResponse,
    GetRoleResponse,
    GetSSHKeypairResponse,
    SignoutResponse,
    SignupResponse,
    SSHKeypairResponse,
    UpdateFullNameResponse,
    UpdatePasswordNoAuthResponse,
    UpdatePasswordResponse,
    VerifyAuthResponse,
)


class AuthClient(BaseDomainClient):
    async def authorize(self, request: AuthorizeRequest) -> AuthorizeResponse:
        return await self._client.typed_request(
            "POST",
            "/auth/authorize",
            request=request,
            response_model=AuthorizeResponse,
        )

    async def signup(self, request: SignupRequest) -> SignupResponse:
        return await self._client.typed_request(
            "POST",
            "/auth/signup",
            request=request,
            response_model=SignupResponse,
        )

    async def signout(self, request: SignoutRequest) -> SignoutResponse:
        return await self._client.typed_request(
            "POST",
            "/auth/signout",
            request=request,
            response_model=SignoutResponse,
        )

    async def get_role(self, request: GetRoleRequest) -> GetRoleResponse:
        params: dict[str, str] = {}
        if request.group is not None:
            params["group"] = str(request.group)
        return await self._client.typed_request(
            "GET",
            "/auth/role",
            response_model=GetRoleResponse,
            params=params,
        )

    async def update_password(self, request: UpdatePasswordRequest) -> UpdatePasswordResponse:
        return await self._client.typed_request(
            "POST",
            "/auth/update-password",
            request=request,
            response_model=UpdatePasswordResponse,
        )

    async def update_password_no_auth(
        self, request: UpdatePasswordNoAuthRequest
    ) -> UpdatePasswordNoAuthResponse:
        return await self._client.typed_request(
            "POST",
            "/auth/update-password-no-auth",
            request=request,
            response_model=UpdatePasswordNoAuthResponse,
        )

    async def update_full_name(self, request: UpdateFullNameRequest) -> UpdateFullNameResponse:
        return await self._client.typed_request(
            "POST",
            "/auth/update-full-name",
            request=request,
            response_model=UpdateFullNameResponse,
        )

    async def get_ssh_keypair(self) -> GetSSHKeypairResponse:
        return await self._client.typed_request(
            "GET",
            "/auth/ssh-keypair",
            response_model=GetSSHKeypairResponse,
        )

    async def generate_ssh_keypair(self) -> SSHKeypairResponse:
        return await self._client.typed_request(
            "PATCH",
            "/auth/ssh-keypair",
            response_model=SSHKeypairResponse,
        )

    async def upload_ssh_keypair(self, request: UploadSSHKeypairRequest) -> SSHKeypairResponse:
        return await self._client.typed_request(
            "POST",
            "/auth/ssh-keypair",
            request=request,
            response_model=SSHKeypairResponse,
        )

    async def verify_auth(self, request: VerifyAuthRequest) -> VerifyAuthResponse:
        return await self._client.typed_request(
            "POST",
            "/auth/test",
            request=request,
            response_model=VerifyAuthResponse,
        )
