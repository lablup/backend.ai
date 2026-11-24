"""Component tests for the v2 session compute-schedule endpoint.

Exercises POST /v2/sessions/compute-schedule through the real aiohttp server,
the SDK v2 client, and a real SchedulingController against the real DB.
"""

from __future__ import annotations

import secrets
import uuid
from collections.abc import AsyncIterator, Callable, Coroutine
from decimal import Decimal
from typing import TYPE_CHECKING, Any, cast
from unittest.mock import AsyncMock, MagicMock

import pytest
import sqlalchemy as sa

from ai.backend.client.exceptions import BackendAPIError
from ai.backend.client.v2.exceptions import NotFoundError
from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.data.entity.agent import AgentUUID
from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.image import ImageID
from ai.backend.common.data.entity.kernel import KernelFieldType
from ai.backend.common.data.entity.kernel_group import KernelGroupFieldType
from ai.backend.common.data.entity.kernel_group_environ import KernelGroupEnvironFieldType
from ai.backend.common.data.entity.kernel_group_resource_slot import (
    KernelGroupResourceSlotFieldType,
)
from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.resource_group import (
    ResourceGroupEntityType,
    ResourceGroupID,
    ResourceGroupName,
)
from ai.backend.common.data.entity.resource_preset import ResourcePresetEntityType
from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.data.entity.user import UserEntityType
from ai.backend.common.dto.manager.v2.common import ResourceSlotEntryInput
from ai.backend.common.dto.manager.v2.scheduler.request import (
    ComputeScheduleInput,
    ComputeScheduleKernelResourceInput,
)
from ai.backend.common.dto.manager.v2.session.types import ClusterModeEnum
from ai.backend.common.dto.manager.v2.session_options.types import AgentSelectionPolicyEnum
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.plugin.monitor import ErrorPluginContext
from ai.backend.common.types import AgentId
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import FieldGroupMeta, GroupMeta
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.data.image.types import ImageStatus, ImageType
from ai.backend.manager.data.kernel.types import KernelInfo
from ai.backend.manager.data.kernel_group.types import (
    KernelGroupData,
    KernelGroupEnvironData,
    KernelGroupResourceSlotData,
)
from ai.backend.manager.data.secret.types import KeyProviderType
from ai.backend.manager.data.session.options import AgentSelectionPolicy, DefaultSessionOptions
from ai.backend.manager.dependencies.infrastructure.redis import ValkeyClients
from ai.backend.manager.models.agent.row import AgentRow
from ai.backend.manager.models.container_registry.row import ContainerRegistryRow
from ai.backend.manager.models.image.row import ImageRow
from ai.backend.manager.models.resource_group.row import resource_groups
from ai.backend.manager.models.resource_slot.row import AgentResourceRow
from ai.backend.manager.models.session.row import SessionRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.plugin.network import NetworkPluginContext
from ai.backend.manager.repositories.container_registry.db_source import ContainerRegistryDBSource
from ai.backend.manager.repositories.ops.v2.permission.provider import PermissionOpsProvider
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ops.v2.reconciler.provider import ReconcileOpsProvider
from ai.backend.manager.repositories.ops.v2.resource_policy.provider import (
    ResourcePolicyOpsProvider,
)
from ai.backend.manager.repositories.ops.v2.share.provider import ShareOpsProvider
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)
from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository
from ai.backend.manager.repositories.session.repository import SessionRepository
from ai.backend.manager.repositories.user.repository import UserRepository
from ai.backend.manager.secret.pool import KeyProviderPool
from ai.backend.manager.services.session.actions.lookup_bulk_kernel_group_environ_owner import (
    LookupBulkKernelGroupEnvironOwnerAction,
)
from ai.backend.manager.services.session.actions.lookup_bulk_kernel_group_owner import (
    LookupBulkKernelGroupOwnerAction,
)
from ai.backend.manager.services.session.actions.lookup_bulk_kernel_group_resource_slot_owner import (
    LookupBulkKernelGroupResourceSlotOwnerAction,
)
from ai.backend.manager.services.session.actions.lookup_bulk_kernel_owner import (
    LookupBulkKernelOwnerAction,
)
from ai.backend.manager.services.session.actions.lookup_kernel_field_owner import (
    LookupKernelFieldOwnerAction,
)
from ai.backend.manager.services.session.actions.lookup_kernel_group_environ_field_owner import (
    LookupKernelGroupEnvironFieldOwnerAction,
)
from ai.backend.manager.services.session.actions.lookup_kernel_group_field_owner import (
    LookupKernelGroupFieldOwnerAction,
)
from ai.backend.manager.services.session.actions.lookup_kernel_group_resource_slot_field_owner import (
    LookupKernelGroupResourceSlotFieldOwnerAction,
)
from ai.backend.manager.services.session.processors import SessionProcessors
from ai.backend.manager.services.session.resource_allocation.processors import (
    ResourceAllocationProcessors,
)
from ai.backend.manager.services.session.service import SessionService, SessionServiceArgs
from ai.backend.manager.sokovan.scheduler.hooks.post_transition import PostTransitionHookRegistry
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.pool import create_agent_selector
from ai.backend.manager.sokovan.scheduling_controller.scheduling_controller import (
    SchedulingController,
    SchedulingControllerArgs,
)

