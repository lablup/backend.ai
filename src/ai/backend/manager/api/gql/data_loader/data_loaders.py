from __future__ import annotations

import uuid
from functools import cached_property, partial
from typing import Optional

from strawberry.dataloader import DataLoader

from ai.backend.manager.data.artifact.types import ArtifactData, ArtifactRevisionData
from ai.backend.manager.data.artifact_registries.types import ArtifactRegistryData
from ai.backend.manager.data.deployment.types import (
    ModelDeploymentData,
    ModelReplicaData,
    ModelRevisionData,
    RouteInfo,
)
from ai.backend.manager.data.huggingface_registry.types import HuggingFaceRegistryData
from ai.backend.manager.data.notification import NotificationChannelData, NotificationRuleData
from ai.backend.manager.data.object_storage.types import ObjectStorageData
from ai.backend.manager.data.reservoir_registry.types import ReservoirRegistryData
from ai.backend.manager.data.scaling_group.types import ScalingGroupData
from ai.backend.manager.data.storage_namespace.types import StorageNamespaceData
from ai.backend.manager.data.vfs_storage.types import VFSStorageData
from ai.backend.manager.services.processors import Processors

from .artifact import load_artifacts_by_ids
from .artifact_registry import load_artifact_registries_by_ids
from .artifact_revision import load_artifact_revisions_by_ids
from .deployment import (
    load_deployments_by_ids,
    load_replicas_by_ids,
    load_revisions_by_ids,
    load_routes_by_ids,
)
from .huggingface_registry import load_huggingface_registries_by_ids
from .notification import load_channels_by_ids, load_rules_by_ids
from .object_storage import load_object_storages_by_ids
from .reservoir_registry import load_reservoir_registries_by_ids
from .scaling_group import load_scaling_groups_by_names
from .storage_namespace import load_storage_namespaces_by_ids
from .vfs_storage import load_vfs_storages_by_ids


class DataLoaders:
    """
    Manages domain-specific DataLoader instances for GraphQL resolvers.

    This class is the central registry for all DataLoaders used in the GraphQL API.
    Each domain (notification, model_deployment, model_replica, etc.) will have
    its own loader instances initialized here.
    """

    _processors: Processors

    def __init__(self, processors: Processors) -> None:
        self._processors = processors

    @cached_property
    def scaling_group_loader(
        self,
    ) -> DataLoader[str, Optional[ScalingGroupData]]:
        return DataLoader(
            load_fn=partial(load_scaling_groups_by_names, self._processors.scaling_group)
        )

    @cached_property
    def notification_channel_loader(
        self,
    ) -> DataLoader[uuid.UUID, Optional[NotificationChannelData]]:
        return DataLoader(load_fn=partial(load_channels_by_ids, self._processors.notification))

    @cached_property
    def notification_rule_loader(
        self,
    ) -> DataLoader[uuid.UUID, Optional[NotificationRuleData]]:
        return DataLoader(load_fn=partial(load_rules_by_ids, self._processors.notification))

    @cached_property
    def artifact_registry_loader(
        self,
    ) -> DataLoader[uuid.UUID, Optional[ArtifactRegistryData]]:
        return DataLoader(
            load_fn=partial(load_artifact_registries_by_ids, self._processors.artifact_registry)
        )

    @cached_property
    def huggingface_registry_loader(
        self,
    ) -> DataLoader[uuid.UUID, Optional[HuggingFaceRegistryData]]:
        return DataLoader(
            load_fn=partial(load_huggingface_registries_by_ids, self._processors.artifact_registry)
        )

    @cached_property
    def reservoir_registry_loader(
        self,
    ) -> DataLoader[uuid.UUID, Optional[ReservoirRegistryData]]:
        return DataLoader(
            load_fn=partial(load_reservoir_registries_by_ids, self._processors.artifact_registry)
        )

    @cached_property
    def storage_namespace_loader(
        self,
    ) -> DataLoader[uuid.UUID, Optional[StorageNamespaceData]]:
        return DataLoader(
            load_fn=partial(load_storage_namespaces_by_ids, self._processors.storage_namespace)
        )

    @cached_property
    def object_storage_loader(
        self,
    ) -> DataLoader[uuid.UUID, Optional[ObjectStorageData]]:
        return DataLoader(
            load_fn=partial(load_object_storages_by_ids, self._processors.object_storage)
        )

    @cached_property
    def vfs_storage_loader(
        self,
    ) -> DataLoader[uuid.UUID, Optional[VFSStorageData]]:
        return DataLoader(load_fn=partial(load_vfs_storages_by_ids, self._processors.vfs_storage))

    @cached_property
    def artifact_loader(
        self,
    ) -> DataLoader[uuid.UUID, Optional[ArtifactData]]:
        return DataLoader(load_fn=partial(load_artifacts_by_ids, self._processors.artifact))

    @cached_property
    def artifact_revision_loader(
        self,
    ) -> DataLoader[uuid.UUID, Optional[ArtifactRevisionData]]:
        return DataLoader(
            load_fn=partial(load_artifact_revisions_by_ids, self._processors.artifact_revision)
        )

    @cached_property
    def route_loader(
        self,
    ) -> DataLoader[uuid.UUID, Optional[RouteInfo]]:
        return DataLoader(load_fn=partial(load_routes_by_ids, self._processors.deployment))

    @cached_property
    def deployment_loader(
        self,
    ) -> DataLoader[uuid.UUID, Optional[ModelDeploymentData]]:
        return DataLoader(load_fn=partial(load_deployments_by_ids, self._processors.deployment))

    @cached_property
    def revision_loader(
        self,
    ) -> DataLoader[uuid.UUID, Optional[ModelRevisionData]]:
        return DataLoader(load_fn=partial(load_revisions_by_ids, self._processors.deployment))

    @cached_property
    def replica_loader(
        self,
    ) -> DataLoader[uuid.UUID, Optional[ModelReplicaData]]:
        return DataLoader(load_fn=partial(load_replicas_by_ids, self._processors.deployment))
