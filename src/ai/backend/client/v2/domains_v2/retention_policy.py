"""V2 SDK client for the retention policy domain (superadmin only)."""

from __future__ import annotations

from uuid import UUID

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.retention_policy.request import (
    CreateRetentionPolicyInput,
    SearchRetentionPoliciesInput,
    UpdateRetentionPolicyInput,
)
from ai.backend.common.dto.manager.v2.retention_policy.response import (
    CreateRetentionPolicyPayload,
    DeleteRetentionPolicyPayload,
    PurgeRetentionPolicyPayload,
    RetentionPolicyNode,
    SearchRetentionPoliciesPayload,
    UpdateRetentionPolicyPayload,
)

_PATH = "/v2/retention-policies"


class V2RetentionPolicyClient(BaseDomainClient):
    """SDK client for retention policy operations."""

    async def search(self, request: SearchRetentionPoliciesInput) -> SearchRetentionPoliciesPayload:
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/search",
            request=request,
            response_model=SearchRetentionPoliciesPayload,
        )

    async def get(self, policy_id: UUID) -> RetentionPolicyNode:
        return await self._client.typed_request(
            "GET",
            f"{_PATH}/{policy_id}",
            response_model=RetentionPolicyNode,
        )

    async def create(self, request: CreateRetentionPolicyInput) -> CreateRetentionPolicyPayload:
        return await self._client.typed_request(
            "POST",
            _PATH,
            request=request,
            response_model=CreateRetentionPolicyPayload,
        )

    async def update(
        self, policy_id: UUID, request: UpdateRetentionPolicyInput
    ) -> UpdateRetentionPolicyPayload:
        return await self._client.typed_request(
            "PATCH",
            f"{_PATH}/{policy_id}",
            request=request,
            response_model=UpdateRetentionPolicyPayload,
        )

    async def delete(self, policy_id: UUID) -> DeleteRetentionPolicyPayload:
        return await self._client.typed_request(
            "DELETE",
            f"{_PATH}/{policy_id}",
            response_model=DeleteRetentionPolicyPayload,
        )

    async def purge(self, policy_id: UUID) -> PurgeRetentionPolicyPayload:
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/{policy_id}/purge",
            response_model=PurgeRetentionPolicyPayload,
        )
