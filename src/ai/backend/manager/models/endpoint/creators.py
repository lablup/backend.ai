"""Creator specs for the endpoint tables."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import override

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.deployment.types import ModelDeploymentAccessTokenData
from ai.backend.manager.models.endpoint.row import EndpointTokenRow
from ai.backend.manager.models.specs.creator import FieldCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck


@dataclass
class EndpointTokenCreator(
    FieldCreator[DeploymentID, EndpointTokenRow, ModelDeploymentAccessTokenData]
):
    """Registers an access token under the deployment it grants access to.

    The token itself is the JWT the app-proxy coordinator minted; a locally
    generated string would never satisfy the worker's bearer check, so it has no
    fallback.
    """

    domain: str
    project_id: ProjectID
    session_owner_id: UserID
    token: str
    expires_at: datetime | None = None

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_row(self, owner_id: DeploymentID) -> EndpointTokenRow:
        return EndpointTokenRow(
            id=uuid.uuid4(),
            token=self.token,
            endpoint=owner_id,
            domain=self.domain,
            project=self.project_id,
            session_owner=self.session_owner_id,
            expires_at=self.expires_at,
        )

    @override
    def to_data(self, row: EndpointTokenRow) -> ModelDeploymentAccessTokenData:
        return ModelDeploymentAccessTokenData(
            id=row.id,
            token=row.token,
            expires_at=row.expires_at,
            created_at=row.created_at,
        )
