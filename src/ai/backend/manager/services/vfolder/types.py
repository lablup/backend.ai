import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import (
    Any,
)

from ai.backend.common.types import VFolderMountPolicy
from ai.backend.manager.models.vfolder import (
    VFolderInvitationState,
)


@dataclass
class VFolderUsageInfo:
    num_files: int
    used_bytes: int


@dataclass
class VFolderInvitationInfo:
    id: uuid.UUID
    vfolder_id: uuid.UUID
    vfolder_name: str
    invitee_user_email: str
    inviter_user_email: str
    inviter_username: str | None
    mount_permission: VFolderMountPolicy
    created_at: datetime
    modified_at: datetime | None
    status: VFolderInvitationState

    def to_json(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "vfolder_id": str(self.vfolder_id),
            "vfolder_name": self.vfolder_name,
            "invitee_user_email": self.invitee_user_email,
            "inviter_user_email": self.inviter_user_email,
            "inviter_username": self.inviter_username,
            "mount_permission": self.mount_permission.value,
            "created_at": self.created_at.isoformat(),
            "modified_at": self.modified_at.isoformat() if self.modified_at is not None else None,
            "status": self.status.value,
        }


@dataclass
class FileInfo:
    name: str
    type: str
    size: int
    mode: str
    created: str
    modified: str

    def to_json(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type,
            "size": self.size,
            "mode": self.mode,
            "created": self.created,
            "modified": self.modified,
        }
