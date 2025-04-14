import logging
from dataclasses import dataclass
from typing import Final, override

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.types import SMTPTriggerPolicy

from ...actions.action import BaseAction, BaseActionTriggerMeta, ProcessResult
from .monitor import ActionMonitor

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


UNKNOWN_ENTITY_ID: Final[str] = "(unknown)"


@dataclass
class SMTPMonitorArgs:
    trigger_policy: SMTPTriggerPolicy


class SMTPMonitor(ActionMonitor):
    _trigger_policy: SMTPTriggerPolicy

    def __init__(self, args: SMTPMonitorArgs) -> None:
        self._trigger_policy = args.trigger_policy

    @override
    async def prepare(self, action: BaseAction, meta: BaseActionTriggerMeta) -> None:
        pass

    @override
    async def done(self, action: BaseAction, result: ProcessResult) -> None:
        pass
