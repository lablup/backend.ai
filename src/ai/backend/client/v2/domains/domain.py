from __future__ import annotations

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.domain import (
    CreateDomainRequest,
    CreateDomainResponse,
    DeleteDomainRequest,
    DeleteDomainResponse,
    GetDomainResponse,
    PurgeDomainRequest,
    PurgeDomainResponse,
    SearchDomainsRequest,
    SearchDomainsResponse,
    UpdateDomainRequest,
    UpdateDomainResponse,
)

_DOMAINS_PATH = "/admin/domains"


class DomainClient(BaseDomainClient):
    async def create(
        self,
        request: CreateDomainRequest,
    ) -> CreateDomainResponse:
        return await self._client.typed_request(
            "POST",
            _DOMAINS_PATH,
            request=request,
            response_model=CreateDomainResponse,
        )

    async def get(
        self,
        domain_name: str,
    ) -> GetDomainResponse:
        return await self._client.typed_request(
            "GET",
            f"{_DOMAINS_PATH}/{domain_name}",
            response_model=GetDomainResponse,
        )

    async def search(
        self,
        request: SearchDomainsRequest,
    ) -> SearchDomainsResponse:
        return await self._client.typed_request(
            "POST",
            f"{_DOMAINS_PATH}/search",
            request=request,
            response_model=SearchDomainsResponse,
        )

    async def update(
        self,
        domain_name: str,
        request: UpdateDomainRequest,
    ) -> UpdateDomainResponse:
        return await self._client.typed_request(
            "PATCH",
            f"{_DOMAINS_PATH}/{domain_name}",
            request=request,
            response_model=UpdateDomainResponse,
        )

    async def delete(
        self,
        request: DeleteDomainRequest,
    ) -> DeleteDomainResponse:
        return await self._client.typed_request(
            "POST",
            f"{_DOMAINS_PATH}/delete",
            request=request,
            response_model=DeleteDomainResponse,
        )

    async def purge(
        self,
        request: PurgeDomainRequest,
    ) -> PurgeDomainResponse:
        return await self._client.typed_request(
            "POST",
            f"{_DOMAINS_PATH}/purge",
            request=request,
            response_model=PurgeDomainResponse,
        )
