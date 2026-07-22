"""Container user mapping rule.

Ports the legacy per-kernel fallback (``SessionPreparer._prepare_kernels``
lines 286-289) into the draft chain. For each kernel draft:

  * ``uid`` falls back to ``context.user.container_user.uid`` when unset
  * ``main_gid`` falls back to ``context.user.container_user.main_gid``
  * ``supplementary_gids`` falls back to the context's list when empty

Caller-specified values (e.g. a per-kernel override that the request
adapter placed directly onto ``KernelSpecDraft.uid``) survive — the
rule only fills in absent values.

Runs after :class:`.expand_kernel_groups_rule.ExpandKernelGroupsRule`
so the fallback targets each materialized per-replica draft.
"""

from __future__ import annotations

from typing import override

from ai.backend.manager.data.session.draft import SessionResourceSpecDraft
from ai.backend.manager.sokovan.scheduling_controller.preparers.draft_rule import (
    SessionSpecDraftRule,
)
from ai.backend.manager.views.sokovan.session_creation import (
    SessionSpecContext,
)


class AssignContainerUserMappingRule(SessionSpecDraftRule):
    """Fill kernel-draft ``uid`` / ``main_gid`` / ``supplementary_gids`` from the context."""

    @override
    def name(self) -> str:
        return "assign_container_user_mapping"

    @override
    async def prepare(
        self,
        draft: SessionResourceSpecDraft,
        context: SessionSpecContext,
    ) -> SessionResourceSpecDraft:
        info = context.user.container_user
        new_kernels = tuple(
            k.model_copy(
                update={
                    "uid": k.uid if k.uid is not None else info.uid,
                    "main_gid": (k.main_gid if k.main_gid is not None else info.main_gid),
                    "supplementary_gids": (
                        k.supplementary_gids
                        if k.supplementary_gids
                        else tuple(info.supplementary_gids)
                    ),
                }
            )
            for k in draft.kernel_specs
        )
        return draft.model_copy(update={"kernel_specs": new_kernels})
