from __future__ import annotations

import asyncio
from dataclasses import dataclass
import functools
import importlib
import logging
import logging.config
import os
import os.path
import shutil
import signal
import ssl
import sys
import time
from collections import OrderedDict, defaultdict
from datetime import datetime, timezone
from ipaddress import IPv4Address, IPv6Address, ip_network
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

import aiohttp_cors
import aiomonitor
import aiotools
import click
import tomlkit
from aiohttp import web
from aiotools import aclosing
from callosum.lower.zeromq import ZeroMQAddress, ZeroMQRPCTransport
from callosum.ordering import ExitOrderedAsyncScheduler
from callosum.rpc import Peer, RPCMessage
from etcd_client import WatchEventType
from setproctitle import setproctitle
from zmq.auth.certs import load_certificate

from ai.backend.agent.agent import EVENT_DISPATCHER_CONSUMER_GROUP
from ai.backend.agent.manager import Agent, AgentArgs
from ai.backend.agent.metrics.metric import RPCMetricObserver
from ai.backend.agent.resources import scan_gpu_alloc_map
from ai.backend.common import config, identity, msgpack, utils
from ai.backend.common.auth import AgentAuthHandler, PublicKey, SecretKey
from ai.backend.common.bgtask.bgtask import BackgroundTaskManager, ProgressReporter
from ai.backend.common.defs import REDIS_STREAM_DB
from ai.backend.common.docker import ImageRef
from ai.backend.common.dto.agent.response import AbstractAgentResp, PurgeImagesResp
from ai.backend.common.dto.agent.rpc_request import PurgeImagesReq
from ai.backend.common.etcd import AsyncEtcd, ConfigScopes
from ai.backend.common.events.image import (
    ImagePullFailedEvent,
    ImagePullFinishedEvent,
    ImagePullStartedEvent,
)
from ai.backend.common.events.kernel import (
    KernelLifecycleEventReason,
    KernelTerminatedEvent,
)
from ai.backend.common.json import pretty_json
from ai.backend.common.message_queue.hiredis_queue import HiRedisMQArgs, HiRedisQueue
from ai.backend.common.message_queue.queue import AbstractMessageQueue
from ai.backend.common.message_queue.redis_queue import RedisMQArgs, RedisQueue
from ai.backend.common.metrics.http import (
    build_api_metric_middleware,
    build_prometheus_metrics_handler,
)
from ai.backend.common.metrics.metric import CommonMetricRegistry
from ai.backend.common.metrics.profiler import Profiler, PyroscopeArgs
from ai.backend.common.types import (
    AutoPullBehavior,
    ClusterInfo,
    CommitStatus,
    HardwareMetadata,
    HostPortPair,
    ImageConfig,
    ImageRegistry,
    KernelCreationConfig,
    KernelId,
    QueueSentinel,
    RedisConnectionInfo,
    RedisTarget,
    SessionId,
    aobject,
)
from ai.backend.common.utils import current_loop
from ai.backend.logging import BraceStyleAdapter, Logger, LogLevel

from . import __version__ as VERSION
from .config import (
    agent_etcd_config_iv,
    agent_local_config_iv,
    container_etcd_config_iv,
    docker_extra_config_iv,
    read_agent_config,
    read_agent_config_container,
)
from .exception import ResourceError
from .monitor import AgentErrorPluginContext, AgentStatsPluginContext
from .types import AgentBackend, KernelOwnershipData, LifecycleEvent, VolumeInfo
from .utils import get_arch_name, get_subnet_ip

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

def collect_error(meth: Callable) -> Callable:
    @functools.wraps(meth)
    async def _inner(self: AgentRPCHandler, *args, **kwargs):
        try:
            return await meth(self, *args, **kwargs)
        except Exception:
            await self._agent.produce_error_event()
            raise

    return _inner


class RPCFunctionRegistry:
    functions: Set[str]
    _metric_observer: RPCMetricObserver

    def __init__(self) -> None:
        self.functions = set()
        self._metric_observer = RPCMetricObserver.instance()

    def __call__(
        self,
        meth: Callable[..., Coroutine[None, None, Any]],
    ) -> Callable[[AgentRPCHandler, RPCMessage], Coroutine[None, None, Any]]:
        @functools.wraps(meth)
        @_collect_metrics(self._metric_observer)
        async def _inner(self_: AgentRPCHandler, request: RPCMessage) -> Any:
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