from .conftest import build_session_registries

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

    from ai.backend.common.plugin.hook_context import HookPluginContext

AgentFactoryFunc = Callable[[dict[str, str]], Coroutine[Any, Any, str]]


@pytest.fixture()
async def resource_slot_types_seed(db_engine: SAEngine) -> None:
    """Ensure resource_slot_types has seed data for cpu/mem slots."""
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.text(
                "INSERT INTO resource_slot_types (slot_name, slot_type, rank)"
                " VALUES ('cpu', 'count', 40), ('mem', 'bytes', 50)"
                " ON CONFLICT DO NOTHING"
            )
        )


@pytest.fixture()
async def compute_registry_fixture(db_engine: SAEngine) -> AsyncIterator[uuid.UUID]:
    """Insert a test Docker container registry and yield its UUID."""
    registry_id = uuid.uuid4()
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(ContainerRegistryRow.__table__).values(
                id=registry_id,
                url="https://registry.session.test.local",
                registry_name=f"session-registry-{registry_id.hex[:8]}",
                type=ContainerRegistryType.DOCKER,
            )
        )
    yield registry_id
    async with db_engine.begin() as conn:
        await conn.execute(
            ContainerRegistryRow.__table__.delete().where(
                ContainerRegistryRow.__table__.c.id == registry_id
            )
        )


@pytest.fixture()
async def compute_image_fixture(
    db_engine: SAEngine,
    compute_registry_fixture: uuid.UUID,
) -> AsyncIterator[ImageID]:
    """Insert an x86_64 image with min-only resource limits; yield its ID."""
    image_id = ImageID(uuid.uuid4())
    unique = secrets.token_hex(4)
    image_name = f"compute-image-{unique}"
    canonical = f"registry.session.test.local/testproject/{image_name}:latest"
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(ImageRow.__table__).values(
                id=image_id,
                name=canonical,
                project="testproject",
                image=image_name,
                tag="latest",
                registry="registry.session.test.local",
                registry_id=compute_registry_fixture,
                architecture="x86_64",
                config_digest=f"sha256:{image_id.hex * 2}",
                size_bytes=2048000,
                is_local=False,
                type=ImageType.COMPUTE,
                accelerators=None,
                labels={},
                resources={
                    "cpu": {"min": "1"},
                    "mem": {"min": "536870912"},
                },
                status=ImageStatus.ALIVE,
            )
        )
    yield image_id
    async with db_engine.begin() as conn:
        await conn.execute(ImageRow.__table__.delete().where(ImageRow.__table__.c.id == image_id))


