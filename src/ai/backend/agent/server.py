from __future__ import annotations

import asyncio
import functools
import importlib
import json
import logging
import logging.config
import os
import os.path
import shutil
import signal
import sys
from collections import OrderedDict, defaultdict
from ipaddress import _BaseAddress as BaseIPAddress
from ipaddress import ip_network
from pathlib import Path
from pprint import pformat, pprint
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncGenerator,
    Callable,
    ClassVar,
    Coroutine,
    Iterable,
    Literal,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
    cast,
)
from uuid import UUID

import aiomonitor
import aiotools
import click
import tomlkit
from aiotools import aclosing
from callosum.lower.zeromq import ZeroMQAddress, ZeroMQRPCTransport
from callosum.ordering import ExitOrderedAsyncScheduler
from callosum.rpc import Peer, RPCMessage
from etcd_client import WatchEventType
from setproctitle import setproctitle
from trafaret.dataerror import DataError as TrafaretDataError
from zmq.auth.certs import load_certificate

from ai.backend.common import config, identity, msgpack, utils
from ai.backend.common.auth import AgentAuthHandler, PublicKey, SecretKey
from ai.backend.common.bgtask import ProgressReporter
from ai.backend.common.docker import ImageRef
from ai.backend.common.etcd import AsyncEtcd, ConfigScopes
from ai.backend.common.events import (
    KernelLifecycleEventReason,
    KernelTerminatedEvent,
)
from ai.backend.common.logging import BraceStyleAdapter, Logger
from ai.backend.common.types import (
    ClusterInfo,
    CommitStatus,
    HardwareMetadata,
    HostPortPair,
    ImageRegistry,
    KernelCreationConfig,
    KernelId,
    LogSeverity,
    QueueSentinel,
    SessionId,
    aobject,
)
from ai.backend.common.utils import current_loop

from . import __version__ as VERSION
from .config import (
    agent_etcd_config_iv,
    agent_local_config_iv,
    container_etcd_config_iv,
    docker_extra_config_iv,
)
from .exception import ResourceError
from .monitor import AgentErrorPluginContext, AgentStatsPluginContext
from .types import AgentBackend, LifecycleEvent, VolumeInfo
from .utils import get_arch_name, get_subnet_ip

if TYPE_CHECKING:
    from .agent import AbstractAgent

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]

deeplearning_image_keys = {
    "tensorflow",
    "caffe",
    "keras",
    "torch",
    "mxnet",
    "theano",
}

deeplearning_sample_volume = VolumeInfo(
    "deeplearning-samples",
    "/home/work/samples",
    "ro",
)

agent_instance: AgentRPCServer


async def get_extra_volumes(docker, lang):
    avail_volumes = (await docker.volumes.list())["Volumes"]
    if not avail_volumes:
        return []
    avail_volume_names = set(v["Name"] for v in avail_volumes)

    # deeplearning specialization
    # TODO: extract as config
    volume_list = []
    for k in deeplearning_image_keys:
        if k in lang:
            volume_list.append(deeplearning_sample_volume)
            break

    # Mount only actually existing volumes
    mount_list = []
    for vol in volume_list:
        if vol.name in avail_volume_names:
            mount_list.append(vol)
        else:
            log.info(
                "skipped attaching extra volume {0} to a kernel based on image {1}",
                vol.name,
                lang,
            )
    return mount_list


def collect_error(meth: Callable) -> Callable:
    @functools.wraps(meth)
    async def _inner(self: AgentRPCServer, *args, **kwargs):
        try:
            return await meth(self, *args, **kwargs)
        except Exception:
            await self.agent.produce_error_event()
            raise

    return _inner


class RPCFunctionRegistry:
    functions: Set[str]

    def __init__(self) -> None:
        self.functions = set()

    def __call__(
        self,
        meth: Callable[..., Coroutine[None, None, Any]],
    ) -> Callable[[AgentRPCServer, RPCMessage], Coroutine[None, None, Any]]:
        @functools.wraps(meth)
        async def _inner(self_: AgentRPCServer, request: RPCMessage) -> Any:
            try:
                if request.body is None:
                    return await meth(self_)
                else:
                    return await meth(
                        self_,
                        *request.body["args"],
                        **request.body["kwargs"],
                    )
            except (asyncio.CancelledError, asyncio.TimeoutError):
                raise
            except ResourceError:
                # This is an expected scenario.
                raise
            except Exception:
                log.exception("unexpected error")
                await self_.error_monitor.capture_exception()
                raise

        self.functions.add(meth.__name__)
        return _inner