class RPCFunctionRegistryV2:
    functions: Set[str]
    _metric_observer: RPCMetricObserver

    def __init__(self) -> None:
        self.functions = set()
        self._metric_observer = RPCMetricObserver.instance()

    def __call__(
        self,
        meth: Callable[..., Coroutine[None, None, AbstractAgentResp]],
    ) -> Callable[[AgentRPCHandler, RPCMessage], Coroutine[None, None, Any]]:
        @functools.wraps(meth)
        @_collect_metrics(self._metric_observer)
        async def _inner(self_: AgentRPCHandler, request: RPCMessage) -> Any:
            try:
                if request.body is None:
                    return await meth(self_)
                else:
                    res = await meth(
                        self_,
                        *request.body["args"],
                        **request.body["kwargs"],
                    )
                    return res.as_dict()
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


def _collect_metrics(observer: RPCMetricObserver) -> Callable:
    def decorator(meth: Callable) -> Callable[[AgentRPCHandler, RPCMessage], Any]:
        @functools.wraps(meth)
        async def _inner(self: AgentRPCHandler, *args, **kwargs) -> Any:
            start_time = time.perf_counter()
            try:
                res = await meth(self, *args, **kwargs)
                duration = time.perf_counter() - start_time
                observer.observe_rpc_request_success(
                    method=meth.__name__,
                    duration=duration,
                )
                return res
            except BaseException as e:
                duration = time.perf_counter() - start_time
                observer.observe_rpc_request_failure(
                    method=meth.__name__,
                    duration=duration,
                    exception=e,
                )
                raise

        return _inner

    return decorator

@dataclass
class Authenticator:
    rpc_auth_manager_public_key: PublicKey
    rpc_auth_agent_public_key: PublicKey
    rpc_auth_agent_secret_key: SecretKey
    auth_handler: AgentAuthHandler

@dataclass
class AgentRPCHandlerArgs:
    etcd: AsyncEtcd
    agent: Agent
    background_task_manager: BackgroundTaskManager
    local_config: Mapping[str, Any]


