from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseAction


@dataclass
class ProjectRegistryQuotaAction(BaseAction):
    @override
    @classmethod
    def entity_type(cls) -> str:
        return "project_registry_quota"
