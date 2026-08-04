"""Holds what every processor is built from, so a domain names no monitor or validator.

Method names are ``<shape>_<operation>``. The per-operation ``validators`` / ``monitors``
arguments only append — what the shape carries is always applied.
"""

from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass

from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.v2.bulk.base import BaseBulkAction
from ai.backend.manager.actions.v2.bulk.monitor import BulkActionMonitor
from ai.backend.manager.actions.v2.bulk.processor import BulkActionProcessor
from ai.backend.manager.actions.v2.bulk.result import BaseBulkActionResult
from ai.backend.manager.actions.v2.bulk.validator import BulkActionValidator
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.actions.v2.global_scope.monitor import GlobalActionMonitor
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.global_scope.validator import GlobalActionValidator
from ai.backend.manager.actions.v2.lookup.base import BaseLookupAction, BaseLookupActionResult
from ai.backend.manager.actions.v2.lookup.monitor import LookupActionMonitor
from ai.backend.manager.actions.v2.lookup.processor import LookupActionProcessor
from ai.backend.manager.actions.v2.lookup.validator import LookupActionValidator
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.scope.monitor import ScopeActionMonitor
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor
from ai.backend.manager.actions.v2.scope.result import BaseScopeActionResult
from ai.backend.manager.actions.v2.scope.validator import ScopeActionValidator
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.actions.v2.single_entity.monitor import SingleEntityActionMonitor
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
from ai.backend.manager.actions.v2.single_entity.validator import SingleEntityActionValidator
from ai.backend.manager.actions.v2.validators import ActionValidators
from ai.backend.manager.repositories.ops.repository import OpsRepository

__all__ = (
    "ProcessorDependencies",
    "ProcessorGroup",
    "ProcessorRegistry",
)


@dataclass(frozen=True)
class ProcessorDependencies[TData]:
    monitors: ActionMonitors
    validators: ActionValidators
    repository: OpsRepository[TData]


