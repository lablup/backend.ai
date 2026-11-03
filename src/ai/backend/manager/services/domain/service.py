from __future__ import annotations

import logging

from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.dotfile import DotfilePath
from ai.backend.logging.structured import StructuredLogger
from ai.backend.manager.actions.v2.ops.result import CreatedEntityOpsResult
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.dotfile.types import DotfileEntries
from ai.backend.manager.models.domain.updaters import DomainDotfilesUpdater
from ai.backend.manager.repositories.domain.repository import DomainRepository
from ai.backend.manager.services.domain.actions.create_container_registry_relations import (
    CreateDomainContainerRegistryRelationsAction,
    CreateDomainContainerRegistryRelationsActionResult,
)
from ai.backend.manager.services.domain.actions.create_domain import CreateDomainAction
from ai.backend.manager.services.domain.actions.create_domain_dotfile import (
    CreateDomainDotfileAction,
    CreateDomainDotfileActionResult,
)
from ai.backend.manager.services.domain.actions.delete_domain_dotfile import (
    DeleteDomainDotfileAction,
    DeleteDomainDotfileActionResult,
)
from ai.backend.manager.services.domain.actions.purge_container_registry_relations import (
    PurgeDomainContainerRegistryRelationsAction,
    PurgeDomainContainerRegistryRelationsActionResult,
)
from ai.backend.manager.services.domain.actions.purge_domain import (
    PurgeDomainAction,
    PurgeDomainActionResult,
)
from ai.backend.manager.services.domain.actions.search_container_registry_relations import (
    SearchDomainContainerRegistryRelationsAction,
    SearchDomainContainerRegistryRelationsActionResult,
)
from ai.backend.manager.services.domain.actions.update_domain_dotfile import (
    UpdateDomainDotfileAction,
    UpdateDomainDotfileActionResult,
)
from ai.backend.manager.services.rbac.actions.relation.base import (
    RelationLinkResult,
    RelationPair,
    RelationUnlinkResult,
)

log = StructuredLogger(logging.getLogger(__spec__.name))


class DomainService:
    _repository: DomainRepository

    def __init__(self, repository: DomainRepository) -> None:
        self._repository = repository

    async def create(self, action: CreateDomainAction) -> CreatedEntityOpsResult[DomainData]:
        """Register a domain. Not the generic create: a domain is registered with a
        model-store project, in the same transaction."""
        return CreatedEntityOpsResult(
            data=await self._repository.create_domain(action.to_creator())
        )

    async def create_container_registry_relations(
        self, action: CreateDomainContainerRegistryRelationsAction
    ) -> CreateDomainContainerRegistryRelationsActionResult:
        written = await self._repository.create_container_registry_relations([
            (action.domain_id, registry_id) for registry_id in action.registry_ids
        ])
        results: list[RelationLinkResult[DomainID, ContainerRegistryID]] = []
        for registry_id, linked in zip(action.registry_ids, written, strict=True):
            pair = RelationPair(scope=action.domain_id, target=registry_id)
            results.append(RelationLinkResult(pair=pair, linked=linked))
        return CreateDomainContainerRegistryRelationsActionResult(results=results)

    async def purge_container_registry_relations(
        self, action: PurgeDomainContainerRegistryRelationsAction
    ) -> PurgeDomainContainerRegistryRelationsActionResult:
        purged = await self._repository.purge_container_registry_relations([
            (action.domain_id, registry_id) for registry_id in action.registry_ids
        ])
        results: list[RelationUnlinkResult[DomainID, ContainerRegistryID]] = []
        for registry_id, was_linked in zip(action.registry_ids, purged, strict=True):
            pair = RelationPair(scope=action.domain_id, target=registry_id)
            results.append(RelationUnlinkResult(pair=pair, unlinked=was_linked))
        return PurgeDomainContainerRegistryRelationsActionResult(results=results)

    async def search_container_registry_relations(
        self, action: SearchDomainContainerRegistryRelationsAction
    ) -> SearchDomainContainerRegistryRelationsActionResult:
        result = await self._repository.search_container_registry_relations(
            action.operation_scopes(), action.searcher
        )
        return SearchDomainContainerRegistryRelationsActionResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

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
        )
