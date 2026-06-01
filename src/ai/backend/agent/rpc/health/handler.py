"""RPC handler for agent health checks (v3, pydantic-typed).

Unlike the kernel handler, ``HealthRPCHandler`` is **not** agent-scoped:
the connectivity probe it relies on (``HealthProbe``) is a process-level
singleton owned by ``AgentRPCServer`` that checks external dependencies
(etcd, docker, …) shared across every ``AbstractAgent`` instance. Only
the probe is injected via the constructor — the handler's state does
not depend on which agent routed the request.

The registrar (``register_health_domain`` in sibling ``registry.py``)
provides the lambda ``lambda agent: HealthRPCHandler(health_probe=...)``
that the top-level registry calls once per agent at bind time. The
``agent`` argument is discarded inside the lambda because there is no
per-agent state to bind; we simply reuse the probe-holding handler
instance shape for every agent slot.

TODO(v3-refactor): when the split between server-scoped and agent-scoped
RPC handlers becomes painful, consider extending ``AgentRPCRegistry``
with an explicit "server-scoped domain" variant so we do not
manufacture ``N`` identical handlers for ``N`` agents. Not worth the
structural churn right now — the extra instances are stateless and
cheap.
"""

from __future__ import annotations

from ai.backend.agent import __version__ as AGENT_VERSION
from ai.backend.common.dto.agent.request import HealthReq
from ai.backend.common.dto.agent.response import HealthResp
from ai.backend.common.dto.internal.health import HealthStatus
from ai.backend.common.health_checker.probe import HealthProbe


class HealthRPCHandler:
    """Server-scoped RPC handler for the agent health endpoint."""

    _health_probe: HealthProbe

    def __init__(self, *, health_probe: HealthProbe) -> None:
        self._health_probe = health_probe

    async def health(self, req: HealthReq) -> HealthResp:
        del req  # empty payload; arg present only so the registry can validate it
        connectivity = await self._health_probe.get_connectivity_status()
        return HealthResp(
            status=HealthStatus.OK if connectivity.overall_healthy else HealthStatus.DEGRADED,
            version=AGENT_VERSION,
            component="agent",
            connectivity=connectivity,
        )
