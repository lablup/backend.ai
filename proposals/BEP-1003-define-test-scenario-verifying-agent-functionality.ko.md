# Agent 동작

---

## `update_scaling_group`

* **설명**: agent 의 자원 그룹 설정을 변경한다.
* **입력값**:
    * `scaling_group: str`: 자원 그룹 이름
* **응답값**:
    * `None` (성공 시 암묵적으로 반환한다)
* **부작용**:
    * agent 의 TOML 설정 파일을 읽는다.
    * 설정의 `agent.scaling-group` 값을 수정하고 파일을 갱신한다.
    * 원본 설정 파일의 백업을 생성한다(예: `agent.toml.bak`).
    * agent 메모리의 `local_config` 에서 `scaling-group` 을 갱신한다.

---

## `ping`

* **설명**: 연결을 확인하는 단순 ping RPC 다.
* **입력값**:
    * `msg: str`: ping message
* **응답값**:
    * `str`: 요청으로 보낸 message 를 그대로 반환한다.

---

## `gather_hwinfo`

* **설명**: agent 가 실행되는 host 에서 하드웨어 메타데이터를 수집한다.
* **응답값**:
    * `Mapping[str, HardwareMetadata]`: CPU, GPU, 메모리 같은 하드웨어 세부 정보를 담은 dictionary 다.

---

## `ping_kernel`

* **설명**: 실행 중인 특정 kernel 에 ping 을 보내 응답 여부를 확인한다.
* **입력값**:
    * `kernel_id: str`: ping 을 보낼 kernel 의 id
* **응답값**:
    * `dict[str, float] | None`: kernel 이 응답하면 timing 과 status 정보를 담은 dictionary 를, 응답하지 않으면 `None` 을 반환한다.

---

## `check_and_pull`

* **설명**: 지정한 container image 가 로컬에 있는지 확인하고, 없거나 갱신이 필요하면 pull 하는 background task 를 시작한다.
* **입력값**:
    * `image_configs: Mapping[str, ImageConfig]`:
* **응답값**:
    * `dict[str, str]`: image 이름을 pull 을 맡은 background task ID 로 연결한 dictionary 다.
* **부작용**:
    * (check_and_pull):
        * (DockerAgent.check_image)
            * (docker.images.inspect): 이미지가 있는지 확인하고 AutoPullBehavior 에 따라 다음과 같이 동작한다.
                * (TAG): 이미지가 로컬에 있으면 항상 False 를 반환해 로컬 이미지를 사용한다.
                * (DIGEST): 이미지가 로컬에 있고 그 ID 가 전달된 image_id 와 일치할 때만 로컬 이미지를 사용한다. 그 외에는 False 를 반환해 pull 을 시작한다.
                * (NONE): 이미지가 로컬에 없으면 예외를 발생시킨다.
        * (pull 이 필요하면 ImagePullStartedEvent 를 발생시킨다)
            * (DockerAgent.pull_image):
                * (docker.images.pull): image_id 로 지정한 이미지를 pull 한다.
                * (성공하면 ImagePullFinishedEvent 를 발생시킨다)
                * (실패하면 ImagePullFailedEvent 를 발생시킨다)
        * (pull 이 필요 없으면 ImagePullFinishedEvent 를 발생시킨다)

---

## `create_kernels`

* **설명**: 계산 kernel(container)을 하나 이상 생성한다.
* **입력값**:
    * `raw_session_id: str`
    * `raw_kernel_ids: Sequence[str]`
    * `raw_configs: Sequence[dict]`
    * `raw_cluster_info: dict`
    * `kernel_image_refs: dict[KernelId, ImageRef]`
* **응답값**:
    * `list[dict]`: 생성에 성공한 kernel 정보(ID, host, port, container ID, 자원 사양 등)를 담은 dictionary 목록이다.
    * kernel 생성이 하나라도 실패하면 예외를 발생시킨다. 첫 번째 에러이거나, 여러 건이 실패하면 `TaskGroupError` 다.
* **부작용**:
    * (create_kernels): `kernel-creation-concurrency` 만큼의 semaphore 를 적용하고 `asyncio.gather` 로 kernel 을 생성하는 coroutine 을 실행한다.
        * (DockerAgent.init_kernel_context):
            * 이미지 label `ai.backend.base-distro` 가 있으면 그 값을 distro 로 사용한다.
            * 없으면 `redis_stat_pool` 의 `"image:{image_id}:distro"` cache 가 있을 때 그 값을 읽어 distro 로 사용한다.
            * cache 도 없으면 `aiodocker.containers.create` 로 container 를 생성해 `ldd --version` 을 실행하고, container log 에서 distro 를 읽어 `redis_stat_pool` 에 cache 한다.
        * (DockerAgent.check_image): `aiodocker.images.inspect` 로 지정한 이미지를 pull 해야 하는지, 이미 있는지 판단한다.
        * (DockerAgent.pull_image): `aiodocker.images.pull` 로 이미지를 pull 한다.
        * (DockerAgent.prepare_resource_spec): `config_dir` 아래 `resource.txt` 에서 kernel 자원 사양을 읽는다.
        * (DockerAgent.prepare_scratch):
            * host platform 이 `linux` 이면
                * `scratch_type` 이 `memory` 이면
                    * 새 kernel 의 `scratch_dir` 에 filesystem 을 생성한다(tmpfs 를 mount 하는 subprocess 를 띄운다).
                    * 새 kernel 의 `tmp_dir` 에 filesystem 을 생성한다(tmpfs 를 mount 하는 subprocess 를 띄운다).
                * `scratch_type` 이 `hostfile` 이면 새 kernel 의 `scratch_root` 에 loop-back file 을 생성한다.
            * Linux 가 아닌 host 에서는 `scratch_dir` 을 `mkdir` 만 한다.
            * `scratch_dir` 아래에 `config_dir` 과 `work_dir` 을 권한 `0o755` 로 생성한다.
        * (_clone_dotfiles): `ai.backend.runner` 아래 다음 `pkg_resources` 파일을 복사한다.
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
        * (_clone_dotfiles): `euid` 가 0 이면 복사한 파일의 `uid` 와 `gid` 를 `kernel-uid`, `kernel-gid` 로 변경한다.
        * (DockerKernelCreationContext.prepare_ssh)
            * 전달받은 SSH key 를 `config_dir/ssh/id_cluster` 에 작성한다.
            * 전달받은 SSH public key 를 `config_dir/ssh/id_cluster.pub` 에 작성한다.
            * `kernel_features` 에 `uid-match`(`KernelFeatures.UID_MATCH`)가 설정되어 있으면 작성한 SSH 파일의 소유자를 `kernel-uid`, `kernel-gid` 로 변경한다.
            * `cluster_info` 에 `cluster_ssh_port_mapping` 이 있으면 `config_dir/ssh/port-mapping.json` 에 작성한다.
        * (DockerKernelCreationContext.mount_krunner)
            * `runner/su-exec.{arch}.bin` 을 `/opt/kernel/su-exec` 에 bind mount 한다.
            * `runner/libbaihook.*.{arch}.so` 를 `/opt/kernel/libbaihook.so` 에 bind mount 한다.
            * `runner/dropbearmulti.{arch}.bin` 을 `/opt/kernel/dropbearmulti` 에 bind mount 한다.
            * `runner/sftp-server.{arch}.bin` 을 `/opt/kernel/sftp-server` 에 bind mount 한다.
            * `runner/tmux.{arch}.bin` 을 `/opt/kernel/tmux` 에 bind mount 한다.
            * `sandbox-type` 이 `"jail"` 이면 `runner/jail.*.{arch}.bin` 을 `/opt/kernel/jail` 에 bind mount 한다.
            * `runner/extract_dotfiles.py` 를 `/opt/kernel/extract_dotfiles.py` 에 bind mount 한다.
            * `runner/entrypoint.sh` 를 `/opt/kernel/entrypoint.sh` 에 bind mount 한다.
            * `runner/fantompass.py` 를 `/opt/kernel/fantompass.py` 에 bind mount 한다.
            * `runner/hash_phrase.py` 를 `/opt/kernel/hash_phrase.py` 에 bind mount 한다.
            * `runner/words.json` 을 `/opt/kernel/words.json` 에 bind mount 한다.
            * `runner/DO_NOT_STORE_PERSISTENT_FILES_HERE.md` 를 `/home/work/DO_NOT_STORE_PERSISTENT_FILES_HERE.md` 에 bind mount 한다.
            * 대상 libc 가 `musl` 이면 `runner/terminfo.alpine3.8` 을 `/home/work/.terminfo` 에 bind mount 한다.
            * `local_config.container.krunner_volume` 에 설정한 directory 를 `/opt/backend.ai` 에 volume mount 한다.
            * `LD_PRELOAD` 환경 변수를 `/opt/kernel/libbaihook.so` 로 설정해 `libbaihook.so` 가 먼저 load 되게 한다.
            * `ai/backend/kernel` package 를 `/opt/backend.ai/lib/python{pyver}/site-packages/ai/backend/kernel` 에 bind mount 한다.
            * `ai/backend/helpers` package 를 `/opt/backend.ai/lib/python{pyver}/site-packages/ai/backend/helpers` 에 bind mount 한다.
            * accelerator plugin 마다 `apply_accelerator_allocation` 을 호출한다.
                * 각 plugin 은 aiodocker 객체를 받아 `generate_docker_args` 로 자원 격리를 위한 Docker args 를 생성한다.
            * 각 plugin 의 `generate_accelerator_mounts` 를 호출하고 반환된 mount 를 `resource_spec.mounts` 에 추가한다.
            * plugin 이 추가 hook 을 필요로 하면 `/opt/kernel/{hook}.so` 를 bind mount 하고 그 path 를 `LD_PRELOAD` 에 추가한다.
        * (AbstractComputePlugin.get_attached_devices): 각 plugin 의 `get_attached_devices` 를 호출해 `KernelCreationContext` 로 전달할 장치 정보를 얻는다.
        * (DockerAgent.load_model_definition): inference model 에서만 실행한다.
            * `aiodocker.images.get` 로 이미지의 `CMD` 를 읽는다(deprecated 이며 `inspect` 로 대체해야 한다).
            * `model_definition_yaml` 에서 model definition 을 읽는다.
        * (restart_kernel__store_config): 새 kernel 설정을 pickle 형식으로 `config/kconfig.dat` 에 직렬화한다.
        * (restart_kernel__store_config): 새 cluster 설정을 pickle 형식으로 `config/cluster.json` 에 직렬화한다.
        * (DockerKernelCreationContext.prepare_container)
            * work directory 아래에 사용자 bootstrap script `/bootstrap.sh` 를 생성한다.
                * `KernelFeatures.UID_MATCH` 이면 소유자를 `kernel-uid/gid` 로 변경한다.
            * `config_dir` 아래에 다음 내용을 담아 `environ.txt` 를 작성한다.
                * 전달받은 `environ`
                * `self.computer_docker_args["Env"]` 항목
            * `config_dir` 아래에 다음 내용을 담아 `resource.txt` 를 작성한다.
                * `resource_spec.write_to_file` 의 출력
                * 각 accelerator 의 `instance.generate_resource_data` 가 만든 key-value 쌍
            * `internal_data.docker_credentials` 가 있으면 `config_dir/docker-creds.json` 에 저장한다.
            * `config_dir` 에서 `environ.txt` 를 `environ_base.txt` 로, `resource.txt` 를 `resource_base.txt` 로 복사한다.
            * `internal_data.ssh_keypair` 가 있고 `/home/work/.ssh` 가 mount 되지 않았으면
                * work dir 아래에 `.ssh`(0700)를 생성하고 `authorized_keys`, `id_rsa`, `id_container`(0600)를 생성한다.
                * `KernelFeatures.UID_MATCH` 이면 `.ssh` 와 그 파일의 소유자를 `kernel-uid/gid` 로 변경한다.
            * `internal_data.dotfiles` 의 각 path 를 처리한다.
                * 절대 path → 변경하지 않는다.
                * `"/home/"` 로 시작하는 path → `scratch_dir` 아래로 둔다.
                * 그 밖의 path → work directory 아래로 둔다.
                * dotfile 을 정한 path 에 작성하고 `dotfile["perm"]` 으로 `chmod` 한다.
                * `KernelFeatures.UID_MATCH` 이면 각 dotfile 과 상위 directory 의 소유자를 `kernel-uid/gid` 로 변경한다.
        * (DockerKernelCreationContext.start_container)
            * `HostConfig.NetworkMode` 가 `host` 이면 intrinsic port 정보(`replin`, `replout`, `sshd`, `ttyd`)를 `config_dir/intrinsic-ports.json` 에 작성한다.
            * 다음 path 에서 `agent-docker-container-opts.json` 을 추가로 읽어 container option 으로 적용한다.
                * `/etc/backend.ai`
                * `.config/backend.ai`
                * `~/.config/backend.ai`
            * `aiodocker.containers.create` 로 container 를 생성한다.
            * `config_dir/resource.txt` 를 다시 열어 다음을 기록한다.
                * `container_id`
                * plugin 이 `generate_resource_data` 로 가져온 추가 자원 정보
            * `aiodocker.containers.start` 로 container 를 시작한다.
            * `sudo_session_enabled` 이면 container 안에서 `sh -c "mkdir -p /etc/sudoers.d && echo 'work ALL=(ALL:ALL) NOPASSWD:ALL' > /etc/sudoers.d/01-bai-work"` 를 실행해 비밀번호 없는 sudo 를 활성화한다.
            * 각 accelerator 의 `get_docker_networks` 를 호출하고 `aiodocker.networks.get` 으로 DockerNetwork 객체를 얻어 연결한다.
            * `container.port` 를 호출해 container 의 port mapping 을 가져온다.
            * network plugin 의 `get_capabilities` 를 호출해 network 기능을 가져온다.
                * `GLOBAL` capability 가 있으면 `expose_ports` 를 호출해 container 시작 후 port 를 public network 에 노출한다.
            * `_clean_scratch` 에서 예외가 발생하면 `_rollback_container_creation` 을 호출해 `scratch` 와 accelerator 자원을 정리한다.
        * (AbstractKernel.init)
            * (DockerKernel.create_code_runner): `AbstractCodeRunner`(`DockerCodeRunner`) 객체를 생성한다.
        * (AbstractKernel.check_status)
            * runner 에 `status` message 를 보내 kernel runner 의 상태를 확인한다.
        * (KernelObjectType.get_service_apps)
            * runner 에 `get-apps` message 를 보내 service app 을 가져온다.
        * (DockerAgent.start_and_monitor_model_service_health): 재시작한 kernel 의 `session_type` 이 `INFERENCE` 이면
            * (AbstractKernel.start_model_service)
                * runner 에 `start-model-service` message 를 보내 model service 를 시작한다.
            * (ModelServiceStatusEvent) 를 발생시킨다.
                * (_dispatch_model_serving_events)
                * (handle_model_service_status_update)
                * (update_appproxy_endpoint_routes): DB 에서 자원 그룹의 App Proxy 주소를 읽고 `f"{wsproxy_addr}/v2/endpoints/{endpoint.id}"` 로 POST 요청을 보내 `endpoints` table 의 배포 엔드포인트 주소를 갱신한다.
        * (KernelStartedEvent) 를 발생시킨다.
            * (mark_kernel_running): DB 에서 kernel 의 status 를 `KernelStatus.RUNNING` 으로 갱신한다.

