from dataclasses import dataclass
from typing import override

from ai.backend.common.types import AbuseReport, AccessKey
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.session.types import SessionData
from ai.backend.manager.services.session.base import SessionAction


@dataclass
class GetAbusingReportAction(SessionAction):
    session_name: str
    owner_access_key: AccessKey

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_abusing_report"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetAbusingReportActionResult:
    abuse_report: AbuseReport | None
    session_data: SessionData
