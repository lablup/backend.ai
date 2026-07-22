"""Types for session creation and enqueueing."""

from collections.abc import Mapping
from dataclasses import dataclass, field

from ai.backend.common.identifier.image import ImageID
from ai.backend.common.identifier.resource_group import ResourceGroupID, ResourceGroupName
from ai.backend.common.types import (
    SessionId,
    SlotName,
    SlotTypes,
    VFolderMount,
)
from ai.backend.manager.data.dotfile.types import DotfileBundle
from ai.backend.manager.data.resource.types import SlotTypePolicy, UserEnqueuePolicy
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


@dataclass
class SessionSpecContext:
    """Shared read-only context the preparer and validator chains consume.

    Assembled from ``ScheduleDBSource.fetch_session_spec_contexts`` in a
    single readonly transaction; ``vfolder_mounts_by_role`` is filled in
    by the controller after the separate storage-manager resolution step
    (it stays empty for resource-only callers such as compute-schedule).

    ``vfolder_mounts_by_role`` is keyed by ``KernelGroup.role``: each
    group's mount requests resolve to one ``VFolderMount`` tuple that
    every replica sharing the role copies verbatim.
    """

    resource_group_defaults: DefaultSessionOptions
    resource_group_network: ScalingGroupNetworkInfo | None
    container_user_info: ContainerUserInfo
    image_infos: dict[ImageID, ImageInfo]
    resource_group_allow_fractional: bool
    dotfile_data: DotfileBundle
    user_enqueue_policy: UserEnqueuePolicy | None
    known_slot_types: Mapping[SlotName, SlotTypes] = field(default_factory=dict)
    slot_type_policy: SlotTypePolicy = field(default_factory=SlotTypePolicy)
    pending_session_count: int = 0
    vfolder_mounts_by_role: Mapping[str, tuple[VFolderMount, ...]] = field(default_factory=dict)
