from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseAction


@dataclass
class ScalingGroupAction(BaseAction):
    """Base action class for scaling group operations."""

    @override
    @classmethod
    def entity_type(cls) -> str:
        return "scaling_group"
