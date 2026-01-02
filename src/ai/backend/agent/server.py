from __future__ import annotations

import asyncio
import functools
import logging
import os
import shutil
import signal
import ssl
import sys
import time
import traceback
from collections import OrderedDict, defaultdict
from collections.abc import AsyncIterator
from contextlib import AsyncExitStack, asynccontextmanager
from ipaddress import ip_network
from pathlib import Path
from pprint import pformat, pprint
from typing import (
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
from pydantic import ValidationError
from setproctitle import setproctitle
from zmq.auth.certs import load_certificate

from ai.backend.agent.agent import AbstractAgent
from ai.backend.agent.errors import AgentInitializationError, InvalidAgentConfigError
from ai.backend.agent.health.docker import DockerHealthChecker
from ai.backend.agent.metrics.metric import RPCMetricObserver
from ai.backend.agent.monitor import AgentErrorPluginContext, AgentStatsPluginContext
from ai.backend.agent.resources import scan_gpu_alloc_map
from ai.backend.agent.runtime import AgentRuntime
from ai.backend.agent.types import AgentBackend
from ai.backend.common import config, identity, msgpack, utils
from ai.backend.common.auth import AgentAuthHandler, PublicKey, SecretKey
from ai.backend.common.bgtask.bgtask import ProgressReporter
from ai.backend.common.configs.redis import RedisConfig
from ai.backend.common.defs import RedisRole
from ai.backend.common.docker import ImageRef
from ai.backend.common.dto.agent.response import (
    AbstractAgentResp,
    CodeCompletionResp,
    DropKernelRegistryResp,
    PurgeContainersResp,
    PurgeImagesResp,
)
from ai.backend.common.dto.internal.health import HealthResponse, HealthStatus
from ai.backend.common.dto.manager.rpc_request import PurgeImagesReq
from ai.backend.common.etcd import AsyncEtcd, ConfigScopes
from ai.backend.common.events.event_types.kernel.anycast import (
    KernelTerminatedAnycastEvent,
)
from ai.backend.common.events.event_types.kernel.broadcast import (
    KernelTerminatedBroadcastEvent,
)
from ai.backend.common.events.event_types.kernel.types import KernelLifecycleEventReason
from ai.backend.common.exception import ConfigurationError
from ai.backend.common.health_checker.checkers.etcd import EtcdHealthChecker
from ai.backend.common.health_checker.checkers.valkey import ValkeyHealthChecker
from ai.backend.common.health_checker.probe import HealthProbe, HealthProbeOptions
from ai.backend.common.health_checker.types import ComponentId
from ai.backend.common.json import pretty_json
from ai.backend.common.metrics.http import (
    build_api_metric_middleware,
    build_prometheus_metrics_handler,
)
from ai.backend.common.metrics.metric import CommonMetricRegistry
from ai.backend.common.metrics.profiler import Profiler, PyroscopeArgs
from ai.backend.common.service_discovery.etcd_discovery.service_discovery import (
    ETCDServiceDiscovery,
    ETCDServiceDiscoveryArgs,
)
from ai.backend.common.service_discovery.redis_discovery.service_discovery import (
    RedisServiceDiscovery,
    RedisServiceDiscoveryArgs,
)
from ai.backend.common.service_discovery.service_discovery import (
    ServiceDiscovery,
    ServiceDiscoveryLoop,
    ServiceEndpoint,
    ServiceMetadata,
)
from ai.backend.common.types import (
    AgentId,
    ClusterInfo,
    CommitStatus,
    ContainerId,
    ContainerKernelId,
    HardwareMetadata,
    HostPortPair,
    ImageConfig,
    ImageRegistry,
    KernelCreationConfig,
    KernelId,
    QueueSentinel,
    ServiceDiscoveryType,
    SessionId,
    aobject,
)
from ai.backend.common.utils import current_loop
from ai.backend.logging import BraceStyleAdapter, Logger, LogLevel
from ai.backend.logging.otel import OpenTelemetrySpec

from . import __version__ as VERSION
from .config.unified import (
    AgentConfigValidationContext,
    AgentUnifiedConfig,
    APIConfig,
    ContainerLogsConfig,
    EventLoopType,
    KernelLifecyclesConfig,
)
from .exception import ResourceError
from .types import (
    KernelLifecycleStatus,
    KernelOwnershipData,
    LifecycleEvent,
    get_agent_discovery,
)
from .utils import get_subnet_ip

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


def collect_error(meth: Callable) -> Callable:
    @functools.wraps(meth)
    async def _inner(self: AgentRPCServer, *args, **kwargs):
        try:
            return await meth(self, *args, **kwargs)
        except Exception:
            agent_id = kwargs.get("agent_id", None)
            agent = self.runtime.get_agent(agent_id)
            await agent.produce_error_event()
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
    ) -> Callable[[AgentRPCServer, RPCMessage], Coroutine[None, None, Any]]:
        @functools.wraps(meth)
        @_collect_metrics(self._metric_observer, meth.__name__)
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


class RPCFunctionRegistryV2:
    functions: Set[str]
    _metric_observer: RPCMetricObserver

    def __init__(self) -> None:
        self.functions = set()
        self._metric_observer = RPCMetricObserver.instance()

    def __call__(
        self,
        meth: Callable[..., Coroutine[None, None, AbstractAgentResp]],
    ) -> Callable[[AgentRPCServer, RPCMessage], Coroutine[None, None, Any]]:
        @functools.wraps(meth)
        @_collect_metrics(self._metric_observer, meth.__name__)
        async def _inner(self_: AgentRPCServer, request: RPCMessage) -> Any:
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


def _collect_metrics(observer: RPCMetricObserver, method_name: str) -> Callable:
    def decorator(meth: Callable) -> Callable[[AgentRPCServer, RPCMessage], Any]:
        @functools.wraps(meth)
        async def _inner(self: AgentRPCServer, *args, **kwargs) -> Any:
            start_time = time.perf_counter()
            try:
                res = await meth(self, *args, **kwargs)
                duration = time.perf_counter() - start_time
                observer.observe_rpc_request_success(
                    method=method_name,
                    duration=duration,
                )
                return res
            except BaseException as e:
                duration = time.perf_counter() - start_time
                observer.observe_rpc_request_failure(
                    method=method_name,
                    duration=duration,
                    exception=e,
                )
                raise

        return _inner

    return decorator


