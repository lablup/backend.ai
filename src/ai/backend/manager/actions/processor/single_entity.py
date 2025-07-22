import asyncio
import uuid
from datetime import datetime
from typing import Awaitable, Callable, Generic, Optional

from ai.backend.common.exception import BackendAIError, ErrorCode
from ai.backend.manager.actions.types import OperationStatus
from ai.backend.manager.data.permission.id import (
    ObjectId,
)
from ai.backend.manager.errors.common import PermissionDeniedError
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)

from ..action.single_entity import (
    TSingleEntityAction,
    TSingleEntityActionResult,
)
from ..monitors.monitor import ActionMonitor
from ..types import ActionResultMeta, ActionTargetMeta, ActionTriggerMeta, ProcessResult


class ActionProcessor(Generic[TSingleEntityAction, TSingleEntityActionResult]):
    _monitors: list[ActionMonitor]
    _repository: PermissionControllerRepository
    _func: Callable[[TSingleEntityAction], Awaitable[TSingleEntityActionResult]]

    def __init__(
        self,
        func: Callable[[TSingleEntityAction], Awaitable[TSingleEntityActionResult]],
        permission_control_repository: PermissionControllerRepository,
        monitors: Optional[list[ActionMonitor]] = None,
    ) -> None:
        self._func = func
        self._monitors = monitors or []
        self._repository = permission_control_repository

    async def _run(self, action: TSingleEntityAction) -> TSingleEntityActionResult:
        started_at = datetime.now()
        status = OperationStatus.UNKNOWN
        description: str = "unknown"
        result: Optional[TSingleEntityActionResult] = None
        error_code: Optional[ErrorCode] = None
        object_id: Optional[ObjectId] = None

        action_id = uuid.uuid4()
        action_trigger_meta = ActionTriggerMeta(action_id=action_id, started_at=started_at)
        for monitor in self._monitors:
            await monitor.prepare(action, action_trigger_meta)

        try:
            permission_params = action.permission_query_params()
            object_id = await self._repository.get_allowed_single_entity(permission_params)
            if object_id is None:
                raise PermissionDeniedError
            action.accessible_entity_id = object_id
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
            entity_id = action.entity_id()
            if entity_id is None and result is not None:
                entity_id = result.entity_id()
            meta = ActionResultMeta(
                action_id=action_id,
                target=ActionTargetMeta(
                    entity_type=action.entity_type(),
                    entity_ids=[entity_id] if entity_id else None,
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

    async def wait_for_complete(self, action: TSingleEntityAction) -> TSingleEntityActionResult:
        return await self._run(action)

    async def fire_and_forget(self, action: TSingleEntityAction) -> None:
        asyncio.create_task(self.wait_for_complete(action))
