"""Session-level environ overlay rule.

Ports the legacy per-session environ composition
(``SessionPreparer.prepare`` lines 87-92) into the draft chain: when
``sudo_session_enabled`` is set on the preparation context, every
kernel draft's ``execution_spec.environ`` gets an
``"SUDO_SESSION_ENABLED": "1"`` entry overlaid on top.

Runs after :class:`.expand_kernel_groups_rule.ExpandKernelGroupsRule`
so the overlay lands on the per-replica drafts directly, and caller-
supplied environ keys (from the request adapter) survive underneath —
the overlay only ever adds one deterministic key.
"""

from __future__ import annotations

from typing import override

from ai.backend.manager.data.session.draft import SessionResourceSpecDraft
from ai.backend.manager.sokovan.scheduling_controller.preparers.draft_rule import (
    SessionSpecDraftRule,
    SessionSpecPreparationContext,
)

_SUDO_ENABLED_ENV_KEY = "SUDO_SESSION_ENABLED"
_SUDO_ENABLED_ENV_VALUE = "1"


class InjectSessionEnvironRule(SessionSpecDraftRule):
    """Overlay ``SUDO_SESSION_ENABLED=1`` on every kernel when sudo is enabled."""

    @override
    def name(self) -> str:
        return "inject_session_environ"

    @override
    async def prepare(
        self,
        draft: SessionResourceSpecDraft,
        context: SessionSpecPreparationContext,
    ) -> SessionResourceSpecDraft:
        if not draft.internal_data_extras.sudo_session_enabled:
            return draft

        new_kernels = tuple(
            k.model_copy(
                update={
                    "execution_spec": k.execution_spec.model_copy(
                        update={
                            "environ": {
                                **dict(k.execution_spec.environ),
                                _SUDO_ENABLED_ENV_KEY: _SUDO_ENABLED_ENV_VALUE,
                            }
                        }
                    )
                }
            )
            for k in draft.kernel_specs
        )
        return draft.model_copy(update={"kernel_specs": new_kernels})
