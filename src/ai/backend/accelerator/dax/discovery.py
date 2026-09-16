import enum
import os
import re
import stat
from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Final

from ai.backend.accelerator.dax.config import DAXPluginConfig
from ai.backend.common.types import DeviceId

DEVICE_DAX_DRIVER: Final[str] = "device_dax"
CONTAINER_DEV_DIR: Final[Path] = Path("/dev")

_rx_dax_name = re.compile(r"^dax(\d+)\.(\d+)$")
_rx_cxl_region = re.compile(r"^region\d+$")

type StatFunc = Callable[[Path], os.stat_result]


class ExcludedReason(enum.StrEnum):
    NOT_DEVICE_DAX = "not_device_dax"
    NOT_CXL = "not_cxl"
    SPLIT_REGION = "split_region"
    NO_SERIAL = "no_serial"
    NOT_ALLOWLISTED = "not_allowlisted"
    NODE_MISSING = "node_missing"
    NODE_PERMISSIONS = "node_permissions"
    HETEROGENEOUS_SIZE = "heterogeneous_size"


@dataclass(frozen=True)
class DAXDeviceInfo:
    """One dax device as read from sysfs, admitted when `excluded_reason` is None."""

    name: str
    device_id: DeviceId | None
    path: str
    size: int
    align: int
    numa_node: int
    target_node: int
    region: str
    serials: tuple[str, ...]
    driver: str | None
    gid: int | None
    excluded_reason: ExcludedReason | None


@dataclass(frozen=True)
class DiscoveryResult:
    admitted: Sequence[DAXDeviceInfo]
    excluded: Sequence[DAXDeviceInfo]


def _read_text(path: Path) -> str | None:
    try:
        return path.read_text().strip()
    except OSError:
        return None


def _read_int(path: Path, default: int) -> int:
    raw = _read_text(path)
    if raw is None:
        return default
    try:
        return int(raw, 0)
    except ValueError:
        return default


def _sort_key(entry: Path) -> tuple[int, int, str]:
    m = _rx_dax_name.match(entry.name)
    if m is None:
        return (-1, -1, entry.name)
    return (int(m.group(1)), int(m.group(2)), entry.name)


def _is_cxl_region(region_dir: Path) -> bool:
    if not _rx_cxl_region.match(region_dir.name):
        return False
    try:
        return (region_dir / "subsystem").resolve(strict=True).name == "cxl"
    except OSError:
        return False


def _count_sized_siblings(dax_region_dir: Path) -> int:
    # A zero-size seed device is not a mapping and does not split the region.
    try:
        entries = list(dax_region_dir.iterdir())
    except OSError:
        return 0
    return sum(
        1
        for entry in entries
        if _rx_dax_name.match(entry.name) and _read_int(entry / "size", 0) > 0
    )


def read_region_serials(sysfs_root: Path, region_dir: Path) -> tuple[str, ...]:
    """
    Memdev serials of a CXL region in target order:
    `regionZ/targetN` → `decoderX.Y` → `endpointX/uport` → `memN/serial`.
    """
    serials: list[str] = []
    idx = 0
    while (target_file := region_dir / f"target{idx}").exists():
        idx += 1
        decoder_name = _read_text(target_file)
        if not decoder_name:
            continue
        try:
            decoder_dir = (sysfs_root / "bus" / "cxl" / "devices" / decoder_name).resolve(
                strict=True
            )
            memdev_dir = (decoder_dir.parent / "uport").resolve(strict=True)
        except OSError:
            return ()
        serial = _read_text(memdev_dir / "serial")
        if not serial:
            return ()
        serials.append(serial)
    return tuple(serials)


