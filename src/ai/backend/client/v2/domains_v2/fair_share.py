"""V2 SDK client for the fair share domain."""

from __future__ import annotations

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.fair_share.request import (
    BulkUpsertDomainFairShareWeightInput,
    BulkUpsertProjectFairShareWeightInput,
    BulkUpsertUserFairShareWeightInput,
    GetDomainFairShareInput,
    GetProjectFairShareInput,
    GetUserFairShareInput,
    SearchDomainFairSharesInput,
    SearchProjectFairSharesInput,
    SearchUserFairSharesInput,
    UpsertDomainFairShareWeightInput,
    UpsertProjectFairShareWeightInput,
    UpsertUserFairShareWeightInput,
)
from ai.backend.common.dto.manager.v2.fair_share.response import (
    BulkUpsertDomainFairShareWeightPayload,
    BulkUpsertProjectFairShareWeightPayload,
    BulkUpsertUserFairShareWeightPayload,
    GetDomainFairSharePayload,
    GetProjectFairSharePayload,
    GetUserFairSharePayload,
    SearchDomainFairSharesPayload,
    SearchProjectFairSharesPayload,
    SearchUserFairSharesPayload,
    UpsertDomainFairShareWeightPayload,
    UpsertProjectFairShareWeightPayload,
    UpsertUserFairShareWeightPayload,
)

_PATH = "/v2/fair-share"


class V2FairShareClient(BaseDomainClient):
    """SDK client for fair share operations."""

    # ========== Domain Fair Share ==========

    async def get_domain(self, request: GetDomainFairShareInput) -> GetDomainFairSharePayload:
        """Get a single domain fair share record."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/domains/get",
            request=request,
            response_model=GetDomainFairSharePayload,
        )

    async def search_domain(
        self, request: SearchDomainFairSharesInput
    ) -> SearchDomainFairSharesPayload:
        """Search domain fair shares with filters and pagination."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/domains/search",
            request=request,
            response_model=SearchDomainFairSharesPayload,
        )

    async def upsert_domain(
        self, request: UpsertDomainFairShareWeightInput
    ) -> UpsertDomainFairShareWeightPayload:
        """Upsert a domain fair share weight."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/domains/upsert",
            request=request,
            response_model=UpsertDomainFairShareWeightPayload,
        )

    async def bulk_upsert_domain(
        self, request: BulkUpsertDomainFairShareWeightInput
    ) -> BulkUpsertDomainFairShareWeightPayload:
        """Bulk upsert domain fair share weights."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/domains/bulk-upsert",
            request=request,
            response_model=BulkUpsertDomainFairShareWeightPayload,
        )

    # ========== Project Fair Share ==========

    async def get_project(self, request: GetProjectFairShareInput) -> GetProjectFairSharePayload:
        """Get a single project fair share record."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/projects/get",
            request=request,
            response_model=GetProjectFairSharePayload,
        )

    async def search_project(
        self, request: SearchProjectFairSharesInput
    ) -> SearchProjectFairSharesPayload:
        """Search project fair shares with filters and pagination."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/projects/search",
            request=request,
            response_model=SearchProjectFairSharesPayload,
        )

    async def upsert_project(
        self, request: UpsertProjectFairShareWeightInput
    ) -> UpsertProjectFairShareWeightPayload:
        """Upsert a project fair share weight."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/projects/upsert",
            request=request,
            response_model=UpsertProjectFairShareWeightPayload,
        )

    async def bulk_upsert_project(
        self, request: BulkUpsertProjectFairShareWeightInput
    ) -> BulkUpsertProjectFairShareWeightPayload:
        """Bulk upsert project fair share weights."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/projects/bulk-upsert",
            request=request,
            response_model=BulkUpsertProjectFairShareWeightPayload,
        )

    # ========== User Fair Share ==========

    async def get_user(self, request: GetUserFairShareInput) -> GetUserFairSharePayload:
        """Get a single user fair share record."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/users/get",
            request=request,
            response_model=GetUserFairSharePayload,
        )

    async def search_user(self, request: SearchUserFairSharesInput) -> SearchUserFairSharesPayload:
        """Search user fair shares with filters and pagination."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/users/search",
            request=request,
            response_model=SearchUserFairSharesPayload,
        )

    async def upsert_user(
        self, request: UpsertUserFairShareWeightInput
    ) -> UpsertUserFairShareWeightPayload:
        """Upsert a user fair share weight."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/users/upsert",
            request=request,
            response_model=UpsertUserFairShareWeightPayload,
        )

    async def bulk_upsert_user(
        self, request: BulkUpsertUserFairShareWeightInput
    ) -> BulkUpsertUserFairShareWeightPayload:
        """Bulk upsert user fair share weights."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/users/bulk-upsert",
            request=request,
            response_model=BulkUpsertUserFairShareWeightPayload,
        )
