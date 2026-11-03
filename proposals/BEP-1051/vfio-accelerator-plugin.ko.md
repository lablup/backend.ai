<!-- context-for-ai
type: detail-doc
parent: BEP-1051 (Kata Containers Agent Backend)
scope: VFIO-based GPU passthrough compute plugin for Kata backend
depends-on: [kata-agent-backend.md]
key-decisions:
  - New CUDAVFIOPlugin separate from existing CUDAPlugin
  - DiscretePropertyAllocMap only (no FractionAllocMap)
  - Device discovery via sysfs PCI scan (not NVML)
  - IOMMU group validation at device scan time
  - GPUDirect RDMA support via Kata VRA: PCIe topology replication (switch-port mode), clique-id P2P grouping, GPU+NIC co-passthrough
  - InfiniBand HCA passthrough alongside GPU requires BAR sizing fix (Kata 3.8+) and RDMA device plugin
-->
# BEP-1051: VFIO 가속기 plugin

## 요약

새 `CUDAVFIOPlugin` compute plugin 이 Kata VM 용 NVIDIA GPU 를 VFIO passthrough 로 관리한다. Docker `DeviceRequests` API 와 NVML 을 사용하는 기존 `CUDAPlugin` 과 달리, 이 plugin 은 sysfs PCI 열거로 장치를 찾고, IOMMU group 격리를 검증하며, `KataKernelCreationContext` 가 소비하는 VFIO 장치 할당 구성을 생성한다.

## 현재 설계

기존 `CUDAPlugin`(`src/ai/backend/accelerator/cuda_open/plugin.py`)은 다음과 같다.

```python
# Device discovery via NVML/libcudart
async def list_devices(self) -> Collection[CUDADevice]:
    count = libcudart.get_device_count()
    for idx in range(count):
        props = libcudart.get_device_props(idx)
        # Uses nvidia driver to enumerate devices

# Docker-specific GPU attachment
async def generate_docker_args(self, docker, device_alloc):
    return {
        "HostConfig": {
            "DeviceRequests": [{
                "Driver": "nvidia",
                "DeviceIDs": assigned_device_ids,
                "Capabilities": [["utility", "compute", "video", "graphics"]],
            }]
        }
    }

# Allocation via DiscretePropertyAllocMap
async def create_alloc_map(self) -> AbstractAllocMap:
    return DiscretePropertyAllocMap(
        device_slots={
            dev.device_id: DeviceSlotInfo(SlotTypes.COUNT, SlotName("cuda.device"), Decimal(1))
            for dev in devices
        },
    )
```

Kata/VFIO 와 맞지 않는 점은 다음과 같다.

1. NVML 은 `nvidia` driver 가 적재된 상태에서만 동작한다. VFIO 모드에서는 GPU 가 `vfio-pci` 에 바인딩된다
2. `DeviceRequests` 는 Docker API 개념이다. Kata 는 VFIO 장치 annotation 을 사용한다
3. 장치가 `vfio-pci` 에 바인딩되면 호스트 측 지표(NVML)를 사용할 수 없다

## 제안 설계

### Package 구조

```
src/ai/backend/accelerator/cuda_vfio/
├── __init__.py
├── plugin.py           # CUDAVFIOPlugin
├── device.py           # CUDAVFIODevice, PCI/sysfs scanning
├── iommu.py            # IOMMU group detection and validation
└── BUILD               # Pants build with backendai_accelerator_v21 entry point
```

### Entry point 등록

```python
# BUILD
python_distribution(
    name="dist",
    entry_points={
        "backendai_accelerator_v21": {
            "cuda_vfio": "ai.backend.accelerator.cuda_vfio.plugin:CUDAVFIOPlugin",
        }
    },
)
```

agent config 의 plugin allowlist/blocklist 가 적재할 plugin 을 정한다.

- Docker agent: `cuda` 적재 (기존 CUDAPlugin)
- Kata agent: `cuda_vfio` 적재 (새 CUDAVFIOPlugin)

### CUDAVFIODevice

