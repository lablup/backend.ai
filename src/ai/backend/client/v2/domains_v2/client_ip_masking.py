"""V2 SDK client for the client IP masking domain."""

from __future__ import annotations

from typing import Final
from uuid import UUID

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.client_ip_masking.request import (
    AdminPurgeClientIPMaskingPolicyInput,
    AdminSearchClientIPMaskingPoliciesInput,
    AdminUpsertClientIPMaskingPolicyInput,
    PartialBulkPurgeClientIPMaskingPoliciesInput,
)
from ai.backend.common.dto.manager.v2.client_ip_masking.response import (
    AdminSearchClientIPMaskingPoliciesPayload,
    ClientIPMaskingPolicyNode,
    ClientIPMaskingPolicyPayload,
)
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload

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

    async def upsert(
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

    async def purge(self, policy_id: UUID) -> ClientIPMaskingPolicyPayload:
        """Drop one target's policy so it falls back to the default."""
        return await self._client.typed_request(
            "DELETE",
            f"{_PATH}/{policy_id}",
            response_model=ClientIPMaskingPolicyPayload,
        )

    async def partial_bulk_purge(
        self, request: PartialBulkPurgeClientIPMaskingPoliciesInput
    ) -> PartialBulkPayload[ClientIPMaskingPolicyNode]:
        """Drop several policies, answering for each one."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/partial-bulk-purge",
            request=request,
            response_model=PartialBulkPayload[ClientIPMaskingPolicyNode],
        )

    async def admin_upsert(
        self,
        request: AdminUpsertClientIPMaskingPolicyInput,
    ) -> ClientIPMaskingPolicyPayload:
        """Deprecated. Use :meth:`upsert`."""
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
        """Deprecated. Use :meth:`purge`."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/purge",
            request=request,
            response_model=ClientIPMaskingPolicyPayload,
        )
