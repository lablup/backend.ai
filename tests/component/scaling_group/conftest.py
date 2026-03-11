from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.api.rest.fair_share.handler import FairShareAPIHandler
from ai.backend.manager.api.rest.fair_share.registry import register_fair_share_routes
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.scaling_group.handler import ScalingGroupHandler
from ai.backend.manager.api.rest.scaling_group.registry import register_scaling_group_routes
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.fair_share.repository import FairShareRepository
from ai.backend.manager.repositories.resource_usage_history.repository import (
    ResourceUsageHistoryRepository,
)
from ai.backend.manager.repositories.scaling_group.repository import ScalingGroupRepository
from ai.backend.manager.services.fair_share.processors import FairShareProcessors
from ai.backend.manager.services.fair_share.service import FairShareService
from ai.backend.manager.services.resource_usage.processors import ResourceUsageProcessors
from ai.backend.manager.services.resource_usage.service import ResourceUsageService
from ai.backend.manager.services.scaling_group.processors import ScalingGroupProcessors
from ai.backend.manager.services.scaling_group.service import ScalingGroupService


@pytest.fixture()
def scaling_group_processors(database_engine: ExtendedAsyncSAEngine) -> ScalingGroupProcessors:
    repo = ScalingGroupRepository(database_engine)
    service = ScalingGroupService(repo)
    return ScalingGroupProcessors(
        service=service, action_monitors=[], validators=MagicMock(spec=ActionValidators)
    )


@pytest.fixture()
def fair_share_processors(database_engine: ExtendedAsyncSAEngine) -> FairShareProcessors:
    repo = FairShareRepository(database_engine)
    service = FairShareService(repo)
    return FairShareProcessors(
        service=service, action_monitors=[], validators=MagicMock(spec=ActionValidators)
    )


@pytest.fixture()
def resource_usage_processors(database_engine: ExtendedAsyncSAEngine) -> ResourceUsageProcessors:
    repo = ResourceUsageHistoryRepository(database_engine)
    service = ResourceUsageService(repo)
    return ResourceUsageProcessors(
        service=service, action_monitors=[], validators=MagicMock(spec=ActionValidators)
    )


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    scaling_group_processors: ScalingGroupProcessors,
    fair_share_processors: FairShareProcessors,
    resource_usage_processors: ResourceUsageProcessors,
) -> list[RouteRegistry]:
    """Load only the modules required for scaling-group-domain tests."""
    return [
        register_scaling_group_routes(
            ScalingGroupHandler(scaling_group=scaling_group_processors), route_deps
        ),
        register_fair_share_routes(
            FairShareAPIHandler(
                fair_share=fair_share_processors,
                resource_usage=resource_usage_processors,
                scaling_group=scaling_group_processors,
            ),
            route_deps,
        ),
    ]