@pytest.fixture()
async def agent_factory(
    db_engine: SAEngine,
    resource_group_name: ResourceGroupName,
    resource_group_id: ResourceGroupID,
) -> AsyncIterator[AgentFactoryFunc]:
    """Factory that seeds ALIVE schedulable x86_64 agents in the test scaling group."""
    created_ids: list[str] = []

    async def _create(available_slots: dict[str, str]) -> str:
        agent_id = f"i-test-{secrets.token_hex(4)}"
        agent_uuid = AgentUUID(uuid.uuid4())
        async with db_engine.begin() as conn:
            await conn.execute(
                sa.insert(AgentRow.__table__).values(
                    id=agent_id,
                    uuid=agent_uuid,
                    status=AgentStatus.ALIVE,
                    region="local",
                    scaling_group=resource_group_name,
                    resource_group_id=resource_group_id,
                    schedulable=True,
                    addr=f"10.0.0.{len(created_ids) + 1}:6001",
                    version="26.0.0",
                    architecture="x86_64",
                    compute_plugins={},
                )
            )
            # The scheduling read path sources capacity from the normalized
            # agent_resources table (filled by heartbeat in production).
            await conn.execute(
                sa.insert(AgentResourceRow.__table__),
                [
                    {
                        "agent_id": agent_id,
                        "agent_uuid": agent_uuid,
                        "slot_name": slot_name,
                        "capacity": Decimal(quantity),
                        "reserved": Decimal(0),
                        "used": Decimal(0),
                    }
                    for slot_name, quantity in available_slots.items()
                ],
            )
        created_ids.append(agent_id)
        return agent_id

    yield _create

    if created_ids:
        async with db_engine.begin() as conn:
            await conn.execute(
                AgentResourceRow.__table__.delete().where(
                    AgentResourceRow.__table__.c.agent_id.in_(created_ids)
                )
            )
            await conn.execute(
                AgentRow.__table__.delete().where(AgentRow.__table__.c.id.in_(created_ids))
            )


@pytest.fixture()
async def compute_session_processors(
    database_engine: ExtendedAsyncSAEngine,
    background_task_manager: BackgroundTaskManager,
    error_monitor: ErrorPluginContext,
    rbac_permission_repo: PermissionControllerRepository,
    storage_manager: StorageSessionManager,
    valkey_clients: ValkeyClients,
    config_provider: ManagerConfigProvider,
    event_producer: EventProducer,
    network_plugin_ctx: NetworkPluginContext,
    hook_plugin_ctx: HookPluginContext,
    resource_slot_types_seed: None,
    processor_registry: ProcessorRegistry[Any],
) -> SessionProcessors:
    """SessionProcessors wired with a real SchedulingController and UserRepository.

    Drives the actual compute-schedule path (spec preparation + agent
    selection) against the real DB instead of a mocked controller.
    """
    # The shared _TestConfigProvider mocks get_raw to "true" for every key,
    # which breaks the int-typed config/agent/max-container-count read in the
    # scheduling path; "not configured" is the realistic default here.
    cast(MagicMock, config_provider._legacy_etcd_config_loader).get_raw = AsyncMock(
        return_value=None
    )
    scheduler_repository = SchedulerRepository(
        database_engine,
        ReconcileOpsProvider(database_engine),
        valkey_clients.stat,
        valkey_clients.schedule,
        config_provider,
        storage_manager,
        RbacPermissionCheckRepository(PermissionOpsProvider(database_engine), config_provider),
        key_provider_pool=KeyProviderPool(providers=[], write_provider_type=KeyProviderType.PLAIN),
    )
    scheduling_controller = SchedulingController(
        SchedulingControllerArgs(
            repository=scheduler_repository,
            config_provider=config_provider,
            storage_manager=storage_manager,
            event_producer=event_producer,
            valkey_schedule=valkey_clients.schedule,
            network_plugin_ctx=network_plugin_ctx,
            hook_plugin_ctx=hook_plugin_ctx,
            agent_selector=create_agent_selector(
                config_provider.config.manager.agent_selection_resource_priority
            ),
            post_transition_hooks=PostTransitionHookRegistry(),
        )
    )
    args = SessionServiceArgs(
        agent_registry=AsyncMock(),
        event_fetcher=AsyncMock(),
        background_task_manager=background_task_manager,
        event_hub=AsyncMock(),
        error_monitor=error_monitor,
        idle_checker_host=AsyncMock(),
        session_repository=SessionRepository(
            database_engine,
            V2DBOpsProvider(database_engine),
            registry_db_source=ContainerRegistryDBSource(V2DBOpsProvider(database_engine)),
        ),
        scheduler_repository=scheduler_repository,
        scheduling_controller=scheduling_controller,
        appproxy_client_pool=AsyncMock(),
        user_repository=UserRepository(
            database_engine,
            V2DBOpsProvider(database_engine),
            ShareOpsProvider(database_engine),
            ResourcePolicyOpsProvider(database_engine),
            KeyProviderPool(providers=[], write_provider_type=KeyProviderType.PLAIN),
        ),
    )
    service = SessionService(args)
    return SessionProcessors(
        processor_registry.group(GroupMeta(SessionEntityType())),
        processor_registry.group(GroupMeta(ResourceGroupEntityType())),
        processor_registry.group(GroupMeta(SessionEntityType())).field_group(
            FieldGroupMeta(KernelFieldType()),
            KernelInfo,
            LookupKernelFieldOwnerAction,
            LookupBulkKernelOwnerAction,
        ),
        processor_registry.group(GroupMeta(SessionEntityType())).field_group(
            FieldGroupMeta(KernelGroupFieldType()),
            KernelGroupData,
            LookupKernelGroupFieldOwnerAction,
            LookupBulkKernelGroupOwnerAction,
        ),
        processor_registry.group(GroupMeta(SessionEntityType())).field_group(
            FieldGroupMeta(KernelGroupEnvironFieldType()),
            KernelGroupEnvironData,
            LookupKernelGroupEnvironFieldOwnerAction,
            LookupBulkKernelGroupEnvironOwnerAction,
        ),
        processor_registry.group(GroupMeta(SessionEntityType())).field_group(
            FieldGroupMeta(KernelGroupResourceSlotFieldType()),
            KernelGroupResourceSlotData,
            LookupKernelGroupResourceSlotFieldOwnerAction,
            LookupBulkKernelGroupResourceSlotOwnerAction,
        ),
        ResourceAllocationProcessors(
            processor_registry.group(GroupMeta(UserEntityType())),
            processor_registry.group(GroupMeta(ProjectEntityType())),
            processor_registry.group(GroupMeta(DomainEntityType())),
            processor_registry.group(GroupMeta(ResourceGroupEntityType())),
            processor_registry.group(GroupMeta(SessionEntityType())),
            processor_registry.group(GroupMeta(ResourcePresetEntityType())),
            MagicMock(),
        ),
        service,
    )


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    compute_session_processors: SessionProcessors,
) -> list[RouteRegistry]:
    """Serve v2 session routes backed by the real scheduling controller."""
    return build_session_registries(route_deps, compute_session_processors)


