from __future__ import annotations

import logging
import uuid

from ai.backend.common.contexts.user import current_user
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.errors.common import GenericForbidden
from ai.backend.manager.errors.resource import ProjectNotFound
from ai.backend.manager.errors.storage import DotfileNotFound
from ai.backend.manager.models.domain import verify_dotfile_name
from ai.backend.manager.repositories.group_config.repository import GroupConfigRepository
from ai.backend.manager.repositories.group_config.types import DotfileInput
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

    async def _resolve_group_for_admin(
        self,
        domain_name: str | None,
        group_id_or_name: uuid.UUID | str,
        user_domain: str,
        is_superadmin: bool,
    ) -> uuid.UUID:
        """
        Resolve group for admin operations (create, update, delete dotfiles).

        Validates that admin has permission to modify the group's dotfiles.
        """
        group_id = await self._group_config_repository.resolve_group_id(
            domain_name, group_id_or_name
        )

        if not is_superadmin:
            group_domain = await self._group_config_repository.get_group_domain(group_id)
            if user_domain != group_domain:
                raise GenericForbidden("Admins cannot modify group dotfiles of other domains")

        return group_id

    async def _resolve_group_for_user(
        self,
        domain_name: str | None,
        group_id_or_name: uuid.UUID | str,
        user_id: uuid.UUID,
        user_domain: str,
        is_superadmin: bool,
        is_admin: bool,
    ) -> uuid.UUID:
        """
        Resolve group for user operations (list, get dotfiles).

        Validates that user has permission to access the group's dotfiles.
        """
        group_id = await self._group_config_repository.resolve_group_id(
            domain_name, group_id_or_name
        )

        if is_superadmin:
            return group_id

        group_domain = await self._group_config_repository.get_group_domain(group_id)

        if is_admin:
            if user_domain != group_domain:
                raise GenericForbidden(
                    "Domain admins cannot access group dotfiles of other domains"
                )
            return group_id

        # Regular user: check if they are a member of the group
        is_member = await self._group_config_repository.check_user_in_group(user_id, group_id)
        if not is_member:
            raise GenericForbidden("Users cannot access group dotfiles of other groups")

        return group_id

    async def create_dotfile(self, action: CreateDotfileAction) -> CreateDotfileActionResult:
        user = current_user()
        assert user is not None

        if not verify_dotfile_name(action.path):
            raise InvalidAPIParameters("dotfile path is reserved for internal operations.")

        group_id = await self._resolve_group_for_admin(
            action.domain_name,
            action.group_id_or_name,
            user.domain_name,
            user.is_superadmin,
        )

        await self._group_config_repository.add_dotfile(
            group_id,
            DotfileInput(path=action.path, permission=action.permission, data=action.data),
        )
        return CreateDotfileActionResult(group_id=group_id)

    async def list_dotfiles(self, action: ListDotfilesAction) -> ListDotfilesActionResult:
        user = current_user()
        assert user is not None

        group_id = await self._resolve_group_for_user(
            action.domain_name,
            action.group_id_or_name,
            user.user_id,
            user.domain_name,
            user.is_superadmin,
            user.is_admin,
        )

        result = await self._group_config_repository.get_dotfiles(group_id)
        return ListDotfilesActionResult(dotfiles=result.dotfiles)

    async def get_dotfile(self, action: GetDotfileAction) -> GetDotfileActionResult:
        user = current_user()
        assert user is not None

        group_id = await self._resolve_group_for_user(
            action.domain_name,
            action.group_id_or_name,
            user.user_id,
            user.domain_name,
            user.is_superadmin,
            user.is_admin,
        )

        result = await self._group_config_repository.get_dotfiles(group_id)
        for dotfile in result.dotfiles:
            if dotfile["path"] == action.path:
                return GetDotfileActionResult(dotfile=dotfile)
        raise DotfileNotFound

    async def update_dotfile(self, action: UpdateDotfileAction) -> UpdateDotfileActionResult:
        user = current_user()
        assert user is not None

        group_id = await self._resolve_group_for_admin(
            action.domain_name,
            action.group_id_or_name,
            user.domain_name,
            user.is_superadmin,
        )

        await self._group_config_repository.modify_dotfile(
            group_id,
            DotfileInput(path=action.path, permission=action.permission, data=action.data),
        )
        return UpdateDotfileActionResult(group_id=group_id)

    async def delete_dotfile(self, action: DeleteDotfileAction) -> DeleteDotfileActionResult:
        user = current_user()
        assert user is not None

        group_id = await self._resolve_group_for_admin(
            action.domain_name,
            action.group_id_or_name,
            user.domain_name,
            user.is_superadmin,
        )

        try:
            await self._group_config_repository.remove_dotfile(group_id, action.path)
        except ProjectNotFound:
            # Original API raises DotfileNotFound when group is not found in delete
            raise DotfileNotFound

        return DeleteDotfileActionResult(success=True)
