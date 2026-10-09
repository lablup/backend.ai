"""The agent's container-network plugin: CNI's ADD, DEL, STATUS and GC as a Python plugin.

The agent knows a session's network only through this interface; see `ai.backend.agent.network.cni`.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from ai.backend.agent.network.cni import (
    CNI_TYPE_KEY,
    CniAttachment,
    CniRequest,
    CniResult,
    CniStatus,
)
from ai.backend.common.etcd import AbstractKVStore
from ai.backend.common.plugin import AbstractPlugin, BasePluginContext

__all__ = ("AbstractCniPlugin", "CniHostContext", "CniPluginContext")


@dataclass(frozen=True)
class CniHostContext:
    """What the hosting agent gives a CNI plugin at `init`."""

    agent_id: str
    #: Changes on every agent start; fences what an earlier run of this agent id wrote.
    boot_id: str
    #: The container runtime backend, e.g. ``docker``.
    runtime_backend: str
    etcd: AbstractKVStore
    #: The nameservers a container on this node would use, re-read on each call.
    upstream_nameservers: Callable[[], Awaitable[Sequence[str]]]


class AbstractCniPlugin(AbstractPlugin, metaclass=ABCMeta):
    """A container network the agent attaches containers to, without knowing how it is built.

    ``init`` receives a `CniHostContext`. DEL and GC must be idempotent and tolerate containers the
    plugin never attached.
    """

    @abstractmethod
    async def add(self, request: CniRequest) -> CniResult:
        """Attach the container in ``request.netns``; called before its command runs."""
        raise NotImplementedError

    @abstractmethod
    async def delete(self, request: CniRequest) -> None:
        """Detach the container and give back what its ADD took. Called before it is removed."""
        raise NotImplementedError

    @abstractmethod
    async def status(self) -> CniStatus:
        """Whether this plugin can serve an ADD now; polled with the agent's heartbeat."""
        raise NotImplementedError

    @abstractmethod
    async def gc(self, valid: Sequence[CniAttachment]) -> None:
        """Drop what this plugin holds for any container not in ``valid``; called at agent start."""
        raise NotImplementedError


class CniPluginContext(BasePluginContext[AbstractCniPlugin]):
    plugin_group = "backendai_network_cni_v1"

    def plugin_of(self, network_config: Mapping[str, Any] | None) -> AbstractCniPlugin | None:
        """The plugin a session's network config names in its ``type``, or None."""
        name = (network_config or {}).get(CNI_TYPE_KEY)
        return self.plugins.get(name) if isinstance(name, str) else None
