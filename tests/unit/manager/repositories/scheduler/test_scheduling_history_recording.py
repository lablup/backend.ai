"""
Tests for scheduling history recording in enqueue_session() and mark_sessions_terminating().

Regression tests for BA-4694: Ensure scheduling history records are created
for enqueue (initial creation to PENDING) and RUNNING to TERMINATING transitions.
"""

import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa
from dateutil.tz import tzutc
from sqlalchemy.orm import aliased

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.domain import DomainID, DomainName
from ai.backend.common.data.entity.image import ImageID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.resource_group import ResourceGroupID, ResourceGroupName
from ai.backend.common.data.entity.resource_slot import ResourceSlotName
from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.events.event_types.kernel.types import KernelLifecycleEventReason
from ai.backend.common.types import (
    AccessKey,
    ClusterMode,
    DefaultForUnspecified,
    ResourceSlot,
    ResourceSlotEntry,
    SecretKey,
    SessionId,
    SessionResult,
    SessionTypes,
)
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.data.image.types import ImageStatus, ImageType
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.network.types import NetworkType
from ai.backend.manager.data.session.options import (
    KernelExecutionSpec,
    KernelResourceConfig,
    SchedulingTarget,
    SessionHandlerOptions,
    SessionOptions,
)
from ai.backend.manager.data.session.spec import (
    KernelSpec,
    SessionClassification,
    SessionIdentity,
    SessionNetwork,
    SessionResourceSpec,
    SessionScope,
    SessionSpec,
)
from ai.backend.manager.data.session.types import SchedulingResult, SessionStatus
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.errors.image import ImageNotFound
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.project import ProjectRow
from ai.backend.manager.models.rbac_models import (
    AssociationScopesEntitiesRow,
    EntityFieldRow,
    RoleRow,
    UserRoleRow,
)
from ai.backend.manager.models.resource_group import ResourceGroupOpts, ResourceGroupRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_slot import ResourceAllocationRow
from ai.backend.manager.models.resource_slot.row import ResourceSlotTypeRow
from ai.backend.manager.models.scheduling_history.row import SessionSchedulingHistoryRow
from ai.backend.manager.models.session import SessionDependencyRow, SessionRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.ops.v2.reconciler.provider import ReconcileOpsProvider
from ai.backend.manager.repositories.scheduler import SchedulerRepository
from ai.backend.manager.repositories.scheduler.db_source.db_source import ScheduleDBSource
from ai.backend.manager.secret.types import SecretValue
from ai.backend.testutils.db import with_tables
from ai.backend.testutils.fixtures import DomainFixtureData


