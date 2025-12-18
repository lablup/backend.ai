from __future__ import annotations

import uuid
from functools import cached_property, partial
from typing import Optional

from strawberry.dataloader import DataLoader

from ai.backend.manager.data.deployment.types import ModelDeploymentAutoScalingRuleData
from ai.backend.manager.data.notification import NotificationChannelData, NotificationRuleData
from ai.backend.manager.services.processors import Processors

from .auto_scaling_rule import load_auto_scaling_rules_by_ids
from .notification import load_channels_by_ids, load_rules_by_ids


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
    def auto_scaling_rule_loader(
        self,
    ) -> DataLoader[uuid.UUID, Optional[ModelDeploymentAutoScalingRuleData]]:
        assert self._processors.deployment is not None
        return DataLoader(
            load_fn=partial(load_auto_scaling_rules_by_ids, self._processors.deployment)
        )
