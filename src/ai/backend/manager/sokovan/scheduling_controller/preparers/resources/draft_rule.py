"""Rule interface for the resource-determining portion of a draft.

Same chaining contract as :class:`..draft_rule.SessionSpecDraftRule`,
but over :class:`ResourceSpecDraft` — the options/kernel-spec slice a
session's resource amounts are computed from. The fitting check runs
these rules alone; the enqueue preparer bridges the full draft through
them before the spec rules run.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ai.backend.manager.data.session.draft import ResourceSpecDraft
from ai.backend.manager.views.sokovan.session_creation import SessionSpecContext


class ResourceSpecDraftRule(ABC):
    """Abstract base for resource-determining draft rules.

    Each rule is stateless with respect to a single session and MUST
    be a pure function of its inputs. Returning the same ``draft``
    instance unchanged is explicitly allowed when the rule has
    nothing to contribute.
    """

    @abstractmethod
    def name(self) -> str:
        """Short identifier used in logs and error messages."""
        raise NotImplementedError

    @abstractmethod
    async def prepare(
        self,
        draft: ResourceSpecDraft,
        context: SessionSpecContext,
    ) -> ResourceSpecDraft:
        """Return a new draft with this rule's fields resolved."""
        raise NotImplementedError
