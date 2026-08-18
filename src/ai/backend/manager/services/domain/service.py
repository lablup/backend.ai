from __future__ import annotations

import logging

from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.dotfile.types import DotfileEntries
from ai.backend.manager.models.domain.row import verify_dotfile_name
from ai.backend.manager.models.domain.updaters import DomainDotfilesUpdater
from ai.backend.manager.repositories.domain.repository import DomainRepository
from ai.backend.manager.services.domain.actions.create_domain import (
    CreateDomainAction,
    CreateDomainActionResult,
)
from ai.backend.manager.services.domain.actions.create_domain_dotfile import (
    CreateDomainDotfileAction,
    CreateDomainDotfileActionResult,
)
from ai.backend.manager.services.domain.actions.create_domain_node import (
    CreateDomainNodeAction,
    CreateDomainNodeActionResult,
)
from ai.backend.manager.services.domain.actions.delete_domain_dotfile import (
    DeleteDomainDotfileAction,
    DeleteDomainDotfileActionResult,
)
from ai.backend.manager.services.domain.actions.purge_domain import (
    PurgeDomainAction,
    PurgeDomainActionResult,
)
from ai.backend.manager.services.domain.actions.update_domain_dotfile import (
    UpdateDomainDotfileAction,
    UpdateDomainDotfileActionResult,
)
from ai.backend.manager.services.domain.actions.update_domain_node import (
    UpdateDomainNodeAction,
    UpdateDomainNodeActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

_MAXIMUM_DOMAIN_NAME_LENGTH = 64


class DomainService:
    _repository: DomainRepository

    def __init__(self, repository: DomainRepository) -> None:
        self._repository = repository

    async def create_domain(self, action: CreateDomainAction) -> CreateDomainActionResult:
        self._validate_name(action.creator.name)
        domain_data = await self._repository.create_domain(action.creator)
        return CreateDomainActionResult(domain_data=domain_data)

    async def create_domain_node(
        self, action: CreateDomainNodeAction
    ) -> CreateDomainNodeActionResult:
        self._validate_name(action.creator.name)
        domain_data = await self._repository.create_domain_node(
            action.creator, action.scaling_group_ids
        )
        return CreateDomainNodeActionResult(domain_data=domain_data)

    async def update_domain_node(
        self, action: UpdateDomainNodeAction
    ) -> UpdateDomainNodeActionResult:
        if action.sgroup_ids_to_add is not None and action.sgroup_ids_to_remove is not None:
            if conflict := action.sgroup_ids_to_add & action.sgroup_ids_to_remove:
                raise InvalidAPIParameters(
                    "Should be no scaling groups included in both `sgroups_to_add` and "
                    f"`sgroups_to_remove` (sg:{conflict})."
                )
        domain_data = await self._repository.update_domain_node(
            action.domain_id,
            action.updater,
            action.sgroup_ids_to_add,
            action.sgroup_ids_to_remove,
        )
        return UpdateDomainNodeActionResult(domain_data=domain_data)

    async def purge_domain(self, action: PurgeDomainAction) -> PurgeDomainActionResult:
        domain_data = await self._repository.purge_domain(action.domain_id, action.name)
        return PurgeDomainActionResult(domain_data=domain_data)

    async def create_dotfile(
        self, action: CreateDomainDotfileAction
    ) -> CreateDomainDotfileActionResult:
        if not verify_dotfile_name(action.entry.path):
            raise InvalidAPIParameters("dotfile path is reserved for internal operations.")
        entries = (await self._read_dotfiles(action.name)).added(action.entry)
        await self._write_dotfiles(action.name, entries)
        return CreateDomainDotfileActionResult(entries=entries.entries)

    async def update_dotfile(
        self, action: UpdateDomainDotfileAction
    ) -> UpdateDomainDotfileActionResult:
        entries = (await self._read_dotfiles(action.name)).replaced(action.entry)
        await self._write_dotfiles(action.name, entries)
        return UpdateDomainDotfileActionResult(entries=entries.entries)

    async def delete_dotfile(
        self, action: DeleteDomainDotfileAction
    ) -> DeleteDomainDotfileActionResult:
        entries = (await self._read_dotfiles(action.name)).removed(action.path)
        await self._write_dotfiles(action.name, entries)
        return DeleteDomainDotfileActionResult(entries=entries.entries)

    def _validate_name(self, name: str) -> None:
        candidate = name.strip()
        if candidate == "" or len(candidate) > _MAXIMUM_DOMAIN_NAME_LENGTH:
            raise InvalidAPIParameters(
                f"Domain name cannot be empty or exceed {_MAXIMUM_DOMAIN_NAME_LENGTH} characters."
            )

    async def _read_dotfiles(self, name: str) -> DotfileEntries:
        data = await self._repository.get_domain(name)
        return DotfileEntries.unpack(data.dotfiles)

    async def _write_dotfiles(self, name: str, entries: DotfileEntries) -> None:
        await self._repository.update_dotfiles(
            DomainDotfilesUpdater(name=name, dotfiles=entries.pack())
        )
