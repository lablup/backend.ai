from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseAction


@dataclass
class ErrorLogAction(BaseAction):
    """Base action class for error log operations."""

    @override
    @classmethod
    def entity_type(cls) -> str:
        return "error_log"
