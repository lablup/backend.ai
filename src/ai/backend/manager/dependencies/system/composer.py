from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
from ai.backend.common.clients.prometheus.client import PrometheusClient
from ai.backend.common.dependencies import DependencyComposer, DependencyStack
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.health_checker import HealthProbe
from ai.backend.common.jwt.validator import JWTValidator
from ai.backend.common.metrics.metric import CommonMetricRegistry
from ai.backend.common.service_discovery.service_discovery import (
    ServiceDiscovery,
    ServiceDiscoveryLoop,
)
from ai.backend.common.types import ValkeyProfileTarget
from ai.backend.manager.api.gql.adapter import BaseGQLAdapter
from ai.backend.manager.api.types import CORSOptions
from ai.backend.manager.config.unified import ManagerUnifiedConfig
from ai.backend.manager.dependencies.infrastructure.redis import ValkeyClients
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

from .background_task_manager import BackgroundTaskManagerDependency, BackgroundTaskManagerInput
from .cors_options import CORSOptionsDependency
from .gql_adapter import GQLAdapterDependency
from .health_probe import HealthProbeDependency, HealthProbeInput
from .jwt_validator import JWTValidatorDependency
from .metrics import MetricsDependency
from .prometheus_client import PrometheusClientDependency
from .service_discovery import ServiceDiscoveryDependency, ServiceDiscoveryInput


@dataclass
class SystemInput:
    """Input required for system services setup.

    Contains configuration and infrastructure resources from earlier stages.
    """

    config: ManagerUnifiedConfig
    etcd: AsyncEtcd
    valkey: ValkeyClients
    db: ExtendedAsyncSAEngine
    event_producer: EventProducer
    valkey_profile_target: ValkeyProfileTarget


@dataclass
class SystemResources:
    """Container for all system service resources."""

    cors_options: CORSOptions
    metrics: CommonMetricRegistry
    gql_adapter: BaseGQLAdapter
    jwt_validator: JWTValidator
    prometheus_client: PrometheusClient
    service_discovery: ServiceDiscovery
    sd_loop: ServiceDiscoveryLoop
    background_task_manager: BackgroundTaskManager
    health_probe: HealthProbe


class SystemComposer(DependencyComposer[SystemInput, SystemResources]):
    """Composes all system service dependencies.

    Orchestrates initialization across 4 layers:
    - Layer 0: CORS options, metrics, GQL adapter (no dependencies)
    - Layer 1: JWT validator, Prometheus client, service discovery (config-dependent)
    - Layer 3: Background task manager (event_producer-dependent)
    - Layer 4: Health probe (depends on all infrastructure)
    """

    @property
    def stage_name(self) -> str:
        return "system"

    @asynccontextmanager
    async def compose(
        self,
        stack: DependencyStack,
        setup_input: SystemInput,
    ) -> AsyncIterator[SystemResources]:
        # Layer 0: No external dependencies
        cors_options = await stack.enter_dependency(CORSOptionsDependency(), None)
        metrics = await stack.enter_dependency(MetricsDependency(), None)
        gql_adapter = await stack.enter_dependency(GQLAdapterDependency(), None)

        # Layer 1: Config-dependent services
        jwt_validator = await stack.enter_dependency(JWTValidatorDependency(), setup_input.config)
        prometheus_client = await stack.enter_dependency(
            PrometheusClientDependency(), setup_input.config
        )
        sd_resources = await stack.enter_dependency(
            ServiceDiscoveryDependency(),
            ServiceDiscoveryInput(
                config=setup_input.config,
                etcd=setup_input.etcd,
                valkey_profile_target=setup_input.valkey_profile_target,
            ),
        )

        # Layer 3: Event-producer-dependent services
        background_task_manager = await stack.enter_dependency(
            BackgroundTaskManagerDependency(),
            BackgroundTaskManagerInput(
                event_producer=setup_input.event_producer,
                valkey_bgtask=setup_input.valkey.bgtask,
                server_id=setup_input.config.manager.id,
                bgtask_observer=metrics.bgtask,
            ),
        )

        # Layer 4: Infrastructure-dependent services
        health_probe = await stack.enter_dependency(
            HealthProbeDependency(),
            HealthProbeInput(
                db=setup_input.db,
                etcd=setup_input.etcd,
                valkey=setup_input.valkey,
            ),
        )

        yield SystemResources(
            cors_options=cors_options,
            metrics=metrics,
            gql_adapter=gql_adapter,
            jwt_validator=jwt_validator,
            prometheus_client=prometheus_client,
            service_discovery=sd_resources.service_discovery,
            sd_loop=sd_resources.sd_loop,
            background_task_manager=background_task_manager,
            health_probe=health_probe,
        )