class AgentRPCServer(aobject):
    rpc_function: ClassVar[RPCFunctionRegistry] = RPCFunctionRegistry()
    rpc_auth_manager_public_key: Optional[PublicKey]
    rpc_auth_agent_public_key: Optional[PublicKey]
    rpc_auth_agent_secret_key: Optional[SecretKey]

    loop: asyncio.AbstractEventLoop
    agent: AbstractAgent
    rpc_server: Peer
    rpc_addr: str
    agent_addr: str

    _stop_signal: signal.Signals
    debug_server_task: asyncio.Task

    def __init__(
        self,
        etcd: AsyncEtcd,
        local_config: Mapping[str, Any],
        *,
        skip_detect_manager: bool = False,
    ) -> None:
        self.loop = current_loop()
        self.etcd = etcd
        self.local_config = local_config
        self.skip_detect_manager = skip_detect_manager
        self._stop_signal = signal.SIGTERM

    async def __ainit__(self) -> None:
        # Start serving requests.
        await self.update_status("starting")

        if not self.skip_detect_manager:
            await self.detect_manager()

        await self.read_agent_config()
        await self.read_agent_config_container()

        self.stats_monitor = AgentStatsPluginContext(self.etcd, self.local_config)
        self.error_monitor = AgentErrorPluginContext(self.etcd, self.local_config)
        await self.stats_monitor.init()
        await self.error_monitor.init()

        if self.local_config["agent"]["rpc-auth-agent-keypair"] is not None:
            manager_pkey, _ = load_certificate(
                self.local_config["agent"]["rpc-auth-manager-public-key"]
            )
            self.rpc_auth_manager_public_key = PublicKey(manager_pkey)
            agent_pkey, agent_skey = load_certificate(
                self.local_config["agent"]["rpc-auth-agent-keypair"]
            )
            assert agent_skey is not None
            self.rpc_auth_agent_public_key = PublicKey(agent_pkey)
            self.rpc_auth_agent_secret_key = SecretKey(agent_skey)
            log.info(
                "RPC encryption and authentication is enabled. "
                "(agent_public_key = '{}', manager_public_key='{}')",
                self.rpc_auth_agent_public_key.decode("ascii"),
                self.rpc_auth_manager_public_key.decode("ascii"),
            )
            auth_handler = AgentAuthHandler(
                "local",
                self.rpc_auth_manager_public_key,
                self.rpc_auth_agent_public_key,
                self.rpc_auth_agent_secret_key,
            )
        else:
            self.rpc_auth_manager_public_key = None
            self.rpc_auth_agent_public_key = None
            self.rpc_auth_agent_secret_key = None
            auth_handler = None

        backend = self.local_config["agent"]["backend"]
        agent_mod = importlib.import_module(f"ai.backend.agent.{backend.value}")
        self.agent = await agent_mod.get_agent_cls().new(  # type: ignore
            self.etcd,
            self.local_config,
            stats_monitor=self.stats_monitor,
            error_monitor=self.error_monitor,
            agent_public_key=self.rpc_auth_agent_public_key,
        )

        rpc_addr = self.local_config["agent"]["rpc-listen-addr"]
        self.rpc_server = Peer(
            bind=ZeroMQAddress(f"tcp://{rpc_addr}"),
            transport=ZeroMQRPCTransport,
            authenticator=auth_handler,
            scheduler=ExitOrderedAsyncScheduler(),
            serializer=msgpack.packb,
            deserializer=msgpack.unpackb,
            debug_rpc=self.local_config["debug"]["enabled"],
        )
        for func_name in self.rpc_function.functions:
            self.rpc_server.handle_function(func_name, getattr(self, func_name))
        log.info("started handling RPC requests at {}", rpc_addr)

        debug_socket_path = (
            self.local_config["agent"]["ipc-base-path"] / "agent-registry-snapshot.sock"
        )
        server = await asyncio.start_unix_server(
            self.status_snapshot_request_handler, debug_socket_path.as_posix()
        )

        async def _debug_server_task():
            try:
                async with server:
                    await server.serve_forever()
            except Exception:
                log.exception("_debug_server_task():")
                raise

        self.debug_server_task = asyncio.create_task(_debug_server_task())

        await self.etcd.put("ip", rpc_addr.host, scope=ConfigScopes.NODE)
        watcher_port = utils.nmget(self.local_config, "watcher.service-addr.port", None)
        if watcher_port is not None:
            await self.etcd.put("watcher_port", watcher_port, scope=ConfigScopes.NODE)

        await self.update_status("running")

    async def status_snapshot_request_handler(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        def _ensure_serializable(o) -> Any:
            match o:
                case dict() | defaultdict() | OrderedDict():
                    return {_ensure_serializable(k): _ensure_serializable(v) for k, v in o.items()}
                case list():
                    return [_ensure_serializable(e) for e in o]
                case set():
                    return set([_ensure_serializable(e) for e in o])
                case tuple():
                    return tuple([_ensure_serializable(e) for e in o])
                case _:
                    return str(o)

        try:
            if self.agent:
                snapshot = {
                    "registry": {
                        str(kern_id): _ensure_serializable(kern.__getstate__())
                        for kern_id, kern in self.agent.kernel_registry.items()
                    },
                    "allocs": {
                        str(computer): _ensure_serializable(
                            dict(computer_ctx.alloc_map.allocations)
                        )
                        for computer, computer_ctx in self.agent.computers.items()
                    },
                }
                writer.write(json.dumps(snapshot, ensure_ascii=False, indent=2).encode())
            await writer.drain()
            writer.close()
            await writer.wait_closed()
        except Exception:
            log.exception("status_snapshot_request_handler():")
            raise

    async def detect_manager(self):
        log.info("detecting the manager...")
        manager_instances = await self.etcd.get_prefix("nodes/manager")
        if not manager_instances:
            log.warning("watching etcd to wait for the manager being available")
            async with aclosing(self.etcd.watch_prefix("nodes/manager")) as agen:
                async for ev in agen:
                    match ev:
                        case QueueSentinel.CLOSED | QueueSentinel.TIMEOUT:
                            break
                        case _:
                            if ev.event == WatchEventType.PUT and ev.value == "up":
                                break
        log.info("detected at least one manager running")

    async def read_agent_config(self):
        # Fill up Redis configs from etcd.
        self.local_config["redis"] = config.redis_config_iv.check(
            await self.etcd.get_prefix("config/redis"),
        )
        log.info("configured redis: {0}", self.local_config["redis"])

        # Fill up vfolder configs from etcd.
        self.local_config["vfolder"] = config.vfolder_config_iv.check(
            await self.etcd.get_prefix("volumes"),
        )
        if self.local_config["vfolder"]["mount"] is None:
            log.info(
                "assuming use of storage-proxy since vfolder mount path is not configured in etcd"
            )
        else:
            log.info("configured vfolder mount base: {0}", self.local_config["vfolder"]["mount"])
            log.info("configured vfolder fs prefix: {0}", self.local_config["vfolder"]["fsprefix"])

        # Fill up shared agent configurations from etcd.
        agent_etcd_config = agent_etcd_config_iv.check(
            await self.etcd.get_prefix("config/agent"),
        )
        for k, v in agent_etcd_config.items():
            self.local_config["agent"][k] = v

    async def read_agent_config_container(self):
        # Fill up global container configurations from etcd.
        try:
            container_etcd_config = container_etcd_config_iv.check(
                await self.etcd.get_prefix("config/container"),
            )
        except TrafaretDataError as etrafa:
            log.warning("etcd: container-config error: {}".format(etrafa))
            container_etcd_config = {}
        for k, v in container_etcd_config.items():
            self.local_config["container"][k] = v
            log.info("etcd: container-config: {}={}".format(k, v))

    async def __aenter__(self) -> None:
        await self.rpc_server.__aenter__()

    def mark_stop_signal(self, stop_signal: signal.Signals) -> None:
        self._stop_signal = stop_signal

    async def __aexit__(self, *exc_info) -> None:
        # Stop receiving further requests.
        await self.rpc_server.__aexit__(*exc_info)
        self.debug_server_task.cancel()
        await asyncio.sleep(0)
        if not self.debug_server_task.done():
            await self.debug_server_task
        await self.agent.shutdown(self._stop_signal)
        await self.stats_monitor.cleanup()
        await self.error_monitor.cleanup()

    @collect_error
    async def update_status(self, status):
        await self.etcd.put("", status, scope=ConfigScopes.NODE)

    @rpc_function
    @collect_error
    async def update_scaling_group(self, scaling_group):
        cfg_src_path = config.find_config_file("agent")
        with open(cfg_src_path, "r") as f:
            data = tomlkit.load(f)
            data["agent"]["scaling-group"] = scaling_group
        shutil.copy(cfg_src_path, f"{cfg_src_path}.bak")
        with open(cfg_src_path, "w") as f:
            tomlkit.dump(data, f)
        self.local_config["agent"]["scaling-group"] = scaling_group
        log.info("rpc::update_scaling_group()")

    @rpc_function
    @collect_error
    async def ping(self, msg: str) -> str:
        log.debug("rpc::ping()")
        return msg

    @rpc_function
    @collect_error
    async def gather_hwinfo(self) -> Mapping[str, HardwareMetadata]:
        log.debug("rpc::gather_hwinfo()")
        return await self.agent.gather_hwinfo()

    @rpc_function
    @collect_error
    async def ping_kernel(self, kernel_id: str) -> dict[str, float] | None:
        log.debug("rpc::ping_kernel(k:{})", kernel_id)
        return await self.agent.ping_kernel(KernelId(UUID(kernel_id)))

    @rpc_function
    @collect_error
    async def sync_kernel_registry(
        self,
        raw_kernel_session_ids: Iterable[tuple[str, str]],
    ) -> None:
        kernel_session_ids = [
            (KernelId(UUID(raw_kid)), SessionId(UUID(raw_sid)))
            for raw_kid, raw_sid in raw_kernel_session_ids
        ]
        for kid, sid in kernel_session_ids:
            if kid not in self.agent.kernel_registry:
                # produce KernelTerminatedEvent
                await self.agent.produce_event(
                    KernelTerminatedEvent(
                        kid,
                        sid,
                        reason=KernelLifecycleEventReason.ALREADY_TERMINATED,
                    )
                )

        kernel_ids = {kern_id for kern_id, sess_id in kernel_session_ids}
        for kid, kernel in self.agent.kernel_registry.items():
            if kid not in kernel_ids:
                # destroy kernel
                await self.agent.inject_container_lifecycle_event(
                    kid,
                    kernel.session_id,
                    LifecycleEvent.DESTROY,
                    KernelLifecycleEventReason.NOT_FOUND_IN_MANAGER,
                    suppress_events=True,
                )

    @rpc_function
    @collect_error
    async def create_kernels(
        self,
        raw_session_id: str,
        raw_kernel_ids: Sequence[str],
        raw_configs: Sequence[dict],
        raw_cluster_info: dict,
    ):
        cluster_info = cast(ClusterInfo, raw_cluster_info)
        session_id = SessionId(UUID(raw_session_id))
        coros = []
        throttle_sema = asyncio.Semaphore(self.local_config["agent"]["kernel-creation-concurrency"])
        for raw_kernel_id, raw_config in zip(raw_kernel_ids, raw_configs):
            log.info(
                "rpc::create_kernel(k:{0}, img:{1})",
                raw_kernel_id,
                raw_config["image"]["canonical"],
            )
            kernel_id = KernelId(UUID(raw_kernel_id))
            kernel_config = cast(KernelCreationConfig, raw_config)
            coros.append(
                self.agent.create_kernel(
                    session_id,
                    kernel_id,
                    kernel_config,
                    cluster_info,
                    throttle_sema=throttle_sema,
                )
            )
        results = await asyncio.gather(*coros, return_exceptions=True)
        raw_results = []
        errors = []
        for result in results:
            match result:
                case BaseException():
                    errors.append(result)
                case _:
                    raw_results.append({
                        "id": str(result["id"]),
                        "kernel_host": result["kernel_host"],
                        "repl_in_port": result["repl_in_port"],
                        "repl_out_port": result["repl_out_port"],
                        "stdin_port": result["stdin_port"],  # legacy
                        "stdout_port": result["stdout_port"],  # legacy
                        "service_ports": result["service_ports"],
                        "container_id": result["container_id"],
                        "resource_spec": result["resource_spec"],
                        "attached_devices": result["attached_devices"],
                        "agent_addr": result["agent_addr"],
                        "scaling_group": result["scaling_group"],
                    })
        if errors:
            # Raise up the first error.
            if len(errors) == 1:
                raise errors[0]
            raise aiotools.TaskGroupError("agent.create_kernels() failed", errors)
        return raw_results

    @rpc_function
    @collect_error
    async def destroy_kernel(
        self,
        kernel_id: str,
        session_id: str,
        reason: Optional[KernelLifecycleEventReason] = None,
        suppress_events: bool = False,
    ):
        loop = asyncio.get_running_loop()
        done = loop.create_future()
        log.info("rpc::destroy_kernel(k:{0})", kernel_id)
        await self.agent.inject_container_lifecycle_event(
            KernelId(UUID(kernel_id)),
            SessionId(UUID(session_id)),
            LifecycleEvent.DESTROY,
            reason or KernelLifecycleEventReason.USER_REQUESTED,
            done_future=done,
            suppress_events=suppress_events,
        )
        return await done

    @rpc_function
    @collect_error
    async def interrupt_kernel(self, kernel_id: str):
        log.info("rpc::interrupt_kernel(k:{0})", kernel_id)
        await self.agent.interrupt_kernel(KernelId(UUID(kernel_id)))

    @rpc_function
    @collect_error
    async def get_completions(self, kernel_id: str, text: str, opts: dict):
        log.debug("rpc::get_completions(k:{0}, ...)", kernel_id)
        await self.agent.get_completions(KernelId(UUID(kernel_id)), text, opts)

    @rpc_function
    @collect_error
    async def get_logs(self, kernel_id: str):
        log.info("rpc::get_logs(k:{0})", kernel_id)
        return await self.agent.get_logs(KernelId(UUID(kernel_id)))

    @rpc_function
    @collect_error
    async def restart_kernel(
        self,
        session_id: str,
        kernel_id: str,
        updated_config: dict,
    ) -> dict[str, Any]:
        log.info("rpc::restart_kernel(s:{0}, k:{1})", session_id, kernel_id)
        return await self.agent.restart_kernel(
            SessionId(UUID(session_id)),
            KernelId(UUID(kernel_id)),
            cast(KernelCreationConfig, updated_config),
        )

    @rpc_function
    @collect_error
    async def execute(
        self,
        session_id: str,
        kernel_id: str,
        api_version: int,
        run_id: str,
        mode: Literal["query", "batch", "continue", "input"],
        code: str,
        opts: dict[str, Any],
        flush_timeout: float,
    ) -> dict[str, Any]:
        if mode != "continue":
            log.info(
                "rpc::execute(k:{0}, run-id:{1}, mode:{2}, code:{3!r})",
                kernel_id,
                run_id,
                mode,
                code[:20] + "..." if len(code) > 20 else code,
            )
        result = await self.agent.execute(
            SessionId(UUID(session_id)),
            KernelId(UUID(kernel_id)),
            run_id,
            mode,
            code,
            opts=opts,
            api_version=api_version,
            flush_timeout=flush_timeout,
        )
        return result

    @rpc_function
    @collect_error
    async def start_service(
        self,
        kernel_id: str,
        service: str,
        opts: dict[str, Any],
    ) -> dict[str, Any]:
        log.info("rpc::start_service(k:{0}, app:{1})", kernel_id, service)
        return await self.agent.start_service(KernelId(UUID(kernel_id)), service, opts)

    @rpc_function
    @collect_error
    async def get_commit_status(
        self,
        kernel_id: str,
        subdir: str,
    ) -> dict[str, Any]:
        # Only this function logs debug since web sends request at short intervals
        log.debug("rpc::get_commit_status(k:{})", kernel_id)
        status: CommitStatus = await self.agent.get_commit_status(
            KernelId(UUID(kernel_id)),
            subdir,
        )
        return {
            "kernel": kernel_id,
            "status": status.value,
        }

    @rpc_function
    @collect_error
    async def commit(
        self,
        kernel_id: str,
        subdir: str,
        *,
        canonical: str | None = None,
        filename: str | None = None,
        extra_labels: dict[str, str] = {},
    ) -> dict[str, Any]:
        log.info("rpc::commit(k:{})", kernel_id)
        bgtask_mgr = self.agent.background_task_manager

        async def _commit(reporter: ProgressReporter) -> None:
            await self.agent.commit(
                reporter,
                KernelId(UUID(kernel_id)),
                subdir,
                canonical=canonical,
                filename=filename,
                extra_labels=extra_labels,
            )

        task_id = await bgtask_mgr.start(_commit)
        return {
            "bgtask_id": str(task_id),
            "kernel": kernel_id,
            "path": str(Path(subdir, filename)) if filename else None,
        }

    @rpc_function
    @collect_error
    async def push_image(
        self,
        canonical: str,
        architecture: str,
        registry_conf: ImageRegistry,
        *,
        is_local: bool = False,
    ) -> dict[str, Any]:
        log.info("rpc::push_image(c:{})", canonical)
        bgtask_mgr = self.agent.background_task_manager

        async def _push_image(reporter: ProgressReporter) -> None:
            await self.agent.push_image(
                ImageRef(
                    canonical,
                    known_registries=["*"],
                    is_local=is_local,
                    architecture=architecture,
                ),
                registry_conf,
            )

        task_id = await bgtask_mgr.start(_push_image)
        return {
            "bgtask_id": str(task_id),
            "canonical": canonical,
        }

    @rpc_function
    @collect_error
    async def get_local_config(self) -> Mapping[str, Any]:
        agent_config: Mapping[str, Any] = self.local_config["agent"]
        report_path: Path | None = agent_config.get("abuse-report-path")
        return {
            "agent": {
                "abuse-report-path": str(report_path) if report_path is not None else "",
            },
            "watcher": self.local_config["watcher"],
        }

    @rpc_function
    @collect_error
    async def shutdown_service(
        self,
        kernel_id,  # type: str
        service,  # type: str
    ):
        log.info("rpc::shutdown_service(k:{0}, app:{1})", kernel_id, service)
        return await self.agent.shutdown_service(KernelId(UUID(kernel_id)), service)

    @rpc_function
    @collect_error
    async def upload_file(self, kernel_id: str, filename: str, filedata: bytes):
        log.info("rpc::upload_file(k:{0}, fn:{1})", kernel_id, filename)
        await self.agent.accept_file(KernelId(UUID(kernel_id)), filename, filedata)

    @rpc_function
    @collect_error
    async def download_file(self, kernel_id: str, filepath: str):
        log.info("rpc::download_file(k:{0}, fn:{1})", kernel_id, filepath)
        return await self.agent.download_file(KernelId(UUID(kernel_id)), filepath)

    @rpc_function
    @collect_error
    async def download_single(self, kernel_id: str, filepath: str):
        log.info("rpc::download_single(k:{0}, fn:{1})", kernel_id, filepath)
        return await self.agent.download_single(KernelId(UUID(kernel_id)), filepath)

    @rpc_function
    @collect_error
    async def list_files(self, kernel_id: str, path: str):
        log.info("rpc::list_files(k:{0}, fn:{1})", kernel_id, path)
        return await self.agent.list_files(KernelId(UUID(kernel_id)), path)

    @rpc_function
    @collect_error
    async def shutdown_agent(self, terminate_kernels: bool):
        # TODO: implement
        log.info("rpc::shutdown_agent()")
        pass

    @rpc_function
    @collect_error
    async def create_local_network(self, network_name: str) -> None:
        log.debug("rpc::create_local_network(name:{})", network_name)
        return await self.agent.create_local_network(network_name)

    @rpc_function
    @collect_error
    async def destroy_local_network(self, network_name: str) -> None:
        log.debug("rpc::destroy_local_network(name:{})", network_name)
        return await self.agent.destroy_local_network(network_name)

    @rpc_function
    @collect_error
    async def reset_agent(self):
        log.debug("rpc::reset()")
        kernel_ids = tuple(self.agent.kernel_registry.keys())
        tasks = []
        for kernel_id in kernel_ids:
            try:
                task = asyncio.ensure_future(self.agent.destroy_kernel(kernel_id, "agent-reset"))
                tasks.append(task)
            except Exception:
                await self.error_monitor.capture_exception()
                log.exception("reset: destroying {0}", kernel_id)
        await asyncio.gather(*tasks)

    @rpc_function
    @collect_error
    async def assign_port(self):
        log.debug("rpc::assign_port()")
        return self.agent.port_pool.pop()

    @rpc_function
    @collect_error
    async def release_port(self, port_no: int):
        log.debug("rpc::release_port(port_no:{})", port_no)
        self.agent.port_pool.add(port_no)


@aiotools.server
async def server_main_logwrapper(
    loop: asyncio.AbstractEventLoop,
    pidx: int,
    _args: Tuple[Any, ...],
) -> AsyncGenerator[None, signal.Signals]:
    setproctitle(f"backend.ai: agent worker-{pidx}")
    log_endpoint = _args[1]
    logger = Logger(_args[0]["logging"], is_master=False, log_endpoint=log_endpoint)
    with logger:
        async with server_main(loop, pidx, _args):
            yield


@aiotools.server
async def server_main(
    loop: asyncio.AbstractEventLoop,
    pidx: int,
    _args: Tuple[Any, ...],
) -> AsyncGenerator[None, signal.Signals]:
    local_config = _args[0]

    # Start aiomonitor.
    # Port is set by config (default=50200).
    loop.set_debug(local_config["debug"]["asyncio"])
    monitor = aiomonitor.Monitor(
        loop,
        termui_port=local_config["agent"]["aiomonitor-termui-port"] + pidx,
        webui_port=local_config["agent"]["aiomonitor-webui-port"] + pidx,
        console_enabled=False,
        hook_task_factory=local_config["debug"]["enhanced-aiomonitor-task-info"],
    )
    monitor.prompt = "monitor (agent) >>> "
    monitor.console_locals["local_config"] = local_config
    aiomon_started = False
    try:
        monitor.start()
        aiomon_started = True
    except Exception as e:
        log.warning("aiomonitor could not start but skipping this error to continue", exc_info=e)

    log.info("Preparing kernel runner environments...")
    kernel_mod = importlib.import_module(
        f"ai.backend.agent.{local_config['agent']['backend'].value}.kernel",
    )
    krunner_volumes = await kernel_mod.prepare_krunner_env(local_config)  # type: ignore
    # TODO: merge k8s branch: nfs_mount_path = local_config['baistatic']['mounted-at']
    log.info("Kernel runner environments: {}", [*krunner_volumes.keys()])
    local_config["container"]["krunner-volumes"] = krunner_volumes

    if not local_config["agent"]["id"]:
        local_config["agent"]["id"] = await identity.get_instance_id()
    if not local_config["agent"]["instance-type"]:
        local_config["agent"]["instance-type"] = await identity.get_instance_type()

    etcd_credentials = None
    if local_config["etcd"]["user"]:
        etcd_credentials = {
            "user": local_config["etcd"]["user"],
            "password": local_config["etcd"]["password"],
        }
    scope_prefix_map = {
        ConfigScopes.GLOBAL: "",
        ConfigScopes.SGROUP: f"sgroup/{local_config['agent']['scaling-group']}",
        ConfigScopes.NODE: f"nodes/agents/{local_config['agent']['id']}",
    }
    etcd = AsyncEtcd(
        local_config["etcd"]["addr"],
        local_config["etcd"]["namespace"],
        scope_prefix_map,
        credentials=etcd_credentials,
    )

    rpc_addr = local_config["agent"]["rpc-listen-addr"]
    if not rpc_addr.host:
        _subnet_hint = await etcd.get("config/network/subnet/agent")
        subnet_hint = None
        if _subnet_hint is not None:
            subnet_hint = ip_network(_subnet_hint)
        log.debug("auto-detecting agent host")
        local_config["agent"]["rpc-listen-addr"] = HostPortPair(
            await identity.get_instance_ip(subnet_hint),
            rpc_addr.port,
        )
    if "kernel-host" in local_config["container"]:
        log.warning(
            "The configuration parameter `container.kernel-host` is deprecated; "
            "use `container.bind-host` instead!"
        )
        # fallback for legacy configs
        local_config["container"]["bind-host"] = local_config["container"]["kernel-host"]
    if not local_config["container"]["bind-host"]:
        log.debug(
            "auto-detecting `container.bind-host` from container subnet config "
            "and agent.rpc-listen-addr"
        )
        local_config["container"]["bind-host"] = await get_subnet_ip(
            etcd,
            "container",
            fallback_addr=local_config["agent"]["rpc-listen-addr"].host,
        )
    log.info("Agent external IP: {}", local_config["agent"]["rpc-listen-addr"].host)
    log.info("Container external IP: {}", local_config["container"]["bind-host"])
    if not local_config["agent"]["region"]:
        local_config["agent"]["region"] = await identity.get_instance_region()
    log.info(
        "Node ID: {0} (machine-type: {1}, host: {2})",
        local_config["agent"]["id"],
        local_config["agent"]["instance-type"],
        rpc_addr.host,
    )

    # Pre-load compute plugin configurations.
    local_config["plugins"] = await etcd.get_prefix_dict("config/plugins/accelerator")

    # Start RPC server.
    global agent_instance
    agent = await AgentRPCServer.new(
        etcd,
        local_config,
        skip_detect_manager=local_config["agent"]["skip-manager-detection"],
    )
    agent_instance = agent
    monitor.console_locals["agent"] = agent

    # Run!
    try:
        async with agent:
            stop_signal = yield
            agent.mark_stop_signal(stop_signal)
    finally:
        if aiomon_started:
            monitor.close()


@click.group(invoke_without_command=True)
@click.option(
    "-f",
    "--config-path",
    "--config",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="The config file path. (default: ./agent.conf and /etc/backend.ai/agent.conf)",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Set the logging level to DEBUG",
)
@click.option(
    "--log-level",
    type=click.Choice([*LogSeverity], case_sensitive=False),
    default=LogSeverity.INFO,
    help="Set the logging verbosity level",
)
@click.pass_context
def main(
    cli_ctx: click.Context,
    config_path: Path,
    log_level: LogSeverity,
    debug: bool = False,
) -> int:
    """Start the agent service as a foreground process."""
    # Determine where to read configuration.
    try:
        raw_cfg, cfg_src_path = config.read_from_file(config_path, "agent")
    except config.ConfigurationError as e:
        print(
            "ConfigurationError: Could not read or validate the storage-proxy local config:",
            file=sys.stderr,
        )
        print(pformat(e.invalid_data), file=sys.stderr)
        raise click.Abort()

    # Override the read config with environment variables (for legacy).
    config.override_with_env(raw_cfg, ("etcd", "namespace"), "BACKEND_NAMESPACE")
    config.override_with_env(raw_cfg, ("etcd", "addr"), "BACKEND_ETCD_ADDR")
    config.override_with_env(raw_cfg, ("etcd", "user"), "BACKEND_ETCD_USER")
    config.override_with_env(raw_cfg, ("etcd", "password"), "BACKEND_ETCD_PASSWORD")
    config.override_with_env(
        raw_cfg, ("agent", "rpc-listen-addr", "host"), "BACKEND_AGENT_HOST_OVERRIDE"
    )
    config.override_with_env(raw_cfg, ("agent", "rpc-listen-addr", "port"), "BACKEND_AGENT_PORT")
    config.override_with_env(raw_cfg, ("agent", "pid-file"), "BACKEND_PID_FILE")
    config.override_with_env(raw_cfg, ("container", "port-range"), "BACKEND_CONTAINER_PORT_RANGE")
    config.override_with_env(raw_cfg, ("container", "bind-host"), "BACKEND_BIND_HOST_OVERRIDE")
    config.override_with_env(raw_cfg, ("container", "sandbox-type"), "BACKEND_SANDBOX_TYPE")
    config.override_with_env(raw_cfg, ("container", "scratch-root"), "BACKEND_SCRATCH_ROOT")

    if debug:
        log_level = LogSeverity.DEBUG
    config.override_key(raw_cfg, ("debug", "enabled"), log_level == LogSeverity.DEBUG)
    config.override_key(raw_cfg, ("logging", "level"), log_level)
    config.override_key(raw_cfg, ("logging", "pkg-ns", "ai.backend"), log_level)

    # Validate and fill configurations
    # (allow_extra will make configs to be forward-copmatible)
    try:
        cfg = config.check(raw_cfg, agent_local_config_iv)
        if cfg["agent"]["backend"] == AgentBackend.KUBERNETES:
            if cfg["container"]["scratch-type"] == "k8s-nfs" and (
                cfg["container"]["scratch-nfs-address"] is None
                or cfg["container"]["scratch-nfs-options"] is None
            ):
                raise ValueError(
                    "scratch-nfs-address and scratch-nfs-options are required for k8s-nfs"
                )
        if cfg["agent"]["backend"] == AgentBackend.DOCKER:
            config.check(raw_cfg, docker_extra_config_iv)
        if "debug" in cfg and cfg["debug"]["enabled"]:
            print("== Agent configuration ==")
            pprint(cfg)
        cfg["_src"] = cfg_src_path
    except config.ConfigurationError as e:
        print("ConfigurationError: Validation of agent local config has failed:", file=sys.stderr)
        print(pformat(e.invalid_data), file=sys.stderr)
        raise click.Abort()

    # FIXME: Remove this after ARM64 support lands on Jail
    current_arch = get_arch_name()
    if cfg["container"]["sandbox-type"] == "jail" and current_arch != "x86_64":
        print(f"ConfigurationError: Jail sandbox is not supported on architecture {current_arch}")
        raise click.Abort()

    rpc_host = cfg["agent"]["rpc-listen-addr"].host
    if isinstance(rpc_host, BaseIPAddress) and (rpc_host.is_unspecified or rpc_host.is_link_local):
        print(
            "ConfigurationError: "
            "Cannot use link-local or unspecified IP address as the RPC listening host.",
            file=sys.stderr,
        )
        raise click.Abort()

    if os.getuid() != 0 and cfg["container"]["stats-type"] == "cgroup":
        print(
            "Cannot use cgroup statistics collection mode unless the agent runs as root.",
            file=sys.stderr,
        )
        raise click.Abort()

    if os.getuid() != 0 and cfg["container"]["scratch-type"] == "hostfile":
        print(
            "Cannot use hostfile scratch type unless the agent runs as root.",
            file=sys.stderr,
        )
        raise click.Abort()

    if cli_ctx.invoked_subcommand is None:
        if cfg["debug"]["coredump"]["enabled"]:
            if not sys.platform.startswith("linux"):
                print(
                    "ConfigurationError: Storing container coredumps is only supported in Linux.",
                    file=sys.stderr,
                )
                raise click.Abort()
            core_pattern = Path("/proc/sys/kernel/core_pattern").read_text().strip()
            if core_pattern.startswith("|") or not core_pattern.startswith("/"):
                print(
                    "ConfigurationError: "
                    "/proc/sys/kernel/core_pattern must be an absolute path "
                    "to enable container coredumps.",
                    file=sys.stderr,
                )
                raise click.Abort()
            cfg["debug"]["coredump"]["core_path"] = Path(core_pattern).parent

        cfg["agent"]["pid-file"].write_text(str(os.getpid()))
        image_commit_path = cfg["agent"]["image-commit-path"]
        image_commit_path.mkdir(parents=True, exist_ok=True)
        ipc_base_path = cfg["agent"]["ipc-base-path"]
        log_sockpath = ipc_base_path / f"agent-logger-{os.getpid()}.sock"
        log_sockpath.parent.mkdir(parents=True, exist_ok=True)
        log_endpoint = f"ipc://{log_sockpath}"
        cfg["logging"]["endpoint"] = log_endpoint
        try:
            logger = Logger(cfg["logging"], is_master=True, log_endpoint=log_endpoint)
            with logger:
                ns = cfg["etcd"]["namespace"]
                setproctitle(f"backend.ai: agent {ns}")
                log.info("Backend.AI Agent {0}", VERSION)
                log.info("runtime: {0}", utils.env_info())

                log_config = logging.getLogger("ai.backend.agent.config")
                if log_level == "DEBUG":
                    log_config.debug("debug mode enabled.")

                if cfg["agent"]["event-loop"] == "uvloop":
                    import uvloop

                    uvloop.install()
                    log.info("Using uvloop as the event loop backend")
                aiotools.start_server(
                    server_main_logwrapper,
                    num_workers=1,
                    args=(cfg, log_endpoint),
                    wait_timeout=5.0,
                )
                log.info("exit.")
        finally:
            if cfg["agent"]["pid-file"].is_file():
                # check is_file() to prevent deleting /dev/null!
                cfg["agent"]["pid-file"].unlink()
    else:
        # Click is going to invoke a subcommand.
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
