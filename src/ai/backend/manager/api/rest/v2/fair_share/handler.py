"""REST v2 handler for the fair share domain."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import APIResponse, BodyParam
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
from ai.backend.logging import BraceStyleAdapter

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.fair_share import FairShareAdapter

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class V2FairShareHandler:
    """REST v2 handler for fair share operations."""

    def __init__(self, *, adapter: FairShareAdapter) -> None:
        self._adapter = adapter

    # ========== Domain Fair Share ==========

    async def admin_get_domain(
        self,
        body: BodyParam[GetDomainFairShareInput],
    ) -> APIResponse:
        """Get a single domain fair share record."""
        result = await self._adapter.get_domain(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_search_domain(
        self,
        body: BodyParam[SearchDomainFairSharesInput],
    ) -> APIResponse:
        """Search domain fair shares with filters and pagination."""
        result = await self._adapter.search_domain(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_upsert_domain(
        self,
        body: BodyParam[UpsertDomainFairShareWeightInput],
    ) -> APIResponse:
        """Upsert a domain fair share weight."""
        result = await self._adapter.upsert_domain(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_bulk_upsert_domain(
        self,
        body: BodyParam[BulkUpsertDomainFairShareWeightInput],
    ) -> APIResponse:
        """Bulk upsert domain fair share weights."""
        result = await self._adapter.bulk_upsert_domain(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    # ========== Project Fair Share ==========

    async def admin_get_project(
        self,
        body: BodyParam[GetProjectFairShareInput],
    ) -> APIResponse:
        """Get a single project fair share record."""
        result = await self._adapter.get_project(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_search_project(
        self,
        body: BodyParam[SearchProjectFairSharesInput],
    ) -> APIResponse:
        """Search project fair shares with filters and pagination."""
        result = await self._adapter.search_project(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_upsert_project(
        self,
        body: BodyParam[UpsertProjectFairShareWeightInput],
    ) -> APIResponse:
        """Upsert a project fair share weight."""
        result = await self._adapter.upsert_project(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_bulk_upsert_project(
        self,
        body: BodyParam[BulkUpsertProjectFairShareWeightInput],
    ) -> APIResponse:
        """Bulk upsert project fair share weights."""
        result = await self._adapter.bulk_upsert_project(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    # ========== User Fair Share ==========

    async def admin_get_user(
        self,
        body: BodyParam[GetUserFairShareInput],
    ) -> APIResponse:
        """Get a single user fair share record."""
        result = await self._adapter.get_user(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_search_user(
        self,
        body: BodyParam[SearchUserFairSharesInput],
    ) -> APIResponse:
        """Search user fair shares with filters and pagination."""
        result = await self._adapter.search_user(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_upsert_user(
        self,
        body: BodyParam[UpsertUserFairShareWeightInput],
    ) -> APIResponse:
        """Upsert a user fair share weight."""
        result = await self._adapter.upsert_user(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_bulk_upsert_user(
        self,
        body: BodyParam[BulkUpsertUserFairShareWeightInput],
    ) -> APIResponse:
        """Bulk upsert user fair share weights."""
        result = await self._adapter.bulk_upsert_user(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
