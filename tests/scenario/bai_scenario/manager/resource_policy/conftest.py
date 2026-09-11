"""The resource policy adapter, assembled for one row.

One adapter over three processor groups, one per policy. Every operation runs straight
against ops, so nothing beyond the registry is wired.
"""

from __future__ import annotations

from typing import Any

import pytest

from ai.backend.common.data.entity.resource_policy import (
    KeyPairResourcePolicyEntityType,
    ProjectResourcePolicyEntityType,
    UserResourcePolicyEntityType,
)
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta, ProcessorDependencies
from ai.backend.manager.actions.v2.validators import ActionValidators as V2ActionValidators
from ai.backend.manager.api.adapters.resource_policy.adapter import ResourcePolicyAdapter
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.services.keypair_resource_policy.processors import (
    KeypairResourcePolicyProcessors,
)
from ai.backend.manager.services.project_resource_policy.processors import (
    ProjectResourcePolicyProcessors,
)
from ai.backend.manager.services.user_resource_policy.processors import (
    UserResourcePolicyProcessors,
)


@pytest.fixture
async def adapter(
    engine: Any,
    validators: V2ActionValidators,
    monitors: ActionMonitors,
) -> ResourcePolicyAdapter:
    registry: ProcessorRegistry[Any] = ProcessorRegistry(
        ProcessorDependencies(
            monitors=monitors,
            validators=validators,
            repository=OpsRepository(V2DBOpsProvider(engine)),
        )
    )
    return ResourcePolicyAdapter(
        KeypairResourcePolicyProcessors(
            registry.group(GroupMeta(KeyPairResourcePolicyEntityType()))
        ),
        UserResourcePolicyProcessors(registry.group(GroupMeta(UserResourcePolicyEntityType()))),
        ProjectResourcePolicyProcessors(
            registry.group(GroupMeta(ProjectResourcePolicyEntityType()))
        ),
    )
