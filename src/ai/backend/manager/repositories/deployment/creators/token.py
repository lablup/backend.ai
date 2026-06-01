"""CreatorSpec for endpoint token creation."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import override

from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.manager.models.endpoint import EndpointTokenRow
from ai.backend.manager.repositories.base import CreatorSpec


@dataclass
class EndpointTokenCreatorSpec(CreatorSpec[EndpointTokenRow]):
    """CreatorSpec for endpoint access token creation.

    The persisted token is the JWT minted by the app-proxy coordinator
    (HS256-signed with the shared ``jwt_secret``). The service layer
    obtains it from the coordinator and passes it in via ``token``;
    locally generated random strings would never satisfy the worker's
    ``Authorization: Bearer <jwt>`` check, so this field has no fallback.
    """

    deployment_id: DeploymentID
    domain: str
    project_id: uuid.UUID
    session_owner_id: uuid.UUID
    token: str
    expires_at: datetime | None = None

    @override
    def build_row(self) -> EndpointTokenRow:
        return EndpointTokenRow(
            id=uuid.uuid4(),
            token=self.token,
            endpoint=self.deployment_id,
            domain=self.domain,
            project=self.project_id,
            session_owner=self.session_owner_id,
            expires_at=self.expires_at,
        )
