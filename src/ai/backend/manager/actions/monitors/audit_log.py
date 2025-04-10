import logging
import uuid
from typing import Final, override

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.actions.action import BaseAction, BaseActionTriggerMeta, ProcessResult
from ai.backend.manager.actions.monitors.monitor import ActionMonitor

NULL_UUID: Final[uuid.UUID] = uuid.UUID("00000000-0000-0000-0000-000000000000")
UNKNOWN_ENTITY_ID: Final[str] = "(unknown)"


NULL_UUID: Final[uuid.UUID] = uuid.UUID("00000000-0000-0000-0000-000000000000")
UNKNOWN_ENTITY_ID: Final[str] = "(unknown)"


log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class AuditLogMonitor(ActionMonitor):
    def __init__(self) -> None:
        pass

    @override
    async def prepare(self, action: BaseAction, meta: BaseActionTriggerMeta) -> None:
        pass

    @override
    async def done(self, action: BaseAction, result: ProcessResult) -> None:
        pass
