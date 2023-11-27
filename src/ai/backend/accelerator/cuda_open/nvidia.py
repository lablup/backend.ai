import ctypes
import platform
from abc import ABCMeta, abstractmethod
from itertools import groupby
from operator import itemgetter
from typing import Any, MutableMapping, NamedTuple, Tuple, TypeAlias

# ref: https://developer.nvidia.com/cuda-toolkit-archive
TARGET_CUDA_VERSIONS = (
    (12, 2),
    (12, 1),
    (12, 0),
    (11, 8),
    (11, 7),
    (11, 6),
    (11, 5),
    (11, 4),
    (11, 3),
    (11, 2),
    (11, 1),
    (11, 0),
    (10, 2),
    (10, 1),
    (10, 0),
    (9, 2),
    (9, 1),
    (9, 0),
    (8, 0),
    (7, 5),
    (7, 0),
    (6, 5),
    (6, 0),
    (5, 5),
    (5, 0),
    # older versions are not supported
)


class LibraryError(RuntimeError):
    lib: str
    func: str
    code: int

    def __init__(self, lib: str, func: str, code: int):
        super().__init__(lib, func, code)
        self.lib = lib
        self.func = func
        self.code = code

    def __str__(self):
        return f"LibraryError: {self.lib}::{self.func}() returned error {self.code}"

    def __repr__(self):
        args = ", ".join(map(repr, self.args))
        return f"LibraryError({args})"


class cudaDeviceProp_v12(ctypes.Structure):
    _fields_ = [
        ("name", ctypes.c_char * 256),
        ("uuid", ctypes.c_byte * 16),  # cudaUUID_t
        ("luid", ctypes.c_byte * 8),
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
        ("managedMemSupported", ctypes.c_int),
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
        ("accessPolicyMaxWindowSize", ctypes.c_int),
        ("accessPolicyMaxWindowSize", ctypes.c_int),
        ("reservedSharedMemPerBlock", ctypes.c_size_t),
        ("hostRegisterSupported", ctypes.c_int),  # new in CUDA 12
        ("sparseCudaArraySupported", ctypes.c_int),  # new in CUDA 12
        ("hostRegisterReadOnlySupported", ctypes.c_int),  # new in CUDA 12
        ("timelineSemaphoreInteropSupported", ctypes.c_int),  # new in CUDA 12
        ("memoryPoolsSupported", ctypes.c_int),  # new in CUDA 12
        ("gpuDirectRDMASupported", ctypes.c_int),  # new in CUDA 12
        ("gpuDirectRDMAFlushWritesOptions", ctypes.c_uint),  # new in CUDA 12
        ("gpuDirectRDMAWritesOrdering", ctypes.c_int),  # new in CUDA 12
        ("memoryPoolSupportedHandleTypes", ctypes.c_uint),  # new in CUDA 12
        ("deferredMappingCudaArraySupported", ctypes.c_int),  # new in CUDA 12
        ("ipcEventSupported", ctypes.c_int),  # new in CUDA 12
        ("clusterLaunch", ctypes.c_int),  # new in CUDA 12
        ("unifiedFunctionPointers", ctypes.c_int),  # new in CUDA 12
        ("reserved2", ctypes.c_int * 2),
        ("reserved", ctypes.c_int * 61),
    ]


class cudaDeviceProp_v11(ctypes.Structure):
    _fields_ = [
        ("name", ctypes.c_char * 256),
        ("uuid", ctypes.c_byte * 16),  # cudaUUID_t
        ("luid", ctypes.c_byte * 8),
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
        ("persistingL2CacheMaxSize", ctypes.c_int),  # new in CUDA 11
        ("maxThreadsPerMultiProcessor", ctypes.c_int),
        ("streamPrioritiesSupported", ctypes.c_int),
        ("globalL1CacheSupported", ctypes.c_int),
        ("localL1CacheSupported", ctypes.c_int),
        ("sharedMemPerMultiprocessor", ctypes.c_size_t),
        ("regsPerMultiprocessor", ctypes.c_int),
        ("managedMemSupported", ctypes.c_int),
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
        ("maxBlocksPerMultiProcessor", ctypes.c_int),  # new in CUDA 11
        ("accessPolicyMaxWindowSize", ctypes.c_int),  # new in CUDA 11
        ("reservedSharedMemPerBlock", ctypes.c_size_t),  # new in CUDA 11
        ("_reserved", ctypes.c_char * 1024),
    ]


class cudaDeviceProp_v10(ctypes.Structure):
    _fields_ = [
        ("name", ctypes.c_char * 256),
        ("uuid", ctypes.c_byte * 16),  # cudaUUID_t  # new in CUDA 10
        ("luid", ctypes.c_byte * 8),  # new in CUDA 10
        ("luidDeviceNodeMask", ctypes.c_uint),  # new in CUDA 10
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
        ("maxThreadsPerMultiProcessor", ctypes.c_int),
        ("streamPrioritiesSupported", ctypes.c_int),
        ("globalL1CacheSupported", ctypes.c_int),
        ("localL1CacheSupported", ctypes.c_int),
        ("sharedMemPerMultiprocessor", ctypes.c_size_t),
        ("regsPerMultiprocessor", ctypes.c_int),
        ("managedMemSupported", ctypes.c_int),
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
        ("_reserved", ctypes.c_char * 1024),
    ]


