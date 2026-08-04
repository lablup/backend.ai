from __future__ import annotations

import asyncio
import logging
import os
import re
import time
from abc import ABCMeta, abstractmethod
from collections import UserDict
from collections.abc import (
    Iterator,
    Mapping,
    MutableMapping,
)
from dataclasses import dataclass
from typing import (
    Any,
    Literal,
    overload,
    override,
)

import zmq
import zmq.asyncio

from ai.backend.common.docker import ImageRef
from ai.backend.common.dto.agent.response import CodeCompletionResp
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.kernel.types import (
    KernelLifecycleEventReason,
)
from ai.backend.common.kernel_runner import (
    RUN_ID_FOR_BATCH_JOB,
    AbstractCodeRunner,
    BuildFinished,
    CleanFinished,
    ClientFeatures,
    ConsoleItemType,
    ExecTimeout,
    InputRequestPending,
    NextResult,
    ResultRecord,
    ResultType,
    RunEvent,
    RunFinished,
    default_api_version,
    default_client_features,
    outgoing_msg_types,
)
from ai.backend.common.types import (
    AgentId,
    CommitStatus,
    ContainerId,
    KernelId,
    ServicePort,
    SessionId,
    SessionTypes,
    aobject,
)
from ai.backend.logging import BraceStyleAdapter

from .errors import (
    KernelRunnerNotInitializedError,
    UnsupportedBaseDistroError,
)
from .resources import KernelResourceSpec
from .types import AgentEventData, KernelLifecycleStatus, KernelOwnershipData

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

__all__ = [
    "RUN_ID_FOR_BATCH_JOB",
    "AbstractCodeRunner",
    "AbstractKernel",
    "BuildFinished",
    "CleanFinished",
    "ClientFeatures",
    "ConsoleItemType",
    "ExecTimeout",
    "InputRequestPending",
    "KernelOwnershipData",
    "NextResult",
    "ResultRecord",
    "ResultType",
    "RunEvent",
    "RunFinished",
    "default_api_version",
    "default_client_features",
    "outgoing_msg_types",
]