def read_device(sysfs_root: Path, name: str, *, allow_non_cxl: bool) -> DAXDeviceInfo | None:
    """
    Read one dax device from sysfs with identity; node, allowlist, and size checks
    are left to `discover_devices`. Returns None if sysfs has no such device.
    """
    entry = sysfs_root / "bus" / "dax" / "devices" / name
    try:
        device_dir = entry.resolve(strict=True)
    except OSError:
        return None
    driver: str | None
    try:
        driver = (device_dir / "driver").resolve(strict=True).name
    except OSError:
        driver = None
    dax_region_dir = device_dir.parent
    region_dir = dax_region_dir.parent
    is_cxl = _is_cxl_region(region_dir)
    info = DAXDeviceInfo(
        name=name,
        device_id=None,
        path=str(CONTAINER_DEV_DIR / name),
        size=_read_int(device_dir / "size", 0),
        align=_read_int(device_dir / "align", 0),
        numa_node=_read_int(device_dir / "numa_node", -1),
        target_node=_read_int(device_dir / "target_node", -1),
        region=region_dir.name if is_cxl else dax_region_dir.name,
        serials=(),
        driver=driver,
        gid=None,
        excluded_reason=None,
    )
    if driver != DEVICE_DAX_DRIVER:
        return replace(info, excluded_reason=ExcludedReason.NOT_DEVICE_DAX)
    if not is_cxl and not allow_non_cxl:
        return replace(info, excluded_reason=ExcludedReason.NOT_CXL)
    if _count_sized_siblings(dax_region_dir) > 1:
        return replace(info, excluded_reason=ExcludedReason.SPLIT_REGION)
    if not is_cxl:
        return replace(info, device_id=DeviceId(f"dax-{name}"))
    serials = read_region_serials(sysfs_root, region_dir)
    if not serials:
        return replace(info, excluded_reason=ExcludedReason.NO_SERIAL)
    return replace(info, serials=serials, device_id=DeviceId("dax-" + "+".join(serials)))


def _check_node(dev_root: Path, info: DAXDeviceInfo, stat_func: StatFunc) -> DAXDeviceInfo:
    try:
        st = stat_func(dev_root / info.name)
    except OSError:
        return replace(info, excluded_reason=ExcludedReason.NODE_MISSING)
    group_rw = stat.S_IRGRP | stat.S_IWGRP
    if (
        not stat.S_ISCHR(st.st_mode)
        or (st.st_mode & group_rw) != group_rw
        or st.st_mode & stat.S_IWOTH
    ):
        return replace(info, excluded_reason=ExcludedReason.NODE_PERMISSIONS)
    return replace(info, gid=st.st_gid)


def discover_devices(config: DAXPluginConfig, stat_func: StatFunc = os.stat) -> DiscoveryResult:
    """Scan `/sys/bus/dax/devices` and split the devices into admitted and excluded."""
    devices_dir = config.sysfs_root / "bus" / "dax" / "devices"
    try:
        entries = sorted(devices_dir.iterdir(), key=_sort_key)
    except OSError:
        return DiscoveryResult(admitted=(), excluded=())
    allowlist = set(config.allowlist) if config.allowlist is not None else None
    candidates: list[DAXDeviceInfo] = []
    excluded: list[DAXDeviceInfo] = []
    for entry in entries:
        info = read_device(config.sysfs_root, entry.name, allow_non_cxl=config.allow_non_cxl)
        if info is None:
            continue
        if info.excluded_reason is None and allowlist is not None:
            if info.name not in allowlist and info.device_id not in allowlist:
                info = replace(info, excluded_reason=ExcludedReason.NOT_ALLOWLISTED)
        if info.excluded_reason is None and not config.mock:
            info = _check_node(config.dev_root, info, stat_func)
        if info.excluded_reason is None:
            candidates.append(info)
        else:
            excluded.append(info)
    if len({info.size for info in candidates}) > 1:
        excluded.extend(
            replace(info, excluded_reason=ExcludedReason.HETEROGENEOUS_SIZE) for info in candidates
        )
        candidates = []
    return DiscoveryResult(admitted=candidates, excluded=excluded)