class AgentRPCHandler:
    _etcd: AsyncEtcd
    _agent: Agent
    _background_task_manager: BackgroundTaskManager
    _local_config: Mapping[str, Any]

    def __init__(
        self,
        args: AgentRPCHandlerArgs,
    ) -> None:
        self._etcd = args.etcd
        self._agent = args.agent
        self._background_task_manager = args.background_task_manager
        self._local_config = args.local_config

    @collect_error
    async def update_scaling_group(self, scaling_group):
        cfg_src_path = config.find_config_file("agent")
        with open(cfg_src_path, "r") as f:
            data = tomlkit.load(f)
            data["agent"]["scaling-group"] = scaling_group
        shutil.copy(cfg_src_path, f"{cfg_src_path}.bak")
        with open(cfg_src_path, "w") as f:
            tomlkit.dump(data, f)
        self._local_config["agent"]["scaling-group"] = scaling_group
        log.info("rpc::update_scaling_group()")

    @collect_error
    async def ping(self, msg: str) -> str:
        log.debug("rpc::ping()")
        return msg

    @collect_error
    async def gather_hwinfo(self) -> Mapping[str, HardwareMetadata]:
        log.debug("rpc::gather_hwinfo()")
        return await self._agent.gather_hwinfo()

    @collect_error
    async def ping_kernel(self, kernel_id: str) -> dict[str, float] | None:
        log.debug("rpc::ping_kernel(k:{})", kernel_id)
        kernel = await self._agent.get_kernel(KernelId(UUID(kernel_id)))
        return await kernel.ping()
        return await self._agent.ping_kernel(KernelId(UUID(kernel_id)))

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
            if kid not in self._agent.kernel_registry:
                # produce KernelTerminatedEvent
                await self._agent.produce_event(
                    KernelTerminatedEvent(
                        kid,
                        sid,
                        reason=KernelLifecycleEventReason.ALREADY_TERMINATED,
                    )
                )

        kernel_ids = {kern_id for kern_id, sess_id in kernel_session_ids}
        for kid, kernel in self._agent.kernel_registry.items():
            if kid not in kernel_ids:
                # destroy kernel
                await self._agent.inject_container_lifecycle_event(
                    kid,
                    kernel.session_id,
                    LifecycleEvent.DESTROY,
                    KernelLifecycleEventReason.NOT_FOUND_IN_MANAGER,
                    suppress_events=True,
                )

    @collect_error
    async def check_and_pull(
        self,
        image_configs: Mapping[str, ImageConfig],
    ) -> dict[str, str]:
        """
        Check whether the agent has an image.
        Spawn a bgtask that pulls the specified image and return bgtask ID.
        """
        log.info(
            "rpc::check_and_pull(images:{0})",
            [
                {
                    "name": conf["canonical"],
                    "project": conf["project"],
                    "registry": conf["registry"]["name"],
                }
                for conf in image_configs.values()
            ],
        )

        async def _pull(reporter: ProgressReporter, *, img_conf: ImageConfig) -> None:
            img_ref = ImageRef.from_image_config(img_conf)
            image_registry = self._agent.image_registry
            need_to_pull = await image_registry.check_image(
                img_ref, img_conf["digest"], AutoPullBehavior(img_conf["auto_pull"])
            )
            if need_to_pull:
                log.info(f"rpc::check_and_pull() start pulling {str(img_ref)}")
                await self._agent.produce_event(
                    ImagePullStartedEvent(
                        image=str(img_ref),
                        image_ref=img_ref,
                        agent_id=self._agent.id,
                        timestamp=datetime.now(timezone.utc).timestamp(),
                    )
                )
                image_pull_timeout = cast(
                    Optional[float], self._local_config["agent"]["api"]["pull-timeout"]
                )
                try:
                    await image_registry.pull_image(
                        img_ref, img_conf["registry"], timeout=image_pull_timeout
                    )
                except asyncio.TimeoutError:
                    log.exception(
                        f"Image pull timeout (img:{str(img_ref)}, sec:{image_pull_timeout})"
                    )
                    await self._agent.produce_event(
                        ImagePullFailedEvent(
                            image=str(img_ref),
                            image_ref=img_ref,
                            agent_id=self._agent.id,
                            msg=f"timeout (s:{image_pull_timeout})",
                        )
                    )
                except Exception as e:
                    log.exception(f"Image pull failed (img:{img_ref}, err:{repr(e)})")
                    await self._agent.produce_event(
                        ImagePullFailedEvent(
                            image=str(img_ref),
                            image_ref=img_ref,
                            agent_id=self._agent.id,
                            msg=repr(e),
                        )
                    )
                else:
                    log.info(f"Image pull succeeded {img_ref}")
                    await self._agent.produce_event(
                        ImagePullFinishedEvent(
                            image=str(img_ref),
                            image_ref=img_ref,
                            agent_id=self._agent.id,
                            timestamp=datetime.now(timezone.utc).timestamp(),
                        )
                    )
            else:
                log.debug(f"No need to pull image {img_ref}")
                await self._agent.produce_event(
                    ImagePullFinishedEvent(
                        image=str(img_ref),
                        image_ref=img_ref,
                        agent_id=self._agent.id,
                        timestamp=datetime.now(timezone.utc).timestamp(),
                        msg="Image already exists",
                    )
                )

        ret: dict[str, str] = {}
        for img, img_conf in image_configs.items():
            task_id = await self._background_task_manager.start(_pull, img_conf=img_conf)
            ret[img] = task_id.hex
        return ret

    @collect_error
    async def create_kernels(
        self,
        raw_session_id: str,
        raw_kernel_ids: Sequence[str],
        raw_configs: Sequence[dict],
        raw_cluster_info: dict,
        kernel_image_refs: dict[KernelId, ImageRef],
    ):
        cluster_info = cast(ClusterInfo, raw_cluster_info)
        session_id = SessionId(UUID(raw_session_id))
        coros = []
        throttle_sema = asyncio.Semaphore(self._local_config["agent"]["kernel-creation-concurrency"])
        for raw_kernel_id, raw_config in zip(raw_kernel_ids, raw_configs):
            log.info(
                "rpc::create_kernel(k:{0}, img:{1})",
                raw_kernel_id,
                raw_config["image"]["canonical"],
            )
            kernel_id = KernelId(UUID(raw_kernel_id))
            kernel_config = cast(KernelCreationConfig, raw_config)
            coros.append(
                self._agent.create_kernel(
                    KernelOwnershipData(
                        kernel_id,
                        session_id,
                        self._agent.id,
                        raw_config.get("owner_user_id"),
                        raw_config.get("owner_project_id"),
                    ),
                    kernel_image_refs[kernel_id],
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
        kernel = await self._agent.get_kernel(KernelId(UUID(kernel_id)))
        await kernel.destroy_kernel(reason or KernelLifecycleEventReason.USER_REQUESTED)
        await self._agent.inject_container_lifecycle_event(
            KernelId(UUID(kernel_id)),
            SessionId(UUID(session_id)),
            LifecycleEvent.DESTROY,
            reason or KernelLifecycleEventReason.USER_REQUESTED,
            done_future=done,
            suppress_events=suppress_events,
        )
        return await done

    @collect_error
    async def interrupt_kernel(self, kernel_id: str):
        log.info("rpc::interrupt_kernel(k:{0})", kernel_id)
        kernel = await self._agent.get_kernel(KernelId(UUID(kernel_id)))
        await kernel.kernel().interrupt_kernel()

    @collect_error
    async def get_completions(self, kernel_id: str, text: str, opts: dict):
        log.debug("rpc::get_completions(k:{0}, ...)", kernel_id)
        kernel = await self._agent.get_kernel(KernelId(UUID(kernel_id)))
        await kernel.kernel().get_completions(text, opts)

    @collect_error
    async def get_logs(self, kernel_id: str):
        log.info("rpc::get_logs(k:{0})", kernel_id)
        kernel = await self._agent.get_kernel(KernelId(UUID(kernel_id)))
        return await kernel.kernel().get_logs()

    @collect_error
    async def restart_kernel(
        self,
        session_id: str,
        kernel_id: str,
        kernel_image: ImageRef,
        updated_config: dict,
    ) -> dict[str, Any]:
        log.info("rpc::restart_kernel(s:{0}, k:{1})", session_id, kernel_id)
        kernel = await self._agent.get_kernel(KernelId(UUID(kernel_id)))
        kernel.kernel
        return await self._agent.restart_kernel(
            KernelOwnershipData(
                KernelId(UUID(kernel_id)),
                SessionId(UUID(session_id)),
                self._agent.id,
            ),
            kernel_image,
            cast(KernelCreationConfig, updated_config),
        )

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
        
        kernel = await self._agent.get_kernel(KernelId(UUID(kernel_id)))
        result = await kernel.execute(
            run_id,
            mode,
            code,
            opts=opts,
            api_version=api_version,
            flush_timeout=flush_timeout,
        )
        return result

    @collect_error
    async def trigger_batch_execution(
        self,
        session_id: str,
        kernel_id: str,
        code: str,
        timeout: Optional[float],
    ) -> None:
        log.info(
            "rpc::trigger_batch_execution(k:{0}, s:{1}, code:{2}, timeout:{3})",
            kernel_id,
            session_id,
            code,
            timeout,
        )
        
        await self._agent.create_batch_execution_task(
            SessionId(UUID(session_id)), KernelId(UUID(kernel_id)), code, timeout
        )

    @collect_error
    async def start_service(
        self,
        kernel_id: str,
        service: str,
        opts: dict[str, Any],
    ) -> dict[str, Any]:
        log.info("rpc::start_service(k:{0}, app:{1})", kernel_id, service)
        kernel = await self._agent.get_kernel(KernelId(UUID(kernel_id)))
        return await kernel.kernel().start_service(service, opts)

    @collect_error
    async def get_commit_status(
        self,
        kernel_id: str,
        subdir: str,
    ) -> dict[str, Any]:
        # Only this function logs debug since web sends request at short intervals
        log.debug("rpc::get_commit_status(k:{})", kernel_id)
        kernel = await self._agent.get_kernel(KernelId(UUID(kernel_id)))
        status = await kernel.kernel().check_duplicate_commit(subdir)
        return {
            "kernel": kernel_id,
            "status": status.value,
        }

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
        kernel = await self._agent.get_kernel(KernelId(UUID(kernel_id)))
        async def _commit(reporter: ProgressReporter) -> None:
            await kernel.kernel().commit(
                reporter,
                KernelId(UUID(kernel_id)),
                subdir,
                canonical=canonical,
                filename=filename,
                extra_labels=extra_labels,
            )

        task_id = await self._background_task_manager.start(_commit)
        return {
            "bgtask_id": str(task_id),
            "kernel": kernel_id,
            "path": str(Path(subdir, filename)) if filename else None,
        }

    @collect_error
    async def push_image(
        self,
        image_ref: ImageRef,
        registry_conf: ImageRegistry,
    ) -> dict[str, Any]:
        log.info("rpc::push_image(c:{})", image_ref.canonical)
        image_push_timeout = cast(
            Optional[float], self._local_config["agent"]["api"]["push-timeout"]
        )

        async def _push_image(reporter: ProgressReporter) -> None:
            await self._agent.image_registry.push_image(
                image_ref,
                registry_conf,
                timeout=image_push_timeout,
            )

        task_id = await self._background_task_manager.start(_push_image)
        return {
            "bgtask_id": str(task_id),
            "canonical": image_ref.canonical,
        }

    @collect_error
    async def purge_images(
        self, image_canonicals: list[str], force: bool, noprune: bool
    ) -> PurgeImagesResp:
        log.info(
            "rpc::purge_images(images:{0}, force:{1}, noprune:{2})",
            image_canonicals,
            force,
            noprune,
        )
        return await self._agent.image_registry.purge_images(
            PurgeImagesReq(images=image_canonicals, force=force, noprune=noprune)
        )

    @collect_error
    async def get_local_config(self) -> Mapping[str, Any]:
        agent_config: Mapping[str, Any] = self._local_config["agent"]
        report_path: Path | None = agent_config.get("abuse-report-path")
        return {
            "agent": {
                "abuse-report-path": str(report_path) if report_path is not None else "",
            },
            "watcher": self._local_config["watcher"],
        }

    @collect_error
    async def shutdown_service(
        self,
        kernel_id,  # type: str
        service,  # type: str
    ):
        log.info("rpc::shutdown_service(k:{0}, app:{1})", kernel_id, service)
        kernel = await self._agent.get_kernel(KernelId(UUID(kernel_id)))
        return await kernel.kernel().shutdown_service(service)

    @collect_error
    async def upload_file(self, kernel_id: str, filename: str, filedata: bytes):
        log.info("rpc::upload_file(k:{0}, fn:{1})", kernel_id, filename)
        kernel = await self._agent.get_kernel(KernelId(UUID(kernel_id)))
        await kernel.kernel().accept_file(filename, filedata)

    @collect_error
    async def download_file(self, kernel_id: str, filepath: str):
        log.info("rpc::download_file(k:{0}, fn:{1})", kernel_id, filepath)
        kernel = await self._agent.get_kernel(KernelId(UUID(kernel_id)))
        return await kernel.kernel().download_file(filepath)

    @collect_error
    async def download_single(self, kernel_id: str, filepath: str):
        log.info("rpc::download_single(k:{0}, fn:{1})", kernel_id, filepath)
        kernel = await self._agent.get_kernel(KernelId(UUID(kernel_id)))
        return await kernel.kernel().download_single(filepath)

    @collect_error
    async def list_files(self, kernel_id: str, path: str):
        log.info("rpc::list_files(k:{0}, fn:{1})", kernel_id, path)
        kernel = await self._agent.get_kernel(KernelId(UUID(kernel_id)))
        return await kernel.kernel().list_files(path)

    @collect_error
    async def shutdown_agent(self, terminate_kernels: bool):
        # TODO: implement
        log.info("rpc::shutdown_agent()")
        pass

    @collect_error
    async def create_local_network(self, network_name: str) -> None:
        log.debug("rpc::create_local_network(name:{})", network_name)
        return await self._agent.backend.create_local_network(network_name)

    @collect_error
    async def destroy_local_network(self, network_name: str) -> None:
        log.debug("rpc::destroy_local_network(name:{})", network_name)
        return await self._agent.backend.destroy_local_network(network_name)

    @collect_error
    async def reset_agent(self):
        log.debug("rpc::reset()")
        kernel_ids = tuple(self._agent.kernel_registry.keys())
        tasks = []
        for kernel_id in kernel_ids:
            try:
                task = asyncio.ensure_future(self._agent.destroy_kernel(kernel_id, "agent-reset"))
                tasks.append(task)
            except Exception:
                await self.error_monitor.capture_exception()
                log.exception("reset: destroying {0}", kernel_id)
        await asyncio.gather(*tasks)

    @collect_error
    async def assign_port(self):
        log.debug("rpc::assign_port()")
        return self._agent.port_pool.pop()

    @collect_error
    async def release_port(self, port_no: int):
        log.debug("rpc::release_port(port_no:{})", port_no)
        self._agent.port_pool.add(port_no)

    @collect_error
    async def scan_gpu_alloc_map(self) -> Mapping[str, Any]:
        log.debug("rpc::scan_gpu_alloc_map()")
        scratch_root = self._agent.local_config["container"]["scratch-root"]
        kernels = await self._agent.all_kernels()
        result = await scan_gpu_alloc_map(list(kernels.keys()), scratch_root)
        return {k: str(v) for k, v in result.items()}

class AgentRPCDebugServer:
    _agent: Agent

    def __init__(self, agent: Agent) -> None:
        self._agent = agent

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
            kernels = await self._agent.all_kernels()
            computers = await self._agent.all_computers()
            snapshot = {
                "registry": {
                    str(kern_id): _ensure_serializable(kern.__getstate__())
                    for kern_id, kern in kernels.items()
                },
                "allocs": {
                    str(computer): _ensure_serializable(
                        dict(computer_ctx.alloc_map.allocations)
                    )
                    for computer, computer_ctx in computers.items()
                },
            }
            writer.write(pretty_json(snapshot))
            await writer.drain()
            writer.close()
            await writer.wait_closed()
        except Exception:
            log.exception("status_snapshot_request_handler():")
            raise

@dataclass
class AgentRPCServerArgs:
    etcd: AsyncEtcd
    rpc_addr: HostPortPair
    debug_rpc: bool
    watcher_port: Optional[str]
    debug_socket_path: Path
    stats_monitor: AgentStatsPluginContext
    error_monitor: AgentErrorPluginContext
    authenticator: Optional[Authenticator] = None

class AgentRPCServer:
    _rpc_server: Peer
    _rpc_addr: HostPortPair
    _etcd: AsyncEtcd
    _tasks: list[asyncio.Task]
    _watcher_port: Optional[str]
    _debug_socket_path: Path
    _stats_monitor: AgentStatsPluginContext
    _error_monitor: AgentErrorPluginContext

    def __init__(self, args: AgentRPCServerArgs) -> None:
        self._rpc_server = Peer(
            bind=ZeroMQAddress(f"tcp://{args.rpc_addr}"),
            transport=ZeroMQRPCTransport,
            authenticator=args.authenticator.auth_handler if args.authenticator else None,
            scheduler=ExitOrderedAsyncScheduler(),
            serializer=msgpack.packb,
            deserializer=msgpack.unpackb,
            debug_rpc=args.debug_rpc,
        )
        self._rpc_addr = args.rpc_addr
        self._etcd = args.etcd
        self._tasks = []
        self._watcher_port = args.watcher_port
        self._debug_socket_path = args.debug_socket_path
        self._stats_monitor = args.stats_monitor
        self._error_monitor = args.error_monitor
    
    async def register_handler(self, handler: AgentRPCHandler) -> None:
        ...
    
    async def register_debug_handler(self, handler: AgentRPCDebugServer) -> None:
        server = await asyncio.start_unix_server(
            handler.status_snapshot_request_handler, self._debug_socket_path.as_posix()
        )

        async def _debug_server_task():
            try:
                async with server:
                    await server.serve_forever()
            except Exception:
                log.exception("_debug_server_task():")
                raise

        debug_server_task = asyncio.create_task(_debug_server_task())
        self._tasks.append(debug_server_task)

    async def _detect_manager(self):
        log.info("detecting the manager...")
        manager_instances = await self._etcd.get_prefix("nodes/manager")
        if not manager_instances:
            log.warning("watching etcd to wait for the manager being available")
            async with aclosing(self._etcd.watch_prefix("nodes/manager")) as agen:
                async for ev in agen:
                    match ev:
                        case QueueSentinel.CLOSED | QueueSentinel.TIMEOUT:
                            break
                        case _:
                            if ev.event == WatchEventType.PUT and ev.value == "up":
                                break
        log.info("detected at least one manager running")
    
    async def start(self, skip_detect_manager: bool) -> None:
        # Start serving requests.
        await self._update_status("starting")

        if not skip_detect_manager:
            await self._detect_manager()

        await self._stats_monitor.init()
        await self._error_monitor.init()
        await self._run()
    
    async def _run(self) -> None:
        await self._etcd.put("ip", self._rpc_addr.host, scope=ConfigScopes.NODE)
        if self._watcher_port is not None:
            await self._etcd.put("watcher_port", self._watcher_port, scope=ConfigScopes.NODE)

        await self._update_status("running")

    async def __aenter__(self) -> None:
        await self._rpc_server.__aenter__()

    def mark_stop_signal(self, stop_signal: signal.Signals) -> None:
        self._stop_signal = stop_signal

    async def __aexit__(self, *exc_info) -> None:
        # Stop receiving further requests.
        await self._rpc_server.__aexit__(*exc_info)
        for task in self._tasks:
            task.cancel()
        await asyncio.sleep(0)
        for task in self._tasks:
            if not task.done():
                await task
        await self._stats_monitor.cleanup()
        await self._stats_monitor.cleanup()

    @collect_error
    async def _update_status(self, status: str) -> None:
        await self._etcd.put("", status, scope=ConfigScopes.NODE)


@aiotools.server_context
async def server_main_logwrapper(
    loop: asyncio.AbstractEventLoop,
    pidx: int,
    _args: Tuple[Any, ...],
) -> AsyncGenerator[None, signal.Signals]:
    setproctitle(f"backend.ai: agent worker-{pidx}")
    log_endpoint = _args[1]
    logger = Logger(
        _args[0]["logging"],
        is_master=False,
        log_endpoint=log_endpoint,
        msgpack_options={
            "pack_opts": msgpack.DEFAULT_PACK_OPTS,
            "unpack_opts": msgpack.DEFAULT_UNPACK_OPTS,
        },
    )
    with logger:
        async with server_main(loop, pidx, _args):
            yield


def build_root_server() -> web.Application:
    metric_registry = CommonMetricRegistry.instance()
    app = web.Application(
        middlewares=[
            build_api_metric_middleware(metric_registry.api),
        ],
    )
    cors = aiohttp_cors.setup(
        app,
        defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=False, expose_headers="*", allow_headers="*"
            ),
        },
    )
    cors.add(
        app.router.add_route("GET", r"/metrics", build_prometheus_metrics_handler(metric_registry))
    )
    return app


