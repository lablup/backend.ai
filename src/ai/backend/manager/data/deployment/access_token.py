from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class ModelDeploymentAccessTokenCreator:
    model_deployment_id: UUID
    expires_at: datetime | None
