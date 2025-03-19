from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseAction, BaseBatchAction


@dataclass
class ResourceAction(BaseAction):
    @override
    def entity_type(self):
        return "resource"

    @override
    def request_id(self):
        # TODO: request_id는 어떻게 생성?
        return "..."


@dataclass
class ResourceBatchAction(BaseBatchAction):
    @override
    def entity_type(self):
        return "resource"
