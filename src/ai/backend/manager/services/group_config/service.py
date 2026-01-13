from __future__ import annotations

import logging

from ai.backend.common import msgpack
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.errors.resource import ProjectNotFound
from ai.backend.manager.errors.storage import (
    DotfileAlreadyExists,
    DotfileCreationFailed,
    DotfileNotFound,
)
from ai.backend.manager.models.domain import MAXIMUM_DOTFILE_SIZE, verify_dotfile_name
from ai.backend.manager.repositories.group_config.repository import GroupConfigRepository
from ai.backend.manager.services.group_config.actions.create_dotfile import (
    CreateDotfileAction,
    CreateDotfileActionResult,
)
from ai.backend.manager.services.group_config.actions.delete_dotfile import (
    DeleteDotfileAction,
    DeleteDotfileActionResult,
)
from ai.backend.manager.services.group_config.actions.get_dotfile import (
    GetDotfileAction,
    GetDotfileActionResult,
)
from ai.backend.manager.services.group_config.actions.list_dotfiles import (
    ListDotfilesAction,
    ListDotfilesActionResult,
)
from ai.backend.manager.services.group_config.actions.update_dotfile import (
    UpdateDotfileAction,
    UpdateDotfileActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class GroupConfigService:
    _group_config_repository: GroupConfigRepository

    def __init__(
        self,
        group_config_repository: GroupConfigRepository,
    ) -> None:
        self._group_config_repository = group_config_repository

    async def create_dotfile(self, action: CreateDotfileAction) -> CreateDotfileActionResult:
        dotfiles, leftover_space = await self._group_config_repository.get_dotfiles(action.group_id)

        if leftover_space == 0:
            raise DotfileCreationFailed("No leftover space for dotfile storage")
        if len(dotfiles) == 100:
            raise DotfileCreationFailed("Dotfile creation limit reached")
        if not verify_dotfile_name(action.path):
            raise InvalidAPIParameters("dotfile path is reserved for internal operations.")

        duplicate = [x for x in dotfiles if x["path"] == action.path]
        if len(duplicate) > 0:
            raise DotfileAlreadyExists

        new_dotfiles = list(dotfiles)
        new_dotfiles.append({
            "path": action.path,
            "perm": action.permission,
            "data": action.data,
        })
        dotfile_packed = msgpack.packb(new_dotfiles)
        if len(dotfile_packed) > MAXIMUM_DOTFILE_SIZE:
            raise DotfileCreationFailed("No leftover space for dotfile storage")

        await self._group_config_repository.update_dotfiles(action.group_id, dotfile_packed)
        return CreateDotfileActionResult(group_id=action.group_id)

    async def list_dotfiles(self, action: ListDotfilesAction) -> ListDotfilesActionResult:
        dotfiles, _ = await self._group_config_repository.get_dotfiles(action.group_id)
        return ListDotfilesActionResult(dotfiles=dotfiles)

    async def get_dotfile(self, action: GetDotfileAction) -> GetDotfileActionResult:
        dotfiles, _ = await self._group_config_repository.get_dotfiles(action.group_id)
        for dotfile in dotfiles:
            if dotfile["path"] == action.path:
                return GetDotfileActionResult(dotfile=dotfile)
        raise DotfileNotFound

    async def update_dotfile(self, action: UpdateDotfileAction) -> UpdateDotfileActionResult:
        dotfiles, _ = await self._group_config_repository.get_dotfiles(action.group_id)
        new_dotfiles = [x for x in dotfiles if x["path"] != action.path]
        if len(new_dotfiles) == len(dotfiles):
            raise DotfileNotFound

        new_dotfiles.append({
            "path": action.path,
            "perm": action.permission,
            "data": action.data,
        })
        dotfile_packed = msgpack.packb(new_dotfiles)
        if len(dotfile_packed) > MAXIMUM_DOTFILE_SIZE:
            raise DotfileCreationFailed("No leftover space for dotfile storage")

        await self._group_config_repository.update_dotfiles(action.group_id, dotfile_packed)
        return UpdateDotfileActionResult(group_id=action.group_id)

    async def delete_dotfile(self, action: DeleteDotfileAction) -> DeleteDotfileActionResult:
        try:
            dotfiles, _ = await self._group_config_repository.get_dotfiles(action.group_id)
        except ProjectNotFound:
            # Original API raises DotfileNotFound when group is not found in delete
            raise DotfileNotFound

        new_dotfiles = [x for x in dotfiles if x["path"] != action.path]
        if len(new_dotfiles) == len(dotfiles):
            raise DotfileNotFound

        dotfile_packed = msgpack.packb(new_dotfiles)
        await self._group_config_repository.update_dotfiles(action.group_id, dotfile_packed)
        return DeleteDotfileActionResult(success=True)
