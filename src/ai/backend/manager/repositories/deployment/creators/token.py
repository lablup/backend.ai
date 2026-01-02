"""CreatorSpec for endpoint token creation."""

from __future__ import annotations

import secrets
import uuid
from dataclasses import dataclass

from typing_extensions import override

from ai.backend.manager.models.endpoint import EndpointTokenRow
from ai.backend.manager.repositories.base import CreatorSpec


@dataclass
class EndpointTokenCreatorSpec(CreatorSpec[EndpointTokenRow]):
    """CreatorSpec for endpoint access token creation.

    Creates an access token that can be used to authenticate requests
    to a specific endpoint. Token ID and token value are generated
    automatically in build_row().
    """

    endpoint_id: uuid.UUID
    domain: str
    project_id: uuid.UUID
    session_owner_id: uuid.UUID

    @override
    def build_row(self) -> EndpointTokenRow:
        return EndpointTokenRow(
            id=uuid.uuid4(),
            token=secrets.token_urlsafe(32),
            endpoint=self.endpoint_id,
            domain=self.domain,
            project=self.project_id,
            session_owner=self.session_owner_id,
        )
