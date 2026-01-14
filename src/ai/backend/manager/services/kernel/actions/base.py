from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseAction


@dataclass
class KernelAction(BaseAction):
    """Base action class for kernel operations."""

    @override
    @classmethod
    def entity_type(cls) -> str:
        return "kernel"
