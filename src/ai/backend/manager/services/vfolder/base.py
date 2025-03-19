import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseAction
from ai.backend.manager.models.user import UserRole


@dataclass
class DomainAction(BaseAction):
    @override
    def entity_type(self):
        return "domain"


@dataclass
class UserInfo:
    id: uuid.UUID
    role: UserRole
    domain_name: str