```python
@attrs.define(slots=True)
class CUDAVFIODevice(AbstractComputeDevice):
    pci_address: str           # "0000:41:00.0"
    iommu_group: int           # IOMMU group number
    vfio_device_path: str      # "/dev/vfio/42"
    pci_vendor_id: str         # "10de" (NVIDIA)
    pci_device_id: str         # "2684" (e.g., RTX 4090)
    model_name: str            # Mapped from PCI device ID
    memory_size: int           # GPU memory in bytes (from PCI BAR or lookup table)
    numa_node: int             # NUMA node affinity
    clique_id: str | None      # PCIe P2P group ID from Kata VRA (e.g., "clusterUUID.0")
```

### sysfs 를 통한 장치 탐지

GPU 가 `vfio-pci` 에 바인딩되어(`nvidia` 가 아니라) NVML 을 사용할 수 없다. PCI sysfs 로 탐지한다.

```python
async def list_devices(self) -> Collection[CUDAVFIODevice]:
    devices = []
    pci_devices_path = Path("/sys/bus/pci/devices")

    for pci_dir in pci_devices_path.iterdir():
        vendor = (pci_dir / "vendor").read_text().strip()
        if vendor != "0x10de":  # NVIDIA vendor ID
            continue

        device_class = (pci_dir / "class").read_text().strip()
        if not device_class.startswith("0x0302"):  # 3D controller (GPU)
            # Also check 0x0300 (VGA) for display GPUs
            if not device_class.startswith("0x0300"):
                continue

        driver_link = pci_dir / "driver"
        if driver_link.is_symlink():
            driver = driver_link.resolve().name
            if driver != "vfio-pci":
                log.warning("GPU {} bound to {} (expected vfio-pci), skipping",
                           pci_dir.name, driver)
                continue

        iommu_group = self._get_iommu_group(pci_dir)
        if iommu_group is None:
            log.warning("GPU {} has no IOMMU group, skipping", pci_dir.name)
            continue

        pci_device_id = (pci_dir / "device").read_text().strip().removeprefix("0x")
        model_name = PCI_DEVICE_ID_MAP.get(pci_device_id, f"NVIDIA GPU ({pci_device_id})")

        devices.append(CUDAVFIODevice(
            device_id=DeviceId(pci_dir.name),
            hw_location=pci_dir.name,
            numa_node=self._read_numa_node(pci_dir),
            memory_size=self._estimate_memory(pci_dir),
            processing_units=0,  # Unknown without NVML
            pci_address=pci_dir.name,
            iommu_group=iommu_group,
            vfio_device_path=f"/dev/vfio/{iommu_group}",
            pci_vendor_id="10de",
            pci_device_id=pci_device_id,
            model_name=model_name,
        ))

    return devices
```

### IOMMU group 검증

GPU 를 안전하게 passthrough 하려면 IOMMU group 이 격리되어야 한다.

```python
def _validate_iommu_group(self, pci_address: str, iommu_group: int) -> bool:
    """Check that the IOMMU group contains only the GPU and its audio companion."""
    group_path = Path(f"/sys/kernel/iommu_groups/{iommu_group}/devices")
    group_devices = [d.name for d in group_path.iterdir()]

    allowed_companions = set()
    for dev_addr in group_devices:
        if dev_addr == pci_address:
            continue
        dev_class = (Path("/sys/bus/pci/devices") / dev_addr / "class").read_text().strip()
        # 0x0403 = Audio device (NVIDIA GPU audio is commonly co-located)
        # 0x0604 = PCI bridge (acceptable, handled by VFIO)
        if dev_class.startswith("0x0403") or dev_class.startswith("0x0604"):
            allowed_companions.add(dev_addr)
        else:
            log.warning(
                "IOMMU group {} contains non-GPU device {} (class {}), "
                "GPU {} may not be passthrough-safe",
                iommu_group, dev_addr, dev_class, pci_address,
            )
            return False

    return True
```

GPU 가 서로 다른 IOMMU group 에 있으면 각각 다른 VM 에 독립적으로 할당할 수 있다. GPU 가 IOMMU group 을 공유하면 함께 할당하거나 아예 할당하지 않는다. 서버 하드웨어에서는 드물고 소비자용 mainboard 에서 흔하다.

### 할당 map

기존 CUDAPlugin 과 같은 `DiscretePropertyAllocMap` 방식을 사용한다.

