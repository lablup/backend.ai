import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.events.dispatcher import EventDispatcher, EventProducer
from ai.backend.common.events.volume import (
    DoVolumeMountEvent,
    DoVolumeUnmountEvent,
    VolumeMounted,
    VolumeUnmounted,
)
from ai.backend.common.exception import VolumeMountFailed
from ai.backend.common.types import AgentId, VolumeMountableNodeType
from ai.backend.common.utils import mount, umount
from ai.backend.logging.utils import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


# TODO: Move this logic into a mount manager.
class MountDispatcher:
    _agent_id: AgentId
    _etcd: AsyncEtcd
    _local_config: Mapping[str, Any]
    _event_producer: EventProducer

    def __init__(
        self,
        agent_id: AgentId,
        etcd: AsyncEtcd,
        local_config: Mapping[str, Any],
        event_producer: EventProducer,
    ) -> None:
        self._agent_id = agent_id
        self._etcd = etcd
        self._local_config = local_config
        self._event_producer = event_producer

    async def handle_volume_mount(
        self,
        context: None,
        source: AgentId,
        event: DoVolumeMountEvent,
    ) -> None:
        if self._local_config["agent"]["cohabiting-storage-proxy"]:
            log.debug("Storage proxy is in the same node. Skip the volume task.")
            await self._event_producer.produce_event(
                VolumeMounted(
                    str(self._agent_id),
                    VolumeMountableNodeType.AGENT,
                    "",
                    event.quota_scope_id,
                )
            )
            return
        mount_prefix = await self._etcd.get("volumes/_mount")
        volume_mount_prefix: Optional[str] = self._local_config["agent"]["mount-path"]
        if volume_mount_prefix is None:
            volume_mount_prefix = "./"
        real_path = Path(volume_mount_prefix, event.dir_name)
        err_msg: Optional[str] = None
        try:
            await mount(
                str(real_path),
                event.fs_location,
                event.fs_type,
                event.cmd_options,
                event.edit_fstab,
                event.fstab_path,
                mount_prefix,
            )
        except VolumeMountFailed as e:
            err_msg = str(e)
        await self._event_producer.produce_event(
            VolumeMounted(
                str(self._agent_id),
                VolumeMountableNodeType.AGENT,
                str(real_path),
                event.quota_scope_id,
                err_msg,
            )
        )

    async def handle_volume_umount(
        self,
        context: None,
        source: AgentId,
        event: DoVolumeUnmountEvent,
    ) -> None:
        if self._local_config["agent"]["cohabiting-storage-proxy"]:
            log.debug("Storage proxy is in the same node. Skip the volume task.")
            await self._event_producer.produce_event(
                VolumeUnmounted(
                    str(self._agent_id),
                    VolumeMountableNodeType.AGENT,
                    "",
                    event.quota_scope_id,
                )
            )
            return
        mount_prefix = await self._etcd.get("volumes/_mount")
        timeout = await self._etcd.get("config/watcher/file-io-timeout")
        volume_mount_prefix = self._local_config["agent"]["mount-path"]
        real_path = Path(volume_mount_prefix, event.dir_name)
        err_msg: Optional[str] = None
        did_umount = False
        try:
            did_umount = await umount(
                str(real_path),
                mount_prefix,
                event.edit_fstab,
                event.fstab_path,
                timeout_sec=float(timeout) if timeout is not None else None,
            )
        except VolumeMountFailed as e:
            err_msg = str(e)
        if not did_umount:
            log.warning("{} does not exist. Skip umount", real_path)
        await self._event_producer.produce_event(
            VolumeUnmounted(
                str(self._agent_id),
                VolumeMountableNodeType.AGENT,
                str(real_path),
                event.quota_scope_id,
                err_msg,
            )
        )


@dataclass
class DispatcherArgs:
    agent_id: AgentId
    etcd: AsyncEtcd
    local_config: Mapping[str, Any]
    event_producer: EventProducer


class Dispatchers:
    _mount_dispatcher: MountDispatcher

    def __init__(self, args: DispatcherArgs) -> None:
        """
        Initialize the Dispatchers with the given arguments.
        """
        self._mount_dispatcher = MountDispatcher(
            args.agent_id,
            args.etcd,
            args.local_config,
            args.event_producer,
        )

    def _dispatch_agent_events(
        self,
        event_dispatcher: EventDispatcher,
    ) -> None:
        """
        Register event dispatchers for agent events.
        """
        # Register agent events here
        event_dispatcher.subscribe(
            DoVolumeMountEvent,
            None,
            self._mount_dispatcher.handle_volume_mount,
            name="ag.volume.mount",
        )
        event_dispatcher.subscribe(
            DoVolumeUnmountEvent,
            None,
            self._mount_dispatcher.handle_volume_umount,
            name="ag.volume.umount",
        )

    def dispatch(self, event_dispatcher: EventDispatcher) -> None:
        """
        Dispatch events to the appropriate dispatcher.
        """
        self._dispatch_agent_events(event_dispatcher)
