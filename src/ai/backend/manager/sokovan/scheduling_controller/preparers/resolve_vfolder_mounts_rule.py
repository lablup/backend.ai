"""Per-role vfolder mount resolution rule.

Copies the controller-resolved :class:`VFolderMount` tuple from the
preparation context onto each kernel in the draft. Resolution itself
(accessibility check, dot-prefix auto-mount, host path materialization,
frozen permissions) is performed by the controller inside its readonly
batch-fetch transaction — a pure preparer rule would need to issue DB
reads otherwise, breaking the ``prepare`` signature's "no IO"
invariant. See
:attr:`SessionSpecPreparationContext.vfolder_mounts_by_role`.

Runs after :class:`.expand_kernel_groups_rule.ExpandKernelGroupsRule`
so ``draft.kernel_specs`` is already expanded per-replica; each kernel
reads its ``cluster_role`` to fetch the tuple its
:class:`KernelGroup` was resolved to. Replicas of the same role share
the identical tuple without any per-replica duplication at
controller-fetch time. Task #33 (role-based mount override) slots in
naturally — the controller fetch emits distinct tuples per role and
this rule keeps working unchanged.
"""

from __future__ import annotations

from ai.backend.manager.data.session.draft import SessionSpecDraft
from ai.backend.manager.sokovan.scheduling_controller.preparers.draft_rule import (
    SessionSpecDraftRule,
    SessionSpecPreparationContext,
)


class ResolveVFolderMountsRule(SessionSpecDraftRule):
    """Copy the per-role resolved vfolder mounts from context onto each kernel."""

    def name(self) -> str:
        return "resolve_vfolder_mounts"

    async def prepare(
        self,
        draft: SessionSpecDraft,
        context: SessionSpecPreparationContext,
    ) -> SessionSpecDraft:
        resolved = context.vfolder_mounts_by_role
        if not resolved or not draft.kernel_specs:
            return draft
        updated = []
        for kernel in draft.kernel_specs:
            role = kernel.cluster_role
            mounts = resolved.get(role, ()) if role is not None else ()
            if mounts == kernel.vfolder_mounts:
                updated.append(kernel)
                continue
            updated.append(kernel.model_copy(update={"vfolder_mounts": mounts}))
        return draft.model_copy(update={"kernel_specs": tuple(updated)})
