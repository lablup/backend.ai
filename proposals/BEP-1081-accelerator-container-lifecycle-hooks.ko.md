# 가속기 플러그인 컨테이너 라이프사이클 훅

## Related Issues

- JIRA: 아직 생성하지 않음
- 사용처: `backend.ai-accelerator-cuda-open` (독립 오픈소스 CUDA 가속기 플러그인)의 fractional 할당 모드
- 상위 문서: [BEP-1016](BEP-1016-accelerator-interface-v2.md) (Accelerator Interface v2, `AbstractLifecycleHook`)

## Goal

가속기 플러그인은 컨테이너가 생기기 전에만 컨테이너 설정을 만듭니다 (`generate_docker_args`, `generate_mounts`, `generate_resource_data`). 컨테이너 자체에는 작업할 수 없습니다. 이 BEP 는 플러그인이 생성된 컨테이너에 시작 전에 작업하고, 컨테이너가 사라질 때 컨테이너별 상태를 해제할 수 있도록 Agent 호출 두 개를 추가합니다. 첫 사용처를 만들면서 발견한 코어 결함 두 개도 수정합니다.

첫 사용처는 독립 CUDA 플러그인의 fractional 모드입니다. 컨테이너에 `LD_PRELOAD` 훅 없이, 공유 GPU 의 메모리를 `cuda.mem` 슬롯 (bytes) 으로 제공합니다.

| 플러그인이 강제하는 것 | 방법 | 코어에 필요한 것 |
|---|---|---|
| 컨테이너별 GPU 메모리 제한 | 컨테이너 cgroup 에 `nvmlDeviceSetMemoryLimits_v1`, cgroup v2 `dmem` 컨트롤러 (Linux 6.14+) 또는 `misc` (Linux 5.14+) 로 집계, 드라이버 r615+ | create 이후, start 이전의 컨테이너 ID. 첫 프로세스가 실행되기 전에 제한이 걸려 있어야 함 |
| 컨테이너별 SM 몫 | 컨테이너마다 MPS namespace (와 SM 파티션) 하나 | 컨테이너가 사라질 때 namespace 와 파티션을 삭제할 호출 |
| Agent 재시작 뒤 복원한 할당 | `restore_from_container()` 가 `resource.txt` 를 읽음 | bytes 타입 슬롯의 정확한 바이트 수 |
| 에이전트 heartbeat | Agent 가 `cuda.mem` 용량을 보고 | `cuda.mem` 의 `resource_slot_types` 행 |

## Non-goals

- BEP-1016 의 v2 플러그인 인터페이스 (`AbstractLifecycleHook`, `Workload`, `WorkloadConfig`). 여기의 두 호출은 나중에 그 인터페이스로 대체합니다 (결정 요약 참고).
- Docker 외의 Agent 백엔드.
- 훅이 반환하는 설정 변경. 컨테이너 설정은 계속 `generate_docker_args` 가 만듭니다.
- 열린 질문의 후속 항목: MIG 자원 슬롯 유형 등록, GPU 개수 힌트, 트리 안의 `cuda_open` 사본.

## Current design and scope, by area

### 가속기 플러그인 인터페이스 (`AbstractComputePlugin`)

| | 항목 |
|---|---|
| ✅ 있음 | `generate_docker_args`, `generate_mounts`, `generate_resource_data`, `restore_from_container`. 모두 create 전이나 복원 시에 호출 |
| ➕ 추가 | `on_container_created(container_id, device_alloc)`, `on_container_destroyed(container_id, device_alloc)`. 둘 다 기본 구현은 아무것도 하지 않음 |

### Docker Agent

| | 항목 |
|---|---|
| ✅ 있음 | `start_container`: create → `resource.txt` 에 CID 기록 → start. create 뒤의 실패는 컨테이너 ID 를 담은 `ContainerCreationError` 로 올라가고, 실패 처리가 그 ID 로 커널을 destroy 함 |
| ✅ 있음 | `clean_kernel`: 로그 수집 → domain socket proxy 종료 → 컨테이너 삭제 → 네트워크 이탈 |
| ➕ 추가 | CID 기록 뒤, start 전에 플러그인마다 `on_container_created` 호출 |
| ➕ 추가 | `clean_kernel` 에서 컨테이너 삭제 전에 플러그인마다 `on_container_destroyed` 호출 |

### `resource.txt`

| | 항목 |
|---|---|
| ✅ 있음 | `KernelResourceSpec.write_to_string()` 이 bytes 타입 슬롯 할당을 `BinarySize` 문자열 (`1.67g`) 로 써서 값이 반올림됨. 읽을 때는 `BinarySize` 형식과 숫자를 모두 받음 |
| ➕ 변경 | bytes 타입 슬롯 할당을 바이트 수 정수로 기록. 읽기는 그대로 |

