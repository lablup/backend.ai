"""Per-role vfolder mount resolution rule.

Copies the controller-resolved :class:`VFolderMount` tuple from the
preparation context onto each kernel in the draft. Resolution itself
(accessibility check, dot-prefix auto-mount, host path materialization,
frozen permissions) is performed by the controller inside its readonly
batch-fetch transaction — a pure preparer rule would need to issue DB
reads otherwise, breaking the ``prepare`` signature's "no IO"
invariant. See
:attr:`SessionSpecContext.vfolder_mounts_by_role`.

Runs after :class:`.expand_kernel_groups_rule.ExpandKernelGroupsRule`
so ``draft.resource.kernel_specs`` is already expanded per-replica; each kernel
reads its ``cluster_role`` to fetch the tuple its
:class:`KernelGroup` was resolved to. Replicas of the same role share
the identical tuple without any per-replica duplication at
controller-fetch time. Task #33 (role-based mount override) slots in
naturally — the controller fetch emits distinct tuples per role and
this rule keeps working unchanged.
"""

from __future__ import annotations

from typing import override

from ai.backend.manager.data.session.draft import SessionResourceSpecDraft
from ai.backend.manager.sokovan.scheduling_controller.preparers.specs.draft_rule import (
    SessionSpecDraftRule,
)
from ai.backend.manager.views.sokovan.session_creation import (
    SessionSpecContext,
)


class ResolveVFolderMountsRule(SessionSpecDraftRule):
    """Copy the per-role resolved vfolder mounts from context onto each kernel."""

    @override
    def name(self) -> str:
        return "resolve_vfolder_mounts"

    @override
    async def prepare(
        self,
        draft: SessionResourceSpecDraft,
        context: SessionSpecContext,
    ) -> SessionResourceSpecDraft:
        resolved = context.user.vfolder_mounts_by_role
        if not resolved or not draft.resource.kernel_specs:
            return draft
        updated = []
        for kernel in draft.resource.kernel_specs:
            role = kernel.cluster_role
            mounts = resolved.get(role, ()) if role is not None else ()
            if mounts == kernel.vfolder_mounts:
                updated.append(kernel)
                continue
            updated.append(kernel.model_copy(update={"vfolder_mounts": mounts}))
        return draft.model_copy(
            update={"resource": draft.resource.model_copy(update={"kernel_specs": tuple(updated)})}
        )
