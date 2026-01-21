# SessionLauncher Test Scenarios

## Overview

Test scenarios for `SessionLauncher` based on actual code behavior.

The Launcher handles:
1. **Image Pulling**: Triggers `check_and_pull()` RPC to agents (asynchronous)
2. **Kernel Creation**: Creates kernels on agents via `create_kernels()` RPC

**Source Files:** `sokovan/scheduler/launcher/launcher.py`

---

## trigger_image_pulling Flow

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

## start_sessions_for_handler Flow

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

## Dependencies (Mock Targets)

- `agent_client_pool: AgentClientPool`
  - `acquire(agent_id)` -> `AsyncContextManager[AgentClient]`
  - `AgentClient.check_and_pull(images)` -> `Mapping[str, str]`
  - `AgentClient.create_kernels(...)` -> `None`
  - `AgentClient.create_local_network(name)` -> `None`
  - `AgentClient.assign_port()` -> `int`
- `network_plugin_ctx: NetworkPluginContext`
  - `plugins[driver].create_network(identifier)` -> `NetworkInfo`
- `repository: SchedulerRepository`
  - `update_session_network_id(session_id, network_name)` -> `None`
  - `update_session_error_info(session_id, error_info)` -> `None`

---

## Image Pulling Scenarios

### SC-LA-001: Trigger Image Pulling for All Agents

- **Purpose**: Verify check_and_pull is called for each unique agent
- **Dependencies (Mock):**
  - `agent_client.check_and_pull(images)`:
    - Returns: `{"image1": "pulled", "image2": "cached"}`
- **Input:**
  - 2 sessions with kernels on agents `a1` and `a2`
- **Execution:** `await launcher.trigger_image_pulling(sessions, image_configs)`
- **Verification:**
  - `agent_client_pool.acquire.call_count` == 2 (one per agent)
  - `check_and_pull` called with correct images per agent
- **Classification**: `happy-path`

---

### SC-LA-002: Deduplicate Images Per Agent

- **Purpose**: Verify same image is only pulled once per agent
- **Input:**
  - 2 sessions using `image1` on agent `a1`
- **Execution:** `await launcher.trigger_image_pulling(sessions, image_configs)`
- **Verification:**
  - `check_and_pull` called once with `{"image1": config}`
- **Classification**: `edge-case`

---

### SC-LA-003: Empty Session List Does Nothing

- **Purpose**: Verify no agent calls for empty input
- **Input:**
  - `sessions = []`
- **Execution:** `await launcher.trigger_image_pulling([], {})`
- **Verification:**
  - `agent_client_pool.acquire.assert_not_called()`
- **Classification**: `edge-case`

---

### SC-LA-004: Agent Pulling Failure Doesn't Block Others

- **Purpose**: Verify partial agent failure is tolerated
- **Dependencies (Mock):**
  - `agent_client_pool.acquire(a1).check_and_pull()`:
    - Raises: `AgentError("Connection refused")`
  - `agent_client_pool.acquire(a2).check_and_pull()`:
    - Returns: `{"image1": "pulled"}`
- **Input:**
  - Sessions on agents `a1` (fails) and `a2` (succeeds)
- **Execution:** `await launcher.trigger_image_pulling(sessions, image_configs)`
- **Verification:**
  - Method completes (gather with return_exceptions=True)
  - Agent `a2` pulling still executed
- **Classification**: `error-case`

---

## Kernel Creation Scenarios

### SC-LA-005: Start Single Kernel Session

- **Purpose**: Verify basic kernel creation flow
- **Dependencies (Mock):**
  - `agent_client.create_kernels(...)`:
    - Returns: `None`
  - `repository.update_session_network_id(...)`:
    - Returns: `None`
- **Input:**
  - Single session with 1 kernel on agent `a1`
- **Execution:** `await launcher.start_sessions_for_handler([session], image_configs)`
- **Verification:**
  - `create_kernels` called once
  - `KernelCreationConfig` contains correct fields
  - Network ID updated in repository
- **Classification**: `happy-path`

---

### SC-LA-006: Multi-Kernel Cluster Session

- **Purpose**: Verify cluster info is correctly passed for multi-kernel sessions
- **Dependencies (Mock):**
  - `agent_client.create_kernels(...)`:
    - Called with multiple kernels per agent
- **Input:**
  - Session with 3 kernels on 3 agents (cluster_mode=MULTI_NODE)
- **Execution:** `await launcher.start_sessions_for_handler([session], image_configs)`
- **Verification:**
  - `create_kernels` called 3 times (once per agent)
  - `ClusterInfo.size` == 3
  - `ClusterInfo.ssh_keypair` populated
  - Environment variables include `BACKENDAI_CLUSTER_SIZE`, `BACKENDAI_CLUSTER_HOSTS`
- **Classification**: `happy-path`

---

### SC-LA-007: Session Without Kernels Raises Error

- **Purpose**: Verify error handling for invalid session state
- **Input:**
  - Session with `kernels = []`
- **Execution:** `await launcher.start_sessions_for_handler([session], image_configs)`
- **Verification:**
  - ValueError raised
  - `repository.update_session_error_info` called
- **Classification**: `error-case`

---

### SC-LA-008: Concurrent Session Start with Timeout

- **Purpose**: Verify timeout handling for slow sessions
- **Dependencies (Mock):**
  - Session 1: `create_kernels` returns in 1 second
  - Session 2: `create_kernels` takes 5 minutes (exceeds timeout)
- **Input:**
  - 2 sessions
- **Execution:** `await launcher.start_sessions_for_handler(sessions, image_configs)`
- **Verification:**
  - Session 1 completes
  - Session 2 times out
  - Timeout logged as warning
- **Classification**: `error-case`

