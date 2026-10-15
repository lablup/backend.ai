import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path

from dataclasses_json import DataClassJsonMixin

from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))


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
    devices: list[ATOMDeviceStat]
    contexts: list[ATOMContext] | None = None


class ATOMAPI:
    @classmethod
    def _tool_name(cls, exec_path: str) -> str:
        return Path(exec_path).name

    @classmethod
    def _stat_args(cls, exec_path: str) -> list[str]:
        # TODO(rebel100): confirm the `rbln-smi` JSON flags on the node (checklist step 5);
        # `-g -j` is the `rbln-stat` form, `-j` assumed to include group info for `rbln-smi`.
        if cls._tool_name(exec_path).startswith("rbln-smi"):
            return ["-j"]
        return ["-g", "-j"]

    @classmethod
    async def _run(cls, exec_path: str, args: list[str]) -> bytes:
        """
        Runs the tool and returns stdout. Stderr output alone is not an error
        (the tools print warnings there); a non-zero exit code is.
        """
        result = await asyncio.create_subprocess_exec(
            exec_path,
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        out, err = await result.communicate()
        if result.returncode:
            raise LibraryError(
                f"Error while executing {cls._tool_name(exec_path)} {' '.join(args)}"
                f" (exit code {result.returncode}): {err.decode('utf-8')}"
            )
        if err:
            log.warning(
                "rbln tool wrote to stderr",
                tool=cls._tool_name(exec_path),
                stderr=err.decode("utf-8", errors="replace"),
            )
        return out

    @classmethod
    async def get_stats(cls, exec_path: str) -> ATOMStat:
        out = await cls._run(exec_path, cls._stat_args(exec_path))
        return ATOMStat.from_json(out.decode("utf-8"))

    @classmethod
    async def list_devices(cls, exec_path: str) -> list[ATOMDeviceStat]:
        return (await cls.get_stats(exec_path)).devices

    @classmethod
    async def create_group(cls, exec_path: str, member_indexes: list[int]) -> int:
        """
        Creates new NPU group (RSD) and returns the group index
        """
        if len(member_indexes) == 0:
            raise LibraryError("Group member not specified")

        stats = await cls.get_stats(exec_path)
        groups = {int(d.group_id) for d in stats.devices}
        new_group_id = -1
        for i in range(1, 256):
            if i not in groups:
                new_group_id = i
                break
        else:
            raise LibraryError("Failed to create group: Group ID pool empty")

        # TODO(rebel100): confirm `rbln-smi group` syntax on the node (checklist step 8, 15).
        args = ["group", "-c", str(new_group_id), "-a", ",".join([str(x) for x in member_indexes])]
        await cls._run(exec_path, args)
        return new_group_id

    @classmethod
    async def destroy_groups(cls, exec_path: str, group_ids: list[int]) -> None:
        if len(group_ids) == 0:
            return
        args = ["group", "-d", ",".join([str(x) for x in group_ids])]
        await cls._run(exec_path, args)


class LibraryError(RuntimeError):
    pass
