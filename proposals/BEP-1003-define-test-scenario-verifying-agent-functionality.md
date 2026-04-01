---
Author: Bokeum Kim (bkkim@lablup.com)
Status: Draft
Created:
Created-Version:
Target-Version:
Implemented-Version:
---

# Agent Operations

---

## `update_scaling_group`
* **Description**: Updates the scaling group configuration for the agent.
* **Input Value**:
    * `scaling_group: str`: name of scaling-group
* **Response Value**:
    * `None` (implicitly on success).
* **Side Effects**:
    * Reads the agent's TOML configuration file.
    * Modifies the `agent.scaling-group` value in the configuration and Update file
    * Creates a backup of the original configuration file (e.g., `agent.toml.bak`).
    * Updates the `scaling-group` in the agent's in-memory `local_config`.

---

## `ping`
* **Description**: A simple ping RPC to check connectivity.
* **Input Value**: 
    * `msg: str`: ping message
* **Response Value**:
    * `str`: The original message sent in the request.

---

## `gather_hwinfo`
* **Description**: Collects hardware metadata from the agent's host.
* **Response Value**:
    * `Mapping[str, HardwareMetadata]`: A dictionary containing various hardware details (e.g., CPU, GPU, memory).

---

## `ping_kernel`
* **Description**: Pings a specific running kernel to check its responsiveness.
* **Input Value**:
    * `kernel_id: str`: Id of kernel that wants to send ping
* **Response Value**:
    * `dict[str, float] | None`: A dictionary with timing/status information if the kernel responds, otherwise `None`.

---

## `check_and_pull`
* **Description**: Checks if specified container images exist locally and initiates a background task to pull them if they don't or if an update is needed.
* **Input Value**:
    * `image_configs: Mapping[str, ImageConfig]`: 
* **Response Value**:
    * `dict[str, str]`: A dictionary mapping image names to the background task IDs responsible for pulling them.
* **Side Effects**:
    * (check_and_pull):
        * (DockerAgent.check_image)
            * (docker.images.inspect): Checks whether the image exists and acts as follows, depending on AutoPullBehavior.
                * (TAG): If the image exists locally, always returns False so the local image is used.
                * (DIGEST): Uses the local image only when it exists and its ID matches the supplied image_id; otherwise returns False to trigger a pull.
                * (NONE): Throws an exception if the image is not found locally.
        * (If a pull is required → emits ImagePullStartedEvent)
            * (DockerAgent.pull_image):
                * (docker.images.pull): Pulls the image specified by image_id.
                * (on success → emits ImagePullFinishedEvent)
                * (on failure → emits ImagePullFailedEvent)
        * (If no pull is required → emits ImagePullFinishedEvent)

---

## `create_kernels`
* **Description**: Creates one or more new computation kernels (containers).
* **Input Value**: 
    * `raw_session_id: str` 
    * `raw_kernel_ids: Sequence[str]`
    * `raw_configs: Sequence[dict]`
    * `raw_cluster_info: dict`
    * `kernel_image_refs: dict[KernelId, ImageRef]`
* **Response Value**:
    * `list[dict]`: A list of dictionaries, each containing information about a successfully created kernel (e.g., ID, host, ports, container ID, resource specs).
    * Raises an exception if any kernel creation fails (either the first error or a `TaskGroupError` for multiple failures).
* **Side Effects**:
    * (create_kernels): Applies a semaphore equal to `kernel-creation-concurrency` and
        executes coroutines that create kernels via `asyncio.gather`.
        * (DockerAgent.init_kernel_context):
            * If the image label `ai.backend.base-distro` is present, that value is used
                as the distro.
            * If not, the distro is loaded from the `"image:{image_id}:distro"` cache in
                `redis_stat_pool`, if available.
            * If the cache is missing, a container is created with
                `aiodocker.containers.create` to run `ldd --version`; the distro is then
                read from the container log and cached in `redis_stat_pool`.
        * (DockerAgent.check_image): Uses `aiodocker.images.inspect` to decide whether
            the specified image needs to be pulled or is already present.
        * (DockerAgent.pull_image): Pulls the image via `aiodocker.images.pull`.
        * (DockerAgent.prepare_resource_spec): Loads the kernel resource spec from `resource.txt`
            under `config_dir`.
        * (DockerAgent.prepare_scratch):
            * If the host platform is `linux`
                * When `scratch_type` is `memory`
                    * Creates a filesystem in the new kernel’s `scratch_dir`
                        (spawns a subprocess to mount a tmpfs).
                    * Creates a filesystem in the new kernel’s `tmp_dir`
                        (spawns a subprocess to mount a tmpfs).
                * When `scratch_type` is `hostfile`, creates a loop-back file in the new
                    kernel’s `scratch_root`.
            * On non-Linux hosts, simply `mkdir`s the `scratch_dir`.
            * Creates `config_dir` and `work_dir` under `scratch_dir` with permission
                `0o755`.
        * (_clone_dotfiles): Copies the following `pkg_resources` files under
            `ai.backend.runner`:
            * `jupyter-custom.css`
            * `logo.svg`
            * `roboto.ttf`
            * `roboto-italic.ttf`
            * `.bashrc`
            * `.bash_profile`
            * `.zshrc`
            * `.vimrc`
            * `.tmux.conf`
            * `.jupyter/custom`
            * `.jupyter/custom/custom.css`
            * `.jupyter/custom/logo.svg`
            * `.jupyter/custom/roboto.ttf`
            * `.jupyter/custom/roboto-italic.ttf`
        * (_clone_dotfiles): If `euid` is 0, changes the copied files’ `uid` and `gid`
            to `kernel-uid` and `kernel-gid`.
        * (DockerKernelCreationContext.prepare_ssh)
            * Writes the provided SSH key to `config_dir/ssh/id_cluster`.
            * Writes the provided SSH public key to `config_dir/ssh/id_cluster.pub`.
            * If `uid-match` (`KernelFeatures.UID_MATCH`) is set in `kernel_features`,
                changes ownership of the written SSH files to `kernel-uid` and
                `kernel-gid`.
            * If `cluster_info` contains `cluster_ssh_port_mapping`, writes it to
                `config_dir/ssh/port-mapping.json`.
        * (DockerKernelCreationContext.mount_krunner)
            * Bind-mounts `runner/su-exec.{arch}.bin` to `/opt/kernel/su-exec`.
            * Bind-mounts `runner/libbaihook.*.{arch}.so` to
                `/opt/kernel/libbaihook.so`.
            * Bind-mounts `runner/dropbearmulti.{arch}.bin` to
                `/opt/kernel/dropbearmulti`.
            * Bind-mounts `runner/sftp-server.{arch}.bin` to
                `/opt/kernel/sftp-server`.
            * Bind-mounts `runner/tmux.{arch}.bin` to `/opt/kernel/tmux`.
            * If `sandbox-type` is `"jail"`, bind-mounts `runner/jail.*.{arch}.bin` to
                `/opt/kernel/jail`.
            * Bind-mounts `runner/extract_dotfiles.py` to
                `/opt/kernel/extract_dotfiles.py`.
            * Bind-mounts `runner/entrypoint.sh` to `/opt/kernel/entrypoint.sh`.
            * Bind-mounts `runner/fantompass.py` to `/opt/kernel/fantompass.py`.
            * Bind-mounts `runner/hash_phrase.py` to `/opt/kernel/hash_phrase.py`.
            * Bind-mounts `runner/words.json` to `/opt/kernel/words.json`.
            * Bind-mounts `runner/DO_NOT_STORE_PERSISTENT_FILES_HERE.md` to
                `/home/work/DO_NOT_STORE_PERSISTENT_FILES_HERE.md`.
            * If the target libc is `musl`, bind-mounts `runner/terminfo.alpine3.8` to
                `/home/work/.terminfo`.
            * Volume-mounts the directory set in `local_config.container.krunner_volume`
                to `/opt/backend.ai`.
            * Sets the `LD_PRELOAD` environment variable to
                `/opt/kernel/libbaihook.so` so that `libbaihook.so` loads first.
            * Bind-mounts the `ai/backend/kernel` package to
                `/opt/backend.ai/lib/python{pyver}/site-packages/ai/backend/kernel`.
            * Bind-mounts the `ai/backend/helpers` package to
                `/opt/backend.ai/lib/python{pyver}/site-packages/ai/backend/helpers`.
            * Calls `apply_accelerator_allocation` for each accelerator plugin.
                * Each plugin receives the aiodocker object and generates Docker args
                    for resource isolation via `generate_docker_args`.
            * Calls each plugin’s `generate_accelerator_mounts`, adding the returned
                mounts to `resource_spec.mounts`.
            * If a plugin needs extra hooks, bind-mounts `/opt/kernel/{hook}.so` and
                appends its path to `LD_PRELOAD`.
        * (AbstractComputePlugin.get_attached_devices): Calls `get_attached_devices` on each plugin to obtain
            device info to pass to `KernelCreationContext`.
        * (DockerAgent.load_model_definition): Executed only for inference models.
            * Reads the image’s `CMD` via `aiodocker.images.get` (deprecated; should be
                replaced with `inspect`).
            * Reads the model definition from `model_definition_yaml`.
        * (restart_kernel__store_config): Serializes the new kernel configuration to
            `config/kconfig.dat` in pickle format.
        * (restart_kernel__store_config): Serializes the new cluster configuration to
            `config/cluster.json` in pickle format.
        * (DockerKernelCreationContext.prepare_container)
            * Creates a user bootstrap script `/bootstrap.sh` under the work directory.
                * If `KernelFeatures.UID_MATCH`, chowns it to `kernel-uid/gid`.
            * Writes `environ.txt` under `config_dir` containing:
                * The provided `environ`.
                * The `self.computer_docker_args["Env"]` entry.
            * Writes `resource.txt` under `config_dir` containing:
                * The output of `resource_spec.write_to_file`.
                * Key–value pairs from each accelerator’s
                    `instance.generate_resource_data`.
            * If `internal_data.docker_credentials` exists, saves it to
                `config_dir/docker-creds.json`.
            * Copies `environ.txt` to `environ_base.txt` and `resource.txt` to
                `resource_base.txt` in `config_dir`.
            * If `internal_data.ssh_keypair` exists and `/home/work/.ssh` is not
                mounted:
                * Creates `.ssh` (0700) under the work dir and creates
                    `authorized_keys`, `id_rsa`, and `id_container` (0600).
                * If `KernelFeatures.UID_MATCH`, chowns `.ssh` and its files to
                    `kernel-uid/gid`.
            * Processes each path in `internal_data.dotfiles`:
                * Absolute paths → unchanged.
                * Paths starting with `"/home/"` → into `scratch_dir`.
                * Others → into the work directory.
                * Writes each dotfile to the determined path and `chmod`s with
                    `dotfile["perm"]`.
                * If `KernelFeatures.UID_MATCH`, chowns each dotfile and its parent
                    directories to `kernel-uid/gid`.
        * (DockerKernelCreationContext.start_container)
            * If `HostConfig.NetworkMode` is `host`, writes intrinsic port info
                (`replin`, `replout`, `sshd`, `ttyd`) to
                `config_dir/intrinsic-ports.json`.
            * Additionally reads `agent-docker-container-opts.json` from the following
                paths and applies them as container options:
                * `/etc/backend.ai`
                * `.config/backend.ai`
                * `~/.config/backend.ai`
            * Creates the container via `aiodocker.containers.create`.
            * Reopens `config_dir/resource.txt` and records:
                * `container_id`
                * Additional resource info fetched from plugins via
                    `generate_resource_data`.
            * Starts the container via `aiodocker.containers.start`.
            * If `sudo_session_enabled`, executes
                `sh -c "mkdir -p /etc/sudoers.d && echo 'work ALL=(ALL:ALL) NOPASSWD:ALL' > /etc/sudoers.d/01-bai-work"`
                inside the container to enable password-less sudo.
            * Calls each accelerator’s `get_docker_networks`, obtains DockerNetwork
                objects via `aiodocker.networks.get`, and connects them.
            * Calls `container.port` to retrieve the container’s port mappings.
            * Calls the network plugin’s `get_capabilities` to fetch network features.
                * If the `GLOBAL` capability exists, calls `expose_ports` to expose the
                    ports to the public network after the container starts.
            * On an exception in `_clean_scratch`, calls
                `_rollback_container_creation` to clean up `scratch` and accelerator
                resources.
        * (AbstractKernel.init)
            * (DockerKernel.create_code_runner): Creates an `AbstractCodeRunner`
                (`DockerCodeRunner`) object.
        * (AbstractKernel.check_status)
            * Sends a `status` message to the runner to check the kernel runner’s
                state.
        * (KernelObjectType.get_service_apps)
            * Sends a `get-apps` message to the runner to retrieve service apps.
        * (DockerAgent.start_and_monitor_model_service_health): If the restarted kernel’s
            `session_type` is `INFERENCE`
            * (AbstractKernel.start_model_service)
                * Sends a `start-model-service` message to the runner to start the
                    model service.
            * (ModelServiceStatusEvent) is emitted:
                * (_dispatch_model_serving_events)
                * (handle_model_service_status_update)
                * (update_appproxy_endpoint_routes): Reads the wsproxy address for the
                    scaling group from the DB and sends a POST request to
                    `f"{wsproxy_addr}/v2/endpoints/{endpoint.id}"` to update the
                    endpoint address in the `endpoints` table.
        * (KernelStartedEvent) is emitted:
            * (mark_kernel_running): Updates the kernel’s status in the DB to
                `KernelStatus.RUNNING`.