class TestEnqueueSessionSchedulingHistory:
    """Test that enqueue_session() creates scheduling history records."""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database connection with tables created. TRUNCATE CASCADE handles cleanup."""
        async with with_tables(
            database_connection,
            [
                # FK dependency order: parents first
                DomainRow,
                ResourceGroupRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                RoleRow,
                UserRoleRow,
                UserRow,
                KeyPairRow,
                ProjectRow,
                AssociationScopesEntitiesRow,
                EntityFieldRow,
                VirtualEntityRow,
                EntityMembershipRow,
                ScopeBindingRow,
                AgentRow,
                ContainerRegistryRow,
                ImageRow,
                SessionRow,
                KernelRow,
                ResourceSlotTypeRow,
                ResourceAllocationRow,
                SessionDependencyRow,
                SessionSchedulingHistoryRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def test_domain(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[DomainFixtureData, None]:
        """Create test domain and return domain name."""
        domain_id = DomainID(uuid.uuid4())
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            domain = DomainRow(
                id=domain_id,
                name=domain_name,
                total_resource_slots=ResourceSlot({
                    "cpu": Decimal("1000"),
                    "mem": Decimal("1048576"),
                }),
            )
            db_sess.add(domain)
            await db_sess.flush()

        yield DomainFixtureData(domain_name=DomainName(domain_name), domain_id=domain_id)

    @pytest.fixture
    async def test_scaling_group_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create test scaling group and return scaling group name."""
        sg_name = f"test-sgroup-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            sg = ResourceGroupRow(
                name=sg_name,
                driver="static",
                scheduler="fifo",
                scheduler_opts=ResourceGroupOpts(
                    allowed_session_types=[],
                    pending_timeout=timedelta(hours=1),
                    config={},
                ),
                driver_opts={},
                is_active=True,
            )
            db_sess.add(sg)
            await db_sess.flush()

        yield sg_name

    @pytest.fixture
    async def test_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create test resource policy and return policy name."""
        policy_name = f"test-policy-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            project_policy = ProjectResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=-1,
                max_network_count=10,
            )
            db_sess.add(project_policy)
            await db_sess.flush()

        yield policy_name

    @pytest.fixture
    async def test_user_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create test user resource policy and return policy name."""
        policy_name = f"test-user-policy-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            user_policy = UserResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=10,
                max_customized_image_count=3,
            )
            db_sess.add(user_policy)
            await db_sess.flush()

        yield policy_name

    @pytest.fixture
    async def test_keypair_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create test keypair resource policy and return policy name."""
        policy_name = f"test-keypair-policy-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            keypair_policy = KeyPairResourcePolicyRow(
                name=policy_name,
                default_for_unspecified=DefaultForUnspecified.LIMITED,
                total_resource_slots=ResourceSlot({
                    "cpu": Decimal("100"),
                    "mem": Decimal("102400"),
                }),
                max_concurrent_sessions=10,
                max_containers_per_session=1,
                idle_timeout=600,
                max_session_lifetime=0,
                allowed_vfolder_hosts={},
            )
            db_sess.add(keypair_policy)
            await db_sess.flush()

        yield policy_name

    @pytest.fixture
    async def test_user_uuid(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: DomainFixtureData,
        test_user_resource_policy_name: str,
    ) -> AsyncGenerator[uuid.UUID, None]:
        """Create test user and return user UUID."""
        user_uuid = uuid.uuid4()

        async with db_with_cleanup.begin_session() as db_sess:
            user = UserRow(
                uuid=user_uuid,
                email=f"test-user-{uuid.uuid4().hex[:8]}@test.com",
                username=f"test-user-{uuid.uuid4().hex[:8]}",
                role=UserRole.USER,
                status=UserStatus.ACTIVE,
                domain_name=test_domain.domain_name,
                resource_policy=test_user_resource_policy_name,
                domain_id=test_domain.domain_id,
            )
            db_sess.add(user)
            await db_sess.flush()

        yield user_uuid

    @pytest.fixture
    async def test_access_key(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_user_uuid: uuid.UUID,
        test_keypair_resource_policy_name: str,
    ) -> AsyncGenerator[AccessKey, None]:
        """Create test keypair and return access key."""
        access_key = AccessKey(f"AKIA{uuid.uuid4().hex[:16].upper()}")

        async with db_with_cleanup.begin_session() as db_sess:
            keypair = KeyPairRow(
                access_key=access_key,
                secret_key=SecretValue(SecretKey(f"SK{uuid.uuid4().hex}")),
                is_active=True,
                is_admin=False,
                resource_policy=test_keypair_resource_policy_name,
                rate_limit=1000,
                num_queries=0,
                user=test_user_uuid,
            )
            db_sess.add(keypair)
            await db_sess.flush()

        yield access_key

    @pytest.fixture
    async def test_group_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: DomainFixtureData,
        test_resource_policy_name: str,
    ) -> AsyncGenerator[uuid.UUID, None]:
        """Create test group and return group ID."""
        group_id = uuid.uuid4()

        async with db_with_cleanup.begin_session() as db_sess:
            group = ProjectRow(
                id=group_id,
                name=f"test-group-{uuid.uuid4().hex[:8]}",
                description="Test group",
                is_active=True,
                domain_name=test_domain.domain_name,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts={},
                resource_policy=test_resource_policy_name,
            )
            db_sess.add(group)
            await db_sess.flush()

        yield group_id

    @pytest.fixture
    async def test_image_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ImageID, None]:
        """Register a container registry and one image, and return the image id."""
        registry_id = uuid.uuid4()
        image_id = ImageID(uuid.uuid4())

        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                ContainerRegistryRow(
                    id=ContainerRegistryID(registry_id),
                    url="https://registry.example.com",
                    registry_name="test-registry",
                    type=ContainerRegistryType.DOCKER,
                )
            )
            await db_sess.flush()
            image = ImageRow(
                name="test-image:latest",
                project=None,
                architecture="x86_64",
                registry_id=registry_id,
                registry="test-registry",
                image="test-image",
                tag="latest",
                config_digest="sha256:" + "0" * 64,
                size_bytes=1024,
                type=ImageType.COMPUTE,
                accelerators="",
                labels={},
                resources={},
                status=ImageStatus.ALIVE,
            )
            image.id = image_id
            db_sess.add(image)
            await db_sess.flush()

        yield image_id

    @pytest.fixture
    async def resource_slot_types(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[None, None]:
        """Register the slot types the requested amounts refer to."""
        async with db_with_cleanup.begin_session() as db_sess:
            for slot_name, slot_type in [("cpu", "count"), ("mem", "bytes")]:
                db_sess.add(ResourceSlotTypeRow(slot_name=slot_name, slot_type=slot_type))
            await db_sess.flush()

        yield

    @pytest.fixture
    async def enrolled_scopes(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_user_uuid: uuid.UUID,
        test_group_id: uuid.UUID,
    ) -> AsyncGenerator[None, None]:
        """Provision the user's and the project's virtual entities.

        Existing deployments carry them from the backfill migration; a session joins
        both as a member, and a parent without a virtual entity fails the write.
        """
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add_all([
                VirtualEntityRow(entity_type="user", entity_id=test_user_uuid),
                VirtualEntityRow(entity_type="project", entity_id=test_group_id),
            ])
            await db_sess.flush()

        yield

    def _spec(
        self,
        *,
        session_id: SessionID,
        domain: DomainFixtureData,
        resource_group_id: ResourceGroupID,
        resource_group_name: str,
        project_id: uuid.UUID,
        user_uuid: uuid.UUID,
        access_key: AccessKey,
        image_id: ImageID,
        dependencies: tuple[SessionID, ...] = (),
    ) -> SessionSpec:
        execution_spec = KernelExecutionSpec(
            resource_input=KernelResourceConfig(
                image_id=image_id,
                resources=[
                    ResourceSlotEntry(resource_type=ResourceSlotName("cpu"), quantity="2"),
                    ResourceSlotEntry(resource_type=ResourceSlotName("mem"), quantity="1024"),
                ],
            ),
        )
        return SessionSpec(
            resource_spec=SessionResourceSpec(
                identity=SessionIdentity(
                    session_id=session_id,
                    creation_id=f"creation-{uuid.uuid4().hex[:8]}",
                    session_name=f"session-{uuid.uuid4().hex[:8]}",
                    access_key=access_key,
                    user_uuid=user_uuid,
                ),
                classification=SessionClassification(session_type=SessionTypes.INTERACTIVE),
                network=SessionNetwork(network_type=NetworkType.VOLATILE),
                dependencies=dependencies,
                options=SessionOptions(
                    priority=10,
                    is_preemptible=False,
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    cluster_size=1,
                    scheduling_target=SchedulingTarget(),
                    kernel_groups=[],
                    handler_options=SessionHandlerOptions(),
                ),
                kernel_specs=(
                    KernelSpec(
                        cluster_role="main",
                        cluster_idx=1,
                        cluster_hostname="main1",
                        local_rank=0,
                        execution_spec=execution_spec,
                    ),
                ),
            ),
            scope=SessionScope(
                domain_id=domain.domain_id,
                domain_name=domain.domain_name,
                project_id=ProjectID(project_id),
                resource_group_id=resource_group_id,
                resource_group_name=ResourceGroupName(resource_group_name),
            ),
        )

    async def _resource_group_id(
        self,
        db: ExtendedAsyncSAEngine,
        resource_group_name: str,
    ) -> ResourceGroupID:
        async with db.begin_readonly_session() as db_sess:
            return ResourceGroupID(
                await db_sess.scalar(
                    sa.select(ResourceGroupRow.id).where(
                        ResourceGroupRow.name == resource_group_name
                    )
                )
            )

    async def test_enqueue_writes_the_session_its_kernels_and_the_history(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: DomainFixtureData,
        test_scaling_group_name: str,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_access_key: AccessKey,
        test_image_id: ImageID,
        enrolled_scopes: None,
        resource_slot_types: None,
    ) -> None:
        """One enqueue writes the session, its kernels, their requested slots, and the
        PENDING history row, and enrolls the session under its user and project."""
        db_source = ScheduleDBSource(db_with_cleanup, ReconcileOpsProvider(db_with_cleanup))
        session_id = SessionID(uuid.uuid4())
        spec = self._spec(
            session_id=session_id,
            domain=test_domain,
            resource_group_id=await self._resource_group_id(
                db_with_cleanup, test_scaling_group_name
            ),
            resource_group_name=test_scaling_group_name,
            project_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
            image_id=test_image_id,
        )

        enqueued = await db_source.enqueue_session_from_spec(spec)

        assert enqueued == SessionId(session_id)
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            session = await db_sess.scalar(sa.select(SessionRow).where(SessionRow.id == session_id))
            assert session is not None
            assert session.status == SessionStatus.PENDING

            kernels = (
                (
                    await db_sess.execute(
                        sa.select(KernelRow).where(KernelRow.session_id == session_id)
                    )
                )
                .scalars()
                .all()
            )
            assert len(kernels) == 1
            assert kernels[0].status == KernelStatus.PENDING

            allocations = (
                (
                    await db_sess.execute(
                        sa.select(ResourceAllocationRow).where(
                            ResourceAllocationRow.kernel_id == kernels[0].id
                        )
                    )
                )
                .scalars()
                .all()
            )
            assert {allocation.slot_name: allocation.requested for allocation in allocations} == {
                "cpu": Decimal("2"),
                "mem": Decimal("1024"),
            }

            history = await db_sess.scalar(
                sa.select(SessionSchedulingHistoryRow).where(
                    SessionSchedulingHistoryRow.session_id == session_id
                )
            )
            assert history is not None
            assert history.phase == "enqueue"
            assert history.result == str(SchedulingResult.SUCCESS)
            assert history.to_status == str(SessionStatus.PENDING)
            assert history.attempts == 1

            # The session became its own scope and joined its user and project.
            assert (
                await db_sess.scalar(
                    sa.select(VirtualEntityRow.id).where(
                        VirtualEntityRow.entity_type == "session",
                        VirtualEntityRow.entity_id == session_id,
                    )
                )
                is not None
            )
            scope = aliased(VirtualEntityRow, name="scope_virtual_entity")
            parents = (
                await db_sess.execute(
                    sa.select(scope.entity_type, scope.entity_id)
                    .select_from(ScopeBindingRow)
                    .join(
                        VirtualEntityRow,
                        VirtualEntityRow.id == ScopeBindingRow.virtual_entity_id,
                    )
                    .join(scope, scope.id == ScopeBindingRow.scope_entity_id)
                    .where(VirtualEntityRow.entity_id == session_id)
                )
            ).all()
            assert {(row.entity_type, row.entity_id) for row in parents} == {
                ("session", session_id),
                ("user", UserID(test_user_uuid)),
                ("project", ProjectID(test_group_id)),
            }

    async def test_enqueue_records_the_declared_dependency(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: DomainFixtureData,
        test_scaling_group_name: str,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_access_key: AccessKey,
        test_image_id: ImageID,
        enrolled_scopes: None,
        resource_slot_types: None,
    ) -> None:
        """A dependency the caller declares becomes one row of the dependency graph."""
        db_source = ScheduleDBSource(db_with_cleanup, ReconcileOpsProvider(db_with_cleanup))
        resource_group_id = await self._resource_group_id(db_with_cleanup, test_scaling_group_name)
        first_id = SessionID(uuid.uuid4())
        await db_source.enqueue_session_from_spec(
            self._spec(
                session_id=first_id,
                domain=test_domain,
                resource_group_id=resource_group_id,
                resource_group_name=test_scaling_group_name,
                project_id=test_group_id,
                user_uuid=test_user_uuid,
                access_key=test_access_key,
                image_id=test_image_id,
            )
        )

        second_id = SessionID(uuid.uuid4())
        await db_source.enqueue_session_from_spec(
            self._spec(
                session_id=second_id,
                domain=test_domain,
                resource_group_id=resource_group_id,
                resource_group_name=test_scaling_group_name,
                project_id=test_group_id,
                user_uuid=test_user_uuid,
                access_key=test_access_key,
                image_id=test_image_id,
                dependencies=(first_id,),
            )
        )

        async with db_with_cleanup.begin_readonly_session() as db_sess:
            dependencies = (
                (
                    await db_sess.execute(
                        sa.select(SessionDependencyRow).where(
                            SessionDependencyRow.session_id == second_id
                        )
                    )
                )
                .scalars()
                .all()
            )
            assert [dependency.depends_on for dependency in dependencies] == [first_id]

    async def test_enqueue_refuses_an_unknown_dependency(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: DomainFixtureData,
        test_scaling_group_name: str,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_access_key: AccessKey,
        test_image_id: ImageID,
        enrolled_scopes: None,
    ) -> None:
        """A dependency naming no session leaves nothing behind."""
        db_source = ScheduleDBSource(db_with_cleanup, ReconcileOpsProvider(db_with_cleanup))
        session_id = SessionID(uuid.uuid4())
        spec = self._spec(
            session_id=session_id,
            domain=test_domain,
            resource_group_id=await self._resource_group_id(
                db_with_cleanup, test_scaling_group_name
            ),
            resource_group_name=test_scaling_group_name,
            project_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
            image_id=test_image_id,
            dependencies=(SessionID(uuid.uuid4()),),
        )

        with pytest.raises(InvalidAPIParameters):
            await db_source.enqueue_session_from_spec(spec)

        async with db_with_cleanup.begin_readonly_session() as db_sess:
            assert (
                await db_sess.scalar(sa.select(SessionRow).where(SessionRow.id == session_id))
            ) is None

    async def test_enqueue_refuses_an_unregistered_image(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: DomainFixtureData,
        test_scaling_group_name: str,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_access_key: AccessKey,
        enrolled_scopes: None,
    ) -> None:
        """A kernel whose image is not registered fails before anything is written."""
        db_source = ScheduleDBSource(db_with_cleanup, ReconcileOpsProvider(db_with_cleanup))
        session_id = SessionID(uuid.uuid4())
        spec = self._spec(
            session_id=session_id,
            domain=test_domain,
            resource_group_id=await self._resource_group_id(
                db_with_cleanup, test_scaling_group_name
            ),
            resource_group_name=test_scaling_group_name,
            project_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
            image_id=ImageID(uuid.uuid4()),
        )

        with pytest.raises(ImageNotFound):
            await db_source.enqueue_session_from_spec(spec)

        async with db_with_cleanup.begin_readonly_session() as db_sess:
            assert (
                await db_sess.scalar(sa.select(SessionRow).where(SessionRow.id == session_id))
            ) is None


class TestMarkTerminatingSchedulingHistory:
    """Test that _mark_sessions_as_terminating() creates scheduling history records."""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database connection with tables created. TRUNCATE CASCADE handles cleanup."""
        async with with_tables(
            database_connection,
            [
                # FK dependency order: parents first
                DomainRow,
                ResourceGroupRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                RoleRow,
                UserRoleRow,
                UserRow,
                KeyPairRow,
                ProjectRow,
                AgentRow,
                ContainerRegistryRow,
                ImageRow,
                SessionRow,
                KernelRow,
                ResourceSlotTypeRow,
                ResourceAllocationRow,
                SessionSchedulingHistoryRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    def test_domain_id(self) -> DomainID:
        return DomainID(uuid.uuid4())

    @pytest.fixture
    def test_scaling_group_id(self) -> ResourceGroupID:
        return ResourceGroupID(uuid.uuid4())

    @pytest.fixture
    async def test_domain(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_id: DomainID,
    ) -> AsyncGenerator[DomainFixtureData, None]:
        """Create test domain and return domain name."""
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            domain = DomainRow(
                id=test_domain_id,
                name=domain_name,
                total_resource_slots=ResourceSlot({
                    "cpu": Decimal("1000"),
                    "mem": Decimal("1048576"),
                }),
            )
            db_sess.add(domain)
            await db_sess.flush()

        yield DomainFixtureData(domain_name=DomainName(domain_name), domain_id=test_domain_id)

    @pytest.fixture
    async def test_scaling_group_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_scaling_group_id: ResourceGroupID,
    ) -> AsyncGenerator[str, None]:
        """Create test scaling group and return scaling group name."""
        sg_name = f"test-sgroup-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            sg = ResourceGroupRow(
                id=test_scaling_group_id,
                name=sg_name,
                driver="static",
                scheduler="fifo",
                scheduler_opts=ResourceGroupOpts(
                    allowed_session_types=[],
                    pending_timeout=timedelta(hours=1),
                    config={},
                ),
                driver_opts={},
                is_active=True,
            )
            db_sess.add(sg)
            await db_sess.flush()

        yield sg_name

    @pytest.fixture
    async def test_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create test resource policy and return policy name."""
        policy_name = f"test-policy-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            project_policy = ProjectResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=-1,
                max_network_count=10,
            )
            db_sess.add(project_policy)
            await db_sess.flush()

        yield policy_name

    @pytest.fixture
    async def test_user_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create test user resource policy and return policy name."""
        policy_name = f"test-user-policy-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            user_policy = UserResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=10,
                max_customized_image_count=3,
            )
            db_sess.add(user_policy)
            await db_sess.flush()

        yield policy_name

    @pytest.fixture
    async def test_keypair_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create test keypair resource policy and return policy name."""
        policy_name = f"test-keypair-policy-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            keypair_policy = KeyPairResourcePolicyRow(
                name=policy_name,
                default_for_unspecified=DefaultForUnspecified.LIMITED,
                total_resource_slots=ResourceSlot({
                    "cpu": Decimal("100"),
                    "mem": Decimal("102400"),
                }),
                max_concurrent_sessions=10,
                max_containers_per_session=1,
                idle_timeout=600,
                max_session_lifetime=0,
                allowed_vfolder_hosts={},
            )
            db_sess.add(keypair_policy)
            await db_sess.flush()

        yield policy_name

    @pytest.fixture
    async def test_user_uuid(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: DomainFixtureData,
        test_user_resource_policy_name: str,
    ) -> AsyncGenerator[uuid.UUID, None]:
        """Create test user and return user UUID."""
        user_uuid = uuid.uuid4()

        async with db_with_cleanup.begin_session() as db_sess:
            user = UserRow(
                uuid=user_uuid,
                email=f"test-user-{uuid.uuid4().hex[:8]}@test.com",
                username=f"test-user-{uuid.uuid4().hex[:8]}",
                role=UserRole.USER,
                status=UserStatus.ACTIVE,
                domain_name=test_domain.domain_name,
                resource_policy=test_user_resource_policy_name,
                domain_id=test_domain.domain_id,
            )
            db_sess.add(user)
            await db_sess.flush()

        yield user_uuid

    @pytest.fixture
    async def test_access_key(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_user_uuid: uuid.UUID,
        test_keypair_resource_policy_name: str,
    ) -> AsyncGenerator[AccessKey, None]:
        """Create test keypair and return access key."""
        access_key = AccessKey(f"AKIA{uuid.uuid4().hex[:16].upper()}")

        async with db_with_cleanup.begin_session() as db_sess:
            keypair = KeyPairRow(
                access_key=access_key,
                secret_key=SecretValue(SecretKey(f"SK{uuid.uuid4().hex}")),
                is_active=True,
                is_admin=False,
                resource_policy=test_keypair_resource_policy_name,
                rate_limit=1000,
                num_queries=0,
                user=test_user_uuid,
            )
            db_sess.add(keypair)
            await db_sess.flush()

        yield access_key

    @pytest.fixture
    async def test_group_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: DomainFixtureData,
        test_resource_policy_name: str,
    ) -> AsyncGenerator[uuid.UUID, None]:
        """Create test group and return group ID."""
        group_id = uuid.uuid4()

        async with db_with_cleanup.begin_session() as db_sess:
            group = ProjectRow(
                id=group_id,
                name=f"test-group-{uuid.uuid4().hex[:8]}",
                description="Test group",
                is_active=True,
                domain_name=test_domain.domain_name,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts={},
                resource_policy=test_resource_policy_name,
            )
            db_sess.add(group)
            await db_sess.flush()

        yield group_id

    @pytest.fixture
    async def test_agent_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_scaling_group_name: str,
        test_scaling_group_id: ResourceGroupID,
    ) -> AsyncGenerator[str, None]:
        """Create test agent and return agent ID."""
        agent_id = f"test-agent-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            agent = AgentRow(
                id=agent_id,
                status=AgentStatus.ALIVE,
                region="local",
                scaling_group=test_scaling_group_name,
                resource_group_id=test_scaling_group_id,
                addr="127.0.0.1:6001",
                version="1.0.0",
                architecture="x86_64",
            )
            db_sess.add(agent)
            await db_sess.flush()

        yield agent_id

    async def _create_session_with_kernel(
        self,
        db: ExtendedAsyncSAEngine,
        *,
        session_status: SessionStatus,
        kernel_status: KernelStatus,
        domain_name: str,
        domain_id: DomainID,
        resource_group_name: str,
        resource_group_id: ResourceGroupID,
        group_id: uuid.UUID,
        user_uuid: uuid.UUID,
        access_key: AccessKey,
        agent_id: str,
    ) -> SessionId:
        """Helper to create a session with a kernel in given statuses."""
        session_id = SessionId(uuid.uuid4())
        kernel_id = uuid.uuid4()

        async with db.begin_session() as db_sess:
            session = SessionRow(
                id=session_id,
                name=f"test-session-{uuid.uuid4().hex[:8]}",
                session_type=SessionTypes.INTERACTIVE,
                domain_name=domain_name,
                domain_id=domain_id,
                group_id=group_id,
                scaling_group_name=resource_group_name,
                resource_group_id=resource_group_id,
                status=session_status,
                status_info="test",
                cluster_mode=ClusterMode.SINGLE_NODE,
                created_at=datetime.now(tzutc()),
                images=["python:3.8"],
                vfolder_mounts=[],
                environ={},
                result=SessionResult.UNDEFINED,
            )
            db_sess.add(session)
            await db_sess.flush()

            kernel = KernelRow(
                id=kernel_id,
                session_id=session_id,
                agent=agent_id,
                agent_addr="127.0.0.1:6001",
                scaling_group=resource_group_name,
                resource_group_id=resource_group_id,
                cluster_idx=0,
                cluster_role="main",
                cluster_hostname=f"kernel-{uuid.uuid4().hex[:8]}",
                image="python:3.8",
                architecture="x86_64",
                registry="docker.io",
                container_id=f"container-{uuid.uuid4().hex[:8]}",
                status=kernel_status,
                status_changed=datetime.now(tzutc()),
                domain_name=domain_name,
                group_id=group_id,
                user_uuid=user_uuid,
                access_key=access_key,
                mounts=[],
                environ={},
                vfolder_mounts=[],
                preopen_ports=[],
                repl_in_port=2001,
                repl_out_port=2002,
                stdin_port=2003,
                stdout_port=2004,
            )
            db_sess.add(kernel)
            await db_sess.flush()

        return session_id

    @pytest.fixture
    def scheduler_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> SchedulerRepository:
        return SchedulerRepository(
            db_with_cleanup,
            ReconcileOpsProvider(db_with_cleanup),
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(),
        )

    @pytest.fixture
    async def running_session_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: DomainFixtureData,
        test_domain_id: DomainID,
        test_scaling_group_name: str,
        test_scaling_group_id: ResourceGroupID,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_access_key: AccessKey,
        test_agent_id: str,
    ) -> SessionId:
        return await self._create_session_with_kernel(
            db_with_cleanup,
            session_status=SessionStatus.RUNNING,
            kernel_status=KernelStatus.RUNNING,
            domain_name=test_domain.domain_name,
            domain_id=test_domain_id,
            resource_group_name=test_scaling_group_name,
            resource_group_id=test_scaling_group_id,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
            agent_id=test_agent_id,
        )

    async def test_mark_sessions_as_terminating_creates_scheduling_history(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        running_session_id: SessionId,
    ) -> None:
        """Test that mark_sessions_terminating() creates history records for RUNNING sessions."""
        db_source = ScheduleDBSource(db_with_cleanup, ReconcileOpsProvider(db_with_cleanup))

        result = await db_source.mark_sessions_terminating([running_session_id])
        assert running_session_id in result.terminating_sessions

        # Verify scheduling history record was created
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            history_stmt = sa.select(SessionSchedulingHistoryRow).where(
                SessionSchedulingHistoryRow.session_id == running_session_id
            )
            history_record = await db_sess.scalar(history_stmt)
            assert history_record is not None
            assert history_record.phase == "mark_terminating"
            assert history_record.result == str(SchedulingResult.SUCCESS)
            assert history_record.from_status == str(SessionStatus.RUNNING)
            assert history_record.to_status == str(SessionStatus.TERMINATING)
            assert history_record.message == "mark_terminating success"

    async def test_mark_sessions_as_terminating_records_custom_history_message(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        running_session_id: SessionId,
        scheduler_repository: SchedulerRepository,
    ) -> None:
        result = await scheduler_repository.mark_sessions_terminating(
            [running_session_id],
            reason=KernelLifecycleEventReason.IDLE_TIMEOUT.value,
            message="idle check timeout",
        )

        assert result.terminating_sessions == [running_session_id]
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            history = await db_sess.scalar(
                sa.select(SessionSchedulingHistoryRow).where(
                    SessionSchedulingHistoryRow.session_id == running_session_id
                )
            )
        assert history is not None
        assert history.message == "idle check timeout"

    async def test_cancel_pending_creates_scheduling_history(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: DomainFixtureData,
        test_domain_id: DomainID,
        test_scaling_group_name: str,
        test_scaling_group_id: ResourceGroupID,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_access_key: AccessKey,
        test_agent_id: str,
    ) -> None:
        """Test that mark_sessions_terminating() records history for cancelled PENDING sessions."""
        db_source = ScheduleDBSource(db_with_cleanup, ReconcileOpsProvider(db_with_cleanup))

        session_id = await self._create_session_with_kernel(
            db_with_cleanup,
            session_status=SessionStatus.PENDING,
            kernel_status=KernelStatus.PENDING,
            domain_name=test_domain.domain_name,
            domain_id=test_domain_id,
            resource_group_name=test_scaling_group_name,
            resource_group_id=test_scaling_group_id,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
            agent_id=test_agent_id,
        )

        result = await db_source.mark_sessions_terminating([session_id])
        assert session_id in result.cancelled_sessions

        # Verify scheduling history record was created
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            history_stmt = sa.select(SessionSchedulingHistoryRow).where(
                SessionSchedulingHistoryRow.session_id == session_id
            )
            history_record = await db_sess.scalar(history_stmt)
            assert history_record is not None
            assert history_record.phase == "cancel"
            assert history_record.result == str(SchedulingResult.SUCCESS)
            assert history_record.from_status == str(SessionStatus.PENDING)
            assert history_record.to_status == str(SessionStatus.CANCELLED)
            assert history_record.message == "USER_REQUESTED"

    async def test_force_terminate_creates_scheduling_history(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: DomainFixtureData,
        test_domain_id: DomainID,
        test_scaling_group_name: str,
        test_scaling_group_id: ResourceGroupID,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_access_key: AccessKey,
        test_agent_id: str,
    ) -> None:
        """Test that mark_sessions_terminating(forced=True) creates TERMINATED history records."""
        db_source = ScheduleDBSource(db_with_cleanup, ReconcileOpsProvider(db_with_cleanup))

        session_id = await self._create_session_with_kernel(
            db_with_cleanup,
            session_status=SessionStatus.RUNNING,
            kernel_status=KernelStatus.RUNNING,
            domain_name=test_domain.domain_name,
            domain_id=test_domain_id,
            resource_group_name=test_scaling_group_name,
            resource_group_id=test_scaling_group_id,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
            agent_id=test_agent_id,
        )

        result = await db_source.mark_sessions_terminating([session_id], forced=True)
        assert session_id in result.force_terminated_sessions

        async with db_with_cleanup.begin_readonly_session() as db_sess:
            history_stmt = sa.select(SessionSchedulingHistoryRow).where(
                SessionSchedulingHistoryRow.session_id == session_id
            )
            history_record = await db_sess.scalar(history_stmt)
            assert history_record is not None
            assert history_record.phase == "force_terminate"
            assert history_record.result == str(SchedulingResult.SUCCESS)
            assert history_record.from_status == str(SessionStatus.RUNNING)
            assert history_record.to_status == str(SessionStatus.TERMINATED)
            assert history_record.message == "force_terminate success"

    async def test_force_terminate_from_terminating_creates_scheduling_history(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: DomainFixtureData,
        test_domain_id: DomainID,
        test_scaling_group_name: str,
        test_scaling_group_id: ResourceGroupID,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_access_key: AccessKey,
        test_agent_id: str,
    ) -> None:
        """Forced termination should record history for TERMINATING sessions too."""
        db_source = ScheduleDBSource(db_with_cleanup, ReconcileOpsProvider(db_with_cleanup))

        session_id = await self._create_session_with_kernel(
            db_with_cleanup,
            session_status=SessionStatus.TERMINATING,
            kernel_status=KernelStatus.TERMINATING,
            domain_name=test_domain.domain_name,
            domain_id=test_domain_id,
            resource_group_name=test_scaling_group_name,
            resource_group_id=test_scaling_group_id,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
            agent_id=test_agent_id,
        )

        result = await db_source.mark_sessions_terminating([session_id], forced=True)
        assert session_id in result.force_terminated_sessions

        async with db_with_cleanup.begin_readonly_session() as db_sess:
            history_stmt = sa.select(SessionSchedulingHistoryRow).where(
                SessionSchedulingHistoryRow.session_id == session_id
            )
            history_record = await db_sess.scalar(history_stmt)
            assert history_record is not None
            assert history_record.phase == "force_terminate"
            assert history_record.result == str(SchedulingResult.SUCCESS)
            assert history_record.from_status == str(SessionStatus.TERMINATING)
            assert history_record.to_status == str(SessionStatus.TERMINATED)
            assert history_record.message == "force_terminate success"

    async def test_mark_sessions_as_terminating_captures_correct_from_status(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: DomainFixtureData,
        test_domain_id: DomainID,
        test_scaling_group_name: str,
        test_scaling_group_id: ResourceGroupID,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_access_key: AccessKey,
        test_agent_id: str,
    ) -> None:
        """Test that different from_statuses are correctly captured for each session."""
        db_source = ScheduleDBSource(db_with_cleanup, ReconcileOpsProvider(db_with_cleanup))

        # Create sessions in different terminatable statuses
        running_session_id = await self._create_session_with_kernel(
            db_with_cleanup,
            session_status=SessionStatus.RUNNING,
            kernel_status=KernelStatus.RUNNING,
            domain_name=test_domain.domain_name,
            domain_id=test_domain_id,
            resource_group_name=test_scaling_group_name,
            resource_group_id=test_scaling_group_id,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
            agent_id=test_agent_id,
        )
        scheduled_session_id = await self._create_session_with_kernel(
            db_with_cleanup,
            session_status=SessionStatus.SCHEDULED,
            kernel_status=KernelStatus.SCHEDULED,
            domain_name=test_domain.domain_name,
            domain_id=test_domain_id,
            resource_group_name=test_scaling_group_name,
            resource_group_id=test_scaling_group_id,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
            agent_id=test_agent_id,
        )

        result = await db_source.mark_sessions_terminating([
            running_session_id,
            scheduled_session_id,
        ])
        assert running_session_id in result.terminating_sessions
        assert scheduled_session_id in result.terminating_sessions

        # Verify each history record has the correct from_status
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            # Check RUNNING session history
            running_history_stmt = sa.select(SessionSchedulingHistoryRow).where(
                SessionSchedulingHistoryRow.session_id == running_session_id
            )
            running_history = await db_sess.scalar(running_history_stmt)
            assert running_history is not None
            assert running_history.from_status == str(SessionStatus.RUNNING)
            assert running_history.to_status == str(SessionStatus.TERMINATING)

            # Check SCHEDULED session history
            scheduled_history_stmt = sa.select(SessionSchedulingHistoryRow).where(
                SessionSchedulingHistoryRow.session_id == scheduled_session_id
            )
            scheduled_history = await db_sess.scalar(scheduled_history_stmt)
            assert scheduled_history is not None
            assert scheduled_history.from_status == str(SessionStatus.SCHEDULED)
            assert scheduled_history.to_status == str(SessionStatus.TERMINATING)