class AbstractKernel(UserDict[str, Any], aobject, metaclass=ABCMeta):
    version: int
    ownership_data: KernelOwnershipData
    agent_config: Mapping[str, Any]
    session_id: SessionId
    kernel_id: KernelId
    agent_id: AgentId
    network_id: str
    container_id: ContainerId | None
    image: ImageRef
    resource_spec: KernelResourceSpec
    service_ports: list[ServicePort]
    data: dict[Any, Any]
    last_used: float
    termination_reason: KernelLifecycleEventReason | None
    clean_event: asyncio.Future[Any] | None
    # FIXME: apply TypedDict to data in Python 3.8
    environ: Mapping[str, Any]
    state: KernelLifecycleStatus
    session_type: SessionTypes

    _tasks: set[asyncio.Task[Any]]

    runner: AbstractCodeRunner | None

    def __init__(
        self,
        ownership_data: KernelOwnershipData,
        network_id: str,
        image: ImageRef,
        version: int,
        *,
        agent_config: Mapping[str, Any],
        resource_spec: KernelResourceSpec,
        service_ports: Any,  # TODO: type-annotation
        data: dict[Any, Any],
        environ: Mapping[str, Any],
        session_type: SessionTypes = SessionTypes.INTERACTIVE,
    ) -> None:
        self.agent_config = agent_config
        self.ownership_data = ownership_data
        self.kernel_id = ownership_data.kernel_id
        self.session_id = ownership_data.session_id
        self.agent_id = ownership_data.agent_id
        self.network_id = network_id
        self.image = image
        self.version = version
        self.resource_spec = resource_spec
        self.service_ports = service_ports
        self.data = data
        self.last_used = time.monotonic()
        self.termination_reason = None
        self.clean_event = None
        self.environ = environ
        self.runner = None
        self.container_id = None
        self.state = KernelLifecycleStatus.PREPARING
        self.session_type = session_type

    @property
    def channel_terminated(self) -> bool:
        return False

    def set_container_id(self, cid: ContainerId) -> None:
        self.container_id = cid
        self["container_id"] = cid

    async def init(self, event_producer: EventProducer) -> None:
        if self.channel_terminated:
            return
        log.debug(
            "kernel.init(k:{0}, api-ver:{1}, client-features:{2}): starting new runner",
            self.kernel_id,
            default_api_version,
            default_client_features,
        )
        try:
            self.runner = await self.create_code_runner(
                event_producer,
                client_features=default_client_features,
                api_version=default_api_version,
            )
        except Exception as e:
            log.error("kernel.init(k:{0}): failed to create code runner: {1}", self.kernel_id, e)
            self.runner = None
            raise

    @override
    def __getstate__(self) -> Mapping[str, Any]:
        props = self.__dict__.copy()
        del props["agent_config"]
        del props["clean_event"]
        return props

    def __setstate__(self, props: MutableMapping[str, Any]) -> None:
        # Used when a `Kernel` object is loaded from pickle data.
        if "state" not in props:
            props["state"] = KernelLifecycleStatus.RUNNING
        if "ownership_data" not in props:
            props["ownership_data"] = KernelOwnershipData(
                props["kernel_id"],
                props["session_id"],
                props["agent_id"],
            )
        if "session_type" not in props:
            props["session_type"] = SessionTypes.INTERACTIVE
        if "stats_enabled" in props:
            # stats_enabled is a property, not an attribute.
            del props["stats_enabled"]
        self.__dict__.update(props)
        # agent_config is set by the pickle.loads() caller.
        self.clean_event = None

    @abstractmethod
    async def close(self) -> None:
        """
        Release internal resources used for interacting with the kernel.
        Note that this does NOT terminate the container.
        """
        pass

    # We don't have "allocate_slots()" method here because:
    # - resource_spec is initialized by allocating slots at computer's alloc_map
    #   when creating new kernels.
    # - restoration from running containers is done by computer's classmethod
    #   "restore_from_container"

    def release_slots(self, computer_ctxs: Mapping[str, Any]) -> None:
        """
        Release the resource slots occupied by the kernel
        to the allocation maps.
        """
        for accel_key, accel_alloc in self.resource_spec.allocations.items():
            computer_ctxs[accel_key].alloc_map.free(accel_alloc)

    @property
    def stats_enabled(self) -> bool:
        """
        Returns True if the kernel supports statistics gathering.
        """
        return self.state == KernelLifecycleStatus.RUNNING

    @abstractmethod
    async def create_code_runner(
        self,
        event_producer: EventProducer,
        *,
        client_features: frozenset[str],
        api_version: int,
    ) -> AbstractCodeRunner:
        raise NotImplementedError

    @abstractmethod
    async def check_status(self) -> dict[str, Any] | None:
        raise NotImplementedError

    @abstractmethod
    async def get_completions(self, text: str, opts: Mapping[str, Any]) -> CodeCompletionResp:
        raise NotImplementedError

    @abstractmethod
    async def get_logs(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def interrupt_kernel(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def start_service(self, service: str, opts: Mapping[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def start_model_service(self, model_service: Mapping[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def shutdown_service(self, service: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def check_duplicate_commit(self, kernel_id: KernelId, subdir: str) -> CommitStatus:
        raise NotImplementedError

    @abstractmethod
    async def commit(
        self,
        kernel_id: KernelId,
        subdir: str,
        *,
        canonical: str | None = None,
        filename: str | None = None,
        extra_labels: dict[str, str] | None = None,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_service_apps(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def accept_file(self, container_path: os.PathLike[str] | str, filedata: bytes) -> None:
        """
        Put the uploaded file to the designated container path.
        The path should be inside /home/work of the container.
        A relative path is interpreted as a subpath inside /home/work.

        WARNING: Since the implementations may use the scratch directory mounted as the home
        directory inside the container, the file may not be visible inside the container if the
        designated home-relative path overlaps with a vfolder mount.
        """
        raise NotImplementedError

    @abstractmethod
    async def download_file(self, container_path: os.PathLike[str] | str) -> bytes:
        """
        Download the designated path (a single file or an entire directory) as a tar archive.
        The path should be inside /home/work of the container.
        A relative path is interpreted as a subpath inside /home/work.
        The return value is the raw byte stream of the archive itself, and it is the caller's
        responsibility to extract the tar archive.

        This API is intended to download a small set of files from the container filesystem.
        """
        raise NotImplementedError

    @abstractmethod
    async def download_single(self, container_path: os.PathLike[str] | str) -> bytes:
        """
        Download the designated path (a single file) as a tar archive.
        The path should be inside /home/work of the container.
        A relative path is interpreted as a subpath inside /home/work.
        The return value is the content of the file *extracted* from the downloaded archive.

        This API is intended to download a small file from the container filesystem.
        """
        raise NotImplementedError

    @abstractmethod
    async def list_files(self, container_path: os.PathLike[str] | str) -> dict[str, Any]:
        """
        List the directory entries of the designated path.
        The path should be inside /home/work of the container.
        A relative path is interpreted as a subpath inside /home/work.
        """
        raise NotImplementedError

    @abstractmethod
    async def notify_event(self, evdata: AgentEventData) -> None:
        raise NotImplementedError

    async def ping(self) -> dict[str, float] | None:
        if self.runner is None:
            raise KernelRunnerNotInitializedError("Kernel runner is not initialized")
        return await self.runner.ping()

    async def execute(
        self,
        run_id: str | None,
        mode: Literal["batch", "query", "input", "continue"],
        text: str,
        *,
        opts: Mapping[str, Any],
        api_version: int,
        flush_timeout: float,
    ) -> NextResult:
        if self.runner is None:
            raise KernelRunnerNotInitializedError("Kernel runner is not initialized")
        try:
            log.info(
                "kernel.execute(k:{0}, run_id:{1}, mode:{2}, opts:{3})",
                self.kernel_id,
                run_id,
                mode,
                opts,
            )
            await self.runner.attach_output_queue(run_id)
            try:
                if mode == "batch":
                    await self.runner.feed_batch(opts)
                elif mode == "query":
                    await self.runner.feed_code(text)
                elif mode == "input":
                    await self.runner.feed_input(text)
                elif mode == "continue":
                    pass
            except zmq.ZMQError as e:
                # cancel the operation by myself
                # since the peer is gone.
                raise asyncio.CancelledError from e

            return await self.runner.get_next_result(
                api_ver=api_version,
                flush_timeout=flush_timeout,
            )
        except asyncio.CancelledError:
            await self.runner.close()
            raise


@dataclass(frozen=True)
class AgentKernelRegistryKey:
    agent_id: AgentId
    kernel_id: KernelId


class KernelRegistryAgentMapping(MutableMapping[KernelId, AbstractKernel]):
    _registry: KernelRegistry
    _agent_id: AgentId

    def __init__(self, kernel_registry: KernelRegistry, agent_id: AgentId) -> None:
        super().__init__()

        self._registry = kernel_registry
        self._agent_id = agent_id

    @override
    def __getitem__(self, key: KernelId) -> AbstractKernel:
        return self._registry[AgentKernelRegistryKey(self._agent_id, key)]

    @override
    def __setitem__(self, key: KernelId, value: AbstractKernel) -> None:
        self._registry[AgentKernelRegistryKey(self._agent_id, key)] = value

    @override
    def __delitem__(self, key: KernelId) -> None:
        del self._registry[AgentKernelRegistryKey(self._agent_id, key)]

    @override
    def __iter__(self) -> Iterator[KernelId]:
        for registry_key in self._registry:
            if registry_key.agent_id == self._agent_id:
                yield registry_key.kernel_id

    @override
    def __len__(self) -> int:
        return sum(1 for key in self._registry if key.agent_id == self._agent_id)


class KernelRegistryGlobalView(Mapping[KernelId, AbstractKernel]):
    _registry: KernelRegistry

    def __init__(self, kernel_registry: KernelRegistry) -> None:
        super().__init__()

        self._registry = kernel_registry

    @override
    def __getitem__(self, key: KernelId) -> AbstractKernel:
        return self._registry[key]

    @override
    def __iter__(self) -> Iterator[KernelId]:
        for registry_key in self._registry:
            yield registry_key.kernel_id

    @override
    def __len__(self) -> int:
        return len(self._registry)


class KernelRegistry(MutableMapping[AgentKernelRegistryKey, AbstractKernel]):
    _registry: MutableMapping[AgentKernelRegistryKey, AbstractKernel]
    _global_registry: MutableMapping[KernelId, AbstractKernel]

    def __init__(self) -> None:
        super().__init__()

        self._registry = {}
        self._global_registry = {}

    def agent_mapping(self, agent_id: AgentId) -> KernelRegistryAgentMapping:
        return KernelRegistryAgentMapping(self, agent_id)

    def global_view(self) -> KernelRegistryGlobalView:
        return KernelRegistryGlobalView(self)

    @overload
    def __getitem__(self, key: KernelId) -> AbstractKernel: ...

    @overload
    def __getitem__(self, key: AgentKernelRegistryKey) -> AbstractKernel: ...

    @override
    def __getitem__(self, key: KernelId | AgentKernelRegistryKey) -> AbstractKernel:
        if isinstance(key, AgentKernelRegistryKey):
            return self._registry[key]
        return self._global_registry[key]

    @override
    def __setitem__(self, key: AgentKernelRegistryKey, value: AbstractKernel) -> None:
        self._registry[key] = value
        self._global_registry[key.kernel_id] = value

    @override
    def __delitem__(self, key: AgentKernelRegistryKey) -> None:
        del self._registry[key]
        del self._global_registry[key.kernel_id]

    @override
    def __iter__(self) -> Iterator[AgentKernelRegistryKey]:
        return iter(self._registry)

    @override
    def __len__(self) -> int:
        return len(self._registry)




def match_distro_data(data: Mapping[str, Any], distro: str) -> tuple[str, Any]:
    """
    Find the latest or exactly matching entry from krunner_volumes mapping using the given distro
    string expression.

    It assumes that the keys of krunner_volumes mapping is a string concatenated with a distro
    prefix (e.g., "centos", "ubuntu") and a distro version composed of multiple integer components
    joined by single dots (e.g., "1.2.3", "18.04").
    """
    rx_ver_suffix = re.compile(r"(\d+(\.\d+)*)$")

    def _extract_version(key: str) -> tuple[int, ...]:
        m = rx_ver_suffix.search(key)
        if m is not None:
            return tuple(map(int, m.group(1).split(".")))
        return (0,)

    m = rx_ver_suffix.search(distro)
    if m is None:
        # Assume latest
        distro_prefix = distro
        distro_ver = None
    else:
        distro_prefix = distro[: -len(m.group(1))]
        distro_ver = tuple(map(int, m.group(1).split(".")))

    # Check if there are static-build krunners first.
    if distro_prefix == "alpine":
        libc_flavor = "musl"
    else:
        libc_flavor = "gnu"
    distro_key = f"static-{libc_flavor}"
    if volume := data.get(distro_key):
        return distro_key, volume

    # Search through the per-distro versions
    match_list = [
        (distro_key, value, _extract_version(distro_key))
        for distro_key, value in data.items()
        if distro_key.startswith(distro_prefix)
    ]

    match_list = sorted(match_list, key=lambda x: x[2], reverse=True)
    if match_list:
        if distro_ver is None:
            return match_list[0][:-1]  # return latest
        for distro_key, value, matched_distro_ver in match_list:
            if distro_ver >= matched_distro_ver:
                return (distro_key, value)
        return match_list[-1][:-1]  # fallback to the latest of its kind
    raise UnsupportedBaseDistroError(distro)