---

## `destroy_kernel`

* **설명**: 특정 계산 kernel(container)을 종료한다.
* **입력값**:
    * `kernel_id: str`
    * `session_id: str`
    * `reason: Optional[KernelLifecycleEventReason]`
    * `suppress_events: bool`
* **응답값**:
    * `asyncio.Future` 의 결과다. 보통 성공 시 `None` 이고, 종료에 실패하면 예외다.
* **부작용**:
    **Agent 쪽**:
        * (inject_container_lifecycle_event):
            * (_handle_destroy_event):
                * `registry_lock` 을 획득한다. kernel 이 이미 종료되었으면 `reconstruct_resource_usage` 를 호출하고 `KernelTerminatedEvent` 를 발생시킨다.
                * 그렇지 않으면 `AbstractAgent.destroy_kernel` 을 호출해 kernel 을 종료한다.
                    * (aiodocker.containers.stop):
                        * `container_id` 로 container 를 정지한다.
                    * kernel 이 이미 죽었거나 404 에러가 나면 `reconstruct_resource_usage` 를 호출한다.
                    * (reconstruct_resource_usage):
                        * (DockerAgent.enumerate_containers): 순회할 container 를 식별한다.
                            * (aiodocker.containers.list): container 를 나열한다.
                            * (get_kernel_id_from_container): container 이름에서 kernel ID 를 추출한다. container label `ai.backend.owner` 가 `DockerAgent.id` 와 같으면 `aiodocker.containers.show` 로 container 정보를 가져와 순회 대상에 포함한다.
                        * 각 accelerator 에서 `restore_from_container` 를 호출해 `alloc_map` 을 초기화한 뒤 `scratches` 아래 `resource.txt` 에서 `alloc_map` 을 다시 읽는다.
                    * (AbstractCodeRunner.close()):
                        * socket, task 같은 자원을 정리한다.
            * `ContainerLifecycleEvent` 를 `container_lifecycle_queue` 에 넣고 `process_lifecycle_events` 에서 처리한다.
            * (_handle_clean_event):
                * `_ongoing_destruction_tasks` 의 `destruction_task` 가 끝날 때까지 기다린 뒤 kernel 의 code-runner `close` 를 호출한다.
                * `DockerAgent.clean_kernel` 을 호출해 kernel 을 정리한다.
                * 예외가 발생하면 `AgentErrorEvent` 를 발생시킨다.
                * `AbstractKernel.close` 를 호출한다(`DockerAgent` 에서는 아무것도 하지 않는다).
                * 종료한 kernel 의 `kernel_id` 가 `restart_tracker` 에 있으면 해당 Event 를 설정하고, 없으면 `KernelTerminatedEvent` 를 발생시킨다.
                * `.AbstractKernel.clean_event` 와 `ev.done_future` 를 설정해 kernel 정리가 끝났음을 알린다.
            * (collect_logs):
                * 수집한 container log 를 `redis_stream_pool` 의 `containerlog.{container_id}` 에 작성한다.
            * kernel 에 domain-socket proxy 가 있으면 `proxy_server.wait_close` 를 호출한다.
            * (aiodocker.containers.delete): container 를 삭제한다.
            * (_clean_scratch): `scratch` 와 `tmp_dir` path 의 filesystem 을 unmount 하고 `rmtree` 로 제거한다. `scratch_root` loop filesystem 도 삭제하고, network plugin 이 설정되어 있으면 plugin 의 `leave_network` 를 호출해 network 를 정리한다.
    **Manager 쪽**:
        * (handle_kernel_terminated): `KernelTerminatedEvent` 를 받으면 호출된다.
        * (mark_kernel_terminated):
            * (recalc_agent_resource_occupancy):
                * `redis_stat.keypair.concurrency_used.{access_key}` 를 갱신한다.
                * `redis_stat.keypair.sftp_concurrency_used.{access_key}` 를 갱신한다.
            * (recalc_concurrency_used): kernel table 을 갱신한다.
        * (session_lifecycle_mgr.register_status_updatable_session): 갱신이 필요한 session 을 `redis_obj.session_status_update` set 에 PUSH 한다.
        * `DoUpdateSessionStatusEvent` 를 발생시킨다.
        * (SchedulerDispatcher.update_session_status): `DoUpdateSessionStatusEvent` 를 처리한다.
        * (update_session_status): `redis_obj.session_status_update` set 에서 session status 갱신 event 를 가져와 session status 를 갱신한다.
        * (transit_session_status): `sessions` table 의 session status 를 갱신한다.
        * (_post_status_transition): `SessionTerminatedEvent` 를 발생시킨다.
        * (handle_session_terminated): `SessionTerminatedEvent` 를 처리한다.
        * (AgentRegistry.clean_session):
            * `SINGLE_NODE` 이면 `destroy_local_network` 를 호출한다.
            * `MULTI_NODE` 이면 network plugin 의 `destroy_network` 를 호출한다.
        * (invoke_session_callback): 종료한 session 이 inference session 일 때 호출된다.
            * `routings` table 을 갱신한다.
            * (agent_registry.update_appproxy_endpoint_routes): `{wsproxy_addr}/v2/endpoints/{endpoint.id}` 로 POST 요청을 보내 `endpoints` table 을 갱신한다.
        * (_clear_error): 삭제한 session 에 `callback_url` 이 있으면
            * (_make_session_callback): `{callback_url}` 로 session lifecycle event 를 보내 session 이 종료되었음을 알린다.

---

## `interrupt_kernel`

* **설명**: 실행 중인 kernel 에 interrupt 신호를 보낸다.
* **입력값**:
    * `kernel_id: str`
* **응답값**:
    * `None`.
* **부작용**:
    * (DockerAgent.interrupt_kernel)
    * (DockerKernel.interrupt_kernel)
    * (AbstractCodeRunner.feed_interrupt):
        * runner 에 `interrupt` message 를 보낸다.
    * (BaseRunner.main_loop):
        * `interrupt` message 를 받으면 `self._interrupt` 를 호출해 subprocess 에 `SIGINT` 신호를 보낸다.
        * BaseRunner 에 `kernel_mgr` attribute 가 있으면 `AsyncKernelManager.interrupt_kernel`(Jupyter client)을 호출한다.

---

## `get_completions`

* **설명**: kernel 에 code completion 을 요청한다.
* **입력값**:
    * `kernel_id: str`
    * `text: str`
    * `opts: dict`
* **응답값**:
    * 제안하는 code completion 을 담은 completion 결과를 JSON 으로 parse 해서 반환한다.
* **부작용**:
    * (AbstractCodeRunner.get_completions):
    * (AbstractKernel.get_completions):
    * (AbstractCodeRunner.feed_and_get_completion):
        * runner 에 `complete` message 를 보낸다.
    * (BaseRunner.main_loop):
        * `complete` message 를 받으면 `self._complete` 를 호출한다.
    * (BaseRunner.complete):
        * auto-complete 목록에 표시할 문자열을 반환한다. 현재 구현은 빈 목록을 반환하는 것으로 보인다.

---

## `get_logs`

* **설명**: 특정 kernel 의 container 에서 log 를 가져온다.
* **입력값**:
    * `kernel_id: str`
* **응답값**:
    * kernel log 를 JSON 으로 parse 한 결과
* **부작용**:
    * (aiodocker.containers.get):
        * `container_id` 로 container 정보를 가져온다.
    * (aiodocker.containers.log):
        * container 의 log 를 가져와 반환한다.

---

## `restart_kernel`

* **설명**: kernel 을 재시작한다.
* **입력값**:
    * `kernel_id: str`
    * `session_id: str`
    * `kernel_image: ImageRef`
    * `updated_config: dict`
* **응답값**:
    * `dict[str, Any]`: 새로 재시작한 kernel 의 정보다(`create_kernels` 의 kernel 하나 응답과 비슷하다).
