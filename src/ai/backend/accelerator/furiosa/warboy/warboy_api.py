import asyncio
import glob
from pathlib import Path
from typing import AsyncIterable, Mapping


class WarboyAPI:
    FURIOSA_VID = "0x1ed2"

    @classmethod
    async def is_furiosa_device(cls, idx: int) -> bool:
        platform_type_path = Path("/sys/class/npu_mgmt") / f"npu{idx}_mgmt" / "platform_type"
        if not (platform_type_path.exists() and platform_type_path.is_file()):
            return False

        contents = await asyncio.get_running_loop().run_in_executor(
            None, platform_type_path.read_text
        )
        return contents in ["FuriosaAI", "VITIS"]

    @classmethod
    async def list_devices(cls) -> AsyncIterable[Mapping[str, str]]:
        async def _read_prop(path: Path) -> str:
            return await asyncio.get_running_loop().run_in_executor(None, path.read_text)

        candidates = await asyncio.get_running_loop().run_in_executor(None, glob.glob, "/dev/npu?")
        for idx in range(len(candidates)):
            if not await cls.is_furiosa_device(idx):
                continue

            mgmt_path = Path("/sys/class/npu_mgmt") / f"npu{idx}_mgmt"
            device_uuid = await _read_prop(mgmt_path / "device_uuid")
            device_sn = await _read_prop(mgmt_path / "device_sn")
            model = await _read_prop(mgmt_path / "device_type")
            pci_bus_id = await _read_prop(mgmt_path / "busname")
            sysfs_device_path = Path("/sys/bus/pci/devices") / pci_bus_id
            numa_node = await _read_prop(sysfs_device_path / "numa_node")

            yield {
                "pci_bus_id": pci_bus_id,
                "numa_node": numa_node,
                "model": model,
                "device_sn": device_sn,
                "device_uuid": device_uuid,
            }


class LibraryError(RuntimeError):
    pass