def _single_kernel_input(
    resource_group_id: ResourceGroupID,
    image_id: ImageID,
    *,
    cpu: str,
    mem: str,
    cluster_mode: ClusterModeEnum = ClusterModeEnum.SINGLE_NODE,
    designated_agent_ids: list[AgentId] | None = None,
    agent_selection_policy: AgentSelectionPolicyEnum | None = None,
) -> ComputeScheduleInput:
    return ComputeScheduleInput(
        kernels=[
            ComputeScheduleKernelResourceInput(
                image_id=image_id,
                resources=[
                    ResourceSlotEntryInput(resource_type="cpu", quantity=cpu),
                    ResourceSlotEntryInput(resource_type="mem", quantity=mem),
                ],
            )
        ],
        cluster_mode=cluster_mode,
        resource_group_id=resource_group_id,
        designated_agent_ids=designated_agent_ids,
        agent_selection_policy=agent_selection_policy,
    )


@pytest.fixture()
async def strict_agent_selection(
    db_engine: SAEngine,
    resource_group_id: ResourceGroupID,
) -> None:
    """Make the test resource group enforce designated agents strictly."""
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.update(resource_groups)
            .where(resource_groups.c.id == resource_group_id)
            .values(
                default_session_options=DefaultSessionOptions(
                    agent_selection_policy=AgentSelectionPolicy.STRICT,
                )
            )
        )


