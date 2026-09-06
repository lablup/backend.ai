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
from ai.backend.common.data.entity.domain import DomainName
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
from ai.backend.manager.dto.context import UserContext
from ai.backend.manager.dto.domain_request import (
    GetDomainPathParam,
    UpdateDomainPathParam,
)
from ai.backend.manager.models.domain.creators import DomainCreator
from ai.backend.manager.models.domain.updaters import DomainSoftDeleteUpdater
from ai.backend.manager.models.project.creators import ProjectCreator
from ai.backend.manager.services.domain.actions.create_domain import CreateDomainAction
from ai.backend.manager.services.domain.actions.delete_domain import DeleteDomainAction
from ai.backend.manager.services.domain.actions.get import GetDomainAction
from ai.backend.manager.services.domain.actions.lookup import LookupDomainAction
from ai.backend.manager.services.domain.actions.purge_domain import PurgeDomainAction
from ai.backend.manager.services.domain.actions.search_domains import GlobalSearchDomainsAction
from ai.backend.manager.services.domain.actions.update_domain import UpdateDomainAction
from ai.backend.manager.services.project.actions.create_project import CreateProjectAction

from .adapter import DomainAdapter

if TYPE_CHECKING:
    from ai.backend.manager.services.domain.processors import DomainProcessors
    from ai.backend.manager.services.project.processors import ProjectProcessors

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class DomainHandler:
    """Domain API handler with constructor-injected dependencies."""

    def __init__(self, *, domain: DomainProcessors, project: ProjectProcessors) -> None:
        self._domain = domain
        self._project = project
        self._adapter = DomainAdapter()

    # ------------------------------------------------------------------
    # create (POST /admin/domains)
    # ------------------------------------------------------------------

    async def create(
        self,
        body: BodyParam[CreateDomainRequest],
        ctx: UserContext,
    ) -> APIResponse:
        creator = DomainCreator(
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
            integration_name=body.parsed.integration_id,  # v1 DTO uses integration_id
        )
        action_result = await self._domain.create_domain.run(CreateDomainAction(creator=creator))
        domain_data = action_result.data
        await self._project.create_project.run(
            CreateProjectAction(
                domain_id=domain_data.id,
                creator=ProjectCreator.model_store(
                    domain_id=domain_data.id, domain_name=domain_data.name
                ),
            )
        )

        resp = CreateDomainResponse(domain=self._adapter.convert_to_dto(domain_data))
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=resp)

    # ------------------------------------------------------------------
    # get (GET /admin/domains/{domain_name})
    # ------------------------------------------------------------------

    async def get(
        self,
        path: PathParam[GetDomainPathParam],
        ctx: UserContext,
    ) -> APIResponse:
        resolved = await self._domain.lookup.run(
            LookupDomainAction(name=DomainName(path.parsed.domain_name))
        )
        action_result = await self._domain.get.run(GetDomainAction(domain_id=resolved.entity_id()))

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
        searcher = self._adapter.build_searcher(body.parsed)

        action_result = await self._domain.global_search.run(
            GlobalSearchDomainsAction(searcher=searcher)
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
        target = await self._domain.lookup.run(LookupDomainAction(name=DomainName(domain_name)))
        updater = self._adapter.build_updater(body.parsed, target.entity_id())

        action_result = await self._domain.update_domain.run(UpdateDomainAction(updater=updater))

        resp = UpdateDomainResponse(domain=self._adapter.convert_to_dto(action_result.data))
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    # ------------------------------------------------------------------
    # delete (POST /admin/domains/delete)
    # ------------------------------------------------------------------

    async def delete(
        self,
        body: BodyParam[DeleteDomainRequest],
        ctx: UserContext,
    ) -> APIResponse:
        target = await self._domain.lookup.run(
            LookupDomainAction(name=DomainName(body.parsed.name))
        )
        await self._domain.delete_domain.run(
            DeleteDomainAction(
                updater=DomainSoftDeleteUpdater(domain_id=target.entity_id()),
            )
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
        target = await self._domain.lookup.run(
            LookupDomainAction(name=DomainName(body.parsed.name))
        )
        await self._domain.purge_domain.run(
            PurgeDomainAction(domain_id=target.entity_id(), name=body.parsed.name)
        )

        resp = PurgeDomainResponse(purged=True)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)
