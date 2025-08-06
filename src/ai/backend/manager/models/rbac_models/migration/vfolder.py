import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Self, cast, override

from ai.backend.manager.data.permission.association_scopes_entities import (
    AssociationScopesEntitiesCreateInput,
)
from ai.backend.manager.data.permission.id import ObjectId, ScopeId
from ai.backend.manager.models.vfolder import (
    VFolderOwnershipType,
    VFolderPermissionRow,
    VFolderRow,
)

from .types import PermissionCreateInputGroup

ENTITY_TYPE = "vfolder"
ROLE_NAME_PREFIX = "vfolder_granted_"
OBJECT_PERMISSION_DEFAULT_OPERATION_VALUE = "read"


class VFolderData(ABC):
    @abstractmethod
    def to_association_scopes_entities_create_input(self) -> AssociationScopesEntitiesCreateInput:
        """
        Convert the VFolderData instance to an AssociationScopesEntitiesCreateInput.
        This method should be implemented by subclasses to provide the necessary conversion.
        """
        raise NotImplementedError


@dataclass
class UserVFolderData(VFolderData):
    id: uuid.UUID
    user_id: uuid.UUID

    @override
    def to_association_scopes_entities_create_input(self) -> AssociationScopesEntitiesCreateInput:
        return AssociationScopesEntitiesCreateInput(
            scope_id=ScopeId(
                scope_type="user",
                scope_id=str(self.user_id),
            ),
            object_id=ObjectId(entity_type=ENTITY_TYPE, entity_id=str(self.id)),
        )


@dataclass
class ProjectVFolderData(VFolderData):
    id: uuid.UUID
    project_id: uuid.UUID

    @override
    def to_association_scopes_entities_create_input(self) -> AssociationScopesEntitiesCreateInput:
        return AssociationScopesEntitiesCreateInput(
            scope_id=ScopeId(
                scope_type="project",
                scope_id=str(self.project_id),
            ),
            object_id=ObjectId(entity_type=ENTITY_TYPE, entity_id=str(self.id)),
        )


@dataclass
class VFolderPermissionData(VFolderData):
    vfolder_id: uuid.UUID
    user_id: uuid.UUID

    @classmethod
    def from_row(cls, row: VFolderPermissionRow) -> Self:
        return cls(
            vfolder_id=row.vfolder,
            user_id=row.user,
        )

    @override
    def to_association_scopes_entities_create_input(self) -> AssociationScopesEntitiesCreateInput:
        return AssociationScopesEntitiesCreateInput(
            scope_id=ScopeId(
                scope_type="user",
                scope_id=str(self.user_id),
            ),
            object_id=ObjectId(entity_type=ENTITY_TYPE, entity_id=str(self.vfolder_id)),
        )


def vfolder_row_to_rbac_row(vfolder: VFolderRow) -> PermissionCreateInputGroup:
    ownership_type = cast(VFolderOwnershipType, vfolder.ownership_type)
    data: UserVFolderData | ProjectVFolderData
    match ownership_type:
        case VFolderOwnershipType.USER:
            data = UserVFolderData(
                id=vfolder.id,
                user_id=vfolder.user,
            )
        case VFolderOwnershipType.GROUP:
            data = ProjectVFolderData(
                id=vfolder.id,
                project_id=vfolder.group,
            )
    association_inputs = [data.to_association_scopes_entities_create_input()]
    return PermissionCreateInputGroup(
        association_scopes_entities=association_inputs,
    )


def vfolder_permission_row_to_rbac_row(
    vfolder_permission: VFolderPermissionRow,
) -> PermissionCreateInputGroup:
    data = VFolderPermissionData.from_row(vfolder_permission)
    association_inputs = [data.to_association_scopes_entities_create_input()]
    return PermissionCreateInputGroup(
        association_scopes_entities=association_inputs,
    )