---

## Network Setup Scenarios

### SC-LA-009: VOLATILE Network for Single Node Multi-Kernel

- **Purpose**: Verify local network is created for single node multi-kernel
- **Dependencies (Mock):**
  - `agent_client.create_local_network("bai-singlenode-{session_id}")`:
    - Returns: `None`
- **Input:**
  - Session with `network_type=VOLATILE`, `cluster_mode=SINGLE_NODE`, 3 kernels
- **Execution:** Via `_setup_network_configuration()`
- **Verification:**
  - `create_local_network` called
  - `network_config["mode"]` == "bridge"
  - `network_config["network_name"]` starts with "bai-singlenode-"
- **Classification**: `happy-path`

---

### SC-LA-010: VOLATILE Network for Multi-Node Overlay

- **Purpose**: Verify overlay network is created via plugin
- **Dependencies (Mock):**
  - `config_provider.config.network.inter_container.default_driver = "overlay"`
  - `network_plugin.create_network(identifier)`:
    - Returns: `NetworkInfo(network_id="overlay-123", options={...})`
- **Input:**
  - Session with `cluster_mode=MULTI_NODE`
- **Execution:** Via `_setup_network_configuration()`
- **Verification:**
  - `network_plugin.create_network.assert_called()`
  - Network ID from plugin is used
- **Classification**: `happy-path`

---

### SC-LA-011: HOST Network with SSH Port Mapping

- **Purpose**: Verify port mapping for multi-kernel HOST mode
- **Dependencies (Mock):**
  - `agent_client.assign_port()`:
    - Returns: `12345`
- **Input:**
  - Session with `network_type=HOST`, 3 kernels
- **Execution:** Via `_setup_network_configuration()`
- **Verification:**
  - `network_config["mode"]` == "host"
  - `ClusterSSHPortMapping` populated
  - `assign_port` called for each kernel
- **Classification**: `happy-path`

---

### SC-LA-012: PERSISTENT Network Lookup

- **Purpose**: Verify pre-created network is used for PERSISTENT type
- **Input:**
  - Session with `network_type=PERSISTENT`, `network_id=n1`
- **Execution:** Via `_setup_network_configuration()`
- **Verification:**
  - Network name format: `persistent-{network_id}`
  - No network creation calls
- **Classification**: `happy-path`

---

### SC-LA-013: No Network Plugin Error

- **Purpose**: Verify error when network driver is unavailable
- **Dependencies (Mock):**
  - `config_provider.config.network.inter_container.default_driver = "weave"`
  - `network_plugin_ctx.plugins = {}` (no plugins)
- **Input:**
  - Session with `cluster_mode=MULTI_NODE`
- **Execution:** Via `_setup_network_configuration()`
- **Verification:**
  - KeyError raised with helpful message
  - Error contains list of available plugins
- **Classification**: `error-case`

---

## KernelCreationConfig Scenarios

### SC-LA-014: KernelCreationConfig Contains All Required Fields

- **Purpose**: Verify config structure matches agent expectations
- **Input:**
  - Session with all fields populated
- **Execution:** Via `_start_single_session()`
- **Verification:**
  - Config contains: `image`, `kernel_id`, `session_id`, `resource_slots`
  - Config contains: `cluster_mode`, `cluster_role`, `cluster_idx`, `cluster_hostname`
  - Config contains: `environ` with `BACKENDAI_*` variables
  - Config contains: `mounts`, `idle_timeout`, `preopen_ports`
- **Classification**: `happy-path`

---

### SC-LA-015: Environment Variables Correctly Populated

- **Purpose**: Verify BACKENDAI_* environment variables are set correctly
- **Input:**
  - Session with user info and cluster configuration
- **Execution:** Via `_start_single_session()`
- **Verification:**
  - `environ["BACKENDAI_USER_UUID"]` == str(user_uuid)
  - `environ["BACKENDAI_SESSION_ID"]` == str(session_id)
  - `environ["BACKENDAI_CLUSTER_SIZE"]` == str(kernel_count)
  - `environ["BACKENDAI_KERNEL_ID"]` per kernel
  - `environ["BACKENDAI_CLUSTER_ROLE"]` per kernel
- **Classification**: `happy-path`

---

## SSH Keypair Generation

### SC-LA-016: SSH Keypair Generation for Cluster

- **Purpose**: Verify RSA keypair is generated for cluster communication
- **Execution:** `await launcher._create_cluster_ssh_keypair()`
- **Verification:**
  - `keypair.private_key` is in PEM format
  - `keypair.public_key` is in OpenSSH format
  - Public key ends with `work@cluster.backend.ai.local`
- **Classification**: `happy-path`

---

## Error Handling Scenarios

### SC-LA-017: Agent Error Updates Session Error Info

- **Purpose**: Verify error is recorded in session status_data
- **Dependencies (Mock):**
  - `agent_client.create_kernels(...)`:
    - Raises: `AgentError("Container creation failed")`
  - `repository.update_session_error_info(session_id, error_info)`:
    - Returns: `None`
- **Input:**
  - Session that fails during kernel creation
- **Execution:** Via `_start_single_session()`
- **Verification:**
  - `update_session_error_info.assert_called()`
  - Error info contains exception details
  - Session is not terminated (handled by timeout detection)
- **Classification**: `error-case`

---

### SC-LA-018: Image Not Found in Config

- **Purpose**: Verify error when image configuration is missing
- **Dependencies (Mock):**
  - `image_configs = {}` (missing image for kernel)
- **Input:**
  - Session with kernel using unresolved image
- **Execution:** Via `_start_single_session()`
- **Verification:**
  - ValueError raised for missing image
  - Error logged
- **Classification**: `error-case`