```python
async def create_alloc_map(self) -> AbstractAllocMap:
    devices = await self.list_devices()
    return DiscretePropertyAllocMap(
        device_slots={
            dev.device_id: DeviceSlotInfo(
                SlotTypes.COUNT,
                SlotName("cuda.device"),
                Decimal(1),
            )
            for dev in devices
        },
    )
```

slot 이름 `cuda.device` 는 Docker CUDAPlugin 과 같다. scheduler 입장에서는 연결 방식과 무관하게 GPU 는 GPU 다.

### generate_docker_args(): VFIO 장치 구성

method 이름은 `AbstractComputePlugin` 에서 상속했지만 실제로는 Kata 전용 VFIO 구성을 반환한다.

```python
async def generate_docker_args(
    self,
    docker: Any,  # Unused for Kata; None is passed
    device_alloc: DeviceAllocation,
) -> Mapping[str, Any]:
    vfio_devices = []
    for slot_type, per_device_alloc in device_alloc.items():
        for device_id, alloc in per_device_alloc.items():
            if alloc > 0:
                dev = self._device_map[DeviceId(device_id)]
                vfio_devices.append({
                    "pci_address": dev.pci_address,
                    "iommu_group": dev.iommu_group,
                    "vfio_device": dev.vfio_device_path,
                    "model_name": dev.model_name,
                    "clique_id": dev.clique_id,      # P2P group for Kata VRA topology
                    "memory_size": dev.memory_size,   # GPU memory in bytes
                    "numa_node": dev.numa_node,       # NUMA affinity for CPU pinning
                })
    return {"_kata_vfio_devices": vfio_devices}
```

`KataKernelCreationContext.apply_accelerator_allocation()` 이 `_kata_vfio_devices` 를 읽어 VFIO hotplug 용 Kata 컨테이너 annotation 으로 변환한다. [kata-agent-backend.md](kata-agent-backend.md) 를 참고한다.

### 지표 수집

장치가 `vfio-pci` 에 바인딩되면 호스트 측 GPU 지표가 제한된다.

**node 수준 지표** (sysfs 에서 사용 가능):
- 전력 소비: `/sys/bus/pci/devices/{addr}/power/` (제한적)
- 온도: sysfs 만으로는 사용할 수 없다

**컨테이너 수준 지표** (guest VM 내부에서):
- guest VM 에는 `nvidia` driver 가 적재되어 NVML 이 guest 안에서 동작한다
- CoCo 가 기본: kata-agent 의 `ExecProcessRequest` 를 정책이 차단하므로 `containerd exec nvidia-smi` 는 **동작하지 않는다**
- 지표는 guest 안에서 systemd service 로 실행하는 **DCGM Exporter**(`:9400`)와 **Node Exporter**(`:9100`)가 노출한다 (attested rootfs 에 포함)
- Prometheus 가 Calico 네트워크로 이 exporter 에서 지표를 수집한다. 표준 HTTP 이며 kata-agent 가 관여하지 않는다
- CoCo 정책은 tRPC API 호출(exec, file 복사)을 제어하며 네트워크 트래픽은 제어하지 않는다

```python
async def gather_container_measures(
    self, stat_ctx, container_ids,
) -> Sequence[ContainerMeasurement]:
    # CoCo: ExecProcessRequest is blocked by kata-agent policy.
    # GPU metrics are collected by Prometheus scraping DCGM Exporter
    # inside the guest over the Calico network (port 9400).
    # This plugin does NOT collect per-container GPU metrics directly.
    # Backend.AI reads GPU metrics from Prometheus/Grafana instead.
    return []
```

### restore_from_container()

agent 가 재시작하면 실행 중인 Kata sandbox 에서 VFIO 바인딩을 재구성한다.

```python
async def restore_from_container(self, container, alloc_map):
    labels = container.labels
    # Read allocated device info from container labels
    # (KataKernelCreationContext stores PCI addresses in labels at creation time)
    pci_addresses = labels.get("ai.backend.vfio.pci_addresses", "").split(",")
    for pci_addr in pci_addresses:
        if pci_addr:
            device_id = DeviceId(pci_addr)
            alloc_map.apply_allocation({
                SlotName("cuda.device"): {device_id: Decimal(1)},
            })
```

