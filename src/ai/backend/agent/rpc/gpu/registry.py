"""RPC method registration for agent GPU devices."""

from __future__ import annotations

from ai.backend.agent.rpc.routing import AgentRPCRegistry

from .handler import GPURPCHandler


def register_gpu_domain(agent_rpc: AgentRPCRegistry) -> None:
    """Attach the GPU-domain registry to ``agent_rpc``."""
    domain = agent_rpc.create_domain(lambda agent: GPURPCHandler(agent=agent))
    domain.add_method("scan_gpu_devices", lambda h: h.scan_gpu_devices)