* **부작용**:
    * (restart_kernel__load_config): scratch directory 에서 이전 kernel 의 `kconfig.dat` 을 읽는다.
    * (restart_kernel__load_config): scratch directory 에서 이전 kernel 의 `cluster.json` 을 읽는다.
    * (_handle_destroy_event)
        * kernel_id 가 kernel registry 에 등록되어 **있지 않으면**(이미 종료됨)
            * (reconstruct_resource_usage): agent 의 accelerator 마다 `restore_from_container` 를 통해 scratch directory 의 `resource.txt` 에서 alloc_map 을 읽는다.
        * **등록되어 있으면**
            * (AbstractCodeRunner.close): 이전 kernel runner 의 자원(watchdog_task, status_task, read_task, input_sock, output_sock)을 정리한다.
        * (destroy_kernel):
            * (aiodocker.containers.stop): 이전 kernel container 를 정지한다.
                * 예외가 발생하면 reconstruct_resource_usage 를 호출한다.
    * (_handle_clean_event)
        * (aiodocker.containers.log): 이전 kernel container 의 log 를 수집한다.
        * (DockerAgent.collect_logs): 수집한 container log 를 `redis_stream_pool` 의 `containerlog.{container_id}` 에 작성한다. log 는 1시간 뒤 만료되도록 설정한다.
            * DoSyncKernelLogsEvent 를 publish 한다.
            * (handle_kernel_log): Manager 가 `DoSyncKernelLogsEvent` 를 받아 log 를 DB `kernels` table 의 `container_log` column 에 작성한 뒤 Valkey 에서 삭제한다.
        * (aiodocker.containers.delete): 이전 kernel container 를 삭제한다.
        * (clean_kernel): kernel 에 `domain_socket_proxies` 가 있으면 `proxy_server.wait_close()` 를 호출해 domain-socket proxy 를 정리한다.
        * (_clean_scratch): scratch path 와 tmp_dir 의 filesystem 을 unmount 하고 rmtree 로 제거한 뒤 scratch_root loop filesystem 을 제거한다.
        * kernel 의 network driver 가 `bridge` 가 아니면 plugin 의 `leave_network` 를 호출해 network 를 정리한다.
    * (DockerAgent.init_kernel_context):
        * (DockerAgent.resolve_image_distro):
            * 이미지 label `ai.backend.base-distro` 가 설정되어 있으면 그 값을 distro 로 사용한다.
            * 없으면 `redis_stat_pool` 에 `"image:{image_id}:distro"` cache 가 있을 때 읽어 distro 로 사용한다.
            * cache 가 없으면 `aiodocker.containers.create` 로 container 를 생성해 `ldd --version` 을 실행하고, container log 에서 distro 를 읽어 `redis_stat_pool` 에 cache 한다.
    * (DockerAgent.check_image): `aiodocker.images.inspect` 로 이미지를 pull 해야 하는지, 이미 있는지 판단한다.
    * (DockerAgent.pull_image): `aiodocker.images.pull` 로 이미지를 pull 한다.
    * (DockerAgent.prepare_resource_spec): `config_dir` path 아래 `resource.txt` 에서 kernel 자원 사양을 읽는다.
    * (DockerAgent.prepare_scratch):
        * host platform 이 `linux` 이면
            * `scratch_type` 이 `memory` 이면
                * 새 kernel 의 `scratch_dir` 에 filesystem 을 생성한다(tmpfs 를 mount 하는 subprocess 를 띄운다).
                * 새 kernel 의 `tmp_dir` 에 filesystem 을 생성한다(tmpfs 를 mount 하는 subprocess 를 띄운다).
            * `scratch_type` 이 `hostfile` 이면 새 kernel 의 `scratch_root` 에 loop file 을 생성한다.
        * Linux 가 아닌 host 에서는 `scratch_dir` 을 `mkdir` 만 한다.
        * `scratch_dir` 아래에 `config_dir` 과 `work_dir` 을 권한 `0o755` 로 생성한다.
    * (_clone_dotfiles): `ai/backend/runner` 아래 다음 `pkg_resources` 파일을 복사한다.
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
    * (_clone_dotfiles): agent process 의 `euid` 가 0 이면 복사한 파일의 `uid` 와 `gid` 를 `kernel-uid`, `kernel-gid` 로 변경한다.
    * (DockerKernelCreationContext.prepare_ssh)
        * 전달받은 SSH key 를 `config_dir/ssh/id_cluster` 에 작성한다.
        * 전달받은 SSH public key 를 `config_dir/ssh/id_cluster.pub` 에 작성한다.
        * `uid-match`(`KernelFeatures.UID_MATCH`)가 설정되어 있으면 작성한 SSH 파일의 소유자를 `kernel-uid`, `kernel-gid` 로 변경한다.
        * `cluster_info` 에 `cluster_ssh_port_mapping` 이 있으면 `config_dir/ssh/port-mapping.json` 에 기록한다.
    * (DockerKernelCreationContext.mount_krunner)
        * `runner/su-exec.{arch}.bin` 을 `/opt/kernel/su-exec` 에 bind mount 한다.
        * `runner/libbaihook.*.{arch}.so` 를 `/opt/kernel/libbaihook.so` 에 bind mount 한다.
        * `runner/dropbearmulti.{arch}.bin` 을 `/opt/kernel/dropbearmulti` 에 bind mount 한다.
        * `runner/sftp-server.{arch}.bin` 을 `/opt/kernel/sftp-server` 에 bind mount 한다.
        * `runner/tmux.{arch}.bin` 을 `/opt/kernel/tmux` 에 bind mount 한다.
        * `sandbox-type` 이 "jail" 이면 `runner/jail.*.{arch}.bin` 을 `/opt/kernel/jail` 에 bind mount 한다.
        * `runner/extract_dotfiles.py` 를 `/opt/kernel/extract_dotfiles.py` 에 bind mount 한다.
        * `runner/entrypoint.sh` 를 `/opt/kernel/entrypoint.sh` 에 bind mount 한다.
        * `runner/fantompass.py` 를 `/opt/kernel/fantompass.py` 에 bind mount 한다.
        * `runner/hash_phrase.py` 를 `/opt/kernel/hash_phrase.py` 에 bind mount 한다.
        * `runner/words.json` 을 `/opt/kernel/words.json` 에 bind mount 한다.
        * `runner/DO_NOT_STORE_PERSISTENT_FILES_HERE.md` 를 `/home/work/DO_NOT_STORE_PERSISTENT_FILES_HERE.md` 에 bind mount 한다.
        * 대상 libc 가 `musl` 이면 `runner/terminfo.alpine3.8` 을 `/home/work/.terminfo` 에 bind mount 한다.
        * `local_config.container.krunner_volume` 에 설정한 directory 를 `/opt/backend.ai` 에 volume mount 한다.
        * `LD_PRELOAD` 환경 변수를 `/opt/kernel/libbaihook.so` 로 설정해 먼저 load 되게 한다.
        * `ai/backend/kernel` package 를 `/opt/backend.ai/lib/python{pyver}/site-packages/ai/backend/kernel` 에 bind mount 한다.
        * `ai/backend/helpers` package 를 `/opt/backend.ai/lib/python{pyver}/site-packages/ai/backend/helpers` 에 bind mount 한다.
        * accelerator plugin 마다 `apply_accelerator_allocation` 을 호출한다.
            * 각 plugin 은 aiodocker 객체를 받아 `generate_docker_args` 로 자원 격리를 위한 Docker args 를 생성한다.
        * 각 plugin 의 `generate_accelerator_mounts` 를 호출하고 반환된 mount 를 `resource_spec.mounts` 에 추가한다.
        * accelerator plugin 이 추가 hook 을 필요로 하면 `/opt/kernel/{hook}.so` 를 bind mount 하고 그 path 를 `LD_PRELOAD` 에 추가한다.
    * (AbstractComputePlugin.get_attached_devices): 각 plugin 의 `get_attached_devices` 를 호출해 KernelCreationContext 로 전달할 장치 정보를 얻는다.
    * (DockerAgent.load_model_definition): inference model 에서만 실행한다.
        * `aiodocker.images.get` 로 이미지의 `CMD` 를 읽는다(deprecated 이며 `inspect` 로 대체해야 한다).
        * `model_definition_yaml` 에서 model definition 을 읽는다.
    * (restart_kernel__store_config): 새 kernel 설정을 pickle 로 `config/kconfig.dat` 에 직렬화한다.
    * (restart_kernel__store_config): 새 cluster 설정을 pickle 로 `config/cluster.json` 에 직렬화한다.
    * (DockerKernelCreationContext.prepare_container)
        * work directory 아래에 사용자 bootstrap script `/bootstrap.sh` 를 생성한다.
            * `KernelFeatures.UID_MATCH` 이면 소유자를 kernel-uid/gid 로 변경한다.
        * `config_dir` 아래에 다음 내용을 담아 `environ.txt` 를 작성한다.
            * 전달받은 `environ`
            * `self.computer_docker_args["Env"]` 항목
        * `config_dir` 아래에 다음 내용을 담아 `resource.txt` 를 작성한다.
            * `resource_spec.write_to_file` 출력
            * 각 accelerator 의 `instance.generate_resource_data` 가 만든 key-value 쌍
        * `internal_data.docker_credentials` 가 있으면 `config_dir/docker-creds.json` 에 저장한다.
        * `config_dir` 에서 `environ.txt` 를 `environ_base.txt` 로, `resource.txt` 를 `resource_base.txt` 로 복사한다.
        * `internal_data.ssh_keypair` 가 있고 `/home/work/.ssh` 가 mount 되지 않았으면
            * work dir 아래에 `.ssh`(0700)를 생성하고 `authorized_keys`, `id_rsa`, `id_container`(0600)를 생성한다.
            * `KernelFeatures.UID_MATCH` 이면 `.ssh` 와 그 파일의 소유자를 kernel-uid/gid 로 변경한다.
        * `internal_data.dotfiles` 의 각 path 를 처리한다.
            * 절대 path → 변경하지 않는다.
            * `"/home/"` 로 시작하는 path → `scratch_dir` 아래로 둔다.
            * 그 밖의 path → `work` directory 아래로 둔다.
            * dotfile 을 정한 path 에 작성하고 `dotfile["perm"]` 으로 chmod 한다.
            * `KernelFeatures.UID_MATCH` 이면 각 dotfile 과 상위 dir 의 소유자를 kernel-uid/gid 로 변경한다.
    * (DockerKernelCreationContext.start_container)
        * `HostConfig.NetworkMode` 가 `host` 이면
            * intrinsic port 정보(`replin`, `replout`, `sshd`, `ttyd`)를 `config_dir/intrinsic-ports.json` 에 작성한다.
        * 다음 path 에서 `agent-docker-container-opts.json` 을 추가로 읽어 container option 으로 적용한다.
            * `/etc/backend.ai`
            * `.config/backend.ai`
            * `~/.config/backend.ai`
        * `aiodocker.containers.create` 로 container 를 생성한다.
        * `config_dir/resource.txt` 를 다시 열어 `container_id` 를 기록하고, plugin 이 `generate_resource_data` 로 제공한 자원 정보를 함께 기록한다.
        * `aiodocker.containers.start` 로 container 를 시작한다.
        * `sudo_session_enabled` 이면 `aiodocker.containers.exec` 로 `sh -c mkdir -p /etc/sudoers.d && echo "work ALL=(ALL:ALL) NOPASSWD:ALL" > /etc/sudoers.d/01-bai-work` 를 실행해 container 안에서 비밀번호 없는 sudo 를 설정한다.
        * 각 accelerator 의 `get_docker_networks` 를 호출하고 `aiodocker.networks.get` 으로 DockerNetwork 객체를 가져와 연결한다.
        * `container.port` 를 호출해 container 의 port 정보를 가져온다.
        * network plugin 의 `network_config.mode` 가 `bridge` 가 아니면 `get_capabilities` 를 호출해 network capability 를 가져온다.
            * `GLOBAL` capability 가 있으면 plugin 의 `expose_ports` 를 호출해 container 시작 후 port 를 public network 에 노출한다.
        * (DockerKernelCreationContext._apply_seccomp_profile): `runner/default-seccomp.json` 의 기본 seccomp profile 을 적용하고 추가 syscall 을 `SecurityOpt` 에 덧붙인다.
        * `_clean_scratch` 에서 예외가 발생하면 `_rollback_container_creation` 을 호출해 `scratch` 와 accelerator 자원을 정리한다.
    * (AbstractKernel.init)
        * (DockerKernel.create_code_runner): `AbstractCodeRunner`(`DockerCodeRunner`) 객체를 생성한다.
    * (DockerKernel.check_status)
        * runner 에 `status` message 를 보내 kernel runner 상태를 확인한다.
    * (KernelObjectType.get_service_apps)
        * runner 에 `get-apps` message 를 보내 service app 을 가져온다.
    * (DockerAgent.start_and_monitor_model_service_health): 재시작한 kernel 의 `session_type` 이 `INFERENCE` 이면
        * (AbstractKernel.start_model_service)
            * runner 에 `start-model-service` message 를 보내 model service 를 시작한다.
        * (BaseRunner.start_model_service)
            * (BaseRunner._start_service): `model-service-result` 로 model service 시작 결과를 받는다.
                * (ServiceParser.start_service): `ServiceDefinition.prestart_actions` 에 나열된 action 을 실행한다.
                * (AbstractCodeRunner.read_output): `LD_LIBRARY_PATH` 에서 `"/opt/backend.ai/lib:"` 를 제거한다.
                * (asyncio.create_subprocess_exec): model service subprocess 를 시작한다.
                * (wait_local_port_open): `service_info.port` 로 지정한 로컬 port 가 열릴 때까지 기다린다.
        * ModelServiceStatusEvent 를 publish 한다.
            * (_dispatch_model_serving_events)
            * (handle_model_service_status_update): Manager 가 `ModelServiceStatusEvent` 를 받는다.
            * (AgentRegistry.update_appproxy_endpoint_routes): DB 에서 배포 엔드포인트의 자원 그룹 App Proxy 주소를 읽고 `f"{wsproxy_addr}/v2/endpoints/{endpoint.id}"` 로 POST 요청을 보내 `endpoints` table 의 배포 엔드포인트 주소를 갱신한다.
    * KernelStartedEvent 를 publish 한다.
        * (AgentRegistry.mark_kernel_running): DB 에서 kernel 의 status 를 `KernelStatus.RUNNING` 으로 갱신한다.