class cudaDeviceProp(ctypes.Structure):
    _fields_ = [
        ("name", ctypes.c_char * 256),
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
        ("maxThreadsPerMultiProcessor", ctypes.c_int),
        ("streamPrioritiesSupported", ctypes.c_int),
        ("globalL1CacheSupported", ctypes.c_int),
        ("localL1CacheSupported", ctypes.c_int),
        ("sharedMemPerMultiprocessor", ctypes.c_size_t),
        ("regsPerMultiprocessor", ctypes.c_int),
        ("managedMemSupported", ctypes.c_int),
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
        ("_reserved", ctypes.c_char * 1024),
    ]


cudaDeviceProp_t: TypeAlias = (
    cudaDeviceProp_v12 | cudaDeviceProp_v11 | cudaDeviceProp_v10 | cudaDeviceProp
)


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


class libcudart(LibraryBase):
    name = "CUDART"

    _version = (0, 0)

    @classmethod
    def load_library(cls):
        system_type = platform.system()
        match system_type:
            case "Windows":
                arch = platform.architecture()[0]
                for major, minor in TARGET_CUDA_VERSIONS:
                    ver = f"{major}{minor}"
                    cudart = _load_library("cudart%s_%d.dll" % (arch[:2], ver))
                    if cudart is not None:
                        return cudart
            case "Darwin":
                for major, _ in groupby(TARGET_CUDA_VERSIONS, key=itemgetter(0)):
                    cudart = _load_library("libcudart.%d.dylib" % major)
                    if cudart is not None:
                        return cudart
                for major, minor in TARGET_CUDA_VERSIONS:
                    cudart = _load_library("libcudart.%d.%d.dylib" % (major, minor))
                    if cudart is not None:
                        return cudart
                return _load_library("libcudart.dylib")
            case _:
                for major, _ in groupby(TARGET_CUDA_VERSIONS, key=itemgetter(0)):
                    cudart = _load_library("libcudart.so.%d" % major)
                    if cudart is not None:
                        return cudart
                for major, minor in TARGET_CUDA_VERSIONS:
                    cudart = _load_library("libcudart.so.%d.%d" % (major, minor))
                    if cudart is not None:
                        return cudart
                return _load_library("libcudart.so")
        return None

    @classmethod
    def get_version(cls) -> Tuple[int, int]:
        if cls._version == (0, 0):
            raw_ver = ctypes.c_int()
            cls.invoke("cudaRuntimeGetVersion", ctypes.byref(raw_ver))
            cls._version = (raw_ver.value // 1000, (raw_ver.value % 100) // 10)
        return cls._version

    @classmethod
    def get_device_count(cls) -> int:
        count = ctypes.c_int()
        cls.invoke("cudaGetDeviceCount", ctypes.byref(count))
        return count.value

    @classmethod
    def get_device_props(cls, device_idx: int):
        props_struct: cudaDeviceProp_t
        if cls.get_version() >= (12, 0):
            props_struct = cudaDeviceProp_v12()
        elif cls.get_version() >= (11, 0):
            props_struct = cudaDeviceProp_v11()
        elif cls.get_version() >= (10, 0):
            props_struct = cudaDeviceProp_v10()
        else:
            props_struct = cudaDeviceProp()
        cls.invoke("cudaGetDeviceProperties", ctypes.byref(props_struct), device_idx)
        props: MutableMapping[str, Any] = {
            k: getattr(props_struct, k) for k, _ in props_struct._fields_
        }
        pci_bus_id = b" " * 16
        cls.invoke("cudaDeviceGetPCIBusId", ctypes.c_char_p(pci_bus_id), 16, device_idx)
        props["name"] = props["name"].decode()
        props["pciBusID_str"] = pci_bus_id.split(b"\x00")[0].decode()
        if "uuid" in props:
            props["uuid"] = bytes(props["uuid"])
        if "luid" in props:
            props["luid"] = bytes(props["luid"])
        return props

    @classmethod
    def reset(cls):
        """
        Releases the underlying CUDA driver context and resources occupied by it.
        """
        cls.invoke("cudaDeviceReset")


class nvmlMemoryInfo_t(ctypes.Structure):
    _fields_ = [
        ("total", ctypes.c_uint),
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

    _initialized = False

    @classmethod
    def load_library(cls):
        system_type = platform.system()
        if system_type == "Windows":
            return _load_library("libnvidia-ml.dll")
        elif system_type == "Darwin":
            return _load_library("libnvidia-ml.dylib")
        else:
            lib = _load_library("libnvidia-ml.so")
            if lib is None:
                lib = _load_library("libnvidia-ml.so.1")
            return lib
        return None

    @classmethod
    def ensure_init(cls):
        if not cls._initialized:
            cls.invoke("nvmlInit", NVML_INIT_FLAG_NO_GPUS)
            cls._initialized = True

    @classmethod
    def shutdown(cls):
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
