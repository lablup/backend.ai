"""RPC method registration for the agent health endpoint."""

from __future__ import annotations

from ai.backend.agent.rpc.routing import AgentRPCRegistry
from ai.backend.common.health_checker.probe import HealthProbe

from .handler import HealthRPCHandler


def register_health_domain(
    agent_rpc: AgentRPCRegistry,
    *,
    health_probe: HealthProbe,
) -> None:
    """Attach the health-domain registry to ``agent_rpc``.

    ``health_probe`` is captured once at registration time and passed
    into every ``HealthRPCHandler`` instance. The handler is server-
    scoped (see ``handler.py`` docstring), so the factory lambda below
    discards the ``agent`` argument — probe-only state means every agent
    gets an equivalent handler instance.
    """
    domain = agent_rpc.create_domain(
        lambda _agent: HealthRPCHandler(health_probe=health_probe),
    )
    domain.add_method("health_v2", lambda h: h.health)