async def load_authenticator(
    local_config: Mapping[str, Any],
) -> Optional[Authenticator]:
    if local_config["agent"]["rpc-auth-agent-keypair"] is None:
        return None
    manager_pkey, _ = load_certificate(
        local_config["agent"]["rpc-auth-manager-public-key"]
    )
    rpc_auth_manager_public_key = PublicKey(manager_pkey)
    agent_pkey, agent_skey = load_certificate(
        local_config["agent"]["rpc-auth-agent-keypair"]
    )
    assert agent_skey is not None
    rpc_auth_agent_public_key = PublicKey(agent_pkey)
    rpc_auth_agent_secret_key = SecretKey(agent_skey)
    log.info(
        "RPC encryption and authentication is enabled. "
        "(agent_public_key = '{}', manager_public_key='{}')",
        rpc_auth_agent_public_key.decode("ascii"),
        rpc_auth_manager_public_key.decode("ascii"),
    )
    auth_handler = AgentAuthHandler(
        "local",
        rpc_auth_manager_public_key,
        rpc_auth_agent_public_key,
        rpc_auth_agent_secret_key,
    )
    return Authenticator(
        rpc_auth_manager_public_key=rpc_auth_manager_public_key,
        rpc_auth_agent_public_key=rpc_auth_agent_public_key,
        rpc_auth_agent_secret_key=rpc_auth_agent_secret_key,
        auth_handler=auth_handler,
    )

