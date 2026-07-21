import logging
import uuid
from collections.abc import Awaitable, Callable, Sequence
from datetime import UTC, datetime

from ai.backend.common.exception import BackendAIError, ErrorCode
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.scope.base import BaseScopeAction
from ai.backend.manager.actions.scope.monitor import ScopeActionMonitor
from ai.backend.manager.actions.scope.result import (
    ScopeActionProcessResult,
    ScopeActionResultMeta,
)
from ai.backend.manager.actions.scope.validator import ScopeActionValidator
from ai.backend.manager.actions.types import OperationStatus

__all__ = ("ScopeActionProcessor",)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ScopeActionProcessor[TAction: BaseScopeAction, TResult]:
    """Validate, run monitors around, then execute a scope action.

    Each registered validator runs first. The action function then executes within a
    monitor lifecycle: every monitor's ``prepare`` is called before, and ``done`` after
    (on success or failure), with status / timing / error captured into a
    :class:`ScopeActionProcessResult`. This path depends only on the pure-ABC
    :class:`BaseScopeAction`, never on the legacy ``BaseAction`` framework.
    """

    _func: Callable[[TAction], Awaitable[TResult]]
    _monitors: Sequence[ScopeActionMonitor]
    _validators: Sequence[ScopeActionValidator]

    def __init__(
        self,
        func: Callable[[TAction], Awaitable[TResult]],
        monitors: Sequence[ScopeActionMonitor] | None = None,
        validators: Sequence[ScopeActionValidator] | None = None,
    ) -> None:
        self._func = func
        self._monitors = monitors or []
        self._validators = validators or []

    async def _prepare_monitors(self, action: TAction, trigger_meta: BaseActionTriggerMeta) -> None:
        for monitor in self._monitors:
            try:
                await monitor.prepare(action, trigger_meta)
            except Exception as e:
                log.warning("Error in monitor prepare method: {}", e)

    async def _finalize_monitors(self, action: TAction, meta: ScopeActionResultMeta) -> None:
        process_result = ScopeActionProcessResult(meta=meta)
        for monitor in reversed(self._monitors):
            try:
                await monitor.done(action, process_result)
            except Exception as e:
                log.warning("Error in monitor done method: {}", e)

    async def run(self, action: TAction) -> TResult:
        started_at = datetime.now(UTC)
        action_id = uuid.uuid4()
        trigger_meta = BaseActionTriggerMeta(action_id=action_id, started_at=started_at)

        for validator in self._validators:
            await validator.validate(action, trigger_meta)

        status = OperationStatus.UNKNOWN
        description = "unknown"
        error_code: ErrorCode | None = None

        await self._prepare_monitors(action, trigger_meta)
        try:
            result = await self._func(action)
        except BackendAIError as e:
            log.exception("Action processing error: {}", e)
            status = OperationStatus.ERROR
            description = str(e)
            error_code = e.error_code()
            raise
        except BaseException as e:
            log.exception("Unexpected error during action processing: {}", e)
            status = OperationStatus.ERROR
            description = str(e)
            error_code = ErrorCode.default()
            raise
        else:
            status = OperationStatus.SUCCESS
            description = "Success"
            return result
        finally:
            ended_at = datetime.now(UTC)
            meta = ScopeActionResultMeta(
                action_id=action_id,
                scope_targets=action.scope_targets(),
                status=status,
                description=description,
                started_at=started_at,
                ended_at=ended_at,
                duration=ended_at - started_at,
                error_code=error_code,
            )
            await self._finalize_monitors(action, meta)
