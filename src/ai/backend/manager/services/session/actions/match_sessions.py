from dataclasses import dataclass
from typing import Any, Optional, override

from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.session.base import SessionAction


# TODO: Make this BatchAction
@dataclass
class MatchSessionsAction(SessionAction):
    id_or_name_prefix: str
    owner_access_key: AccessKey

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "match_multi"


@dataclass
class MatchSessionsActionResult(BaseActionResult):
    # TODO: Add proper type
    result: Any
    # session_rows: list[SessionRow]

    @override
    def entity_id(self) -> Optional[str]:
        return None
