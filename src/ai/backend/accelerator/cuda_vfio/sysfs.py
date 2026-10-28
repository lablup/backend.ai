import logging
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from ai.backend.agent.errors.resources import ResourceError
from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))

DEFAULT_SYSFS_ROOT: Final[Path] = Path("/sys")
DEFAULT_DEV_ROOT: Final[Path] = Path("/dev")

VFIO_DRIVER: Final[str] = "vfio-pci"
NVIDIA_VENDOR_ID: Final[str] = "0x10de"
# Base class and sub-class (the 24-bit sysfs class without the prog-if byte).
# 0x0302: 3D controller, 0x0300: VGA compatible controller, 0x0604: PCI bridge
GPU_CLASSES: Final[frozenset[int]] = frozenset({0x0302, 0x0300})
PCI_BRIDGE_CLASS: Final[int] = 0x0604

# PCI device id -> (model name, memory size in bytes)
# TODO: confirm the 96 GiB size inside a TD
GPU_MODELS: Final[Mapping[str, tuple[str, int]]] = {
    "0x2bb5": ("NVIDIA RTX PRO 6000 Blackwell", 96 * 1024**3),
}


class VFIODeviceUnavailable(ResourceError):
    """Raised when the vfio device node of an allocated GPU cannot be found."""

    error_type = "https://api.backend.ai/probs/agent/vfio-device-unavailable"
    error_title = "VFIO device node is unavailable."


@dataclass(frozen=True)
class VFIOGPUInfo:
    bdf: str
    model_name: str
    memory_size: int
    numa_node: int | None
    iommu_group: int
    vfio_node: str


def _read(path: Path) -> str | None:
    try:
        return path.read_text().strip().lower()
    except OSError:
        return None


def _driver_name(pci_dir: Path) -> str | None:
    try:
        return (pci_dir / "driver").readlink().name
    except OSError:
        return None


def _pci_class(pci_dir: Path) -> int | None:
    """The base class and sub-class of the device, without the prog-if byte."""
    text = _read(pci_dir / "class")
    if text is None:
        return None
    try:
        return int(text, 16) >> 8
    except ValueError:
        return None


def _normalize_key(key: str) -> str:
    return bdf_to_device_id(key.lower().removeprefix("0x"))


def _parse_numa_node(text: str | None) -> int | None:
    if text is None:
        return None
    try:
        node = int(text)
    except ValueError:
        return None
    return node if node >= 0 else None


def _find_vfio_dev_name(pci_dir: Path) -> str | None:
    try:
        names = sorted(p.name for p in (pci_dir / "vfio-dev").glob("vfio*"))
    except OSError:
        return None
    return names[0] if names else None


def _list_group_members(sysfs_root: Path, group: str) -> list[str] | None:
    try:
        return sorted(
            p.name for p in (sysfs_root / "kernel" / "iommu_groups" / group / "devices").iterdir()
        )
    except OSError:
        return None


def _find_unisolated_member(sysfs_root: Path, members: list[str]) -> str | None:
    """The first member of the IOMMU group that is neither vfio-pci-bound nor a bridge."""
    pci_devices = sysfs_root / "bus" / "pci" / "devices"
    for member in members:
        member_dir = pci_devices / member
        if _driver_name(member_dir) == VFIO_DRIVER or _pci_class(member_dir) == PCI_BRIDGE_CLASS:
            continue
        return member
    return None


def scan_vfio_gpus(
    sysfs_root: Path,
    memory_overrides: Mapping[str, int] | None = None,
) -> list[VFIOGPUInfo]:
    """Scan the PCI bus for NVIDIA GPUs that are bound to vfio-pci and safe to pass through."""
    overrides = {_normalize_key(k): v for k, v in (memory_overrides or {}).items()}
    pci_devices = sysfs_root / "bus" / "pci" / "devices"
    gpus: list[VFIOGPUInfo] = []
    for pci_dir in sorted(pci_devices.iterdir()):
        if _read(pci_dir / "vendor") != NVIDIA_VENDOR_ID:
            continue
        if _pci_class(pci_dir) not in GPU_CLASSES:
            continue
        # A device with no driver bound is skipped as well.
        if _driver_name(pci_dir) != VFIO_DRIVER:
            continue
        bdf = pci_dir.name
        vfio_name = _find_vfio_dev_name(pci_dir)
        if vfio_name is None:
            log.warning("GPU skipped, no iommufd device node", bdf=bdf)
            continue
        try:
            group = (pci_dir / "iommu_group").readlink().name
        except OSError:
            log.warning("GPU skipped, no IOMMU group", bdf=bdf)
            continue
        members = _list_group_members(sysfs_root, group)
        if members is None:
            log.warning("GPU skipped, IOMMU group members unreadable", bdf=bdf, iommu_group=group)
            continue
        offender = _find_unisolated_member(sysfs_root, members)
        if offender is not None:
            log.warning(
                "GPU skipped, IOMMU group has a member that is neither vfio-pci nor a bridge",
                bdf=bdf,
                iommu_group=group,
                member=offender,
            )
            continue
        device_id = _read(pci_dir / "device") or ""
        model_name, memory_size = GPU_MODELS.get(device_id, (f"NVIDIA GPU [{device_id}]", 0))
        memory_size = overrides.get(
            _normalize_key(bdf), overrides.get(_normalize_key(device_id), memory_size)
        )
        gpus.append(
            VFIOGPUInfo(
                bdf=bdf,
                model_name=model_name,
                memory_size=memory_size,
                numa_node=_parse_numa_node(_read(pci_dir / "numa_node")),
                iommu_group=int(group),
                vfio_node=f"/dev/vfio/devices/{vfio_name}",
            )
        )
    return gpus


def bdf_to_device_id(bdf: str) -> str:
    """Return the colon-free device id; resource.txt splits ``id:share`` on the first colon."""
    return bdf.replace(":", "-")


def resolve_vfio_node(sysfs_root: Path, dev_root: Path, bdf: str) -> str:
    """The iommufd device node path of the GPU, resolved from sysfs at the time of the call."""
    pci_dir = sysfs_root / "bus" / "pci" / "devices" / bdf
    vfio_name = _find_vfio_dev_name(pci_dir)
    if vfio_name is None or not (dev_root / "vfio" / "devices" / vfio_name).exists():
        raise VFIODeviceUnavailable(f"No iommufd device node for the GPU {bdf}")
    return f"/dev/vfio/devices/{vfio_name}"
