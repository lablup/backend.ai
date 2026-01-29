from dataclasses import dataclass
from typing import override

from ai.backend.common.types import AbuseReport, AccessKey
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.session.types import SessionData
from ai.backend.manager.services.session.base import SessionAction


@dataclass
class GetAbusingReportAction(SessionAction):
    session_name: str
    owner_access_key: AccessKey

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "get_abusing_report"


@dataclass
class GetAbusingReportActionResult(BaseActionResult):
    abuse_report: AbuseReport | None
    session_data: SessionData

    @override
    def entity_id(self) -> str | None:
        return str(self.session_data.id)
