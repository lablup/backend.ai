"""Creator specs for the endpoint tables."""

from __future__ import annotations

import uuid
from collections.abc import Collection, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import override

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.deployment_token import DeploymentTokenID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.deployment.types import (
    DeploymentInfo,
    DeploymentOptions,
    ModelDeploymentAccessTokenData,
)
from ai.backend.manager.data.model_serving.types import EndpointLifecycle
from ai.backend.manager.models.endpoint.row import EndpointRow, EndpointTokenRow
from ai.backend.manager.models.specs.creator import EntityCreator, FieldCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck


@dataclass
class DeploymentMetadataFields:
    """Metadata of a deployment to create."""

    name: str
    domain: str
    project_id: ProjectID
    resource_group: str
    created_user_id: uuid.UUID
    session_owner_id: UserID
    revision_history_limit: int = 10
    tag: str | None = None
    created_at: datetime | None = None


@dataclass
class DeploymentReplicaFields:
    """Replica counts of a deployment to create."""

    replica_count: int
    desired_replica_count: int | None = None


@dataclass
class DeploymentNetworkFields:
    """Network exposure of a deployment to create."""

    open_to_public: bool = False
    url: str | None = None


@dataclass
class DeploymentCreator(EntityCreator[EndpointRow, DeploymentInfo]):
    """Creates a deployment.

    It joins its project and its session owner, as the placement group of its
    replicas does: admission is the owner's, visibility the project's.

    ``options`` is a resolved snapshot of the resource group's
    ``default_deployment_options``, so every deployment persists its own copy.
    """

    metadata: DeploymentMetadataFields
    replica: DeploymentReplicaFields
    network: DeploymentNetworkFields
    options: DeploymentOptions

    @override
    def entity_id(self, row: EndpointRow) -> DeploymentID:
        return DeploymentID(row.id)

    @override
    def created_in(self, row: EndpointRow) -> Collection[EntityIdentifier]:
        return (self.metadata.project_id, self.metadata.session_owner_id)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_row(self) -> EndpointRow:
        return EndpointRow(
            name=self.metadata.name,
            domain=self.metadata.domain,
            project=self.metadata.project_id,
            resource_group=self.metadata.resource_group,
            created_user=self.metadata.created_user_id,
            session_owner=self.metadata.session_owner_id,
            revision_history_limit=self.metadata.revision_history_limit,
            tag=self.metadata.tag,
            replicas=self.replica.replica_count,
            desired_replicas=self.replica.desired_replica_count,
            open_to_public=self.network.open_to_public,
            url=self.network.url,
            lifecycle_stage=EndpointLifecycle.PENDING,
            retries=0,
            options=self.options,
        )

    @override
    def to_data(self, row: EndpointRow) -> DeploymentInfo:
        return row.to_bare_deployment_info()


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
    def field_id(self, row: EndpointTokenRow) -> DeploymentTokenID:
        return row.id

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_row(self, owner_id: DeploymentID) -> EndpointTokenRow:
        return EndpointTokenRow(
            id=DeploymentTokenID(uuid.uuid4()),
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