---

## `destroy_kernel`
* **Description**: Destroys a specific computation kernel (container).
* **Input Value**: 
    * `kernel_id: str`
    * `session_id: str`
    * `reason: Optional[KernelLifecycleEventReason]`
    * `suppress_events: bool`
* **Response Value**:
    * The result of an `asyncio.Future` (typically `None` on success, or an exception if destruction fails).
* **Side Effects**:
    **Agent Side**:
        * (inject_container_lifecycle_event):
            * (_handle_destroy_event):
                * Acquires `registry_lock`; if the kernel is already terminated, calls
                    `reconstruct_resource_usage` and emits `KernelTerminatedEvent`.
                * Otherwise, calls `AbstractAgent.destroy_kernel` to terminate the kernel.
                    * (aiodocker.containers.stop):
                        * Stops the container by `container_id`.
                    * If the kernel is already dead or a 404 error occurs, calls
                        `reconstruct_resource_usage`.
                    * (reconstruct_resource_usage):
                        * (DockerAgent.enumerate_containers): Identifies containers to
                            iterate over.
                            * (aiodocker.containers.list): Lists containers.
                            * (get_kernel_id_from_container): Extracts the kernel ID from
                                the container name. If the container label
                                `ai.backend.owner` equals `DockerAgent.id`, calls
                                `aiodocker.containers.show` to fetch container info and
                                includes it in the iteration set.
                        * Invokes `restore_from_container` on each accelerator to reset
                            `alloc_map`, then reloads `alloc_map` from `resource.txt`
                            under `scratches`.
                    * (AbstractCodeRunner.close()):
                        * Cleans up resources such as sockets and tasks.
            * Places a `ContainerLifecycleEvent` in `container_lifecycle_queue` and
                processes it in `process_lifecycle_events`.
            * (_handle_clean_event):
                * Waits for the `destruction_task` in `_ongoing_destruction_tasks` to
                    finish, then calls the kernel’s code-runner `close`.
                * Calls `DockerAgent.clean_kernel` to clean up the kernel.
                * Emits `AgentErrorEvent` if an exception occurs.
                * Calls `AbstractKernel.close` (no-op in `DockerAgent`).
                * If the terminated kernel’s `kernel_id` is in `restart_tracker`, sets
                    the corresponding Event; otherwise emits `KernelTerminatedEvent`.
                * Sets `.AbstractKernel.clean_event` and `ev.done_future` to signal that
                    the kernel has been cleaned.
            * (collect_logs):
                * Writes collected container logs to
                    `containerlog.{container_id}` in `redis_stream_pool`.
            * If the kernel has a domain-socket proxy, calls `proxy_server.wait_close`.
            * (aiodocker.containers.delete): Deletes the container.
            * (_clean_scratch): Unmounts filesystems at the `scratch` and `tmp_dir`
                paths, removes them with `rmtree`, deletes the `scratch_root` loop
                filesystem, and—if a network plugin is configured—calls the plugin’s
                `leave_network` to clean up networking.
    **Manager side**:
        * (handle_kernel_terminated): Invoked on receipt of `KernelTerminatedEvent`.
        * (mark_kernel_terminated):
            * (recalc_agent_resource_occupancy):
                * Updates `redis_stat.keypair.concurrency_used.{access_key}`.
                * Updates `redis_stat.keypair.sftp_concurrency_used.{access_key}`.
            * (recalc_concurrency_used): Updates the kernel table.
        * (session_lifecycle_mgr.register_status_updatable_session): PUSHes sessions
            that need updating to the set `redis_obj.session_status_update`.
        * Emits `DoUpdateSessionStatusEvent`.
        * (SchedulerDispatcher.update_session_status): Handles
            `DoUpdateSessionStatusEvent`.
        * (update_session_status): Retrieves session-status update events from the set
            `redis_obj.session_status_update` and updates session statuses.
        * (transit_session_status): Updates the session status in the `sessions` table.
        * (_post_status_transition): Emits `SessionTerminatedEvent`.
        * (handle_session_terminated): Handles `SessionTerminatedEvent`.
        * (AgentRegistry.clean_session):
            * For `SINGLE_NODE`, calls `destroy_local_network`.
            * For `MULTI_NODE`, calls the network plugin’s `destroy_network`.
        * (invoke_session_callback): Called when a terminated session is an inference
            session.
            * Updates the `routings` table.
            * (agent_registry.update_appproxy_endpoint_routes): Updates the `endpoints`
                table by sending a POST request to
                `{wsproxy_addr}/v2/endpoints/{endpoint.id}`.
        * (_clear_error): If the removed session has a `callback_url`:
            * (_make_session_callback): Sends a session-lifecycle event to
                `{callback_url}` to notify that the session has terminated.

---

## `interrupt_kernel`
* **Description**: Sends an interrupt signal to a running kernel.
* **Input Value**: 
    * `kernel_id: str`
* **Response Value**:
    * `None`.
* **Side Effects**:
    * (DockerAgent.interrupt_kernel)
    * (DockerKernel.interrupt_kernel)
    * (AbstractCodeRunner.feed_interrupt):
        * Sends an `interrupt` message to the runner.
    * (BaseRunner.main_loop):
        * When an `interrupt` message is received, calls `self._interrupt` to send a `SIGINT` signal to its subprocess.
        * If the BaseRunner has a `kernel_mgr` attribute, calls `AsyncKernelManager.interrupt_kernel` (Jupyter client).

---

## `get_completions`
* **Description**: Requests code completions from a kernel.
* **Input Value**: 
    * `kernel_id: str`
    * `text: str`
    * `opts: dict`
* **Response Value**:
    * JSON-parsed completion results containing suggested code completions
* **Side Effects**:
    * (AbstractCodeRunner.get_completions):
    * (AbstractKernel.get_completions):
    * (AbstractCodeRunner.feed_and_get_completion):
        * Sends a `complete` message to the runner.
    * (BaseRunner.main_loop):
        * Upon receiving a `complete` message, calls `self._complete`.
    * (BaseRunner.complete):
        * Returns the strings to display in the auto-complete list. The current implementation appears to return an empty list.

---

## `get_logs`
* **Description**: Retrieves logs from a specific kernel's container.
* **Input Value**: 
    * `kernel_id: str`
* **Response Value**:
    * JSON-parsed result of kernel logs
* **Side Effects**:
    * (aiodocker.containers.get):
        * Retrieves container information by `container_id`.
    * (aiodocker.containers.log):
        * Fetches and returns the container’s logs.

