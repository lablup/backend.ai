# SessionLauncher 테스트 시나리오

## 개요

실제 코드 동작을 바탕으로 `SessionLauncher` 의 테스트 시나리오를 정의한다.

launcher 는 다음을 처리한다.
1. **image pulling**: agent 에 `check_and_pull()` RPC 를 트리거한다(비동기).
2. **kernel 생성**: `create_kernels()` RPC 로 agent 에 kernel 을 생성한다.

**소스 파일:** `sokovan/scheduler/launcher/launcher.py`

---

## trigger_image_pulling 흐름

```python
async def trigger_image_pulling(sessions, image_configs):
    # 1. Group kernels by agent
    agent_image_configs: dict[AgentId, dict[str, ImageConfig]] = ...
    for session in sessions:
        for kernel in session.kernels:
            agent_image_configs[kernel.agent_id][kernel.image] = ...

    # 2. Trigger check_and_pull for each agent (parallel)
    async def pull_for_agent(agent_id, images):
        async with agent_client_pool.acquire(agent_id) as client:
            return await client.check_and_pull(images)

    await asyncio.gather(*pull_tasks, return_exceptions=True)
```

---

## start_sessions_for_handler 흐름

```python
async def start_sessions_for_handler(sessions, image_configs):
    # Start sessions concurrently with timeout
    for session in sessions:
        async with timeout(START_SESSION_TIMEOUT_SEC):
            await _start_single_session(session, image_configs)

async def _start_single_session(session, image_configs):
    # 1. Configure network setup
    network_setup = await _setup_network_configuration(session)

    # 2. Create SSH keypair
    ssh_keypair = await _create_cluster_ssh_keypair()

    # 3. Group kernels by agent
    kernels_by_agent: dict[AgentId, list[KernelBindingData]] = ...

    # 4. Create kernels on each agent
    for agent_id, kernels in kernels_by_agent.items():
        # Build KernelCreationConfig for each kernel
        await client.create_kernels(session_id, kernel_ids, kernel_configs, cluster_info, image_refs)
```

---

## 의존성(mock 대상)

- `agent_client_pool: AgentClientPool`
  - `acquire(agent_id)` → `AsyncContextManager[AgentClient]`
  - `AgentClient.check_and_pull(images)` → `Mapping[str, str]`
  - `AgentClient.create_kernels(...)` → `None`
  - `AgentClient.create_local_network(name)` → `None`
  - `AgentClient.assign_port()` → `int`
- `network_plugin_ctx: NetworkPluginContext`
  - `plugins[driver].create_network(identifier)` → `NetworkInfo`
- `repository: SchedulerRepository`
  - `update_session_network_id(session_id, network_name)` → `None`
  - `update_session_error_info(session_id, error_info)` → `None`

---

## image pulling 시나리오

### SC-LA-001: 모든 agent 의 image pulling 을 트리거한다

- **목적**: 고유한 agent 마다 check_and_pull 을 호출하는지 확인한다
- **의존성(mock):**
  - `agent_client.check_and_pull(images)`:
    - 반환: `{"image1": "pulled", "image2": "cached"}`
- **입력:**
  - agent `a1`, `a2` 에 kernel 을 가진 session 2개
- **실행:** `await launcher.trigger_image_pulling(sessions, image_configs)`
- **검증:**
  - `agent_client_pool.acquire.call_count` == 2(agent 마다 한 번)
  - agent 마다 올바른 image 로 `check_and_pull` 을 호출한다
- **분류**: `happy-path`

---

### SC-LA-002: agent 마다 image 를 중복 제거한다

- **목적**: 같은 image 를 agent 마다 한 번만 가져오는지 확인한다
- **입력:**
  - agent `a1` 에서 `image1` 을 사용하는 session 2개
- **실행:** `await launcher.trigger_image_pulling(sessions, image_configs)`
- **검증:**
  - `check_and_pull` 을 `{"image1": config}` 로 한 번 호출한다
- **분류**: `edge-case`

---

### SC-LA-003: 빈 session 목록은 아무것도 하지 않는다

- **목적**: 빈 입력에 agent 호출이 없는지 확인한다
- **입력:**
  - `sessions = []`
- **실행:** `await launcher.trigger_image_pulling([], {})`
- **검증:**
  - `agent_client_pool.acquire.assert_not_called()`
- **분류**: `edge-case`

---

### SC-LA-004: agent pull 실패가 다른 agent 를 차단하지 않는다

- **목적**: 일부 agent 실패를 허용하는지 확인한다
- **의존성(mock):**
  - `agent_client_pool.acquire(a1).check_and_pull()`:
    - 발생: `AgentError("Connection refused")`
  - `agent_client_pool.acquire(a2).check_and_pull()`:
    - 반환: `{"image1": "pulled"}`
- **입력:**
  - agent `a1`(실패)과 `a2`(성공)의 session
