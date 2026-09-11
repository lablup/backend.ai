"""The image adapter, assembled for one row.

The only place in these scenarios that knows how the adapter is built. Everything the
eleven calls it offers actually read is wired; the agent registry is not, because only
the wirings outside this adapter reach it.
"""

from __future__ import annotations

from typing import Any

import pytest
from bai_scenario.runner.unwired import unwired

from ai.backend.common.clients.valkey_client.valkey_image.client import ValkeyImageClient
from ai.backend.common.data.entity.image import ImageEntityType
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta, ProcessorDependencies
from ai.backend.manager.actions.v2.validators import ActionValidators as V2ActionValidators
from ai.backend.manager.api.adapters.image.adapter import ImageAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.repositories.image.repository import ImageRepository
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.services.image.processors import ImageProcessors
from ai.backend.manager.services.image.service import ImageService


@pytest.fixture
async def adapter(
    engine: Any,
    config: ManagerConfigProvider,
    validators: V2ActionValidators,
    monitors: ActionMonitors,
) -> ImageAdapter:
    provider = V2DBOpsProvider(engine)
    registry: ProcessorRegistry[Any] = ProcessorRegistry(
        ProcessorDependencies(
            monitors=monitors,
            validators=validators,
            repository=OpsRepository(provider),
        )
    )
    return ImageAdapter(
        ImageProcessors(
            registry.group(GroupMeta(ImageEntityType())),
            ImageService(
                unwired(AgentRegistry, "only the wirings outside this adapter reach agents"),
                ImageRepository(
                    engine,
                    provider,
                    unwired(ValkeyImageClient, "no call of this adapter reads the image cache"),
                    config,
                ),
                config,
            ),
        )
    )
