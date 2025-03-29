from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseAction


@dataclass
class SessionAction(BaseAction):
    @override
    def entity_type(self):
        return "session"
