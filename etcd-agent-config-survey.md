# Agent가 etcd에서 읽는 설정 전수 조사

에이전트 데몬과 가속기 플러그인이 etcd에서 읽는 모든 값에 대한 판정과 처방.
판정 기준은 BEP-1059의 것 — **부팅·동작 파라미터인가, 매니저가 소유해야 하는 상태인가**.

관련 이슈: BA-8103 (에픽), BA-8104 (조사)

## 판정 범례

| 판정 | 뜻 |
|---|---|
| `BLOCKER` | 설정이 아님 |
| `WRONG AXIS` | 설정이지만 위치 또는 스코프가 틀림 |
| `DEAD` | 읽지만 소비되지 않음 |
| `OK` | 유지 |
| `OUT OF SCOPE` | 다른 이슈 소관 |

## Agent daemon

| etcd key | 용도 | 판정 | 처방 |
|---|---|---|---|
| `nodes/manager` | 매니저가 한 대라도 살아 있을 때까지 기동 대기 (`detect_manager`, `server.py:519,522`) | `BLOCKER` — 런타임 상태 | 매니저 생존 여부를 `ai/backend/service_discovery`에서 읽고, 이 키와 watch를 제거 |
| `config/container/kernel-uid`, `kernel-gid` | 컨테이너 내 프로세스 UID/GID | `WRONG AXIS` — 전역 키가 노드 로컬 TOML 필드를 덮어씀 | 노드 TOML이 이기게 하고 etcd는 클러스터 기본값으로만 사용 |
| `config/agent/api/pull-timeout` | 이미지 pull 타임아웃 (`agent.py:2152,2645`, `stage/kernel_lifecycle/docker/image.py:119`) | `WRONG AXIS` — pull 소요 시간은 그 노드의 NIC·디스크·레지스트리 거리에 좌우되는데 전역 키가 이김 | 위와 동일 |
| `config/agent/api/commit-timeout` | 컨테이너 commit 타임아웃 (`docker/kernel.py:260`) | `WRONG AXIS` — 동일 | 동일 |
| `config/agent/api/push-timeout` | commit된 이미지 push 타임아웃 (`server.py:1084`) | `WRONG AXIS` — 동일 | 동일 |
| `config/network/subnet/agent` | RPC 주소 자동 탐지용 서브넷 힌트 (`server.py:1476`) | `WRONG AXIS` — 노드 NIC 구성이 전역 키에. 영향은 경미 (부팅 시 1회 힌트) | 동일, 우선순위 최하 |
| `config/network/subnet/<network>` | 컨테이너 바인드 주소 힌트 (`utils.py:191`) | `WRONG AXIS` — 동일, 경미 | 동일, 우선순위 최하 |
| `config/plugins/cpu`, `config/plugins/memory` | 내장 CPU/메모리 플러그인에 전달 | `DEAD` — 두 플러그인 모두 키를 읽지 않고 `config_watch_enabled = False` | 읽기와 키 제거 |
| `config/plugins/accelerator` | 벌크 dict를 `AgentUnifiedConfig.plugins`에 주입 (`server.py:1640`) | `DEAD` — 이 필드를 읽는 코드가 agent·in-tree 가속기·plugins 전체에 없음 | 읽기와 필드 제거 |
| `config/redis/*` | 메시지 큐·통계·서비스 디스커버리용 Redis/Valkey 접속 | `OK` — 클러스터 공유 인프라 엔드포인트 | 유지. BA-7794가 스토리지 프록시에서 하듯 typed config 필드로 승격 |
| `config/agent/container-logs/{driver,max-length,chunk-size}` | 컨테이너 로그 수집 정책 | `OK` — 동작 튜닝 | 유지 |
| `config/agent/kernel-lifecycles/{init-polling-attempt,init-polling-timeout-sec,init-timeout-sec}` | 커널 기동 대기 정책 | `OK` — 동작 튜닝 | 유지. BA-7322이 start-service launch budget을 이 섹션에 추가 |
| `config/watcher/file-io-timeout` | watcher 파일 I/O 타임아웃 | `OK` — 동작 튜닝 | 유지 |
| `config/plugins/{metadata_app,stats_monitor,error_monitor,network_agent}/<name>/` | 플러그인별 파라미터 | `OK` — 플러그인 설정 | 유지 |
| `volumes`, `volumes/_mount`, `volumes/_fsprefix` | vfolder 마운트 기준 경로 | `OUT OF SCOPE` — 스토리지 토폴로지 | BA-7655 소관. 이관은 BA-7693, 스키마 폐기는 BA-7694 |