---

## `execute`

* **설명**: 지정한 kernel 안에서 code 를 실행한다.
* **입력값**:
    * `session_id: str`
    * `kernel_id: str`
    * `api_version: int`
    * `run_id: str`
    * `mode: Literal["query", "batch", "continue", "input"]`
    * `code: str`
    * `opts: dict[str, Any]`
    * `flush_timeout: float`
* **응답값**:
    * `dict[str, Any]`: 실행 결과와 file field 를 담은 dictionary 다.
        ```json
        {
            execution result,
            "files": [],  # kept for API backward-compatibility
        }
        ```
* **부작용**:
    * (AbstractCodeRunner.execute):
    * (AbstractKernel.execute):
        * (AbstractCodeRunner.attach_output_queue):
            * `run_id`(`secrets.token_hex(16)`)를 생성해 `self.pending_queues` 에 추가한다. 그 queue 에 `asyncio.Event` 객체를 주입한다.
            * `next_output_queue` 가 주입한 Event 객체를 설정할 때까지 기다린다.
        * mode 가 "batch" 이면 `feed_batch` 를 호출한다.
            * `clean`, `build`, `exec` message 를 차례로 보낸다.
        * mode 가 "query" 이면 `feed_code` 를 호출한다.
            * `code` message 를 보낸다.
        * mode 가 "input" 이면 `feed_input` 을 호출한다.
            * `input` message 를 보낸다.
        * mode 가 "continue" 이면 건너뛴다.
    * (AbstractCodeRunner.get_next_result): `aggregate_console` 로 `NextResult` 객체를 생성한다.
        * 정상 완료(`RunFinished`)이면 다음 queue(`next_output_queue`)로 넘어간다.
        * 그 밖의 경우(`BuildFinished`, `CleanFinished`, `TimeoutError` 등)에는 현재 queue 를 tail 로 옮긴 뒤 출력 queue 를 다시 시작한다(`resume_output_queue`).
    * (AbstractCodeRunner.close): socket, task 같은 CodeRunner 내부 자원을 정리한다.

---

## `trigger_batch_execution`

* **설명**: kernel 의 batch 실행 task 를 시작한다.
* **응답값**:
    * `None`.
* **부작용**:
    * `self.agent.create_batch_execution_task()` 를 호출한다. 이 method 는 보통 agent 안에서 batch 처리를 위해 kernel 에 code 를 공급하는 background process 나 수단을 준비한다.

---

## `start_service`

* **설명**: kernel 의 container 안에서 지정한 service 를 시작한다.
* **응답값**:
    * `dict[str, Any]`: 시작한 service 의 정보(access point, status 등)를 담은 dictionary 다.
* **부작용**:
    * (DockerAgent.start_service)
    * (DockerKernel.start_service):
    * (AbstractCodeRunner.feed_start_service)
        * runner 에 `start-service` message 를 보내고,
        * (read_output) `service_queue` 로 `service-result` 를 받아 service 이름, port 번호, protocol, option 등을 JSON 으로 반환한다.

---

## `get_commit_status`

* **설명**: kernel 에서 진행 중이거나 이전에 실행한 commit 동작의 상태를 확인한다.
* **입력값**:
    * `kernel_id: KernelId`: 사용 중인 kernel 의 식별자
    * `subdir: str`: 파일이나 출력을 정리하는 path
* **응답값**:
    * `CommitStatus`
        * image commit 이 진행 중이면(lock_path(image-comit-path / subdir / lock / kernel_id)가 있으면) 응답값은 `CommitStatus.ONGOING` 이다.
        * image commit 이 완료되었으면(lock_path 가 없으면) 응답값은 `CommitStatus.READY` 다.
* **부작용**:
    * `kernel_id` 의 kernel 에 `check_duplicate_commit(kernel_id, subdir)` method 를 호출한다.

---

## `commit`

* **설명**: kernel container 의 현재 상태(또는 그 안의 하위 directory)를 새 image 로 commit 한다.
* **입력값**:
    * `reporter: ProgressReporter` : 진행 상황을 추적하고 보고하는 ProgressReporter instance(현재는 사용하지 않는다)
    * `kernel_id: KernelId`: 사용 중인 kernel 의 식별자
    * `subdir: str`: 파일이나 출력을 정리하는 path
    * `canonical: str | None = None`: 참조용 canonical name 또는 path(선택)
    * `filename: str | None = None`: 출력이나 식별에 사용할 filename(선택)
    * `extra_labels: dict[str, str] = {}`: 추가 label dictionary
* **응답값**:
    * `None`
* **부작용**:
    * 같은 인자로 kernel 의 `commit` method 를 호출한다.
        * 지정한 출력 path 와 lock_path 에 필요한 directory 를 생성한다.
        * 전달받은 canonical 과 label 로 새 image 를 commit 한다.
        * `filename` 이 있으면 새로 생성한 Docker image 를 gzip tarball 로 `path / filename` 에 내보낸다. 내보내기에 성공하면 앞 단계에서 생성한 중간 Docker image 를 삭제한다.
        * lock_path 는 commit 과정이 모두 끝난 뒤 제거된다.

### 테스트 시나리오 1 - 내보내기 없는 기본 commit

* **사전 조건**:
    * `kernel_id_VALID` kernel 이 실행 중이고 그 container 가 있다.
    * Docker image `myimage:basic_commit` 이 현재 로컬 Docker image 목록에 없다.
    * host 에 `{base_commit_path}/test_commit_no_export/` 와 `{base_commit_path}/test_commit_no_export/lock/` directory 가 있을 수도 있고 없을 수도 있다.
* **실행**:
    * 다음 입력값으로 `commit` method 를 호출한다.
        * `reporter`: mock `ProgressReporter` instance
        * `kernel_id`: `kernel_id_VALID`
        * `subdir`: `"test_commit_no_export"`
        * `canonical`: `"myimage"`
        * `filename`: `None`
        * `extra_labels`: `{"author": "test_user", "version": "1.0"}`
* **기대 결과**:
    * method 는 아무것도 반환하지 않는다.
    * `{base_commit_path}/test_commit_no_export/` directory 가 없었다면 host 에 생성된다.
    * `{base_commit_path}/test_commit_no_export/lock/` directory 가 없었다면 host 에 생성된다.
    * `myimage:latest` tag 가 붙은 새 Docker image 가 로컬 Docker image 목록에 있다.
    * 생성한 Docker image `myimage:latest` 에 `author="test_user"` 와 `version="1.0"` label 이 있다.
    * host filesystem 에 gzip tarball 파일이 생성되지 않는다(`filename` 이 `None` 이었기 때문이다).
    * 이 동작으로 Docker image `myimage:latest` 가 로컬 Docker image 목록에서 삭제되지 않는다.

### 테스트 시나리오 2 - 내보내기를 포함한 commit

* **사전 조건**:
    * agent 가 실행 중이다.
    * `kernel_id_VALID` kernel 이 실행 중이고 그 container 가 있다.
    * Docker image `myimage:exported_commit` 이 현재 없다.
    * host filesystem 의 `{base_commit_path}/test_commit_with_export/exported_image.tar.gz` 파일이 없다.
    * `{base_commit_path}/test_commit_with_export/` 와 `{base_commit_path}/test_commit_with_export/lock/` directory 가 있을 수도 있고 없을 수도 있다.
* **실행**:
    * 다음 입력값으로 `commit` method 를 호출한다.
        * `reporter`: mock `ProgressReporter` instance
        * `kernel_id`: `kernel_id_VALID`
        * `subdir`: `"test_commit_with_export"`
        * `canonical`: `"myimage:exported_commit"`
        * `filename`: `"exported_image"`
        * `extra_labels`: `{"status": "exported"}`
* **기대 결과**:
    * method 는 아무것도 반환하지 않는다.
    * `{base_commit_path}/test_commit_with_export/` directory 가 없었다면 host 에 생성된다.
    * `{base_commit_path}/test_commit_with_export/lock/` directory 가 없었다면 host 에 생성된다.
    * 동작 중에 host 의 `{base_commit_path}/test_commit_with_export/lock/{kernel_id_VALID}` path 에 `{kernel_id_VALID}` 이름의 lock file 이 생성되고, 완료하거나 실패하면 제거된다.
    * host filesystem 의 `{base_commit_path}/test_commit_with_export/exported_image` path 에 `exported_image` 이름의 gzip tarball 파일이 있다.
    * Docker image `myimage:exported_commit` 이 로컬 Docker image 목록에 더 이상 없다.

### 테스트 시나리오 3 - canonical name 없는 commit

* **사전 조건**:
    * agent 가 실행 중이다.
    * `kernel_id_VALID` kernel 이 실행 중이고 그 container 가 있다.
    * `{base_commit_path}/test_commit_no_canonical/` 와 `{base_commit_path}/test_commit_no_canonical/lock/` directory 가 있을 수도 있고 없을 수도 있다.
* **실행**:
    * 다음 입력값으로 `commit` method 를 호출한다.
        * `reporter`: mock `ProgressReporter` instance
        * `kernel_id`: `kernel_id_VALID`
        * `subdir`: `"test_commit_no_canonical"`
        * `canonical`: `None`
        * `filename`: `None`
        * `extra_labels`: `{}`
* **기대 결과**:
    * method 는 아무것도 반환하지 않는다.
    * `{base_commit_path}/test_commit_no_canonical/` directory 가 없었다면 host 에 생성된다.
    * `{base_commit_path}/test_commit_no_canonical/lock/` directory 가 없었다면 host 에 생성된다.
    * `{base_commit_path}/test_commit_no_canonical/lock/{kernel_id_VALID}` 에 `{kernel_id_VALID}` 이름의 lock file 이 생성되고 이후 제거된다.
    * 새 Docker image 가 생성된다. 그 식별자(예: image ID)를 확인할 수 있어야 하며, `<none>:<none>` 같은 구체적인 tag 는 Docker 의 기본 commit 동작에 따른다.
    * host filesystem 에 gzip tarball 파일이 생성되지 않는다.
    * 생성한 Docker image 가 이 동작으로 삭제되지 않는다.

### 테스트 시나리오 4 - 존재하지 않는 kernel ID 에 대한 commit

* **사전 조건**:
    * agent 가 실행 중이다.
    * `kernel_id_INVALID` kernel 이 없거나 실행 상태가 아니다.
    * Docker image `myimage:fail_commit` 이 없다.
* **실행**:
    * 다음 입력값으로 `commit` method 를 호출한다.
        * `reporter`: mock `ProgressReporter` instance
        * `kernel_id`: `kernel_id_INVALID`
        * `subdir`: `"test_commit_invalid_kernel"`
        * `canonical`: `"myimage:fail_commit"`
        * `filename`: `None`
        * `extra_labels`: `{}`
