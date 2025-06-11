from dataclasses import dataclass
from typing import Optional, override

from ai.backend.common.events.types import AbstractBroadcastEvent, EventDomain
from ai.backend.common.events.user_event.user_event import UserEvent
from ai.backend.common.types import QuotaScopeID, VolumeMountableNodeType


class BaseVolumeEvent(AbstractBroadcastEvent):
    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.VOLUME

    @override
    def domain_id(self) -> Optional[str]:
        return None

    @override
    def user_event(self) -> Optional[UserEvent]:
        return None


@dataclass
class DoVolumeMountEvent(BaseVolumeEvent):
    # Let storage proxies and agents find the real path of volume
    # with their mount_path or mount_prefix.
    dir_name: str
    volume_backend_name: str
    quota_scope_id: QuotaScopeID

    fs_location: str
    fs_type: str = "nfs"
    cmd_options: Optional[str] = None
    scaling_group: Optional[str] = None

    # if `edit_fstab` is False, `fstab_path` is ignored
    # if `edit_fstab` is True, `fstab_path` or "/etc/fstab" is used to edit fstab
    edit_fstab: bool = False
    fstab_path: str = "/etc/fstab"

    def serialize(self) -> tuple:
        return (
            self.dir_name,
            self.volume_backend_name,
            str(self.quota_scope_id),
            self.fs_location,
            self.fs_type,
            self.cmd_options,
            self.scaling_group,
            self.edit_fstab,
            self.fstab_path,
        )

    @classmethod
    def deserialize(cls, value: tuple):
        return cls(
            dir_name=value[0],
            volume_backend_name=value[1],
            quota_scope_id=QuotaScopeID.parse(value[2]),
            fs_location=value[3],
            fs_type=value[4],
            cmd_options=value[5],
            scaling_group=value[6],
            edit_fstab=value[7],
            fstab_path=value[8],
        )

    @classmethod
    def event_name(cls) -> str:
        return "do_volume_mount"


@dataclass
class DoVolumeUnmountEvent(BaseVolumeEvent):
    # Let storage proxies and agents find the real path of volume
    # with their mount_path or mount_prefix.
    dir_name: str
    volume_backend_name: str
    quota_scope_id: QuotaScopeID
    scaling_group: Optional[str] = None

    # if `edit_fstab` is False, `fstab_path` is ignored
    # if `edit_fstab` is True, `fstab_path` or "/etc/fstab" is used to edit fstab
    edit_fstab: bool = False
    fstab_path: Optional[str] = None

    def serialize(self) -> tuple:
        return (
            self.dir_name,
            self.volume_backend_name,
            str(self.quota_scope_id),
            self.scaling_group,
            self.edit_fstab,
            self.fstab_path,
        )

    @classmethod
    def deserialize(cls, value: tuple):
        return cls(
            dir_name=value[0],
            volume_backend_name=value[1],
            quota_scope_id=QuotaScopeID.parse(value[2]),
            scaling_group=value[3],
            edit_fstab=value[4],
            fstab_path=value[5],
        )

    @classmethod
    def event_name(cls) -> str:
        return "do_volume_unmount"


@dataclass
class BaseAgentVolumeMountEvent(BaseVolumeEvent):
    node_id: str
    node_type: VolumeMountableNodeType
    mount_path: str
    quota_scope_id: QuotaScopeID
    err_msg: Optional[str] = None

    def serialize(self) -> tuple:
        return (
            self.node_id,
            str(self.node_type),
            self.mount_path,
            str(self.quota_scope_id),
            self.err_msg,
        )

    @classmethod
    def deserialize(cls, value: tuple):
        return cls(
            value[0],
            VolumeMountableNodeType(value[1]),
            value[2],
            QuotaScopeID.parse(value[3]),
            value[4],
        )


class VolumeMounted(BaseAgentVolumeMountEvent):
    @classmethod
    def event_name(cls) -> str:
        return "volume_mounted"


class VolumeUnmounted(BaseAgentVolumeMountEvent):
    @classmethod
    def event_name(cls) -> str:
        return "volume_unmounted"
