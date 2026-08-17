import logging
import uuid
from collections.abc import Awaitable, Callable, Sequence
from datetime import UTC, datetime

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.actions.run_status import ActionRunStatus
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.actions.v2.single_entity.monitor import SingleEntityActionMonitor
from ai.backend.manager.actions.v2.single_entity.result import (
    SingleEntityActionProcessResult,
    SingleEntityActionResultMeta,
)
from ai.backend.manager.actions.v2.single_entity.trigger import (
    SingleEntityActionTriggerMeta,
)
from ai.backend.manager.actions.v2.single_entity.validator import SingleEntityActionValidator
from ai.backend.manager.actions.v2.single_entity.validator.authenticated import (
    AuthenticatedActionValidator,
)
from ai.backend.manager.errors.common import ServerMisconfiguredError

__all__ = ("SingleEntityActionProcessor", "PublicSingleEntityActionProcessor")

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class SingleEntityActionProcessor[TAction: BaseSingleEntityAction, TResult]:
    """Validate, run monitors around, then execute a single-entity action.

    Each registered validator runs first. The action function then executes within a
    monitor lifecycle: every monitor's ``prepare`` is called before, and ``done`` after
    (on success or failure), with status / timing / error captured into a
    :class:`ProcessResult`. This path depends only on the pure-ABC
    :class:`BaseSingleEntityAction`, never on the legacy ``BaseAction`` framework.
    """

    _func: Callable[[TAction], Awaitable[TResult]]
    _monitors: Sequence[SingleEntityActionMonitor]
    _validators: Sequence[SingleEntityActionValidator]

    def __init__(
        self,
        func: Callable[[TAction], Awaitable[TResult]],
        monitors: Sequence[SingleEntityActionMonitor] | None = None,
        validators: Sequence[SingleEntityActionValidator] | None = None,
    ) -> None:
        self._func = func
        self._monitors = monitors or []
        self._validators = validators or []

    async def _prepare_monitors(self, trigger_meta: SingleEntityActionTriggerMeta) -> None:
        for monitor in self._monitors:
            try:
                await monitor.prepare(trigger_meta)
            except Exception as e:
                log.warning("Error in monitor prepare method: {}", e)

    async def _finalize_monitors(
        self, trigger_meta: SingleEntityActionTriggerMeta, meta: SingleEntityActionResultMeta
    ) -> None:
        process_result = SingleEntityActionProcessResult(meta=meta)
        for monitor in reversed(self._monitors):
            try:
                await monitor.done(trigger_meta, process_result)
            except Exception as e:
                log.warning("Error in monitor done method: {}", e)

    async def run(self, action: TAction) -> TResult:
        started_at = datetime.now(UTC)
        action_id = uuid.uuid4()
        trigger_meta = SingleEntityActionTriggerMeta(
            action_id=action_id,
            started_at=started_at,
            entity=action.entity_id().entity_ref(),
            operation_type=action.operation_type(),
            action_name=action.action_name(),
        )

        run_status = ActionRunStatus.unknown()

        # Validation runs inside the monitor lifecycle so a rejected action is
        # recorded too; monitors that only wrapped execution missed every denial.
        await self._prepare_monitors(trigger_meta)
        try:
            try:
                for validator in self._validators:
                    await validator.validate(trigger_meta)
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
            meta = SingleEntityActionResultMeta(
                status=run_status.status,
                description=run_status.description,
                ended_at=ended_at,
                duration=ended_at - started_at,
                error_code=run_status.error_code,
            )
            await self._finalize_monitors(trigger_meta, meta)


class PublicSingleEntityActionProcessor[TAction: BaseSingleEntityAction, TResult](
    SingleEntityActionProcessor[TAction, TResult]
):
    """Validate authentication only, then execute a single-entity read.

    The shape stays single-entity, so the audit row still names the id that was read;
    only the RBAC validators are left off. The constructor rejects writes.
    """

    def __init__(
        self,
        action_cls: type[TAction],
        func: Callable[[TAction], Awaitable[TResult]],
        monitors: Sequence[SingleEntityActionMonitor] | None = None,
        validators: Sequence[SingleEntityActionValidator] | None = None,
    ) -> None:
        operation_type = action_cls.operation_type()
        if operation_type not in ActionOperationType.read_operations():
            raise ServerMisconfiguredError(
                f"{action_cls.__name__} declares operation_type()={operation_type}, "
                "but the public path only accepts read actions."
            )
        super().__init__(
            func,
            monitors=monitors,
            validators=[AuthenticatedActionValidator(), *(validators or [])],
        )
