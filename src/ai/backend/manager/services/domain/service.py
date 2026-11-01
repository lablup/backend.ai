from __future__ import annotations

import logging
from typing import cast

<<<<<<< HEAD
from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.repositories.domain.creators import DomainCreatorSpec
=======
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.dotfile import DotfilePath
from ai.backend.logging.structured import StructuredLogger
from ai.backend.manager.actions.v2.ops.result import CreatedEntityOpsResult
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.dotfile.types import DotfileEntries
from ai.backend.manager.models.domain.updaters import DomainDotfilesUpdater
>>>>>>> 249726371 (fix(BA-8786): keep dotfile paths under the kernel work directory (#16231))
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
from ai.backend.manager.services.domain.actions.resolve_domain_id_by_name import (
    ResolveDomainIDByNameAction,
    ResolveDomainIDByNameActionResult,
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

<<<<<<< HEAD
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

    async def resolve_domain_id_by_name(
        self, action: ResolveDomainIDByNameAction
    ) -> ResolveDomainIDByNameActionResult:
        domain_id = await self._repository.get_domain_id_by_name(action.name)
        return ResolveDomainIDByNameActionResult(domain_id=domain_id)

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
=======
    async def purge(self, action: PurgeDomainAction) -> PurgeDomainActionResult:
        domain_data = await self._repository.purge_domain(action.domain_id, action.name)
        return PurgeDomainActionResult(domain_data=domain_data)

    async def create_dotfile(
        self, action: CreateDomainDotfileAction
    ) -> CreateDomainDotfileActionResult:
        DotfilePath(action.entry.path)
        domain_id, current = await self._read_dotfiles(action.name)
        entries = current.added(action.entry)
        await self._write_dotfiles(domain_id, entries)
        return CreateDomainDotfileActionResult(entries=entries.entries)

    async def update_dotfile(
        self, action: UpdateDomainDotfileAction
    ) -> UpdateDomainDotfileActionResult:
        DotfilePath(action.entry.path)
        domain_id, current = await self._read_dotfiles(action.name)
        entries = current.replaced(action.entry)
        await self._write_dotfiles(domain_id, entries)
        return UpdateDomainDotfileActionResult(entries=entries.entries)

    async def delete_dotfile(
        self, action: DeleteDomainDotfileAction
    ) -> DeleteDomainDotfileActionResult:
        domain_id, current = await self._read_dotfiles(action.name)
        entries = current.removed(action.path)
        await self._write_dotfiles(domain_id, entries)
        return DeleteDomainDotfileActionResult(entries=entries.entries)

    async def _read_dotfiles(self, name: str) -> tuple[DomainID, DotfileEntries]:
        """The domain's id alongside its entries, so the write keys on the id it read."""
        data = await self._repository.get_domain(name)
        return data.id, DotfileEntries.unpack(data.dotfiles)

    async def _write_dotfiles(self, domain_id: DomainID, entries: DotfileEntries) -> None:
        await self._repository.update_dotfiles(
            DomainDotfilesUpdater(domain_id=domain_id, dotfiles=entries.pack())
>>>>>>> 249726371 (fix(BA-8786): keep dotfile paths under the kernel work directory (#16231))
        )
