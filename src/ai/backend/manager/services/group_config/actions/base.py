from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseAction


@dataclass
class GroupConfigAction(BaseAction):
    @override
    @classmethod
    def entity_type(cls) -> str:
        return "group_config"
