"""The notification adapter, assembled for one row.

Both catalogs run against ops; the two validations keep a service, and the service's
notification center is the fake that records instead of sending.
"""

from __future__ import annotations

from typing import Any

import pytest

from ai.backend.common.data.entity.notification import (
    NotificationChannelEntityType,
    NotificationRuleEntityType,
)
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta, ProcessorDependencies
from ai.backend.manager.actions.v2.validators import ActionValidators as V2ActionValidators
from ai.backend.manager.api.adapters.notification.adapter import NotificationAdapter
from ai.backend.manager.repositories.notification.repository import NotificationRepository
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.services.notification.processors import NotificationProcessors
from ai.backend.manager.services.notification.service import NotificationService
from bai_scenario.fakes.notification import FakeNotificationCenter


@pytest.fixture
async def adapter(
    engine: Any,
    validators: V2ActionValidators,
    monitors: ActionMonitors,
) -> NotificationAdapter:
    registry: ProcessorRegistry[Any] = ProcessorRegistry(
        ProcessorDependencies(
            monitors=monitors,
            validators=validators,
            repository=OpsRepository(V2DBOpsProvider(engine)),
        )
    )
    return NotificationAdapter(
        NotificationProcessors(
            registry.group(GroupMeta(NotificationChannelEntityType())),
            registry.group(GroupMeta(NotificationRuleEntityType())),
            NotificationService(NotificationRepository(engine), FakeNotificationCenter()),
        )
    )
