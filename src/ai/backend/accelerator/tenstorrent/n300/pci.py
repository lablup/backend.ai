import asyncio
from pathlib import Path


async def read_sysfs(path, attr):
    def _blocking():
        return (path / attr).read_text().strip()

    return await asyncio.get_running_loop().run_in_executor(None, _blocking)


async def lspci():
    # See https://github.com/pciutils/pciutils/blob/master/lib/sysfs.c
    sysfs_pci_path = Path("/sys/bus/pci")
    for device_path in (sysfs_pci_path / "devices").iterdir():
        device_info = {}
        device_info["slot"] = device_path.name
        device_info["vendor"] = await read_sysfs(device_path, "vendor")
        device_info["device"] = await read_sysfs(device_path, "device")
        device_info["numa_node"] = int(await read_sysfs(device_path, "numa_node"))
        yield device_info
