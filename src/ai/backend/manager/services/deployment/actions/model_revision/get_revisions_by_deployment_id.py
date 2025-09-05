from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.deployment.types import ModelRevisionData
from ai.backend.manager.services.deployment.actions.model_revision.base import (
    ModelRevisionBaseAction,
)


@dataclass
class GetRevisionsByDeploymentIdAction(ModelRevisionBaseAction):
    deployment_id: UUID

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "get"


@dataclass
class GetRevisionsByDeploymentIdActionResult(BaseActionResult):
    data: list[ModelRevisionData]

    @override
    def entity_id(self) -> Optional[str]:
        return None