* **기대 결과**:
    * method 는 아무것도 반환하지 않는다.
    * `self.kernel_registry[kernel_id]` 에서 kernel 을 찾지 못해 `KeyError` 를 발생시킨다.

### 테스트 시나리오 5 - 같은 kernel 과 subdir 에 대한 동시 commit 시도

* **사전 조건**:
    * agent 가 실행 중이다.
    * `kernel_id_A` kernel 이 실행 중이고 그 container 가 있다.
* **실행**:
    * 거의 동시에 `commit` method 를 두 번 호출한다. `kernel_id_A` 와 `subdir_X` 는 *같고* 나머지 인자는 다를 수 있다.
        * 호출 1: `kernel_id_A`, `subdir_X`, `canonical="img1:tag1"`, `filename="f1.tar.gz"`
        * 호출 2: `kernel_id_A`, `subdir_X`, `canonical="img2:tag2"`, `filename="f2.tar.gz"`
* **기대 결과**:
    * 두 호출 중 하나(예: 호출 1)가 성공적으로 끝난다.
    * 다른 호출(예: 호출 2)은 호출 1 이후에 끝난다.
    * 기대한 성공 부작용은 한 차례만 일어난다.
        * Docker image `img1:tag1` 이 임시로 생성되고 `f1.tar.gz` 파일이 `{base_commit_path}/subdir_X/f1.tar.gz` 로 내보내진 뒤 image `img1:tag1` 이 삭제된다.
        * 이어서 Docker image `img2:tag2` 가 임시로 생성되고 `f2.tar.gz` 파일이 `{base_commit_path}/subdir_X/f2.tar.gz` 로 내보내진 뒤 image `img2:tag2` 가 삭제된다.
        * 마지막에는 `f1.tar.gz` 와 `f2.tar.gz` 파일이 모두 있다.

---

## `push_image`

* **설명**: 로컬에서 build 하거나 commit 한 image 를 지정한 container registry 로 push 한다.
* **입력값**:
    * `image_ref: ImageRef`: container image 참조
    * `registry_conf: ImageRegistry`: image registry 설정
    * `timeout: float | None | Sentinel = Sentinel.TOKEN` : 초 단위 timeout 값. timeout 을 설정하지 않을 때는 sentinel 을 사용한다.
* **응답값**:
    * `None`
* **부작용**:
    * image_ref 가 local 이면 agent 는 아무것도 하지 않는다.
    * registry username 과 password 로 만든 인증 정보로 container runtime 이 image 를 push 한다.
    * image push 에 실패하면 `RuntimeError` 를 발생시킨다.

### 테스트 시나리오 1 - private registry 에 인증해 push 성공

* **사전 조건**:
    * `image_to_push_private` 라는 `ImageRef` instance 를 다음과 같이 정의한다.
        * `name="myimage"`
        * `project="myproject"`
        * `tag="latest"`
        * `registry="myprivatereg.example.com"`
        * `architecture="amd64"`
        * `is_local=False`
    * `image_to_push_private` 에서 유도한 canonical name(예: `"myprivatereg.example.com/myproject/myimage:latest"`)에 해당하는 로컬 Docker image 가 agent 의 로컬 Docker 저장소에 있다.
    * `private_registry_config` 라는 `ImageRegistry` instance 를 다음과 같이 정의한다.
        * `name="myprivatereg.example.com"`
        * `url="https://myprivatereg.example.com"`
        * `username="valid_user"`
        * `password="valid_password"`
    * `image_to_push_private.canonical` 에서 유도한 image 가 `private_registry_config.url` 의 원격 private registry 에 아직 없거나 다시 push 해 교체할 수 있다.
* **실행**:
    * 다음 인자로 `push_image` method 를 호출한다.
        * `image_ref`: `image_to_push_private`
        * `registry_conf`: `private_registry_config`
        * `timeout`: 적절한 값(예: `300.0`) 또는 기본값 `Sentinel.TOKEN`
* **기대 결과**:
    * method 가 성공적으로 끝나고 `None` 을 반환한다(예외가 발생하지 않는다).
    * `image_to_push_private.canonical` 에서 유도한 Docker image 가 원격 private registry `myprivatereg.example.com` 에 push 되어 그곳에 있다. 원격 registry 를 조회해 확인한다.

### 테스트 시나리오 2 - local 로 표시된 이미지 push 시도

* **사전 조건**:
    * `local_image_ref` 라는 `ImageRef` instance 를 다음과 같이 정의한다.
        * `name="mylocalimg"`
        * `project=None`
        * `tag="test"`
        * `registry="local"`
        * `architecture="amd64"`
        * `is_local=True`
* **실행**:
    * 다음 인자로 `push_image` method 를 호출한다.
        * `image_ref`: `local_image_ref`
        * `registry_conf`: `any_registry_config`
        * `timeout`: 적절한 값 또는 기본값
* **기대 결과**:
    * method 가 즉시 성공적으로 끝나고 `None` 을 반환한다.
    * `local_image_ref.canonical` 에서 유도한 image 를 원격 registry 로 push 하려는 시도가 없다.
    * Docker push 관련 에러가 log 에 남거나 발생하지 않는다.

### 테스트 시나리오 3 - 인증 실패로 인한 push 실패

* **사전 조건**:
    * `image_for_auth_fail` 이라는 `ImageRef` instance 를 다음과 같이 정의한다.
        * `name="imageauthfail"`
        * `project="secureproject"`
        * `tag="1.0"`
        * `registry="myprivatereg.example.com"`
        * `architecture="amd64"`
        * `is_local=False`
    * `image_for_auth_fail.canonical` 에 해당하는 로컬 Docker image 가 agent 의 로컬 Docker 저장소에 있다.
    * `invalid_auth_registry_config` 라는 `ImageRegistry` instance 를 다음과 같이 정의한다.
        * `name="myprivatereg.example.com"`
        * `url="https://myprivatereg.example.com"`
        * `username="invalid_user"`
        * `password="wrong_password"`
* **실행**:
    * 다음 인자로 `push_image` method 를 호출한다.
        * `image_ref`: `image_for_auth_fail`
        * `registry_conf`: `invalid_auth_registry_config`
        * `timeout`: 적절한 값 또는 기본값
* **기대 결과**:
    * method 가 `RuntimeError` 를 발생시킨다.
    * `image_for_auth_fail.canonical` 에서 유도한 image 가 원격 registry 로 push 되지 않는다.

### 테스트 시나리오 4 - push 동작 timeout

* **사전 조건**:
    * `large_image_for_timeout` 이라는 `ImageRef` instance 를 다음과 같이 정의한다.
        * `name="verylargeimage"`
        * `project="testproject"`
        * `tag="1.0"`
        * `registry="slowregistry.example.com"`
        * `architecture="amd64"`
        * `is_local=False`
    * `large_image_for_timeout.canonical` 에 해당하는 로컬 Docker image 가 있다.
* **실행**:
    * 다음 인자로 `push_image` method 를 호출한다.
        * `image_ref`: `large_image_for_timeout`
        * `registry_conf`: `slow_registry_config`
        * `timeout`: 예상 push 완료 시간보다 짧다고 알려진 아주 작은 float 값(예: `0.01` 초)
* **기대 결과**:
    * method 가 `RuntimeError` 를 발생시킨다.
    * `large_image_for_timeout.canonical` 에서 유도한 image 가 완전히 push 되지 않거나 원격 registry 에 없다.

---

## `purge_images`

* **설명**: 지정한 container image 를 `force` 와 `noprune` option 으로 제거한다. 보통 Image GraphQL mutation 이 일으킨 `PurgeImageAction` 이 이 method 를 호출한다.
* **입력값**:
    * `request: PurgeImagesReq`
        * `image_canonicals: list[str]` - purge 할 image canonical name 목록
        * `force: bool = False` - true 이면 image 를 사용 중이어도 강제로 제거한다.
        * `noprune: bool = False` - true 이면 tag 가 없는 상위 image 의 제거하지 않는다.
* **응답값**:
    * `PurgeImagesResp`:
        * `image: str` - 처리한 image 의 canonical name
        * `error: Optional[str] = None` - 삭제에 실패하면 에러 message, 그 밖에는 None
* **부작용**:
    * `request.images` 에 지정한 image 마다
        `force` 와 `noprune` flag 를 붙여 `docker.images.delete()` 로 image 삭제를 시도한다.
    * image 삭제에 실패하면 `error` field 를 채운 `PurgeImagesResp` 를 반환한다.

### 테스트 시나리오 1 - 기존 이미지 하나 purge 성공

* **사전 조건**:
    * `"image-to-delete:v1"` 이름의 Docker image 가 로컬 Docker 저장소에 있다.
* **실행**:
    * 다음 `PurgeImagesReq` 객체로 `purge_images` method 를 호출한다.
        * `images = ["image-to-delete:v1"]`
        * `force = False`
        * `noprune = False`
* **기대 결과**:
    * method 가 `PurgeImagesResp` 객체를 반환한다. 반환한 instance 를 `overall_response` 라고 한다.
    * `overall_response.responses` 는 항목 하나를 담은 목록이다.
    * `overall_response.responses` 의 항목은 `image` field 값이 `"image-to-delete:v1"` 이고 `error` field 가 `None` 이다(또는 field 가 없어 성공을 나타낸다).
    * Docker image `"image-to-delete:v1"` 이 로컬 Docker 저장소에 더 이상 없다.

### 테스트 시나리오 2 - 기존 이미지 여러 개 purge 성공

* **사전 조건**:
    * `"image-a:latest"` 와 `"image-b:1.0"` 이름의 Docker image 가 로컬 Docker 저장소에 있다.
* **실행**:
    * 다음 `PurgeImagesReq` 객체로 `purge_images` method 를 호출한다.
        * `images = ["image-a:latest", "image-b:1.0"]`
        * `force = False`
        * `noprune = False`
* **기대 결과**:
    * method 가 `PurgeImagesResp` 객체(`overall_response`)를 반환한다.
    * `overall_response.responses` 는 항목 두 개를 담은 목록이다.
    * `overall_response.responses` 의 각 항목은 해당 image 의 성공을 나타낸다. 예를 들어 `image` field 가 입력 image 이름과 같고 `error` field 가 `None` 이다.
    * Docker image `"image-a:latest"` 와 `"image-b:1.0"` 이 로컬 Docker 저장소에 더 이상 없다.

### 테스트 시나리오 3 - 존재하지 않는 이미지 purge 시도

* **사전 조건**:
    * `"ghost-image:v0"` 이름의 Docker image 가 로컬 Docker 저장소에 없다.
* **실행**:
    * 다음 `PurgeImagesReq` 객체로 `purge_images` method 를 호출한다.
        * `images = ["ghost-image:v0"]`
        * `force = False`
        * `noprune = False`
* **기대 결과**:
    * method 가 `PurgeImagesResp` 객체(`overall_response`)를 반환한다.
    * `overall_response.responses` 는 항목 하나를 담은 목록이다.
    * `overall_response.responses` 의 항목은 `image = "ghost-image:v0"` 이고 `error` field 에 에러 message 가 있다(예: "No such image" 또는 "image not found").
    * `"ghost-image:v0"` 에 대한 로컬 Docker 저장소 상태는 그대로다(여전히 없다).

### 테스트 시나리오 4 - 사용 중인 이미지 purge 시도(force 없음)

* **사전 조건**:
    * `"busy-image:stable"` 이름의 Docker image 가 로컬 Docker 저장소에 있다.
    * `"busy-image:stable"` image 로 생성한 container 가 현재 실행 중이다.
* **실행**:
    * 다음 `PurgeImagesReq` 객체로 `purge_images` method 를 호출한다.
        * `images = ["busy-image:stable"]`
        * `force = False`
        * `noprune = False`
