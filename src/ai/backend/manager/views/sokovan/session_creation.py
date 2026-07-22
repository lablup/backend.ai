"""Session creation context types shared with the scheduling controller."""

from collections.abc import Mapping
from dataclasses import dataclass

from ai.backend.common.identifier.image import ImageID
from ai.backend.common.types import (
    SlotName,
    VFolderMount,
)
from ai.backend.manager.data.dotfile.types import DotfileBundle
from ai.backend.manager.data.resource.types import SlotTypeInfo, UserEnqueuePolicy
from ai.backend.manager.data.session.creation import (
    ContainerUserInfo,
    ImageInfo,
    ScalingGroupNetworkInfo,
)
from ai.backend.manager.data.session.options import DefaultSessionOptions


@dataclass(frozen=True)
class ResourceGroupEnqueueInfo:
    """Enqueue-time information read from the target resource group."""

    defaults: DefaultSessionOptions
    network: ScalingGroupNetworkInfo | None
    allow_fractional: bool
    # Slot names served by the group's non-terminated agents (membership
    # only; unit metadata lives in the global registry SlotTypeInfo)
    served_slot_names: frozenset[SlotName]


@dataclass(frozen=True)
class UserEnqueueInfo:
    """The owner's full enqueue information: DB-derived fields plus the
    storage-manager mount resolution.

    ``vfolder_mounts_by_role`` is keyed by ``KernelGroup.role``: each
    group's mount requests resolve to one ``VFolderMount`` tuple that
    every replica sharing the role copies verbatim. It stays empty for
    resource-only callers such as compute-schedule.
    """

    policy: UserEnqueuePolicy | None
    container_user: ContainerUserInfo
    dotfiles: DotfileBundle
    pending_session_count: int
    vfolder_mounts_by_role: Mapping[str, tuple[VFolderMount, ...]]


@dataclass(frozen=True)
class GlobalEnqueueInfo:
    """Enqueue-time information from cluster-global registries."""

    image_infos: Mapping[ImageID, ImageInfo]
    slot_type_info: SlotTypeInfo


@dataclass(frozen=True)
class SessionSpecContext:
    """Shared read-only context the preparer and validator chains consume.

    Grouped by data source: the target resource group, the session
    owner, and cluster-global registries. Assembled entirely inside the
    repository (DB reads plus the storage-manager mount resolution) so
    it only ever exists in a complete state.
    """

    resource_group: ResourceGroupEnqueueInfo
    user: UserEnqueueInfo
    global_info: GlobalEnqueueInfo
