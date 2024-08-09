from __future__ import annotations

import asyncio
import contextlib
import logging
import re
from typing import FrozenSet

from ai.backend.common.logging_utils import BraceStyleAdapter
from ai.backend.common.types import HardwareMetadata

from ..abc import CAP_FAST_FS_SIZE, CAP_FAST_SCAN, CAP_METRIC, CAP_VFOLDER, AbstractFSOpModel
from ..types import CapacityUsage, FSPerfMetric
from ..vfs import BaseVolume
from .purity import PurityClient
from .rapidfiles import RapidFileToolsFSOpModel
from .rapidfiles_v2 import RapidFileToolsv2FSOpModel

FLASHBLADE_TOOLKIT_V2_VERSION_RE = re.compile(r"version p[a-zA-Z\d]+ \(RapidFile\) (2\..+)")
FLASHBLADE_TOOLKIT_V1_VERSION_RE = re.compile(r"p[a-zA-Z\d]+ \(RapidFile Toolkit\) (1\..+)")

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


class FlashBladeVolume(BaseVolume):
    name = "purestorage"
    _toolkit_version: int | None

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self._toolkit_version = None

    async def create_fsop_model(self) -> AbstractFSOpModel:
        if (await self.get_toolkit_version()) == 2:
            return RapidFileToolsv2FSOpModel(
                self.mount_path,
                self.local_config["storage-proxy"]["scandir-limit"],
            )
        else:
            return RapidFileToolsFSOpModel(
                self.mount_path,
                self.local_config["storage-proxy"]["scandir-limit"],
            )

    async def get_toolkit_version(self) -> int:
        if self._toolkit_version is not None:
            return self._toolkit_version
        try:
            proc = await asyncio.create_subprocess_exec(
                b"pdu",
                b"--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
        except FileNotFoundError:
            self._toolkit_version = -1
            return -1
        try:
            stdout, stderr = await proc.communicate()
            if proc.returncode != 0:
                self._toolkit_version = -1
            else:
                version_line = stdout.decode().splitlines()[0]
                if FLASHBLADE_TOOLKIT_V2_VERSION_RE.match(version_line):
                    self._toolkit_version = 2
                    log.info("FlashBlade Toolkit 2 detected")
                elif FLASHBLADE_TOOLKIT_V1_VERSION_RE.match(version_line):
                    self._toolkit_version = 1
                    log.info("FlashBlade Toolkit 1 detected")
                else:
                    log.warn("Unrecogized FlashBlade Toolkit version: {}", version_line)
                    self._toolkit_version = -1
        finally:
            await proc.wait()
            assert self._toolkit_version
            return self._toolkit_version

    async def init(self) -> None:
        toolkit_version = await self.get_toolkit_version()
        if toolkit_version == -1:
            raise RuntimeError(
                "PureStorage RapidFile Toolkit is not installed. "
                "You cannot use the PureStorage backend for the stroage proxy.",
            )
        self.purity_client = PurityClient(
            self.config["purity_endpoint"],
            self.config["purity_api_token"],
            api_version=self.config["purity_api_version"],
        )
        await super().init()

    async def shutdown(self) -> None:
        await self.purity_client.aclose()

    async def get_capabilities(self) -> FrozenSet[str]:
        return frozenset(
            [
                CAP_FAST_FS_SIZE,
                CAP_VFOLDER,
                CAP_METRIC,
                CAP_FAST_SCAN,
            ],
        )

    async def get_hwinfo(self) -> HardwareMetadata:
        async with self.purity_client as client:
            metadata = await client.get_metadata()
        return {
            "status": "healthy",
            "status_info": None,
            "metadata": {
                **metadata,
            },
        }

    async def get_fs_usage(self) -> CapacityUsage:
        async with self.purity_client as client:
            usage = await client.get_usage(self.config["purity_fs_name"])
        return CapacityUsage(
            capacity_bytes=usage["capacity_bytes"],
            used_bytes=usage["used_bytes"],
        )

    async def get_performance_metric(self) -> FSPerfMetric:
        async with self.purity_client as client:
            async with contextlib.aclosing(
                client.get_nfs_metric(self.config["purity_fs_name"]),
            ) as items:
                async for item in items:
                    return FSPerfMetric(
                        iops_read=item["reads_per_sec"],
                        iops_write=item["writes_per_sec"],
                        io_bytes_read=item["read_bytes_per_sec"],
                        io_bytes_write=item["write_bytes_per_sec"],
                        io_usec_read=item["usec_per_read_op"],
                        io_usec_write=item["usec_per_write_op"],
                    )
                else:
                    raise RuntimeError(
                        "no metric found for the configured flashblade filesystem",
                    )