## 인터페이스 / API

| method | 목적 |
|--------|---------|
| `list_devices()` | vfio-pci 에 바인딩된 NVIDIA GPU 를 PCI sysfs 로 스캔한다 |
| `available_slots()` | passthrough 준비가 된 GPU 수 |
| `create_alloc_map()` | `cuda.device` slot 을 가진 `DiscretePropertyAllocMap` |
| `generate_docker_args()` | Kata shim 용 `_kata_vfio_devices` 목록을 반환한다 |
| `gather_node_measures()` | 제한적인 sysfs 지표 (호스트에 NVML 이 없다) |
| `gather_container_measures()` | 빈 결과. CoCo 정책이 exec 를 차단하며 지표는 Prometheus 가 DCGM Exporter 에서 수집한다 |
| `restore_from_container()` | 컨테이너 label 에서 할당을 재구성한다 |

## 다중 node GPU 상호 연결: GPUDirect RDMA

### 개요

다중 node GPU 워크로드(분산 학습, 다중 node inference)에는 **GPUDirect RDMA** 가 필요하다. CPU 를 거치지 않고 GPU 와 RDMA 지원 NIC(InfiniBand HCA 또는 RoCE adapter) 사이에서 직접 메모리에 접근하는 방식이다. node 간 NCCL 기반 collective 연산을 InfiniBand 대역폭에 가까운 속도로 수행한다.

Kata VM 에서는 **GPU 와 InfiniBand HCA 를 모두 같은 VM 에 VFIO passthrough 로 할당**해야 하고, 둘 사이 peer-to-peer DMA 가 VM 경계를 넘어 동작해야 한다.

### Kata VM 의 GPUDirect RDMA 요구 사항

| 요구 사항 | 상세 |
|---|---|
| **GPU + NIC 동시 passthrough** | NVIDIA GPU 와 InfiniBand HCA(ConnectX-5 이상)를 같은 Kata VM 에 VFIO 할당해야 한다 |
| **IOMMU pass-through 모드** | GPUDirect RDMA 는 두 장치 관점에서 물리 주소가 같아야 한다. IOMMU 가 주소 변환 없이 1:1 pass-through 모드(`iommu=pt`)여야 한다. guest 안에 vIOMMU 가 있으면 그것도 pass-through 이거나 두 장치가 IOMMU domain 을 공유해야 한다 |
| **같은 PCIe root complex** | GPU 와 NIC 가 upstream PCIe root complex 를 공유해야 한다. socket 간(QPI/UPI) P2P 는 신뢰할 수 없거나 동작하지 않는다 |
| **Direct Translated P2P 용 ACS/ATS** | ACS(Access Control Services)는 보통 모든 DMA 를 root complex 로 강제한다. ATS(Address Translation Services, ConnectX-5 이상과 Volta 이상 GPU 에서 사용 가능)는 endpoint 가 IOVA→PA 변환을 미리 가져와 peer 에 직접 DMA 할 수 있게 해 P2P 에서 IOMMU 를 우회한다 |
| **PCIe 토폴로지 복제** | NVIDIA driver 는 PCIe 토폴로지로 P2P 가능 여부를 판단한다. 기본 가상화는 토폴로지를 평탄화해(모든 장치가 root bus 에 있다) P2P 를 비활성화한다. guest 가 호스트의 PCIe switch 계층을 복제해야 한다 |
| **guest driver stack** | guest 안에 전체 NVIDIA 와 Mellanox stack 이 필요하다: `nvidia` driver, `mlx5_core`/`mlx5_ib`, `ib_core`, `ib_uverbs`, `nvidia-peermem`(GPU 와 IB subsystem 을 연결한다), MLNX_OFED |

### Kata VRA (Virtualization Reference Architecture)

