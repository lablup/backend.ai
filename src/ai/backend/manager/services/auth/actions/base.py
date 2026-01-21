from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseAction


@dataclass
class AuthAction(BaseAction):
    @classmethod
    @override
    def entity_type(cls) -> str:
        return "auth"
