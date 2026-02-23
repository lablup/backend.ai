from __future__ import annotations

import pytest

from ai.backend.client.v2.exceptions import NotFoundError, PermissionDeniedError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.quota_scope import (
    SearchQuotaScopesRequest,
    SearchQuotaScopesResponse,
    SetQuotaRequest,
    SetQuotaResponse,
    UnsetQuotaRequest,
    UnsetQuotaResponse,
)
from ai.backend.common.dto.manager.quota_scope.response import GetQuotaScopeResponse


class TestQuotaScopeGet:
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires a running storage proxy service")
    async def test_admin_gets_quota_scope(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Admin can get a quota scope from a storage host; response is valid."""
        result = await admin_registry.quota_scope.get(
            storage_host_name="local:volume1",
            quota_scope_id="user:00000000-0000-0000-0000-000000000001",
        )
        assert isinstance(result, GetQuotaScopeResponse)
        assert result.quota_scope.storage_host_name == "local:volume1"
        assert result.quota_scope.quota_scope_id == "user:00000000-0000-0000-0000-000000000001"

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires a running storage proxy service")
    async def test_get_nonexistent_quota_scope(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Getting a quota scope for an unknown scope returns a not-found response."""
        with pytest.raises(NotFoundError):
            await admin_registry.quota_scope.get(
                storage_host_name="local:volume1",
                quota_scope_id="user:00000000-0000-0000-0000-000000000000",
            )

    @pytest.mark.asyncio
    async def test_regular_user_cannot_get_quota_scope(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        """Non-superadmin user receives PermissionDeniedError when getting a quota scope."""
        with pytest.raises(PermissionDeniedError):
            await user_registry.quota_scope.get(
                storage_host_name="local:volume1",
                quota_scope_id="user:00000000-0000-0000-0000-000000000001",
            )


class TestQuotaScopeSearch:
    @pytest.mark.asyncio
    async def test_admin_searches_quota_scopes(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Admin can search quota scopes; response contains valid pagination metadata."""
        result = await admin_registry.quota_scope.search(SearchQuotaScopesRequest())
        assert isinstance(result, SearchQuotaScopesResponse)
        assert isinstance(result.quota_scopes, list)
        assert result.pagination.total >= 0
        assert result.pagination.offset == 0

    @pytest.mark.asyncio
    async def test_search_with_pagination(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Pagination parameters (limit/offset) are reflected in the search response."""
        result = await admin_registry.quota_scope.search(
            SearchQuotaScopesRequest(limit=10, offset=0),
        )
        assert isinstance(result, SearchQuotaScopesResponse)
        assert result.pagination.limit == 10
        assert result.pagination.offset == 0
        assert len(result.quota_scopes) <= 10

    @pytest.mark.asyncio
    async def test_regular_user_cannot_search_quota_scopes(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        """Non-superadmin user receives PermissionDeniedError when searching quota scopes."""
        with pytest.raises(PermissionDeniedError):
            await user_registry.quota_scope.search(SearchQuotaScopesRequest())


class TestQuotaScopeSetQuota:
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires a running storage proxy service")
    async def test_admin_sets_quota(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Admin can set a hard-limit quota on a scope; response reflects the new limit."""
        result = await admin_registry.quota_scope.set_quota(
            SetQuotaRequest(
                storage_host_name="local:volume1",
                quota_scope_id="user:00000000-0000-0000-0000-000000000001",
                hard_limit_bytes=1_073_741_824,  # 1 GiB
            )
        )
        assert isinstance(result, SetQuotaResponse)
        assert result.quota_scope.hard_limit_bytes == 1_073_741_824
        assert result.quota_scope.storage_host_name == "local:volume1"
        assert result.quota_scope.quota_scope_id == "user:00000000-0000-0000-0000-000000000001"

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires a running storage proxy service")
    async def test_set_quota_creates_if_not_exists(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Setting a quota on a new scope creates the quota entry."""
        result = await admin_registry.quota_scope.set_quota(
            SetQuotaRequest(
                storage_host_name="local:volume1",
                quota_scope_id="user:00000000-0000-0000-0000-000000000002",
                hard_limit_bytes=2_147_483_648,  # 2 GiB
            )
        )
        assert isinstance(result, SetQuotaResponse)
        assert result.quota_scope.hard_limit_bytes == 2_147_483_648

    @pytest.mark.asyncio
    async def test_regular_user_cannot_set_quota(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        """Non-superadmin user receives PermissionDeniedError when setting a quota."""
        with pytest.raises(PermissionDeniedError):
            await user_registry.quota_scope.set_quota(
                SetQuotaRequest(
                    storage_host_name="local:volume1",
                    quota_scope_id="user:00000000-0000-0000-0000-000000000001",
                    hard_limit_bytes=1_073_741_824,
                )
            )


class TestQuotaScopeUnsetQuota:
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires a running storage proxy service")
    async def test_admin_unsets_quota(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Admin can unset a quota from a scope; response shows null hard_limit_bytes."""
        result = await admin_registry.quota_scope.unset_quota(
            UnsetQuotaRequest(
                storage_host_name="local:volume1",
                quota_scope_id="user:00000000-0000-0000-0000-000000000001",
            )
        )
        assert isinstance(result, UnsetQuotaResponse)
        assert result.quota_scope.hard_limit_bytes is None

    @pytest.mark.asyncio
    async def test_regular_user_cannot_unset_quota(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        """Non-superadmin user receives PermissionDeniedError when unsetting a quota."""
        with pytest.raises(PermissionDeniedError):
            await user_registry.quota_scope.unset_quota(
                UnsetQuotaRequest(
                    storage_host_name="local:volume1",
                    quota_scope_id="user:00000000-0000-0000-0000-000000000001",
                )
            )
