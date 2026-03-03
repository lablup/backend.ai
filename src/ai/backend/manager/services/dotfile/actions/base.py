from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action import BaseAction


@dataclass
class DotfileAction(BaseAction):
    """Base action class for dotfile operations."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.DOTFILE
