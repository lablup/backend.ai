from __future__ import annotations

import secrets

import pytest

from ai.backend.client.v2.exceptions import NotFoundError, PermissionDeniedError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.domain import (
    CreateDomainRequest,
    CreateDomainResponse,
    DeleteDomainRequest,
    DeleteDomainResponse,
    DomainFilter,
    GetDomainResponse,
    PurgeDomainRequest,
    PurgeDomainResponse,
    SearchDomainsRequest,
    SearchDomainsResponse,
    UpdateDomainRequest,
    UpdateDomainResponse,
)
from ai.backend.common.dto.manager.query import StringFilter

from .conftest import DomainFactory


class TestDomainCreate:
    @pytest.mark.asyncio
    async def test_admin_creates_domain(
        self,
        admin_registry: BackendAIClientRegistry,
        domain_factory: DomainFactory,
    ) -> None:
        unique = secrets.token_hex(4)
        result = await domain_factory(
            name=f"test-domain-{unique}",
            description=f"Test domain {unique}",
        )
        assert isinstance(result, CreateDomainResponse)
        assert result.domain.name == f"test-domain-{unique}"
        assert result.domain.description == f"Test domain {unique}"
        assert result.domain.is_active is True

    @pytest.mark.asyncio
    async def test_regular_user_cannot_create_domain(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        unique = secrets.token_hex(4)
        request = CreateDomainRequest(
            name=f"denied-domain-{unique}",
            description="Should be denied",
        )
        with pytest.raises(PermissionDeniedError):
            await user_registry.domain.create(request)


class TestDomainGet:
    @pytest.mark.asyncio
    async def test_admin_gets_domain_by_name(
        self,
        admin_registry: BackendAIClientRegistry,
        target_domain: CreateDomainResponse,
    ) -> None:
        get_result = await admin_registry.domain.get(target_domain.domain.name)
        assert isinstance(get_result, GetDomainResponse)
        assert get_result.domain.name == target_domain.domain.name
        assert get_result.domain.description == target_domain.domain.description

    @pytest.mark.asyncio
    async def test_get_nonexistent_domain_returns_not_found(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(NotFoundError):
            await admin_registry.domain.get("nonexistent-domain-xyz-12345")


class TestDomainSearch:
    @pytest.mark.asyncio
    async def test_admin_searches_domains(
        self,
        admin_registry: BackendAIClientRegistry,
        domain_factory: DomainFactory,
    ) -> None:
        await domain_factory()
        result = await admin_registry.domain.search(SearchDomainsRequest())
        assert isinstance(result, SearchDomainsResponse)
        # At minimum the "default" domain plus the one we created
        assert result.pagination.total >= 1
        assert len(result.domains) >= 1

    @pytest.mark.asyncio
    async def test_search_with_name_filter(
        self,
        admin_registry: BackendAIClientRegistry,
        domain_factory: DomainFactory,
    ) -> None:
        unique = secrets.token_hex(4)
        marker = f"searchable-{unique}"
        await domain_factory(name=marker, description=f"Searchable domain {unique}")
        result = await admin_registry.domain.search(
            SearchDomainsRequest(
                filter=DomainFilter(name=StringFilter(contains=marker)),
            )
        )
        assert result.pagination.total >= 1
        assert any(d.name == marker for d in result.domains)

    @pytest.mark.asyncio
    async def test_search_with_pagination(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.domain.search(
            SearchDomainsRequest(limit=1, offset=0),
        )
        assert result.pagination.limit == 1
        assert len(result.domains) <= 1

    @pytest.mark.asyncio
    async def test_regular_user_cannot_search_domains(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.domain.search(SearchDomainsRequest())


class TestDomainUpdate:
    @pytest.mark.asyncio
    async def test_admin_updates_domain_fields(
        self,
        admin_registry: BackendAIClientRegistry,
        target_domain: CreateDomainResponse,
    ) -> None:
        unique = secrets.token_hex(4)
        update_result = await admin_registry.domain.update(
            target_domain.domain.name,
            UpdateDomainRequest(
                description=f"Updated description {unique}",
            ),
        )
        assert isinstance(update_result, UpdateDomainResponse)
        assert update_result.domain.description == f"Updated description {unique}"
        assert update_result.domain.name == target_domain.domain.name

    @pytest.mark.asyncio
    async def test_regular_user_cannot_update_domain(
        self,
        user_registry: BackendAIClientRegistry,
        target_domain: CreateDomainResponse,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.domain.update(
                target_domain.domain.name,
                UpdateDomainRequest(description="Denied"),
            )


class TestDomainDelete:
    @pytest.mark.asyncio
    async def test_admin_soft_deletes_domain(
        self,
        admin_registry: BackendAIClientRegistry,
        target_domain: CreateDomainResponse,
    ) -> None:
        delete_result = await admin_registry.domain.delete(
            DeleteDomainRequest(name=target_domain.domain.name)
        )
        assert isinstance(delete_result, DeleteDomainResponse)
        assert delete_result.deleted is True

    @pytest.mark.asyncio
    async def test_regular_user_cannot_delete_domain(
        self,
        user_registry: BackendAIClientRegistry,
        target_domain: CreateDomainResponse,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.domain.delete(DeleteDomainRequest(name=target_domain.domain.name))


class TestDomainPurge:
    @pytest.mark.asyncio
    async def test_admin_purges_domain(
        self,
        admin_registry: BackendAIClientRegistry,
        domain_factory: DomainFactory,
    ) -> None:
        r = await domain_factory()
        purge_result = await admin_registry.domain.purge(PurgeDomainRequest(name=r.domain.name))
        assert isinstance(purge_result, PurgeDomainResponse)
        assert purge_result.purged is True
        with pytest.raises(NotFoundError):
            await admin_registry.domain.get(r.domain.name)

    @pytest.mark.asyncio
    async def test_regular_user_cannot_purge_domain(
        self,
        user_registry: BackendAIClientRegistry,
        target_domain: CreateDomainResponse,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.domain.purge(PurgeDomainRequest(name=target_domain.domain.name))
