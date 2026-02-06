from __future__ import annotations

import uuid
from functools import cached_property, partial

from strawberry.dataloader import DataLoader

from ai.backend.common.types import AgentId, ImageID, KernelId
from ai.backend.manager.data.artifact.types import ArtifactData, ArtifactRevisionData
from ai.backend.manager.data.artifact_registries.types import ArtifactRegistryData
from ai.backend.manager.data.deployment.types import (
    ModelDeploymentData,
    ModelReplicaData,
    ModelRevisionData,
    RouteInfo,
)
from ai.backend.manager.data.huggingface_registry.types import HuggingFaceRegistryData
from ai.backend.manager.data.image.types import ImageAliasData, ImageData
from ai.backend.manager.data.kernel.types import KernelInfo
from ai.backend.manager.data.notification import NotificationChannelData, NotificationRuleData
from ai.backend.manager.data.object_storage.types import ObjectStorageData
from ai.backend.manager.data.reservoir_registry.types import ReservoirRegistryData
from ai.backend.manager.data.scaling_group.types import ScalingGroupData
from ai.backend.manager.data.storage_namespace.types import StorageNamespaceData
from ai.backend.manager.data.vfs_storage.types import VFSStorageData
from ai.backend.manager.services.processors import Processors

from .agent.loader import load_container_counts
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
from .image import load_alias_by_ids, load_images_by_ids
from .kernel import load_kernels_by_ids
from .notification import load_channels_by_ids, load_rules_by_ids
from .object_storage import load_object_storages_by_ids
from .reservoir_registry import load_reservoir_registries_by_ids
from .resource_group import load_resource_groups_by_names
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
    def resource_group_loader(
        self,
    ) -> DataLoader[str, ScalingGroupData | None]:
        return DataLoader(
            load_fn=partial(load_resource_groups_by_names, self._processors.scaling_group)
        )

    @cached_property
    def notification_channel_loader(
        self,
    ) -> DataLoader[uuid.UUID, NotificationChannelData | None]:
        return DataLoader(load_fn=partial(load_channels_by_ids, self._processors.notification))

    @cached_property
    def notification_rule_loader(
        self,
    ) -> DataLoader[uuid.UUID, NotificationRuleData | None]:
        return DataLoader(load_fn=partial(load_rules_by_ids, self._processors.notification))

    @cached_property
    def artifact_registry_loader(
        self,
    ) -> DataLoader[uuid.UUID, ArtifactRegistryData | None]:
        return DataLoader(
            load_fn=partial(load_artifact_registries_by_ids, self._processors.artifact_registry)
        )

    @cached_property
    def huggingface_registry_loader(
        self,
    ) -> DataLoader[uuid.UUID, HuggingFaceRegistryData | None]:
        return DataLoader(
            load_fn=partial(load_huggingface_registries_by_ids, self._processors.artifact_registry)
        )

    @cached_property
    def reservoir_registry_loader(
        self,
    ) -> DataLoader[uuid.UUID, ReservoirRegistryData | None]:
        return DataLoader(
            load_fn=partial(load_reservoir_registries_by_ids, self._processors.artifact_registry)
        )

    @cached_property
    def storage_namespace_loader(
        self,
    ) -> DataLoader[uuid.UUID, StorageNamespaceData | None]:
        return DataLoader(
            load_fn=partial(load_storage_namespaces_by_ids, self._processors.storage_namespace)
        )

    @cached_property
    def object_storage_loader(
        self,
    ) -> DataLoader[uuid.UUID, ObjectStorageData | None]:
        return DataLoader(
            load_fn=partial(load_object_storages_by_ids, self._processors.object_storage)
        )

    @cached_property
    def vfs_storage_loader(
        self,
    ) -> DataLoader[uuid.UUID, VFSStorageData | None]:
        return DataLoader(load_fn=partial(load_vfs_storages_by_ids, self._processors.vfs_storage))

    @cached_property
    def artifact_loader(
        self,
    ) -> DataLoader[uuid.UUID, ArtifactData | None]:
        return DataLoader(load_fn=partial(load_artifacts_by_ids, self._processors.artifact))

    @cached_property
    def artifact_revision_loader(
        self,
    ) -> DataLoader[uuid.UUID, ArtifactRevisionData | None]:
        return DataLoader(
            load_fn=partial(load_artifact_revisions_by_ids, self._processors.artifact_revision)
        )

    @cached_property
    def route_loader(
        self,
    ) -> DataLoader[uuid.UUID, RouteInfo | None]:
        return DataLoader(load_fn=partial(load_routes_by_ids, self._processors.deployment))

    @cached_property
    def deployment_loader(
        self,
    ) -> DataLoader[uuid.UUID, ModelDeploymentData | None]:
        return DataLoader(load_fn=partial(load_deployments_by_ids, self._processors.deployment))

    @cached_property
    def revision_loader(
        self,
    ) -> DataLoader[uuid.UUID, ModelRevisionData | None]:
        return DataLoader(load_fn=partial(load_revisions_by_ids, self._processors.deployment))

    @cached_property
    def replica_loader(
        self,
    ) -> DataLoader[uuid.UUID, ModelReplicaData | None]:
        return DataLoader(load_fn=partial(load_replicas_by_ids, self._processors.deployment))

    @cached_property
    def container_count_loader(
        self,
    ) -> DataLoader[AgentId, int]:
        return DataLoader(load_fn=partial(load_container_counts, self._processors.agent))

    @cached_property
    def image_loader(
        self,
    ) -> DataLoader[ImageID, ImageData | None]:
        return DataLoader(load_fn=partial(load_images_by_ids, self._processors.image))

    @cached_property
    def kernel_loader(
        self,
    ) -> DataLoader[KernelId, KernelInfo | None]:
        return DataLoader(load_fn=partial(load_kernels_by_ids, self._processors.session))

    @cached_property
    def image_alias_loader(
        self,
    ) -> DataLoader[uuid.UUID, ImageAliasData | None]:
        """Load a single alias by its own ID (ImageAliasRow.id)."""
        return DataLoader(load_fn=partial(load_alias_by_ids, self._processors.image))
