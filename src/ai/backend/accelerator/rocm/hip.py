import ctypes
import logging
import platform
from abc import ABCMeta, abstractmethod
from typing import Any, MutableMapping, Tuple

from ai.backend.common.logging import BraceStyleAdapter

from .exception import LibraryError

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class hipDeviceArch_t(ctypes.Structure):
    _fields_ = [
        ("hasGlobalInt32Atomics", ctypes.c_uint, 1),
        ("hasGlobalFloatAtomicExch", ctypes.c_uint, 1),
        ("hasSharedInt32Atomics", ctypes.c_uint, 1),
        ("hasSharedFloatAtomicExch", ctypes.c_uint, 1),
        ("hasFloatAtomicAdd", ctypes.c_uint, 1),
        ("hasGlobalInt64Atomics", ctypes.c_uint, 1),
        ("hasSharedInt64Atomics", ctypes.c_uint, 1),
        ("hasDoubles", ctypes.c_uint, 1),
        ("hasWarpVote", ctypes.c_uint, 1),
        ("hasWarpBallot", ctypes.c_uint, 1),
        ("hasWarpShuffle", ctypes.c_uint, 1),
        ("hasFunnelShift", ctypes.c_uint, 1),
        ("hasThreadFenceSystem", ctypes.c_uint, 1),
        ("hasSyncThreadsExt", ctypes.c_uint, 1),
        ("hasSurfaceFuncs", ctypes.c_uint, 1),
        ("has3dGrid", ctypes.c_uint, 1),
        ("hasDynamicParallelism", ctypes.c_uint, 1),
    ]


class hipUUID_t(ctypes.Structure):
    _fields_ = [("bytes", ctypes.c_char * 16)]


