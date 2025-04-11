import enum
import logging
from dataclasses import dataclass
from typing import Final, override

from ai.backend.logging.utils import BraceStyleAdapter

from ...actions.action import BaseAction, BaseActionTriggerMeta, ProcessResult
from .monitor import ActionMonitor

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


UNKNOWN_ENTITY_ID: Final[str] = "(unknown)"


class SMTPTriggerPolicy(enum.Flag):
    PRE_ACTION = enum.auto()
    POST_ACTION = enum.auto()
    ON_ERROR = enum.auto()


@dataclass
class SMTPMonitorArgs:
    trigger_policy: SMTPTriggerPolicy


class SMTPMonitor(ActionMonitor):
    _trigger_policy: SMTPTriggerPolicy

    def __init__(self, args: SMTPMonitorArgs) -> None:
        self._trigger_policy = args.trigger_policy

    @override
    async def prepare(self, action: BaseAction, meta: BaseActionTriggerMeta) -> None:
        if SMTPTriggerPolicy.PRE_ACTION in self._trigger_policy:
            pass

    @override
    async def done(self, action: BaseAction, result: ProcessResult) -> None:
        if SMTPTriggerPolicy.ON_ERROR in self._trigger_policy:
            pass
        if SMTPTriggerPolicy.POST_ACTION in self._trigger_policy:
            pass
