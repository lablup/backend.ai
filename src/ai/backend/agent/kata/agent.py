"""
KataAgent — a (hacky MVP) Backend.AI agent backend that runs each compute
session's kernel inside a Kata Containers lightweight VM.

Design (see ``mvp-findings-kataagent.md`` and report §6b):

* ``KataAgent`` subclasses :class:`DockerAgent`. The entire ``create_kernel``
  orchestration, scratch/config generation, krunner mounting, vfolder mounting,
  resource spec handling and image pull/scan are reused **verbatim** from the
  Docker path. The functional delta is only "how the assembled container_config
  becomes a running container".
* ``KataKernelCreationContext`` subclasses :class:`DockerKernelCreationContext`
  and overrides exactly two methods:
    - ``prepare_container`` — reuses the Docker file-staging body and only
      re-classes the resulting kernel as :class:`KataKernel`;
    - ``start_container`` — instead of two ``aiodocker`` calls
      (``containers.create`` + ``container.start``), it translates the same
      ``container_config`` dict into a ``nerdctl run --runtime
      io.containerd.kata.v2`` invocation.
* Per-container lifecycle ops that address the container by ID
  (``destroy_kernel`` / ``clean_kernel``) are overridden to use ``nerdctl``.

Known MVP degradations (intentional): container-event monitoring for
self-termination is best-effort via a poller (Docker's event stream watches the
``moby`` namespace, not containerd's ``default``); stats, log-streaming and
commit are stubbed. These do not block the "session runs in a Kata VM" demo.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from collections.abc import AsyncGenerator, Mapping, MutableMapping, Sequence
from pathlib import Path
from typing import Any, cast, override

from ai.backend.agent.agent import ACTIVE_STATUS_SET
from ai.backend.agent.config.unified import ContainerSandboxType
from ai.backend.agent.docker.agent import (
    DockerAgent,
    DockerKernelCreationContext,
    _clean_scratch,
)
from ai.backend.agent.errors.agent import (
    ContainerCreationError,
    InvalidArgumentError,
)
from ai.backend.agent.errors.resources import PortPoolExhaustedError
from ai.backend.agent.kata import nerdctl
from ai.backend.agent.kata.kernel import KataKernel
from ai.backend.agent.kernel import AbstractKernel
from ai.backend.agent.resources import KernelResourceSpec
from ai.backend.agent.types import (
    Container,
    KernelOwnershipData,
    LifecycleEvent,
)
from ai.backend.agent.utils import get_safe_ulimit, update_nested_dict
from ai.backend.common.asyncio import current_loop
from ai.backend.common.docker import ImageRef, LabelName
from ai.backend.common.events.kernel import KernelLifecycleEventReason
from ai.backend.common.json import load_json
from ai.backend.common.types import (
    BinarySize,
    ClusterInfo,
    ClusterSSHPortMapping,
    ContainerId,
    ContainerStatus,
    KernelCreationConfig,
    KernelId,
    ServicePort,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.logging.formatter import pretty

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class KataKernelCreationContext(DockerKernelCreationContext):
    """A DockerKernelCreationContext that starts the container in a Kata microVM."""

    @property
    def kata_runtime(self) -> str:
        return nerdctl.DEFAULT_KATA_RUNTIME

    @override
    async def prepare_container(
        self,
        resource_spec: KernelResourceSpec,
        environ: Mapping[str, str],
        service_ports: list[ServicePort],
        cluster_info: ClusterInfo,
    ) -> KataKernel:
        # Reuse the entire Docker file-staging body (bootstrap.sh, environ.txt,
        # resource.txt, ssh keypair, dotfiles, ...) and only swap the concrete
        # kernel class. DockerKernel and KataKernel share an identical
        # constructor and instance layout (UserDict-based, no __slots__); only
        # the container-addressing methods differ. Re-classing avoids
        # duplicating ~150 lines of staging logic.
        kernel = await super().prepare_container(
            resource_spec, environ, service_ports, cluster_info
        )
        kernel.__class__ = KataKernel
        return cast(KataKernel, kernel)

    async def _externalize_inline_seccomp(self, container_config: MutableMapping[str, Any]) -> None:
        """Docker's API (and ``_apply_seccomp_profile``) injects the seccomp
        profile as *inline JSON* in ``HostConfig.SecurityOpt`` (``seccomp=<json>``).
        nerdctl's ``--security-opt seccomp=`` instead expects a *file path*, so it
        tries to ``open()`` the JSON blob and fails with "file name too long".
        Write any inline profile to the kernel's config dir and rewrite the opt to
        point at that file (cleaned up with the scratch)."""
        host_config = container_config.get("HostConfig", {}) or {}
        sec_opts = host_config.get("SecurityOpt")
        if not sec_opts:
            return
        loop = current_loop()
        new_opts: list[str] = []
        for opt in sec_opts:
            prefix = "seccomp="
            if isinstance(opt, str) and opt.startswith(prefix):
                value = opt[len(prefix) :]
                if value.lstrip().startswith("{"):
                    profile_path = self.config_dir / "seccomp.json"
                    await loop.run_in_executor(None, profile_path.write_text, value)
                    new_opts.append(f"{prefix}{profile_path}")
                    continue
            new_opts.append(opt)
        host_config["SecurityOpt"] = new_opts

    async def _resolve_named_volumes(self, container_config: Mapping[str, Any]) -> dict[str, str]:
        """Pre-resolve every Docker named volume referenced by the mounts to its
        host path (async), so the pure translation function can look them up
        synchronously. Kata cannot share a Docker named volume into the guest, so
        these are bind-mounted by host path instead (the krunner /opt/backend.ai
        volume is the main case)."""
        host_config = container_config.get("HostConfig", {}) or {}
        volume_names = {
            mount["Source"]
            for mount in (host_config.get("Mounts", []) or [])
            if mount.get("Type") == "volume"
        }
        resolved: dict[str, str] = {}
        for name in volume_names:
            resolved[name] = await nerdctl.resolve_docker_volume_path(name)
            log.debug("kata: resolved named volume {} -> {}", name, resolved[name])
        return resolved

    @override
    async def start_container(
        self,
        kernel_obj: AbstractKernel,
        cmdargs: list[str],
        resource_opts: Mapping[str, Any] | None,
        preopen_ports: list[int],
        cluster_info: ClusterInfo,
    ) -> Mapping[str, Any]:
        loop = current_loop()
        resource_spec = kernel_obj.resource_spec
        service_ports = kernel_obj.service_ports
        environ = kernel_obj.environ
        image_labels = self.kernel_config["image"]["labels"]

        # --- Port computation (reused verbatim from DockerKernelCreationContext) ---
        container_bind_host = self.local_config.container.bind_host
        advertised_kernel_host = self.local_config.container.advertised_host
        if len(service_ports) + len(self.repl_ports) > len(self.port_pool):
            raise PortPoolExhaustedError(
                f"Container ports are not sufficiently available. "
                f"(remaining ports: {self.port_pool.remaining()})"
            )
        exposed_ports = [*self.repl_ports]
        host_ports = [self.port_pool.acquire() for _ in self.repl_ports]
        host_ips = []
        for sport in service_ports:
            exposed_ports.extend(sport["container_ports"])
            if (
                sport["name"] == "sshd"
                and self.cluster_ssh_port_mapping
                and (
                    ssh_host_port := self.cluster_ssh_port_mapping.get(
                        self.kernel_config["cluster_hostname"]
                    )
                )
            ):
                host_ports.append(ssh_host_port[1])
            else:
                hport = self.port_pool.acquire()
                host_ports.append(hport)
        protected_service_ports: set[int] = set()
        for sport in service_ports:
            if sport["name"] in self.protected_services:
                protected_service_ports.update(sport["container_ports"])
        for eport in exposed_ports:
            # repl + protected ports MUST stay on 127.0.0.1 — this is the
            # load-bearing assumption (docker/kernel.py:98). nerdctl's portmap
            # CNI installs the host(127.0.0.1)->guest DNAT, so it holds across
            # the Kata VM boundary.
            if eport in self.repl_ports or eport in protected_service_ports:
                host_ips.append("127.0.0.1")
            else:
                host_ips.append(str(container_bind_host))
        if len(host_ips) != len(host_ports) or len(host_ports) != len(exposed_ports):
            raise InvalidArgumentError(
                f"Port list length mismatch: host_ips={len(host_ips)}, "
                f"host_ports={len(host_ports)}, exposed_ports={len(exposed_ports)}"
            )

        container_log_size = self.local_config.container_logs.max_length
        container_log_file_count = 5
        container_log_file_size = BinarySize(container_log_size // container_log_file_count)

        if self.image_ref.is_local:
            image = self.image_ref.short
        else:
            image = self.image_ref.canonical

        # --- container_config assembly (reused verbatim; consumed by nerdctl) ---
        container_config: MutableMapping[str, Any] = {
            "Image": image,
            "Tty": True,
            "OpenStdin": True,
            "Privileged": False,
            "StopSignal": "SIGINT",
            "ExposedPorts": {f"{port}/tcp": {} for port in exposed_ports},
            "EntryPoint": ["/opt/kernel/entrypoint.sh"],
            "Cmd": cmdargs,
            "Env": [f"{k}={v}" for k, v in environ.items()],
            "WorkingDir": "/home/work",
            "Hostname": self.kernel_config["cluster_hostname"],
            "Labels": {
                LabelName.AGENT_ID: str(self.agent_id),
                LabelName.KERNEL_ID: str(self.kernel_id),
                LabelName.SESSION_ID: str(self.session_id),
                LabelName.OWNER_USER: self.ownership_data.owner_user_id_to_str,
                LabelName.OWNER_PROJECT: self.ownership_data.owner_project_id_to_str,
                LabelName.OWNER_AGENT: str(self.agent_id),
                LabelName.BLOCK_SERVICE_PORTS: (
                    "1" if self.internal_data.get("block_service_ports", False) else "0"
                ),
            },
            "HostConfig": {
                "Init": True,
                "PortBindings": {
                    f"{eport}/tcp": [{"HostPort": str(hport), "HostIp": hip}]
                    for eport, hport, hip in zip(exposed_ports, host_ports, host_ips, strict=True)
                },
                "PublishAllPorts": False,  # we manage port mapping manually!
                "CapAdd": [
                    "IPC_LOCK",  # for hugepages and RDMA
                    "SYS_NICE",  # for NFS based GPUDirect Storage
                ],
                "Ulimits": [
                    get_safe_ulimit("nofile", 1048576, 1048576),
                    get_safe_ulimit("memlock", -1, -1),
                ],
                "LogConfig": {
                    "Type": "local",
                    "Config": {
                        "max-size": f"{container_log_file_size:s}",
                        "max-file": str(container_log_file_count),
                        "compress": "false",
                    },
                },
            },
        }

        await self._apply_seccomp_profile(container_config)

        # merge all container configs generated during prior preparation steps
        # (mounts from process_mounts, accelerator args from computer_docker_args)
        for c in self.container_configs:
            update_nested_dict(container_config, c)
        if self.local_config.container.sandbox_type == ContainerSandboxType.JAIL:
            update_nested_dict(
                container_config,
                {
                    "HostConfig": {
                        "SecurityOpt": ["seccomp=unconfined", "apparmor=unconfined"],
                        "CapAdd": ["SYS_PTRACE"],
                    },
                },
            )

        if resource_opts and resource_opts.get("shmem"):
            shmem = int(resource_opts.get("shmem", "0"))
            self.computer_docker_args["HostConfig"]["ShmSize"] = shmem

        service_ports_label: list[str] = []
        service_ports_label += image_labels.get(LabelName.SERVICE_PORTS, "").split(",")
        service_ports_label += [f"{port_no}:preopen:{port_no}" for port_no in preopen_ports]
        container_config["Labels"][LabelName.SERVICE_PORTS] = ",".join([
            label for label in service_ports_label if label
        ])
        update_nested_dict(container_config, self.computer_docker_args)
        kernel_name = f"kernel.{self.image_ref.name.split('/')[-1]}.{self.kernel_id}"

        # optional local override of docker config (reused; same JSON files)
        extra_container_opts_name = "agent-docker-container-opts.json"
        for extra_container_opts_file in [
            Path("/etc/backend.ai") / extra_container_opts_name,
            Path.home() / ".config" / "backend.ai" / extra_container_opts_name,
            Path.cwd() / extra_container_opts_name,
        ]:
            if extra_container_opts_file.is_file():
                try:
                    extra_container_opts = load_json(extra_container_opts_file.read_bytes())
                    update_nested_dict(container_config, extra_container_opts)
                except OSError:
                    pass

        if self.local_config.debug.log_kernel_config:
            log.debug("full container config: {!r}", pretty(container_config))

        async def _rollback_container_creation() -> None:
            await _clean_scratch(
                loop,
                self.local_config.container.scratch_type,
                self.local_config.container.scratch_root,
                self.kernel_id,
            )
            self.port_pool.release_many(host_ports)
            async with self.resource_lock:
                for dev_name, device_alloc in resource_spec.allocations.items():
                    self.computers[dev_name].alloc_map.free(device_alloc)

        # --- THE delta: translate config -> nerdctl run (Kata runtime) ---
        # nerdctl needs the seccomp profile as a file path, not Docker's inline JSON.
        await self._externalize_inline_seccomp(container_config)
        volume_map = await self._resolve_named_volumes(container_config)
        nerdctl_args = nerdctl.translate_container_config_to_nerdctl_args(
            container_config,
            name=kernel_name,
            runtime=self.kata_runtime,
            resolve_volume=volume_map.__getitem__,
        )
        try:
            cid = await nerdctl.nerdctl_run(nerdctl_args)
        except asyncio.CancelledError as e:
            await _rollback_container_creation()
            raise ContainerCreationError(
                container_id="", message="Kata container creation was cancelled"
            ) from e
        except Exception as e:
            await _rollback_container_creation()
            raise ContainerCreationError(
                container_id="", message=f"nerdctl run failed: {e!r}"
            ) from e

        def _append_cid() -> None:
            with (self.config_dir / "resource.txt").open("a") as f:
                f.write(f"CID={cid}\n")

        await loop.run_in_executor(None, _append_cid)
        kernel_obj.set_container_id(ContainerId(cid))

        # --- Build the port map directly. Unlike Docker we don't need a port
        # read-back: nerdctl honors our explicit `-p 127.0.0.1:HPORT:CPORT`, so
        # the host ports we assigned ARE the published ports. ---
        repl_in_port = 0
        repl_out_port = 0
        stdin_port = 0
        stdout_port = 0
        ctnr_host_port_map: dict[int, int] = {}
        for idx, port in enumerate(exposed_ports):
            host_port = host_ports[idx]
            if port == 2000:  # intrinsic repl-in
                repl_in_port = host_port
            elif port == 2001:  # intrinsic repl-out
                repl_out_port = host_port
            elif port == 2002:  # legacy
                stdin_port = host_port
            elif port == 2003:  # legacy
                stdout_port = host_port
            else:
                ctnr_host_port_map[port] = host_port
        for sport in service_ports:
            sport["host_ports"] = tuple(
                ctnr_host_port_map[cport] for cport in sport["container_ports"]
            )

        if repl_in_port == 0:
            raise InvalidArgumentError("repl_in_port should have been assigned")
        if repl_out_port == 0:
            raise InvalidArgumentError("repl_out_port should have been assigned")

        kernel_host = advertised_kernel_host or container_bind_host
        return {
            "container_id": cid,
            "kernel_host": kernel_host,
            "repl_in_port": repl_in_port,
            "repl_out_port": repl_out_port,
            "stdin_port": stdin_port,  # legacy
            "stdout_port": stdout_port,  # legacy
            "host_ports": host_ports,
            "domain_socket_proxies": self.domain_socket_proxies,
            "block_service_ports": self.internal_data.get("block_service_ports", False),
        }


class KataAgent(DockerAgent):
    """A DockerAgent whose kernels run inside Kata Containers microVMs.

    Everything except per-container create/start and lifecycle ops is inherited
    from DockerAgent (image scan/pull, krunner volume prep, scratch handling,
    resource accounting, RPC server, health, the agent socket relay).
    """

    _kata_liveness_task: asyncio.Task[Any] | None

    @override
    async def __ainit__(self) -> None:
        await super().__ainit__()
        # Docker's event monitor (started by super) watches the "moby" namespace
        # and will never see Kata kernels (they live in containerd's "default"
        # namespace). Run a lightweight poller to catch self-termination.
        self._kata_liveness_task = asyncio.create_task(self._poll_kata_liveness())

    @override
    async def shutdown(self, stop_signal: Any) -> None:
        task = getattr(self, "_kata_liveness_task", None)
        if task is not None:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        await super().shutdown(stop_signal)

    @override
    async def init_kernel_context(
        self,
        ownership_data: KernelOwnershipData,
        kernel_image: ImageRef,
        kernel_config: KernelCreationConfig,
        *,
        restarting: bool = False,
        cluster_ssh_port_mapping: ClusterSSHPortMapping | None = None,
    ) -> KataKernelCreationContext:
        distro = await self.resolve_image_distro(kernel_config["image"])
        return KataKernelCreationContext(
            ownership_data,
            self.event_producer,
            kernel_image,
            kernel_config,
            distro,
            self.local_config,
            self.computers,
            self.port_pool,
            self.agent_sockpath,
            self.resource_lock,
            self.network_plugin_ctx,
            restarting=restarting,
            cluster_ssh_port_mapping=cluster_ssh_port_mapping,
            gwbridge_subnet=self.gwbridge_subnet,
        )

    @override
    async def enumerate_containers(
        self,
        status_filter: frozenset[ContainerStatus] = ACTIVE_STATUS_SET,
    ) -> Sequence[tuple[KernelId, Container]]:
        # CRITICAL: DockerAgent.enumerate_containers lists containers from the
        # Docker ("moby") namespace, which NEVER contains Kata kernels (they live
        # in containerd's `default` namespace). The registry-reconciliation loop
        # (`_clean_kernel_registry_loop`) uses this to find "dangling" kernels; if
        # it sees zero alive Kata containers it evicts every live kernel from the
        # registry, after which destroy can't find the container_id and the VM
        # leaks. So we enumerate via nerdctl/containerd instead.
        infos = await nerdctl.nerdctl_inspect_kernel_containers(LabelName.KERNEL_ID)
        result: list[tuple[KernelId, Container]] = []
        for info in infos:
            labels = (info.get("Config") or {}).get("Labels") or {}
            if labels.get(LabelName.OWNER_AGENT) != str(self.id):
                continue
            raw_status = ((info.get("State") or {}).get("Status") or "").lower()
            try:
                status = ContainerStatus(raw_status)
            except ValueError:
                continue
            if status not in status_filter:
                continue
            raw_kernel_id = labels.get(LabelName.KERNEL_ID)
            if not raw_kernel_id:
                continue
            container = Container(
                id=ContainerId(info.get("Id") or ""),
                status=status,
                image=(info.get("Config") or {}).get("Image") or info.get("Image") or "",
                labels=labels,
                ports=[],  # MVP: restart-recovery of ports is not reconstructed
                backend_obj=info,
            )
            result.append((KernelId(uuid.UUID(raw_kernel_id)), container))
        return result

    @override
    async def destroy_kernel(
        self,
        kernel_id: KernelId,
        container_id: ContainerId | None,
    ) -> None:
        # Guard falsy ids too: a create that fails before `nerdctl run` returns a
        # cid leaves container_id="" — calling nerdctl stop/logs with it triggers
        # a filter parse error.
        if not container_id:
            return
        try:
            await nerdctl.nerdctl_stop(str(container_id))
        except Exception:
            log.exception("destroy_kernel(k:{}) nerdctl stop error", kernel_id)
            await self.reconstruct_resource_usage()

    @override
    async def clean_kernel(
        self,
        kernel_id: KernelId,
        container_id: ContainerId | None,
        restarting: bool,
    ) -> None:
        loop = current_loop()
        if container_id:  # falsy when a create failed before producing a cid
            try:
                logs = await nerdctl.nerdctl_logs(str(container_id))
                await self.collect_logs(
                    kernel_id, str(container_id), _bytes_aiter(logs.encode("utf-8"))
                )
            except Exception as e:
                log.warning(
                    "error while collecting kata container logs (k:{}, cid:{}): {}",
                    kernel_id,
                    container_id,
                    e,
                )

        kernel_obj = self.kernel_registry.get(kernel_id)
        if kernel_obj is not None:
            for domain_socket_proxy in kernel_obj.get("domain_socket_proxies", []):
                if domain_socket_proxy.proxy_server.is_serving():
                    domain_socket_proxy.proxy_server.close()
                    await domain_socket_proxy.proxy_server.wait_closed()
                    try:
                        domain_socket_proxy.host_proxy_path.unlink()
                    except OSError:
                        pass

        if not self.local_config.debug.skip_container_deletion and container_id:
            try:
                await nerdctl.nerdctl_rm(str(container_id))
            except Exception:
                log.exception(
                    "unexpected error while removing kata container (k:{}, c:{})",
                    kernel_id,
                    container_id,
                )

        if not restarting:
            await _clean_scratch(
                loop,
                self.local_config.container.scratch_type,
                self.local_config.container.scratch_root,
                kernel_id,
            )

    async def _poll_kata_liveness(self) -> None:
        """Best-effort death detection: when a tracked kernel's container is no
        longer in `nerdctl ps`, inject a CLEAN lifecycle event. This stands in
        for Docker's event stream, which does not observe containerd's namespace.
        """
        poll_interval = 5.0
        while True:
            try:
                await asyncio.sleep(poll_interval)
                running = await nerdctl.nerdctl_list_running_kernel_ids(LabelName.KERNEL_ID)
                running_short = {cid[:12] for cid in running}
                for kernel_id, kernel_obj in list(self.kernel_registry.items()):
                    cid = kernel_obj.container_id
                    if cid is None:
                        continue
                    if str(cid)[:12] in running_short or str(cid) in running:
                        continue
                    log.warning(
                        "kata: kernel {} container {} disappeared; injecting CLEAN",
                        kernel_id,
                        cid,
                    )
                    await self.inject_container_lifecycle_event(
                        kernel_id,
                        kernel_obj.session_id,
                        LifecycleEvent.CLEAN,
                        kernel_obj.termination_reason or KernelLifecycleEventReason.SELF_TERMINATED,
                        container_id=cid,
                    )
            except asyncio.CancelledError:
                raise
            except Exception as e:
                log.warning("kata: liveness poller error: {}", e)


async def _bytes_aiter(data: bytes) -> AsyncGenerator[bytes, None]:
    yield data
