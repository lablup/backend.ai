from __future__ import annotations

import asyncio
import ctypes
import enum
import glob
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar

from ai.backend.common.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]

# ---------------------------------------------------------------------------
# Constants (from furiosa_smi.h)
# ---------------------------------------------------------------------------

MAX_PATH_SIZE = 256
MAX_DEVICE_FILE_SIZE = 64
MAX_CORE_STATUS_SIZE = 128
MAX_PE_SIZE = 64
MAX_DEVICE_HANDLE_SIZE = 64
MAX_CSTR_SIZE = 96

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class FuriosaSmiReturnCode(enum.IntEnum):
    OK = 0
    INVALID_ARGUMENT_ERROR = 1
    NULL_POINTER_ERROR = 2
    MAX_BUFFER_SIZE_EXCEED_ERROR = 3
    DEVICE_NOT_FOUND_ERROR = 4
    DEVICE_LOST_ERROR = 5
    DEVICE_BUSY_ERROR = 6
    IO_ERROR = 7
    PERMISSION_DENIED_ERROR = 8
    UNKNOWN_ARCH_ERROR = 9
    NOT_SUPPORTED_ARCH_ERROR = 10
    INCOMPATIBLE_DRIVER_ERROR = 11
    UNEXPECTED_VALUE_ERROR = 12
    PARSE_ERROR = 13
    UNKNOWN_ERROR = 14
    INTERNAL_ERROR = 15
    UNINITIALIZED_ERROR = 16
    CONTEXT_ERROR = 17
    NOT_SUPPORTED_ERROR = 18


class FuriosaSmiArch(enum.IntEnum):
    WARBOY = 0
    RNGD = 1
    RNGD_MAX = 2
    RNGD_S = 3


ARCH_NAMES: dict[int, str] = {
    FuriosaSmiArch.WARBOY: "WARBOY",
    FuriosaSmiArch.RNGD: "RNGD",
    FuriosaSmiArch.RNGD_MAX: "RNGD_MAX",
    FuriosaSmiArch.RNGD_S: "RNGD_S",
}


class FuriosaSmiCoreStatus(enum.IntEnum):
    AVAILABLE = 0
    OCCUPIED = 1


# ---------------------------------------------------------------------------
# ctypes struct definitions (1:1 with furiosa_smi.h)
# ---------------------------------------------------------------------------


class FuriosaSmiVersion(ctypes.Structure):
    _fields_ = [
        ("major", ctypes.c_uint32),
        ("minor", ctypes.c_uint32),
        ("patch", ctypes.c_uint32),
        ("metadata", ctypes.c_char * MAX_CSTR_SIZE),
        ("prerelease", ctypes.c_char * MAX_CSTR_SIZE),
    ]


class FuriosaSmiDeviceHandles(ctypes.Structure):
    _fields_ = [
        ("count", ctypes.c_uint32),
        ("device_handles", ctypes.c_uint32 * MAX_DEVICE_HANDLE_SIZE),
    ]


class FuriosaSmiDeviceInfo(ctypes.Structure):
    _fields_ = [
        ("index", ctypes.c_uint32),
        ("arch", ctypes.c_uint32),
        ("core_num", ctypes.c_uint32),
        ("numa_node", ctypes.c_int32),
        ("name", ctypes.c_char * MAX_CSTR_SIZE),
        ("serial", ctypes.c_char * MAX_CSTR_SIZE),
        ("uuid", ctypes.c_char * MAX_CSTR_SIZE),
        ("bdf", ctypes.c_char * MAX_CSTR_SIZE),
        ("major", ctypes.c_uint16),
        ("minor", ctypes.c_uint16),
        ("firmware_version", FuriosaSmiVersion),
    ]


class FuriosaSmiDeviceTemperature(ctypes.Structure):
    _fields_ = [
        ("soc_peak", ctypes.c_double),
        ("ambient", ctypes.c_double),
    ]


