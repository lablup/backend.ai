"""The group a link between two entities is wired through.

Apart from :class:`~.group.ProcessorGroup` because that group is answered for by an
entity type and a relation is answered for by neither of the two it names. It takes no
meta: there is nothing for one to carry.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence
from typing import Any

from ai.backend.manager.actions.registry.types import (
    ProcessorDependencies,
    WiredProcessor,
)
from ai.backend.manager.actions.types import ActionBacking, ActionGate, ActionKind
from ai.backend.manager.actions.v2.relation.base import BaseRelationAction
from ai.backend.manager.actions.v2.relation.monitor import RelationActionMonitor
from ai.backend.manager.actions.v2.relation.processor import RelationActionProcessor
from ai.backend.manager.actions.v2.relation.validator import RelationActionValidator

__all__ = ("RelationGroup",)


class RelationGroup:
    """The relation operations of one area."""

    _deps: ProcessorDependencies[Any]
    _records: list[WiredProcessor]
    _concern: str

    def __init__(
        self,
        deps: ProcessorDependencies[Any],
        records: list[WiredProcessor],
        concern: str,
    ) -> None:
        self._deps = deps
        self._records = records
        self._concern = concern

    def relation[TAction: BaseRelationAction, TResult](
        self,
        action_cls: type[TAction],
        func: Callable[[TAction], Awaitable[TResult]],
        *,
        validators: Sequence[RelationActionValidator] = (),
        monitors: Sequence[RelationActionMonitor] = (),
    ) -> RelationActionProcessor[TAction, TResult]:
        """A link between two entities, or its removal.

        Recorded against no entity type: what it writes is neither of the two, and which
        two it was about is on the run's scopes. The spec travels on the action, so one
        wiring serves every relation.
        """
        self._records.append(
            WiredProcessor(
                concern=self._concern,
                entity_type=None,
                field_type=None,
                action_cls=action_cls,
                kind=ActionKind.RELATION,
                gate=ActionGate.PERMISSION,
                backing=ActionBacking.CUSTOM,
            )
        )
        return RelationActionProcessor(
            func,
            monitors=(*self._deps.monitors.relation, *monitors),
            validators=(*self._deps.validators.relation, *validators),
        )
