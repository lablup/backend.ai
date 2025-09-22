from typing import override

from ai.backend.manager.actions.action import BaseAction


class AutoScalingRuleBaseAction(BaseAction):
    @override
    @classmethod
    def entity_type(cls) -> str:
        return "auto_scaling_rule"