* **기대 결과**:
    * method 가 `PurgeImagesResp` 객체(`overall_response`)를 반환한다.
    * `overall_response.responses` 는 항목 하나를 담은 목록이다.
    * `overall_response.responses` 의 항목은 `image = "busy-image:stable"` 이고 `error` field 에 image 가 사용 중이라는 에러 message 가 있다(예: "conflict: unable to delete image...image is being used by running container...").
    * Docker image `"busy-image:stable"` 이 로컬 Docker 저장소에 여전히 있다.
    * `"busy-image:stable"` 을 사용하는 container 가 여전히 실행 중이다.

### 테스트 시나리오 5 - 사용 중인 이미지 purge 성공(force 사용)

* **사전 조건**:
    * `"busy-image:force-delete"` 이름의 Docker image 가 로컬 Docker 저장소에 있다.
    * `"busy-image:force-delete"` image 로 생성한 container 가 현재 실행 중이다.
* **실행**:
    * 다음 `PurgeImagesReq` 객체로 `purge_images` method 를 호출한다.
        * `images = ["busy-image:force-delete"]`
        * `force = True`
        * `noprune = False`
* **기대 결과**:
    * method 가 `PurgeImagesResp` 객체(`overall_response`)를 반환한다.
    * `overall_response.responses` 는 항목 하나를 담은 목록이다.
    * `overall_response.responses` 의 항목은 `image = "busy-image:force-delete"` 이고 `error` field 가 `None` 이다.
    * Docker image `"busy-image:force-delete"` 가 로컬 Docker 저장소에 더 이상 없다.
    * `"busy-image:force-delete"` 를 사용하던 container 는 계속 실행된다.

### 테스트 시나리오 6 - 기존, 존재하지 않음, 사용 중 이미지를 섞어 purge(force 없음)

* **사전 조건**:
    * `"delete-me:ok"` 이름의 Docker image 가 로컬 Docker 저장소에 있다.
    * `"iamghost:hmm"` 이름의 Docker image 가 로컬 Docker 저장소에 없다.
    * `"dont-delete-me:busy"` 이름의 Docker image 가 있고 실행 중인 container 가 사용한다.
* **실행**:
    * 다음 `PurgeImagesReq` 객체로 `purge_images` method 를 호출한다.
        * `images = ["delete-me:ok", "iamghost:hmm", "dont-delete-me:busy"]`
        * `force = False`
        * `noprune = False`
* **기대 결과**:
    * method 가 `PurgeImagesResp` 객체(`overall_response`)를 반환한다.
    * `overall_response.responses` 는 항목 세 개를 담은 목록이다.
    * `"delete-me:ok"` 항목은 성공을 나타낸다(error 가 `None`).
    * `"iamghost:hmm"` 항목은 에러 message 와 함께 실패를 나타낸다.
    * `"dont-delete-me:busy"` 항목은 에러 message 와 함께 실패를 나타낸다.
    * Docker image `"delete-me:ok"` 가 로컬 Docker 저장소에 더 이상 없다.
    * Docker image `"dont-delete-me:busy"` 가 로컬 Docker 저장소에 여전히 있다.

### 테스트 시나리오 7 - 빈 이미지 목록 purge

* **사전 조건**:
* **실행**:
    * 다음 `PurgeImagesReq` 객체로 `purge_images` method 를 호출한다.
        * `images = []`
        * `force = False`
        * `noprune = False`
* **기대 결과**:
    * `PurgeImagesReq` 의 `images` field 에 빈 목록(`[]`)을 전달하면 `[None]` 같은 값이 허용되지 않으므로 Pydantic validation error 가 발생한다.

---

## `shutdown_service`

* **설명**: kernel 의 container 안에서 실행 중인 service 를 shutdown 한다.
* **입력값**:
    * `kernel_id: KernelId`: message 를 보낼 kernel 의 id
    * `service: str`: service 이름
* **응답값**:
    * `None`
* **부작용**:
    * `kernel_id` 의 kernel 에 `shutdown_service(service)` method 를 호출한다.
        * kernel 안에서 `self.runner.feed_shutdown_service(service)` 를 호출한다.

### 테스트 시나리오 1 - 실행 중인 service shutdown 성공

* **사전 조건**:
    * agent 가 실행 중이다.
    * `kernel_id_VALID` kernel 이 활성 상태이고 그 container 가 실행 중이다.
    * `kernel_id_VALID` 의 container 안에서 `"active_service_A"` 이름의 service 가 현재 실행 중이다(예: process 가 있고 특정 port 를 listen 한다).
* **실행**:
    * 다음 입력값으로 agent 의 `shutdown_service` RPC method 를 호출한다.
        * `kernel_id`: `kernel_id_VALID`
        * `service`: `"active_service_A"`
* **기대 결과**:
    * `shutdown_service` 가 아무것도 반환하지 않는다.
    * `kernel_id_VALID` 의 container 안에서 service `"active_service_A"` 가 더 이상 실행되지 않는다.

### 테스트 시나리오 2 - 실행 중인 kernel 에서 존재하지 않는 service shutdown 시도

* **사전 조건**:
    * agent 가 실행 중이다.
    * `kernel_id_VALID` kernel 이 활성 상태이고 그 container 가 실행 중이다.
    * `kernel_id_VALID` 의 container 안에서 `"ghost_service_B"` 이름의 service 는 현재 실행 중이 *아니다*.
* **실행**:
    * 다음 입력값으로 agent 의 `shutdown_service` RPC method 를 호출한다.
        * `kernel_id`: `kernel_id_VALID`
        * `service`: `"ghost_service_B"`
* **기대 결과**:
    * 아무것도 반환하지 않는다.
    * log('unhandled exception while shutting down service app') 예외가 마지막에 남고 아무 동작도 하지 않는다.

### 테스트 시나리오 3 - 존재하지 않거나 정지한 kernel 의 service shutdown 시도

* **사전 조건**:
    * agent 가 실행 중이다.
    * `kernel_id_INVALID` 가 agent 가 아는 활성 상태나 실행 중인 kernel 과 대응하지 않는다.
* **실행**:
    * 다음 입력값으로 agent 의 `shutdown_service` RPC method 를 호출한다.
        * `kernel_id`: `kernel_id_INVALID`
        * `service`: `"any_service_C"`
* **기대 결과**:
    * 아무것도 반환하지 않는다.
    * log('unhandled exception while shutting down service app') 예외가 남고 아무 동작도 하지 않는다.

### 테스트 시나리오 4 - 이미 정지한 service shutdown 시도

* **사전 조건**:
    * agent 가 실행 중이다.
    * `kernel_id_VALID` kernel 이 활성 상태이고 그 container 가 실행 중이다.
    * `kernel_id_VALID` 의 container 안에서 `"already_stopped_service_D"` 이름의 service 가 이전에 실행되었으나 이미 정지했다.
* **실행**:
    * 다음 입력값으로 agent 의 `shutdown_service` RPC method 를 호출한다.
        * `kernel_id`: `kernel_id_VALID`
        * `service`: `"already_stopped_service_D"`
* **기대 결과**:
    * `kernel_id_VALID` 의 container 안에서 service `"already_stopped_service_D"` 가 정지 상태로 남는다.
    * 예외가 발생하지 않는다.

---

## `accept_file`

* **설명**: agent host 에 파일을 upload 한다. 보통 manager 의 session api `upload_files` 가 일으킨 `UploadFilesAction` 이 이 method 를 호출한다.
* **입력값**:
    * `kernel_id: KernelId`: 파일을 upload 할 kernel 의 id
    * `filename: str`: 파일 이름
    * `filedata`: 저장할 binary data
* **응답값**:
    * `None`.
* **부작용**:
    * `kernel_id` 의 kernel 에 `accept_file(filename, filedata)` method 를 호출한다.
        * 사용자가 `/home/work` directory 밖으로 파일을 upload 하려 하면 `PermissionError` 가 발생한다.
        * 파일은 `{agent_config["container"]["scratch-root"]}/{kernel_id}/work/home/work/` 아래에 생성된다.
        * 이 대상 host path 의 상위 directory 가 없으면 생성한다.
        * host 에서 directory 생성이나 파일 작성 중 `OSError`(예: disk full, host filesystem 권한 문제)가 발생하면 `RuntimeError` 를 발생시킨다.

### 테스트 시나리오 1 - kernel work directory 최상위에 파일 upload 성공

* **사전 조건**:
    * `kernel_id_VALID` kernel 이 활성 상태이고, 그에 대응하는 scratch directory 기준 path(`{agent_config["container"]["scratch-root"]}/{kernel_id_VALID}/work/`)가 host 에 있거나 생성할 수 있다.
    * `{agent_config["container"]["scratch-root"]}/{kernel_id_VALID}/work/uploaded_file.txt` 파일이 host 에 현재 없다.
* **실행**:
    * 다음 인자로 agent 의 `accept_file` method 를 호출한다.
        * `kernel_id`: `kernel_id_VALID`
        * `filename`: `"/home/work/uploaded_file.txt"` (container 환경 안의 path)
        * `filedata`: `b"This is test data."`
* **기대 결과**:
    * `accept_file` method 가 `None` 을 반환한다.
    * host filesystem 의 `{agent_config["container"]["scratch-root"]}/{kernel_id_VALID}/work/uploaded_file.txt` path 에 파일이 있다.
    * 그 path 의 host 파일 내용이 `b"This is test data."` 다.
    * agent 의 호출에서 예외가 발생하지 않는다.

### 테스트 시나리오 2 - `/home/work` 밖으로 파일 upload 시도(예: container path 에 `../` 사용)

* **사전 조건**:
    * `kernel_id_VALID` kernel 이 활성 상태다.
* **실행**:
    * 다음 인자로 agent 의 `accept_file` method 를 호출한다.
        * `kernel_id`: `kernel_id_VALID`
        * `filename`: `"/home/work/../attempt_outside.txt"` (`/home/work` 에서 위로 이동하려는 path)
        * `filedata`: `b"Malicious data"`
* **기대 결과**:
    * `accept_file` method 가 `PermissionError` 를 발생시킨다.
    * host 의 지정된 `{agent_config["container"]["scratch-root"]}/{kernel_id_VALID}/work/` directory 밖 어디에도 `attempt_outside.txt`(또는 비슷한 이름) 파일이 생성되지 않는다.

### 테스트 시나리오 3 - `/home/work` 밖 절대 path 로 파일 upload 시도(예: `/etc/`)

* **사전 조건**:
    * `kernel_id_VALID` kernel 이 활성 상태다.
* **실행**:
    * 다음 인자로 agent 의 `accept_file` method 를 호출한다.
        * `kernel_id`: `kernel_id_VALID`
        * `filename`: `"/etc/new_file_by_agent"` (허용된 container work directory 밖의 절대 path)
        * `filedata`: `b"System data attempt"`
* **기대 결과**:
    * `accept_file` method 가 `PermissionError` 를 발생시킨다.
    * host filesystem 의 `/etc/new_file_by_agent`(또는 그에 대응하는 host path)에 파일이 생성되지 않는다.

### 테스트 시나리오 4 - 존재하지 않거나 정지한 kernel 에 upload

* **사전 조건**:
    * `kernel_id_INVALID` 가 agent 가 아는 활성 상태나 실행 중인 kernel 과 대응하지 않는다.
* **실행**:
    * 다음 인자로 agent 의 `accept_file` method 를 호출한다.
        * `kernel_id`: `kernel_id_INVALID`
        * `filename`: `"/home/work/anyfile.txt"`
        * `filedata`: `b"Orphaned data"`
* **기대 결과**:
    * `accept_file` method 가 `KeyError` 예외를 발생시킨다.

---

## `download_file`

* **설명**: agent host 에서 파일을 download 한다. 보통 manager 의 session api `download_files` 가 일으킨 `DownloadFilesAction` 이 이 method 를 호출한다.
* **입력값**:
    * `kernel_id: KernelId`: 파일을 download 할 kernel 의 id
    * `filepath: str`: `/home/work` 안에서 파일이나 directory 를 download 할 path
* **응답값**:
    * `/home/work/filepath` 의 내용을 담은 tar archive 의 raw bytes
        * `/home/work/filepath` 가 단일 파일이면 archive 에 그 파일이 담긴다.
        * directory 이면 archive 에 그 directory 와 내용이 담긴다.
