from typing import Optional

from ai.backend.manager.actions.action import BaseAction, BaseActionResult


class MetricAction(BaseAction):
    def entity_id(self) -> Optional[str]:
        return "metric"


class MetricActionResult(BaseActionResult):
    def entity_id(self) -> Optional[str]:
        return "metric"
