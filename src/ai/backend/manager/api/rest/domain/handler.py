"""Domain API handler using constructor dependency injection.

All handlers use the new ApiHandler pattern: typed parameters
(``BodyParam``, ``PathParam``, ``UserContext``) are automatically
extracted by ``_wrap_api_handler`` and responses are returned as
``APIResponse`` objects.
"""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.domain import (
    CreateDomainRequest,
    CreateDomainResponse,
    DeleteDomainRequest,
    DeleteDomainResponse,
    GetDomainResponse,
    PaginationInfo,
    PurgeDomainRequest,
    PurgeDomainResponse,
    SearchDomainsRequest,
    SearchDomainsResponse,
    UpdateDomainRequest,
    UpdateDomainResponse,
)
from ai.backend.common.types import ResourceSlot
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.domain.types import UserInfo
from ai.backend.manager.dto.context import UserContext
from ai.backend.manager.dto.domain_request import (
    GetDomainPathParam,
    UpdateDomainPathParam,
)
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.domain.creators import DomainCreatorSpec
from ai.backend.manager.services.domain.actions.create_domain import CreateDomainAction
from ai.backend.manager.services.domain.actions.delete_domain import DeleteDomainAction
from ai.backend.manager.services.domain.actions.get_domain import GetDomainAction
from ai.backend.manager.services.domain.actions.modify_domain import ModifyDomainAction
from ai.backend.manager.services.domain.actions.purge_domain import PurgeDomainAction
from ai.backend.manager.services.domain.actions.search_domains import SearchDomainsAction

from .adapter import DomainAdapter

if TYPE_CHECKING:
    from ai.backend.manager.services.processors import Processors

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class DomainHandler:
    """Domain API handler with constructor-injected dependencies."""

    def __init__(self, *, processors: Processors) -> None:
        self._processors = processors
        self._adapter = DomainAdapter()

    # ------------------------------------------------------------------
    # create (POST /admin/domains)
    # ------------------------------------------------------------------

    async def create(
        self,
        body: BodyParam[CreateDomainRequest],
        ctx: UserContext,
    ) -> APIResponse:
        log.info("CREATE_DOMAIN (ak:{})", ctx.access_key)
        creator = Creator(
            spec=DomainCreatorSpec(
                name=body.parsed.name,
                description=body.parsed.description,
                is_active=body.parsed.is_active,
                total_resource_slots=(
                    ResourceSlot(body.parsed.total_resource_slots)
                    if body.parsed.total_resource_slots is not None
                    else None
                ),
                allowed_vfolder_hosts=body.parsed.allowed_vfolder_hosts,
                allowed_docker_registries=body.parsed.allowed_docker_registries,
                integration_id=body.parsed.integration_id,
            )
        )
        user_info = UserInfo(
            id=ctx.user_uuid,
            role=UserRole.SUPERADMIN,
            domain_name=ctx.user_domain,
        )

        action_result = await self._processors.domain.create_domain.wait_for_complete(
            CreateDomainAction(creator=creator, user_info=user_info)
        )

        resp = CreateDomainResponse(domain=self._adapter.convert_to_dto(action_result.domain_data))
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=resp)

    # ------------------------------------------------------------------
    # get (GET /admin/domains/{domain_name})
    # ------------------------------------------------------------------

    async def get(
        self,
        path: PathParam[GetDomainPathParam],
        ctx: UserContext,
    ) -> APIResponse:
        log.info("GET_DOMAIN (ak:{}, d:{})", ctx.access_key, path.parsed.domain_name)
        action_result = await self._processors.domain.get_domain.wait_for_complete(
            GetDomainAction(domain_name=path.parsed.domain_name)
        )

        resp = GetDomainResponse(domain=self._adapter.convert_to_dto(action_result.data))
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    # ------------------------------------------------------------------
    # search (POST /admin/domains/search)
    # ------------------------------------------------------------------

    async def search(
        self,
        body: BodyParam[SearchDomainsRequest],
        ctx: UserContext,
    ) -> APIResponse:
        log.info("SEARCH_DOMAINS (ak:{})", ctx.access_key)
        querier = self._adapter.build_querier(body.parsed)

        action_result = await self._processors.domain.search_domains.wait_for_complete(
            SearchDomainsAction(querier=querier)
        )

        resp = SearchDomainsResponse(
            domains=[self._adapter.convert_to_dto(d) for d in action_result.items],
            pagination=PaginationInfo(
                total=action_result.total_count,
                offset=body.parsed.offset,
                limit=body.parsed.limit,
            ),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    # ------------------------------------------------------------------
    # update (PATCH /admin/domains/{domain_name})
    # ------------------------------------------------------------------

    async def update(
        self,
        path: PathParam[UpdateDomainPathParam],
        body: BodyParam[UpdateDomainRequest],
        ctx: UserContext,
    ) -> APIResponse:
        domain_name = path.parsed.domain_name
        log.info("UPDATE_DOMAIN (ak:{}, d:{})", ctx.access_key, domain_name)
        updater = self._adapter.build_updater(body.parsed, domain_name)
        user_info = UserInfo(
            id=ctx.user_uuid,
            role=UserRole.SUPERADMIN,
            domain_name=ctx.user_domain,
        )

        action_result = await self._processors.domain.modify_domain.wait_for_complete(
            ModifyDomainAction(user_info=user_info, updater=updater)
        )

        resp = UpdateDomainResponse(domain=self._adapter.convert_to_dto(action_result.domain_data))
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    # ------------------------------------------------------------------
    # delete (POST /admin/domains/delete)
    # ------------------------------------------------------------------

    async def delete(
        self,
        body: BodyParam[DeleteDomainRequest],
        ctx: UserContext,
    ) -> APIResponse:
        log.info("DELETE_DOMAIN (ak:{}, d:{})", ctx.access_key, body.parsed.name)
        user_info = UserInfo(
            id=ctx.user_uuid,
            role=UserRole.SUPERADMIN,
            domain_name=ctx.user_domain,
        )

        await self._processors.domain.delete_domain.wait_for_complete(
            DeleteDomainAction(name=body.parsed.name, user_info=user_info)
        )

        resp = DeleteDomainResponse(deleted=True)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    # ------------------------------------------------------------------
    # purge (POST /admin/domains/purge)
    # ------------------------------------------------------------------

    async def purge(
        self,
        body: BodyParam[PurgeDomainRequest],
        ctx: UserContext,
    ) -> APIResponse:
        log.info("PURGE_DOMAIN (ak:{}, d:{})", ctx.access_key, body.parsed.name)
        user_info = UserInfo(
            id=ctx.user_uuid,
            role=UserRole.SUPERADMIN,
            domain_name=ctx.user_domain,
        )

        await self._processors.domain.purge_domain.wait_for_complete(
            PurgeDomainAction(name=body.parsed.name, user_info=user_info)
        )

        resp = PurgeDomainResponse(purged=True)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)