class FuriosaSmiDevicePowerConsumption(ctypes.Structure):
    _fields_ = [
        ("rms_total", ctypes.c_double),
    ]


class FuriosaSmiPePerformanceCounter(ctypes.Structure):
    _fields_ = [
        ("timestamp", ctypes.c_long),
        ("core", ctypes.c_uint32),
        ("cycle_count", ctypes.c_uint64),
        ("task_execution_cycle", ctypes.c_uint64),
    ]


class FuriosaSmiDevicePerformanceCounter(ctypes.Structure):
    _fields_ = [
        ("pe_count", ctypes.c_uint32),
        (
            "pe_performance_counters",
            FuriosaSmiPePerformanceCounter * MAX_PE_SIZE,
        ),
    ]


class FuriosaSmiMemoryBlock(ctypes.Structure):
    _fields_ = [
        ("count", ctypes.c_uint32),
        ("core", ctypes.c_uint32 * MAX_PE_SIZE),
        ("total_bytes", ctypes.c_uint64),
        ("in_use_bytes", ctypes.c_uint64),
    ]


class FuriosaSmiMemory(ctypes.Structure):
    _fields_ = [
        ("count", ctypes.c_uint32),
        ("memory", FuriosaSmiMemoryBlock * MAX_PE_SIZE),
    ]


class FuriosaSmiMemoryUtilization(ctypes.Structure):
    _fields_ = [
        ("dram", FuriosaSmiMemory),
        ("dram_shared", FuriosaSmiMemory),
        ("sram", FuriosaSmiMemory),
        ("instruction", FuriosaSmiMemory),
    ]


class FuriosaSmiPeStatus(ctypes.Structure):
    _fields_ = [
        ("core", ctypes.c_uint32),
        ("status", ctypes.c_uint32),
    ]


class FuriosaSmiCoreStatuses(ctypes.Structure):
    _fields_ = [
        ("count", ctypes.c_uint32),
        ("core_status", FuriosaSmiPeStatus * MAX_CORE_STATUS_SIZE),
    ]


class FuriosaSmiPcieLinkInfo(ctypes.Structure):
    _fields_ = [
        ("pcie_gen_status", ctypes.c_uint8),
        ("link_width_status", ctypes.c_uint32),
        ("link_speed_status", ctypes.c_double),
        ("max_link_width_capability", ctypes.c_uint32),
        ("max_link_speed_capability", ctypes.c_double),
    ]


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class LibraryError(RuntimeError):
    lib: str
    func: str
    code: int

    def __init__(self, lib: str, func: str, code: int) -> None:
        super().__init__(lib, func, code)
        self.lib = lib
        self.func = func
        self.code = code

    def __str__(self) -> str:
        return f"LibraryError: {self.lib}::{self.func}() returned error {self.code}"

    def __repr__(self) -> str:
        args = ", ".join(map(repr, self.args))
        return f"LibraryError({args})"


# ---------------------------------------------------------------------------
# ctypes FFI wrapper (_LibFuriosaSmi)
# ---------------------------------------------------------------------------

_LIB_NAME = "libfuriosa_smi"


