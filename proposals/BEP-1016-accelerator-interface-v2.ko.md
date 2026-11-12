# 가속기 인터페이스 v2

## 현재 설계

### `AbstractComputePlugin` API

| 함수                                                             | 역할                                                                                                                                   |
| ---------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| `list_devices()`                                                 | node 에서 사용 가능한 device 를 나열한다                                                                                               |
| `available_slots()`                                              | 설정에 따라 현재 사용 가능한 resource slot type 을 나열한다                                                                            |
| `get_metadata()`                                                 | resource slot 표시 메타데이터(사람이 읽는 이름 등)를 반환한다                                                                          |
| `extra_info()`                                                   | driver / compute API version 을 반환한다                                                                                               |
| `get_node_hwinfo()`                                              | node 의 hardware 고유 정보를 임의의 key-value map 으로 반환한다                                                                        |
| `create_alloc_map()`                                             | 설정에 따라 Backend.AI agent(discrete / fractional)나 plugin 이 제공할 수 있는 `AbstractAllocMap` 을 생성한다                          |
| `get_hooks(distro, arch)`                                        | 주어진 container image base distro 정보에 따라 library hook 으로 마운트할 추가 host file 을 조회한다                                   |
| `generate_docker_args(docker, device_alloc)`                     | Docker container 생성 API param 과 합칠 중첩 dict 를 생성한다                                                                          |
| `get_attached_devices(device_alloc)`                             | 주어진 allocation 에서 사용하는 device 목록을 메타데이터와 함께 추출한다                                                               |
| `get_docker_networks(device_alloc)`                              | 주어진 allocation 에 따라 연결할 Docker network 목록을 생성한다                                                                        |
| `generate_mounts(source_path, device_alloc)`                     | 마운트할 추가 host file 을 생성한다                                                                                                    |
| `generate_resource_data(device_alloc)`                           | container 의 `resource.txt` 에 넣을 문자열(KEY=VALUE 형태) 목록을 생성한다                                                            |
| `restore_from_container(container, alloc_map)`                   | `aiodocker.DockerContainer` object 에서 device allocation 을 복원한다                                                                  |
| `gather_{node,container,process}_metrics(stat_ctx[, target_id])` | node, container, process 별 processor 와 memory 사용률 같은 raw metric 값을 수집한다                                                   |

### `AbstractComputeDevice` Struct

새 제안과 현재 설계와의 비교를 포함한 내용은 [BEP-1000](https://github.com/lablup/beps/blob/main/proposals/BEP-1000-redefining-accelerator-metadata.md) 을 참고한다.

## 제안 설계

### 핵심 목표

* Docker 가 아닌 agent backend 에도 적용할 수 있게 한다
    - 기존 plugin API 상당수는 Docker 전용 용어와 API param 형식에 강하게 결합한다
* container lifecycle event 를 코드로 확장할 수 있게 한다
    - 예: node 에서 새 container 를 생성하거나 종료할 때 vendor 가 제공하는 device 관리 service 와 상호작용한다
* 일부 정보만 노출하는 중복되고 난잡한 method 를 정리한다
* 더 자세한 가속기 메타데이터를 제공한다 ([BEP-1000](https://github.com/lablup/beps/blob/main/proposals/BEP-1000-redefining-accelerator-metadata.md))

### `AbstractComputePlugin` API

| 함수                                                              | 역할                                                                                                                               |
| ----------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| `list_devices()`                                                  | node 에서 사용 가능한 device 를 나열한다                                                                                           |
| `configurable_slots()` ✨                                          | 가능한 모든 resource slot type 을 표시 메타데이터와 함께 나열한다                                                                  |
| `available_slots()` ✨                                             | 설정에 따라 현재 할당 가능한 resource slot type 을 나열한다                                                                        |
| `create_alloc_map()`                                              | 설정에 따라 `AbstractAllocMap` instance 를 생성한다                                                                                |
| `create_lifecycle_hook(workload, device_alloc)` ✨                 | `AbstractLifecycleHook` instance 를 생성한다                                                                                       |
| `alloc_to_devices(device_alloc)` ♻️                               | 주어진 allocation 에서 사용하는 device 목록을 메타데이터와 함께 추출한다                                                           |
| `gather_{node,workload,process}_metrics(stat_ctx[, target_id])` ♻ | node, workload(container 또는 process tree), process 별 processor 와 memory 사용률 같은 raw metric 값을 수집한다                  |
| `get_node_info()` ♻                                               | driver/runtime version 과 추가 hardware 정보 같은 node 정보를 구조화된 dataclass 로 조회한다                                       |

여기서 "workload" 는 agent backend 구현에 따라 container 또는 (native) process tree 를 의미한다.

### `AbstractComputeDevice` Struct

새 제안은 [BEP-1000](https://github.com/lablup/beps/blob/main/proposals/BEP-1000-redefining-accelerator-metadata.md) 을 참고한다.

### `AbstractLifecycleHook` API ✨

| 함수                               | 역할                                                                                                                                                                 |
| ---------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `__init__(workload, device_alloc)` | 주어진 workload 와 allocation 으로 instance 를 초기화한다                                                                                                           |
| `pre_create()`                     | workload 를 생성하기 전에 호출한다.<br>미리 정의한 예외를 발생시켜 생성을 거부하거나 (일시적으로) 실패시킬 수 있다.<br>`WorkloadConfig` struct 를 반환해야 한다. |
| `post_create()`                    | workload 를 생성한 뒤 호출한다.                                                                                                                                      |
| `pre_terminate()`                  | workload 를 종료하기 전에 호출한다.<br>종료를 취소할 수는 없지만 plugin 별 정리를 위해 종료를 미룰 수 있다.                                                          |
| `post_terminate()`                 | workload 를 종료한 뒤 호출한다.                                                                                                                                      |

이 새 API 는 이전 설계의 Docker 전용 argument/mount 생성 method 를 합치고 대체한다.

`AbstractLifecycleHook` 은 stateless 로 설계해야 하며, 필요하면 container 에서 추가 상태를 복원할 수 있어야 Backend.AI Agent 를 언제든 완전히 재시작할 수 있다.

### `Workload` Struct ✨

| 속성 | 내용                                               |
| --------- | -------------------------------------------------- |
| `id`      | 식별자(container ID 또는 leader process ID)        |
| `type`    | "container" \| "process_tree"                      |

### `WorkloadConfig` Struct ✨

| 속성             | 내용                                                                                                                                   |
| ---------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| `mounts`         | device file 과 library hook 을 포함한 host-to-workload mount 목록                                                                      |
| `env_vars`       | 환경 변수 key-value map                                                                                                                |
| `resource_data`  | workload 안에서 읽을 수 있는 `resource.txt` 에 추가되는 key-value map                                                                  |
| `networks`       | plugin 을 위해 연결할 network 이름 목록(network namespace 가 격리된 경우에만 적용)                                                     |
| `extra_gids`     | workload 에 적용할 Linux GID 목록                                                                                                      |
| `extra_syscalls` | workload 에서 추가로 허용할 Linux syscall 목록(AppArmor 나 Seccomp 처럼 syscall filter 가 있을 때만 적용)                              |

모든 field 는 선택 항목이다.

### 논의

* lifecycle hook 에서 in-place restart 와 relocated restart 를 처리하고 구분하는 방법
* lifecycle hook instance 에 stateless 설계를 강제하는 대신 managed state-store 인터페이스를 제공하는 방안
* "workload" 에 더 나은 이름
    - cluster 전체 scheduler 와 맞춰 "kernel" 을 계속 사용하는 방안
    - "session" 과의 관계도 함께 고려해야 한다
