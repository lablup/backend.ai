from dataclasses import dataclass
from datetime import datetime

from ai.backend.common.data.entity.deployment import DeploymentID


@dataclass
class ModelDeploymentAccessTokenCreator:
    model_deployment_id: DeploymentID
    expires_at: datetime
