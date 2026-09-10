"""EntityNode union type definition.

Separated from entity.py to prevent circular imports when other modules
in this package need to reference EntityNode at runtime.
"""

from __future__ import annotations

from typing import Annotated

import strawberry

from ai.backend.manager.api.gql.agent.types import AgentV2GQL
from ai.backend.manager.api.gql.app_config_allow_list.types import AppConfigAllowListGQL
from ai.backend.manager.api.gql.app_config_definition.types import AppConfigDefinitionGQL
from ai.backend.manager.api.gql.app_config_fragment.types import AppConfigFragmentGQL
from ai.backend.manager.api.gql.artifact.types import Artifact, ArtifactRevision
from ai.backend.manager.api.gql.artifact_registry import ArtifactRegistry
from ai.backend.manager.api.gql.container_registry.types import ContainerRegistryGQL
from ai.backend.manager.api.gql.deployment.types.deployment import ModelDeployment
from ai.backend.manager.api.gql.domain_v2.types.node import DomainV2GQL
from ai.backend.manager.api.gql.idle_checker.types import IdleCheckerGQL
from ai.backend.manager.api.gql.image.types import ImageV2GQL
from ai.backend.manager.api.gql.notification.types import (
    NotificationChannel,
    NotificationRule,
)
from ai.backend.manager.api.gql.object_storage import ObjectStorage
from ai.backend.manager.api.gql.project_v2.types.node import ProjectV2GQL
from ai.backend.manager.api.gql.rbac.types.role import RoleGQL
from ai.backend.manager.api.gql.resource_group.types import ResourceGroupGQL
from ai.backend.manager.api.gql.runtime_variant.types import RuntimeVariantGQL
from ai.backend.manager.api.gql.runtime_variant_preset.types import RuntimeVariantPresetGQL
from ai.backend.manager.api.gql.session.types import SessionV2GQL
from ai.backend.manager.api.gql.session_federation import Session
from ai.backend.manager.api.gql.storage_namespace import StorageNamespace
from ai.backend.manager.api.gql.user.types.node import UserV2GQL
from ai.backend.manager.api.gql.vfolder import VFolder
from ai.backend.manager.api.gql.vfolder_v2.types.node import VFolderGQL
from ai.backend.manager.api.gql.vfs_storage import VFSStorage

# NOTE: We use direct imports instead of strawberry.lazy() here because strawberry
# does not support the combination of lazy types with union type definitions.
# See: https://github.com/strawberry-graphql/strawberry/issues/3381
#      https://github.com/strawberry-graphql/strawberry/issues/2302
EntityNodeGQL = Annotated[
    UserV2GQL
    | ProjectV2GQL
    | DomainV2GQL
    | VFolder
    | ImageV2GQL
    | Session
    | SessionV2GQL
    | Artifact
    | ArtifactRegistry
    | NotificationChannel
    | NotificationRule
    | ModelDeployment
    | ResourceGroupGQL
    | ContainerRegistryGQL
    | ArtifactRevision
    | RoleGQL
    | AgentV2GQL
    | AppConfigAllowListGQL
    | AppConfigDefinitionGQL
    | AppConfigFragmentGQL
    | IdleCheckerGQL
    | ObjectStorage
    | RuntimeVariantGQL
    | RuntimeVariantPresetGQL
    | StorageNamespace
    | VFolderGQL
    | VFSStorage,
    strawberry.union("EntityNode"),
]
