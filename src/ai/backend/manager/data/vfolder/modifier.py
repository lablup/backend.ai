from dataclasses import dataclass, field
from typing import Any, override
from uuid import UUID

from ai.backend.manager.models.vfolder import VFolderOwnershipType, VFolderPermission
from ai.backend.manager.types import OptionalState, PartialModifier, TriState


@dataclass
class VFolderModifier(PartialModifier):
    """Modifier for vfolder operations."""

    name: OptionalState[str] = field(default_factory=OptionalState.nop)
    host: OptionalState[str] = field(default_factory=OptionalState.nop)
    quota_scope_id: OptionalState[str] = field(default_factory=OptionalState.nop)
    usage_mode: OptionalState[str] = field(default_factory=OptionalState.nop)
    permission: OptionalState[VFolderPermission] = field(default_factory=OptionalState.nop)
    ownership_type: OptionalState[VFolderOwnershipType] = field(default_factory=OptionalState.nop)
    user: TriState[UUID] = field(default_factory=TriState.nop)
    group: TriState[UUID] = field(default_factory=TriState.nop)
    unmanaged_path: TriState[str] = field(default_factory=TriState.nop)
    cloneable: OptionalState[bool] = field(default_factory=OptionalState.nop)

    @override
    def fields_to_update(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.name.update_dict(to_update, "name")
        self.host.update_dict(to_update, "host")
        self.quota_scope_id.update_dict(to_update, "quota_scope_id")
        self.usage_mode.update_dict(to_update, "usage_mode")
        self.permission.update_dict(to_update, "permission")
        self.ownership_type.update_dict(to_update, "ownership_type")
        self.user.update_dict(to_update, "user")
        self.group.update_dict(to_update, "group")
        self.unmanaged_path.update_dict(to_update, "unmanaged_path")
        self.cloneable.update_dict(to_update, "cloneable")
        return to_update


@dataclass
class VFolderPermissionModifier(PartialModifier):
    """Modifier for vfolder permission operations."""

    vfolder: OptionalState[UUID] = field(default_factory=OptionalState.nop)
    user: OptionalState[UUID] = field(default_factory=OptionalState.nop)
    permission: OptionalState[VFolderPermission] = field(default_factory=OptionalState.nop)

    @override
    def fields_to_update(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.vfolder.update_dict(to_update, "vfolder")
        self.user.update_dict(to_update, "user")
        self.permission.update_dict(to_update, "permission")
        return to_update


@dataclass
class VFolderInvitationModifier(PartialModifier):
    """Modifier for vfolder invitation operations."""

    vfolder: OptionalState[UUID] = field(default_factory=OptionalState.nop)
    inviter: OptionalState[str] = field(default_factory=OptionalState.nop)
    invitee: OptionalState[str] = field(default_factory=OptionalState.nop)
    permission: OptionalState[VFolderPermission] = field(default_factory=OptionalState.nop)

    @override
    def fields_to_update(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.vfolder.update_dict(to_update, "vfolder")
        self.inviter.update_dict(to_update, "inviter")
        self.invitee.update_dict(to_update, "invitee")
        self.permission.update_dict(to_update, "permission")
        return to_update
