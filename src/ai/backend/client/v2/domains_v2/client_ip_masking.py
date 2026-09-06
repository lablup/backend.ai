"""V2 SDK client for the client IP masking domain."""

from __future__ import annotations

from typing import Final

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.client_ip_masking.request import (
    AdminPurgeClientIPMaskingPolicyInput,
    AdminSearchClientIPMaskingPoliciesInput,
    AdminUpsertClientIPMaskingPolicyInput,
)
from ai.backend.common.dto.manager.v2.client_ip_masking.response import (
    AdminSearchClientIPMaskingPoliciesPayload,
    ClientIPMaskingPolicyPayload,
)

_PATH: Final = "/v2/client-ip-masking-policies"


class V2ClientIPMaskingClient(BaseDomainClient):
    """SDK client for the client IP masking policies."""

    async def admin_search(
        self,
        request: AdminSearchClientIPMaskingPoliciesInput,
    ) -> AdminSearchClientIPMaskingPoliciesPayload:
        """Read the masking set for every target."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/search",
            request=request,
            response_model=AdminSearchClientIPMaskingPoliciesPayload,
        )

    async def admin_upsert(
        self,
        request: AdminUpsertClientIPMaskingPolicyInput,
    ) -> ClientIPMaskingPolicyPayload:
        """Set the masking one target gets."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/upsert",
            request=request,
            response_model=ClientIPMaskingPolicyPayload,
        )

    async def admin_purge(
        self,
        request: AdminPurgeClientIPMaskingPolicyInput,
    ) -> ClientIPMaskingPolicyPayload:
        """Drop one target's policy so it falls back to the default."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/purge",
            request=request,
            response_model=ClientIPMaskingPolicyPayload,
        )