class _LibFuriosaSmi:
    _lib: ClassVar[ctypes.CDLL | None] = None
    _initialized: ClassVar[bool] = False

    @classmethod
    def _load(cls) -> ctypes.CDLL | None:
        try:
            return ctypes.cdll.LoadLibrary("libfuriosa_smi.so")
        except OSError:
            return None

    @classmethod
    def _ensure_init(cls) -> None:
        if cls._initialized:
            return
        if cls._lib is None:
            cls._lib = cls._load()
        if cls._lib is None:
            raise LibraryError(_LIB_NAME, "load", -1)
        rc = cls._lib.furiosa_smi_init()
        if rc != FuriosaSmiReturnCode.OK:
            raise LibraryError(_LIB_NAME, "furiosa_smi_init", rc)
        cls._initialized = True

    @classmethod
    def invoke(cls, func_name: str, *args: object, check_rc: bool = True) -> int:
        cls._ensure_init()
        if cls._lib is None:
            raise LibraryError(_LIB_NAME, "invoke", -1)
        func = getattr(cls._lib, func_name)
        rc: int = func(*args)
        if check_rc and rc != FuriosaSmiReturnCode.OK:
            raise LibraryError(_LIB_NAME, func_name, rc)
        return rc

    # -- Wrapped API methods --

    @classmethod
    def get_driver_info(cls) -> FuriosaSmiVersion:
        out = FuriosaSmiVersion()
        cls.invoke("furiosa_smi_get_driver_info", ctypes.byref(out))
        return out

    @classmethod
    def get_device_handles(cls) -> FuriosaSmiDeviceHandles:
        out = FuriosaSmiDeviceHandles()
        cls.invoke("furiosa_smi_get_device_handles", ctypes.byref(out))
        return out

    @classmethod
    def get_device_info(cls, handle: int) -> FuriosaSmiDeviceInfo:
        out = FuriosaSmiDeviceInfo()
        cls.invoke(
            "furiosa_smi_get_device_info",
            ctypes.c_uint32(handle),
            ctypes.byref(out),
        )
        return out

    @classmethod
    def get_device_liveness(cls, handle: int) -> bool:
        out = ctypes.c_bool()
        cls.invoke(
            "furiosa_smi_get_device_liveness",
            ctypes.c_uint32(handle),
            ctypes.byref(out),
        )
        return out.value

    @classmethod
    def get_memory_utilization(cls, handle: int) -> FuriosaSmiMemoryUtilization:
        out = FuriosaSmiMemoryUtilization()
        cls.invoke(
            "furiosa_smi_get_memory_utilization",
            ctypes.c_uint32(handle),
            ctypes.byref(out),
        )
        return out

    @classmethod
    def get_device_performance_counter(cls, handle: int) -> FuriosaSmiDevicePerformanceCounter:
        out = FuriosaSmiDevicePerformanceCounter()
        cls.invoke(
            "furiosa_smi_get_device_performance_counter",
            ctypes.c_uint32(handle),
            ctypes.byref(out),
        )
        return out

    @classmethod
    def get_device_temperature(cls, handle: int) -> FuriosaSmiDeviceTemperature:
        out = FuriosaSmiDeviceTemperature()
        cls.invoke(
            "furiosa_smi_get_device_temperature",
            ctypes.c_uint32(handle),
            ctypes.byref(out),
        )
        return out

    @classmethod
    def get_device_power_consumption(cls, handle: int) -> FuriosaSmiDevicePowerConsumption:
        out = FuriosaSmiDevicePowerConsumption()
        cls.invoke(
            "furiosa_smi_get_device_power_consumption",
            ctypes.c_uint32(handle),
            ctypes.byref(out),
        )
        return out

    @classmethod
    def get_device_core_status(cls, handle: int) -> FuriosaSmiCoreStatuses:
        out = FuriosaSmiCoreStatuses()
        cls.invoke(
            "furiosa_smi_get_device_core_status",
            ctypes.c_uint32(handle),
            ctypes.byref(out),
        )
        return out


# ---------------------------------------------------------------------------
# sysfs helpers
# ---------------------------------------------------------------------------

_SYSFS_RNGD_MGMT = Path("/sys/class/rngd_mgmt")
_SYSFS_PCI_DEVICES = Path("/sys/bus/pci/devices")


async def _read_sysfs(path: Path) -> str:
    loop = asyncio.get_running_loop()
    return (await loop.run_in_executor(None, path.read_text)).strip()


async def _read_sysfs_int(path: Path, base: int = 10) -> int:
    text = await _read_sysfs(path)
    return int(text, base)


def _mgmt_path(idx: int) -> Path:
    return _SYSFS_RNGD_MGMT / f"rngd!npu{idx}mgmt"