@dataclass
class RedisConnections:
    stream_redis: RedisConnectionInfo
    stat_redis: RedisConnectionInfo


def _make_redis_connections(
    local_config: Mapping[str, Any],
) -> RedisConnections:
    ...

def _make_message_queue(
    self, stream_redis_target: RedisTarget, stream_redis: RedisConnectionInfo
) -> AbstractMessageQueue:
    """
    Returns the message queue object.
    """
    node_id = self.local_config["agent"]["id"]
    if self.local_config["agent"].get("use-experimental-redis-event-dispatcher"):
        return HiRedisQueue(
            stream_redis_target,
            HiRedisMQArgs(
                stream_key="events",
                group_name=EVENT_DISPATCHER_CONSUMER_GROUP,
                node_id=node_id,
                db=REDIS_STREAM_DB,
            ),
        )
    return RedisQueue(
        stream_redis,
        RedisMQArgs(
            stream_key="events",
            group_name=EVENT_DISPATCHER_CONSUMER_GROUP,
            node_id=node_id,
        ),
    )

@aiotools.server_context
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
    Profiler(
        pyroscope_args=PyroscopeArgs(
            enabled=local_config["pyroscope"]["enabled"],
            application_name=local_config["pyroscope"]["app-name"],
            server_address=local_config["pyroscope"]["server-addr"],
            sample_rate=local_config["pyroscope"]["sample-rate"],
        )
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
    await read_agent_config(etcd, local_config)
    await read_agent_config_container(etcd, local_config)
    authenticator = await load_authenticator(local_config)
    agent_backend = ""
    agent = Agent(AgentArgs(
        id=local_config["agent"]["id"],
        local_config=local_config,
        etcd=etcd,
        backend=agent_backend,
    ))
    agent_handler = AgentRPCHandler(
        etcd,
        agent,
        local_config,
    )
    rpc_server = AgentRPCServer(
        AgentRPCServerArgs(
            etcd=etcd,
            rpc_addr=rpc_addr,
            debug_rpc=local_config["agent"]["debug-rpc"],
            watcher_port=local_config["agent"]["watcher-port"],
            debug_socket_path=local_config["agent"]["debug-socket-path"],
            stats_monitor=AgentStatsPluginContext(etcd, local_config),
            error_monitor=AgentErrorPluginContext(etcd, local_config),
            authenticator=authenticator,
        )
    )
    await rpc_server.register_handler(agent_handler)
    await rpc_server.register_debug_handler(AgentRPCDebugServer(agent))

    monitor.console_locals["agent"] = agent_handler
    app = build_root_server()
    runner = web.AppRunner(app)
    await runner.setup()
    service_addr = local_config["agent"]["service-addr"]
    ssl_ctx = None
    if local_config["agent"]["ssl-enabled"]:
        ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_ctx.load_cert_chain(
            str(local_config["agent"]["ssl-cert"]),
            str(local_config["agent"]["ssl-privkey"]),
        )
    site = web.TCPSite(
        runner,
        str(service_addr.host),
        service_addr.port,
        backlog=1024,
        reuse_port=True,
        ssl_context=ssl_ctx,
    )
    await site.start()
    log.info("started serving HTTP at {}", service_addr)

    # Run!
    try:
        async with rpc_server:
            stop_signal = yield
        await agent.shutdown(stop_signal)
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
    help="The config file path. (default: ./agent.toml and /etc/backend.ai/agent.toml)",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Set the logging level to DEBUG",
)
@click.option(
    "--log-level",
    type=click.Choice([*LogLevel], case_sensitive=False),
    default=LogLevel.NOTSET,
    help="Set the logging verbosity level",
)
@click.pass_context
def main(
    cli_ctx: click.Context,
    config_path: Path,
    log_level: LogLevel,
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
        log_level = LogLevel.DEBUG
    config.override_key(raw_cfg, ("debug", "enabled"), log_level == LogLevel.DEBUG)
    if log_level != LogLevel.NOTSET:
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
    if isinstance(rpc_host, (IPv4Address, IPv6Address)) and (
        rpc_host.is_unspecified or rpc_host.is_link_local
    ):
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
            logger = Logger(
                cfg["logging"],
                is_master=True,
                log_endpoint=log_endpoint,
                msgpack_options={
                    "pack_opts": msgpack.DEFAULT_PACK_OPTS,
                    "unpack_opts": msgpack.DEFAULT_UNPACK_OPTS,
                },
            )
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
