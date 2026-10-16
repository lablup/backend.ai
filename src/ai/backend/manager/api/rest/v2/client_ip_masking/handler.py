"""REST v2 handler for the client IP masking domain."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
from ai.backend.common.data.entity.client_ip_masking import ClientIPMaskingPolicyID
from ai.backend.common.dto.manager.v2.client_ip_masking.request import (
    AdminPurgeClientIPMaskingPolicyInput,
    AdminSearchClientIPMaskingPoliciesInput,
    AdminUpsertClientIPMaskingPolicyInput,
    PartialBulkPurgeClientIPMaskingPoliciesInput,
)
from ai.backend.manager.api.rest.v2.path_params import ClientIPMaskingPolicyIdPathParam

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.client_ip_masking.adapter import ClientIPMaskingAdapter


class V2ClientIPMaskingHandler:
    """REST v2 handler for the client IP masking policies."""

    def __init__(self, *, adapter: ClientIPMaskingAdapter) -> None:
        self._adapter = adapter

    async def admin_search(
        self,
        body: BodyParam[AdminSearchClientIPMaskingPoliciesInput],
    ) -> APIResponse:
        """Read the masking set for every target."""
        result = await self._adapter.admin_search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def upsert(
        self,
        body: BodyParam[AdminUpsertClientIPMaskingPolicyInput],
    ) -> APIResponse:
        """Set the masking one target gets."""
        result = await self._adapter.upsert(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def purge(
        self,
        path: PathParam[ClientIPMaskingPolicyIdPathParam],
    ) -> APIResponse:
        """Drop one target's policy so it falls back to the default."""
        result = await self._adapter.purge(ClientIPMaskingPolicyID(path.parsed.policy_id))
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def partial_bulk_purge(
        self,
        body: BodyParam[PartialBulkPurgeClientIPMaskingPoliciesInput],
    ) -> APIResponse:
        """Drop several policies, answering for each one."""
        result = await self._adapter.partial_bulk_purge(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_purge(
        self,
        body: BodyParam[AdminPurgeClientIPMaskingPolicyInput],
    ) -> APIResponse:
        """Deprecated. Use `DELETE /v2/client-ip-masking-policies/{policy_id}`."""
        result = await self._adapter.purge(ClientIPMaskingPolicyID(body.parsed.id))
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