## 가속기 플러그인 — `config/plugins/accelerator/<name>/`

`BasePluginContext.init`(`common/plugin/__init__.py:177`)을 통해 `self.plugin_config`으로 전달된다.
아래는 키 집합이 가장 넓은 enterprise CUDA 플러그인 기준.

| etcd key | 용도 | 판정 | 처방 |
|---|---|---|---|
| `device_mask` | 열거 단계(`list_devices()`)에서 제외. 해당 디바이스는 용량·할당·지표·인벤토리 전부에서 사라진다 (아래 참조) | `WRONG AXIS` — 이 노드의 물리 하드웨어가 클러스터 전역 키에 있고, 구현이 플러그인마다 다섯 갈래 | **DB로 일반화.** 마스킹을 플러그인에서 걷어내 에이전트 계층으로 올리고, `devices` 인벤토리(BA-7176)의 제외 상태로 관리 |
| `allocation_mode` | 보고할 슬롯 이름을 결정: `cuda.device`(discrete) vs `cuda.shares`(fractional) | `WRONG AXIS` — 런타임 설정이 아닌 배포 파라미터. 바꾸면 보고 슬롯 이름이 바뀌므로 무중단 적용 불가 | 설정으로 유지하되 재시작 필요를 명시. 리소스 그룹 스코프가 맞는지 재검토 |
| `unit_mem`, `unit_proc` | fGPU 환산 기준 (`_get_share_raw`, `_share_to_spec`) | `WRONG AXIS` — 클러스터 할당 정책이 에이전트별 플러그인 키에 | 매니저 DB의 리소스 그룹 정책으로 이동 |
| `quantum_size` | fractional 할당 단위. `get_metadata()`의 표시 `round_length`와 `ScalingGroup.accelerator_quantum_size`(`api/gql_legacy/scaling_group.py:569`)의 근거 | `WRONG AXIS` — 리소스 그룹별 GraphQL 필드로 노출되면서 실제로는 전역 단일 값 | BA-5692 — 리소스 그룹 정책으로 이동 |
| `reserved_memory` | fractional일 때만. `CUDA_RESERVED_MEMORY`로 주입 | `WRONG AXIS` — 할당 정책 | `unit_mem`/`unit_proc`과 함께 이동 |
| `skip_hook` | hook 주입 생략. discrete에서만 허용 | `OK` — 배포 파라미터 | 유지 |
| `expose_real_gpu_name`, `masked_gpu_name` | `CUDA_MASK_GPU_NAME` / `CUDA_MASKED_GPU_NAME`으로 주입해 컨테이너 내 GPU 모델명을 가림 | `OK` — 동작 튜닝 | 유지 |

- **핫 리로드가 전무하다.** enterprise CUDA 플러그인은 `config_watch_enabled = False`이고, 나머지 모든 가속기 플러그인은 `update_plugin_config()`를 `pass`로 구현한다. 위 키는 전부 기동 시 1회만 읽히며, 이후 etcd 변경은 agent 재시작 없이는 반영되지 않는다.
- 읽는 키가 더 좁은 플러그인: `cuda_unified`는 `skip_hook`만, `mock`은 CUDA와 동일 집합, `cuda_open`·`atom`/`atom-plus`/`atom-max`·`warboy`·`rngd`·`ipu`·`lpu`·`n300`·`rebellions`는 `device_mask`만.

### `device_mask` — 유일하게 일반화가 필요한 키

마스킹은 `list_devices()`에서 `continue`로 걸러내므로 그 디바이스는 `CUDADevice` 객체 자체가 생성되지 않는다.
"컨테이너 생성에 쓰지 않는다"가 아니라 시스템에서 사라진다.

| 경로 | 결과 |
|---|---|
| `available_slots()` (`plugin.py:731-732`) | 매니저가 보고받는 용량에서 빠짐. 스케줄러가 존재를 모름 |
| alloc map `device_slots` | 항목 없음 → 할당 대상 아님 |
| `activate_devices()` → `_active_accelerators` | 라이선스 활성화 대상도 아님 |
| 노드·컨테이너 통계 (`:797`, `:907`) | 비활성이므로 `_check_active_by_device_id`에서 걸러짐 |
| `get_attached_devices()` | 커널 디바이스 리포트와 `kernels.attached_devices`에 안 나옴 |