class ProcessorGroup[TData]:
    _deps: ProcessorDependencies[TData]

    def __init__(self, deps: ProcessorDependencies[TData]) -> None:
        self._deps = deps

    def _single_entity[TAction: BaseSingleEntityAction, TResult](
        self,
        func: Callable[[TAction], Awaitable[TResult]],
        validators: Sequence[SingleEntityActionValidator],
        monitors: Sequence[SingleEntityActionMonitor],
    ) -> SingleEntityActionProcessor[TAction, TResult]:
        return SingleEntityActionProcessor(
            func,
            monitors=(*self._deps.monitors.single_entity, *monitors),
            validators=(*self._deps.validators.single_entity, *validators),
        )

    def single_get[TAction: BaseSingleEntityAction, TResult](
        self,
        func: Callable[[TAction], Awaitable[TResult]],
        *,
        validators: Sequence[SingleEntityActionValidator] = (),
        monitors: Sequence[SingleEntityActionMonitor] = (),
    ) -> SingleEntityActionProcessor[TAction, TResult]:
        return self._single_entity(func, validators, monitors)

    def single_update[TAction: BaseSingleEntityAction, TResult](
        self,
        func: Callable[[TAction], Awaitable[TResult]],
        *,
        validators: Sequence[SingleEntityActionValidator] = (),
        monitors: Sequence[SingleEntityActionMonitor] = (),
    ) -> SingleEntityActionProcessor[TAction, TResult]:
        return self._single_entity(func, validators, monitors)

    def single_delete[TAction: BaseSingleEntityAction, TResult](
        self,
        func: Callable[[TAction], Awaitable[TResult]],
        *,
        validators: Sequence[SingleEntityActionValidator] = (),
        monitors: Sequence[SingleEntityActionMonitor] = (),
    ) -> SingleEntityActionProcessor[TAction, TResult]:
        return self._single_entity(func, validators, monitors)

    def single_purge[TAction: BaseSingleEntityAction, TResult](
        self,
        func: Callable[[TAction], Awaitable[TResult]],
        *,
        validators: Sequence[SingleEntityActionValidator] = (),
        monitors: Sequence[SingleEntityActionMonitor] = (),
    ) -> SingleEntityActionProcessor[TAction, TResult]:
        return self._single_entity(func, validators, monitors)

    def _scope[TAction: BaseScopeAction, TResult: BaseScopeActionResult](
        self,
        func: Callable[[TAction], Awaitable[TResult]],
        validators: Sequence[ScopeActionValidator],
        monitors: Sequence[ScopeActionMonitor],
    ) -> ScopeActionProcessor[TAction, TResult]:
        return ScopeActionProcessor(
            func,
            monitors=(*self._deps.monitors.scope, *monitors),
            validators=(*self._deps.validators.scope, *validators),
        )

    def scope_get[TAction: BaseScopeAction, TResult: BaseScopeActionResult](
        self,
        func: Callable[[TAction], Awaitable[TResult]],
        *,
        validators: Sequence[ScopeActionValidator] = (),
        monitors: Sequence[ScopeActionMonitor] = (),
    ) -> ScopeActionProcessor[TAction, TResult]:
        return self._scope(func, validators, monitors)

    def scope_create[TAction: BaseScopeAction, TResult: BaseScopeActionResult](
        self,
        func: Callable[[TAction], Awaitable[TResult]],
        *,
        validators: Sequence[ScopeActionValidator] = (),
        monitors: Sequence[ScopeActionMonitor] = (),
    ) -> ScopeActionProcessor[TAction, TResult]:
        return self._scope(func, validators, monitors)

    def scope_search[TAction: BaseScopeAction, TResult: BaseScopeActionResult](
        self,
        func: Callable[[TAction], Awaitable[TResult]],
        *,
        validators: Sequence[ScopeActionValidator] = (),
        monitors: Sequence[ScopeActionMonitor] = (),
    ) -> ScopeActionProcessor[TAction, TResult]:
        return self._scope(func, validators, monitors)

    def scope_update[TAction: BaseScopeAction, TResult: BaseScopeActionResult](
        self,
        func: Callable[[TAction], Awaitable[TResult]],
        *,
        validators: Sequence[ScopeActionValidator] = (),
        monitors: Sequence[ScopeActionMonitor] = (),
    ) -> ScopeActionProcessor[TAction, TResult]:
        return self._scope(func, validators, monitors)

    def scope_delete[TAction: BaseScopeAction, TResult: BaseScopeActionResult](
        self,
        func: Callable[[TAction], Awaitable[TResult]],
        *,
        validators: Sequence[ScopeActionValidator] = (),
        monitors: Sequence[ScopeActionMonitor] = (),
    ) -> ScopeActionProcessor[TAction, TResult]:
        return self._scope(func, validators, monitors)

    def scope_purge[TAction: BaseScopeAction, TResult: BaseScopeActionResult](
        self,
        func: Callable[[TAction], Awaitable[TResult]],
        *,
        validators: Sequence[ScopeActionValidator] = (),
        monitors: Sequence[ScopeActionMonitor] = (),
    ) -> ScopeActionProcessor[TAction, TResult]:
        return self._scope(func, validators, monitors)

    def _bulk[TAction: BaseBulkAction, TResult: BaseBulkActionResult](
        self,
        func: Callable[[TAction], Awaitable[TResult]],
        validators: Sequence[BulkActionValidator],
        monitors: Sequence[BulkActionMonitor],
    ) -> BulkActionProcessor[TAction, TResult]:
        return BulkActionProcessor(
            func,
            monitors=(*self._deps.monitors.bulk, *monitors),
            validators=(*self._deps.validators.bulk, *validators),
        )

    def bulk_update[TAction: BaseBulkAction, TResult: BaseBulkActionResult](
        self,
        func: Callable[[TAction], Awaitable[TResult]],
        *,
        validators: Sequence[BulkActionValidator] = (),
        monitors: Sequence[BulkActionMonitor] = (),
    ) -> BulkActionProcessor[TAction, TResult]:
        return self._bulk(func, validators, monitors)

    def bulk_delete[TAction: BaseBulkAction, TResult: BaseBulkActionResult](
        self,
        func: Callable[[TAction], Awaitable[TResult]],
        *,
        validators: Sequence[BulkActionValidator] = (),
        monitors: Sequence[BulkActionMonitor] = (),
    ) -> BulkActionProcessor[TAction, TResult]:
        return self._bulk(func, validators, monitors)

    def bulk_purge[TAction: BaseBulkAction, TResult: BaseBulkActionResult](
        self,
        func: Callable[[TAction], Awaitable[TResult]],
        *,
        validators: Sequence[BulkActionValidator] = (),
        monitors: Sequence[BulkActionMonitor] = (),
    ) -> BulkActionProcessor[TAction, TResult]:
        return self._bulk(func, validators, monitors)

    def _global[TAction: BaseGlobalAction, TResult](
        self,
        func: Callable[[TAction], Awaitable[TResult]],
        validators: Sequence[GlobalActionValidator],
        monitors: Sequence[GlobalActionMonitor],
    ) -> GlobalActionProcessor[TAction, TResult]:
        return GlobalActionProcessor(
            func,
            monitors=(*self._deps.monitors.global_scope, *monitors),
            validators=(*self._deps.validators.global_scope, *validators),
        )

    def global_create[TAction: BaseGlobalAction, TResult](
        self,
        func: Callable[[TAction], Awaitable[TResult]],
        *,
        validators: Sequence[GlobalActionValidator] = (),
        monitors: Sequence[GlobalActionMonitor] = (),
    ) -> GlobalActionProcessor[TAction, TResult]:
        return self._global(func, validators, monitors)

    def global_search[TAction: BaseGlobalAction, TResult](
        self,
        func: Callable[[TAction], Awaitable[TResult]],
        *,
        validators: Sequence[GlobalActionValidator] = (),
        monitors: Sequence[GlobalActionMonitor] = (),
    ) -> GlobalActionProcessor[TAction, TResult]:
        return self._global(func, validators, monitors)

    def lookup[TAction: BaseLookupAction, TResult: BaseLookupActionResult](
        self,
        func: Callable[[TAction], Awaitable[TResult]],
        *,
        validators: Sequence[LookupActionValidator] = (),
        monitors: Sequence[LookupActionMonitor] = (),
    ) -> LookupActionProcessor[TAction, TResult]:
        return LookupActionProcessor(
            func,
            monitors=(*self._deps.monitors.lookup, *monitors),
            validators=(*self._deps.validators.lookup, *validators),
        )


class ProcessorRegistry[TData]:
    _deps: ProcessorDependencies[TData]

    def __init__(self, deps: ProcessorDependencies[TData]) -> None:
        self._deps = deps

    def group(self) -> ProcessorGroup[TData]:
        return ProcessorGroup(self._deps)
