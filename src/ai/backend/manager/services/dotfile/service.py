from __future__ import annotations

import logging
import uuid
from typing import Final

from ai.backend.common import msgpack
from ai.backend.common.dto.manager.config.types import MAXIMUM_DOTFILE_SIZE
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.dotfile.types import DotfileQueryResult, DotfileScope
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.errors.resource import DomainNotFound, ProjectNotFound
from ai.backend.manager.errors.storage import (
    DotfileAlreadyExists,
    DotfileCreationFailed,
    DotfileNotFound,
)
from ai.backend.manager.models.domain import verify_dotfile_name
from ai.backend.manager.repositories.dotfile.repository import DotfileRepository

from .actions.check_group_membership import (
    CheckGroupMembershipAction,
    CheckGroupMembershipActionResult,
)
from .actions.create import CreateDotfileAction, CreateDotfileActionResult
from .actions.delete import DeleteDotfileAction, DeleteDotfileActionResult
from .actions.get_bootstrap import GetBootstrapScriptAction, GetBootstrapScriptActionResult
from .actions.list_or_get import ListOrGetDotfilesAction, ListOrGetDotfilesActionResult
from .actions.resolve_group import ResolveGroupAction, ResolveGroupActionResult
from .actions.update import UpdateDotfileAction, UpdateDotfileActionResult
from .actions.update_bootstrap import UpdateBootstrapScriptAction, UpdateBootstrapScriptActionResult

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class DotfileService:
    _repository: DotfileRepository

    def __init__(self, repository: DotfileRepository) -> None:
        self._repository = repository

    async def create_dotfile(self, action: CreateDotfileAction) -> CreateDotfileActionResult:
        """Create a dotfile in the specified scope."""
        query_result = await self._get_dotfiles(action.scope, action.entity_key)

        if not query_result.entries and query_result.leftover_space == MAXIMUM_DOTFILE_SIZE:
            # Entity not found (query returned empty with full leftover = no entity)
            self._raise_entity_not_found(action.scope)

        if query_result.leftover_space == 0:
            raise DotfileCreationFailed("No leftover space for dotfile storage")
        if len(query_result.entries) == 100:
            raise DotfileCreationFailed("Dotfile creation limit reached")
        if not verify_dotfile_name(action.path):
            raise InvalidAPIParameters("dotfile path is reserved for internal operations.")

        # Check for vFolder conflict (user scope only)
        if action.scope == DotfileScope.USER and action.user_uuid is not None:
            conflict = await self._repository.check_vfolder_conflict(action.user_uuid, action.path)
            if conflict:
                raise InvalidAPIParameters("dotfile path conflicts with your dot-prefixed vFolder")

        duplicate = [e for e in query_result.entries if e.path == action.path]
        if len(duplicate) > 0:
            raise DotfileAlreadyExists

        new_entries = [
            {"path": e.path, "perm": e.perm, "data": e.data} for e in query_result.entries
        ]
        new_entries.append({
            "path": action.path,
            "perm": action.permission,
            "data": action.data,
        })
        packed = msgpack.packb(new_entries)
        if len(packed) > MAXIMUM_DOTFILE_SIZE:
            raise DotfileCreationFailed("No leftover space for dotfile storage")

        await self._save_dotfiles(action.scope, action.entity_key, packed)
        return CreateDotfileActionResult()

    async def list_or_get_dotfiles(
        self, action: ListOrGetDotfilesAction
    ) -> ListOrGetDotfilesActionResult:
        """List all dotfiles or get a specific one by path."""
        query_result = await self._get_dotfiles(action.scope, action.entity_key)

        if action.path:
            for entry in query_result.entries:
                if entry.path == action.path:
                    return ListOrGetDotfilesActionResult(entries=[entry])
            raise DotfileNotFound
        return ListOrGetDotfilesActionResult(entries=query_result.entries)

    async def update_dotfile(self, action: UpdateDotfileAction) -> UpdateDotfileActionResult:
        """Update an existing dotfile."""
        query_result = await self._get_dotfiles(action.scope, action.entity_key)

        new_entries_raw = [
            {"path": e.path, "perm": e.perm, "data": e.data}
            for e in query_result.entries
            if e.path != action.path
        ]
        if len(new_entries_raw) == len(query_result.entries):
            raise DotfileNotFound
        new_entries_raw.append({
            "path": action.path,
            "perm": action.permission,
            "data": action.data,
        })
        packed = msgpack.packb(new_entries_raw)
        if len(packed) > MAXIMUM_DOTFILE_SIZE:
            raise DotfileCreationFailed("No leftover space for dotfile storage")

        await self._save_dotfiles(action.scope, action.entity_key, packed)
        return UpdateDotfileActionResult()

    async def delete_dotfile(self, action: DeleteDotfileAction) -> DeleteDotfileActionResult:
        """Delete a dotfile."""
        query_result = await self._get_dotfiles(action.scope, action.entity_key)

        new_entries_raw = [
            {"path": e.path, "perm": e.perm, "data": e.data}
            for e in query_result.entries
            if e.path != action.path
        ]
        if len(new_entries_raw) == len(query_result.entries):
            raise DotfileNotFound

        packed = msgpack.packb(new_entries_raw)
        await self._save_dotfiles(action.scope, action.entity_key, packed)
        return DeleteDotfileActionResult()

    async def resolve_group(self, action: ResolveGroupAction) -> ResolveGroupActionResult:
        """Resolve a group identifier to a (group_id, domain) pair."""
        group_id, domain = await self._repository.resolve_group(
            action.group_id_or_name,
            action.group_domain,
            action.user_domain,
        )
        if group_id is None or domain is None:
            raise ProjectNotFound
        return ResolveGroupActionResult(group_id=group_id, domain=domain)

    async def check_group_membership(
        self, action: CheckGroupMembershipAction
    ) -> CheckGroupMembershipActionResult:
        """Get the list of group IDs a user belongs to."""
        group_ids = await self._repository.get_user_group_ids(action.user_uuid)
        return CheckGroupMembershipActionResult(group_ids=group_ids)

    async def get_bootstrap_script(
        self, action: GetBootstrapScriptAction
    ) -> GetBootstrapScriptActionResult:
        """Get a user's bootstrap script."""
        script, _ = await self._repository.get_bootstrap_script(action.access_key)
        return GetBootstrapScriptActionResult(script=script)

    async def update_bootstrap_script(
        self, action: UpdateBootstrapScriptAction
    ) -> UpdateBootstrapScriptActionResult:
        """Update a user's bootstrap script."""
        script = action.script.strip()
        if len(script) > MAXIMUM_DOTFILE_SIZE:
            raise DotfileCreationFailed("Maximum bootstrap script length reached")
        await self._repository.save_bootstrap_script(action.access_key, script)
        return UpdateBootstrapScriptActionResult()

    # --- Internal helpers ---

    async def _get_dotfiles(
        self, scope: DotfileScope, entity_key: str | uuid.UUID
    ) -> DotfileQueryResult:
        if scope == DotfileScope.DOMAIN:
            return await self._repository.get_domain_dotfiles(str(entity_key))
        if scope == DotfileScope.GROUP:
            return await self._repository.get_group_dotfiles(
                entity_key if isinstance(entity_key, uuid.UUID) else uuid.UUID(str(entity_key))
            )
        if scope == DotfileScope.USER:
            return await self._repository.get_user_dotfiles(str(entity_key))
        raise ValueError(f"Unknown scope: {scope}")

    async def _save_dotfiles(
        self, scope: DotfileScope, entity_key: str | uuid.UUID, packed: bytes
    ) -> None:
        if scope == DotfileScope.DOMAIN:
            await self._repository.save_domain_dotfiles(str(entity_key), packed)
        elif scope == DotfileScope.GROUP:
            await self._repository.save_group_dotfiles(
                entity_key if isinstance(entity_key, uuid.UUID) else uuid.UUID(str(entity_key)),
                packed,
            )
        elif scope == DotfileScope.USER:
            await self._repository.save_user_dotfiles(str(entity_key), packed)
        else:
            raise ValueError(f"Unknown scope: {scope}")

    @staticmethod
    def _raise_entity_not_found(scope: DotfileScope) -> None:
        if scope == DotfileScope.DOMAIN:
            raise DomainNotFound("Input domain is not found")
        if scope == DotfileScope.GROUP:
            raise ProjectNotFound
        # USER scope: keypair always exists if authenticated
