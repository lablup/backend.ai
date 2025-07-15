from dataclasses import dataclass
from typing import Any, Optional, override
from uuid import UUID

from ai.backend.common.types import AccessKey, ResourceSlot, SessionId
from ai.backend.manager.types import Creator


@dataclass
class SessionCreator(Creator):
    """Creator for session operations."""
    
    id: SessionId
    name: str
    access_key: AccessKey
    image: str
    group_id: UUID
    domain_name: str
    user_uuid: UUID
    resource_slots: ResourceSlot
    cluster_mode: str = "single-node"
    cluster_size: int = 1
    environ: Optional[dict[str, str]] = None
    mounts: Optional[list[str]] = None
    bootstrap_script: Optional[str] = None
    
    @override
    def fields_to_store(self) -> dict[str, Any]:
        to_store = {
            "id": self.id,
            "name": self.name,
            "access_key": self.access_key,
            "image": self.image,
            "group_id": self.group_id,
            "domain_name": self.domain_name,
            "user_uuid": self.user_uuid,
            "resource_slots": self.resource_slots,
            "cluster_mode": self.cluster_mode,
            "cluster_size": self.cluster_size,
        }
        if self.environ is not None:
            to_store["environ"] = self.environ
        if self.mounts is not None:
            to_store["mounts"] = self.mounts
        if self.bootstrap_script is not None:
            to_store["bootstrap_script"] = self.bootstrap_script
        return to_store


@dataclass
class KernelCreator(Creator):
    """Creator for kernel operations."""
    
    id: UUID
    session_id: SessionId
    cluster_role: str
    cluster_idx: int
    image: str
    resource_slots: ResourceSlot
    local_rank: int = 0
    
    @override
    def fields_to_store(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "cluster_role": self.cluster_role,
            "cluster_idx": self.cluster_idx,
            "image": self.image,
            "resource_slots": self.resource_slots,
            "local_rank": self.local_rank,
        }