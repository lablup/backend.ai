from __future__ import annotations

import logging
from typing import cast

from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.repositories.domain.creators import DomainCreatorSpec
from ai.backend.manager.repositories.domain.repository import DomainRepository
from ai.backend.manager.services.domain.actions.create_domain import (
    CreateDomainAction,
    CreateDomainActionResult,
)
from ai.backend.manager.services.domain.actions.create_domain_node import (
    CreateDomainNodeAction,
    CreateDomainNodeActionResult,
)
from ai.backend.manager.services.domain.actions.delete_domain import (
    DeleteDomainAction,
    DeleteDomainActionResult,
)
from ai.backend.manager.services.domain.actions.get_domain import (
    GetDomainAction,
    GetDomainActionResult,
)
from ai.backend.manager.services.domain.actions.modify_domain import (
    ModifyDomainAction,
    ModifyDomainActionResult,
)
from ai.backend.manager.services.domain.actions.modify_domain_node import (
    ModifyDomainNodeAction,
    ModifyDomainNodeActionResult,
)
from ai.backend.manager.services.domain.actions.purge_domain import (
    PurgeDomainAction,
    PurgeDomainActionResult,
)
from ai.backend.manager.services.domain.actions.search_domains import (
    SearchDomainsAction,
    SearchDomainsActionResult,
)
from ai.backend.manager.services.domain.actions.search_rg_domains import (
    SearchRGDomainsAction,
    SearchRGDomainsActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class DomainService:
    _repository: DomainRepository

    def __init__(
        self,
        repository: DomainRepository,
    ) -> None:
        self._repository = repository

    async def create_domain(self, action: CreateDomainAction) -> CreateDomainActionResult:
        spec = cast(DomainCreatorSpec, action.creator.spec)
        domain_name_candidate = spec.name.strip()
        if domain_name_candidate == "" or len(domain_name_candidate) > 64:
            raise InvalidAPIParameters("Domain name cannot be empty or exceed 64 characters.")

        domain_data = await self._repository.create_domain(action.creator)
        return CreateDomainActionResult(
            domain_data=domain_data,
        )

    async def modify_domain(self, action: ModifyDomainAction) -> ModifyDomainActionResult:
        domain_data = await self._repository.modify_domain(action.updater)
        return ModifyDomainActionResult(
            domain_data=domain_data,
        )

    async def delete_domain(self, action: DeleteDomainAction) -> DeleteDomainActionResult:
        await self._repository.soft_delete_domain(action.name)

        return DeleteDomainActionResult(
            name=action.name,
        )

    async def purge_domain(self, action: PurgeDomainAction) -> PurgeDomainActionResult:
        name = action.name

        await self._repository.purge_domain(name)
        return PurgeDomainActionResult(
            name=name,
        )

    async def create_domain_node(
        self, action: CreateDomainNodeAction
    ) -> CreateDomainNodeActionResult:
        spec = cast(DomainCreatorSpec, action.creator.spec)
        domain_name_candidate = spec.name.strip()
        if domain_name_candidate == "" or len(domain_name_candidate) > 64:
            raise InvalidAPIParameters("Domain name cannot be empty or exceed 64 characters.")

        domain_data = await self._repository.create_domain_node_with_permissions(
            action.creator,
            action.user_info,
            action.scaling_groups,
        )

        return CreateDomainNodeActionResult(
            domain_data=domain_data,
        )

    async def modify_domain_node(
        self, action: ModifyDomainNodeAction
    ) -> ModifyDomainNodeActionResult:
        if action.sgroups_to_add is not None and action.sgroups_to_remove is not None:
            if conflict := action.sgroups_to_add & action.sgroups_to_remove:
                raise InvalidAPIParameters(
                    "Should be no scaling group names included in both `sgroups_to_add` and `sgroups_to_remove` "
                    f"(sg:{conflict})."
                )

        domain_data = await self._repository.modify_domain_node_with_permissions(
            action.updater,
            action.user_info,
            action.sgroups_to_add,
            action.sgroups_to_remove,
        )
        return ModifyDomainNodeActionResult(
            domain_data=domain_data,
        )

    async def get_domain(self, action: GetDomainAction) -> GetDomainActionResult:
        """Get a single domain by name.

        Args:
            action: GetDomainAction with domain_name.

        Returns:
            GetDomainActionResult with domain data.

        Raises:
            DomainNotFound: If domain does not exist.
        """
        data = await self._repository.get_domain(action.domain_name)
        return GetDomainActionResult(data=data)

    async def search_domains(self, action: SearchDomainsAction) -> SearchDomainsActionResult:
        """Search all domains (admin only - no scope filter).

        Args:
            action: SearchDomainsAction with querier.

        Returns:
            SearchDomainsActionResult with items and pagination info.
        """
        result = await self._repository.search_domains(querier=action.querier)
        return SearchDomainsActionResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def search_rg_domains(self, action: SearchRGDomainsAction) -> SearchRGDomainsActionResult:
        """Search domains within a resource group scope.

        Args:
            action: SearchRGDomainsAction with scope and querier.

        Returns:
            SearchRGDomainsActionResult with items and pagination info.
        """
        result = await self._repository.search_rg_domains(
            scope=action.scope,
            querier=action.querier,
        )
        return SearchRGDomainsActionResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )
