"""Repository-internal session creation fetch types."""

from collections.abc import Mapping
from dataclasses import dataclass

from ai.backend.common.identifier.resource_group import ResourceGroupID, ResourceGroupName
from ai.backend.common.types import (
    SessionId,
    VFolderMount,
)
from ai.backend.manager.data.dotfile.types import DotfileBundle
from ai.backend.manager.data.resource.types import UserEnqueuePolicy
from ai.backend.manager.data.session.creation import ContainerUserInfo
from ai.backend.manager.models.scaling_group import ScalingGroupOpts
from ai.backend.manager.views.sokovan.session_creation import (
    GlobalEnqueueInfo,
    ResourceGroupEnqueueInfo,
    UserEnqueueInfo,
)


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
class UserEnqueueFetch:
    """DB-derived enqueue-time information of the session owner."""

    policy: UserEnqueuePolicy | None
    container_user: ContainerUserInfo
    dotfiles: DotfileBundle
    pending_session_count: int

    def to_info(
        self,
        vfolder_mounts_by_role: Mapping[str, tuple[VFolderMount, ...]],
    ) -> UserEnqueueInfo:
        """Complete the DB-derived fields with the resolved mounts."""
        return UserEnqueueInfo(
            policy=self.policy,
            container_user=self.container_user,
            dotfiles=self.dotfiles,
            pending_session_count=self.pending_session_count,
            vfolder_mounts_by_role=vfolder_mounts_by_role,
        )


@dataclass(frozen=True)
class SessionSpecFetch:
    """DB-side sources of the enqueue context (no storage RPC involved).

    The repository composes this with the separately resolved vfolder
    mounts into the final :class:`SessionSpecContext`.
    """

    resource_group: ResourceGroupEnqueueInfo
    global_info: GlobalEnqueueInfo
    user: UserEnqueueFetch
