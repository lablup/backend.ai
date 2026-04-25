"""RPC method registration for kernel lifecycle operations.

Mirrors the REST v2 per-entity registrar pattern (e.g.
``ai.backend.manager.api.rest.v2.domain.registry.register_v2_domain_routes``):
a module-level function creates a per-domain registry on the top-level
``AgentRPCRegistry`` and attaches every v3 kernel RPC method onto it.

Keeping registration out of the handler class means:

* the handler stays focused on request/response translation;
* adding a new v3 method is a single ``add_method`` line here, visible
  alongside every other kernel method in one place;
* the server startup code only has to call
  ``register_kernel_domain(agent_rpc)``.
"""

from __future__ import annotations

from ai.backend.agent.rpc.routing import AgentRPCRegistry

from .handler import KernelRPCHandler


def register_kernel_domain(agent_rpc: AgentRPCRegistry) -> None:
    """Attach the kernel-domain registry to ``agent_rpc``.

    At ``AgentRPCRegistry.bind_to_rpc`` time, the lambda below is invoked
    once per agent — producing one ``KernelRPCHandler`` instance per
    agent, shared by every method registered on this domain.
    Concrete ``add_method`` lines land here as kernel v3 methods are
    introduced; a typical entry looks like::

        domain.add_method("create_kernels_v2", lambda h: h.create_kernels)
    """
    domain = agent_rpc.create_domain(lambda agent: KernelRPCHandler(agent=agent))
    # Concrete v3 kernel method registrations land here.
    del domain
