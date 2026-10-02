from __future__ import annotations

import ctypes
import platform
from abc import ABCMeta, abstractmethod
from typing import Any, ClassVar, NamedTuple

# ref: https://docs.nvidia.com/cuda/cuda-driver-api/group__CUDA__DEVICE.html
CU_DEVICE_ATTRIBUTE_MULTIPROCESSOR_COUNT = 16


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


def _load_library(name: str) -> ctypes.CDLL | None:
    try:
        if platform.system() == "Windows":
            return ctypes.windll.LoadLibrary(name)  # type: ignore[attr-defined]
        return ctypes.cdll.LoadLibrary(name)
    except OSError:
        pass
    return None


class LibraryBase(metaclass=ABCMeta):
    name = "LIBRARY"

    # The class-level caches below (_lib here; _initialized/_version/_init_error
    # in subclasses) are mutated without locking. This is safe because all
    # callers run on the agent's single event-loop thread.
    _lib: ClassVar[ctypes.CDLL | None] = None

    @classmethod
    @abstractmethod
    def load_library(cls) -> ctypes.CDLL | None:
        pass

    @classmethod
    def _ensure_lib(cls) -> None:
        if cls._lib is None:
            cls._lib = cls.load_library()
        if cls._lib is None:
            raise ImportError(f"Could not load the {cls.name} library!")

    @classmethod
    def has_symbol(cls, name: str) -> bool:
        cls._ensure_lib()
        return hasattr(cls._lib, name)

    @classmethod
    def invoke(cls, func_name: str, *args: Any, check_rc: bool = True) -> int:
        cls._ensure_lib()
        func = getattr(cls._lib, func_name)
        rc = func(*args)
        if check_rc and rc != 0:
            raise LibraryError(cls.name, func_name, rc)
        return rc


class CudaDeviceProps(NamedTuple):
    name: str
    uuid: bytes | None
    total_global_mem: int
    multiprocessor_count: int
    pci_bus_id: str


