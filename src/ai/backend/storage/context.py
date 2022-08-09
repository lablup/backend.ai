from __future__ import annotations

from contextlib import asynccontextmanager as actxmgr
from pathlib import Path, PurePosixPath
from typing import Any, AsyncIterator, Mapping, Type

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.storage.weka import WekaVolume

from .abc import AbstractVolume
from .exception import InvalidVolumeError
from .netapp import NetAppVolume
from .purestorage import FlashBladeVolume
from .types import VolumeInfo
from .vfs import BaseVolume
from .xfs import XfsVolume

BACKENDS: Mapping[str, Type[AbstractVolume]] = {
    "purestorage": FlashBladeVolume,
    "vfs": BaseVolume,
    "xfs": XfsVolume,
    "netapp": NetAppVolume,
    "weka": WekaVolume,
}


class Context:

    __slots__ = ("pid", "etcd", "local_config")

    pid: int
    etcd: AsyncEtcd
    local_config: Mapping[str, Any]

    def __init__(
        self,
        pid: int,
        local_config: Mapping[str, Any],
        etcd: AsyncEtcd,
    ) -> None:
        self.pid = pid
        self.etcd = etcd
        self.local_config = local_config

    def list_volumes(self) -> Mapping[str, VolumeInfo]:
        return {name: VolumeInfo(**info) for name, info in self.local_config["volume"].items()}

    @actxmgr
    async def get_volume(self, name: str) -> AsyncIterator[AbstractVolume]:
        try:
            volume_config = self.local_config["volume"][name]
        except KeyError:
            raise InvalidVolumeError(name)
        volume_cls: Type[AbstractVolume] = BACKENDS[volume_config["backend"]]
        volume_obj = volume_cls(
            local_config=self.local_config,
            mount_path=Path(volume_config["path"]),
            fsprefix=PurePosixPath(volume_config["fsprefix"]),
            options=volume_config["options"] or {},
        )
        await volume_obj.init()
        try:
            yield volume_obj
        finally:
            await volume_obj.shutdown()
