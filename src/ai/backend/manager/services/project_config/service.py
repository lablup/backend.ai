"""Service for project configuration (dotfiles) operations.

As there is an ongoing migration of renaming group to project,
there are some occurrences where "group" is being used as "project"
(e.g., GroupMembershipNotFoundError, InsufficientPrivilege).
It will be fixed in the future; for now understand them as the same concept.
"""

from __future__ import annotations

import logging
import uuid

from ai.backend.common.contexts.user import current_user
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.errors.auth import GroupMembershipNotFoundError, InsufficientPrivilege
from ai.backend.manager.errors.storage import DotfileNotFound
from ai.backend.manager.models.domain import verify_dotfile_name
from ai.backend.manager.repositories.project_config.repository import ProjectConfigRepository
from ai.backend.manager.repositories.project_config.types import DotfileInput
from ai.backend.manager.services.project_config.actions.create_dotfile import (
    CreateDotfileAction,
    CreateDotfileActionResult,
)
from ai.backend.manager.services.project_config.actions.delete_dotfile import (
    DeleteDotfileAction,
    DeleteDotfileActionResult,
)
from ai.backend.manager.services.project_config.actions.get_dotfile import (
    GetDotfileAction,
    GetDotfileActionResult,
)
from ai.backend.manager.services.project_config.actions.list_dotfiles import (
    ListDotfilesAction,
    ListDotfilesActionResult,
)
from ai.backend.manager.services.project_config.actions.update_dotfile import (
    UpdateDotfileAction,
    UpdateDotfileActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ProjectConfigService:
    _project_config_repository: ProjectConfigRepository

    def __init__(
        self,
        project_config_repository: ProjectConfigRepository,
    ) -> None:
        self._project_config_repository = project_config_repository

    async def _resolve_project_for_admin(
        self,
        domain_name: str | None,
        project_id_or_name: uuid.UUID | str,
    ) -> uuid.UUID:
        """
        Resolve project for admin operations (create, update, delete dotfiles).

        Validates that admin has permission to modify the project's dotfiles.
        """
        user = current_user()
        if user is None:
            raise InsufficientPrivilege("Authentication required")

        project = await self._project_config_repository.resolve_project(
            domain_name, project_id_or_name
        )

        if not user.is_superadmin:
            if user.domain_name != project.domain_name:
                raise InsufficientPrivilege(
                    "Admins cannot modify project dotfiles of other domains"
                )

        return project.id

    async def _resolve_project_for_user(
        self,
        domain_name: str | None,
        project_id_or_name: uuid.UUID | str,
    ) -> uuid.UUID:
        """
        Resolve project for user operations (list, get dotfiles).

        Validates that user has permission to access the project's dotfiles.
        """
        user = current_user()
        if user is None:
            raise InsufficientPrivilege("Authentication required")

        project = await self._project_config_repository.resolve_project(
            domain_name, project_id_or_name
        )

        if user.is_superadmin:
            return project.id

        if user.is_admin:
            if user.domain_name != project.domain_name:
                raise InsufficientPrivilege(
                    "Domain admins cannot access project dotfiles of other domains"
                )
            return project.id

        # Regular user: check if they are a member of the project
        is_member = await self._project_config_repository.check_user_in_project(
            user.user_id, project.id
        )
        if not is_member:
            raise GroupMembershipNotFoundError(
                "User cannot access project dotfiles of non-member projects"
            )

        return project.id

    async def create_dotfile(self, action: CreateDotfileAction) -> CreateDotfileActionResult:
        if not verify_dotfile_name(action.path):
            raise InvalidAPIParameters("dotfile path is reserved for internal operations.")

        project_id = await self._resolve_project_for_admin(
            action.domain_name,
            action.project_id_or_name,
        )

        await self._project_config_repository.add_dotfile(
            project_id,
            DotfileInput(path=action.path, permission=action.permission, data=action.data),
        )
        return CreateDotfileActionResult(project_id=project_id)

    async def list_dotfiles(self, action: ListDotfilesAction) -> ListDotfilesActionResult:
        project_id = await self._resolve_project_for_user(
            action.domain_name,
            action.project_id_or_name,
        )

        result = await self._project_config_repository.get_dotfiles(project_id)
        return ListDotfilesActionResult(dotfiles=result.dotfiles)

    async def get_dotfile(self, action: GetDotfileAction) -> GetDotfileActionResult:
        project_id = await self._resolve_project_for_user(
            action.domain_name,
            action.project_id_or_name,
        )

        result = await self._project_config_repository.get_dotfiles(project_id)
        for dotfile in result.dotfiles:
            if dotfile["path"] == action.path:
                return GetDotfileActionResult(dotfile=dotfile)
        raise DotfileNotFound

    async def update_dotfile(self, action: UpdateDotfileAction) -> UpdateDotfileActionResult:
        project_id = await self._resolve_project_for_admin(
            action.domain_name,
            action.project_id_or_name,
        )

        await self._project_config_repository.modify_dotfile(
            project_id,
            DotfileInput(path=action.path, permission=action.permission, data=action.data),
        )
        return UpdateDotfileActionResult(project_id=project_id)

    async def delete_dotfile(self, action: DeleteDotfileAction) -> DeleteDotfileActionResult:
        project_id = await self._resolve_project_for_admin(
            action.domain_name,
            action.project_id_or_name,
        )

        await self._project_config_repository.remove_dotfile(project_id, action.path)

        return DeleteDotfileActionResult(success=True)
