"""The reads over one kind of sidecar row."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from ai.backend.manager.actions.registry.types import (
    ProcessorDependencies,
    SidecarGroupMeta,
    WiredProcessor,
)
from ai.backend.manager.actions.types import (
    ActionBacking,
    ActionGate,
    ActionKind,
)
from ai.backend.manager.actions.v2.global_scope.monitor import GlobalActionMonitor
from ai.backend.manager.actions.v2.global_scope.processor import (
    GlobalActionProcessor,
)
from ai.backend.manager.actions.v2.global_scope.validator import GlobalActionValidator
from ai.backend.manager.actions.v2.ops.base import (
    OperationScopeOpsAction,
    SearchGlobalOpsAction,
)
from ai.backend.manager.actions.v2.ops.result import (
    BatchOpsResult,
    ScopedFieldsOpsResult,
)
from ai.backend.manager.actions.v2.scope.monitor import ScopeActionMonitor
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor
from ai.backend.manager.actions.v2.scope.validator import ScopeActionValidator
from ai.backend.manager.services.ops.service import (
    GlobalSearchService,
    SearchFieldsService,
)


class SidecarProcessorGroup[TSidecarData]:
    """The reads over one kind of sidecar row.

    A sidecar stands outside the graph, so there is no create or purge here — those go
    through the repository, which is where the writers of such rows already are. What is
    here is the two reads, and both report no entity: a sidecar row is not one.
    """

    _deps: ProcessorDependencies[Any]
    _records: list[WiredProcessor]
    _concern: str
    _meta: SidecarGroupMeta

    def __init__(
        self,
        deps: ProcessorDependencies[Any],
        records: list[WiredProcessor],
        concern: str,
        meta: SidecarGroupMeta,
    ) -> None:
        self._deps = deps
        self._records = records
        self._concern = concern
        self._meta = meta

    def _record(
        self,
        action_cls: type[Any],
        kind: ActionKind,
        gate: ActionGate,
        backing: ActionBacking,
    ) -> None:
        self._records.append(
            WiredProcessor(
                concern=self._concern,
                entity_type=self._meta.entity_type,
                field_type=None,
                action_cls=action_cls,
                kind=kind,
                gate=gate,
                backing=backing,
            )
        )

    def search_ops[TAction: OperationScopeOpsAction[Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[ScopeActionValidator] = (),
        monitors: Sequence[ScopeActionMonitor] = (),
    ) -> ScopeActionProcessor[TAction, ScopedFieldsOpsResult[TSidecarData]]:
        """A page of the sidecar rows inside the scopes the action names.

        Scope-shaped like every other search that names where it looks, and the scope's
        condition is written against the row's own columns — there is no owner to look up.
        """
        self._record(action_cls, ActionKind.SCOPE, ActionGate.PERMISSION, ActionBacking.OPS)
        return ScopeActionProcessor(
            SearchFieldsService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.scope, *monitors),
            validators=(*self._deps.validators.scope, *validators),
        )

    def global_search_ops[TAction: SearchGlobalOpsAction[Any, Any]](
        self,
        action_cls: type[TAction],
        *,
        validators: Sequence[GlobalActionValidator] = (),
        monitors: Sequence[GlobalActionMonitor] = (),
    ) -> GlobalActionProcessor[TAction, BatchOpsResult[TSidecarData]]:
        """A read across every row of this sidecar type, behind the SUPERADMIN gate.

        For the rows of named scopes use :meth:`search_ops`; this one names none."""
        self._record(action_cls, ActionKind.GLOBAL, ActionGate.PERMISSION, ActionBacking.OPS)
        return GlobalActionProcessor(
            GlobalSearchService(self._deps.repository).execute,
            monitors=(*self._deps.monitors.global_scope, *monitors),
            validators=(*self._deps.validators.global_scope, *validators),
        )
