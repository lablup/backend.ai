from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseAction, BaseBatchAction


@dataclass
class ProjectResourcePolicyAction(BaseAction):
    @override
    @classmethod
    def entity_type(cls) -> str:
        return "project_resource_policy"


@dataclass
class ProjectResourcePolicyBatchAction(BaseBatchAction):
    @override
    @classmethod
    def entity_type(cls) -> str:
        return "project_resource_policy"
