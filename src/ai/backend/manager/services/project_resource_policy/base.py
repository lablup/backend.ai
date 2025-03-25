from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseAction, BaseBatchAction


@dataclass
class ProjectResourcePolicyAction(BaseAction):
    @override
    def entity_type(self):
        return "project_resource_policy"


@dataclass
class ProjectResourcePolicyBatchAction(BaseBatchAction):
    @override
    def entity_type(self):
        return "project_resource_policy"