* **부작용**:
    * `kernel_id` 의 kernel 에 `download_file(filepath)` method 를 호출한다.
        * 사용자가 `/home/work` 밖으로 파일을 download 하려 하면 `PermissionError` 가 발생한다.
        * 파일이 1 MiB 를 넘으면 `ValueError` 가 발생한다.
        * 알 수 없는 docker 에러가 발생하면 `RuntimeError` 를 발생시킨다.

### 테스트 시나리오 1 - 기존 파일 하나 download 성공

* **사전 조건**:
    * `kernel_id_VALID` kernel 이 활성 상태이고 그 container 가 실행 중이다.
    * host filesystem 에, kernel container 안의 `/home/work/data/sample.txt` 에 대응하는 path(host filesystem 의 `{scratch_root}/{kernel_id_VALID}/work/data/sample.txt`)에 파일이 있고 그 내용이 `b"Test content for download."` 다.
* **실행**:
    * RPC 가 호출하는 agent 의 `download_file` method 를 다음 인자로 호출한다.
        * `kernel_id`: `kernel_id_VALID`
        * `filepath`: `"/home/work/data/sample.txt"` (container 안의 path)
* **기대 결과**:
    * method 가 `bytes` 객체를 반환한다.
    * 반환한 `bytes` 객체를 tar archive 로 해석하면 내용이 `b"Test content for download."` 인 항목 하나가 있다. 항목 이름은 `sample.txt` 또는 `data/sample.txt` 로, 특정 파일 path 에 대한 `get_archive` 동작에 따른다.
    * agent 의 method 에서 예외가 발생하지 않는다.

### 테스트 시나리오 2 - 기존 directory download 성공

* **사전 조건**:
    * `kernel_id_VALID` kernel 이 활성 상태이고 그 container 가 실행 중이다.
    * host filesystem 에, kernel container 안의 `/home/work/project_files/` 에 대응하는 path(host filesystem 의 `{scratch_root}/{kernel_id_VALID}/work/project_files/`)에 directory 가 있고 그 안에 다음 파일이 있다.
        * `project_files/file1.py` (내용: `b"print('hello')"`)
        * `project_files/docs/readme.md` (내용: `b"# Project"`)
* **실행**:
    * agent 의 `download_file` method 를 다음 인자로 호출한다.
        * `kernel_id`: `kernel_id_VALID`
        * `filepath`: `"/home/work/project_files"`
* **기대 결과**:
    * method 가 `bytes` 객체를 반환한다.
    * 반환한 `bytes` 객체를 tar archive 로 해석하면 `project_files/file1.py`(내용 `b"print('hello')"`)와 `project_files/docs/readme.md`(내용 `b"# Project"`)에 대응하는 항목이 있다.
    * agent 의 method 에서 예외가 발생하지 않는다.

### 테스트 시나리오 3 - `/home/work` 밖 파일이나 directory download 시도

* **사전 조건**:
    * `kernel_id_VALID` kernel 이 활성 상태이고 그 container 가 실행 중이다.
* **실행**:
    * agent 의 `download_file` method 를 다음 인자로 호출한다.
        * `kernel_id`: `kernel_id_VALID`
        * `filepath`: `"/etc/important_config"` (허용된 `/home/work` 밖의 path)
* **기대 결과**:
    * agent 의 `download_file` method 가 `PermissionError` 를 발생시킨다.

### 테스트 시나리오 4 - 1 MiB 를 넘는 tar archive 가 되는 내용 download 시도

* **사전 조건**:
    * `kernel_id_VALID` kernel 이 활성 상태이고 그 container 가 실행 중이다.
    * kernel container 안의 `/home/work/very_large_data/`(host filesystem 의 `{scratch_root}/{kernel_id_VALID}/work/very_large_data/`)에 파일이나 directory 가 있고, Docker 의 `get_archive` 가 반환하는 tar archive 표현이 1 MiB 를 넘는다.
* **실행**:
    * agent 의 `download_file` method 를 다음 인자로 호출한다.
        * `kernel_id`: `kernel_id_VALID`
        * `filepath`: `"/home/work/very_large_data"`
* **기대 결과**:
    * agent 의 `download_file` method 가 "Too large archive file exceeding 1 MiB" message 와 함께 `ValueError` 를 발생시킨다.

### 테스트 시나리오 5 - `/home/work` 안의 존재하지 않는 path download 시도

* **사전 조건**:
    * `kernel_id_VALID` kernel 이 활성 상태이고 그 container 가 실행 중이다.
    * `/home/work/non_existent_file.txt` path 가 kernel container 환경 안의 실제 파일이나 directory 와 대응하지 않는다.
* **실행**:
    * agent 의 `download_file` method 를 다음 인자로 호출한다.
        * `kernel_id`: `kernel_id_VALID`
        * `filepath`: `"/home/work/non_existent_file.txt"`
* **기대 결과**:
    * agent 의 `download_file` method 가 `RuntimeError` 를 발생시킨다.

### 테스트 시나리오 6 - 존재하지 않거나 정지한 kernel 에서 download 시도

* **사전 조건**:
    * `kernel_id_INVALID` 가 agent 가 아는 활성 상태나 실행 중인 kernel 과 대응하지 않는다.
* **실행**:
    * agent 의 `download_file` method 를 다음 인자로 호출한다.
        * `kernel_id`: `kernel_id_INVALID`
        * `filepath`: `"/home/work/any_file.txt"`
* **기대 결과**:
    * agent 의 `download_file` method 가 `KeyError` 예외를 발생시킨다.

---

## `download_single`

* **설명**: agent host 에서 파일 하나를 download 한다. 보통 manager 의 session api `download_files` 가 일으킨 `DownloadFilesAction` 이 이 method 를 호출한다.
* **입력값**:
    * `kernel_id: KernelId`: 파일을 download 할 kernel 의 id
    * `filepath: str`: `/home/work` 안에서 파일을 download 할 path
* **응답값**:
    * `bytes`: `/home/work/filepath` 로 지정한 단일 파일의 raw content bytes
* **부작용**:
    * `kernel_id` 의 kernel 에 `download_single(filepath)` method 를 호출한다.
        * 사용자가 `/home/work` 밖으로 파일을 download 하려 하면 `PermissionError` 가 발생한다.
        * 파일이 1 MiB 를 넘으면 `ValueError` 가 발생한다.
        * tar archive 에 항목이 둘 이상이면(예상한 단일 파일 archive 가 아니면) `ValueError` 를 발생시킨다.
        * archive 에서 단일 파일을 추출하거나 읽지 못하면(예: archive 가 깨졌거나 예상한 항목이 읽을 수 있는 파일이 아니면) `ValueError` 를 발생시킨다.
        * 알 수 없는 docker 에러가 발생하면 `RuntimeError` 를 발생시킨다.

### 테스트 시나리오 1 - 기존 파일 하나 download 성공

* **사전 조건**:
    * `kernel_id_VALID` kernel 이 활성 상태이고 그 container 가 실행 중이다.
    * host filesystem 에, kernel container 안의 `/home/work/documents/report.txt` 에 대응하는 path(`{scratch_root}/{kernel_id_VALID}/work/documents/report.txt`)에 파일이 있고 그 내용이 `b"This is the final report."` 다.
* **실행**:
    * agent 의 `download_single` method 를 다음 인자로 호출한다.
        * `kernel_id`: `kernel_id_VALID`
        * `filepath`: `"/home/work/documents/report.txt"` (container 안의 path)
* **기대 결과**:
    * method 가 `bytes` 객체를 반환한다.
    * 반환한 `bytes` 객체가 `b"This is the final report."` 와 같다.
    * agent 의 method 에서 예외가 발생하지 않는다.

### 테스트 시나리오 2 - 비어 있지 않은 directory download 시도(tar 에 항목이 여러 개라 실패 예상)

* **사전 조건**:
    * `kernel_id_VALID` kernel 이 활성 상태이고 그 container 가 실행 중이다.
    * host filesystem 에, kernel container 안의 `/home/work/my_pictures/` 에 대응하는 path에 directory 가 있고 그 안에 파일이 하나 이상 있다(예: `my_pictures/photo1.jpg`, `my_pictures/photo2.png`).
* **실행**:
    * agent 의 `download_single` method 를 다음 인자로 호출한다.
        * `kernel_id`: `kernel_id_VALID`
        * `filepath`: `"/home/work/my_pictures"`
* **기대 결과**:
    * agent 의 `download_single` method 가 "Expected a single-file archive but found multiple files from /home/work/my_pictures" message 와 함께 `ValueError` 를 발생시킨다.

### 테스트 시나리오 3 - `/home/work` 밖 파일 download 시도

* **사전 조건**:
    * `kernel_id_VALID` kernel 이 활성 상태이고 그 container 가 실행 중이다.
* **실행**:
    * agent 의 `download_single` method 를 다음 인자로 호출한다.
        * `kernel_id`: `kernel_id_VALID`
        * `filepath`: `"/usr/bin/binary"` (허용된 `/home/work` 밖의 path)
* **기대 결과**:
    * agent 의 `download_single` method 가 "You cannot download files outside /home/work" 와 비슷한 message 와 함께 `PermissionError` 를 발생시킨다.

### 테스트 시나리오 4 - tar archive 가 1 MiB 를 넘는 파일 download 시도

* **사전 조건**:
    * `kernel_id_VALID` kernel 이 활성 상태다.
    * kernel container 안의 `/home/work/data_archive_source.dat` 에 파일 하나가 있다. 이 파일 자체는 1 MiB 보다 조금 작을 수 있으나 tar archive 안에서의 표현(tar header 와 metadata) 때문에 전체 tar archive 크기가 1 MiB 를 넘는다.
* **실행**:
    * agent 의 `download_single` method 를 다음 인자로 호출한다.
        * `kernel_id`: `kernel_id_VALID`
        * `filepath`: `"/home/work/data_archive_source.dat"`
* **기대 결과**:
    * agent 의 `download_single` method 가 "Too large archive file exceeding 1 MiB" 와 비슷한 message 와 함께 `ValueError` 를 발생시킨다.

### 테스트 시나리오 5 - `/home/work` 안의 존재하지 않는 파일 download 시도

* **사전 조건**:
    * `kernel_id_VALID` kernel 이 활성 상태이고 그 container 가 실행 중이다.
    * `/home/work/fantasy_novel.txt` path 가 kernel container 환경 안의 실제 파일과 대응하지 않는다.
* **실행**:
    * agent 의 `download_single` method 를 다음 인자로 호출한다.
        * `kernel_id`: `kernel_id_VALID`
        * `filepath`: `"/home/work/fantasy_novel.txt"`
* **기대 결과**:
    * agent 의 `download_single` method 가 `RuntimeError` 를 발생시킨다.

### 테스트 시나리오 6 - 존재하지 않거나 정지한 kernel 에서 download 시도

* **사전 조건**:
    * `kernel_id_GONE` 이 agent 가 아는 활성 상태나 실행 중인 kernel 과 대응하지 않는다.
* **실행**:
    * agent 의 `download_single` method 를 다음 인자로 호출한다.
        * `kernel_id`: `kernel_id_GONE`
        * `filepath`: `"/home/work/any_single_file.dat"`
* **기대 결과**:
    * agent 의 `download_single` method 가 `KeyError` 예외를 발생시킨다.

---

## `list_files`

* **설명**: agent host 에서 파일 목록을 조회한다. 보통 manager 의 session api `list_files` 가 일으킨 `ListFilesAction` 이 이 method 를 호출한다.
* **입력값**:
    * `kernel_id: KernelId`: 파일 목록을 조회할 kernel 의 id
    * `filepath: str`: `/home/work` 안에서 파일과 directory 목록을 조회할 path
* **응답값**:
    * Json data
        * `"files": str` - JSON string. parse 하면 파일이나 directory 를 나타내는 객체 목록이 되고 각 객체에 세부 정보가 있다.
        * `"errors": str` - docker exec 명령이나 container 안에서 실행한 script 의 standard error stream 에서 수집한 에러 출력. 에러가 없으면 빈 string 이다.
        * `"abspath": str` - 목록 조회를 위해 method 로 전달한 원래 `file_path` 인자
