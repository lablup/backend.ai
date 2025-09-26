from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.deployment.types import ModelDeploymentAccessTokenData
from ai.backend.manager.repositories.deployment.types.types import AccessTokenOrderingOptions
from ai.backend.manager.services.deployment.actions.base import DeploymentBaseAction
from ai.backend.manager.types import PaginationOptions


@dataclass
class ListAccessTokensAction(DeploymentBaseAction):
    pagination: PaginationOptions
    ordering: Optional[AccessTokenOrderingOptions] = None

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "list_access_tokens"


@dataclass
class ListAccessTokensActionResult(BaseActionResult):
    data: list[ModelDeploymentAccessTokenData]
    total_count: int

    @override
    def entity_id(self) -> Optional[str]:
        return None