- **실행:** `await launcher.trigger_image_pulling(sessions, image_configs)`
- **검증:**
  - method 가 완료된다(`return_exceptions=True` 로 gather)
  - agent `a2` 의 pull 은 그대로 실행된다
- **분류**: `error-case`

---

## kernel 생성 시나리오

### SC-LA-005: kernel 하나인 session 을 시작한다

- **목적**: 기본 kernel 생성 흐름을 확인한다
- **의존성(mock):**
  - `agent_client.create_kernels(...)`:
    - 반환: `None`
  - `repository.update_session_network_id(...)`:
    - 반환: `None`
- **입력:**
  - agent `a1` 에 kernel 1개를 가진 session 하나
- **실행:** `await launcher.start_sessions_for_handler([session], image_configs)`
- **검증:**
  - `create_kernels` 를 한 번 호출한다
  - `KernelCreationConfig` 에 올바른 field 가 있다
  - repository 에서 session 의 network id 를 변경한다
- **분류**: `happy-path`

---

### SC-LA-006: kernel 이 여러 개인 session

- **목적**: kernel 이 여러 개인 session 에 cluster info 를 올바르게 전달하는지 확인한다
- **의존성(mock):**
  - `agent_client.create_kernels(...)`:
    - agent 마다 여러 kernel 로 호출한다
- **입력:**
  - agent 3개에 kernel 3개를 가진 session(`cluster_mode=MULTI_NODE`)
- **실행:** `await launcher.start_sessions_for_handler([session], image_configs)`
- **검증:**
  - `create_kernels` 를 3번 호출한다(agent 마다 한 번)
  - `ClusterInfo.size` == 3
  - `ClusterInfo.ssh_keypair` 가 채워진다
  - 환경 변수에 `BACKENDAI_CLUSTER_SIZE`, `BACKENDAI_CLUSTER_HOSTS` 가 포함된다
- **분류**: `happy-path`

---

### SC-LA-007: kernel 이 없는 session 은 에러를 발생시킨다

- **목적**: 잘못된 session 상태의 에러 처리를 확인한다
- **입력:**
  - `kernels = []` 인 session
- **실행:** `await launcher.start_sessions_for_handler([session], image_configs)`
- **검증:**
  - ValueError 가 발생한다
  - `repository.update_session_error_info` 를 호출한다
- **분류**: `error-case`

---

### SC-LA-008: timeout 을 두고 session 을 동시에 시작한다

- **목적**: 느린 session 의 timeout 처리를 확인한다
- **의존성(mock):**
  - session 1: `create_kernels` 가 1초 안에 반환한다
  - session 2: `create_kernels` 가 5분 걸린다(timeout 초과)
- **입력:**
  - session 2개
- **실행:** `await launcher.start_sessions_for_handler(sessions, image_configs)`
- **검증:**
  - session 1 이 완료된다
  - session 2 는 timeout 이 발생한다
  - timeout 을 warning 으로 기록한다
- **분류**: `error-case`

---

## network 설정 시나리오

### SC-LA-009: 단일 node 에서 kernel 이 여러 개인 session 의 VOLATILE network

- **목적**: 단일 node 에서 kernel 이 여러 개일 때 local network 를 생성하는지 확인한다
- **의존성(mock):**
  - `agent_client.create_local_network("bai-singlenode-{session_id}")`:
    - 반환: `None`
- **입력:**
  - `network_type=VOLATILE`, `cluster_mode=SINGLE_NODE`, kernel 3개를 가진 session
- **실행:** `_setup_network_configuration()` 을 통해 실행한다
- **검증:**
  - `create_local_network` 를 호출한다
  - `network_config["mode"]` == "bridge"
  - `network_config["network_name"]` 이 "bai-singlenode-" 로 시작한다
- **분류**: `happy-path`

---

### SC-LA-010: 여러 node 의 overlay network 를 위한 VOLATILE network

- **목적**: plugin 으로 overlay network 를 생성하는지 확인한다
- **의존성(mock):**
  - `config_provider.config.network.inter_container.default_driver = "overlay"`
  - `network_plugin.create_network(identifier)`:
    - 반환: `NetworkInfo(network_id="overlay-123", options={...})`
- **입력:**
  - `cluster_mode=MULTI_NODE` 인 session
- **실행:** `_setup_network_configuration()` 을 통해 실행한다
- **검증:**
  - `network_plugin.create_network.assert_called()`
  - plugin 이 제공한 network id 를 사용한다
- **분류**: `happy-path`

---

### SC-LA-011: SSH port mapping 을 사용하는 HOST network

- **목적**: kernel 이 여러 개인 HOST mode 의 port mapping 을 확인한다
- **의존성(mock):**
  - `agent_client.assign_port()`:
    - 반환: `12345`
