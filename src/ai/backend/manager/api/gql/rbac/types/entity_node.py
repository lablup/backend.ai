"""EntityNode union type definition.

Separated from entity.py to prevent circular imports when other modules
in this package need to reference EntityNode at runtime.
"""

from __future__ import annotations

from typing import Annotated

import strawberry

from ai.backend.manager.api.gql.app_config import AppConfig
from ai.backend.manager.api.gql.artifact.types import Artifact, ArtifactRevision
from ai.backend.manager.api.gql.artifact_registry import ArtifactRegistry
from ai.backend.manager.api.gql.deployment.types.deployment import ModelDeployment
from ai.backend.manager.api.gql.domain_v2.types.node import DomainV2GQL
from ai.backend.manager.api.gql.image.types import ImageV2GQL
from ai.backend.manager.api.gql.notification.types import (
    NotificationChannel,
    NotificationRule,
)
from ai.backend.manager.api.gql.project_v2.types.node import ProjectV2GQL
from ai.backend.manager.api.gql.rbac.types.role import RoleGQL
from ai.backend.manager.api.gql.resource_group.types import ResourceGroupGQL
from ai.backend.manager.api.gql.session import Session
from ai.backend.manager.api.gql.user.types.node import UserV2GQL
from ai.backend.manager.api.gql.vfolder import VFolder

# NOTE: We use direct imports instead of strawberry.lazy() here because strawberry
# does not support the combination of lazy types with union type definitions.
# See: https://github.com/strawberry-graphql/strawberry/issues/3381
#      https://github.com/strawberry-graphql/strawberry/issues/2302
EntityNode = Annotated[
    UserV2GQL
    | ProjectV2GQL
    | DomainV2GQL
    | VFolder
    | ImageV2GQL
    | Session
    | Artifact
    | ArtifactRegistry
    | AppConfig
    | NotificationChannel
    | NotificationRule
    | ModelDeployment
    | ResourceGroupGQL
    | ArtifactRevision
    | RoleGQL,
    strawberry.union("EntityNode"),
]
