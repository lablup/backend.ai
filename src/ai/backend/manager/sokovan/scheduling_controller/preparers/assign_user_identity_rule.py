"""User identity injection rule.

Fills ``SessionIdentity.user_uuid`` from the ambient
:func:`ai.backend.common.contexts.user.current_user` rather than via
the preparation context — the request enters the controller already
authenticated, so the creator-of-record is implicit at that scope.

No-op when the draft already carries a ``user_uuid`` (defensive — the
request adapter should never populate it, but the rule remains
idempotent) or when the ambient context omits a user (rare — left to
finalize to surface as a missing-field error).
"""

from __future__ import annotations

from typing import override

from ai.backend.common.contexts.user import current_user
from ai.backend.manager.data.session.draft import SessionResourceSpecDraft
from ai.backend.manager.sokovan.scheduling_controller.preparers.draft_rule import (
    SessionSpecDraftRule,
)
from ai.backend.manager.views.sokovan.session_creation import (
    SessionSpecContext,
)


class AssignUserIdentityRule(SessionSpecDraftRule):
    """Copy the current user's id into ``SessionIdentityDraft.user_uuid``."""

    @override
    def name(self) -> str:
        return "assign_user_identity"

    @override
    async def prepare(
        self,
        draft: SessionResourceSpecDraft,
        context: SessionSpecContext,
    ) -> SessionResourceSpecDraft:
        if draft.identity.user_uuid is not None:
            return draft
        user = current_user()
        if user is None:
            return draft
        new_identity = draft.identity.model_copy(update={"user_uuid": user.user_id})
        return draft.model_copy(update={"identity": new_identity})
