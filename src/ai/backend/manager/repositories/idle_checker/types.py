"""Repository result types that carry the typed (model-layer) checker spec."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime

from ai.backend.common.identifier.idle_checker import IdleCheckerID
from ai.backend.common.types import SessionId
from ai.backend.manager.data.idle_checker.types import CheckerType, IdleCheckSessionView, ScopeRef
from ai.backend.manager.models.idle_checker.spec import IdleCheckerSpecABC


@dataclass(frozen=True)
class IdleCheckerRef:
    """A bound idle checker definition with its typed, loaded spec."""

    checker_id: IdleCheckerID
    checker_type: CheckerType
    spec: IdleCheckerSpecABC


@dataclass(frozen=True)
class IdleCheckerBindingRef:
    """One enabled scope binding for an idle checker.

    ``binding_created_at`` is the stable tiebreak within a scope.
    """

    binding_created_at: datetime
    checker_id: IdleCheckerID


@dataclass(frozen=True)
class IdleCheckSnapshot:
    """Normalized idle-check source data.

    Session views carry their applicable scopes, scopes reference their checker bindings, and
    checker specs are loaded once by id.
    """

    session_views_by_id: Mapping[SessionId, IdleCheckSessionView]
    bindings_by_scope: Mapping[ScopeRef, Sequence[IdleCheckerBindingRef]]
    checkers_by_id: Mapping[IdleCheckerID, IdleCheckerRef]
