"""V2 SDK client for the app config fragment domain."""

from __future__ import annotations

from typing import Final

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
    AdminSearchAppConfigFragmentInput,
    BulkPurgeAppConfigFragmentInput,
    MyAppConfigFragmentsByNamesInput,
    MyUpsertAppConfigFragmentsInput,
    ScopedAppConfigFragmentsByNamesInput,
    ScopedUpsertAppConfigFragmentsInput,
)
from ai.backend.common.dto.manager.v2.app_config_fragment.response import (
    AppConfigFragmentNode,
    AppConfigFragmentsByNamesResponse,
    BulkPurgeAppConfigFragmentPayload,
    PurgeAppConfigFragmentPayload,
    SearchAppConfigFragmentPayload,
    UpsertAppConfigFragmentsPayload,
)
from ai.backend.common.identifier.app_config_fragment import AppConfigFragmentID

_PATH: Final = "/v2/app-config-fragments"


class V2AppConfigFragmentClient(BaseDomainClient):
    """SDK client for app config fragment operations.

    A fragment is addressed by ``(scope, config_name)``, so the write is an upsert and the
    read takes config names: ``scoped_*`` names the scope in the request, ``my_*`` acts at
    the caller's own user scope. Only the system-wide search is superadmin-only; every other
    call is RBAC-gated at the scope it acts on.
    """

    async def scoped_get_app_config_fragments_by_names(
        self,
        request: ScopedAppConfigFragmentsByNamesInput,
    ) -> AppConfigFragmentsByNamesResponse:
        """Read one scope's fragments for the given config names.

        The answer holds one entry per requested name, in the order they were given, and
        ``None`` where the scope has no fragment for that name.
        """
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/scoped/by-names",
            request=request,
            response_model=AppConfigFragmentsByNamesResponse,
        )

    async def scoped_bulk_upsert_app_config_fragments(
        self,
        request: ScopedUpsertAppConfigFragmentsInput,
    ) -> UpsertAppConfigFragmentsPayload:
        """Upsert many fragments at one scope, all-or-nothing."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/scoped/bulk-upsert",
            request=request,
            response_model=UpsertAppConfigFragmentsPayload,
        )

    async def my_get_app_config_fragments_by_names(
        self,
        request: MyAppConfigFragmentsByNamesInput,
    ) -> AppConfigFragmentsByNamesResponse:
        """Read the caller's own user-scope fragments for the given config names."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/my/by-names",
            request=request,
            response_model=AppConfigFragmentsByNamesResponse,
        )

    async def my_bulk_upsert_app_config_fragments(
        self,
        request: MyUpsertAppConfigFragmentsInput,
    ) -> UpsertAppConfigFragmentsPayload:
        """Upsert many fragments at the caller's own user scope, all-or-nothing."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/my/bulk-upsert",
            request=request,
            response_model=UpsertAppConfigFragmentsPayload,
        )

    async def get(self, app_config_fragment_id: AppConfigFragmentID) -> AppConfigFragmentNode:
        """Get a single fragment by id."""
        return await self._client.typed_request(
            "GET",
            f"{_PATH}/{app_config_fragment_id}",
            response_model=AppConfigFragmentNode,
        )

    async def purge(
        self, app_config_fragment_id: AppConfigFragmentID
    ) -> PurgeAppConfigFragmentPayload:
        """Purge a single fragment by id."""
        return await self._client.typed_request(
            "DELETE",
            f"{_PATH}/{app_config_fragment_id}",
            response_model=PurgeAppConfigFragmentPayload,
        )

    async def bulk_purge(
        self,
        request: BulkPurgeAppConfigFragmentInput,
    ) -> BulkPurgeAppConfigFragmentPayload:
        """Purge many fragments by id, reporting per-item success and failure."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/bulk-delete",
            request=request,
            response_model=BulkPurgeAppConfigFragmentPayload,
        )

    async def admin_search(
        self,
        request: AdminSearchAppConfigFragmentInput,
    ) -> SearchAppConfigFragmentPayload:
        """Search fragments across every scope with filter/order/pagination (superadmin only)."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/admin/search",
            request=request,
            response_model=SearchAppConfigFragmentPayload,
        )
