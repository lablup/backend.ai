from __future__ import annotations

import enum
from uuid import UUID

from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.common.exception import UnreachableError

__all__ = ("VFolderAutoMountScopeType",)


class VFolderAutoMountScopeType(enum.StrEnum):
    """Scope whose sessions a vfolder is auto-mounted into; a personal project is a project,
    and a user scope is mapped to the user directly."""

    PROJECT = "project"
    USER = "user"

    @classmethod
    def of_owner(cls, owner: EntityIdentifier) -> VFolderAutoMountScopeType:
        match owner:
            case _ if owner.entity_type() == ProjectEntityType():
                return cls.PROJECT
            case _ if owner.entity_type() == UserEntityType():
                return cls.USER
            case _:
                raise UnreachableError(
                    f"No vfolder auto-mount scope is owned by a {owner.entity_type()}"
                )

    def to_owner(self, scope_id: UUID) -> EntityIdentifier:
        match self:
            case VFolderAutoMountScopeType.PROJECT:
                return ProjectID(scope_id)
            case VFolderAutoMountScopeType.USER:
                return UserID(scope_id)