def _pe_path(dev_idx: int, pe_idx: int) -> Path:
    return _SYSFS_RNGD_MGMT / f"rngd!npu{dev_idx}pe{pe_idx}"


def _parse_hex_key_value(text: str) -> dict[str, int]:
    """Parse sysfs key-value output like 'dram_capacity: 0xbc0003000'."""
    result: dict[str, int] = {}
    for line in text.strip().splitlines():
        match = re.match(r"(\w+):\s+(0x[0-9a-fA-F]+|\d+)", line.strip())
        if match:
            key = match.group(1)
            val_str = match.group(2)
            result[key] = int(val_str, 16) if val_str.startswith("0x") else int(val_str)
    return result


# ---------------------------------------------------------------------------
# Typed return dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RngdDriverInfo:
    version: str


@dataclass(frozen=True)
class RngdDeviceInfo:
    device_index: int
    arch: str
    device_uuid: str
    device_serial: str
    pci_bus_id: str
    numa_node: int
    firmware_version: str
    memory_size: int  # total bytes (dram + dram_shared)
    num_cores: int


@dataclass(frozen=True)
class RngdDeviceMetrics:
    device_index: int
    memory_used: int  # bytes
    memory_total: int  # bytes
    core_utilizations: list[float] = field(default_factory=list)  # per-core % (0-100)
    temperature_celsius: float = 0.0
    power_watts: float = 0.0


# ---------------------------------------------------------------------------
# Unified RngdAPI
# ---------------------------------------------------------------------------


def _version_str(v: FuriosaSmiVersion) -> str:
    return f"{v.major}.{v.minor}.{v.patch}"


def _compute_memory_totals(
    mem_util: FuriosaSmiMemoryUtilization,
) -> tuple[int, int]:
    """Return (total_bytes, used_bytes) aggregated from DRAM + DRAM shared."""
    total = 0
    used = 0
    # DRAM blocks
    for i in range(mem_util.dram.count):
        total += mem_util.dram.memory[i].total_bytes
        used += mem_util.dram.memory[i].in_use_bytes
    # DRAM shared blocks
    for i in range(mem_util.dram_shared.count):
        total += mem_util.dram_shared.memory[i].total_bytes
        used += mem_util.dram_shared.memory[i].in_use_bytes
    return total, used


def _compute_core_utilizations(
    perf: FuriosaSmiDevicePerformanceCounter,
) -> list[float]:
    """Compute per-core utilization % from performance counters."""
    utils: list[float] = []
    for i in range(perf.pe_count):
        counter = perf.pe_performance_counters[i]
        if counter.cycle_count > 0:
            pct = (counter.task_execution_cycle / counter.cycle_count) * 100.0
            utils.append(min(pct, 100.0))
        else:
            utils.append(0.0)
    return utils


