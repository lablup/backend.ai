from __future__ import annotations

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.config import (
    CreateDomainDotfileRequest,
    CreateDotfileResponse,
    CreateGroupDotfileRequest,
    CreateUserDotfileRequest,
    DeleteDomainDotfileRequest,
    DeleteDotfileResponse,
    DeleteGroupDotfileRequest,
    DeleteUserDotfileRequest,
    GetBootstrapScriptResponse,
    GetDomainDotfileRequest,
    GetDotfileResponse,
    GetGroupDotfileRequest,
    GetUserDotfileRequest,
    ListDotfilesResponse,
    UpdateBootstrapScriptRequest,
    UpdateBootstrapScriptResponse,
    UpdateDomainDotfileRequest,
    UpdateDotfileResponse,
    UpdateGroupDotfileRequest,
    UpdateUserDotfileRequest,
)


class ConfigClient(BaseDomainClient):
    """SDK v2 client for configuration (dotfile) endpoints.

    Covers user, group, and domain dotfiles, plus bootstrap scripts.
    """

    # ---- User Config ----

    async def create_user_dotfile(self, request: CreateUserDotfileRequest) -> CreateDotfileResponse:
        return await self._client.typed_request(
            "POST",
            "/user-config/dotfiles",
            request=request,
            response_model=CreateDotfileResponse,
        )

    async def get_user_dotfile(self, request: GetUserDotfileRequest) -> GetDotfileResponse:
        return await self._client.typed_request(
            "GET",
            "/user-config/dotfiles",
            request=request,
            response_model=GetDotfileResponse,
        )

    async def list_user_dotfiles(self) -> ListDotfilesResponse:
        return await self._client.typed_request(
            "GET",
            "/user-config/dotfiles",
            response_model=ListDotfilesResponse,
        )

    async def update_user_dotfile(self, request: UpdateUserDotfileRequest) -> UpdateDotfileResponse:
        return await self._client.typed_request(
            "PATCH",
            "/user-config/dotfiles",
            request=request,
            response_model=UpdateDotfileResponse,
        )

    async def delete_user_dotfile(self, request: DeleteUserDotfileRequest) -> DeleteDotfileResponse:
        return await self._client.typed_request(
            "DELETE",
            "/user-config/dotfiles",
            request=request,
            response_model=DeleteDotfileResponse,
        )

    async def get_bootstrap_script(self) -> GetBootstrapScriptResponse:
        return await self._client.typed_request(
            "GET",
            "/user-config/bootstrap-script",
            response_model=GetBootstrapScriptResponse,
        )

    async def update_bootstrap_script(
        self, request: UpdateBootstrapScriptRequest
    ) -> UpdateBootstrapScriptResponse:
        return await self._client.typed_request(
            "POST",
            "/user-config/bootstrap-script",
            request=request,
            response_model=UpdateBootstrapScriptResponse,
        )

    # ---- Group Config ----

    async def create_group_dotfile(
        self, request: CreateGroupDotfileRequest
    ) -> CreateDotfileResponse:
        return await self._client.typed_request(
            "POST",
            "/group-config/dotfiles",
            request=request,
            response_model=CreateDotfileResponse,
        )

    async def get_group_dotfile(self, request: GetGroupDotfileRequest) -> GetDotfileResponse:
        return await self._client.typed_request(
            "GET",
            "/group-config/dotfiles",
            request=request,
            response_model=GetDotfileResponse,
        )

    async def list_group_dotfiles(self, request: GetGroupDotfileRequest) -> ListDotfilesResponse:
        return await self._client.typed_request(
            "GET",
            "/group-config/dotfiles",
            request=request,
            response_model=ListDotfilesResponse,
        )

    async def update_group_dotfile(
        self, request: UpdateGroupDotfileRequest
    ) -> UpdateDotfileResponse:
        return await self._client.typed_request(
            "PATCH",
            "/group-config/dotfiles",
            request=request,
            response_model=UpdateDotfileResponse,
        )

    async def delete_group_dotfile(
        self, request: DeleteGroupDotfileRequest
    ) -> DeleteDotfileResponse:
        return await self._client.typed_request(
            "DELETE",
            "/group-config/dotfiles",
            request=request,
            response_model=DeleteDotfileResponse,
        )

    # ---- Domain Config ----

    async def create_domain_dotfile(
        self, request: CreateDomainDotfileRequest
    ) -> CreateDotfileResponse:
        return await self._client.typed_request(
            "POST",
            "/domain-config/dotfiles",
            request=request,
            response_model=CreateDotfileResponse,
        )

    async def get_domain_dotfile(self, request: GetDomainDotfileRequest) -> GetDotfileResponse:
        return await self._client.typed_request(
            "GET",
            "/domain-config/dotfiles",
            request=request,
            response_model=GetDotfileResponse,
        )

    async def list_domain_dotfiles(self, request: GetDomainDotfileRequest) -> ListDotfilesResponse:
        return await self._client.typed_request(
            "GET",
            "/domain-config/dotfiles",
            request=request,
            response_model=ListDotfilesResponse,
        )

    async def update_domain_dotfile(
        self, request: UpdateDomainDotfileRequest
    ) -> UpdateDotfileResponse:
        return await self._client.typed_request(
            "PATCH",
            "/domain-config/dotfiles",
            request=request,
            response_model=UpdateDotfileResponse,
        )

    async def delete_domain_dotfile(
        self, request: DeleteDomainDotfileRequest
    ) -> DeleteDotfileResponse:
        return await self._client.typed_request(
            "DELETE",
            "/domain-config/dotfiles",
            request=request,
            response_model=DeleteDotfileResponse,
        )
