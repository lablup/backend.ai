"""The group an operation over a concern with no row is wired through.

Apart from :class:`~.group.ProcessorGroup` because that group is answered for by an
entity type and these operations are answered for by none: authentication, the etcd
configuration, the manager itself, the secret store. It takes no meta for the same
reason :class:`~.relation.RelationGroup` takes none — there is nothing for one to
carry.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence
from typing import Any

from ai.backend.manager.actions.registry.types import (
    ProcessorDependencies,
    WiredProcessor,
)
from ai.backend.manager.actions.types import ActionBacking, ActionGate, ActionKind
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.actions.v2.global_scope.monitor import GlobalActionMonitor
from ai.backend.manager.actions.v2.global_scope.processor import (
    AnonymousGlobalActionProcessor,
    GlobalActionProcessor,
    PublicActionProcessor,
)
from ai.backend.manager.actions.v2.global_scope.validator import GlobalActionValidator

__all__ = ("UnownedGroup",)


class UnownedGroup:
    """The operations of one area that name no entity."""

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

    def _record(self, action_cls: type[Any], gate: ActionGate) -> None:
        self._records.append(
            WiredProcessor(
                concern=self._concern,
                entity_type=None,
                field_type=None,
                action_cls=action_cls,
                kind=ActionKind.GLOBAL,
                gate=gate,
                backing=ActionBacking.CUSTOM,
            )
        )

    def global_scope[TAction: BaseGlobalAction, TResult](
        self,
        action_cls: type[TAction],
        func: Callable[[TAction], Awaitable[TResult]],
        *,
        validators: Sequence[GlobalActionValidator] = (),
        monitors: Sequence[GlobalActionMonitor] = (),
    ) -> GlobalActionProcessor[TAction, TResult]:
        self._record(action_cls, ActionGate.PERMISSION)
        return GlobalActionProcessor(
            func,
            monitors=(*self._deps.monitors.global_scope, *monitors),
            validators=(*self._deps.validators.global_scope, *validators),
        )

    def public[TAction: BaseGlobalAction, TResult](
        self,
        action_cls: type[TAction],
        func: Callable[[TAction], Awaitable[TResult]],
        *,
        validators: Sequence[GlobalActionValidator] = (),
        monitors: Sequence[GlobalActionMonitor] = (),
    ) -> PublicActionProcessor[TAction, TResult]:
        """Global state every authenticated caller may read.

        The SUPERADMIN gate is replaced by an authentication check; the constructor
        rejects anything that is not a read, so a write cannot reach this path.
        """
        self._record(action_cls, ActionGate.PUBLIC)
        return PublicActionProcessor(
            action_cls,
            func,
            monitors=(*self._deps.monitors.global_scope, *monitors),
            validators=list(validators),
        )

    def anonymous_global[TAction: BaseGlobalAction, TResult](
        self,
        action_cls: type[TAction],
        func: Callable[[TAction], Awaitable[TResult]],
        *,
        monitors: Sequence[GlobalActionMonitor] = (),
    ) -> AnonymousGlobalActionProcessor[TAction, TResult]:
        """Global state reached with no gate at all, writes included.

        Discouraged: every other factory is a better answer. This one exists for the
        caller that can never hold a principal -- an external system posting to a
        webhook -- where the operation checks that caller itself against a secret the
        entity stores. Nothing here verifies that it does, so read the service before
        wiring one.

        The catalog records the wiring as an anonymous gate, which is how the ungated
        writes stay countable.
        """
        self._record(action_cls, ActionGate.ANONYMOUS)
        return AnonymousGlobalActionProcessor(
            func,
            monitors=(*self._deps.monitors.global_scope, *monitors),
        )
