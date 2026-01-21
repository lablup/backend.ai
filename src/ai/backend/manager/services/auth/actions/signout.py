import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.auth.actions.base import AuthAction


@dataclass
class SignoutAction(AuthAction):
    user_id: uuid.UUID
    domain_name: str
    requester_email: str
    email: str
    password: str

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.user_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "signout"


@dataclass
class SignoutActionResult(BaseActionResult):
    success: bool

    @override
    def entity_id(self) -> Optional[str]:
        return None
