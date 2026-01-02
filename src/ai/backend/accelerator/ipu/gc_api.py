import asyncio
import json


class GraphcoreAPI:
    @classmethod
    async def get_monitor_info(cls):
        proc = await asyncio.subprocess.create_subprocess_exec(
            "/usr/bin/env",
            *["gc-monitor", "-j"],
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        out, _ = await proc.communicate()
        graphcore_info = json.loads(out.decode("utf-8"))
        return graphcore_info

    @classmethod
    async def get_poplar_version(cls):
        proc = await asyncio.subprocess.create_subprocess_exec(
            "/usr/bin/env",
            *["gc-monitor", "version"],
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        out, _ = await proc.communicate()
        return out.decode("utf-8").replace("Poplar version:", "").strip()

    @classmethod
    async def get_inventories(cls) -> list[dict[str, str]]:
        proc = await asyncio.subprocess.create_subprocess_exec(
            "/usr/bin/env",
            *["gc-inventory", "-2"],
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        out, _ = await proc.communicate()
        out_str = out.decode("utf-8")
        return json.loads(out_str)["devices"]

    @classmethod
    async def get_inventory_by_device(cls, device_id: int) -> dict[str, str]:
        result = await cls.get_inventories()
        for device in result:
            if device["id"] == str(device_id):
                return device
        raise RuntimeError(f"Device {device_id} not found")
