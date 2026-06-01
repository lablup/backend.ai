"""RPC method registration for agent hardware info."""

from __future__ import annotations

from ai.backend.agent.rpc.routing import AgentRPCRegistry

from .handler import HwinfoRPCHandler


def register_hwinfo_domain(agent_rpc: AgentRPCRegistry) -> None:
    """Attach the hwinfo-domain registry to ``agent_rpc``.

    The factory runs once per agent at bind time, producing one
    ``HwinfoRPCHandler`` instance per agent with the agent injected via
    the constructor.
    """
    domain = agent_rpc.create_domain(lambda agent: HwinfoRPCHandler(agent=agent))
    domain.add_method("gather_hwinfo_v2", lambda h: h.gather_hwinfo)
