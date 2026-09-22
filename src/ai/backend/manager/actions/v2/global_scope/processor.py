import logging
import uuid
from collections.abc import Awaitable, Callable, Sequence
from datetime import UTC, datetime

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.actions.run_status import ActionRunStatus
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.actions.v2.global_scope.monitor import GlobalActionMonitor
from ai.backend.manager.actions.v2.global_scope.result import (
    GlobalActionProcessResult,
    GlobalActionResultMeta,
)
from ai.backend.manager.actions.v2.global_scope.validator import (
    AuthenticatedActionValidator,
    GlobalActionValidator,
)
from ai.backend.manager.actions.v2.trigger import ActionTriggerMeta
from ai.backend.manager.errors.common import ServerMisconfiguredError

__all__ = (
    "AnonymousGlobalActionProcessor",
    "GlobalActionProcessor",
    "PublicActionProcessor",
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class GlobalActionProcessor[TAction: BaseGlobalAction, TResult]:
    """Validate, run monitors around, then execute a global action.

    Each registered validator runs first, then the action within the monitor lifecycle.
    The gate is the one the wiring supplies, as it is for a scope action: the `global`
    singleton answers for the action's entity type.

    The constructor refuses an empty validator list, so a wiring that states no gate
    fails where it is made rather than running ungated at request time. A tool that only
    reads the wiring states :class:`RefusingGlobalActionValidator`.
    """

    _func: Callable[[TAction], Awaitable[TResult]]
    _monitors: Sequence[GlobalActionMonitor]
    _validators: Sequence[GlobalActionValidator]

    def __init__(
        self,
        func: Callable[[TAction], Awaitable[TResult]],
        monitors: Sequence[GlobalActionMonitor] | None = None,
        validators: Sequence[GlobalActionValidator] | None = None,
    ) -> None:
        if not validators:
            raise ServerMisconfiguredError(
                "A global processor states at least one validator; this one states none."
            )
        self._func = func
        self._monitors = monitors or []
        self._validators = validators

    async def _prepare_monitors(self, action: TAction, trigger_meta: ActionTriggerMeta) -> None:
        for monitor in self._monitors:
            try:
                await monitor.prepare(action, trigger_meta)
            except Exception as e:
                log.warning("Error in monitor prepare method: {}", e)

    async def _finalize_monitors(self, action: TAction, meta: GlobalActionResultMeta) -> None:
        process_result = GlobalActionProcessResult(meta=meta)
        for monitor in reversed(self._monitors):
            try:
                await monitor.done(action, process_result)
            except Exception as e:
                log.warning("Error in monitor done method: {}", e)

    async def run(self, action: TAction) -> TResult:
        started_at = datetime.now(UTC)
        action_id = uuid.uuid4()
        trigger_meta = ActionTriggerMeta(action_id=action_id, started_at=started_at)

        run_status = ActionRunStatus.unknown()

        # Validation runs inside the monitor lifecycle so a rejected action is
        # recorded too; monitors that only wrapped execution missed every denial.
        await self._prepare_monitors(action, trigger_meta)
        try:
            try:
                for validator in self._validators:
                    await validator.validate(action, trigger_meta)
            except BaseException as e:
                run_status = ActionRunStatus.of_failure(e, during_validation=True)
                raise
            try:
                result = await self._func(action)
            except BaseException as e:
                run_status = ActionRunStatus.of_failure(e, during_validation=False)
                raise
            else:
                run_status = ActionRunStatus.success()
                return result
        finally:
            ended_at = datetime.now(UTC)
            meta = GlobalActionResultMeta(
                action_id=action_id,
                status=run_status.status,
                description=run_status.description,
                started_at=started_at,
                ended_at=ended_at,
                duration=ended_at - started_at,
                error_code=run_status.error_code,
            )
            await self._finalize_monitors(action, meta)


class PublicActionProcessor[TAction: BaseGlobalAction, TResult]:
    """Validate authentication only, run monitors around, then execute a global read.

    The counterpart of :class:`GlobalActionProcessor` for global state everyone may
    read — the global gate is replaced by an authentication check, and nothing
    else. The action shape stays ``BaseGlobalAction``, so the global monitor set
    (audit, reporter, prometheus) applies unchanged.

    "Public" means every authenticated user, not anonymous access: unlike the REST
    v2 ``/public/`` URL segment, which marks routes with no auth middleware, this
    path always demands a caller identity.

    Only reads may run without the gate, and the constructor enforces it: wiring an
    action whose ``operation_type()`` is not a read operation fails immediately, so
    a write can never reach the public path by miswiring.
    """

    _func: Callable[[TAction], Awaitable[TResult]]
    _monitors: Sequence[GlobalActionMonitor]
    _validators: Sequence[GlobalActionValidator]

    def __init__(
        self,
        action_cls: type[TAction],
        func: Callable[[TAction], Awaitable[TResult]],
        monitors: Sequence[GlobalActionMonitor] | None = None,
        validators: Sequence[GlobalActionValidator] | None = None,
    ) -> None:
        operation_type = action_cls.operation_type()
        if operation_type not in ActionOperationType.read_operations():
            raise ServerMisconfiguredError(
                f"{action_cls.__name__} declares operation_type()={operation_type}, "
                "but the public path only accepts read actions."
            )
        self._func = func
        self._monitors = monitors or []
        self._validators = [AuthenticatedActionValidator(), *(validators or [])]

    async def _prepare_monitors(self, action: TAction, trigger_meta: ActionTriggerMeta) -> None:
        for monitor in self._monitors:
            try:
                await monitor.prepare(action, trigger_meta)
            except Exception as e:
                log.warning("Error in monitor prepare method: {}", e)

    async def _finalize_monitors(self, action: TAction, meta: GlobalActionResultMeta) -> None:
        process_result = GlobalActionProcessResult(meta=meta)
        for monitor in reversed(self._monitors):
            try:
                await monitor.done(action, process_result)
            except Exception as e:
                log.warning("Error in monitor done method: {}", e)

    async def run(self, action: TAction) -> TResult:
        started_at = datetime.now(UTC)
        action_id = uuid.uuid4()
        trigger_meta = ActionTriggerMeta(action_id=action_id, started_at=started_at)

        run_status = ActionRunStatus.unknown()

        # Same lifecycle as the global processor: validation runs inside the monitor
        # lifecycle so a rejected action is recorded too.
        await self._prepare_monitors(action, trigger_meta)
        try:
            try:
                for validator in self._validators:
                    await validator.validate(action, trigger_meta)
            except BaseException as e:
                run_status = ActionRunStatus.of_failure(e, during_validation=True)
                raise
            try:
                result = await self._func(action)
            except BaseException as e:
                run_status = ActionRunStatus.of_failure(e, during_validation=False)
                raise
            else:
                run_status = ActionRunStatus.success()
                return result
        finally:
            ended_at = datetime.now(UTC)
            meta = GlobalActionResultMeta(
                action_id=action_id,
                status=run_status.status,
                description=run_status.description,
                started_at=started_at,
                ended_at=ended_at,
                duration=ended_at - started_at,
                error_code=run_status.error_code,
            )
            await self._finalize_monitors(action, meta)


class AnonymousGlobalActionProcessor[TAction: BaseGlobalAction, TResult]:
    """Run a global action with no gate at all, not even an authentication check.

    Discouraged: prefer any gated path. Reach for this only when the caller can never
    hold a principal -- an external system posting to a webhook -- and the operation
    authenticates that caller itself, inside the service, against a secret the entity
    stores. Nothing here verifies that it does.

    Unlike ``anonymous_scope``, writes are allowed, so a miswiring exposes one. The
    catalog records the wiring as an anonymous gate, which is what makes the set of
    ungated writes countable.
    """

    _func: Callable[[TAction], Awaitable[TResult]]
    _monitors: Sequence[GlobalActionMonitor]

    def __init__(
        self,
        func: Callable[[TAction], Awaitable[TResult]],
        monitors: Sequence[GlobalActionMonitor] | None = None,
    ) -> None:
        self._func = func
        self._monitors = monitors or []

    async def _prepare_monitors(self, action: TAction, trigger_meta: ActionTriggerMeta) -> None:
        for monitor in self._monitors:
            try:
                await monitor.prepare(action, trigger_meta)
            except Exception as e:
                log.warning("Error in monitor prepare method: {}", e)

    async def _finalize_monitors(self, action: TAction, meta: GlobalActionResultMeta) -> None:
        process_result = GlobalActionProcessResult(meta=meta)
        for monitor in reversed(self._monitors):
            try:
                await monitor.done(action, process_result)
            except Exception as e:
                log.warning("Error in monitor done method: {}", e)

    async def run(self, action: TAction) -> TResult:
        started_at = datetime.now(UTC)
        action_id = uuid.uuid4()
        trigger_meta = ActionTriggerMeta(action_id=action_id, started_at=started_at)

        run_status = ActionRunStatus.unknown()

        await self._prepare_monitors(action, trigger_meta)
        try:
            try:
                result = await self._func(action)
            except BaseException as e:
                run_status = ActionRunStatus.of_failure(e, during_validation=False)
                raise
            else:
                run_status = ActionRunStatus.success()
                return result
        finally:
            ended_at = datetime.now(UTC)
            meta = GlobalActionResultMeta(
                action_id=action_id,
                status=run_status.status,
                description=run_status.description,
                started_at=started_at,
                ended_at=ended_at,
                duration=ended_at - started_at,
                error_code=run_status.error_code,
            )
            await self._finalize_monitors(action, meta)
