from dataclasses import dataclass
from typing import Optional, override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.deployment.types import ModelDeploymentAccessTokenData
from ai.backend.manager.services.deployment.actions.base import DeploymentBaseAction


@dataclass
class BatchLoadAccessTokensAction(DeploymentBaseAction):
    access_token_ids: list[UUID]

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "batch_load_access_tokens"


@dataclass
class BatchLoadAccessTokensActionResult(BaseActionResult):
    data: list[ModelDeploymentAccessTokenData]

    @override
    def entity_id(self) -> Optional[str]:
        return None