class RngdAPI:
    _ffi_available: ClassVar[bool | None] = None

    @classmethod
    def _is_ffi_available(cls) -> bool:
        if cls._ffi_available is None:
            try:
                _LibFuriosaSmi._ensure_init()
                cls._ffi_available = True
            except (LibraryError, OSError):
                cls._ffi_available = False
        return cls._ffi_available

    # -- Driver info -------------------------------------------------------

    @classmethod
    async def get_driver_info(cls) -> RngdDriverInfo:
        loop = asyncio.get_running_loop()
        if cls._is_ffi_available():
            ver = await loop.run_in_executor(None, _LibFuriosaSmi.get_driver_info)
            return RngdDriverInfo(version=_version_str(ver))
        # sysfs fallback: read version from first device
        candidates = await loop.run_in_executor(None, glob.glob, "/dev/rngd/npu?mgmt")
        if not candidates:
            return RngdDriverInfo(version="unknown")
        version_text = await _read_sysfs(_mgmt_path(0) / "version")
        return RngdDriverInfo(version=version_text.split(",")[0].strip())

    # -- Device enumeration ------------------------------------------------

    @classmethod
    async def list_devices(cls) -> list[RngdDeviceInfo]:
        loop = asyncio.get_running_loop()
        if cls._is_ffi_available():
            return await cls._list_devices_ffi(loop)
        return await cls._list_devices_sysfs(loop)

    @classmethod
    async def _list_devices_ffi(cls, loop: asyncio.AbstractEventLoop) -> list[RngdDeviceInfo]:
        handles = await loop.run_in_executor(None, _LibFuriosaSmi.get_device_handles)
        devices: list[RngdDeviceInfo] = []
        for i in range(handles.count):
            handle = handles.device_handles[i]
            info = await loop.run_in_executor(None, _LibFuriosaSmi.get_device_info, handle)
            # Get memory size via memory utilization
            try:
                mem_util = await loop.run_in_executor(
                    None, _LibFuriosaSmi.get_memory_utilization, handle
                )
                memory_total, _ = _compute_memory_totals(mem_util)
            except LibraryError:
                memory_total = 0
            devices.append(
                RngdDeviceInfo(
                    device_index=info.index,
                    arch=ARCH_NAMES.get(info.arch, f"UNKNOWN({info.arch})"),
                    device_uuid=info.uuid.decode().strip("\x00"),
                    device_serial=info.serial.decode().strip("\x00"),
                    pci_bus_id=info.bdf.decode().strip("\x00"),
                    numa_node=info.numa_node,
                    firmware_version=_version_str(info.firmware_version),
                    memory_size=memory_total,
                    num_cores=info.core_num,
                )
            )
        return devices

    @classmethod
    async def _list_devices_sysfs(cls, loop: asyncio.AbstractEventLoop) -> list[RngdDeviceInfo]:
        candidates = await loop.run_in_executor(None, glob.glob, "/dev/rngd/npu?mgmt")
        devices: list[RngdDeviceInfo] = []
        for idx in range(len(candidates)):
            mgmt = _mgmt_path(idx)
            if not mgmt.exists():
                continue
            platform_type = await _read_sysfs(mgmt / "platform_type")
            if platform_type != "FuriosaAI":
                continue

            device_uuid = await _read_sysfs(mgmt / "device_uuid")
            device_sn = await _read_sysfs(mgmt / "device_sn")
            model = await _read_sysfs(mgmt / "device_type")
            pci_bus_id = await _read_sysfs(mgmt / "busname")
            numa_node_path = _SYSFS_PCI_DEVICES / pci_bus_id / "numa_node"
            numa_node = int(await _read_sysfs(numa_node_path))
            fw_version = await _read_sysfs(mgmt / "fw_version")

            # Count PEs by scanning sysfs entries
            pe_entries = await loop.run_in_executor(
                None,
                lambda i=idx: list(_SYSFS_RNGD_MGMT.glob(f"rngd!npu{i}pe[0-9]")),
            )
            num_cores = len(pe_entries)

            # Get memory from first PE's alloc_status
            memory_total = 0
            if num_cores > 0:
                try:
                    alloc_text = await _read_sysfs(_pe_path(idx, 0) / "alloc_status")
                    alloc = _parse_hex_key_value(alloc_text)
                    memory_total = alloc.get("dram_capacity", 0) + alloc.get("shared_capacity", 0)
                except (FileNotFoundError, ValueError):
                    pass

            devices.append(
                RngdDeviceInfo(
                    device_index=idx,
                    arch=model,
                    device_uuid=device_uuid,
                    device_serial=device_sn,
                    pci_bus_id=pci_bus_id,
                    numa_node=numa_node,
                    firmware_version=fw_version.split(",")[0].strip(),
                    memory_size=memory_total,
                    num_cores=num_cores,
                )
            )
        return devices

    # -- Device info -------------------------------------------------------

    @classmethod
    async def get_device_info(cls, device_index: int) -> RngdDeviceInfo:
        devices = await cls.list_devices()
        for dev in devices:
            if dev.device_index == device_index:
                return dev
        raise ValueError(f"RNGD device {device_index} not found")

    # -- Device metrics ----------------------------------------------------

    @classmethod
    async def get_device_metrics(cls, device_index: int) -> RngdDeviceMetrics:
        loop = asyncio.get_running_loop()
        if cls._is_ffi_available():
            return await cls._get_device_metrics_ffi(device_index, loop)
        return await cls._get_device_metrics_sysfs(device_index, loop)

    @classmethod
    async def _get_device_metrics_ffi(
        cls, device_index: int, loop: asyncio.AbstractEventLoop
    ) -> RngdDeviceMetrics:
        handles = await loop.run_in_executor(None, _LibFuriosaSmi.get_device_handles)
        handle = handles.device_handles[device_index]

        # Memory
        mem_util = await loop.run_in_executor(None, _LibFuriosaSmi.get_memory_utilization, handle)
        mem_total, mem_used = _compute_memory_totals(mem_util)

        # Utilization
        perf = await loop.run_in_executor(
            None, _LibFuriosaSmi.get_device_performance_counter, handle
        )
        core_utils = _compute_core_utilizations(perf)

        # Temperature
        try:
            temp = await loop.run_in_executor(None, _LibFuriosaSmi.get_device_temperature, handle)
            temperature = temp.soc_peak
        except LibraryError:
            temperature = 0.0

        # Power
        try:
            power = await loop.run_in_executor(
                None, _LibFuriosaSmi.get_device_power_consumption, handle
            )
            power_watts = power.rms_total
        except LibraryError:
            power_watts = 0.0

        return RngdDeviceMetrics(
            device_index=device_index,
            memory_used=mem_used,
            memory_total=mem_total,
            core_utilizations=core_utils,
            temperature_celsius=temperature,
            power_watts=power_watts,
        )

    @classmethod
    async def _get_device_metrics_sysfs(
        cls, device_index: int, loop: asyncio.AbstractEventLoop
    ) -> RngdDeviceMetrics:
        mgmt = _mgmt_path(device_index)
        if not mgmt.exists():
            raise ValueError(f"RNGD device {device_index} not found in sysfs")

        # Count PEs
        pe_entries = await loop.run_in_executor(
            None,
            lambda: sorted(_SYSFS_RNGD_MGMT.glob(f"rngd!npu{device_index}pe[0-9]")),
        )
        num_cores = len(pe_entries)

        # Memory from first PE's alloc_status (all PEs share DRAM)
        mem_total = 0
        mem_used = 0
        if num_cores > 0:
            try:
                alloc_text = await _read_sysfs(_pe_path(device_index, 0) / "alloc_status")
                alloc = _parse_hex_key_value(alloc_text)
                mem_total = alloc.get("dram_capacity", 0) + alloc.get("shared_capacity", 0)
                mem_used = alloc.get("dram_usage", 0) + alloc.get("shared_usage", 0)
            except (FileNotFoundError, ValueError):
                pass

        # Per-core utilization from PE metrics files
        core_utils: list[float] = []
        for pe_idx in range(num_cores):
            try:
                metrics_text = await _read_sysfs(_pe_path(device_index, pe_idx) / "metrics")
                metrics = _parse_hex_key_value(metrics_text)
                cycle = metrics.get("CycleCount", 0)
                task_cycle = metrics.get("TaskCycleCount", 0)
                if cycle > 0:
                    pct = (task_cycle / cycle) * 100.0
                    core_utils.append(min(pct, 100.0))
                else:
                    core_utils.append(0.0)
            except (FileNotFoundError, ValueError):
                core_utils.append(0.0)

        # Temperature and power are not available via sysfs
        return RngdDeviceMetrics(
            device_index=device_index,
            memory_used=mem_used,
            memory_total=mem_total,
            core_utilizations=core_utils,
            temperature_celsius=0.0,
            power_watts=0.0,
        )