Kata project 의 [VRA 설계 문서](https://github.com/kata-containers/kata-containers/blob/main/docs/design/kata-vra.md)는 GPUDirect P2P 와 RDMA 를 세 가지 핵심 방식으로 다룬다.

**1. switch port 를 통한 PCIe 토폴로지 복제:**

```toml
# kata configuration.toml
hotplug_vfio = "switch-port"    # Replicate host PCIe switch topology in guest
pcie_switch_port = 8            # Number of switch downstream ports
```

guest 안에 호스트 토폴로지를 그대로 반영한 PCIe switch 구조를 생성한다. 호스트에서 같은 PCIe switch 아래 있던 장치를 guest 의 같은 가상 switch 아래에 두어 NVIDIA driver 가 P2P 가능성을 인식하게 한다.

**2. P2P 장치 묶음을 위한 clique-id annotation:**

`clique-id` 가 같은 장치가 P2P group 을 이룬다. CDI(Container Device Interface)로 구성한다.

```yaml
# GPU on PCIe switch
- annotations:
    bdf: "41:00.0"
    clique-id: "0"

# InfiniBand HCA on same PCIe switch
- annotations:
    bdf: "42:00.0"
    clique-id: "0"    # Same clique → P2P enabled between GPU and NIC
```

hypervisor 는 clique-id 로 토폴로지 메타데이터를 제공하고 NVIDIA driver 가 이를 읽어 GPUDirect P2P 를 활성화한다. 가상화한 PCIe 토폴로지가 호스트와 정확히 일치하지 않아도 된다.

**3. 다중 function IOMMU group 처리:**

NVIDIA 데이터센터 GPU 는 GPU, audio, USB 가 한 IOMMU group 에 있는 경우가 많다. VRA 는 선택적으로 연결해 처리한다.

- GPU: PCIe root/switch port (express protocol 이 필요하고 4K IO range 를 소비한다)
- audio/USB companion: PCI bridge (표준 PCI, IO range 를 소비하지 않는다)

부족한 PCIe IO 공간(전체 64K, port 당 4K, 최대 약 16 port)을 아낀다.

### NVLink / NVSwitch (node 안 GPU-GPU)

NVLink 는 PCIe 를 우회해 GPU 를 직접 연결한다. NVSwitch 는 DGX/HGX 시스템에서 all-to-all NVLink 를 제공한다.

GPU 를 Kata VM 에 VFIO passthrough 로 할당하면 다음과 같다.

- NVLink 하드웨어 연결은 물리적으로 그대로다
- guest 안의 NVIDIA driver 가 VFIO BAR 매핑으로 접근할 수 있는 GPU register 를 통해 NVLink 를 감지한다
- 두 GPU 가 같은 guest 에 있고 driver 가 NVLink 토폴로지를 감지하면 NVLink 를 통한 P2P 가 동작한다
- VMware vSphere(NVLink 를 사용하는 GPU passthrough)에서 입증되었으므로 KVM/VFIO 도 비슷하게 동작할 것으로 본다

Backend.AI 의 다중 컨테이너 세션(단일 호스트의 cluster)에서는 모든 GPU 를 containerd Sandbox API 로 Kata sandbox(VM) 하나에 passthrough 로 할당해 VM 을 공유하는 컨테이너 사이에서 NVLink 통신을 사용할 수 있다.

### 현재 upstream 상태

| 구성 요소 | 상태 | 참조 |
|---|---|---|
| kata-vra.md 설계 | 작성됨. GPUDirect P2P + RDMA 를 다룬다 | [kata-vra.md](https://github.com/kata-containers/kata-containers/blob/main/docs/design/kata-vra.md) |
| GPU VFIO passthrough | 동작함 (A100, H100 은 주의 사항 있음) | [#12723](https://github.com/kata-containers/kata-containers/issues/12723) |
| InfiniBand HCA passthrough | 부분 동작. BAR 할당은 Kata 3.8 이상에서 수정됨 | [#10392](https://github.com/kata-containers/kata-containers/issues/10392) |
| SR-IOV VF passthrough | 깨져 있음. "No PCI mapping found" | [#11910](https://github.com/kata-containers/kata-containers/issues/11910) |
| GPUDirect RDMA end-to-end | Kata 에서 아직 입증되지 않음 | [#10796](https://github.com/kata-containers/kata-containers/issues/10796) (open, 높은 우선순위) |

### InfiniBand HCA BAR 할당 수정

Kata 3.8 이상은 `getBARsMaxAddressableMemory()` 로 큰 BAR 장치의 PCIe BAR window 크기를 자동으로 정한다. 그러나 이 함수는 처음에 `IsGPU()` 검사로 NVIDIA GPU 만 감지하고 InfiniBand HCA 는 건너뛰었다. ConnectX-6 은 BAR0 이 32MB 이상 필요한데 기본 2MB 할당으로 `"BAR0: no space for [mem size 32MB 64bit pref]"` 가 발생했다. 수정은 BAR 크기 계산에서 GPU 감지와 함께 Mellanox 장치 감지를 포함한다([#10392](https://github.com/kata-containers/kata-containers/issues/10392)).

### CUDAVFIOPlugin 에 대한 영향

GPUDirect RDMA 를 지원하려면 `CUDAVFIOPlugin` 이 함께 배치된 InfiniBand HCA 를 알아야 한다.

```python
async def generate_docker_args(self, docker, device_alloc):
    vfio_devices = []
    for device_id, alloc in per_device_alloc.items():
        dev = self._device_map[DeviceId(device_id)]
        vfio_devices.append({
            "pci_address": dev.pci_address,
            "iommu_group": dev.iommu_group,
            "vfio_device": dev.vfio_device_path,
            "model_name": dev.model_name,
            "clique_id": dev.clique_id,          # NEW: P2P group identifier
        })
    return {
        "_kata_vfio_devices": vfio_devices,
        "_kata_rdma_devices": self._get_colocated_rdma_devices(vfio_devices),  # NEW
    }
```

NIC 쪽의 InfiniBand HCA 탐지, IOMMU group 검증, VFIO 장치 구성을 맡는 별도 **RDMAVFIOPlugin** 이 필요하다. `CUDAVFIOPlugin` 을 확장해 구현할 수도 있다. `clique_id` 가 GPU 와 NIC 장치를 연결해 P2P 토폴로지를 복제한다.

### guest VM 기본 이미지 요구 사항 (GPUDirect RDMA)

스토리지 파일 시스템 클라이언트([migration-compatibility.md](migration-compatibility.md) 참고) 외에 guest rootfs 에 다음이 필요하다.

| 구성 요소 | 목적 |
|---|---|
| NVIDIA GPU driver + CUDA toolkit | GPU 연산과 `nvidia-peermem` 모듈 |
| MLNX_OFED | InfiniBand/RoCE driver stack (`mlx5_core`, `mlx5_ib`) |
| `nvidia-peermem` 커널 모듈 | GPUDirect RDMA 를 위해 GPU 메모리를 IB subsystem 에 등록한다 |
| `libibverbs`, `librdmacm` | RDMA userspace 라이브러리 |
| NCCL | 다중 GPU collective 통신. node 간에는 GPUDirect RDMA 를 사용한다 |
| `CONFIG_INFINIBAND=y`, `CONFIG_MLX5_CORE=y`, `CONFIG_VFIO=y` 를 가진 guest 커널 | InfiniBand 와 VFIO 커널 지원 |

**참고:** MLNX_OFED 는 NVIDIA GPU driver 설치 전에 또는 함께 설치해야 한다. GPU driver 를 먼저 설치하면 `nvidia-peermem` 을 올바르게 빌드하기 위해 OFED 뒤에 다시 설치해야 한다.

## 구현 참고 사항

- `PCI_DEVICE_ID_MAP` 은 PCI 장치 ID 를 model 이름으로 변환하는 정적 mapping 이다. 예를 들어 `"2684"` 는 `"NVIDIA RTX 4090"` 에 매핑한다. PCI ID database 에서 가져오거나 흔한 GPU model 의 선별 목록으로 관리한다.
- VFIO 는 `/dev/vfio/{group}` 장치 file 에 접근할 수 있어야 한다. agent 프로세스에 `CAP_SYS_RAWIO` 나 root 권한이 필요하다.
- BEP-1016(Accelerator Interface v2)를 구현하면 `generate_docker_args()` 를 `create_lifecycle_hook()` 으로 이관해 VFIO 장치 항목을 담은 `WorkloadConfig` 를 반환해야 한다.
- `generate_docker_args()` 의 `docker` 인자는 Docker client 가 없으므로 `KataKernelCreationContext` 가 `None` 을 전달한다.
- 같은 IOMMU group 의 GPU audio companion 장치도 패스스루해야 한다. plugin 이 이를 투명하게 처리한다.