class libcuda(LibraryBase):
    name = "CUDA"

    # Single-threaded caches; see the note on LibraryBase.
    _initialized: ClassVar[bool] = False
    _version: ClassVar[tuple[int, int]] = (0, 0)
    _init_error: ClassVar[LibraryError | None] = None

    @classmethod
    def load_library(cls) -> ctypes.CDLL | None:
        system_type = platform.system()
        match system_type:
            case "Windows":
                return _load_library("nvcuda.dll")
            case "Darwin":
                return _load_library("libcuda.dylib")
            case _:
                # Load only the driver SONAME (libcuda.so.1). The bare
                # libcuda.so symlink is provided by the CUDA toolkit's
                # link-time stub library, which would load successfully but
                # then fail cuInit with confusing errors.
                return _load_library("libcuda.so.1")

    @classmethod
    def ensure_init(cls) -> None:
        # A failed cuInit is sticky: retrying against a broken driver is
        # pointless and slow, so we cache the error and re-raise it as-is.
        if cls._init_error is not None:
            raise cls._init_error
        if not cls._initialized:
            try:
                cls.invoke("cuInit", 0)
            except LibraryError as e:
                cls._init_error = e
                raise
            cls._initialized = True

    @classmethod
    def get_version(cls) -> tuple[int, int]:
        # This reports the maximum CUDA version supported by the installed
        # driver, not the version of a CUDA toolkit (there is none, since we
        # no longer link against the CUDA runtime library).
        # cuDriverGetVersion is documented to be callable before cuInit, so we
        # deliberately skip ensure_init() to keep version reporting working on
        # GPU-less hosts where cuInit would fail.
        if cls._version == (0, 0):
            raw_ver = ctypes.c_int()
            cls.invoke("cuDriverGetVersion", ctypes.byref(raw_ver))
            cls._version = (raw_ver.value // 1000, (raw_ver.value % 100) // 10)
        return cls._version

    @classmethod
    def get_device_count(cls) -> int:
        cls.ensure_init()
        count = ctypes.c_int()
        cls.invoke("cuDeviceGetCount", ctypes.byref(count))
        return count.value

    @classmethod
    def get_device_props(cls, device_idx: int) -> CudaDeviceProps:
        cls.ensure_init()
        device = ctypes.c_int()
        cls.invoke("cuDeviceGet", ctypes.byref(device), device_idx)

        name_buf = (ctypes.c_char * 256)()
        cls.invoke("cuDeviceGetName", ctypes.byref(name_buf), 256, device.value)
        name = name_buf.value.decode()

        # cuDeviceGetUuid_v2 (added in CUDA 11.4) returns the MIG-instance
        # UUID when the device is a MIG instance, while the legacy
        # cuDeviceGetUuid returns the parent GPU's UUID. We deterministically
        # prefer _v2 and fall back to the legacy symbol only on drivers that
        # lack it. Both symbols may be absent on ancient drivers, in which
        # case uuid is None (plugin.py falls back to an all-zero UUID).
        device_uuid: bytes | None = None
        uuid_buf = (ctypes.c_byte * 16)()
        if cls.has_symbol("cuDeviceGetUuid_v2"):
            cls.invoke("cuDeviceGetUuid_v2", ctypes.byref(uuid_buf), device.value)
            device_uuid = bytes(uuid_buf)
        elif cls.has_symbol("cuDeviceGetUuid"):
            cls.invoke("cuDeviceGetUuid", ctypes.byref(uuid_buf), device.value)
            device_uuid = bytes(uuid_buf)

        # cuDeviceTotalMem_v2 exists in every supported driver (CUDA >= 3.2);
        # the legacy cuDeviceTotalMem uses the old 32-bit ABI and would
        # truncate sizes above 4 GiB, so we never fall back to it.
        total_mem = ctypes.c_size_t()
        cls.invoke("cuDeviceTotalMem_v2", ctypes.byref(total_mem), device.value)

        mp_count = ctypes.c_int()
        cls.invoke(
            "cuDeviceGetAttribute",
            ctypes.byref(mp_count),
            CU_DEVICE_ATTRIBUTE_MULTIPROCESSOR_COUNT,
            device.value,
        )

        pci_bus_id = (ctypes.c_char * 16)()
        cls.invoke("cuDeviceGetPCIBusId", ctypes.byref(pci_bus_id), 16, device.value)

        return CudaDeviceProps(
            name=name,
            uuid=device_uuid,
            total_global_mem=total_mem.value,
            multiprocessor_count=mp_count.value,
            pci_bus_id=pci_bus_id.value.decode(),
        )


class nvmlMemoryInfo_t(ctypes.Structure):
    _fields_ = [
        ("total", ctypes.c_ulonglong),
        ("free", ctypes.c_ulonglong),
        ("used", ctypes.c_ulonglong),
    ]


class nvmlUtilization_t(ctypes.Structure):
    _fields_ = [
        ("gpu", ctypes.c_uint),  # percent of unit time for GPU core used
        ("memory", ctypes.c_uint),  # percent of unit time for GPU memory I/O
    ]


class nvmlProcessInfo_t(ctypes.Structure):
    _fields_ = [
        ("pid", ctypes.c_int),
        ("used_gpu_memory", ctypes.c_ulonglong),
    ]


NVML_INIT_FLAG_NO_GPUS = 1  # allow init without GPUs
NVML_INIT_FLAG_NO_ATTACH = 2  # do not attach the GPUs on init


class DeviceStat(NamedTuple):
    device_idx: int
    mem_total: int
    mem_used: int
    mem_free: int
    gpu_util: int
    mem_util: int


class libnvml(LibraryBase):
    name = "NVML"

    # Single-threaded cache; see the note on LibraryBase.
    _initialized: ClassVar[bool] = False

    @classmethod
    def load_library(cls) -> ctypes.CDLL | None:
        system_type = platform.system()
        if system_type == "Windows":
            return _load_library("libnvidia-ml.dll")
        if system_type == "Darwin":
            return _load_library("libnvidia-ml.dylib")
        lib = _load_library("libnvidia-ml.so")
        if lib is None:
            lib = _load_library("libnvidia-ml.so.1")
        return lib

    @classmethod
    def ensure_init(cls) -> None:
        if not cls._initialized:
            cls.invoke("nvmlInit", NVML_INIT_FLAG_NO_GPUS)
            cls._initialized = True

    @classmethod
    def shutdown(cls) -> None:
        if cls._initialized:
            cls.invoke("nvmlShutdown")

    @classmethod
    def get_driver_version(cls) -> str:
        cls.ensure_init()
        buffer = (ctypes.c_char * 80)()
        cls.invoke("nvmlSystemGetDriverVersion", ctypes.byref(buffer), 80)
        return buffer.value.decode()

    @classmethod
    def get_version(cls) -> str:
        cls.ensure_init()
        buffer = (ctypes.c_char * 80)()
        cls.invoke("nvmlSystemGetNVMLVersion", ctypes.byref(buffer), 80)
        return buffer.value.decode()

    @classmethod
    def get_device_count(cls) -> int:
        cls.ensure_init()
        count = ctypes.c_uint()
        cls.invoke("nvmlDeviceGetCount", ctypes.byref(count))
        return count.value

    @classmethod
    def get_device_stats(cls, device_idx: int) -> DeviceStat:
        """
        Returns the current usage information of the given CUDA device.
        """
        cls.ensure_init()
        handle = ctypes.c_void_p()
        mem_info = nvmlMemoryInfo_t()
        util_info = nvmlUtilization_t()
        cls.invoke("nvmlDeviceGetHandleByIndex_v2", device_idx, ctypes.byref(handle))
        cls.invoke("nvmlDeviceGetMemoryInfo", handle, ctypes.byref(mem_info))
        cls.invoke("nvmlDeviceGetUtilizationRates", handle, ctypes.byref(util_info))
        return DeviceStat(
            device_idx=device_idx,
            mem_total=mem_info.total,
            mem_used=mem_info.used,
            mem_free=mem_info.free,
            gpu_util=util_info.gpu,
            mem_util=util_info.memory,
        )
