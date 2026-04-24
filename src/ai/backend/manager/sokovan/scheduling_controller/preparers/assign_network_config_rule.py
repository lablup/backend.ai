"""Network configuration assignment rule.

Ports the legacy :meth:`.preparer.SessionPreparer._determine_network_config`
logic into the draft-based chain. Runs late enough that a caller can
pre-set ``SessionNetworkDraft.network_id`` to force a specific
persistent network, and the resource-group's ``use_host_network``
flag (read from the preparation context) decides between HOST and
VOLATILE for everything else.

Priority (unchanged from legacy):

  1. ``draft.network.network_id`` populated (caller requested a
     persistent network) → :attr:`NetworkType.PERSISTENT`
  2. ``context.resource_group_network.use_host_network`` is true →
     :attr:`NetworkType.HOST`
  3. otherwise → :attr:`NetworkType.VOLATILE` (bridge on single-node,
     overlay on multi-node; resolved at launcher time)

No-op when ``draft.network.network_type`` has already been set by
an earlier rule or by the caller.
"""

from __future__ import annotations

from ai.backend.manager.data.session.draft import SessionSpecDraft
from ai.backend.manager.models.network import NetworkType
from ai.backend.manager.sokovan.scheduling_controller.preparers.draft_rule import (
    SessionSpecDraftRule,
    SessionSpecPreparationContext,
)


class AssignNetworkConfigRule(SessionSpecDraftRule):
    """Resolve ``SessionNetworkDraft.network_type`` using the legacy priority."""

    def name(self) -> str:
        return "assign_network_config"

    async def prepare(
        self,
        draft: SessionSpecDraft,
        context: SessionSpecPreparationContext,
    ) -> SessionSpecDraft:
        net = draft.network
        if net.network_type is not None:
            return draft

        if net.network_id is not None:
            resolved = net.model_copy(update={"network_type": NetworkType.PERSISTENT})
        elif (
            context.resource_group_network is not None
            and context.resource_group_network.use_host_network
        ):
            resolved = net.model_copy(
                update={
                    "network_type": NetworkType.HOST,
                    "use_host_network": True,
                }
            )
        else:
            resolved = net.model_copy(update={"network_type": NetworkType.VOLATILE})
        return draft.model_copy(update={"network": resolved})