### Manager 자원 자원 슬롯 유형

| | 항목 |
|---|---|
| ✅ 있음 | `cuda.device`, `cuda.shares` 의 `resource_slot_types` 행. 등록되지 않은 슬롯을 보고하는 에이전트 heartbeat 는 `agent_resources` 외래 키에서 실패 |
| ➕ 추가 | `cuda.mem` (`bytes`) 을 등록하는 Alembic 마이그레이션 |

## Implementation design

### 훅 계약

| 훅 | 호출 시점 | 인자 | 오류 시 |
|---|---|---|---|
| `on_container_created` | `docker create` 와 `resource.txt` 의 CID 기록 뒤, `docker start` 전 | 컨테이너 ID, 해당 플러그인의 `DeviceAllocation` | start 를 중단: `ContainerCreationError` 로 올라가고, 기존 실패 경로가 커널을 destroy 하고 clean 함 |
| `on_container_destroyed` | `clean_kernel` 에서 컨테이너가 멈추고 로그를 수집한 뒤, 삭제 전. `debug.skip_container_deletion` 으로 컨테이너를 남길 때도 호출 | 컨테이너 ID, 해당 플러그인의 `DeviceAllocation` | 플러그인별로 traceback 과 함께 로그. 나머지 플러그인과 정리는 계속 진행 |

```python
class AbstractComputePlugin:
    async def on_container_created(
        self, container_id: ContainerId, device_alloc: DeviceAllocation
    ) -> None: ...
    async def on_container_destroyed(
        self, container_id: ContainerId, device_alloc: DeviceAllocation
    ) -> None: ...
```

커널 하나의 흐름:

```
generate_docker_args → docker create → resource.txt 에 CID → on_container_created (플러그인마다) → docker start
컨테이너 종료 → clean_kernel → on_container_destroyed (플러그인마다) → docker delete → 할당 해제
```

플러그인이 따르는 규칙:

| 규칙 | 이유 |
|---|---|
| 훅은 `KernelResourceSpec.allocations` 에 항목이 있는 플러그인마다 한 번 호출. 그 커널에 할당이 없는 플러그인은 호출하지 않음 | 할당이 플러그인의 유일한 커널별 입력 |
| `on_container_destroyed` 는 멱등이고, `on_container_created` 가 실행되지 않았거나 실패한 컨테이너도 받음 | 실패한 start, 취소된 create, Agent 크래시 뒤 재시작이 모두 `clean_kernel` 에 도달 |
| 훅은 컨테이너별 상태를 플러그인 메모리가 아니라 컨테이너 (label, `docker inspect`) 에서 읽음 | Agent 는 언제든 재시작됨. BEP-1016 도 `AbstractLifecycleHook` 에 같은 조건을 둠 |
| 커널 재시작은 두 훅을 다시 실행 | 재시작은 destroy → clean → 새 컨테이너 create |

### `resource.txt` 의 정확한 바이트 수

`write_to_string()` 은 bytes 타입의 디바이스별 할당을 정수로 씁니다 (`cuda.mem=0:4294967296`). 반올림된 `BinarySize` 문자열 때문에 `restore_from_container()` 가 복원한 할당이 플러그인이 강제한 양과 달라졌고, Agent 재시작 뒤 alloc map 이 어긋났습니다. 읽기는 두 형식을 모두 받으므로 이전 Agent 가 시작한 커널도 그대로 복원됩니다.

### `cuda.mem` 자원 슬롯 유형

| column | 값 |
|---|---|
| `slot_name` | `cuda.mem` |
| `slot_type` | `bytes` |
| `display_name` | `GPU Memory` |
| `display_unit` | `GiB` |
| `number_format` | `{"binary": true, "round_length": 1}` |
| `rank` | 450 |

upgrade 는 `ON CONFLICT DO NOTHING` 으로 넣습니다. downgrade 는 `cuda.mem` 을 참조하는 테이블이 없을 때만 행을 삭제합니다.

### CUDA 플러그인의 사용

참고용이며 코어 변경에 포함되지 않습니다.

| 훅 | fractional 모드 |
|---|---|
| `on_container_created` | 엔진보다 먼저 컨테이너 cgroup 을 만들고 `dmem` 또는 `misc` 를 위임, 말단 cgroup 에 컨트롤러가 있는지 확인, NVML 로 GPU 마다 hard limit 설정, 컨테이너의 MPS namespace 를 attached 로 표시 |
| `on_container_destroyed` | MPS namespace 와 SM 파티션 삭제, 제한 해제, 엔진이 남긴 cgroup 제거 |