---

## `restart_kernel`
* **Description**: Restarts a kernel
* **Input Value**: 
    * `kernel_id: str`
    * `session_id: str`
    * `kernel_image: ImageRef`
    * `updated_config: dict`
* **Response Value**:
    * `dict[str, Any]`: Information about the newly restarted kernel (similar to `create_kernels` response for a single kernel).
* **Side Effects**:
    * (restart_kernel__load_config): Loads the previous kernel's `kconfig.dat` from the scratch directory.
    * (restart_kernel__load_config): Loads the previous kernel's `cluster.json` from the scratch directory.
    * (_handle_destroy_event)
        * If the kernel_id is **not** registered in the kernel registry (already dead)
            * (reconstruct_resource_usage): Loads the alloc_map from `resource.txt` in the scratch directory via `restore_from_container` for each accelerator in the agent.
        * If it **is** registered
            * (AbstractCodeRunner.close): Cleans up the previous kernel runner's resources (watchdog_task, status_task, read_task, input_sock, output_sock).
        * (destroy_kernel):
            * (aiodocker.containers.stop): Stops the previous kernel container.
                * Calls reconstruct_resource_usage on exception.
    * (_handle_clean_event)
        * (aiodocker.containers.log): Collects the logs of the previous kernel container.
        * (DockerAgent.collect_logs): Writes the collected container logs to `containerlog.{container_id}` in `redis_stream_pool`. The logs are set to expire after 1 hour.
            * Publishes DoSyncKernelLogsEvent
            * (handle_kernel_log): Manager receives `DoSyncKernelLogsEvent`, writes the logs to the `container_log` column of the DB `kernels` table, then deletes them from Redis.
        * (aiodocker.containers.delete): Deletes the previous kernel container.
        * (clean_kernel): If the kernel has `domain_socket_proxies`, calls `proxy_server.wait_close()` to clean up the domain-socket proxy.
        * (_clean_scratch): Unmounts the filesystems at the scratch path and tmp_dir, removes them with rmtree, and then removes the scratch_root loop filesystem.
        * If the kernel’s network driver is not `bridge`, calls the plugin’s `leave_network` to clean up the network.
    * (DockerAgent.init_kernel_context):
        * (DockerAgent.resolve_image_distro):
            * If the image label `ai.backend.base-distro` is set, uses that value as the distro.
            * Otherwise, if there is a `"image:{image_id}:distro"` cache in `redis_stat_pool`, loads it and uses the value as the distro.
            * If no cache, creates a container with `aiodocker.containers.create` to run `ldd --version`, reads the distro from the container log, and caches it in `redis_stat_pool`.
    * (DockerAgent.check_image): Uses `aiodocker.images.inspect` to decide whether the image needs pulling or is already present.
    * (DockerAgent.pull_image): Pulls the image via `aiodocker.images.pull`.
    * (DockerAgent.prepare_resource_spec): Loads the kernel resource spec from `resource.txt` under the `config_dir` path.
    * (DockerAgent.prepare_scratch):
        * If the host platform is `linux`
            * When `scratch_type` is `memory`
                * Creates a filesystem in the new kernel’s `scratch_dir` (spawns a subprocess to mount a tmpfs).
                * Creates a filesystem in the new kernel’s `tmp_dir` (spawns a subprocess to mount a tmpfs).
            * When `scratch_type` is `hostfile`, creates a loop file in the new kernel’s `scratch_root`.
        * On non-Linux hosts, simply `mkdir` the `scratch_dir`.
        * Creates `config_dir` and `work_dir` under `scratch_dir` with permission `0o755`.
    * (_clone_dotfiles): Copies the following `pkg_resources` files under `ai/backend/runner`:
        * `jupyter-custom.css`
        * `logo.svg`
        * `roboto.ttf`
        * `roboto-italic.ttf`
        * `.bashrc`
        * `.bash_profile`
        * `.zshrc`
        * `.vimrc`
        * `.tmux.conf`
        * `.jupyter/custom`
        * `.jupyter/custom/custom.css`
        * `.jupyter/custom/logo.svg`
        * `.jupyter/custom/roboto.ttf`
        * `.jupyter/custom/roboto-italic.ttf`
    * (_clone_dotfiles): If the agent process `euid` is 0, changes the copied files’ `uid` and `gid` to `kernel-uid` and `kernel-gid`.
    * (DockerKernelCreationContext.prepare_ssh)
        * Writes the provided SSH key to `config_dir/ssh/id_cluster`.
        * Writes the provided SSH public key to `config_dir/ssh/id_cluster.pub`.
        * If `uid-match` (`KernelFeatures.UID_MATCH`) is set, changes ownership of the written SSH files to `kernel-uid` and `kernel-gid`.
        * If `cluster_info` has `cluster_ssh_port_mapping`, records it in `config_dir/ssh/port-mapping.json`.
    * (DockerKernelCreationContext.mount_krunner)
        * Bind-mounts `runner/su-exec.{arch}.bin` to `/opt/kernel/su-exec`
        * Bind-mounts `runner/libbaihook.*.{arch}.so` to `/opt/kernel/libbaihook.so`
        * Bind-mounts `runner/dropbearmulti.{arch}.bin` to `/opt/kernel/dropbearmulti`
        * Bind-mounts `runner/sftp-server.{arch}.bin` to `/opt/kernel/sftp-server`
        * Bind-mounts `runner/tmux.{arch}.bin` to `/opt/kernel/tmux`
        * If `sandbox-type` is "jail", bind-mounts `runner/jail.*.{arch}.bin` to `/opt/kernel/jail`
        * Bind-mounts `runner/extract_dotfiles.py` to `/opt/kernel/extract_dotfiles.py`
        * Bind-mounts `runner/entrypoint.sh` to `/opt/kernel/entrypoint.sh`
        * Bind-mounts `runner/fantompass.py` to `/opt/kernel/fantompass.py`
        * Bind-mounts `runner/hash_phrase.py` to `/opt/kernel/hash_phrase.py`
        * Bind-mounts `runner/words.json` to `/opt/kernel/words.json`
        * Bind-mounts `runner/DO_NOT_STORE_PERSISTENT_FILES_HERE.md` to `/home/work/DO_NOT_STORE_PERSISTENT_FILES_HERE.md`
        * If the target libc is `musl`, bind-mounts `runner/terminfo.alpine3.8` to `/home/work/.terminfo`
        * Volume-mounts the directory set in `local_config.container.krunner_volume` to `/opt/backend.ai`
        * Sets the `LD_PRELOAD` env var to `/opt/kernel/libbaihook.so` so it loads first.
        * Bind-mounts the `ai/backend/kernel` package to `/opt/backend.ai/lib/python{pyver}/site-packages/ai/backend/kernel`
        * Bind-mounts the `ai/backend/helpers` package to `/opt/backend.ai/lib/python{pyver}/site-packages/ai/backend/helpers`
        * Calls `apply_accelerator_allocation` for each accelerator plugin,
            * which receives the aiodocker object and generates Docker args for resource isolation via `generate_docker_args`.
        * Calls each plugin’s `generate_accelerator_mounts`, adds the returned mounts to `resource_spec.mounts`.
        * If an accelerator plugin requires extra hooks, bind-mounts `/opt/kernel/{hook}.so` and appends its path to `LD_PRELOAD`.
    * (AbstractComputePlugin.get_attached_devices): Calls each plugin’s `get_attached_devices` to obtain device info to pass to the KernelCreationContext.
    * (DockerAgent.load_model_definition): Executed only for inference models.
        * Reads the image’s `CMD` via `aiodocker.images.get` (deprecated, should be replaced with `inspect`).
        * Reads the model definition from `model_definition_yaml`.
    * (restart_kernel__store_config): Serializes the new kernel config to `config/kconfig.dat` as pickle.
    * (restart_kernel__store_config): Serializes the new cluster config to `config/cluster.json` as pickle.
    * (DockerKernelCreationContext.prepare_container)
        * Creates a user bootstrap script `/bootstrap.sh` under the work directory.
            * If `KernelFeatures.UID_MATCH`, chowns it to kernel-uid/gid.
        * Writes `environ.txt` under `config_dir` containing
            * the provided `environ`
            * the `self.computer_docker_args["Env"]` entry
        * Writes `resource.txt` under `config_dir` containing
            * `resource_spec.write_to_file` output
            * key-value pairs from each accelerator’s `instance.generate_resource_data`
        * If `internal_data.docker_credentials` exists, saves it to `config_dir/docker-creds.json`.
        * Copies `environ.txt` to `environ_base.txt` and `resource.txt` to `resource_base.txt` in `config_dir`.
        * If `internal_data.ssh_keypair` exists and `/home/work/.ssh` is not mounted
            * Creates `.ssh` (0700) under the work dir and creates `authorized_keys`, `id_rsa`, `id_container` (0600).
            * If `KernelFeatures.UID_MATCH`, chowns `.ssh` and its files to kernel-uid/gid.
        * Processes each path in `internal_data.dotfiles`:
            * Absolute paths → unchanged.
            * Paths starting with `"/home/"` → into `scratch_dir`.
            * Others → into the `work` directory.
            * Writes each dotfile to the determined path and chmods with `dotfile["perm"]`.
            * If `KernelFeatures.UID_MATCH`, chowns each dotfile and its parent dirs to kernel-uid/gid.
    * (DockerKernelCreationContext.start_container)
        * If `HostConfig.NetworkMode` is `host`
            * Writes intrinsic port info (`replin`, `replout`, `sshd`, `ttyd`) to `config_dir/intrinsic-ports.json`.
        * Additionally reads `agent-docker-container-opts.json` from the following paths and applies them as container options:
            * `/etc/backend.ai`
            * `.config/backend.ai`
            * `~/.config/backend.ai`
        * Creates the container via `aiodocker.containers.create`.
        * Re-opens `config_dir/resource.txt`, records the `container_id`, and adds.extra resource info from plugins via `generate_resource_data`.
        * Starts the container via `aiodocker.containers.start`.
        * If `sudo_session_enabled`, executes `sh -c mkdir -p /etc/sudoers.d && echo "work ALL=(ALL:ALL) NOPASSWD:ALL" > /etc/sudoers.d/01-bai-work` via `aiodocker.containers.exec` to configure password-less sudo inside the container.
        * Calls.each accelerator’s `get_docker_networks`, fetches DockerNetwork objects via `aiodocker.networks.get`, and connects them.
        * Calls `container.port` to fetch the container’s port info.
        * If the network plugin’s `network_config.mode` is not `bridge`, calls `get_capabilities` to fetch network capabilities.
            * If the `GLOBAL` capability exists, the plugin’s `expose_ports` is called to expose the ports to the public network after the container starts.
        * (DockerKernelCreationContext._apply_seccomp_profile): Applies the default seccomp profile from `runner/default-seccomp.json` and appends any additional syscalls to `SecurityOpt`.
        * On exception in `_clean_scratch`, calls `_rollback_container_creation` to clean up `scratch` and accelerator resources.
    * (AbstractKernel.init)
        * (DockerKernel.create_code_runner): Creates an `AbstractCodeRunner` (`DockerCodeRunner`) object.
    * (DockerKernel.check_status)
        * Sends a `status` message to the runner to check kernel runner status.
    * (KernelObjectType.get_service_apps)
        * Sends a `get-apps` message to the runner to retrieve service apps.
    * (DockerAgent.start_and_monitor_model_service_health): If the restarted kernel’s `session_type` is `INFERENCE`
        * (AbstractKernel.start_model_service)
            * Sends a `start-model-service` message to the runner to start the model service.
        * (BaseRunner.start_model_service)
            * (BaseRunner._start_service): Receives the model service start result via `model-service-result`.
                * (ServiceParser.start_service): Executes the actions listed in `ServiceDefinition.prestart_actions`.
                * (AbstractCodeRunner.read_output): Removes `"/opt/backend.ai/lib:"` from `LD_LIBRARY_PATH`.
                * (asyncio.create_subprocess_exec): Starts the model service subprocess.
                * (wait_local_port_open): Waits until the local port specified in `service_info.port` opens.
        * Publishes ModelServiceStatusEvent
            * (_dispatch_model_serving_events)
            * (handle_model_service_status_update): Manager receives `ModelServiceStatusEvent`.
            * (AgentRegistry.update_appproxy_endpoint_routes): Reads the wsproxy address of the scaling group for the endpoint from the DB and sends a.POST request to `f"{wsproxy_addr}/v2/endpoints/{endpoint.id}"` to update the endpoint address in the `endpoints` table.
    * Publishes KernelStartedEvent
        * (AgentRegistry.mark_kernel_running): Updates the kernel’s status in the DB to `KernelStatus.RUNNING`.

