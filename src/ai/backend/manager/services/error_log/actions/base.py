from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action import BaseAction


@dataclass
class ErrorLogAction(BaseAction):
    """Base action class for error log operations."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.ERROR_LOG
