"""Expand ``KernelGroupDraft`` entries into per-replica ``KernelSpecDraft``.

This is the typed counterpart of the legacy dict-based
:class:`.cluster.ClusterConfigurationRule`. Where the legacy rule had
to infer cluster layout from a ``cluster_size`` integer and a
dict-based kernel-specs list (with implicit auto-replication when the
list had one entry), the new model carries an explicit
``tuple[KernelGroupDraft, ...]`` with a ``replica_count`` on each
group — this rule flattens that list, assigning:

  * ``cluster_idx``    — 1-based within the role
  * ``cluster_hostname`` — ``f"{role}{cluster_idx}"``
  * ``local_rank``     — 0-based across the whole session

The group's ``execution_spec`` (a :class:`KernelExecutionSpecDraft`
with possibly-unset fields) is copied onto each replica unchanged; an
earlier rule is expected to have filled RG-default fields on the
group's execution_spec before expansion runs.
"""

from __future__ import annotations

from typing import override

from ai.backend.manager.data.session.draft import (
    KernelSpecDraft,
    SessionResourceSpecDraft,
)
from ai.backend.manager.sokovan.scheduling_controller.preparers.draft_rule import (
    SessionSpecDraftRule,
    SessionSpecPreparationContext,
)


class ExpandKernelGroupsRule(SessionSpecDraftRule):
    """Flatten ``options.kernel_groups`` into per-replica kernel drafts.

    When ``options.kernel_groups`` is still ``None`` this rule is a
    no-op — the missing-field check surfaces at finalize instead, with
    its attribute-path error message intact.
    """

    @override
    def name(self) -> str:
        return "expand_kernel_groups"

    @override
    async def prepare(
        self,
        draft: SessionResourceSpecDraft,
        context: SessionSpecPreparationContext,
    ) -> SessionResourceSpecDraft:
        groups = draft.options.kernel_groups
        if groups is None:
            return draft

        expanded: list[KernelSpecDraft] = []
        local_rank = 0
        for group in groups:
            for replica_idx in range(group.replica_count):
                cluster_idx = replica_idx + 1  # 1-based within role
                expanded.append(
                    KernelSpecDraft(
                        cluster_role=group.role,
                        cluster_idx=cluster_idx,
                        cluster_hostname=f"{group.role}{cluster_idx}",
                        local_rank=local_rank,
                        preopen_ports=group.preopen_ports,
                        execution_spec=group.execution_spec,
                    )
                )
                local_rank += 1

        return draft.model_copy(update={"kernel_specs": tuple(expanded)})