---

## `execute`
* **Description**: Executes code within a specified kernel.
* **Input value**:
    * `session_id: str`
    * `kernel_id: str`
    * `api_version: int`
    * `run_id: str`
    * `mode: Literal["query", "batch", "continue", "input"]`
    * `code: str`
    * `opts: dict[str, Any]`
    * `flush_timeout: float`
* **Response Value**:
    * `dict[str, Any]`: A dictionary containing the result of the execution, and file field
        ```json
        {
            execution result,
            "files": [],  # kept for API backward-compatibility
        }
        ```
* **Side Effects**:
    * (AbstractCodeRunner.execute):
    * (AbstractKernel.execute):
        * (AbstractCodeRunner.attach_output_queue):
            * Generates a `run_id` (`secrets.token_hex(16)`) and adds it to `self.pending_queues`. Injects an `asyncio.Event` object into that queue.
            * Waits until the injected Event object is set by `next_output_queue`.
        * When mode is "batch", calls `feed_batch`.
            * Sends `clean`, `build`, and `exec` messages in sequence.
        * When mode is "query", calls `feed_code`.
            * Sends a `code` message.
        * When mode is "input", calls `feed_input`.
            * Sends an `input` message.
        * When mode is "continue", skips.
    * (AbstractCodeRunner.get_next_result): Creates a `NextResult` object via `aggregate_console`.
        * On normal completion (`RunFinished`): switches to the next queue (`next_output_queue`).
        * In other cases—`BuildFinished`, `CleanFinished`, `TimeoutError`, etc.—moves the current queue to the tail, then resumes the output queue (`resume_output_queue`).
    * (AbstractCodeRunner.close): Cleans internal CodeRunner resources such as sockets and tasks.

---

## `trigger_batch_execution`
* **Description**: Initiates a batch execution task for a kernel.
* **Response Value**:
    * `None`.
* **Side Effects**:
    * Calls `self.agent.create_batch_execution_task()`, which likely sets up a background process or mechanism in the agent to feed code to the kernel for batch processing.

---

## `start_service`
* **Description**: Starts a specified service within a kernel's container.
* **Response Value**:
    * `dict[str, Any]`: Information about the started service (e.g., access points, status).
* **Side Effects**:
    * (DockerAgent.start_service)
    * (DockerKernel.start_service):
    * (AbstractCodeRunner.feed_start_service)
        * Sends a `start-service` message to the runner, and
        * (read_output) receives the `service-result` via `service_queue`, returning the service’s name, port number, protocol, options, and so on as JSON.

---

## `get_commit_status`
* **Description**: Checks the status of an ongoing or previous commit operation for a kernel.
* **Input Value**:
    * `kernel_id: KernelId`: Identifier for the kernel being used
    * `subdir: str`: path for organizing files or outputs
