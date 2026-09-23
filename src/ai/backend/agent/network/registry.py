"""Which data-plane backends this node has, and how one is built (BEP-1079).

The session network drives a backend through `AbstractNetworkAgentPluginV2` and must not know
which ones exist: the backends are distributed as plugins, declared under the
``backendai_network_agent_v2`` entry-point group, and a node that has none simply serves no
cluster-network session. Importing them by name here would make the core depend on the very
package the plugin seam exists to keep out.

What a backend needs to exist is the node's own facts, not a session's -- the uplink it builds
on, the node-wide LOCAL block store it carves subnets from, and which agent owns what it claims.
`BackendSpec` is that bundle, and `create` is where a backend maps it onto its own constructor.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from ai.backend.agent.plugin.network_v2 import AbstractNetworkAgentPluginV2
from ai.backend.logging import BraceStyleAdapter
from ai.backend.plugin.entrypoint import scan_entrypoints

if TYPE_CHECKING:
    from ai.backend.agent.network.local_subnet import LocalSubnetAllocator

__all__ = ("BACKEND_PLUGIN_GROUP", "BackendSpec", "load_backends")

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

#: The entry-point group a data-plane backend declares itself in.
BACKEND_PLUGIN_GROUP = "backendai_network_agent_v2"


@dataclass(frozen=True)
class BackendSpec:
    """The node's facts a backend is built from."""

    #: The interface the data plane is built on, for the life of the process.
    uplink: str
    #: The node-wide LOCAL block store; several agents on one host share it.
    local_subnets: LocalSubnetAllocator
    #: Which agent's name goes on every claim this backend makes.
    agent_id: str


def load_backends(spec: BackendSpec) -> dict[str, AbstractNetworkAgentPluginV2[Any]]:
    """Every installed backend, by the name it registered under.

    A backend that cannot be loaded is left out rather than taken as fatal: the node then does
    not advertise it, which is what keeps a session from being placed where it cannot be served.
    An empty result is a node with no cluster-network backend at all, and says so at startup.
    """
    backends: dict[str, AbstractNetworkAgentPluginV2[Any]] = {}
    for entrypoint in scan_entrypoints(BACKEND_PLUGIN_GROUP):
        try:
            plugin_cls = entrypoint.load()
            backends[entrypoint.name] = plugin_cls.create(spec)
        except Exception:
            log.exception(
                "could not load the {!r} cluster-network backend; this node will not advertise it",
                entrypoint.name,
            )
    if not backends:
        log.warning(
            "no cluster-network backend is installed (entry-point group {!r}); this node serves"
            " no cluster-network session",
            BACKEND_PLUGIN_GROUP,
        )
    return backends
