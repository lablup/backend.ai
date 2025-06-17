from dataclasses import dataclass
from typing import Optional, override

from ai.backend.common.types import KernelId
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.session.base import SessionAction


@dataclass
class DestroyKernelAction(SessionAction):
    kernel_ids: list[KernelId]

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        # TODO: Handle this
        return "destory_kernel"


@dataclass
class DestroyKernelActionResult(BaseActionResult):
    # TODO: Change this to `entity_ids`
    @override
    def entity_id(self) -> Optional[str]:
        return None
