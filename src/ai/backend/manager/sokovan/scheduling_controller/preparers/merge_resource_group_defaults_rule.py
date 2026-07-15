"""Resource-group default merge rule.

Replaces the previous split
(``ApplyResourceGroupDefaultsRule`` + ``ApplyDefaultKernelExecutionSpecRule``)
with a single pass that treats the resource-group's
``default_session_options`` / ``default_kernel_execution_spec`` as the
**base**, and lets any field the caller explicitly set on the draft
override it.

Scope:

  * option-level fields: ``priority``, ``is_preemptible``,
    ``cluster_mode``, ``timeouts``,
    ``scheduling_target.agent_selection_policy``
  * per-group ``execution_spec`` fields: ``image_id``, ``resources``,
    ``resource_opts``, ``environ``, ``mounts``, ``startup_command``,
    ``bootstrap_script``, ``starts_at``, ``batch_timeout_sec``

Merge semantics (unchanged from prior split):

  * scalar draft value wins when not ``None``
  * collection draft value wins when not empty
  * RG default fills only the "draft did not set" slots

Runs before :class:`.expand_kernel_groups_rule.ExpandKernelGroupsRule`
so downstream expansion and finalize see fully-resolved options.
"""

from __future__ import annotations

from typing import override

from ai.backend.manager.data.session.draft import (
    KernelExecutionSpecDraft,
    SessionSpecDraft,
)
from ai.backend.manager.data.session.options import KernelExecutionSpec
from ai.backend.manager.sokovan.scheduling_controller.preparers.draft_rule import (
    SessionSpecDraftRule,
    SessionSpecPreparationContext,
)


class MergeResourceGroupDefaultsRule(SessionSpecDraftRule):
    """Overlay RG defaults under caller-supplied draft values."""

    @override
    def name(self) -> str:
        return "merge_resource_group_defaults"

    @override
    async def prepare(
        self,
        draft: SessionSpecDraft,
        context: SessionSpecPreparationContext,
    ) -> SessionSpecDraft:
        rg = context.resource_group_defaults

        # Option-level fill.
        opts = draft.options
        sched = opts.scheduling_target
        new_sched = sched.model_copy(
            update={
                "agent_selection_policy": (
                    sched.agent_selection_policy
                    if sched.agent_selection_policy is not None
                    else rg.agent_selection_policy
                ),
            }
        )
        new_options = opts.model_copy(
            update={
                "priority": opts.priority if opts.priority is not None else rg.priority,
                "is_preemptible": (
                    opts.is_preemptible if opts.is_preemptible is not None else rg.is_preemptible
                ),
                "cluster_mode": (
                    opts.cluster_mode if opts.cluster_mode is not None else rg.cluster_mode
                ),
                "handler_options": (
                    opts.handler_options if opts.handler_options is not None else rg.handler_options
                ),
                "scheduling_target": new_sched,
            }
        )

        # Per-group execution-spec fill — only when RG carries a baseline.
        if rg.default_kernel_execution_spec is not None and opts.kernel_groups is not None:
            rg_exec = rg.default_kernel_execution_spec
            merged_groups = tuple(
                group.model_copy(
                    update={
                        "execution_spec": self._merge_execution_spec(group.execution_spec, rg_exec),
                    }
                )
                for group in opts.kernel_groups
            )
            new_options = new_options.model_copy(update={"kernel_groups": merged_groups})

        return draft.model_copy(update={"options": new_options})

    @staticmethod
    def _merge_execution_spec(
        draft_exec: KernelExecutionSpecDraft,
        rg_exec: KernelExecutionSpec,
    ) -> KernelExecutionSpecDraft:
        return draft_exec.model_copy(
            update={
                "resource_input": draft_exec.resource_input.model_copy(
                    update={
                        "image_id": (
                            draft_exec.resource_input.image_id
                            if draft_exec.resource_input.image_id is not None
                            else rg_exec.resource_input.image_id
                        ),
                        "resources": (
                            draft_exec.resource_input.resources
                            if draft_exec.resource_input.resources
                            else tuple(rg_exec.resource_input.resources)
                        ),
                        "resource_opts": (
                            draft_exec.resource_input.resource_opts
                            if draft_exec.resource_input.resource_opts is not None
                            else rg_exec.resource_input.resource_opts
                        ),
                    }
                ),
                "environ": (draft_exec.environ if draft_exec.environ else dict(rg_exec.environ)),
                "mounts": (draft_exec.mounts if draft_exec.mounts else tuple(rg_exec.mounts)),
                "startup_command": (
                    draft_exec.startup_command
                    if draft_exec.startup_command is not None
                    else rg_exec.startup_command
                ),
                "bootstrap_script": (
                    draft_exec.bootstrap_script
                    if draft_exec.bootstrap_script is not None
                    else rg_exec.bootstrap_script
                ),
                "starts_at": (
                    draft_exec.starts_at if draft_exec.starts_at is not None else rg_exec.starts_at
                ),
                "batch_timeout_sec": (
                    draft_exec.batch_timeout_sec
                    if draft_exec.batch_timeout_sec is not None
                    else rg_exec.batch_timeout_sec
                ),
            }
        )
