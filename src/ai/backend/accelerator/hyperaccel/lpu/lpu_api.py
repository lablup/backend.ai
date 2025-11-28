from pathlib import Path
from typing import List

from ai.backend.common.types import DeviceId

from .types import LPUDevice
from .utils import blocking_job


async def list_devices() -> List[LPUDevice]:
    devices: List[LPUDevice] = []
    xclmgmt_path = Path("/sys/bus/pci/drivers/xclmgmt")
    folders = await blocking_job(
        lambda: sorted(
            [x for x in xclmgmt_path.iterdir() if x.name.startswith("0000:")],
        ),
    )

    for idx, folder in zip(range(len(folders)), folders):
        domain, bus, slot_func = folder.name.split(":")[:3]
        slot, func = slot_func.split(".")[:2]
        display_driver_path = (folder / ".." / f"{domain}:{bus}:{slot}.1").resolve()
        renderD_files = await blocking_job(
            lambda: [
                x for x in (display_driver_path / "drm").iterdir() if x.name.startswith("renderD")
            ],
        )
        assert len(renderD_files) == 1, (
            f'no renderD file found under {display_driver_path.as_posix()}/"drm"!'
        )
        renderD_filename = renderD_files[0].name
        devices.append(
            LPUDevice(
                device_id=DeviceId(str(idx)),
                hw_location=f"{domain}:{bus}:{slot}.1",
                memory_size=0,
                processing_units=0,
                model_name="Hyperaccel LPU",
                device_number=idx,
                xvc_pri_path=Path(f"/dev/xfpga/xvc_pri.m{int(bus + slot, 16)}.0"),
                renderD_path=Path(f"/dev/dri/{renderD_filename}"),
            ),
        )

    return devices
