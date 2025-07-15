from dataclasses import dataclass
from typing import Any, Optional, override
from uuid import UUID

from ai.backend.manager.models.vfolder import VFolderOwnershipType, VFolderPermission
from ai.backend.manager.types import Creator


@dataclass
class VFolderCreator(Creator):
    """Creator for vfolder operations."""

    id: UUID
    name: str
    host: str
    domain_name: str
    quota_scope_id: str
    usage_mode: str
    permission: VFolderPermission
    ownership_type: VFolderOwnershipType
    creator: str
    user: Optional[UUID] = None
    group: Optional[UUID] = None
    unmanaged_path: Optional[str] = None
    cloneable: bool = False

    @override
    def fields_to_store(self) -> dict[str, Any]:
        to_store = {
            "id": self.id,
            "name": self.name,
            "host": self.host,
            "domain_name": self.domain_name,
            "quota_scope_id": self.quota_scope_id,
            "usage_mode": self.usage_mode,
            "permission": self.permission,
            "ownership_type": self.ownership_type,
            "creator": self.creator,
            "cloneable": self.cloneable,
        }
        if self.user is not None:
            to_store["user"] = self.user
        if self.group is not None:
            to_store["group"] = self.group
        if self.unmanaged_path is not None:
            to_store["unmanaged_path"] = self.unmanaged_path
        return to_store


@dataclass
class VFolderPermissionCreator(Creator):
    """Creator for vfolder permission operations."""

    id: UUID
    vfolder: UUID
    user: UUID
    permission: VFolderPermission

    @override
    def fields_to_store(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "vfolder": self.vfolder,
            "user": self.user,
            "permission": self.permission,
        }


@dataclass
class VFolderInvitationCreator(Creator):
    """Creator for vfolder invitation operations."""

    id: UUID
    vfolder: UUID
    inviter: str
    invitee: str
    permission: VFolderPermission

    @override
    def fields_to_store(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "vfolder": self.vfolder,
            "inviter": self.inviter,
            "invitee": self.invitee,
            "permission": self.permission,
        }
