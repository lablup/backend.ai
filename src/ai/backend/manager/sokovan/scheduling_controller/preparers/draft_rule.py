"""Draft-based preparer rule interface.

Each rule is a pure async function of ``(draft, context) -> draft``
that the :class:`SessionSpecPreparer` chains in declaration order. A
rule receives an immutable :class:`SessionSpecDraft` and returns a new
one via ``model_copy`` with additional fields resolved — never
mutating the input::

    draft_0 --rule_1--> draft_1 --rule_2--> ... --rule_N--> draft_final

Finalization (projecting the final draft into a
:class:`~ai.backend.manager.data.session.spec.SessionSpec`) is owned
by the preparer, not the rule surface — see
:class:`.session_spec_preparer.SessionSpecPreparer`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ai.backend.manager.data.session.draft import SessionResourceSpecDraft
from ai.backend.manager.repositories.scheduler.types.session_creation import SessionSpecContext


class SessionSpecDraftRule(ABC):
    """Abstract base for draft-based preparer rules.

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
        draft: SessionResourceSpecDraft,
        context: SessionSpecContext,
    ) -> SessionResourceSpecDraft:
        """Return a new draft with this rule's fields resolved."""
        raise NotImplementedError
