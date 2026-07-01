"""RPC handlers for kernel lifecycle operations (v3, pydantic-typed).

Each handler instance is bound to a specific ``AbstractAgent`` at
construction — the ``AgentRPCRegistry`` (see ``agent/rpc/routing.py``)
selects the target agent from the incoming request's ``agent_id`` and
instantiates a fresh handler per dispatch via the factory lambda that
``register_kernel_rpc_methods`` (see sibling ``registry.py``) hands it.

The class is intentionally stateless beyond the bound agent: kernel
lifecycle operations delegate directly to the agent's own methods.
Concrete methods (``create_kernels``, ``destroy_kernel``, …) are added
alongside their wire DTOs as each v3 endpoint lands; they consume
``BaseAgentRequestModel`` payloads and return ``BaseAgentResponseModel``
responses.
"""

from __future__ import annotations

from typing import Any

from ai.backend.agent.agent import AbstractAgent


class KernelRPCHandler:
    """Agent-bound RPC handler for kernel lifecycle operations."""

    _agent: AbstractAgent[Any, Any]

    def __init__(self, *, agent: AbstractAgent[Any, Any]) -> None:
        self._agent = agent

    # Concrete handler methods land here as v3 endpoints are introduced.
    # Expected signature pattern (one param per method):
    #
    #     async def create_kernels(
    #         self,
    #         req: CreateKernelsReq,
    #     ) -> CreateKernelsResp:
    #         return await self._agent.create_kernels(req)