class hipDeviceProp(ctypes.Structure):
    _fields_ = [
        ("name", ctypes.c_char * 256),
        ("uuid", hipUUID_t),
        ("luid", ctypes.c_char * 8),
        ("luidDeviceNodeMask", ctypes.c_uint),
        ("totalGlobalMem", ctypes.c_size_t),
        ("sharedMemPerBlock", ctypes.c_size_t),
        ("regsPerBlock", ctypes.c_int),
        ("warpSize", ctypes.c_int),
        ("memPitch", ctypes.c_size_t),
        ("maxThreadsPerBlock", ctypes.c_int),
        ("maxThreadsDim", ctypes.c_int * 3),
        ("maxGridSize", ctypes.c_int * 3),
        ("clockRate", ctypes.c_int),
        ("totalConstMem", ctypes.c_size_t),
        ("major", ctypes.c_int),
        ("minor", ctypes.c_int),
        ("textureAlignment", ctypes.c_size_t),
        ("texturePitchAlignment", ctypes.c_size_t),
        ("deviceOverlap", ctypes.c_int),
        ("multiProcessorCount", ctypes.c_int),
        ("kernelExecTimeoutEnabled", ctypes.c_int),
        ("integrated", ctypes.c_int),
        ("canMapHostMemory", ctypes.c_int),
        ("computeMode", ctypes.c_int),
        ("maxTexture1D", ctypes.c_int),
        ("maxTexture1DMipmap", ctypes.c_int),
        ("maxTexture1DLinear", ctypes.c_int),
        ("maxTexture2D", ctypes.c_int * 2),
        ("maxTexture2DMipmap", ctypes.c_int * 2),
        ("maxTexture2DLinear", ctypes.c_int * 3),
        ("maxTexture2DGather", ctypes.c_int * 2),
        ("maxTexture3D", ctypes.c_int * 3),
        ("maxTexture3DAlt", ctypes.c_int * 3),
        ("maxTextureCubemap", ctypes.c_int),
        ("maxTexture1DLayered", ctypes.c_int * 2),
        ("maxTexture2DLayered", ctypes.c_int * 3),
        ("maxTextureCubemapLayered", ctypes.c_int * 2),
        ("maxSurface1D", ctypes.c_int),
        ("maxSurface2D", ctypes.c_int * 2),
        ("maxSurface3D", ctypes.c_int * 3),
        ("maxSurface1DLayered", ctypes.c_int * 2),
        ("maxSurface2DLayered", ctypes.c_int * 3),
        ("maxSurfaceCubemap", ctypes.c_int),
        ("maxSurfaceCubemapLayered", ctypes.c_int * 2),
        ("surfaceAlignment", ctypes.c_size_t),
        ("concurrentKernels", ctypes.c_int),
        ("ECCEnabled", ctypes.c_int),
        ("pciBusID", ctypes.c_int),
        ("pciDeviceID", ctypes.c_int),
        ("pciDomainID", ctypes.c_int),
        ("tccDriver", ctypes.c_int),
        ("asyncEngineCount", ctypes.c_int),
        ("unifiedAddressing", ctypes.c_int),
        ("memoryClockRate", ctypes.c_int),
        ("memoryBusWidth", ctypes.c_int),
        ("l2CacheSize", ctypes.c_int),
        ("persistingL2CacheMaxSize", ctypes.c_int),
        ("maxThreadsPerMultiProcessor", ctypes.c_int),
        ("streamPrioritiesSupported", ctypes.c_int),
        ("globalL1CacheSupported", ctypes.c_int),
        ("localL1CacheSupported", ctypes.c_int),
        ("sharedMemPerMultiprocessor", ctypes.c_size_t),
        ("regsPerMultiprocessor", ctypes.c_int),
        ("managedMemory", ctypes.c_int),
        ("isMultiGpuBoard", ctypes.c_int),
        ("multiGpuBoardGroupID", ctypes.c_int),
        ("hostNativeAtomicSupported", ctypes.c_int),
        ("singleToDoublePrecisionPerfRatio", ctypes.c_int),
        ("pageableMemoryAccess", ctypes.c_int),
        ("concurrentManagedAccess", ctypes.c_int),
        ("computePreemptionSupported", ctypes.c_int),
        ("canUseHostPointerForRegisteredMem", ctypes.c_int),
        ("cooperativeLaunch", ctypes.c_int),
        ("cooperativeMultiDeviceLaunch", ctypes.c_int),
        ("sharedMemPerBlockOptin", ctypes.c_size_t),
        ("pageableMemoryAccessUsesHostPageTables", ctypes.c_int),
        ("directManagedMemAccessFromHost", ctypes.c_int),
        ("maxBlocksPerMultiProcessor", ctypes.c_int),
        ("accessPolicyMaxWindowSize", ctypes.c_int),
        ("reservedSharedMemPerBlock", ctypes.c_size_t),
        ("hostRegisterSupported", ctypes.c_int),
        ("sparseHipArraySupported", ctypes.c_int),
        ("hostRegisterReadOnlySupported", ctypes.c_int),
        ("timelineSemaphoreInteropSupported", ctypes.c_int),
        ("memoryPoolsSupported", ctypes.c_int),
        ("gpuDirectRDMASupported", ctypes.c_int),
        ("gpuDirectRDMAFlushWritesOptions", ctypes.c_uint),
        ("gpuDirectRDMAWritesOrdering", ctypes.c_int),
        ("memoryPoolSupportedHandleTypes", ctypes.c_uint),
        ("deferredMappingHipArraySupported", ctypes.c_int),
        ("ipcEventSupported", ctypes.c_int),
        ("clusterLaunch", ctypes.c_int),
        ("unifiedFunctionPointers", ctypes.c_int),
        ("reserved", ctypes.c_int * 63),
        ("hipReserved", ctypes.c_int * 32),
        ("gcnArchName", ctypes.c_char * 256),
        ("maxSharedMemoryPerMultiProcessor", ctypes.c_size_t),
        ("clockInstructionRate", ctypes.c_int),
        ("arch", hipDeviceArch_t),
        ("hdpMemFlushCntl", ctypes.POINTER(ctypes.c_uint)),
        ("hdpRegFlushCntl", ctypes.POINTER(ctypes.c_uint)),
        ("cooperativeMultiDeviceUnmatchedFunc", ctypes.c_int),
        ("cooperativeMultiDeviceUnmatchedGridDim", ctypes.c_int),
        ("cooperativeMultiDeviceUnmatchedBlockDim", ctypes.c_int),
        ("cooperativeMultiDeviceUnmatchedSharedMem", ctypes.c_int),
        ("isLargeBar", ctypes.c_int),
        ("asicRevision", ctypes.c_int),
    ]