class TestComputeSchedule:
    async def test_fitting_kernel_succeeds(
        self,
        admin_v2_registry: V2ClientRegistry,
        resource_group_id: ResourceGroupID,
        compute_image_fixture: ImageID,
        agent_factory: AgentFactoryFunc,
    ) -> None:
        await agent_factory({"cpu": "8", "mem": "34359738368"})
        payload = await admin_v2_registry.session.compute_schedule(
            _single_kernel_input(
                resource_group_id, compute_image_fixture, cpu="1", mem="1073741824"
            )
        )
        assert len(payload.results) == 1
        result = payload.results[0]
        assert result.success is True
        assert result.reason_hint is None
        assert result.requested_architecture == "x86_64"
        requested = {entry.resource_type: entry.quantity for entry in result.requested_slots}
        assert requested["cpu"] == Decimal(1)
        assert requested["mem"] == Decimal(1073741824)

    async def test_oversized_kernel_returns_reduction_hint(
        self,
        admin_v2_registry: V2ClientRegistry,
        resource_group_id: ResourceGroupID,
        compute_image_fixture: ImageID,
        agent_factory: AgentFactoryFunc,
    ) -> None:
        """The hint reflects the best-fitting node's shortage, not a sum over nodes."""
        await agent_factory({"cpu": "4", "mem": "34359738368"})
        await agent_factory({"cpu": "8", "mem": "34359738368"})
        payload = await admin_v2_registry.session.compute_schedule(
            _single_kernel_input(
                resource_group_id, compute_image_fixture, cpu="10", mem="1073741824"
            )
        )
        result = payload.results[0]
        assert result.success is False
        assert result.reason_hint is not None
        assert result.reason_hint.required_reduction is not None
        reduction = {
            entry.resource_type: entry.quantity for entry in result.reason_hint.required_reduction
        }
        # 10 requested vs the larger agent's 8 cores: shortage vs the best
        # node is 2, not 6 (smaller node) nor 8 (sum over both nodes).
        assert reduction["cpu"] == Decimal(2)

    async def test_multi_kernel_results_correlate_by_index(
        self,
        admin_v2_registry: V2ClientRegistry,
        resource_group_id: ResourceGroupID,
        compute_image_fixture: ImageID,
        agent_factory: AgentFactoryFunc,
    ) -> None:
        await agent_factory({"cpu": "8", "mem": "34359738368"})
        body = ComputeScheduleInput(
            kernels=[
                ComputeScheduleKernelResourceInput(
                    image_id=compute_image_fixture,
                    resources=[
                        ResourceSlotEntryInput(resource_type="cpu", quantity="1"),
                        ResourceSlotEntryInput(resource_type="mem", quantity="1073741824"),
                    ],
                ),
                ComputeScheduleKernelResourceInput(
                    image_id=compute_image_fixture,
                    resources=[
                        ResourceSlotEntryInput(resource_type="cpu", quantity="100"),
                        ResourceSlotEntryInput(resource_type="mem", quantity="1073741824"),
                    ],
                ),
            ],
            cluster_mode=ClusterModeEnum.MULTI_NODE,
            resource_group_id=resource_group_id,
        )
        payload = await admin_v2_registry.session.compute_schedule(body)
        assert [result.success for result in payload.results] == [True, False]

    async def test_unknown_resource_group_returns_not_found(
        self,
        admin_v2_registry: V2ClientRegistry,
        compute_image_fixture: ImageID,
    ) -> None:
        unknown_rg = ResourceGroupID(uuid.uuid4())
        with pytest.raises(NotFoundError):
            await admin_v2_registry.session.compute_schedule(
                _single_kernel_input(unknown_rg, compute_image_fixture, cpu="1", mem="1073741824")
            )

    async def test_resource_group_without_agents_is_whole_request_error(
        self,
        admin_v2_registry: V2ClientRegistry,
        resource_group_id: ResourceGroupID,
        compute_image_fixture: ImageID,
    ) -> None:
        with pytest.raises(BackendAPIError) as exc_info:
            await admin_v2_registry.session.compute_schedule(
                _single_kernel_input(
                    resource_group_id, compute_image_fixture, cpu="1", mem="1073741824"
                )
            )
        assert exc_info.value.status == 503

    async def test_compute_schedule_does_not_persist_session(
        self,
        admin_v2_registry: V2ClientRegistry,
        resource_group_id: ResourceGroupID,
        compute_image_fixture: ImageID,
        agent_factory: AgentFactoryFunc,
        db_engine: SAEngine,
    ) -> None:
        await agent_factory({"cpu": "8", "mem": "34359738368"})
        await admin_v2_registry.session.compute_schedule(
            _single_kernel_input(
                resource_group_id, compute_image_fixture, cpu="1", mem="1073741824"
            )
        )
        async with db_engine.begin() as conn:
            count = await conn.scalar(
                sa.select(sa.func.count())
                .select_from(SessionRow.__table__)
                .where(SessionRow.__table__.c.name == "compute-schedule")
            )
        assert count == 0


