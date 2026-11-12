"""Session-level environ overlay rule.

Ports the legacy per-session environ composition
(``SessionPreparer.prepare`` lines 87-92) into the draft chain: when
``sudo_session_enabled`` is set on the preparation context, every
kernel group's ``execution_spec.environ`` gets an
``"SUDO_SESSION_ENABLED": "1"`` entry overlaid on top.

Runs before :class:`.expand_kernel_groups_rule.ExpandKernelGroupsRule`
so the stored group carries the same environ its replicas start with,
and after
:class:`.merge_resource_group_defaults_rule.MergeResourceGroupDefaultsRule`
whose environ merge replaces the whole mapping when the draft's own is
non-empty. Caller-supplied environ keys (from the request adapter)
survive underneath — the overlay only ever adds one deterministic key.
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

_SUDO_ENABLED_ENV_KEY = "SUDO_SESSION_ENABLED"
_SUDO_ENABLED_ENV_VALUE = "1"


class InjectSessionEnvironRule(SessionSpecDraftRule):
    """Overlay ``SUDO_SESSION_ENABLED=1`` on every kernel group when sudo is enabled."""

    @override
    def name(self) -> str:
        return "inject_session_environ"

    @override
    async def prepare(
        self,
        draft: SessionResourceSpecDraft,
        context: SessionSpecContext,
    ) -> SessionResourceSpecDraft:
        if not draft.internal_data_extras.sudo_session_enabled:
            return draft
        groups = draft.resource.options.kernel_groups
        if not groups:
            return draft

        new_groups = tuple(
            group.model_copy(
                update={
                    "execution_spec": group.execution_spec.model_copy(
                        update={
                            "environ": {
                                **dict(group.execution_spec.environ),
                                _SUDO_ENABLED_ENV_KEY: _SUDO_ENABLED_ENV_VALUE,
                            }
                        }
                    )
                }
            )
            for group in groups
        )
        new_options = draft.resource.options.model_copy(update={"kernel_groups": new_groups})
        return draft.model_copy(
            update={"resource": draft.resource.model_copy(update={"options": new_options})}
        )
