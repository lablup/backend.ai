"""Types for session creation and enqueueing."""

from collections.abc import Mapping
from dataclasses import dataclass

from ai.backend.common.identifier.image import ImageID
from ai.backend.common.identifier.resource_group import ResourceGroupID, ResourceGroupName
from ai.backend.common.types import (
    SessionId,
    SlotName,
    SlotTypes,
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
from ai.backend.manager.models.scaling_group import ScalingGroupOpts


@dataclass
class SessionDependencyData:
    """Data for session dependency relationships."""

    session_id: SessionId
    depends_on: SessionId


@dataclass
class AllowedScalingGroup:
    """Allowed scaling group for a user."""

    id: ResourceGroupID
    name: ResourceGroupName
    is_private: bool
    scheduler_opts: ScalingGroupOpts


@dataclass(frozen=True)
class ResourceGroupEnqueueInfo:
    """Enqueue-time information read from the target resource group."""

    defaults: DefaultSessionOptions
    network: ScalingGroupNetworkInfo | None
    allow_fractional: bool
    # Slot kinds served by the group's non-terminated agents
    known_slot_types: Mapping[SlotName, SlotTypes]


@dataclass(frozen=True)
class UserEnqueueFetch:
    """DB-derived enqueue-time information of the session owner."""

    policy: UserEnqueuePolicy | None
    container_user: ContainerUserInfo
    dotfiles: DotfileBundle
    pending_session_count: int


@dataclass(frozen=True)
class UserEnqueueInfo(UserEnqueueFetch):
    """The owner's full enqueue information: DB-derived fields plus the
    storage-manager mount resolution.

    ``vfolder_mounts_by_role`` is keyed by ``KernelGroup.role``: each
    group's mount requests resolve to one ``VFolderMount`` tuple that
    every replica sharing the role copies verbatim. It stays empty for
    resource-only callers such as compute-schedule.
    """

    vfolder_mounts_by_role: Mapping[str, tuple[VFolderMount, ...]]

    @classmethod
    def from_fetch(
        cls,
        base: UserEnqueueFetch,
        vfolder_mounts_by_role: Mapping[str, tuple[VFolderMount, ...]],
    ) -> UserEnqueueInfo:
        """Complete the DB-derived fields with the resolved mounts."""
        return cls(
            policy=base.policy,
            container_user=base.container_user,
            dotfiles=base.dotfiles,
            pending_session_count=base.pending_session_count,
            vfolder_mounts_by_role=vfolder_mounts_by_role,
        )


@dataclass(frozen=True)
class GlobalEnqueueInfo:
    """Enqueue-time information from cluster-global registries."""

    image_infos: Mapping[ImageID, ImageInfo]
    slot_type_info: SlotTypeInfo


@dataclass(frozen=True)
class SessionSpecFetch:
    """DB-side sources of the enqueue context (no storage RPC involved).

    The repository composes this with the separately resolved vfolder
    mounts into the final :class:`SessionSpecContext`.
    """

    resource_group: ResourceGroupEnqueueInfo
    global_info: GlobalEnqueueInfo
    user: UserEnqueueFetch


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