호스트에서 떼는 것은 아니다. `nvidia-smi`로는 보이고, 디바이스 주입이 할당 기반이라 컨테이너에도 들어가지 않는다 — BAI가 모르는 GPU가 된다.

구현은 플러그인마다 갈라져 있다.

| 플러그인 | 설정 출처 | 키 공간 | 상태 |
|---|---|---|---|
| `cuda` (enterprise) | etcd `plugin_config` | 열거=NVML 서수 (`"0"`, MIG는 `"0:1"`), 통계=UUID | 내부 불일치 |
| `cuda_open` | etcd `plugin_config` | UUID | 정상 |
| `mock` | etcd `plugin_config` | UUID | 정상 |
| `atom`/`atom-plus`/`atom-max` | etcd `plugin_config` | — | 파싱 후 미사용 |
| `rocm`, `habana` | 로컬 TOML `local_config["device_mask"]` | UUID | 네임스페이스 없는 최상위 키 — 한 노드의 여러 플러그인이 공유 |

enterprise CUDA에 UUID를 적으면 열거에서 걸리지 않아 **할당은 그대로 되고 지표에서만 사라진다.** 경고도 없다.
서수는 재부팅·PCI 재열거 시 이동할 수 있어 고장 디바이스 격리라는 실제 용도에 맞지 않는다.

일반화 시 필요한 것:

- 플러그인은 열거 결과를 전부 보고하고 마스킹 코드를 제거한다. 에이전트 계층이 일괄 적용한다.
- 키 공간을 `AbstractComputeDevice.device_id` 하나로 고정한다 — BA-7176의 `devices.device_id`와 같은 값이다.
- BA-7176의 `devices` 인벤토리를 커널 RUNNING 전이가 아니라 **에이전트 열거로** 채워야 한다. 아니면 커널이 한 번도 뜨지 않은 디바이스는 가릴 수 없다.
- 제외 사유와 시각 컬럼이 있어야 "하드웨어 고장 격리"와 "운영자가 의도적으로 제외"를 구분할 수 있다.

나머지 가속기 설정은 전부 해당 가속기에 특화된 스키마라 DB로 옮길 수 없다. 로컬 TOML에 남긴다.

## SGROUP 스코프 해석

- 위의 모든 읽기가 기본 `MERGED` 스코프를 쓴다. `scope=ConfigScopes.SGROUP`을 넘기는 호출 지점은 없다. 따라서 위 인벤토리가 곧 SGROUP 도달 집합이다.
- `volumes/_mount`, `config/watcher/file-io-timeout`, `config/plugins/network_agent/<name>/`은 `AgentEtcdClientView`를 거치므로 **에이전트별** 리소스 그룹으로 해석된다. 나머지는 프로세스 단위 `AsyncEtcd`를 쓰므로 **primary 에이전트**의 그룹을 쓴다.
- 플러그인 설정 watch는 `GLOBAL` 고정(`common/plugin/__init__.py:201`)이므로, `sgroup/<name>` 아래 값은 기동 시 읽히고 이후 리로드되지 않는다.
- SGROUP 비대상: `ai/backend/service_discovery`(sweep 루프의 명시적 GLOBAL 읽기 — 설정이 아닌 레지스트리 데이터), agent-watcher 프로세스의 `config/watcher/token`(자체 GLOBAL 전용 클라이언트), 그리고 모든 쓰기(`scope=ConfigScopes.NODE`).

## 부수 발견

- `config/agent/max-container-count`는 agent 네임스페이스에 있지만 agent가 파싱하지 않는다. agent는 `config/agent` prefix를 통째로 읽고 `api`, `container-logs`, `kernel-lifecycles`만 꺼내 쓴다. 유일한 소비자는 매니저의 스케줄러 리포지토리(`repositories/scheduler/repository.py:334`).
- `config/session/hang-tolerance/threshold/{PREPARING,TERMINATING}`는 `ManagerUnifiedConfig`에 정의돼 있으나 소비하는 코드가 없다. PREPARING 단계는 이미지 pull을 포함하므로 agent의 pull 타임아웃에 대응하는 매니저 측 표현인데, 현재 죽은 키다.