* **Response Value**:
    * `CommitStatus`
        * If image commit is ongoing(If lock_path(image-comit-path / subdir / lock / kernel_id) exists), response value is `CommitStatus.ONGOING`
        * If image commit is completed(If lock_path doesn't exit), response value is `CommitStatus.READY`
* **Side Effects**:
    * Calls kernel with `kernel_id` a `check_duplicate_commit(kernel_id, subdir)` method.
---

## `commit`
* **Description**: Commits the current state of a kernel's container (or a subdirectory within it) to a new image.
* **Input Value**: 
    * `reporter: ProgressReporter` : An instance of ProgressReporter to track and report progress(currently not used)
    * `kernel_id: KernelId`: Identifier for the kernel being used
    * `subdir: str`: path for organizing files or outputs
    * `canonical: str | None = None`: Optional canonical name or path for reference
    * `filename: str | None = None`: Optional filename to use for output or identification
    * `extra_labels: dict[str, str] = {}`: Additional labels as a dictionary
* **Response Value**:
    * `None`
* **Side Effects**:
    * Call kernel's `commit` method with same parameters
        * Creates necessary directories for the specified output path and lock_path
        * Commit new image with provided canonical and labels
        * If `filename` provided, the newly created Docker image is exported as a gzipped tarball to `path / filename`. After a successful export, this intermediate Docker image (created in the previous step) is deleted.
        * lock_path will be removed after all commit process

### Test Scenario 1 - Basic Commit without Export

* **Given**:
    * A kernel with `kernel_id_VALID` is running and its underlying container exists.
    * The Docker image `myimage:basic_commit` does not currently exist in the local Docker image list.
    * The directories `{base_commit_path}/test_commit_no_export/` and `{base_commit_path}/test_commit_no_export/lock/` may or may not exist on the host.
* **When**:
    * The `commit` method is called with the following input values:
        * `reporter`: A mock `ProgressReporter` instance.
        * `kernel_id`: `kernel_id_VALID`.
        * `subdir`: `"test_commit_no_export"`.
        * `canonical`: `"myimage"`.
        * `filename`: `None`.
        * `extra_labels`: `{"author": "test_user", "version": "1.0"}`.
* **Then**:
    * The method returns nothing
    * The directory `{base_commit_path}/test_commit_no_export/` is created on the host if it didn't exist.
    * The directory `{base_commit_path}/test_commit_no_export/lock/` is created on the host if it didn't exist.
    * A new Docker image tagged `myimage:latest` exists in the local Docker image list.
    * The created Docker image `myimage:latest` includes the labels `author="test_user"` and `version="1.0"`.
    * No gzipped tarball file is created on the host filesystem (because `filename` was `None`).
    * The Docker image `myimage:latest` is not deleted from the local Docker image list by this operation.


### Test Scenario 2 - Commit with Export

* **Given**:
    * An agent is running.
    * A kernel with `kernel_id_VALID` is running and its underlying container exists.
    * The Docker image `myimage:exported_commit` does not currently exist.
    * The file on the host filesystem at `{base_commit_path}/test_commit_with_export/exported_image.tar.gz` does not exist.
    * The directories `{base_commit_path}/test_commit_with_export/` and `{base_commit_path}/test_commit_with_export/lock/` may or may not exist.
* **When**:
    * The `commit` method is called with the following input values:
        * `reporter`: A mock `ProgressReporter` instance.
        * `kernel_id`: `kernel_id_VALID`.
        * `subdir`: `"test_commit_with_export"`.
        * `canonical`: `"myimage:exported_commit"`.
        * `filename`: `"exported_image"`.
        * `extra_labels`: `{"status": "exported"}`.
* **Then**:
    * The method returns nothing
    * The directory `{base_commit_path}/test_commit_with_export/` is created on the host if it didn't exist.
    * The directory `{base_commit_path}/test_commit_with_export/lock/` is created on the host if it didn't exist.
    * A lock file named `{kernel_id_VALID}` is created at the path `{base_commit_path}/test_commit_with_export/lock/{kernel_id_VALID}` on the host during the operation and is removed upon completion or failure.
    * A gzipped tarball file named `exported_image` exists on the host filesystem at the path `{base_commit_path}/test_commit_with_export/exported_image`.
    * The Docker image `myimage:exported_commit` no longer exists in the local Docker image list


### Test Scenario 3 - Commit with No Canonical Name

* **Given**:
    * An agent is running.
    * A kernel with `kernel_id_VALID` is running and its underlying container exists.
    * The directories `{base_commit_path}/test_commit_no_canonical/` and `{base_commit_path}/test_commit_no_canonical/lock/` may or may not exist.
* **When**:
    * The `commit` method is called with the following input values:
        * `reporter`: A mock `ProgressReporter` instance.
        * `kernel_id`: `kernel_id_VALID`.
        * `subdir`: `"test_commit_no_canonical"`.
        * `canonical`: `None`.
        * `filename`: `None`.
        * `extra_labels`: `{}`.
* **Then**:
    * The method returns nothing
    * The directory `{base_commit_path}/test_commit_no_canonical/` is created on the host if it didn't exist.
    * The directory `{base_commit_path}/test_commit_no_canonical/lock/` is created on the host if it didn't exist.
    * A lock file named `{kernel_id_VALID}` is created at `{base_commit_path}/test_commit_no_canonical/lock/{kernel_id_VALID}` and subsequently removed.
    * A new Docker image is created (its identifier, e.g., image ID, should be verifiable; specific tagging like `<none>:<none>` depends on Docker's default commit behavior).
    * No gzipped tarball file is created on the host filesystem.
    * The created Docker image is not deleted by this operation.


### Test Scenario 4 - Commit for a Non-Existent Kernel ID

* **Given**:
    * An agent is running.
    * A kernel with `kernel_id_INVALID` does not exist or is not in a running state.
    * The Docker image `myimage:fail_commit` does not exist.
* **When**:
    * The `commit` method is called with the following input values:
        * `reporter`: A mock `ProgressReporter` instance.
        * `kernel_id`: `kernel_id_INVALID`.
        * `subdir`: `"test_commit_invalid_kernel"`.
        * `canonical`: `"myimage:fail_commit"`.
        * `filename`: `None`.
        * `extra_labels`: `{}`.
* **Then**:
    * The method returns nothing
    * Raise `KeyError` as kernel are not found in `self.kernel_registry[kernel_id]`


### Test Scenario 5 - Concurrent Commit Attempts on the Same Kernel/Subdir

* **Given**:
    * An agent is running.
    * A kernel with `kernel_id_A` is running and its underlying container exists.
* **When**:
    * The `commit` method is called twice, nearly simultaneously, with the *same* `kernel_id_A` and `subdir_X`, but potentially different other parameters:
        * Call 1: `kernel_id_A`, `subdir_X`, `canonical="img1:tag1"`, `filename="f1.tar.gz"`
        * Call 2: `kernel_id_A`, `subdir_X`, `canonical="img2:tag2"`, `filename="f2.tar.gz"`
* **Then**:
    * One of the calls (e.g., Call 1) completes successfully.
    * The other call (e.g., Call 2) completes after call 1
    * Only one set of the expected successful side effects occurs:
        * EITHER a Docker image `img1:tag1` is temporarily created, file `f1.tar.gz` is exported to `{base_commit_path}/subdir_X/f1.tar.gz`, and image `img1:tag1` is deleted.
        * Then a Docker image `img2:tag2` is temporarily created, file `f2.tar.gz` is exported to `{base_commit_path}/subdir_X/f2.tar.gz`, and image `img2:tag2` is deleted.
        * Finally file `f1.tar.gz`, `f2.tar.gz` both exists


---

## `push_image`
* **Description**: Pushes a locally built or committed image to a specified container registry.
* **Input Value**:
    * `image_ref: ImageRef`: Reference to the container image
    * `registry_conf: ImageRegistry`: Configuration for the image registry
    * `timeout: float | None | Sentinel = Sentinel.TOKEN` : Timeout value in seconds, or a sentinel for not setting timeout
* **Response Value**:
    * `None`
* **Side Effects**:
    * If image_ref is local, agent do nothing
    * Push image by container runtime with auth cred created with registry username and password
    * If Image push fails, raise `RuntimeError`

### Test Scenario 1 - Successful Push with Authentication to Private Registry

* **Given**:
    * An `ImageRef` instance, `image_to_push_private`, is defined with:
        * `name="myimage"`
        * `project="myproject"`
        * `tag="latest"`
        * `registry="myprivatereg.example.com"`
        * `architecture="amd64"`
        * `is_local=False`
    * A local Docker image corresponding to the canonical name derived from `image_to_push_private` (e.g., `"myprivatereg.example.com/myproject/myimage:latest"`) exists in the agent's local Docker storage.
    * An `ImageRegistry` instance, `private_registry_config`, is defined as:
        * `name="myprivatereg.example.com"`
        * `url="https://myprivatereg.example.com"`
        * `username="valid_user"`
        * `password="valid_password"`
    * The image (derived from `image_to_push_private.canonical`) either does not yet exist in the remote private registry at `private_registry_config.url` or can be overwritten.
* **When**:
    * The `push_image` method is called with:
        * `image_ref`: `image_to_push_private`
        * `registry_conf`: `private_registry_config`
        * `timeout`: A reasonable value (e.g., `300.0`) or the default `Sentinel.TOKEN`.
* **Then**:
    * The method completes successfully and returns `None` (no exception is raised).
    * The Docker image (derived from `image_to_push_private.canonical`) is successfully pushed to and now exists in the remote private registry `myprivatereg.example.com`. (This would be verified by checking the remote registry).


### Test Scenario 2 - Attempt to Push an Image Marked as Local

* **Given**:
    * An `ImageRef` instance, `local_image_ref`, is defined with:
        * `name="mylocalimg"`
        * `project=None`
        * `tag="test"`
        * `registry="local"`
        * `architecture="amd64"`
        * `is_local=True`
* **When**:
    * The `push_image` method is called with:
        * `image_ref`: `local_image_ref`
        * `registry_conf`: `any_registry_config`
        * `timeout`: A reasonable value or the default.
* **Then**:
    * The method completes successfully and returns `None` immediately.
    * No attempt is made to push the image (derived from `local_image_ref.canonical`) to any remote registry.
    * No Docker push-related errors are logged or raised.


### Test Scenario 3 - Push Failure due to Invalid Authentication

* **Given**:
    * An `ImageRef` instance, `image_for_auth_fail`, is defined with:
        * `name="imageauthfail"`
        * `project="secureproject"`
        * `tag="1.0"`
        * `registry="myprivatereg.example.com"`
        * `architecture="amd64"`
        * `is_local=False`
    * A local Docker image corresponding to `image_for_auth_fail.canonical` exists in the agent's local Docker storage.
    * An `ImageRegistry` instance, `invalid_auth_registry_config`, is defined as:
        * `name="myprivatereg.example.com"`
        * `url="https://myprivatereg.example.com"`
        * `username="invalid_user"`
        * `password="wrong_password"`
* **When**:
    * The `push_image` method is called with:
        * `image_ref`: `image_for_auth_fail`
        * `registry_conf`: `invalid_auth_registry_config`
        * `timeout`: A reasonable value or the default.
* **Then**:
    * A `RuntimeError` is raised by the method.
    * The image (derived from `image_for_auth_fail.canonical`) is not pushed to the remote registry.


### Test Scenario 4 - Push Operation Timeout

* **Given**:
    * An `ImageRef` instance, `large_image_for_timeout`, is defined with:
        * `name="verylargeimage"`
        * `project="testproject"`
        * `tag="1.0"`
        * `registry="slowregistry.example.com"`
        * `architecture="amd64"`
        * `is_local=False`
    * A local Docker image corresponding to `large_image_for_timeout.canonical` exists
* **When**:
    * The `push_image` method is called with:
        * `image_ref`: `large_image_for_timeout`
        * `registry_conf`: `slow_registry_config`
        * `timeout`: A very short float value (e.g., `0.01` seconds) known to be less than the expected push completion time.
* **Then**:
    * A `RuntimeError` is raised by the method.
    * The image (derived from `large_image_for_timeout.canonical`) is not completely pushed or is not present in the remote registry.

---

## `purge_images`
* **Description**: Removes specified container images with `force` and `noprune` options. This method is usually called by `PurgeImageAction`, which is caused by Image GraphQL mutation
* **Input Value**:
    * `request: PurgeImagesReq`
        * `image_canonicals: list[str]` - List of image canonical names to be purged
        * `force: bool = False` - If true, forces removal of images even if they are in use
        * `noprune: bool = False` - If true, prevents removal of untagged parent images
* **Response Value**:
    * `PurgeImagesResp`: 
        * `image: str` - The canonical name of the image that was processed.
        * `error: Optional[str] = None` - Error message if deletion failed; otherwise, None
* **Side Effects**:
    * For each image specified in `request.images`:
        Attempts to delete the image using `docker.images.delete()` with `force` and `noprune` flags
    * If an image deletion fails, `PurgeImagesResp` returned with an `error` field filled

### Test Scenario 1 - Successfully Purge a Single Existing Image

* **Given**:
    * A Docker image named `"image-to-delete:v1"` exists in the local Docker storage.
* **When**:
    * The `purge_images` method is called with a `PurgeImagesReq` object where:
        * `images = ["image-to-delete:v1"]`
        * `force = False`
        * `noprune = False`
* **Then**:
    * The method returns a `PurgeImagesResp` object (let's call the returned instance `overall_response`).
    * `overall_response.responses` is a list containing one item.
    * The item in `overall_response.responses` has `image` field with value `"image-to-delete:v1"` and its `error` field is `None` (or not present, indicating success).
    * The Docker image `"image-to-delete:v1"` no longer exists in the local Docker storage.


### Test Scenario 2 - Successfully Purge Multiple Existing Images

* **Given**:
    * Docker images named `"image-a:latest"` and `"image-b:1.0"` exist in the local Docker storage.
* **When**:
    * The `purge_images` method is called with a `PurgeImagesReq` object where:
        * `images = ["image-a:latest", "image-b:1.0"]`
        * `force = False`
        * `noprune = False`
* **Then**:
    * The method returns a `PurgeImagesResp` object (`overall_response`).
    * `overall_response.responses` is a list containing two items.
    * Each item in `overall_response.responses` indicates success for its respective image (e.g., `image` field matches the input image name, `error` field is `None`).
    * The Docker images `"image-a:latest"` and `"image-b:1.0"` no longer exist in the local Docker storage.


### Test Scenario 3 - Attempt to Purge a Non-Existent Image

* **Given**:
    * A Docker image named `"ghost-image:v0"` does not exist in the local Docker storage.
* **When**:
    * The `purge_images` method is called with a `PurgeImagesReq` object where:
        * `images = ["ghost-image:v0"]`
        * `force = False`
        * `noprune = False`
* **Then**:
    * The method returns a `PurgeImagesResp` object (`overall_response`).
    * `overall_response.responses` is a list containing one item.
    * The item in `overall_response.responses` has `image = "ghost-image:v0"` and its `error` field contains an error message (e.g., indicating "No such image" or "image not found").
    * The local Docker storage state regarding `"ghost-image:v0"` remains unchanged (it still does not exist).


### Test Scenario 4 - Attempt to Purge an Image in Use (Without Force)

* **Given**:
    * A Docker image named `"busy-image:stable"` exists in the local Docker storage.
    * A container is currently running that was created from the `"busy-image:stable"` image.
* **When**:
    * The `purge_images` method is called with a `PurgeImagesReq` object where:
        * `images = ["busy-image:stable"]`
        * `force = False`
        * `noprune = False`
* **Then**:
    * The method returns a `PurgeImagesResp` object (`overall_response`).
    * `overall_response.responses` is a list containing one item.
    * The item in `overall_response.responses` has `image = "busy-image:stable"` and its `error` field contains an error message indicating the image is in use (ex. "conflict: unable to delete image...image is being used by running container...").
    * The Docker image `"busy-image:stable"` still exists in the local Docker storage.
    * The container using `"busy-image:stable"` is still running.


### Test Scenario 5 - Successfully Purge an Image in Use (With Force)

* **Given**:
    * A Docker image named `"busy-image:force-delete"` exists in the local Docker storage.
    * A container is currently running that was created from the `"busy-image:force-delete"` image.
* **When**:
    * The `purge_images` method is called with a `PurgeImagesReq` object where:
        * `images = ["busy-image:force-delete"]`
        * `force = True`
        * `noprune = False`
* **Then**:
    * The method returns a `PurgeImagesResp` object (`overall_response`).
    * `overall_response.responses` is a list containing one item.
    * The item in `overall_response.responses` has `image = "busy-image:force-delete"` and its `error` field is `None`.
    * The Docker image `"busy-image:force-delete"` no longer exists in the local Docker storage.
    * The container that was using `"busy-image:force-delete"` continues to run


### Test Scenario 6 - Purge a Mix of Existing, Non-Existent, and In-Use (Without Force) Images

* **Given**:
    * A Docker image named `"delete-me:ok"` exists in local Docker storage.
    * A Docker image named `"iamghost:hmm"` does not exist in local Docker storage.
    * A Docker image named `"dont-delete-me:busy"` exists and is used by a running container.
* **When**:
    * The `purge_images` method is called with a `PurgeImagesReq` object where:
        * `images = ["delete-me:ok", "iamghost:hmm", "dont-delete-me:busy"]`
        * `force = False`
        * `noprune = False`
* **Then**:
    * The method returns a `PurgeImagesResp` object (`overall_response`)
    * `overall_response.responses` is a list containing three items
    * The item for `"delete-me:ok"` indicates success (error is `None`)
    * The item for `"iamghost:hmm"` indicates failure with an error message
    * The item for `"dont-delete-me:busy"` indicates failure with an error message
    * The Docker image `"delete-me:ok"` no longer exists in local Docker storage
    * The Docker image `"dont-delete-me:busy"` still exists in local Docker storage


### Test Scenario 7 - Purge an Empty List of Images

* **Given**:
* **When**:
    * The `purge_images` method is called with a `PurgeImagesReq` object where:
        * `images = []`
        * `force = False`
        * `noprune = False`
* **Then**:
    * If an empty list (`[]`) is passed to the `images` field of `PurgeImagesReq`, values like `[None]` are not allowed, so a Pydantic validation error will occur.

---

## `shutdown_service`
* **Description**: Shuts down a running service within a kernel's container.
* **Input Value**:
    * `kernel_id: KernelId`: Id of the kernel to send message
    * `service: str`: Name of service
* **Response Value**:
    * `None`
* **Side Effects**:
    * Calls kernel with `kernel_id` a `shutdown_service(service)` method.
        * Inside kernel, it calls `self.runner.feed_shutdown_service(service)`

### Test Scenario 1 - Successfully Shut Down a Running Service

* **Given**:
    * An agent is running.
    * A kernel with `kernel_id_VALID` is active and its underlying container is running.
    * Inside the container for `kernel_id_VALID`, a service named `"active_service_A"` is currently running (e.g., its process exists, and/or it's listening on a specific port).
* **When**:
    * The `shutdown_service` RPC method is called on the agent with the following input values:
        * `kernel_id`: `kernel_id_VALID`
        * `service`: `"active_service_A"`
* **Then**:
    * The `shutdown_service` will return nothing
    * The service `"active_service_A"` inside the container associated with `kernel_id_VALID` is no longer running


### Test Scenario 2 - Attempt to Shut Down a Non-Existent Service in a Running Kernel

* **Given**:
    * An agent is running.
    * A kernel with `kernel_id_VALID` is active and its underlying container is running.
    * Inside the container for `kernel_id_VALID`, a service named `"ghost_service_B"` is *not* currently running.
* **When**:
    * The `shutdown_service` RPC method is called on the agent with the following input values:
        * `kernel_id`: `kernel_id_VALID`
        * `service`: `"ghost_service_B"`
* **Then**:
    * Returns Nothing
    * Exception log('unhandled exception while shutting down service app') will be last and do nothing


### Test Scenario 3 - Attempt to Shut Down a Service in a Non-Existent or Stopped Kernel

* **Given**:
    * An agent is running.
    * `kernel_id_INVALID` does not correspond to any active/running kernel known to the agent.
* **When**:
    * The `shutdown_service` RPC method is called on the agent with the following input values:
        * `kernel_id`: `kernel_id_INVALID`
        * `service`: `"any_service_C"`
* **Then**:
    * Returns Nothing
    * Exception log('unhandled exception while shutting down service app') will do nothing


### Test Scenario 4 - Attempt to Shut Down an Already Stopped Service

* **Given**:
    * An agent is running.
    * A kernel with `kernel_id_VALID` is active and its underlying container is running.
    * Inside the container for `kernel_id_VALID`, a service named `"already_stopped_service_D"` was previously running but has already been stopped.
* **When**:
    * The `shutdown_service` RPC method is called on the agent with the following input values:
        * `kernel_id`: `kernel_id_VALID`
        * `service`: `"already_stopped_service_D"`
* **Then**:
    * The service `"already_stopped_service_D"` inside the container for `kernel_id_VALID` remains in its stopped state.
    * No exceptions are raised


---

## `accept_file`
* **Description**: Uploads a file into a agent host machine. This method usually called due to `UploadFilesAction`, triggered by manager's session api `upload_files`
* **Input Value**:
    * `kernel_id: KernelId`: Id of the kernel to upload file
    * `filename: str`: Name of file
    * `filedata`: Binary data that wants to save
* **Response Value**:
    * `None`.
* **Side Effects**:
    * Calls kernel with `kernel_id` a `accept_file(filename, filedata)` method.
        * If user tries to upload file outside `/home/work` directory, `PermissionError` occurs
        * File is created under `{agent_config["container"]["scratch-root"]}/{kernel_id}/work/home/work/`
        * Parent directories for this target host path are created if they do not already exist
        * Raises a `RuntimeError` when if an `OSError` (e.g., disk full, host filesystem permission issues) occurs during the directory creation or file writing process on the host


### Test Scenario 1 - Successfully Upload a File to Top Level of Kernel's Work Directory

* **Given**:
    * A kernel with `kernel_id_VALID` is active and its corresponding scratch directory base (`{agent_config["container"]["scratch-root"]}/{kernel_id_VALID}/work/`) exists or can be created on the host.
    * The file `{agent_config["container"]["scratch-root"]}/{kernel_id_VALID}/work/uploaded_file.txt` does not currently exist on the host.
* **When**:
    * The `accept_file` method is called on the agent with:
        * `kernel_id`: `kernel_id_VALID`
        * `filename`: `"/home/work/uploaded_file.txt"` (Path inside the container's environment)
        * `filedata`: `b"This is test data."`
* **Then**:
    * The `accept_file` method returns `None`.
    * A file exists on the host filesystem at the path `{agent_config["container"]["scratch-root"]}/{kernel_id_VALID}/work/uploaded_file.txt`.
    * The content of the host file at that path is `b"This is test data."`.
    * No exceptions are raised by the agent's call.

---
### Test Scenario 2 - Attempt to Upload File Outside `/home/work` (e.g., using `../` in container path)

* **Given**:
    * A kernel with `kernel_id_VALID` is active.
* **When**:
    * The `accept_file` method is called on the agent with:
        * `kernel_id`: `kernel_id_VALID`
        * `filename`: `"/home/work/../attempt_outside.txt"` (Path attempting to traverse up from `/home/work`)
        * `filedata`: `b"Malicious data"`
* **Then**:
    * The `accept_file` method raises a `PermissionError`.
    * No file named `attempt_outside.txt` (or similar) is created anywhere outside the designated `{agent_config["container"]["scratch-root"]}/{kernel_id_VALID}/work/` directory on the host.

### Test Scenario 3 - Attempt to Upload File to an Absolute Path Outside `/home/work` (e.g., `/etc/`)

* **Given**:
    * A kernel with `kernel_id_VALID` is active.
* **When**:
    * The `accept_file` method is called on the agent with:
        * `kernel_id`: `kernel_id_VALID`
        * `filename`: `"/etc/new_file_by_agent"` (Absolute path outside the allowed container work directory)
        * `filedata`: `b"System data attempt"`
* **Then**:
    * The `accept_file` method raises a `PermissionError`.
    * No file is created at `/etc/new_file_by_agent` (or its host equivalent) on the host filesystem.

### Test Scenario 4 - Upload to a Non-Existent or Stopped Kernel

* **Given**:
    * `kernel_id_INVALID` does not correspond to any active/running kernel known to the agent.
* **When**:
    * The `accept_file` method is called on the agent with:
        * `kernel_id`: `kernel_id_INVALID`
        * `filename`: `"/home/work/anyfile.txt"`
        * `filedata`: `b"Orphaned data"`
* **Then**:
    * The `accept_file` method raises an `KeyError` exception

---

## `download_file`
* **Description**: Download a file in a agent host machine. This method usually called due to `DownloadFilesAction`, triggered by manager's session api `download_files`
* **Input Value**:
    * `kernel_id: KernelId`: Id of the kernel to download from
    * `filepath: str`: Path within `/home/work` to download file or directory
* **Response Value**:
    * The raw bytes of the tar archive containing the content at `/home/work/filepath`. 
        * If `/home/work/filepath` is a single file, the archive will contain that file
        * If it's a directory, the archive will contain the directory and its contents.
* **Side Effects**:
    * Calls kernel with `kernel_id` a `download_file(filepath)` method.
        * If user tries to download file outside `/home/work`, `PermissionError` occurs
        * If file is over 1 MiB, `ValueError` occurs
        * If unknown docker error occurs, `RuntimeError` raises

### Test Scenario 1 - Successfully Download a Single Existing File

* **Given**:
    * A kernel with `kernel_id_VALID` is active, and its underlying container is running.
    * On the host filesystem, a file exists at the path corresponding to what is `/home/work/data/sample.txt` inside the kernel's container (and in host filesystemt, `{scratch_root}/{kernel_id_VALID}/work/data/sample.txt`), and its content is `b"Test content for download."`.
* **When**:
    * The agent's `download_file` method (as called by the RPC) is invoked with:
        * `kernel_id`: `kernel_id_VALID`
        * `filepath`: `"/home/work/data/sample.txt"` (Path inside the container)
* **Then**:
    * The method returns a `bytes` object.
    * When the returned `bytes` object is interpreted as a tar archive, it contains a single entry (e.g., `sample.txt` or `data/sample.txt` depending on `get_archive` behavior for a specific file path) whose content is `b"Test content for download."`.
    * No exceptions are raised by the agent's method.


### Test Scenario 2 - Successfully Download an Existing Directory

* **Given**:
    * A kernel with `kernel_id_VALID` is active, and its container is running.
    * On the host filesystem, a directory exists at the path corresponding to `/home/work/project_files/` inside the kernel's container, containing (and in host filesystemt, `{scratch_root}/{kernel_id_VALID}/work/project_files/`):
        * `project_files/file1.py` (content: `b"print('hello')"`).
        * `project_files/docs/readme.md` (content: `b"# Project"`)
* **When**:
    * The agent's `download_file` method is invoked with:
        * `kernel_id`: `kernel_id_VALID`
        * `filepath`: `"/home/work/project_files"`
* **Then**:
    * The method returns a `bytes` object.
    * When the returned `bytes` object is interpreted as a tar archive, it contains entries corresponding to `project_files/file1.py` (with content `b"print('hello')"`) and `project_files/docs/readme.md` (with content `b"# Project"`).
    * No exceptions are raised by the agent's method.


### Test Scenario 3 - Attempt to Download File/Directory Outside `/home/work`

* **Given**:
    * A kernel with `kernel_id_VALID` is active and its container is running.
* **When**:
    * The agent's `download_file` method is invoked with:
        * `kernel_id`: `kernel_id_VALID`
        * `filepath`: `"/etc/important_config"` (Path outside the allowed `/home/work`)
* **Then**:
    * The agent's `download_file` method raises a `PermissionError`


### Test Scenario 4 - Attempt to Download Content Resulting in Tar Archive > 1 MiB

* **Given**:
    * A kernel with `kernel_id_VALID` is active, and its container is running.
    * A file or directory exists at `/home/work/very_large_data/` inside the kernel's container(and in host filesystemt, `{scratch_root}/{kernel_id_VALID}/work/very_large_data/`), such that its tar archive representation (as returned by Docker's `get_archive`) would exceed 1 MiB
* **When**:
    * The agent's `download_file` method is invoked with:
        * `kernel_id`: `kernel_id_VALID`
        * `filepath`: `"/home/work/very_large_data"`
* **Then**:
    * The agent's `download_file` method raises a `ValueError` with a message "Too large archive file exceeding 1 MiB".


### Test Scenario 5 - Attempt to Download a Non-Existent Path Within `/home/work`

* **Given**:
    * A kernel with `kernel_id_VALID` is active and its container is running.
    * The path `/home/work/non_existent_file.txt` does not correspond to any actual file or directory within the kernel's container environment.
* **When**:
    * The agent's `download_file` method is invoked with:
        * `kernel_id`: `kernel_id_VALID`
        * `filepath`: `"/home/work/non_existent_file.txt"`
* **Then**:
    * The agent's `download_file` method raises a `RuntimeError`


### Test Scenario 6 - Attempt to Download from a Non-Existent or Stopped Kernel

* **Given**:
    * `kernel_id_INVALID` does not correspond to any active or running kernel known to the agent.
* **When**:
    * The agent's `download_file` method is invoked with:
        * `kernel_id`: `kernel_id_INVALID`
        * `filepath`: `"/home/work/any_file.txt"`
* **Then**:
    * The agent's `download_file` method raises a `KeyError` exception

---

## `download_single`
* **Description**: Download a single file in a agent host machine. This method usually called due to `DownloadFilesAction`, triggered by manager's session api `download_files`
* **Input Value**:
    * `kernel_id: KernelId`: Id of the kernel to download file from
    * `filepath: str`: Path within `/home/work` to download file
* **Response Value**:
    * `bytes`: The raw content bytes of the single file specified by `/home/work/filepath`
* **Side Effects**:
    * Calls kernel with `kernel_id` a `download_single(filepath)` method.
        * If user tries to download file outsid `/home/work`, `PermissionError` occurs
        * If file is over 1 MiB, `ValueError` occurs
        * If the tar archive contains more than one entry (i.e., it's not a single file archive as expected), a `ValueError` raises
        * If the single file cannot be extracted or read from the archive (e.g., archive is malformed or the expected entry is not a readable file), a `ValueError` is raised
        * If unknown docker error occurs, `RuntimeError` raises

### Test Scenario 1 - Successfully Download a Single Existing File

* **Given**:
    * A kernel with `kernel_id_VALID` is active, and its underlying container is running.
    * On the host filesystem, a file exists at the path corresponding to `/home/work/documents/report.txt` inside the kernel's container (`{scratch_root}/{kernel_id_VALID}/work/documents/report.txt`), and its content is `b"This is the final report."`.
* **When**:
    * The agent's `download_single` method called with:
        * `kernel_id`: `kernel_id_VALID`
        * `filepath`: `"/home/work/documents/report.txt"` (Path inside the container)
* **Then**:
    * The method returns a `bytes` object.
    * The returned `bytes` object is equal to `b"This is the final report."`.
    * No exceptions are raised by the agent's method.


### Test Scenario 2 - Attempt to Download a Non-Empty Directory (Expected to Fail due to Multiple Entries in Tar)

* **Given**:
    * A kernel with `kernel_id_VALID` is active, and its container is running.
    * On the host filesystem, a directory exists at the path corresponding to `/home/work/my_pictures/` inside the kernel's container, and this directory contains one or more files (e.g., `my_pictures/photo1.jpg`, `my_pictures/photo2.png`).
* **When**:
    * The agent's `download_single` method is invoked with:
        * `kernel_id`: `kernel_id_VALID`
        * `filepath`: `"/home/work/my_pictures"`
* **Then**:
    * The agent's `download_single` method raises a `ValueError` with a message "Expected a single-file archive but found multiple files from /home/work/my_pictures".


### Test Scenario 3 - Attempt to Download File Outside `/home/work`

* **Given**:
    * A kernel with `kernel_id_VALID` is active and its container is running.
* **When**:
    * The agent's `download_single` method is invoked with:
        * `kernel_id`: `kernel_id_VALID`
        * `filepath`: `"/usr/bin/binary"` (Path outside the allowed `/home/work`)
* **Then**:
    * The agent's `download_single` method raises a `PermissionError` with a message similar to "You cannot download files outside /home/work".


### Test Scenario 4 - Attempt to Download a File Whose Tar Archive Exceeds 1 MiB

* **Given**:
    * A kernel with `kernel_id_VALID` is active.
    * A single file exists at `/home/work/data_archive_source.dat` inside the kernel's container. This file itself might be slightly less than 1MiB, but its representation within a tar archive (due to tar headers/metadata) causes the total tar archive size to exceed 1 MiB
* **When**:
    * The agent's `download_single` method is invoked with:
        * `kernel_id`: `kernel_id_VALID`
        * `filepath`: `"/home/work/data_archive_source.dat"`
* **Then**:
    * The agent's `download_single` method raises a `ValueError` with a message similar to "Too large archive file exceeding 1 MiB".


### Test Scenario 5 - Attempt to Download a Non-Existent File Within `/home/work`

* **Given**:
    * A kernel with `kernel_id_VALID` is active and its container is running.
    * The path `/home/work/fantasy_novel.txt` does not correspond to any actual file within the kernel's container environment.
* **When**:
    * The agent's `download_single` method is invoked with:
        * `kernel_id`: `kernel_id_VALID`
        * `filepath`: `"/home/work/fantasy_novel.txt"`
* **Then**:
    * The agent's `download_single` method raises a `RuntimeError`


### Test Scenario 6 - Attempt to Download from a Non-Existent or Stopped Kernel

* **Given**:
    * `kernel_id_GONE` does not correspond to any active or running kernel known to the agent.
* **When**:
    * The agent's `download_single` method is invoked with:
        * `kernel_id`: `kernel_id_GONE`
        * `filepath`: `"/home/work/any_single_file.dat"`
* **Then**:
    * The agent's `download_single` method raises a `KeyError` exception


---

## `list_files`
* **Description**: List files in a agent host machine. This method usually called due to `ListFilesAction`, triggered by manager's session api `list_files`
* **Input Value**:
    * `kernel_id: KernelId`: Id of the kernel to list files from
    * `filepath: str`: Path within `/home/work` to list files and directories
* **Response Value**:
    * A Json data
        * `"files": str` - A JSON string. When parsed, this string yields a list of objects, where each object represents a file or directory and contains details.
        * `"errors": str` - Any error output captured from the standard error stream of the docker exec command or the script executed within the container. This will be an empty string if no errors occurred.
        * `"abspath": str` - The original `file_path` argument that was passed to the method for listing.
* **Side Effects**:
    * Calls kernel with `kernel_id` a `list_files(path)` method.
        * If user tries to download file outsid `/home/work`, `PermissionError` occurs
        * Getting lists files and directories is achieved by executing a script inside the container, with running subprocess.

### Test Scenario 1 - Successfully List Files in an Existing, Non-Empty Directory

* **Given**:
    * A kernel with `kernel_id_VALID` is active, and its underlying container is running.
    * Inside the kernel's container, the directory `/home/work/documents/` exists and contains items such as:
        * `report.docx` (file)
        * `images` (subdirectory)
    * (These would physically be on the host at paths like `{scratch_root}/{kernel_id_VALID}/work/documents/report.docx`)
* **When**:
    * The agent's `list_files` method (as called by the RPC) is invoked with:
        * `kernel_id`: `kernel_id_VALID`
        * `path`: `"/home/work/documents"` (Path inside the container)
* **Then**:
    * The method returns a dictionary, let's call it `response_data`.
    * `response_data["abspath"]` is equal to `"/home/work/documents"`.
    * `response_data["errors"]` is an empty string.
    * `response_data["files"]` is a non-empty JSON string.
    * When the JSON string in `response_data["files"]` is parsed, it yields a list containing objects representing at least `report.docx` and `images`, each with correct metadata(ex. filename) 


### Test Scenario 2 - Successfully List an Existing Empty Directory

* **Given**:
    * A kernel with `kernel_id_VALID` is active, and its container is running.
    * Inside the kernel's container, the directory `/home/work/empty_dir/` exists and is empty.
    * (This directory would physically be on the host at `{scratch_root}/{kernel_id_VALID}/work/empty_dir/`)
* **When**:
    * The agent's `list_files` method is invoked with:
        * `kernel_id`: `kernel_id_VALID`
        * `path`: `"/home/work/empty_dir"`
* **Then**:
    * The method returns a dictionary `response_data`.
    * `response_data["abspath"]` is equal to `"/home/work/empty_dir"`.
    * `response_data["errors"]` is an empty string (or non-critical).
    * `response_data["files"]` is a JSON string that, when parsed, yields an empty list (`[]`).


### Test Scenario 3 - Attempt to List a Path Outside `/home/work`

* **Given**:
    * A kernel with `kernel_id_VALID` is active and its container is running.
* **When**:
    * The agent's `list_files` method is invoked with:
        * `kernel_id`: `kernel_id_VALID`
        * `path`: `"/etc"` (Path outside the allowed `/home/work`)
* **Then**:
    * The agent's `list_files` method raises a `PermissionError` with a message similar to "You cannot list files outside /home/work".


### Test Scenario 4 - Attempt to List a Non-Existent Path Within `/home/work`

* **Given**:
    * A kernel with `kernel_id_VALID` is active and its container is running.
    * The path `/home/work/this_folder_does_not_exist/` does not exist inside the kernel's container.
* **When**:
    * The agent's `list_files` method is invoked with:
        * `kernel_id`: `kernel_id_VALID`
        * `path`: `"/home/work/this_folder_does_not_exist"`
* **Then**:
    * The method returns a dictionary `response_data`.
    * `response_data["abspath"]` is equal to `"/home/work/this_folder_does_not_exist"`.
    * `response_data["files"]` is likely an empty string
    * `response_data["errors"]` contains a non-empty string, which includes an error message indicating the path was not found


### Test Scenario 5 - Attempt to List Files with an Invalid/Non-Existent Kernel ID

* **Given**:
    * `kernel_id_INVALID` does not correspond to any active or running kernel in the agent's `kernel_registry`.
* **When**:
    * The agent's `list_files` method is invoked with:
        * `kernel_id`: `kernel_id_INVALID`
        * `path`: `"/home/work/any_target_path"`
* **Then**:
    * The agent's `list_files` method raises a `KeyError`

---

## `shutdown`
* **Description**: Initiates the shutdown process for the agent.
* **Input Value**:
    * `stop_signal: signal.Signals`: Specifies the signal to use for agent shutdown (currently, only `signal.SIGTERM` is meaningful. Usually stop_signal value is signal.SIGTERM)
* **Response Value**:
    * `None`
* **Side Effects**:
    * Task Cancellation:
        * Cancels the agent's main socket communication task
        * Shuts down any implementation-specific periodic task groups (ex Docker-related ptask group)
        * Cancels all ongoing asynchronous batch execution tasks
        * Cancels all scheduled timer tasks.
        * Stops and cancels the Docker event monitoring task (if applicable)
    * Kernel and Container Lifecycle Management:
        * For every registered kernel:
            * Closes the kernel's runner
            * Calls the kernel object's own `close()` method for individual cleanup
        * Persists Kernel Registry: The current state of `self.kernel_registry` is serialized and written to a file with the name `{agent_config['container']['var-base-path']}/last_registry.{self.local_instance_id}.dat`
        * Conditional Full Kernel Destruction (if stop_signal is SIGTERM):
            * All registered kernels are explicitly signaled for destruction (`LifecycleEvent.DESTROY` with reason `AGENT_TERMINATION` is injected).
        * The shutdown process waits for these destruction operations to complete before proceeding. This ensures containers are removed
    * Event System and Handler Shutdown:
        * The container lifecycle event handler task is gracefully stopped.
        * An `AgentTerminatedEvent` with reason="shutdown" is produced
        * The event producer and event dispatcher components are closed.
    * External Service and Resource Cleanup:
        * Connection pools to external services (ex. Redis streams, Redis stats) are closed
        * Implementation-specific metadata server resources are cleaned up
        * The connection to the container engine (ex. Docker client) is closed
---

## `create_local_network`
* **Description**: Creates a container bridge network. Usually used when starting new session
* **Input Value**:
    * `network_name: str`: name of network that wants to make(Usually network name is composed of `bai-singlenode-{scheduled_session.id}`)
* **Response Value**:
    * `None`.
* **Side Effects**:
    * Bridge Network with given network_name, and label `"ai.backend.cluster-network": "1"`


### Test Scenario 1: Successfully Create a New Network

* **Given**:
    * An agent is running and has access to a Docker engine.
    * A Docker network named `"test-new-network-01"` does not currently exist in the Docker environment.
* **When**:
    * The agent's `create_local_network` method is called with:
        * `network_name`: `"test-new-network-01"`
* **Then**:
    * The `create_local_network` method returns `None`
    * A Docker network named `"test-new-network-01"` now exists in the Docker environment.
    * The created network `"test-new-network-01"` has the driver type `"bridge"`.
    * The created network `"test-new-network-01"` has the label `"ai.backend.cluster-network": "1"`.

### Test Scenario 2: Attempt to Create a Network That Already Exists

* **Given**:
    * An agent is running and has access to a Docker engine.
    * A Docker network named `"existing-network-02"` already exists in the Docker environment.
* **When**:
    * The agent's `create_local_network` method is called with:
        * `network_name`: `"existing-network-02"`
* **Then**:
    * The `create_local_network` method raises an exception
    * The state of the existing Docker network `"existing-network-02"` remains unchanged.

### Test Scenario 3: Attempt to Create a Network with an Invalid Name Format (Optional, based on Docker/aiodocker validation)

* **Given**:
    * An agent is running and has access to a Docker engine.
    * The string `"invalid@name#for_net"` is considered an invalid format for a Docker network name.
* **When**:
    * The agent's `create_local_network` method is called with:
        * `network_name`: `"invalid@name#for_net"`
* **Then**:
    * The `create_local_network` method raises an exception
    * No new network with the name `"invalid@name#for_net"` is created in the Docker environment.

---

## `destroy_local_network`
* **Description**: Destroys container network. Usually used when clean up a session
* **Input value**:
    * `network_name: str`: network name wants to destroy
* **Response Value**:
    * `None`.
* **Side Effects**:
    * Destroy container network name with given parameter

### Test Scenario 1: Successfully Destroy an Existing, Unused Network

* **Given**:
    * An agent is running and has access to a Docker engine.
    * A Docker network named `"delete-me-network-A"` exists in the Docker environment.
    * No running containers are currently connected to the `"delete-me-network-A"` network.
* **When**:
    * The agent's `destroy_local_network` method is called with:
        * `network_name`: `"delete-me-network-A"`
* **Then**:
    * The `destroy_local_network` method returns `None`
    * The Docker network `"delete-me-network-A"` no longer exists in the Docker environment.

### Test Scenario 2: Attempt to Destroy a Non-Existent Network

* **Given**:
    * An agent is running and has access to a Docker engine.
    * A Docker network named `"non-existent-network-B"` does not exist in the Docker environment.
* **When**:
    * The agent's `destroy_local_network` method is called with:
        * `network_name`: `"non-existent-network-B"`
* **Then**:
    * The `destroy_local_network` method raises an exception

### Test Scenario 3: Attempt to Destroy a Network Currently in Use by a Container

* **Given**:
    * An agent is running and has access to a Docker engine.
    * A Docker network named `"busy-network-C"` exists in the Docker environment.
    * At least one active container is connected to the `"busy-network-C"` network.
* **When**:
    * The agent's `destroy_local_network` method is called with:
        * `network_name`: `"busy-network-C"`
* **Then**:
    * The `destroy_local_network` method raises an exception
    * The Docker network `"busy-network-C"` still exists in the Docker environment.
    * The container(s) connected to `"busy-network-C"` remain running and connected.