device 모드는 두 훅에서 아무것도 하지 않습니다.

## Migration / Compatibility

| 변경 | 영향 |
|---|---|
| 기본 구현이 비어 있는 훅 두 개 | 추가만 함. 기존 가속기 플러그인과 mock 가속기는 영향 없음 |
| bytes 를 정수로 기록 | 이전 Agent 도 새 형식을 읽음 (`BinarySize.from_str` 가 숫자를 받음). 새 Agent 도 이전 형식을 읽음 |
| `cuda.mem` 마이그레이션 | 멱등. 없으면 운영자가 자원 슬롯 유형을 직접 등록할 때까지 fractional 모드 Agent 의 에이전트 heartbeat 가 실패 |
| 독립 플러그인의 MIG 슬롯 이름 | `cuda.device:<profile>` (`cuda.device:1g.10gb`, `cuda.device:2g.48gb+gfx`), `-mig` 접미사 없음. 코어는 접미사를 해석하지 않으며, 이름마다 `resource_slot_types` 행이 필요 (열린 질문 참고) |

## Implementation Plan

1. 코어: 훅 두 개, `resource.txt` 의 정확한 바이트 수, `cuda.mem` 마이그레이션, 단위 테스트 (`topic/compute-plugin-container-hooks` 의 draft PR).
2. 열린 질문의 코어 후속 작업, 항목마다 PR 하나.
3. BEP-1016: 두 메서드를 `AbstractLifecycleHook.post_create()`, `post_terminate()` 로 대체.

## Decision Summary

| 결정 | 근거 |
|---|---|
| 지금은 BEP-1016 인터페이스가 아니라 `AbstractComputePlugin` 의 메서드 두 개 | 추가만 하고 작음. `on_container_created` 는 `post_create()`, `on_container_destroyed` 는 `post_terminate()` 에 대응 |
| `on_container_created` 는 create 와 start 사이에 실행 | cgroup 제한과 MPS 바인딩이 첫 프로세스 전에 있어야 함. start 뒤라면 제한이 걸리기 전에 프로세스가 GPU 메모리를 할당할 수 있음 |
| `on_container_created` 의 실패는 start 를 중단 | 제한이 없는 컨테이너는 실행하지 않음 |
| `on_container_destroyed` 의 실패는 로그만 남김 | 플러그인 하나의 정리가 컨테이너 삭제와 할당 해제를 차단하지 않음 |
| `on_container_destroyed` 는 컨테이너 삭제 전에 실행 | 플러그인이 컨테이너의 label 과 cgroup parent 를 아직 읽을 수 있음 |
| 훅은 컨테이너 ID 와 자기 할당만 받음 | 플러그인이 컨테이너를 직접 조회하므로 인터페이스가 작게 유지됨 |
| 드라이버, cgroup, MPS 로 강제하고 `LD_PRELOAD` 는 쓰지 않음 | 컨테이너 이미지 안에 끼어들지 않음 |
| bytes 타입 할당을 정수로 기록 | `BinarySize` 문자열은 값을 반올림 |

## Open Questions

| 질문 | 선택지 |
|---|---|
| MIG 자원 슬롯 유형 | 플러그인이 보고하는 `cuda.device:<profile>` 마다 `resource_slot_types` 행이 필요. Agent 가 에이전트 heartbeat 로 보고한 미등록 자원 슬롯 유형을 등록, 플러그인이 자기 자원 슬롯 유형을 선언, 또는 profile 마다 운영자 절차를 문서화 |
| GPU 개수 힌트 | `cuda.mem` 은 GPU 하나에 배치됨. 플러그인의 alloc map 은 요청을 고르게 나눌 GPU 개수를 받지만 아무도 전달하지 않음. 세션별 GPU 개수를 manager 에서 `KernelResourceSpec` 을 거쳐 `allocate()` 까지 전달 |
| 트리 안의 `src/ai/backend/accelerator/cuda_open` | 독립 패키지와 모듈 경로, entry point 가 같고 `./py` 가 `src/` 를 앞에 두므로 독립 패키지를 가림. 삭제하거나 독립 패키지로 대체 |
| `KernelResourceSpec.to_json_serializable_dict()` | bytes 슬롯에서 `o["slots"]` 전체를 서식화한 문자열로 덮어씀. 별도로 수정 |

## Related documents

- [BEP-1016: Accelerator Interface v2](BEP-1016-accelerator-interface-v2.md)
- [BEP-1000: Redefining Accelerator Metadata](BEP-1000-redefining-accelerator-metadata.md)
- [BEP-1061: Agent Kernel Lifecycle Structuring](BEP-1061-agent-kernel-lifecycle.md)
