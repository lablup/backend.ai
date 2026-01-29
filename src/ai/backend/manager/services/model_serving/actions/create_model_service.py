from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.model_serving.creator import ModelServiceCreator
from ai.backend.manager.data.model_serving.types import ServiceInfo
from ai.backend.manager.services.model_serving.actions.base import ModelServiceAction

if TYPE_CHECKING:
    from ai.backend.manager.data.deployment.types import ModelRevisionSpec


@dataclass
class CreateModelServiceAction(ModelServiceAction):
    request_user_id: uuid.UUID
    creator: ModelServiceCreator

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "create"

    def apply_revision(self, revision: ModelRevisionSpec) -> None:
        """Apply revision results to this action."""
        self.creator.image = revision.image_identifier.canonical
        self.creator.architecture = revision.image_identifier.architecture
        self.creator.config.resources = dict(revision.resource_spec.resource_slots)
        if revision.execution.environ:
            self.creator.config.environ = revision.execution.environ


@dataclass
class CreateModelServiceActionResult(BaseActionResult):
    data: ServiceInfo

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.data.endpoint_id)
