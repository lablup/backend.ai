import asyncio
from dataclasses import dataclass
from typing import List, Optional

from dataclasses_json import DataClassJsonMixin


@dataclass
class ATOMStatMemory(DataClassJsonMixin):
    used: str
    total: str


@dataclass
class ATOMDevicePCIInfo(DataClassJsonMixin):
    bus_id: str
    numa_node: int
    link_speed: str
    link_width: str


@dataclass
class ATOMDeviceStat(DataClassJsonMixin):
    npu: int
    name: str
    sid: str | None
    uuid: str
    device: str
    pci: ATOMDevicePCIInfo
    temperature: str
    memory: ATOMStatMemory
    util: str


@dataclass
class ATOMContextJobCount(DataClassJsonMixin):
    done: str
    submitted: str
    requested: str


@dataclass
class ATOMContext(DataClassJsonMixin):
    ctx_id: str
    npu: int
    process: str
    pid: str
    priority: str
    ptid: str
    memalloc: str
    status: str


@dataclass
class ATOMStat(DataClassJsonMixin):
    KMD_version: str
    devices: List[ATOMDeviceStat]
    contexts: Optional[List[ATOMContext]] = None


class ATOMAPI:
    @classmethod
    async def get_stats(cls, exec_path: str) -> ATOMStat:
        result = await asyncio.create_subprocess_exec(
            exec_path,
            "-j",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        out, err = await result.communicate()
        if len(err) > 0:
            raise LibraryError(f"Error while executing rbln-stat -j: {err.decode('utf-8')}")
        return ATOMStat.from_json(out.decode("utf-8"))

    @classmethod
    async def list_devices(cls, exec_path: str) -> List[ATOMDeviceStat]:
        return (await cls.get_stats(exec_path)).devices


class LibraryError(RuntimeError):
    pass
