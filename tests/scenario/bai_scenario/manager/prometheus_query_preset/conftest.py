"""The query preset adapter, assembled for one row, with Prometheus faked.

Two of the calls hand a query to Prometheus and answer what it answers. The stand-in
answers one sample for every query and keeps what it was asked, so a row can compare
the answer and read the query back.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import pytest
from bai_scenario.fakes.prometheus import FakePrometheusClient

from ai.backend.common.data.entity.prometheus_query_preset import (
    PrometheusQueryPresetEntityType,
)
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta, ProcessorDependencies
from ai.backend.manager.actions.v2.validators import ActionValidators as V2ActionValidators
from ai.backend.manager.api.adapters.prometheus_query_preset.adapter import (
    PrometheusQueryPresetAdapter,
)
from ai.backend.manager.clients.prometheus.preset import PromQLTemplateRenderer
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.prometheus_query_preset.repository import (
    PrometheusQueryPresetRepository,
)
from ai.backend.manager.services.prometheus_query_preset.processors import (
    PrometheusQueryPresetProcessors,
)
from ai.backend.manager.services.prometheus_query_preset.service import (
    PrometheusQueryPresetService,
)


@pytest.fixture
def prometheus() -> FakePrometheusClient:
    return FakePrometheusClient()


@pytest.fixture
def fakes(prometheus: FakePrometheusClient) -> Sequence[object]:
    """What a ``then`` may read off the outside."""
    return (prometheus,)


@pytest.fixture
async def adapter(
    engine: Any,
    config: ManagerConfigProvider,
    validators: V2ActionValidators,
    monitors: ActionMonitors,
    prometheus: FakePrometheusClient,
) -> PrometheusQueryPresetAdapter:
    provider = V2DBOpsProvider(engine)
    registry: ProcessorRegistry[Any] = ProcessorRegistry(
        ProcessorDependencies(
            monitors=monitors,
            validators=validators,
            repository=OpsRepository(provider),
        )
    )
    service = PrometheusQueryPresetService(
        repository=PrometheusQueryPresetRepository(engine, prometheus),
        prometheus_client=prometheus,
        default_timewindow=config.config.metric.timewindow,
        template_renderer=PromQLTemplateRenderer(),
        ops_repository=OpsRepository(provider),
    )
    return PrometheusQueryPresetAdapter(
        PrometheusQueryPresetProcessors(
            registry.group(GroupMeta(PrometheusQueryPresetEntityType())), service
        )
    )
