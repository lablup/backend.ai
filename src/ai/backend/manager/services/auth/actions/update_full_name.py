from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.auth.actions.base import AuthAction


@dataclass
class UpdateFullNameAction(AuthAction):
    user_id: str
    full_name: str
    domain_name: str
    email: str

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.user_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "update_full_name"


@dataclass
class UpdateFullNameActionResult(BaseActionResult):
    success: bool

    @override
    def entity_id(self) -> Optional[str]:
        return None
