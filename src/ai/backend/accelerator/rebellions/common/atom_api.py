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
    group_id: str
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
            "-g",
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

    @classmethod
    async def create_group(cls, exec_path: str, member_indexes: List[int]) -> int:
        """
        Creates new NPU group (RSD) and returns the group index
        """
        if len(member_indexes) == 0:
            raise LibraryError("Group member not specified")

        stats = await cls.get_stats(exec_path)
        groups = set([int(d.group_id) for d in stats.devices])
        new_group_id = -1
        for i in range(1, 256):
            if i not in groups:
                new_group_id = i
                break
        else:
            raise LibraryError("Failed to create group: Group ID pool empty")

        args = ["group", "-c", str(new_group_id), "-a", ",".join([str(x) for x in member_indexes])]
        result = await asyncio.create_subprocess_exec(
            exec_path,
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        out, err = await result.communicate()
        if len(err) > 0:
            raise LibraryError(
                f"Error while executing rbln-stat {' '.join(args)}: {err.decode('utf-8')}"
            )

        return new_group_id

    @classmethod
    async def destroy_groups(cls, exec_path: str, group_ids: List[int]) -> None:
        if len(group_ids) == 0:
            return
        args = ["group", "-d", ",".join([str(x) for x in group_ids])]
        result = await asyncio.create_subprocess_exec(
            exec_path,
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        out, err = await result.communicate()
        if len(err) > 0:
            raise LibraryError(
                f"Error while executing rbln-stat {' '.join(args)}: {err.decode('utf-8')}"
            )


class LibraryError(RuntimeError):
    pass
