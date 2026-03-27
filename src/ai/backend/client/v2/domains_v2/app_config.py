"""V2 SDK client for the app configuration domain."""

from __future__ import annotations

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.app_config.request import (
    UpsertDomainConfigInput,
    UpsertUserConfigInput,
)
from ai.backend.common.dto.manager.v2.app_config.response import (
    AppConfigNode,
    DeleteDomainConfigPayload,
    DeleteUserConfigPayload,
    UpsertDomainConfigPayloadDTO,
    UpsertUserConfigPayloadDTO,
)

_PATH = "/v2/app-configs"


class V2AppConfigClient(BaseDomainClient):
    """SDK client for app configuration operations."""

    # ------------------------------------------------------------------ Domain config

    async def get_domain_config(self, domain_name: str) -> AppConfigNode:
        """Get domain-level app configuration."""
        return await self._client.typed_request(
            "GET",
            f"{_PATH}/domains/{domain_name}",
            response_model=AppConfigNode,
        )

    async def upsert_domain_config(
        self, domain_name: str, request: UpsertDomainConfigInput
    ) -> UpsertDomainConfigPayloadDTO:
        """Create or update domain-level app configuration."""
        return await self._client.typed_request(
            "PUT",
            f"{_PATH}/domains/{domain_name}",
            request=request,
            response_model=UpsertDomainConfigPayloadDTO,
        )

    async def delete_domain_config(self, domain_name: str) -> DeleteDomainConfigPayload:
        """Delete domain-level app configuration."""
        return await self._client.typed_request(
            "DELETE",
            f"{_PATH}/domains/{domain_name}",
            response_model=DeleteDomainConfigPayload,
        )

    # ------------------------------------------------------------------ User config

    async def get_user_config(self, user_id: str) -> AppConfigNode:
        """Get user-level app configuration."""
        return await self._client.typed_request(
            "GET",
            f"{_PATH}/users/{user_id}",
            response_model=AppConfigNode,
        )

    async def upsert_user_config(
        self, user_id: str, request: UpsertUserConfigInput
    ) -> UpsertUserConfigPayloadDTO:
        """Create or update user-level app configuration."""
        return await self._client.typed_request(
            "PUT",
            f"{_PATH}/users/{user_id}",
            request=request,
            response_model=UpsertUserConfigPayloadDTO,
        )

    async def delete_user_config(self, user_id: str) -> DeleteUserConfigPayload:
        """Delete user-level app configuration."""
        return await self._client.typed_request(
            "DELETE",
            f"{_PATH}/users/{user_id}",
            response_model=DeleteUserConfigPayload,
        )

    # ------------------------------------------------------------------ Merged config

    async def get_merged_config(self, user_id: str) -> AppConfigNode:
        """Get merged app configuration for a user."""
        return await self._client.typed_request(
            "GET",
            f"{_PATH}/users/{user_id}/merged",
            response_model=AppConfigNode,
        )