class TestComputeScheduleDesignatedAgents:
    async def test_strict_policy_limits_fitting_to_designated_agents(
        self,
        admin_v2_registry: V2ClientRegistry,
        resource_group_id: ResourceGroupID,
        compute_image_fixture: ImageID,
        agent_factory: AgentFactoryFunc,
        strict_agent_selection: None,
    ) -> None:
        """A too-small designated agent fails the fit even though a larger
        undesignated agent could hold the kernel."""
        small_agent = await agent_factory({"cpu": "2", "mem": "34359738368"})
        await agent_factory({"cpu": "8", "mem": "34359738368"})
        payload = await admin_v2_registry.session.compute_schedule(
            _single_kernel_input(
                resource_group_id,
                compute_image_fixture,
                cpu="4",
                mem="1073741824",
                designated_agent_ids=[AgentId(small_agent)],
            )
        )
        result = payload.results[0]
        assert result.success is False
        assert result.reason_hint is not None
        assert result.reason_hint.required_reduction is not None
        reduction = {
            entry.resource_type: entry.quantity for entry in result.reason_hint.required_reduction
        }
        assert reduction["cpu"] == Decimal(2)

    async def test_designated_agent_with_capacity_fits(
        self,
        admin_v2_registry: V2ClientRegistry,
        resource_group_id: ResourceGroupID,
        compute_image_fixture: ImageID,
        agent_factory: AgentFactoryFunc,
        strict_agent_selection: None,
    ) -> None:
        await agent_factory({"cpu": "2", "mem": "34359738368"})
        large_agent = await agent_factory({"cpu": "8", "mem": "34359738368"})
        payload = await admin_v2_registry.session.compute_schedule(
            _single_kernel_input(
                resource_group_id,
                compute_image_fixture,
                cpu="4",
                mem="1073741824",
                designated_agent_ids=[AgentId(large_agent)],
            )
        )
        assert payload.results[0].success is True

    async def test_request_policy_overrides_resource_group_default(
        self,
        admin_v2_registry: V2ClientRegistry,
        resource_group_id: ResourceGroupID,
        compute_image_fixture: ImageID,
        agent_factory: AgentFactoryFunc,
    ) -> None:
        """A STRICT policy in the request overrides the resource group's
        default PREFERRED policy, so a too-small designated agent fails."""
        small_agent = await agent_factory({"cpu": "2", "mem": "34359738368"})
        await agent_factory({"cpu": "8", "mem": "34359738368"})
        payload = await admin_v2_registry.session.compute_schedule(
            _single_kernel_input(
                resource_group_id,
                compute_image_fixture,
                cpu="4",
                mem="1073741824",
                designated_agent_ids=[AgentId(small_agent)],
                agent_selection_policy=AgentSelectionPolicyEnum.STRICT,
            )
        )
        assert payload.results[0].success is False

    async def test_preferred_policy_falls_back_past_designated_agents(
        self,
        admin_v2_registry: V2ClientRegistry,
        resource_group_id: ResourceGroupID,
        compute_image_fixture: ImageID,
        agent_factory: AgentFactoryFunc,
    ) -> None:
        """Under the default PREFERRED policy a designated agent without
        capacity does not block fitting onto other agents — the same
        semantics as the real scheduling path."""
        small_agent = await agent_factory({"cpu": "2", "mem": "34359738368"})
        await agent_factory({"cpu": "8", "mem": "34359738368"})
        payload = await admin_v2_registry.session.compute_schedule(
            _single_kernel_input(
                resource_group_id,
                compute_image_fixture,
                cpu="4",
                mem="1073741824",
                designated_agent_ids=[AgentId(small_agent)],
            )
        )
        assert payload.results[0].success is True
