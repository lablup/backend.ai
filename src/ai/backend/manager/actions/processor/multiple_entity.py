import asyncio
import uuid
from datetime import datetime
from typing import Awaitable, Callable, Generic, Optional

from ai.backend.common.exception import BackendAIError, ErrorCode
from ai.backend.manager.actions.types import OperationStatus
from ai.backend.manager.data.permission.id import (
    ObjectId,
)
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)

from ..action.multiple_entity import (
    TBaseMultiEntityAction,
    TBaseMultiEntityActionResult,
)
from ..monitors.monitor import ActionMonitor
from ..types import ActionResultMeta, ActionTargetMeta, ActionTriggerMeta, ProcessResult


class ActionProcessor(Generic[TBaseMultiEntityAction, TBaseMultiEntityActionResult]):
    _monitors: list[ActionMonitor]
    _repository: PermissionControllerRepository
    _func: Callable[[TBaseMultiEntityAction], Awaitable[TBaseMultiEntityActionResult]]

    def __init__(
        self,
        func: Callable[[TBaseMultiEntityAction], Awaitable[TBaseMultiEntityActionResult]],
        permission_control_repository: PermissionControllerRepository,
        monitors: Optional[list[ActionMonitor]] = None,
    ) -> None:
        self._func = func
        self._monitors = monitors or []
        self._repository = permission_control_repository

    async def _run(self, action: TBaseMultiEntityAction) -> TBaseMultiEntityActionResult:
        started_at = datetime.now()
        status = OperationStatus.UNKNOWN
        description: str = "unknown"
        result: Optional[TBaseMultiEntityActionResult] = None
        error_code: Optional[ErrorCode] = None
        object_ids: list[ObjectId] = []

        action_id = uuid.uuid4()
        action_trigger_meta = ActionTriggerMeta(action_id=action_id, started_at=started_at)
        for monitor in self._monitors:
            await monitor.prepare(action, action_trigger_meta)

        try:
            permission_params = action.permission_query_params()
            object_ids = await self._repository.get_allowed_entity_ids(permission_params)
            action.accessible_entity_ids = object_ids
            result = await self._func(action)
            status = OperationStatus.SUCCESS
            description = "Success"
            return result
        except BackendAIError as e:
            status = OperationStatus.ERROR
            description = str(e)
            error_code = e.error_code()
            raise
        except BaseException as e:
            status = OperationStatus.ERROR
            description = str(e)
            error_code = ErrorCode.default()
            raise
        finally:
            ended_at = datetime.now()
            duration = ended_at - started_at
            entity_ids = action.target_entity_ids()
            if not entity_ids and result is not None:
                entity_ids = result.entity_ids()
            meta = ActionResultMeta(
                action_id=action_id,
                target=ActionTargetMeta(
                    entity_type=action.entity_type(),
                    entity_ids=entity_ids,
                ),
                status=status,
                description=description,
                started_at=started_at,
                ended_at=ended_at,
                duration=duration,
                error_code=error_code,
            )
            process_result = ProcessResult(meta=meta)
            for monitor in reversed(self._monitors):
                await monitor.done(action, process_result)

    async def wait_for_complete(
        self, action: TBaseMultiEntityAction
    ) -> TBaseMultiEntityActionResult:
        return await self._run(action)

    async def fire_and_forget(self, action: TBaseMultiEntityAction) -> None:
        asyncio.create_task(self.wait_for_complete(action))