class rsmiVersionProp(ctypes.Structure):
    _fields_ = [
        ("major", ctypes.c_uint32),
        ("minor", ctypes.c_uint32),
        ("patch", ctypes.c_uint32),
        ("build", ctypes.c_char_p),
    ]


def _load_library(name):
    try:
        if platform.system() == "Windows":
            return ctypes.windll.LoadLibrary(name)
        else:
            return ctypes.cdll.LoadLibrary(name)
    except OSError:
        pass
    return None


class LibraryBase(metaclass=ABCMeta):
    name = "LIBRARY"

    _lib = None

    @classmethod
    @abstractmethod
    def load_library(cls) -> ctypes.CDLL:
        pass

    @classmethod
    def _ensure_lib(cls):
        if cls._lib is None:
            cls._lib = cls.load_library()
        if cls._lib is None:
            raise ImportError(f"Could not load the {cls.name} library!")

    @classmethod
    def invoke(cls, func_name, *args, check_rc=True):
        try:
            cls._ensure_lib()
        except ImportError:
            raise
        func = getattr(cls._lib, func_name)
        rc = func(*args)
        if check_rc and rc != 0:
            raise LibraryError(cls.name, func_name, rc)
        return rc


class libhip(LibraryBase):
    name = "HIP"

    _runtime_version = (0, 0)
    _driver_version = (0, 0)

    @classmethod
    def load_library(cls):
        system_type = platform.system()
        if system_type == "Linux":
            for candidate in [
                "libamdhip64.so",
                "libhip_acc.so",
                "/opt/rocm/lib/libamdhip64.so",
                "libhip_acc.so",
            ]:
                _dll = _load_library(candidate)
                if _dll:
                    return _dll
            return None
        else:
            raise NotImplementedError()

    @classmethod
    def get_version(cls) -> Tuple[int, int]:
        if cls._runtime_version == (0, 0):
            raw_ver = ctypes.c_int()
            cls.invoke("hipRuntimeGetVersion", ctypes.byref(raw_ver))
            log.debug("HIP runtime version: {}", raw_ver.value)
            cls._runtime_version = (raw_ver.value // 1000, (raw_ver.value % 100) // 10)
        return cls._runtime_version

    @classmethod
    def get_driver_version(cls) -> Tuple[int, int]:
        if cls._driver_version == (0, 0):
            raw_ver = ctypes.c_int()
            cls.invoke("hipDriverGetVersion", ctypes.byref(raw_ver))
            cls._driver_version = (raw_ver.value // 1000, (raw_ver.value % 100) // 10)
        return cls._driver_version

    @classmethod
    def get_device_count(cls) -> int:
        count = ctypes.c_int()
        cls.invoke("hipGetDeviceCount", ctypes.byref(count))
        return count.value

    @classmethod
    def get_device_props(cls, device_idx: int):
        props_struct = hipDeviceProp()
        cls.invoke("hipGetDeviceProperties", ctypes.byref(props_struct), device_idx)
        props: MutableMapping[str, Any] = {
            field[0]: getattr(props_struct, field[0]) for field in hipDeviceProp._fields_
        }
        pci_bus_id = b" " * 16
        cls.invoke(
            "hipDeviceGetPCIBusId",
            ctypes.c_char_p(pci_bus_id),
            16,
            device_idx,
        )
        props["name"] = props["name"].decode()
        props["pciBusID_str"] = pci_bus_id.split(b"\x00")[0].decode()
        return props


class librocm_smi(LibraryBase):
    """
    To backport new API from rocm-smi command check out implementations of /opt/rocm/bin/rocm-smi for details.
    """

    name = "ROCm-SMI"
    _version = (0, 0, 0)

    @classmethod
    def load_library(cls):
        system_type = platform.system()
        if system_type == "Linux":
            for candidate in ["librocm_smi64.so", "/opt/rocm/lib/librocm_smi64.so"]:
                _dll = _load_library(candidate)
                if _dll:
                    return _dll
            return None
        else:
            raise NotImplementedError()

    @classmethod
    def get_version(cls) -> Tuple[int, int, int]:
        if cls._version == (0, 0, 0):
            ver_struct = rsmiVersionProp()
            cls.invoke("rsmi_version_get", ctypes.byref(ver_struct))
            cls._version = (ver_struct.major, ver_struct.minor, ver_struct.patch)
        return cls._version

    @classmethod
    def init(cls):
        return_code = cls.invoke("rsmi_init", 0)
        if return_code != 0:
            raise RuntimeError(f"Error while initializing ROCm-SMI: {return_code}")

    @classmethod
    def shutdown(cls):
        return_code = cls.invoke("rsmi_shut_down")
        if return_code != 0:
            raise RuntimeError(f"Error while shutting down ROCm-SMI: {return_code}")

    @classmethod
    def get_serial_number(cls, device_idx: int) -> str:
        sbuf = (ctypes.c_char * 256)()
        ret = cls.invoke("rsmi_dev_serial_number_get", device_idx, sbuf, 256)
        if ret != 0:
            raise RuntimeError(
                f"get_serial_number({device_idx}): error while executing"
                f" rsmi_dev_serial_number_get(): unexpected exit code: {ret}"
            )
        return sbuf.value.decode()

    @classmethod
    def get_memory_info(cls, device_idx: int) -> tuple[int, int]:
        memory_used = ctypes.c_uint64()
        memory_total = ctypes.c_uint64()

        ret = cls.invoke("rsmi_dev_memory_usage_get", device_idx, 0, ctypes.byref(memory_used))
        if ret != 0:
            raise RuntimeError(
                f"get_memory_info({device_idx}): error while executing rsmi_dev_memory_usage_get():"
                f" unexpected exit code: {ret}"
            )

        ret = cls.invoke("rsmi_dev_memory_total_get", device_idx, 0, ctypes.byref(memory_total))
        if ret != 0:
            raise RuntimeError(
                f"get_memory_info({device_idx}): error while executing rsmi_dev_memory_total_get():"
                f" unexpected exit code: {ret}"
            )

        return (memory_used.value, memory_total.value)

    @classmethod
    def get_gpu_utilization(cls, device_idx: int) -> int:
        percent = ctypes.c_uint32()
        ret = cls.invoke("rsmi_dev_busy_percent_get", device_idx, ctypes.byref(percent))
        if ret != 0:
            raise RuntimeError(
                f"get_gpu_utilization({device_idx}): error while executing"
                f" rsmi_dev_busy_percent_get(): unexpected exit code: {ret}"
            )

        return percent.value

    @classmethod
    def get_gpu_vbios_version(cls, device_idx: int) -> str:
        vbios_ptr = (ctypes.c_char * 256)()
        ret = cls.invoke("rsmi_dev_vbios_version_get", device_idx, vbios_ptr, 256)
        if ret != 0:
            return "Unsupported"

        return vbios_ptr.value.decode()

    @classmethod
    def get_gpu_sku(cls, device_idx: int) -> str:
        vbios = cls.get_gpu_vbios_version(device_idx)
        if vbios.count("-") == 2 and len(str(vbios.split("-")[1])) > 1:
            return vbios.split("-")[1]
        else:
            return "unknown"

    @classmethod
    def get_gpu_uuid(cls, device_idx: int) -> str:
        dv_uid = ctypes.c_uint64()
        ret = cls.invoke("rsmi_dev_unique_id_get", device_idx, ctypes.byref(dv_uid))
        if ret != 0:
            raise RuntimeError(
                f"get_gpu_uuid({device_idx}): error while executing rsmi_dev_unique_id_get():"
                f" unexpected exit code: {ret}"
            )

        return str(hex(dv_uid.value))
