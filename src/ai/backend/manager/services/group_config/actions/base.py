from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseAction


@dataclass
class GroupConfigAction(BaseAction):
    """Base action for group config operations."""

    group_id_or_name: uuid.UUID | str
    domain_name: Optional[str]

    @override
    @classmethod
    def entity_type(cls) -> str:
        return "group_config"
