from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ai.backend.common.types import (
    DefaultForUnspecified,
    ResourceSlot,
    SlotName,
    SlotTypes,
    VFolderHostPermissionMap,
)


@dataclass
class UserResourcePolicyData:
    name: str
    created_at: datetime | None = field(compare=False, default=None)
    max_vfolder_count: int = 0
    max_quota_scope_size: int = 0
    max_session_count_per_model_session: int = 0
    max_customized_image_count: int = 3
    max_concurrent_logins: int | None = None


@dataclass
class ProjectResourcePolicyData:
    name: str
    created_at: datetime | None = field(compare=False, default=None)
    max_vfolder_count: int = 0
    max_quota_scope_size: int = 0
    max_network_count: int = 0


@dataclass
class KeyPairResourcePolicyData:
    name: str
    created_at: datetime | None = field(compare=False)
    default_for_unspecified: DefaultForUnspecified
    total_resource_slots: ResourceSlot
    max_session_lifetime: int
    max_concurrent_sessions: int
    max_pending_session_count: int | None
    max_pending_session_resource_slots: Any | None  # TODO: Use ResourceSlot.
    max_concurrent_sftp_sessions: int
    max_containers_per_session: int
    idle_timeout: int
    allowed_vfolder_hosts: dict[str, Any]


@dataclass
class ScalingGroupProxyTarget:
    addr: str
    api_token: str


@dataclass(frozen=True)
class SlotTypeInfo:
    """Global slot-type registry from `resource_slot_types`.

    - types: slot name -> unit kind for every enabled slot, in registry
      ``rank`` order (dict insertion order preserves it). Membership in
      this mapping is the "enabled" test; image-side validators skip
      slots outside it instead of rejecting them. The unit kind also
      drives value humanization.
    - required: slot names with required=true. Sessions must request
      nonzero amounts for these slots.
    """

    types: Mapping[SlotName, SlotTypes]
    required: frozenset[SlotName]


@dataclass(frozen=True)
class UserEnqueuePolicy:
    """Per-user gates applied at session enqueue.

    Sourced from the user's main-keypair resource policy row until
    user-level policy columns exist; carries only the fields the
    enqueue path actually consumes.
    """

    max_containers_per_session: int
    max_pending_session_count: int | None
    allowed_vfolder_hosts: VFolderHostPermissionMap
