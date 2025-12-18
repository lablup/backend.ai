from __future__ import annotations

import uuid
from functools import cached_property, partial
from typing import Optional

from strawberry.dataloader import DataLoader

from ai.backend.manager.data.huggingface_registry.types import HuggingFaceRegistryData
from ai.backend.manager.data.notification import NotificationChannelData, NotificationRuleData
from ai.backend.manager.data.object_storage.types import ObjectStorageData
from ai.backend.manager.services.processors import Processors

from .huggingface_registry import load_huggingface_registries_by_ids
from .notification import load_channels_by_ids, load_rules_by_ids
from .object_storage import load_object_storages_by_ids


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
    def huggingface_registry_loader(
        self,
    ) -> DataLoader[uuid.UUID, Optional[HuggingFaceRegistryData]]:
        return DataLoader(
            load_fn=partial(load_huggingface_registries_by_ids, self._processors.artifact_registry)
        )

    @cached_property
    def object_storage_loader(
        self,
    ) -> DataLoader[uuid.UUID, Optional[ObjectStorageData]]:
        return DataLoader(
            load_fn=partial(load_object_storages_by_ids, self._processors.object_storage)
        )