- **입력:**
  - `network_type=HOST`, kernel 3개를 가진 session
- **실행:** `_setup_network_configuration()` 을 통해 실행한다
- **검증:**
  - `network_config["mode"]` == "host"
  - `ClusterSSHPortMapping` 이 채워진다
  - kernel 마다 `assign_port` 를 호출한다
- **분류**: `happy-path`

---

### SC-LA-012: PERSISTENT network 조회

- **목적**: PERSISTENT type 에 미리 생성한 network 를 사용하는지 확인한다
- **입력:**
  - `network_type=PERSISTENT`, `network_id=n1` 인 session
- **실행:** `_setup_network_configuration()` 을 통해 실행한다
- **검증:**
  - network 이름 형식: `persistent-{network_id}`
  - network 생성 호출이 없다
- **분류**: `happy-path`

---

### SC-LA-013: network plugin 이 없을 때의 에러

- **목적**: network driver 를 사용할 수 없을 때 에러가 발생하는지 확인한다
- **의존성(mock):**
  - `config_provider.config.network.inter_container.default_driver = "weave"`
  - `network_plugin_ctx.plugins = {}`(plugin 없음)
- **입력:**
  - `cluster_mode=MULTI_NODE` 인 session
- **실행:** `_setup_network_configuration()` 을 통해 실행한다
- **검증:**
  - 도움이 되는 메시지와 함께 KeyError 가 발생한다
  - 에러에 사용할 수 있는 plugin 목록이 담긴다
- **분류**: `error-case`

---

## KernelCreationConfig 시나리오

### SC-LA-014: KernelCreationConfig 에 필요한 field 가 모두 있다

- **목적**: config 구조가 agent 의 기대와 맞는지 확인한다
- **입력:**
  - field 를 모두 채운 session
- **실행:** `_start_single_session()` 을 통해 실행한다
- **검증:**
  - config 에 `image`, `kernel_id`, `session_id`, `resource_slots` 가 있다
  - config 에 `cluster_mode`, `cluster_role`, `cluster_idx`, `cluster_hostname` 이 있다
  - config 에 `BACKENDAI_*` 변수를 담은 `environ` 이 있다
  - config 에 `mounts`, `idle_timeout`, `preopen_ports` 가 있다
- **분류**: `happy-path`

---

### SC-LA-015: 환경 변수를 올바르게 채운다

- **목적**: `BACKENDAI_*` 환경 변수를 올바르게 설정하는지 확인한다
- **입력:**
  - user 정보와 cluster 구성을 가진 session
- **실행:** `_start_single_session()` 을 통해 실행한다
- **검증:**
  - `environ["BACKENDAI_USER_UUID"]` == str(user_uuid)
  - `environ["BACKENDAI_SESSION_ID"]` == str(session_id)
  - `environ["BACKENDAI_CLUSTER_SIZE"]` == str(kernel_count)
  - kernel 마다 `environ["BACKENDAI_KERNEL_ID"]` 가 있다
  - kernel 마다 `environ["BACKENDAI_CLUSTER_ROLE"]` 가 있다
- **분류**: `happy-path`

---

## SSH keypair 생성

### SC-LA-016: cluster 용 SSH keypair 생성

- **목적**: cluster 통신용 RSA keypair 를 생성하는지 확인한다
- **실행:** `await launcher._create_cluster_ssh_keypair()`
- **검증:**
  - `keypair.private_key` 가 PEM 형식이다
  - `keypair.public_key` 가 OpenSSH 형식이다
  - public key 가 `work@cluster.backend.ai.local` 로 끝난다
- **분류**: `happy-path`

---

## 에러 처리 시나리오

### SC-LA-017: agent 에러가 session error info 를 변경한다

- **목적**: session status_data 에 에러를 기록하는지 확인한다
- **의존성(mock):**
  - `agent_client.create_kernels(...)`:
    - 발생: `AgentError("Container creation failed")`
  - `repository.update_session_error_info(session_id, error_info)`:
    - 반환: `None`
- **입력:**
  - kernel 생성 중 실패하는 session
- **실행:** `_start_single_session()` 을 통해 실행한다
- **검증:**
  - `update_session_error_info.assert_called()`
  - error info 에 예외 내용이 담긴다
  - session 을 종료하지 않는다(timeout 감지가 처리한다)
- **분류**: `error-case`

---

### SC-LA-018: config 에 image 가 없음

- **목적**: image 구성이 없을 때 에러가 발생하는지 확인한다
- **의존성(mock):**
  - `image_configs = {}`(kernel 의 image 가 없음)
- **입력:**
  - 해석하지 못한 image 를 사용하는 kernel 을 가진 session
- **실행:** `_start_single_session()` 을 통해 실행한다
- **검증:**
  - image 가 없으면 ValueError 가 발생한다
  - 에러를 기록한다
- **분류**: `error-case`