* **부작용**:
    * `kernel_id` 의 kernel 에 `list_files(path)` method 를 호출한다.
        * 사용자가 `/home/work` 밖으로 파일을 download 하려 하면 `PermissionError` 가 발생한다.
        * 파일과 directory 목록은 container 안에서 subprocess 로 script 를 실행해 가져온다.

### 테스트 시나리오 1 - 기존의 비어 있지 않은 directory 에서 파일 목록 조회 성공

* **사전 조건**:
    * `kernel_id_VALID` kernel 이 활성 상태이고 그 container 가 실행 중이다.
    * kernel container 안에 `/home/work/documents/` directory 가 있고 다음 항목이 있다.
        * `report.docx` (파일)
        * `images` (하위 directory)
    * 이 항목은 host 의 `{scratch_root}/{kernel_id_VALID}/work/documents/report.docx` 같은 path 에 실제로 있다.
* **실행**:
    * RPC 가 호출하는 agent 의 `list_files` method 를 다음 인자로 호출한다.
        * `kernel_id`: `kernel_id_VALID`
        * `path`: `"/home/work/documents"` (container 안의 path)
* **기대 결과**:
    * method 가 dictionary 를 반환한다. 반환한 dictionary 를 `response_data` 라고 한다.
    * `response_data["abspath"]` 가 `"/home/work/documents"` 와 같다.
    * `response_data["errors"]` 가 빈 string 이다.
    * `response_data["files"]` 가 비어 있지 않은 JSON string 이다.
    * `response_data["files"]` 의 JSON string 을 parse 하면 적어도 `report.docx` 와 `images` 를 나타내는 객체를 담은 목록이 되고, 각 객체에 올바른 metadata(예: filename)가 있다.

### 테스트 시나리오 2 - 기존 빈 directory 목록 조회 성공

* **사전 조건**:
    * `kernel_id_VALID` kernel 이 활성 상태이고 그 container 가 실행 중이다.
    * kernel container 안에 `/home/work/empty_dir/` directory 가 있고 비어 있다.
    * 이 directory 는 host 의 `{scratch_root}/{kernel_id_VALID}/work/empty_dir/` 에 실제로 있다.
* **실행**:
    * agent 의 `list_files` method 를 다음 인자로 호출한다.
        * `kernel_id`: `kernel_id_VALID`
        * `path`: `"/home/work/empty_dir"`
* **기대 결과**:
    * method 가 dictionary `response_data` 를 반환한다.
    * `response_data["abspath"]` 가 `"/home/work/empty_dir"` 와 같다.
    * `response_data["errors"]` 가 빈 string 이다(또는 치명적이지 않다).
    * `response_data["files"]` 는 parse 하면 빈 목록(`[]`)이 되는 JSON string 이다.

### 테스트 시나리오 3 - `/home/work` 밖 path 목록 조회 시도

* **사전 조건**:
    * `kernel_id_VALID` kernel 이 활성 상태이고 그 container 가 실행 중이다.
* **실행**:
    * agent 의 `list_files` method 를 다음 인자로 호출한다.
        * `kernel_id`: `kernel_id_VALID`
        * `path`: `"/etc"` (허용된 `/home/work` 밖의 path)
* **기대 결과**:
    * agent 의 `list_files` method 가 "You cannot list files outside /home/work" 와 비슷한 message 와 함께 `PermissionError` 를 발생시킨다.

### 테스트 시나리오 4 - `/home/work` 안의 존재하지 않는 path 목록 조회 시도

* **사전 조건**:
    * `kernel_id_VALID` kernel 이 활성 상태이고 그 container 가 실행 중이다.
    * `/home/work/this_folder_does_not_exist/` path 가 kernel container 안에 없다.
* **실행**:
    * agent 의 `list_files` method 를 다음 인자로 호출한다.
        * `kernel_id`: `kernel_id_VALID`
        * `path`: `"/home/work/this_folder_does_not_exist"`
* **기대 결과**:
    * method 가 dictionary `response_data` 를 반환한다.
    * `response_data["abspath"]` 가 `"/home/work/this_folder_does_not_exist"` 와 같다.
    * `response_data["files"]` 가 빈 string 일 가능성이 높다.
    * `response_data["errors"]` 에 비어 있지 않은 string 이 있고, 그 안에 path 를 찾지 못했다는 에러 message 가 있다.

### 테스트 시나리오 5 - 잘못되었거나 존재하지 않는 kernel ID 로 파일 목록 조회 시도

* **사전 조건**:
    * `kernel_id_INVALID` 가 agent 의 `kernel_registry` 에서 활성 상태나 실행 중인 kernel 과 대응하지 않는다.
* **실행**:
    * agent 의 `list_files` method 를 다음 인자로 호출한다.
        * `kernel_id`: `kernel_id_INVALID`
        * `path`: `"/home/work/any_target_path"`
* **기대 결과**:
    * agent 의 `list_files` method 가 `KeyError` 를 발생시킨다.

---

## `shutdown`

* **설명**: agent 의 shutdown 절차를 시작한다.
* **입력값**:
    * `stop_signal: signal.Signals`: agent shutdown 에 사용할 신호를 지정한다(현재는 `signal.SIGTERM` 만 의미가 있다. 보통 stop_signal 값은 signal.SIGTERM 이다).
* **응답값**:
    * `None`
* **부작용**:
    * Task 취소:
        * agent 의 main socket 통신 task 를 취소한다.
        * 구현별 주기 task group(예: Docker 관련 ptask group)을 shutdown 한다.
        * 진행 중인 모든 비동기 batch 실행 task 를 취소한다.
        * 예약된 모든 timer task 를 취소한다.
        * Docker event 감시 task 를 정지하고 취소한다(해당하는 경우).
    * Kernel 과 container 수명 관리:
        * 등록된 kernel 마다
            * kernel 의 runner 를 close 한다.
            * kernel 객체 자체의 `close()` method 를 호출해 개별 정리를 한다.
        * Kernel Registry 유지: `self.kernel_registry` 의 현재 상태를 직렬화해 `{agent_config['container']['var-base-path']}/last_registry.{self.local_instance_id}.dat` 이름의 파일에 작성한다.
        * 조건부 전체 kernel 종료(stop_signal 이 SIGTERM 이면):
            * 등록된 모든 kernel 에 종료 신호를 명시적으로 보낸다(`LifecycleEvent.DESTROY` 를 reason `AGENT_TERMINATION` 으로 주입한다).
        * shutdown 절차는 이 종료 동작이 끝날 때까지 기다린 뒤 진행한다. 그래야 container 가 제거된다.
    * Event system 과 handler shutdown:
        * container lifecycle event handler task 를 정상적으로 정지한다.
        * reason="shutdown" 인 `AgentTerminatedEvent` 를 발생시킨다.
        * event producer 와 event dispatcher 구성 요소를 close 한다.
    * 외부 service 와 자원 정리:
        * 외부 service(예: Valkey streams, Valkey stats)로 가는 connection pool 을 close 한다.
        * 구현별 metadata server 자원을 정리한다.
        * container engine(예: Docker client)과의 연결을 close 한다.
---

## `create_local_network`

* **설명**: container bridge network 를 생성한다. 보통 새 session 을 시작할 때 사용한다.
* **입력값**:
    * `network_name: str`: 생성할 network 이름(보통 `bai-singlenode-{scheduled_session.id}` 로 구성한다)
* **응답값**:
    * `None`.
* **부작용**:
    * 주어진 network_name 과 label `"ai.backend.cluster-network": "1"` 로 bridge network 를 생성한다.

### 테스트 시나리오 1: 새 network 생성 성공

* **사전 조건**:
    * agent 가 실행 중이고 Docker engine 에 접근할 수 있다.
    * `"test-new-network-01"` 이름의 Docker network 가 Docker 환경에 현재 없다.
* **실행**:
    * agent 의 `create_local_network` method 를 다음 인자로 호출한다.
        * `network_name`: `"test-new-network-01"`
* **기대 결과**:
    * `create_local_network` method 가 `None` 을 반환한다.
    * `"test-new-network-01"` 이름의 Docker network 가 Docker 환경에 생긴다.
    * 생성한 network `"test-new-network-01"` 의 driver type 이 `"bridge"` 다.
    * 생성한 network `"test-new-network-01"` 에 label `"ai.backend.cluster-network": "1"` 이 있다.

### 테스트 시나리오 2: 이미 있는 network 생성 시도

* **사전 조건**:
    * agent 가 실행 중이고 Docker engine 에 접근할 수 있다.
    * `"existing-network-02"` 이름의 Docker network 가 Docker 환경에 이미 있다.
* **실행**:
    * agent 의 `create_local_network` method 를 다음 인자로 호출한다.
        * `network_name`: `"existing-network-02"`
* **기대 결과**:
    * `create_local_network` method 가 예외를 발생시킨다.
    * 기존 Docker network `"existing-network-02"` 의 상태가 그대로다.

### 테스트 시나리오 3: 잘못된 이름 형식으로 network 생성 시도(Docker/aiodocker 검증에 따라 선택)

* **사전 조건**:
    * agent 가 실행 중이고 Docker engine 에 접근할 수 있다.
    * `"invalid@name#for_net"` string 은 Docker network 이름으로 잘못된 형식이다.
* **실행**:
    * agent 의 `create_local_network` method 를 다음 인자로 호출한다.
        * `network_name`: `"invalid@name#for_net"`
* **기대 결과**:
    * `create_local_network` method 가 예외를 발생시킨다.
    * `"invalid@name#for_net"` 이름의 새 network 가 Docker 환경에 생성되지 않는다.

---

## `destroy_local_network`

* **설명**: container network 를 제거한다. 보통 session 을 정리할 때 사용한다.
* **입력값**:
    * `network_name: str`: 제거할 network 이름
* **응답값**:
    * `None`.
* **부작용**:
    * 전달받은 인자로 container network 이름을 제거한다.

### 테스트 시나리오 1: 기존의 사용하지 않는 network 제거 성공

* **사전 조건**:
    * agent 가 실행 중이고 Docker engine 에 접근할 수 있다.
    * `"delete-me-network-A"` 이름의 Docker network 가 Docker 환경에 있다.
    * `"delete-me-network-A"` network 에 연결된 실행 중인 container 가 없다.
* **실행**:
    * agent 의 `destroy_local_network` method 를 다음 인자로 호출한다.
        * `network_name`: `"delete-me-network-A"`
* **기대 결과**:
    * `destroy_local_network` method 가 `None` 을 반환한다.
    * Docker network `"delete-me-network-A"` 가 Docker 환경에 더 이상 없다.

### 테스트 시나리오 2: 존재하지 않는 network 제거 시도

* **사전 조건**:
    * agent 가 실행 중이고 Docker engine 에 접근할 수 있다.
    * `"non-existent-network-B"` 이름의 Docker network 가 Docker 환경에 없다.
* **실행**:
    * agent 의 `destroy_local_network` method 를 다음 인자로 호출한다.
        * `network_name`: `"non-existent-network-B"`
* **기대 결과**:
    * `destroy_local_network` method 가 예외를 발생시킨다.

### 테스트 시나리오 3: container 가 사용 중인 network 제거 시도

* **사전 조건**:
    * agent 가 실행 중이고 Docker engine 에 접근할 수 있다.
    * `"busy-network-C"` 이름의 Docker network 가 Docker 환경에 있다.
    * 활성 container 가 하나 이상 `"busy-network-C"` network 에 연결된 상태다.
* **실행**:
    * agent 의 `destroy_local_network` method 를 다음 인자로 호출한다.
        * `network_name`: `"busy-network-C"`
* **기대 결과**:
    * `destroy_local_network` method 가 예외를 발생시킨다.
    * Docker network `"busy-network-C"` 가 Docker 환경에 여전히 있다.
    * `"busy-network-C"` 에 연결된 container 가 계속 실행되고 연결된 상태로 남는다.
