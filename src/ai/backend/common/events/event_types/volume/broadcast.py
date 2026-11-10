from __future__ import annotations

from typing import override

from ai.backend.common.events.types import AbstractBroadcastEvent, EventDomain
from ai.backend.common.events.user_event.user_event import UserEvent
from ai.backend.common.types import QuotaScopeID, VolumeMountableNodeType


class BaseVolumeEvent(AbstractBroadcastEvent):
    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.VOLUME

    @override
    def domain_id(self) -> str | None:
        return None

    @override
    def user_event(self) -> UserEvent | None:
        return None


class DoVolumeMountEvent(BaseVolumeEvent):
    # Let storage proxies and agents find the real path of volume
    # with their mount_path or mount_prefix.
    dir_name: str
    volume_backend_name: str
    quota_scope_id: QuotaScopeID

    fs_location: str
    fs_type: str = "nfs"
    cmd_options: str | None = None
    scaling_group: str | None = None

    # if `edit_fstab` is False, `fstab_path` is ignored
    # if `edit_fstab` is True, `fstab_path` or "/etc/fstab" is used to edit fstab
    edit_fstab: bool = False
    fstab_path: str = "/etc/fstab"

    @classmethod
    @override
    def event_name(cls) -> str:
        return "do_volume_mount"


class DoVolumeUnmountEvent(BaseVolumeEvent):
    # Let storage proxies and agents find the real path of volume
    # with their mount_path or mount_prefix.
    dir_name: str
    volume_backend_name: str
    quota_scope_id: QuotaScopeID
    scaling_group: str | None = None

    # if `edit_fstab` is False, `fstab_path` is ignored
    # if `edit_fstab` is True, `fstab_path` or "/etc/fstab" is used to edit fstab
    edit_fstab: bool = False
    fstab_path: str | None = None

    @classmethod
    @override
    def event_name(cls) -> str:
        return "do_volume_unmount"


class BaseAgentVolumeMountEvent(BaseVolumeEvent):
    node_id: str
    node_type: VolumeMountableNodeType
    mount_path: str
    quota_scope_id: QuotaScopeID
    err_msg: str | None = None


class VolumeMounted(BaseAgentVolumeMountEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "volume_mounted"


class VolumeUnmounted(BaseAgentVolumeMountEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "volume_unmounted"
