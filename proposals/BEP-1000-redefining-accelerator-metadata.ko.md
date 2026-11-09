# 가속기 메타데이터 재정의

## 현재 구조

```python
# ai.backend.common.types
# -----------------------
class ResourceSlotReprFormat(TypedDict):
    # I'd propose to rename this from AcceleratorNumberFormat.
    binary: bool
    round_length: int


class AcceleratorMetadata(TypedDict):
    slot_name: str
    description: str
    human_readable_name: str
    display_unit: str
    display_icon: str
    number_format: ResourceSlotReprFormat


# ai.backend.agent.resources
# --------------------------
class AbstractComputeDevice:
    device_id: DeviceId
    hw_location: str  # either PCI bus ID or arbitrary string
    memory_size: int  # bytes of available per-accelerator memory
    processing_units: int  # number of processing units (e.g., cores, SMP)
    numa_node: Optional[int]  # NUMA node ID (None if not applicable)

    ...

class AbstractComputePlugin(AbstractPlugin, metaclass=ABCMeta):
    key: DeviceName = DeviceName("accelerator")
    slot_types: Sequence[tuple[SlotName, SlotTypes]]
    exclusive_slot_types: set[str]

    @abstractmethod
    def get_metadata(self) -> AcceleratorMetadata: ...

    @abstractmethod
    async def list_devices(self) -> Collection[AbstractComputeDevice]: ...

    @abstractmethod
    async def available_slots(self) -> Mapping[SlotName, Decimal]: ...

    @abstractmethod
    def get_version(self) -> str: ...

    @abstractmethod
    async def extra_info(self) -> Mapping[str, str]: ...

    @abstractmethod
    async def gather_node_measures(self, ctx: StatContext) -> Sequence[NodeMeasurement]: ...

    @abstractmethod
    async def gather_container_measures(
        self,
        ctx: StatContext,
        container_ids: Sequence[str],
    ) -> Sequence[ContainerMeasurement]: ...

    @abstractmethod
    async def gather_process_measures(
        self, ctx: StatContext, pid_map: Mapping[int, str]
    ) -> Sequence[ProcessMeasurement]: ...

    @abstractmethod
    async def create_alloc_map(self) -> AbstractAllocMap: ...

    @abstractmethod
    async def get_hooks(self, distro: str, arch: str) -> Sequence[Path]: ...

    @abstractmethod
    async def generate_docker_args(
        self,
        docker: aiodocker.docker.Docker,
        device_alloc: DeviceAllocation,
    ) -> Mapping[str, Any]: ...

    async def generate_resource_data(self, device_alloc: DeviceAllocation) -> Mapping[str, str]: ...

    @abstractmethod
    async def restore_from_container(
        self,
        container: SessionContainer,
        alloc_map: AbstractAllocMap,
    ) -> None: ...

    @abstractmethod
    async def get_attached_devices(
        self,
        device_alloc: DeviceAllocation,
    ) -> Sequence[DeviceModelInfo]: ...

    async def get_node_hwinfo(self) -> HardwareMetadata: ...

    @abstractmethod
    async def get_docker_networks(
        self,
        device_alloc: DeviceAllocation,
    ) -> list[str]: ...

    @abstractmethod
    async def generate_mounts(
        self,
        source_path: Path,
        device_alloc: DeviceAllocation,
    ) -> list[MountInfo]: ...

    def get_additional_gids(self) -> list[int]: ...

    def get_additional_allowed_syscalls(self) -> list[str]: ...
```

### 문제

* plugin 하나는 `AcceleratorMetadata` 하나만 반환할 수 있다.
  - 예를 들어 cuda plugin 이 구성이 다른 장치를 여럿 가질 때(MIG 를 켠 GPU 2개와 끈 GPU 6개), 서로 다른 AcceleratorMetadata 인스턴스 두 개를 반환할 수 없다.
* `AcceleratorMetadata` 가 자원 슬롯을 나타내는지 장치를 나타내는지 혼동된다. 실제로는 자원 슬롯을 위한 것이다. 이름을 분명히 해야 한다.
* 연산 정밀도 지원, 분할 기능, 메모리 계층처럼 여러 장치 기능을 담도록 메타데이터 형식을 넓혀야 한다.

## 제안 구조 (작성 중)

```python
# ai.backend.common.types
# -----------------------
class ComputePrecisionSupportLevel(enum.StrEnum):
    NATIVE = enum.auto()
    EMULATED = enum.auto()
    NONE = enum.auto()


@attrs.define(auto_attribs=True)
class ComputePrecisionSupport:
    format: str  # e.g., "FP32", "TF32", "BF16", "FP16", "FP8", "INT8", "INT4", "FP4"
    support: ComputePrecisionSupportLevel


@attrs.define(auto_attribs=True)
class ComputeUnit:
    name: str  # e.g., "SM", "Tensor Core", "GPC", "CU", "TPC", "AI Core"
    count: int  # Number of such units in the device


@attrs.define(auto_attribs=True)
class MemorySpec:
    total_memory: int  # Total on-device memory capacity in bytes
    memory_type: str   # e.g., "HBM2", "HBM3", "GDDR6", "DDR5"
    bandwidth: Optional[float] = None          # Peak memory bandwidth in GiB/s
    l1_cache_per_core: Optional[int] = None    # L1 cache size per compute unit (bytes)
    l2_cache: Optional[int] = None             # L2 cache size (bytes, chip-wide or per die)
    shared_mem_per_core: Optional[int] = None  # Size of programmable shared memory per core (bytes)
    memory_channels: Optional[int] = None      # Number of memory channels or HBM stacks


@attrs.define(auto_attribs=True)
class PartitioningCapability:
    max_partitions: int = 1           # Maximum number of slices/partitions
    technology: Optional[str] = None  # Name of partitioning method (e.g., "MIG", "fGPU")


# ai.backend.agent.resources
# --------------------------
class AbstractComputeDevice:
    device_id: DeviceId
    hw_location: str          # either PCI bus ID or arbitrary string
    numa_node: Optional[int]  # NUMA node ID (None if not applicable)
    memory_size: int          # (legacy-compat) size of the on-device memory (bytes)
    processing_units: int     # (legacy-compat) number of the representative compute units
    memory_spec: MemorySpec   # (new) detailed memory specification
    compute_units: Sequence[ComputeUnit]  # (new) detailed compute unit specification
    precision_support: Sequence[ComputePrecisionSupport]
    partioning_support: Sequence[PartitioningCapability]
```

### 설계 목표

* 분할 방식을 여러 가지 지원하는 이기종 가속기에 맞게 일반화한다.
* plugin 인스턴스 하나가 서로 다른 자원 슬롯 정의 여럿을 지원한다. 예를 들어 한 node 에 MIG 와 fGPU 가 섞여 있어도 된다.
* JSON 을 사용하는 포괄적인 schema 기반 메타데이터 인터페이스로, Python plugin 인터페이스를 변경하지 않고 확장할 수 있게 한다.
* 검증을 쉽게 하려고 명시적인 jsonschema 정의를 검토한다.
* `get_metadata()` 와 `extra_info()` 처럼 일부 겹치는 인터페이스를 통합한다.

### 가속기 API 재설계

[BEP-1016](https://github.com/lablup/beps/blob/main/proposals/BEP-1016-accelerator-interface-v2.md)을 참고한다.