class AgentRPCServer(aobject):
    rpc_function: ClassVar[RPCFunctionRegistry] = RPCFunctionRegistry()
    rpc_function_v2: ClassVar[RPCFunctionRegistryV2] = RPCFunctionRegistryV2()

    rpc_auth_manager_public_key: Optional[PublicKey]
    rpc_auth_agent_public_key: Optional[PublicKey]
    rpc_auth_agent_secret_key: Optional[SecretKey]

    loop: asyncio.AbstractEventLoop
    etcd: AsyncEtcd
    runtime: AgentRuntime
    rpc_server: Peer
    rpc_addr: str
    agent_addr: str

    debug_server_task: asyncio.Task
    stats_monitor: AgentStatsPluginContext
    error_monitor: AgentErrorPluginContext
    health_probe: HealthProbe

    def __init__(
        self,
        etcd: AsyncEtcd,
        local_config: AgentUnifiedConfig,
        *,
        skip_detect_manager: bool = False,
    ) -> None:
        self.loop = current_loop()
        self.etcd = etcd
        self.local_config = local_config
        self.skip_detect_manager = skip_detect_manager

    async def __ainit__(self) -> None:
        if not self.skip_detect_manager:
            await self.detect_manager()

        await self.read_agent_config()
        await self.read_agent_config_container()

        self.stats_monitor = AgentStatsPluginContext(
            self.etcd, self.local_config.model_dump(by_alias=True)
        )
        self.error_monitor = AgentErrorPluginContext(
            self.etcd, self.local_config.model_dump(by_alias=True)
        )
        await self.stats_monitor.init()
        await self.error_monitor.init()

        if self.local_config.agent_common.rpc_auth_agent_keypair is not None:
            manager_pkey, _ = load_certificate(
                str(self.local_config.agent_common.rpc_auth_manager_public_key)
            )
            self.rpc_auth_manager_public_key = PublicKey(manager_pkey)
            agent_pkey, agent_skey = load_certificate(
                str(self.local_config.agent_common.rpc_auth_agent_keypair)
            )
            if agent_skey is None:
                raise AgentInitializationError(
                    "Agent secret key is not available from the keypair file."
                )
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

        self.runtime = await AgentRuntime.create_runtime(
            self.local_config,
            self.etcd,
            self.stats_monitor,
            self.error_monitor,
            self.rpc_auth_agent_public_key,
        )

        # Start serving requests.
        async with asyncio.TaskGroup() as tg:
            for agent in self.runtime.get_agents():
                tg.create_task(self.update_status("starting", agent.id))

        rpc_addr = self.local_config.agent_common.rpc_listen_addr
        self.rpc_server = Peer(
            bind=ZeroMQAddress(f"tcp://{rpc_addr.address}"),
            transport=ZeroMQRPCTransport,
            authenticator=auth_handler,
            scheduler=ExitOrderedAsyncScheduler(),
            serializer=msgpack.packb,
            deserializer=msgpack.unpackb,
            debug_rpc=self.local_config.debug.enabled,
        )
        for func_name in self.rpc_function.functions:
            self.rpc_server.handle_function(func_name, getattr(self, func_name))

        for func_name in self.rpc_function_v2.functions:
            self.rpc_server.handle_function(func_name, getattr(self, func_name))

        log.info("started handling RPC requests at {}", rpc_addr)

        debug_socket_path = (
            self.local_config.agent_common.ipc_base_path / "agent-registry-snapshot.sock"
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

        async with asyncio.TaskGroup() as tg:
            for agent in self.runtime.get_agents():
                etcd = self.runtime.get_etcd(agent.id)
                tg.create_task(etcd.put("ip", rpc_addr.host, scope=ConfigScopes.NODE))

                watcher_port = utils.nmget(
                    agent.local_config.model_dump(), "watcher.service-addr.port", None
                )
                if watcher_port is not None:
                    tg.create_task(etcd.put("watcher_port", watcher_port, scope=ConfigScopes.NODE))

        async with asyncio.TaskGroup() as tg:
            for agent in self.runtime.get_agents():
                tg.create_task(self.update_status("running", agent.id))

        # Initialize health probe
        self.health_probe = HealthProbe(options=HealthProbeOptions(check_interval=60))

        # Register health checkers
        await self.health_probe.register(EtcdHealthChecker(etcd=self.etcd))

        # Get default agent for health checking
        default_agent = self.runtime.get_agent(None)

        # Register Docker health checker based on config
        if self.local_config.agent_common.backend == AgentBackend.DOCKER:
            from ai.backend.agent.docker.agent import DockerAgent

            docker_agent = cast(DockerAgent, default_agent)
            await self.health_probe.register(DockerHealthChecker(docker=docker_agent.docker))

        # Register Valkey health checker with all 4 agent valkey clients
        await self.health_probe.register(
            ValkeyHealthChecker(
                clients={
                    ComponentId("stat"): default_agent.valkey_stat_client,
                    ComponentId("stream"): default_agent.valkey_stream_client,
                    ComponentId("bgtask"): default_agent.valkey_bgtask_client,
                    ComponentId("container_log"): default_agent.valkey_container_log_client,
                }
            )
        )

        # Start periodic health checking
        await self.health_probe.start()

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
            if self.runtime.get_agents():
                snapshot = {
                    str(agent.id): {
                        "registry": {
                            str(kern_id): _ensure_serializable(kern.__getstate__())
                            for kern_id, kern in agent.kernel_registry.items()
                        },
                        "allocs": {
                            str(computer): _ensure_serializable(
                                dict(computer_ctx.alloc_map.allocations)
                            )
                            for computer, computer_ctx in agent.computers.items()
                        },
                    }
                    for agent in self.runtime.get_agents()
                }
                writer.write(pretty_json(snapshot))
            await writer.drain()
            writer.close()
            await writer.wait_closed()
        except Exception:
            log.exception("status_snapshot_request_handler():")
            raise

    async def detect_manager(self):
        log.info("detecting the manager...")
        etcd = self.etcd
        manager_instances = await etcd.get_prefix("nodes/manager")
        if not manager_instances:
            log.warning("watching etcd to wait for the manager being available")
            async with aclosing(etcd.watch_prefix("nodes/manager")) as agen:
                async for ev in agen:
                    match ev:
                        case QueueSentinel.CLOSED | QueueSentinel.TIMEOUT:
                            break
                        case _:
                            if ev.event == WatchEventType.PUT and ev.value == "up":
                                break
        log.info("detected at least one manager running")

    async def read_agent_config(self):
        # Fill up Redis configs from etcd and store as separate attributes
        self._redis_config = config.redis_config_iv.check(
            await self.etcd.get_prefix("config/redis"),
        )
        log.info("configured redis: {0}", self._redis_config)

        # Update local_config with redis settings
        # Convert HostPortPair to dict format for compatibility
        redis_config_dict = self._redis_config.copy()
        if isinstance(self._redis_config.get("addr"), object):
            addr = self._redis_config["addr"]
            if addr is not None:
                redis_config_dict["addr"] = f"{addr.host}:{addr.port}"

        redis_config = RedisConfig.model_validate(redis_config_dict)
        self.local_config.overwrite(redis=redis_config)

        # Fill up vfolder configs from etcd and store as separate attributes
        # TODO: Integrate vfolder_config into local_config
        self._vfolder_config = config.vfolder_config_iv.check(
            await self.etcd.get_prefix("volumes"),
        )
        if self._vfolder_config["mount"] is None:
            log.info(
                "assuming use of storage-proxy since vfolder mount path is not configured in etcd"
            )
        else:
            log.info("configured vfolder mount base: {0}", self._vfolder_config["mount"])
            log.info("configured vfolder fs prefix: {0}", self._vfolder_config["fsprefix"])

        # Fill up shared agent configurations from etcd.
        agent_etcd_config_raw = await self.etcd.get_prefix("config/agent")
        if agent_etcd_config_raw:
            try:
                # Parse specific etcd configs and update the unified config
                api_config = APIConfig.model_validate(agent_etcd_config_raw.get("api", {}))
                container_logs_config = ContainerLogsConfig.model_validate(
                    agent_etcd_config_raw.get("container-logs", {})
                )
                kernel_lifecycles_config = KernelLifecyclesConfig.model_validate(
                    agent_etcd_config_raw.get("kernel-lifecycles", {})
                )

                # Update local config with parsed values
                self.local_config.overwrite(
                    api=api_config,
                    container_logs=container_logs_config,
                    kernel_lifecycles=kernel_lifecycles_config,
                )
            except Exception as e:
                log.warning("etcd: agent-config error: {}", e)

    async def read_agent_config_container(self):
        # Fill up global container configurations from etcd.
        try:
            container_etcd_config_raw = await self.etcd.get_prefix("config/container")
            if container_etcd_config_raw:
                # Update config by creating a new instance with modified values
                container_updates = {}
                if "kernel-uid" in container_etcd_config_raw:
                    container_updates["kernel_uid"] = container_etcd_config_raw["kernel-uid"]
                    log.info(
                        "etcd: container-config: kernel-uid={}".format(
                            container_etcd_config_raw["kernel-uid"]
                        )
                    )
                if "kernel-gid" in container_etcd_config_raw:
                    container_updates["kernel_gid"] = container_etcd_config_raw["kernel-gid"]
                    log.info(
                        "etcd: container-config: kernel-gid={}".format(
                            container_etcd_config_raw["kernel-gid"]
                        )
                    )

                self.local_config.update(container_update=container_updates)
        except Exception as e:
            log.warning("etcd: container-config error: {}".format(e))

    async def __aenter__(self) -> None:
        await self.rpc_server.__aenter__()

    def mark_stop_signal(self, stop_signal: signal.Signals) -> None:
        self.runtime.mark_stop_signal(stop_signal)

    async def __aexit__(self, *exc_info) -> None:
        # Stop receiving further requests.
        await self.rpc_server.__aexit__(*exc_info)
        self.debug_server_task.cancel()
        await asyncio.sleep(0)
        if not self.debug_server_task.done():
            await self.debug_server_task
        await self.runtime.__aexit__(*exc_info)
        await self.stats_monitor.cleanup()
        await self.error_monitor.cleanup()
        await self.health_probe.stop()

    @collect_error
    async def update_status(self, status: str, agent_id: AgentId):
        await self.runtime.update_status(status, agent_id)

    @rpc_function
    @collect_error
    async def update_scaling_group(self, scaling_group: str, agent_id: AgentId | None = None):
        cfg_src_path = config.find_config_file("agent")
        with open(cfg_src_path, "r") as f:
            data = tomlkit.load(f)
        agent = self.runtime.get_agent(agent_id)
        if "agents" in data:
            self._update_scaling_group_override(data, scaling_group, agent)
        else:
            self._update_scaling_group_default(data, scaling_group)
        shutil.copy(cfg_src_path, f"{cfg_src_path}.bak")
        with open(cfg_src_path, "w") as f:
            tomlkit.dump(data, f)

        agent.update_scaling_group(scaling_group)
        log.info("rpc::update_scaling_group()")

    def _update_scaling_group_default(
        self,
        config_data: tomlkit.TOMLDocument,
        scaling_group: str,
    ) -> None:
        config_data["agent"]["scaling-group"] = scaling_group  # type: ignore[index]

    def _update_scaling_group_override(
        self,
        config_data: tomlkit.TOMLDocument,
        scaling_group: str,
        agent: AbstractAgent,
    ) -> None:
        if "agents" not in config_data:
            raise InvalidAgentConfigError("Missing 'agents' section in configuration data.")

        for agent_config in config_data["agents"]:  # type: ignore[union-attr]
            if agent_config["agent"]["id"] == str(agent.id):  # type: ignore[index]
                agent_config["agent"]["scaling-group"] = scaling_group  # type: ignore[index]
                break

    @rpc_function
    @collect_error
    async def ping(self, msg: str) -> str:
        log.debug("rpc::ping()")
        return msg

    @rpc_function
    @collect_error
    async def health(self) -> Mapping[str, Any]:
        """
        Health check that returns agent health status with dependency connectivity.

        Returns HealthResponse with connectivity status for etcd and docker.
        """
        log.debug("rpc::health()")
        connectivity = await self.health_probe.get_connectivity_status()
        response = HealthResponse(
            status=HealthStatus.OK if connectivity.overall_healthy else HealthStatus.DEGRADED,
            version=VERSION,
            component="agent",
            connectivity=connectivity,
        )
        return response.model_dump(mode="json")

    @rpc_function
    @collect_error
    async def gather_hwinfo(
        self,
        agent_id: AgentId | None = None,
    ) -> Mapping[str, HardwareMetadata]:
        log.debug("rpc::gather_hwinfo()")
        agent = self.runtime.get_agent(agent_id)
        return await agent.gather_hwinfo()

    @rpc_function
    @collect_error
    async def ping_kernel(
        self,
        kernel_id: str,
        agent_id: AgentId | None = None,
    ) -> dict[str, float] | None:
        log.debug("rpc::ping_kernel(k:{})", kernel_id)
        agent = self.runtime.get_agent(agent_id)
        return await agent.ping_kernel(KernelId(UUID(kernel_id)))

    @rpc_function
    @collect_error
    async def check_pulling(
        self,
        image_name: str,
        agent_id: AgentId | None = None,
    ) -> bool:
        """Check if an image is being pulled."""
        log.debug("rpc::check_pulling(image:{})", image_name)
        agent = self.runtime.get_agent(agent_id)
        return image_name in agent._active_pulls

    @rpc_function
    @collect_error
    async def check_creating(
        self,
        kernel_id: str,
        agent_id: AgentId | None = None,
    ) -> bool:
        """Check if a kernel is being created or already exists."""
        log.debug("rpc::check_creating(k:{})", kernel_id)
        kid = KernelId(UUID(kernel_id))
        agent = self.runtime.get_agent(agent_id)
        # Check if kernel is being created OR already exists in registry
        return kid in agent._active_creates or kid in agent.kernel_registry

    @rpc_function
    @collect_error
    async def check_running(
        self,
        kernel_id: str,
        agent_id: AgentId | None = None,
    ) -> bool:
        """Check if a kernel is running."""
        log.debug("rpc::check_running(k:{})", kernel_id)
        kid = KernelId(UUID(kernel_id))

        # Safely get kernel from registry
        agent = self.runtime.get_agent(agent_id)
        kernel_obj = agent.kernel_registry.get(kid)

        # Check if kernel exists and is running
        if kernel_obj is None:
            return False

        return kernel_obj.state == KernelLifecycleStatus.RUNNING

    @rpc_function
    @collect_error
    async def sync_kernel_registry(
        self,
        raw_kernel_session_ids: Iterable[tuple[str, str]],
        agent_id: AgentId | None = None,
    ) -> None:
        agent = self.runtime.get_agent(agent_id)

        kernel_session_ids = [
            (KernelId(UUID(raw_kid)), SessionId(UUID(raw_sid)))
            for raw_kid, raw_sid in raw_kernel_session_ids
        ]
        for kid, sid in kernel_session_ids:
            if kid not in agent.kernel_registry:
                # produce KernelTerminatedEvent
                await agent.anycast_and_broadcast_event(
                    KernelTerminatedAnycastEvent(
                        kid,
                        sid,
                        reason=KernelLifecycleEventReason.ALREADY_TERMINATED,
                    ),
                    KernelTerminatedBroadcastEvent(
                        kid,
                        sid,
                        reason=KernelLifecycleEventReason.ALREADY_TERMINATED,
                    ),
                )

        kernel_ids = {kern_id for kern_id, sess_id in kernel_session_ids}
        for kid, kernel in agent.kernel_registry.items():
            if kid not in kernel_ids:
                # destroy kernel
                await agent.inject_container_lifecycle_event(
                    kid,
                    kernel.session_id,
                    LifecycleEvent.DESTROY,
                    KernelLifecycleEventReason.NOT_FOUND_IN_MANAGER,
                    suppress_events=True,
                )

    @rpc_function
    @collect_error
    async def check_and_pull(
        self,
        image_configs: Mapping[str, ImageConfig],
        agent_id: AgentId | None = None,
    ) -> dict[str, str]:
        """
        Check whether the agent has images and pull if needed.
        Delegates to agent's check_and_pull method which handles tracking.
        """
        log.debug("rpc::check_and_pull(images:{})", list(image_configs.keys()))
        agent = self.runtime.get_agent(agent_id)
        return await agent.check_and_pull(image_configs)

    @rpc_function
    @collect_error
    async def create_kernels(
        self,
        raw_session_id: str,
        raw_kernel_ids: Sequence[str],
        raw_configs: Sequence[dict],
        raw_cluster_info: dict,
        kernel_image_refs: dict[KernelId, ImageRef],
        agent_id: AgentId | None = None,
    ):
        cluster_info = cast(ClusterInfo, raw_cluster_info)
        session_id = SessionId(UUID(raw_session_id))
        coros = []
        agent = self.runtime.get_agent(agent_id)
        throttle_sema = asyncio.Semaphore(agent.local_config.agent.kernel_creation_concurrency)
        for raw_kernel_id, raw_config in zip(raw_kernel_ids, raw_configs):
            log.info(
                "rpc::create_kernel(k:{0}, img:{1})",
                raw_kernel_id,
                raw_config["image"]["canonical"],
            )
            kernel_id = KernelId(UUID(raw_kernel_id))
            kernel_config = cast(KernelCreationConfig, raw_config)
            coros.append(
                agent.create_kernel(
                    KernelOwnershipData(
                        kernel_id,
                        session_id,
                        agent.id,
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

    @rpc_function
    @collect_error
    async def destroy_kernel(
        self,
        kernel_id: str,
        session_id: str,
        reason: Optional[KernelLifecycleEventReason] = None,
        suppress_events: bool = False,
        agent_id: AgentId | None = None,
    ):
        loop = asyncio.get_running_loop()
        done = loop.create_future()
        log.info("rpc::destroy_kernel(k:{0})", kernel_id)
        agent = self.runtime.get_agent(agent_id)
        await agent.inject_container_lifecycle_event(
            KernelId(UUID(kernel_id)),
            SessionId(UUID(session_id)),
            LifecycleEvent.DESTROY,
            reason or KernelLifecycleEventReason.USER_REQUESTED,
            done_future=done,
            suppress_events=suppress_events,
        )
        return await done

    @rpc_function_v2
    @collect_error
    async def purge_containers(
        self,
        container_kernel_ids: list[tuple[str, str]],
        agent_id: AgentId | None = None,
    ) -> PurgeContainersResp:
        str_kernel_ids = [str(kid) for _, kid in container_kernel_ids]
        log.info("rpc::purge_containers(kernel_ids:{0})", str_kernel_ids)
        kernel_container_pairs = [
            ContainerKernelId(
                ContainerId(cid),
                KernelId(UUID(kid)),
            )
            for cid, kid in container_kernel_ids
        ]
        agent = self.runtime.get_agent(agent_id)
        asyncio.create_task(agent.purge_containers(kernel_container_pairs))
        return PurgeContainersResp()

    @rpc_function_v2
    @collect_error
    async def drop_kernel_registry(
        self,
        kernel_ids: list[UUID],
        agent_id: AgentId | None = None,
    ) -> DropKernelRegistryResp:
        str_kernel_ids = [str(kid) for kid in kernel_ids]
        log.info("rpc::drop_kernel_registry(kernel_ids:{0})", str_kernel_ids)
        kernel_ids_to_purge = [KernelId(kid) for kid in kernel_ids]
        agent = self.runtime.get_agent(agent_id)
        asyncio.create_task(agent.clean_kernel_objects(kernel_ids_to_purge))
        return DropKernelRegistryResp()

    @rpc_function
    @collect_error
    async def interrupt_kernel(
        self,
        kernel_id: str,
        agent_id: AgentId | None = None,
    ):
        log.info("rpc::interrupt_kernel(k:{0})", kernel_id)
        agent = self.runtime.get_agent(agent_id)
        await agent.interrupt_kernel(KernelId(UUID(kernel_id)))

    @rpc_function_v2
    @collect_error
    async def get_completions(
        self,
        kernel_id: str,
        text: str,
        opts: dict,
        agent_id: AgentId | None = None,
    ) -> CodeCompletionResp:
        log.debug("rpc::get_completions(k:{0}, ...)", kernel_id)
        agent = self.runtime.get_agent(agent_id)
        return await agent.get_completions(KernelId(UUID(kernel_id)), text, opts)

    @rpc_function
    @collect_error
    async def get_logs(
        self,
        kernel_id: str,
        agent_id: AgentId | None = None,
    ):
        log.info("rpc::get_logs(k:{0})", kernel_id)
        agent = self.runtime.get_agent(agent_id)
        return await agent.get_logs(KernelId(UUID(kernel_id)))

    @rpc_function
    @collect_error
    async def restart_kernel(
        self,
        session_id: str,
        kernel_id: str,
        kernel_image: ImageRef,
        updated_config: dict,
        agent_id: AgentId | None = None,
    ) -> dict[str, Any]:
        log.info("rpc::restart_kernel(s:{0}, k:{1})", session_id, kernel_id)
        agent = self.runtime.get_agent(agent_id)
        return await agent.restart_kernel(
            KernelOwnershipData(
                KernelId(UUID(kernel_id)),
                SessionId(UUID(session_id)),
                agent.id,
            ),
            kernel_image,
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
        agent_id: AgentId | None = None,
    ) -> dict[str, Any]:
        if mode != "continue":
            log.info(
                "rpc::execute(k:{0}, run-id:{1}, mode:{2}, code:{3!r})",
                kernel_id,
                run_id,
                mode,
                code[:20] + "..." if len(code) > 20 else code,
            )
        agent = self.runtime.get_agent(agent_id)
        result = await agent.execute(
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
    async def trigger_batch_execution(
        self,
        session_id: str,
        kernel_id: str,
        code: str,
        timeout: Optional[float],
        agent_id: AgentId | None = None,
    ) -> None:
        log.info(
            "rpc::trigger_batch_execution(k:{0}, s:{1}, code:{2}, timeout:{3})",
            kernel_id,
            session_id,
            code,
            timeout,
        )
        agent = self.runtime.get_agent(agent_id)
        await agent.create_batch_execution_task(
            SessionId(UUID(session_id)), KernelId(UUID(kernel_id)), code, timeout
        )

    @rpc_function
    @collect_error
    async def start_service(
        self,
        kernel_id: str,
        service: str,
        opts: dict[str, Any],
        agent_id: AgentId | None = None,
    ) -> dict[str, Any]:
        log.info("rpc::start_service(k:{0}, app:{1})", kernel_id, service)
        agent = self.runtime.get_agent(agent_id)
        return await agent.start_service(KernelId(UUID(kernel_id)), service, opts)

    @rpc_function
    @collect_error
    async def get_commit_status(
        self,
        kernel_id: str,
        subdir: str,
        agent_id: AgentId | None = None,
    ) -> dict[str, Any]:
        # Only this function logs debug since web sends request at short intervals
        log.debug("rpc::get_commit_status(k:{})", kernel_id)
        agent = self.runtime.get_agent(agent_id)
        status: CommitStatus = await agent.get_commit_status(
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
        agent_id: AgentId | None = None,
    ) -> dict[str, Any]:
        log.info("rpc::commit(k:{})", kernel_id)
        agent = self.runtime.get_agent(agent_id)
        bgtask_mgr = agent.background_task_manager

        async def _commit(reporter: ProgressReporter) -> None:
            await agent.commit(
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
        image_ref: ImageRef,
        registry_conf: ImageRegistry,
        agent_id: AgentId | None = None,
    ) -> dict[str, Any]:
        log.info("rpc::push_image(c:{})", image_ref.canonical)
        agent = self.runtime.get_agent(agent_id)
        bgtask_mgr = agent.background_task_manager

        image_push_timeout = cast(Optional[float], self.local_config.api.push_timeout)

        async def _push_image(reporter: ProgressReporter) -> None:
            await agent.push_image(
                image_ref,
                registry_conf,
                timeout=image_push_timeout,
            )

        task_id = await bgtask_mgr.start(_push_image)
        return {
            "bgtask_id": str(task_id),
            "canonical": image_ref.canonical,
        }

    @rpc_function_v2
    @collect_error
    async def purge_images(
        self,
        image_canonicals: list[str],
        force: bool,
        noprune: bool,
        agent_id: AgentId | None = None,
    ) -> PurgeImagesResp:
        log.info(
            "rpc::purge_images(images:{0}, force:{1}, noprune:{2})",
            image_canonicals,
            force,
            noprune,
        )
        agent = self.runtime.get_agent(agent_id)
        return await agent.purge_images(
            PurgeImagesReq(images=image_canonicals, force=force, noprune=noprune)
        )

    @rpc_function
    @collect_error
    async def get_local_config(self, agent_id: AgentId | None = None) -> Mapping[str, Any]:
        report_path: Path | None = self.local_config.agent_common.abuse_report_path
        return {
            "agent": {
                "abuse-report-path": str(report_path) if report_path is not None else "",
            },
            "watcher": getattr(self, "_watcher_config", {}),
        }

    @rpc_function
    @collect_error
    async def shutdown_service(
        self,
        kernel_id: str,
        service: str,
        agent_id: AgentId | None = None,
    ):
        log.info("rpc::shutdown_service(k:{0}, app:{1})", kernel_id, service)
        agent = self.runtime.get_agent(agent_id)
        return await agent.shutdown_service(KernelId(UUID(kernel_id)), service)

    @rpc_function
    @collect_error
    async def upload_file(
        self,
        kernel_id: str,
        filename: str,
        filedata: bytes,
        agent_id: AgentId | None = None,
    ):
        log.info("rpc::upload_file(k:{0}, fn:{1})", kernel_id, filename)
        agent = self.runtime.get_agent(agent_id)
        await agent.accept_file(KernelId(UUID(kernel_id)), filename, filedata)

    @rpc_function
    @collect_error
    async def download_file(
        self,
        kernel_id: str,
        filepath: str,
        agent_id: AgentId | None = None,
    ):
        log.info("rpc::download_file(k:{0}, fn:{1})", kernel_id, filepath)
        agent = self.runtime.get_agent(agent_id)
        return await agent.download_file(KernelId(UUID(kernel_id)), filepath)

    @rpc_function
    @collect_error
    async def download_single(
        self,
        kernel_id: str,
        filepath: str,
        agent_id: AgentId | None = None,
    ):
        log.info("rpc::download_single(k:{0}, fn:{1})", kernel_id, filepath)
        agent = self.runtime.get_agent(agent_id)
        return await agent.download_single(KernelId(UUID(kernel_id)), filepath)

    @rpc_function
    @collect_error
    async def list_files(
        self,
        kernel_id: str,
        path: str,
        agent_id: AgentId | None = None,
    ):
        log.info("rpc::list_files(k:{0}, fn:{1})", kernel_id, path)
        agent = self.runtime.get_agent(agent_id)
        return await agent.list_files(KernelId(UUID(kernel_id)), path)

    @rpc_function
    @collect_error
    async def shutdown_agent(self, terminate_kernels: bool, agent_id: AgentId | None = None):
        # TODO: implement
        log.info("rpc::shutdown_agent()")
        pass

    @rpc_function
    @collect_error
    async def create_local_network(
        self,
        network_name: str,
        agent_id: AgentId | None = None,
    ) -> None:
        log.debug("rpc::create_local_network(name:{})", network_name)
        agent = self.runtime.get_agent(agent_id)
        return await agent.create_local_network(network_name)

    @rpc_function
    @collect_error
    async def destroy_local_network(
        self,
        network_name: str,
        agent_id: AgentId | None = None,
    ) -> None:
        log.debug("rpc::destroy_local_network(name:{})", network_name)
        agent = self.runtime.get_agent(agent_id)
        return await agent.destroy_local_network(network_name)

    @rpc_function
    @collect_error
    async def reset_agent(self, agent_id: AgentId | None = None):
        log.debug("rpc::reset()")
        agent = self.runtime.get_agent(agent_id)
        kernel_ids = tuple(agent.kernel_registry.keys())
        tasks = []
        for kernel_id in kernel_ids:
            try:
                task = asyncio.ensure_future(
                    agent.destroy_kernel(kernel_id, ContainerId("agent-reset"))
                )
                tasks.append(task)
            except Exception:
                await self.error_monitor.capture_exception()
                log.exception("reset: destroying {0}", kernel_id)
        await asyncio.gather(*tasks)

    @rpc_function
    @collect_error
    async def assign_port(self, agent_id: AgentId | None = None):
        log.debug("rpc::assign_port()")
        agent = self.runtime.get_agent(agent_id)
        return agent.port_pool.pop()

    @rpc_function
    @collect_error
    async def release_port(self, port_no: int, agent_id: AgentId | None = None):
        log.debug("rpc::release_port(port_no:{})", port_no)
        agent = self.runtime.get_agent(agent_id)
        agent.port_pool.add(port_no)

    @rpc_function
    @collect_error
    async def scan_gpu_alloc_map(self, agent_id: AgentId | None = None) -> Mapping[str, Any]:
        log.debug("rpc::scan_gpu_alloc_map()")
        agent = self.runtime.get_agent(agent_id)
        scratch_root = agent.local_config.container.scratch_root
        result = await scan_gpu_alloc_map(list(agent.kernel_registry.keys()), scratch_root)
        return {k: str(v) for k, v in result.items()}


@aiotools.server_context
async def server_main_logwrapper(
    loop: asyncio.AbstractEventLoop,
    pidx: int,
    _args: Sequence[Any],
) -> AsyncGenerator[None, signal.Signals]:
    setproctitle(f"backend.ai: agent worker-{pidx}")
    local_cfg: AgentUnifiedConfig = _args[0]
    log_endpoint = _args[1]
    logger = Logger(
        local_cfg.logging,
        is_master=False,
        log_endpoint=log_endpoint,
        msgpack_options={
            "pack_opts": msgpack.DEFAULT_PACK_OPTS,
            "unpack_opts": msgpack.DEFAULT_UNPACK_OPTS,
        },
    )
    try:
        with logger:
            async with server_main(loop, pidx, _args):
                yield
    except Exception:
        traceback.print_exc(file=sys.stderr)


async def check_health(request: web.Request) -> web.Response:
    """Health check endpoint with dependency connectivity status"""

    from . import __version__

    request["do_not_print_access_log"] = True

    health_probe: HealthProbe = request.app["health_probe"]
    connectivity = await health_probe.get_connectivity_status()
    response = HealthResponse(
        status=HealthStatus.OK if connectivity.overall_healthy else HealthStatus.DEGRADED,
        version=__version__,
        component="agent",
        connectivity=connectivity,
    )
    return web.json_response(response.model_dump(mode="json"))


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
    cors.add(app.router.add_route("GET", r"/health", check_health))
    cors.add(
        app.router.add_route("GET", r"/metrics", build_prometheus_metrics_handler(metric_registry))
    )
    return app


@asynccontextmanager
async def aiomonitor_ctx(
    local_config: AgentUnifiedConfig,
    pidx: int,
) -> AsyncIterator[aiomonitor.Monitor]:
    """
    Starts aiomonitor.
    """
    # Port is set by config where the defaults are:
    # termui_port = 38200 + pidx
    # webui_port = 39200 + pidx
    loop = asyncio.get_running_loop()
    monitor = aiomonitor.Monitor(
        loop,
        termui_port=local_config.agent_common.aiomonitor_termui_port + pidx,
        webui_port=local_config.agent_common.aiomonitor_webui_port + pidx,
        console_enabled=False,
        hook_task_factory=local_config.debug.enhanced_aiomonitor_task_info,
    )
    Profiler(
        pyroscope_args=PyroscopeArgs(
            enabled=local_config.pyroscope.enabled,
            application_name=local_config.pyroscope.app_name,
            server_address=local_config.pyroscope.server_addr,
            sample_rate=local_config.pyroscope.sample_rate,
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
    try:
        yield monitor
    finally:
        if aiomon_started:
            monitor.close()


@asynccontextmanager
async def etcd_ctx(local_config: AgentUnifiedConfig) -> AsyncGenerator[AsyncEtcd]:
    etcd_credentials = None
    if local_config.etcd.user and local_config.etcd.password:
        etcd_credentials = {
            "user": local_config.etcd.user,
            "password": local_config.etcd.password,
        }
    scope_prefix_map = {
        ConfigScopes.GLOBAL: "",
        ConfigScopes.SGROUP: f"sgroup/{local_config.agent.scaling_group}",
        ConfigScopes.NODE: f"nodes/agents/{local_config.agent.defaulted_id}",
    }
    etcd_config_data = local_config.etcd.to_dataclass()
    etcd = AsyncEtcd(
        [addr.to_legacy() for addr in etcd_config_data.addrs],
        local_config.etcd.namespace,
        scope_prefix_map,
        credentials=etcd_credentials,
    )
    try:
        yield etcd
    finally:
        await etcd.close()


async def prepare_krunner_volumes(local_config: AgentUnifiedConfig) -> None:
    log.info("Preparing kernel runner environments...")
    agent_discovery = get_agent_discovery(local_config.agent_common.backend)
    krunner_volumes = await agent_discovery.prepare_krunner_env(
        local_config.model_dump(by_alias=True)
    )
    # TODO: merge k8s branch: nfs_mount_path = local_config['baistatic']['mounted-at']
    log.info("Kernel runner environments: {}", [*krunner_volumes.keys()])
    local_config.update(container_update={"krunner_volumes": krunner_volumes})


async def auto_detect_agent_identity(local_config: AgentUnifiedConfig) -> None:
    # Update agent id and instance type if not set
    agent_updates = {}
    if not local_config.agent_default.id:
        agent_updates["id"] = await identity.get_instance_id()
    if not local_config.agent_common.instance_type:
        agent_updates["instance_type"] = await identity.get_instance_type()
    local_config.update(agent_update=agent_updates)


async def auto_detect_agent_network(
    local_config: AgentUnifiedConfig,
    etcd: AsyncEtcd,
) -> None:
    rpc_addr = local_config.agent_common.rpc_listen_addr
    if not rpc_addr.host:
        _subnet_hint = await etcd.get("config/network/subnet/agent")
        subnet_hint = None
        if _subnet_hint is not None:
            subnet_hint = ip_network(_subnet_hint)
        log.debug("auto-detecting agent host")
        new_rpc_addr = HostPortPair(
            await identity.get_instance_ip(subnet_hint),
            rpc_addr.port,
        )
        local_config.update(agent_update={"rpc_listen_addr": new_rpc_addr})
    # Handle container bind-host configuration
    if not local_config.container.bind_host:
        log.debug(
            "auto-detecting `container.bind-host` from container subnet config "
            "and agent.rpc-listen-addr"
        )
        bind_host = await get_subnet_ip(
            etcd,
            "container",
            fallback_addr=local_config.agent_common.rpc_listen_addr.host,
        )
        local_config.update(container_update={"bind_host": bind_host})
    log.info("Agent external IP: {}", local_config.agent_common.rpc_listen_addr.host)
    log.info("Container external IP: {}", local_config.container.bind_host)
    # Update region if not set
    if not local_config.agent_common.region:
        region = await identity.get_instance_region()
        local_config.update(agent_update={"region": region})
    log.info(
        "Node ID: {0} (machine-type: {1}, host: {2})",
        local_config.agent_default.id,  # defaults to instance id
        local_config.agent_common.instance_type,
        rpc_addr.host,
    )


@asynccontextmanager
async def agent_server_ctx(
    local_config: AgentUnifiedConfig, etcd: AsyncEtcd
) -> AsyncGenerator[AgentRPCServer]:
    agent_server = await AgentRPCServer.new(
        etcd,
        local_config,
        skip_detect_manager=local_config.agent_common.skip_manager_detection,
    )
    app = build_root_server()
    app["health_probe"] = agent_server.health_probe
    runner = web.AppRunner(app)
    await runner.setup()
    internal_addr = local_config.agent_common.internal_addr.to_legacy()
    ssl_ctx = None

    if local_config.agent_common.ssl_enabled:
        ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_ctx.load_cert_chain(
            str(local_config.agent_common.ssl_cert),
            str(local_config.agent_common.ssl_key),
        )
    site = web.TCPSite(
        runner,
        str(internal_addr.host),
        internal_addr.port,
        backlog=1024,
        reuse_port=True,
        ssl_context=ssl_ctx,
    )
    await site.start()
    log.info("started serving HTTP at {}", internal_addr)
    async with agent_server:
        yield agent_server


@asynccontextmanager
async def service_discovery_ctx(
    etcd: AsyncEtcd,
    agent_server: AgentRPCServer,
) -> AsyncGenerator[None]:
    local_config = agent_server.local_config
    announce_internal_addr = local_config.agent_common.announce_internal_addr.to_legacy()
    sd_type = ServiceDiscoveryType(local_config.service_discovery.type)
    service_discovery: ServiceDiscovery
    match sd_type:
        case ServiceDiscoveryType.ETCD:
            service_discovery = ETCDServiceDiscovery(ETCDServiceDiscoveryArgs(etcd))
        case ServiceDiscoveryType.REDIS:
            await agent_server.read_agent_config()
            if not local_config.redis:
                raise ConfigurationError({"server_main": "Redis runtime configuration is missing."})
            valkey_profile_target = local_config.redis.to_valkey_profile_target()
            live_valkey_target = valkey_profile_target.profile_target(RedisRole.LIVE)
            service_discovery = await RedisServiceDiscovery.create(
                args=RedisServiceDiscoveryArgs(valkey_target=live_valkey_target)
            )
    sd_loop = ServiceDiscoveryLoop(
        sd_type,
        service_discovery,
        ServiceMetadata(
            display_name=f"agent-{local_config.agent_default.defaulted_id}",  # defaults to instance id
            service_group="agent",
            version=VERSION,
            endpoint=ServiceEndpoint(
                address=str(announce_internal_addr),
                port=announce_internal_addr.port,
                protocol="http",
                prometheus_address=str(announce_internal_addr),
            ),
        ),
    )
    if local_config.otel.enabled:
        meta = sd_loop.metadata
        otel_spec = OpenTelemetrySpec(
            service_id=meta.id,
            service_name=meta.service_group,
            service_version=meta.version,
            log_level=local_config.otel.log_level,
            endpoint=local_config.otel.endpoint,
        )
        BraceStyleAdapter.apply_otel(otel_spec)
    try:
        yield
    finally:
        sd_loop.close()


@aiotools.server_context
async def server_main(
    loop: asyncio.AbstractEventLoop,
    pidx: int,
    _args: Sequence[Any],
) -> AsyncGenerator[None, signal.Signals]:
    local_config: AgentUnifiedConfig = _args[0]
    loop.set_debug(local_config.debug.asyncio)
    agent_server: AgentRPCServer | None = None
    agent_init_stack = AsyncExitStack()
    await agent_init_stack.__aenter__()
    try:
        monitor = await agent_init_stack.enter_async_context(aiomonitor_ctx(local_config, pidx))
        await prepare_krunner_volumes(local_config)
        await auto_detect_agent_identity(local_config)

        # etcd's scope-prefix map depends on the auto-detected identity info.
        etcd = await agent_init_stack.enter_async_context(etcd_ctx(local_config))
        await auto_detect_agent_network(local_config, etcd)
        plugins = await etcd.get_prefix_dict("config/plugins/accelerator")
        local_config.overwrite(plugins=plugins)

        # Start RPC server.
        agent_server = await agent_init_stack.enter_async_context(
            agent_server_ctx(local_config, etcd)
        )
        monitor.console_locals["agent_server"] = agent_server

        await agent_init_stack.enter_async_context(service_discovery_ctx(etcd, agent_server))
        log.info("Started the agent service.")
    except Exception:
        log.exception("Server initialization failure; triggering shutdown...")
        loop.call_later(0.2, os.kill, 0, signal.SIGINT)

    # Run!
    stop_signal = signal.SIGTERM  # default termination signal
    try:
        stop_signal = yield
    finally:
        log.info("shutting down...")
        if agent_server is not None:
            agent_server.mark_stop_signal(stop_signal)
        await agent_init_stack.__aexit__(None, None, None)


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
    help="A shortcut to set `--log-level=DEBUG`",
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
    config_path: Path | None,
    debug: bool,
    log_level: LogLevel,
) -> int:
    """Start the agent service as a foreground process."""
    if debug:
        log_level = LogLevel.DEBUG

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

    # Validate and fill configurations
    # (allow_extra will make configs to be forward-copmatible)
    try:
        is_invoked_subcommand = cli_ctx.invoked_subcommand is not None
        server_config = AgentUnifiedConfig.model_validate(
            raw_cfg,
            context=AgentConfigValidationContext(
                debug=log_level == LogLevel.DEBUG,
                log_level=log_level,
                is_invoked_subcommand=is_invoked_subcommand,
            ),
        )

        if server_config.debug.enabled:
            print("== Agent configuration ==")
            pprint(server_config.model_dump(by_alias=True))
    except ValidationError as e:
        print(
            "ConfigurationError: Agent local config failed validation checks:",
            file=sys.stderr,
        )
        print(e, file=sys.stderr)
        raise click.Abort()
    except Exception as e:
        print(
            "ConfigurationError: Parsing agent local config failed for an unknown reason:",
            file=sys.stderr,
        )
        print(str(e), file=sys.stderr)
        raise click.Abort()

    if not is_invoked_subcommand:
        server_config.agent_common.pid_file.write_text(str(os.getpid()))
        image_commit_path = server_config.agent_common.image_commit_path
        image_commit_path.mkdir(parents=True, exist_ok=True)
        ipc_base_path = server_config.agent_common.ipc_base_path
        log_sockpath = ipc_base_path / f"agent-logger-{os.getpid()}.sock"
        log_sockpath.parent.mkdir(parents=True, exist_ok=True)
        log_endpoint = f"ipc://{log_sockpath}"
        try:
            logger = Logger(
                server_config.logging,
                is_master=True,
                log_endpoint=log_endpoint,
                msgpack_options={
                    "pack_opts": msgpack.DEFAULT_PACK_OPTS,
                    "unpack_opts": msgpack.DEFAULT_UNPACK_OPTS,
                },
            )
            with logger:
                ns = server_config.etcd.namespace
                setproctitle(f"backend.ai: agent {ns}")
                log.info("Backend.AI Agent {0}", VERSION)
                log.info("runtime: {0}", utils.env_info())

                log_config = logging.getLogger("ai.backend.agent.config")
                if log_level == LogLevel.DEBUG:
                    log_config.debug("debug mode enabled.")
                match server_config.agent_common.event_loop:
                    case EventLoopType.UVLOOP:
                        import uvloop

                        runner = uvloop.run
                        log.info("Using uvloop as the event loop backend")
                    case EventLoopType.ASYNCIO:
                        runner = asyncio.run
                aiotools.start_server(
                    server_main_logwrapper,
                    num_workers=1,
                    args=(server_config, log_endpoint),
                    wait_timeout=5.0,
                    runner=runner,
                )
                log.info("exit.")
        finally:
            if server_config.agent_common.pid_file.is_file():
                # check is_file() to prevent deleting /dev/null!
                server_config.agent_common.pid_file.unlink()
    else:
        # Click is going to invoke a subcommand.
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
