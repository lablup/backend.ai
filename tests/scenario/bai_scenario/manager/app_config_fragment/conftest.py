"""The app config fragment adapter, assembled for one row.

The only place in the fragment scenarios that knows how the app config processors are
built. The four app config adapters share the bundle, so each package builds it the same
way.
"""

from __future__ import annotations

from typing import Any

import pytest

from ai.backend.common.data.entity.app_config import AppConfigEntityType
from ai.backend.common.data.entity.app_config_allow_list import AppConfigAllowListEntityType
from ai.backend.common.data.entity.app_config_definition import AppConfigDefinitionEntityType
from ai.backend.common.data.entity.app_config_fragment import AppConfigFragmentEntityType
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta, ProcessorDependencies
from ai.backend.manager.actions.v2.validators import ActionValidators as V2ActionValidators
from ai.backend.manager.api.adapters.app_config_fragment.adapter import AppConfigFragmentAdapter
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.services.app_config.processors import AppConfigProcessors
from ai.backend.manager.services.app_config.service import AppConfigService


@pytest.fixture
async def adapter(
    engine: Any,
    validators: V2ActionValidators,
    monitors: ActionMonitors,
) -> AppConfigFragmentAdapter:
    repository: OpsRepository[Any] = OpsRepository(V2DBOpsProvider(engine))
    registry: ProcessorRegistry[Any] = ProcessorRegistry(
        ProcessorDependencies(monitors=monitors, validators=validators, repository=repository)
    )
    return AppConfigFragmentAdapter(
        AppConfigProcessors(
            registry.group(GroupMeta(AppConfigEntityType())),
            registry.group(GroupMeta(AppConfigDefinitionEntityType())),
            registry.group(GroupMeta(AppConfigAllowListEntityType())),
            registry.group(GroupMeta(AppConfigFragmentEntityType())),
            AppConfigService(repository),
        )
    )
