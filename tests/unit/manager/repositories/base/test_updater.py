"""Integration tests for updater with real database."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator, Callable, Sequence
from typing import TYPE_CHECKING, Any
from uuid import UUID

import pytest
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.elements import ColumnElement

from ai.backend.manager.errors.repository import (
    ForeignKeyViolationError,
    RepositoryIntegrityError,
    UniqueConstraintViolationError,
)

# ORM relationship cluster registration: SQLAlchemy's global
# configure_mappers() must resolve every string relationship reachable from
# the rows this isolated test registers, so the whole domain cluster is
# imported here. _ORM_CLUSTER below keeps these imports from being pruned.
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.association_container_registries_groups import (
    AssociationContainerRegistriesGroupsRow,
)
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.deployment_auto_scaling_policy import DeploymentAutoScalingPolicyRow
from ai.backend.manager.models.deployment_policy import DeploymentPolicyRow
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import (
    EndpointAutoScalingRuleRow,
    EndpointRow,
    EndpointTokenRow,
)
from ai.backend.manager.models.fair_share import (
    DomainFairShareRow,
    ProjectFairShareRow,
    UserFairShareRow,
)
from ai.backend.manager.models.group import AssocGroupUserRow, GroupRow
from ai.backend.manager.models.image import ImageAliasRow, ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.network import NetworkRow
from ai.backend.manager.models.notification import NotificationChannelRow, NotificationRuleRow
from ai.backend.manager.models.rbac_models import (
    AssociationScopesEntitiesRow,
    ObjectPermissionRow,
    RoleRow,
    UserRoleRow,
)
from ai.backend.manager.models.replica_group import ReplicaGroupRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.models.resource_slot import (
    AgentResourceRow,
    DeploymentRevisionResourceSlotRow,
    ResourceSlotTypeRow,
)
from ai.backend.manager.models.resource_usage_history import (
    DomainUsageBucketRow,
    KernelUsageRecordRow,
    ProjectUsageBucketRow,
    UserUsageBucketRow,
)
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.runtime_variant import RuntimeVariantRow
from ai.backend.manager.models.runtime_variant_preset import RuntimeVariantPresetRow
from ai.backend.manager.models.scaling_group import (
    ScalingGroupForDomainRow,
    ScalingGroupForKeypairsRow,
    ScalingGroupForProjectRow,
    ScalingGroupRow,
)
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.vfolder import VFolderInvitationRow, VFolderPermissionRow, VFolderRow
from ai.backend.manager.repositories.base import (
    BatchUpdater,
    BatchUpdaterResult,
    BatchUpdaterSpec,
    BulkUpdaterError,
    BulkUpdaterResult,
    Updater,
    UpdaterResult,
    UpdaterSpec,
    execute_batch_updater,
    execute_bulk_updater_partial,
    execute_updater,
)
from ai.backend.manager.repositories.base.types import IntegrityErrorCheck

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


_ORM_CLUSTER = (
    AgentResourceRow,
    AgentRow,
    AssocGroupUserRow,
    AssociationContainerRegistriesGroupsRow,
    AssociationScopesEntitiesRow,
    ContainerRegistryRow,
    DeploymentAutoScalingPolicyRow,
    DeploymentPolicyRow,
    DeploymentRevisionResourceSlotRow,
    DeploymentRevisionRow,
    DomainFairShareRow,
    DomainRow,
    DomainUsageBucketRow,
    EndpointAutoScalingRuleRow,
    EndpointRow,
    EndpointTokenRow,
    GroupRow,
    ImageAliasRow,
    ImageRow,
    KernelRow,
    KernelUsageRecordRow,
    KeyPairResourcePolicyRow,
    KeyPairRow,
    NetworkRow,
    NotificationChannelRow,
    NotificationRuleRow,
    ObjectPermissionRow,
    ProjectFairShareRow,
    ProjectResourcePolicyRow,
    ProjectUsageBucketRow,
    ReplicaGroupRow,
    ResourcePresetRow,
    ResourceSlotTypeRow,
    RoleRow,
    RoutingRow,
    RuntimeVariantPresetRow,
    RuntimeVariantRow,
    ScalingGroupForDomainRow,
    ScalingGroupForKeypairsRow,
    ScalingGroupForProjectRow,
    ScalingGroupRow,
    SessionRow,
    UserFairShareRow,
    UserResourcePolicyRow,
    UserRoleRow,
    UserRow,
    UserUsageBucketRow,
    VFolderInvitationRow,
    VFolderPermissionRow,
    VFolderRow,
)


class UpdaterTestRowInt(Base):  # type: ignore[misc]
    """ORM model for updater testing with integer PK."""

    __tablename__ = "test_updater_int_pk"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    status: Mapped[str] = mapped_column(sa.String(20), nullable=False, default="pending")
    value: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)


class UpdaterTestRowUUID(Base):  # type: ignore[misc]
    """ORM model for updater testing with UUID PK."""

    __tablename__ = "test_updater_uuid_pk"
    __table_args__ = {"extend_existing": True}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    status: Mapped[str] = mapped_column(sa.String(20), nullable=False, default="pending")


class UpdaterTestRowStr(Base):  # type: ignore[misc]
    """ORM model for updater testing with string PK."""

    __tablename__ = "test_updater_str_pk"
    __table_args__ = {"extend_existing": True}

    id: Mapped[str] = mapped_column(sa.String(50), primary_key=True)
    name: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    status: Mapped[str] = mapped_column(sa.String(20), nullable=False, default="pending")


# Single Updater Specs for each row type


class IntPKStatusUpdaterSpec(UpdaterSpec[UpdaterTestRowInt]):
    """Updater spec for updating status on integer PK table."""

    def __init__(self, new_status: str, new_value: int | None = None) -> None:
        self._new_status = new_status
        self._new_value = new_value

    @property
    def row_class(self) -> type[UpdaterTestRowInt]:
        return UpdaterTestRowInt

    def build_values(self) -> dict[str, Any]:
        values: dict[str, Any] = {"status": self._new_status}
        if self._new_value is not None:
            values["value"] = self._new_value
        return values


class IntPKNoValuesUpdaterSpec(UpdaterSpec[UpdaterTestRowInt]):
    """Updater spec that produces no column changes (empty build_values)."""

    @property
    def row_class(self) -> type[UpdaterTestRowInt]:
        return UpdaterTestRowInt

    def build_values(self) -> dict[str, Any]:
        return {}


class UUIDPKStatusUpdaterSpec(UpdaterSpec[UpdaterTestRowUUID]):
    """Updater spec for updating status on UUID PK table."""

    def __init__(self, new_status: str) -> None:
        self._new_status = new_status

    @property
    def row_class(self) -> type[UpdaterTestRowUUID]:
        return UpdaterTestRowUUID

    def build_values(self) -> dict[str, Any]:
        return {"status": self._new_status}


class StrPKStatusUpdaterSpec(UpdaterSpec[UpdaterTestRowStr]):
    """Updater spec for updating status on string PK table."""

    def __init__(self, new_status: str) -> None:
        self._new_status = new_status

    @property
    def row_class(self) -> type[UpdaterTestRowStr]:
        return UpdaterTestRowStr

    def build_values(self) -> dict[str, Any]:
        return {"status": self._new_status}


# Batch Updater Specs


class IntPKBatchUpdaterSpec(BatchUpdaterSpec[UpdaterTestRowInt]):
    """Batch updater spec for updating status on integer PK table."""

    def __init__(self, new_status: str) -> None:
        self._new_status = new_status

    @property
    def row_class(self) -> type[UpdaterTestRowInt]:
        return UpdaterTestRowInt

    def build_values(self) -> dict[str, Any]:
        return {"status": self._new_status}


class TestUpdaterIntPK:
    """Tests for single-row updater with integer PK."""

    @pytest.fixture
    async def int_row_class(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[type[UpdaterTestRowInt], None]:
        """Create ORM test table and return row class."""
        async with database_connection.begin() as conn:
            await conn.run_sync(
                lambda c: Base.metadata.create_all(c, [UpdaterTestRowInt.__table__])
            )

        yield UpdaterTestRowInt

        async with database_connection.begin() as conn:
            await conn.execute(sa.text("DROP TABLE IF EXISTS test_updater_int_pk CASCADE"))

    @pytest.fixture
    async def sample_data(
        self,
        database_connection: ExtendedAsyncSAEngine,
        int_row_class: type[UpdaterTestRowInt],
    ) -> AsyncGenerator[list[int], None]:
        """Insert sample data and return their IDs."""
        ids: list[int] = []
        async with database_connection.begin_session() as db_sess:
            for i in range(3):
                row = UpdaterTestRowInt(name=f"item-{i}", status="pending", value=i * 10)
                db_sess.add(row)
                await db_sess.flush()
                ids.append(row.id)
        yield ids

    async def test_update_by_int_pk(
        self,
        database_connection: ExtendedAsyncSAEngine,
        int_row_class: type[UpdaterTestRowInt],
        sample_data: list[int],
    ) -> None:
        """Test updating a single row by integer PK."""
        async with database_connection.begin_session() as db_sess:
            target_id = sample_data[0]
            updater: Updater[UpdaterTestRowInt] = Updater(
                spec=IntPKStatusUpdaterSpec(new_status="active"),
                pk_value=target_id,
            )

            result = await execute_updater(db_sess, updater)

            assert result is not None
            assert isinstance(result, UpdaterResult)
            assert result.row.status == "active"
            assert result.row.id == target_id

    async def test_update_multiple_fields(
        self,
        database_connection: ExtendedAsyncSAEngine,
        int_row_class: type[UpdaterTestRowInt],
        sample_data: list[int],
    ) -> None:
        """Test updating multiple fields at once."""
        async with database_connection.begin_session() as db_sess:
            target_id = sample_data[1]
            updater: Updater[UpdaterTestRowInt] = Updater(
                spec=IntPKStatusUpdaterSpec(new_status="completed", new_value=999),
                pk_value=target_id,
            )

            result = await execute_updater(db_sess, updater)

            assert result is not None
            assert result.row.status == "completed"
            assert result.row.value == 999

    async def test_update_no_matching_rows(
        self,
        database_connection: ExtendedAsyncSAEngine,
        int_row_class: type[UpdaterTestRowInt],
        sample_data: list[int],
    ) -> None:
        """Test updating when PK doesn't exist."""
        async with database_connection.begin_session() as db_sess:
            updater: Updater[UpdaterTestRowInt] = Updater(
                spec=IntPKStatusUpdaterSpec(new_status="active"),
                pk_value=99999,
            )

            result = await execute_updater(db_sess, updater)

            assert result is None

    async def test_update_no_values_returns_current_row(
        self,
        database_connection: ExtendedAsyncSAEngine,
        int_row_class: type[UpdaterTestRowInt],
        sample_data: list[int],
    ) -> None:
        """Empty build_values returns the current row, not None (None means not-found only)."""
        async with database_connection.begin_session() as db_sess:
            target_id = sample_data[0]
            updater: Updater[UpdaterTestRowInt] = Updater(
                spec=IntPKNoValuesUpdaterSpec(),
                pk_value=target_id,
            )

            result = await execute_updater(db_sess, updater)

            assert result is not None
            assert result.row.id == target_id

    async def test_update_no_values_missing_row_returns_none(
        self,
        database_connection: ExtendedAsyncSAEngine,
        int_row_class: type[UpdaterTestRowInt],
        sample_data: list[int],
    ) -> None:
        """Empty build_values with a missing PK still returns None."""
        async with database_connection.begin_session() as db_sess:
            updater: Updater[UpdaterTestRowInt] = Updater(
                spec=IntPKNoValuesUpdaterSpec(),
                pk_value=99999,
            )

            result = await execute_updater(db_sess, updater)

            assert result is None


class TestUpdaterUUIDPK:
    """Tests for single-row updater with UUID PK."""

    @pytest.fixture
    async def uuid_row_class(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[type[UpdaterTestRowUUID], None]:
        """Create ORM test table and return row class."""
        async with database_connection.begin() as conn:
            await conn.run_sync(
                lambda c: Base.metadata.create_all(c, [UpdaterTestRowUUID.__table__])
            )

        yield UpdaterTestRowUUID

        async with database_connection.begin() as conn:
            await conn.execute(sa.text("DROP TABLE IF EXISTS test_updater_uuid_pk CASCADE"))

    @pytest.fixture
    async def sample_data(
        self,
        database_connection: ExtendedAsyncSAEngine,
        uuid_row_class: type[UpdaterTestRowUUID],
    ) -> AsyncGenerator[list[UUID], None]:
        """Insert sample data and return their UUIDs."""
        ids: list[UUID] = []
        async with database_connection.begin_session() as db_sess:
            for i in range(3):
                row = UpdaterTestRowUUID(id=uuid.uuid4(), name=f"item-{i}", status="pending")
                db_sess.add(row)
                await db_sess.flush()
                ids.append(row.id)
        yield ids

    async def test_update_by_uuid_pk(
        self,
        database_connection: ExtendedAsyncSAEngine,
        uuid_row_class: type[UpdaterTestRowUUID],
        sample_data: list[UUID],
    ) -> None:
        """Test updating a single row by UUID PK."""
        async with database_connection.begin_session() as db_sess:
            target_id = sample_data[0]
            updater: Updater[UpdaterTestRowUUID] = Updater(
                spec=UUIDPKStatusUpdaterSpec(new_status="active"),
                pk_value=target_id,
            )

            result = await execute_updater(db_sess, updater)

            assert result is not None
            assert isinstance(result, UpdaterResult)
            assert result.row.status == "active"
            assert result.row.id == target_id

    async def test_update_no_matching_uuid(
        self,
        database_connection: ExtendedAsyncSAEngine,
        uuid_row_class: type[UpdaterTestRowUUID],
        sample_data: list[UUID],
    ) -> None:
        """Test updating when UUID PK doesn't exist."""
        async with database_connection.begin_session() as db_sess:
            non_existent_id = uuid.uuid4()
            updater: Updater[UpdaterTestRowUUID] = Updater(
                spec=UUIDPKStatusUpdaterSpec(new_status="active"),
                pk_value=non_existent_id,
            )

            result = await execute_updater(db_sess, updater)

            assert result is None


class TestUpdaterStrPK:
    """Tests for single-row updater with string PK."""

    @pytest.fixture
    async def str_row_class(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[type[UpdaterTestRowStr], None]:
        """Create ORM test table and return row class."""
        async with database_connection.begin() as conn:
            await conn.run_sync(
                lambda c: Base.metadata.create_all(c, [UpdaterTestRowStr.__table__])
            )

        yield UpdaterTestRowStr

        async with database_connection.begin() as conn:
            await conn.execute(sa.text("DROP TABLE IF EXISTS test_updater_str_pk CASCADE"))

    @pytest.fixture
    async def sample_data(
        self,
        database_connection: ExtendedAsyncSAEngine,
        str_row_class: type[UpdaterTestRowStr],
    ) -> AsyncGenerator[list[str], None]:
        """Insert sample data and return their string IDs."""
        ids: list[str] = []
        async with database_connection.begin_session() as db_sess:
            for i in range(3):
                str_id = f"item-key-{i}"
                row = UpdaterTestRowStr(id=str_id, name=f"item-{i}", status="pending")
                db_sess.add(row)
                await db_sess.flush()
                ids.append(str_id)
        yield ids

    async def test_update_by_str_pk(
        self,
        database_connection: ExtendedAsyncSAEngine,
        str_row_class: type[UpdaterTestRowStr],
        sample_data: list[str],
    ) -> None:
        """Test updating a single row by string PK."""
        async with database_connection.begin_session() as db_sess:
            target_id = sample_data[0]
            updater: Updater[UpdaterTestRowStr] = Updater(
                spec=StrPKStatusUpdaterSpec(new_status="active"),
                pk_value=target_id,
            )

            result = await execute_updater(db_sess, updater)

            assert result is not None
            assert isinstance(result, UpdaterResult)
            assert result.row.status == "active"
            assert result.row.id == target_id

    async def test_update_no_matching_str(
        self,
        database_connection: ExtendedAsyncSAEngine,
        str_row_class: type[UpdaterTestRowStr],
        sample_data: list[str],
    ) -> None:
        """Test updating when string PK doesn't exist."""
        async with database_connection.begin_session() as db_sess:
            updater: Updater[UpdaterTestRowStr] = Updater(
                spec=StrPKStatusUpdaterSpec(new_status="active"),
                pk_value="non-existent-key",
            )

            result = await execute_updater(db_sess, updater)

            assert result is None


def _make_int_pk_in_condition(
    ids: list[int],
) -> Callable[[], ColumnElement[bool]]:
    """Create a typed condition for IN clause with integer PKs."""
    return lambda: UpdaterTestRowInt.__table__.c.id.in_(ids)


class TestBatchUpdater:
    """Tests for batch updater operations."""

    @pytest.fixture
    async def int_row_class(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[type[UpdaterTestRowInt], None]:
        """Create ORM test table and return row class."""
        async with database_connection.begin() as conn:
            await conn.run_sync(
                lambda c: Base.metadata.create_all(c, [UpdaterTestRowInt.__table__])
            )

        yield UpdaterTestRowInt

        async with database_connection.begin() as conn:
            await conn.execute(sa.text("DROP TABLE IF EXISTS test_updater_int_pk CASCADE"))

    @pytest.fixture
    async def sample_data(
        self,
        database_connection: ExtendedAsyncSAEngine,
        int_row_class: type[UpdaterTestRowInt],
    ) -> AsyncGenerator[list[int], None]:
        """Insert sample data and return their IDs."""
        ids: list[int] = []
        async with database_connection.begin_session() as db_sess:
            for i in range(3):
                row = UpdaterTestRowInt(name=f"item-{i}", status="pending", value=i * 10)
                db_sess.add(row)
                await db_sess.flush()
                ids.append(row.id)
        yield ids

    async def test_bulk_update(
        self,
        database_connection: ExtendedAsyncSAEngine,
        int_row_class: type[UpdaterTestRowInt],
        sample_data: list[int],
    ) -> None:
        """Test updating multiple rows at once."""
        async with database_connection.begin_session() as db_sess:
            spec = IntPKBatchUpdaterSpec(new_status="processed")
            updater: BatchUpdater[UpdaterTestRowInt] = BatchUpdater(
                spec=spec,
                conditions=[
                    lambda: UpdaterTestRowInt.__table__.c.status == "pending",
                ],
            )

            result = await execute_batch_updater(db_sess, updater)

            assert isinstance(result, BatchUpdaterResult)
            assert result.updated_count == 3

            query = (
                sa.select(sa.func.count())
                .select_from(UpdaterTestRowInt.__table__)
                .where(UpdaterTestRowInt.__table__.c.status == "processed")
            )
            count = (await db_sess.execute(query)).scalar()
            assert count == 3

    async def test_bulk_update_with_multiple_conditions(
        self,
        database_connection: ExtendedAsyncSAEngine,
        int_row_class: type[UpdaterTestRowInt],
        sample_data: list[int],
    ) -> None:
        """Test batch update with multiple AND conditions."""
        async with database_connection.begin_session() as db_sess:
            # Only update rows with status="pending" AND value >= 10
            # sample_data has values: 0, 10, 20 -> should update 2 rows
            spec = IntPKBatchUpdaterSpec(new_status="filtered")
            updater: BatchUpdater[UpdaterTestRowInt] = BatchUpdater(
                spec=spec,
                conditions=[
                    lambda: UpdaterTestRowInt.__table__.c.status == "pending",
                    lambda: UpdaterTestRowInt.__table__.c.value >= 10,
                ],
            )

            result = await execute_batch_updater(db_sess, updater)

            assert isinstance(result, BatchUpdaterResult)
            assert result.updated_count == 2

            query = (
                sa.select(sa.func.count())
                .select_from(UpdaterTestRowInt.__table__)
                .where(UpdaterTestRowInt.__table__.c.status == "filtered")
            )
            count = (await db_sess.execute(query)).scalar()
            assert count == 2

    async def test_bulk_update_no_matching_rows(
        self,
        database_connection: ExtendedAsyncSAEngine,
        int_row_class: type[UpdaterTestRowInt],
        sample_data: list[int],
    ) -> None:
        """Test batch update when no rows match."""
        async with database_connection.begin_session() as db_sess:
            spec = IntPKBatchUpdaterSpec(new_status="processed")
            updater: BatchUpdater[UpdaterTestRowInt] = BatchUpdater(
                spec=spec,
                conditions=[
                    lambda: UpdaterTestRowInt.__table__.c.status == "nonexistent",
                ],
            )

            result = await execute_batch_updater(db_sess, updater)

            assert isinstance(result, BatchUpdaterResult)
            assert result.updated_count == 0

    async def test_bulk_update_empty_table(
        self,
        database_connection: ExtendedAsyncSAEngine,
        int_row_class: type[UpdaterTestRowInt],
    ) -> None:
        """Test batch updating an empty table."""
        async with database_connection.begin_session() as db_sess:
            spec = IntPKBatchUpdaterSpec(new_status="processed")
            updater: BatchUpdater[UpdaterTestRowInt] = BatchUpdater(
                spec=spec,
                conditions=[
                    lambda: UpdaterTestRowInt.__table__.c.status == "pending",
                ],
            )

            result = await execute_batch_updater(db_sess, updater)

            assert isinstance(result, BatchUpdaterResult)
            assert result.updated_count == 0

    async def test_bulk_update_by_pk_list_all_exist(
        self,
        database_connection: ExtendedAsyncSAEngine,
        int_row_class: type[UpdaterTestRowInt],
        sample_data: list[int],
    ) -> None:
        """Test batch update with IN clause when all PKs exist."""
        async with database_connection.begin_session() as db_sess:
            target_ids = sample_data[:2]  # First two IDs
            spec = IntPKBatchUpdaterSpec(new_status="processed")
            updater: BatchUpdater[UpdaterTestRowInt] = BatchUpdater(
                spec=spec,
                conditions=[_make_int_pk_in_condition(target_ids)],
            )

            result = await execute_batch_updater(db_sess, updater)

            assert isinstance(result, BatchUpdaterResult)
            assert result.updated_count == 2  # All requested PKs updated

            # Verify only requested rows were updated
            query = (
                sa.select(UpdaterTestRowInt.__table__.c.id)
                .select_from(UpdaterTestRowInt.__table__)
                .where(UpdaterTestRowInt.__table__.c.status == "processed")
            )
            updated_ids = [row[0] for row in (await db_sess.execute(query)).fetchall()]
            assert set(updated_ids) == set(target_ids)

    async def test_bulk_update_by_pk_list_partial_exist(
        self,
        database_connection: ExtendedAsyncSAEngine,
        int_row_class: type[UpdaterTestRowInt],
        sample_data: list[int],
    ) -> None:
        """Test batch update with IN clause when some PKs don't exist (partial failure)."""
        async with database_connection.begin_session() as db_sess:
            existing_id = sample_data[0]
            non_existing_id = 99999
            target_ids = [existing_id, non_existing_id]
            requested_count = len(target_ids)

            spec = IntPKBatchUpdaterSpec(new_status="processed")
            updater: BatchUpdater[UpdaterTestRowInt] = BatchUpdater(
                spec=spec,
                conditions=[_make_int_pk_in_condition(target_ids)],
            )

            result = await execute_batch_updater(db_sess, updater)

            assert isinstance(result, BatchUpdaterResult)
            assert result.updated_count == 1  # Only one exists

            # Partial failure detection: requested - updated = failed
            failed_count = requested_count - result.updated_count
            assert failed_count == 1

    async def test_bulk_update_by_pk_list_none_exist(
        self,
        database_connection: ExtendedAsyncSAEngine,
        int_row_class: type[UpdaterTestRowInt],
        sample_data: list[int],
    ) -> None:
        """Test batch update with IN clause when no PKs exist."""
        async with database_connection.begin_session() as db_sess:
            non_existing_ids = [99998, 99999]
            requested_count = len(non_existing_ids)

            spec = IntPKBatchUpdaterSpec(new_status="processed")
            updater: BatchUpdater[UpdaterTestRowInt] = BatchUpdater(
                spec=spec,
                conditions=[_make_int_pk_in_condition(non_existing_ids)],
            )

            result = await execute_batch_updater(db_sess, updater)

            assert isinstance(result, BatchUpdaterResult)
            assert result.updated_count == 0

            # All failed
            failed_count = requested_count - result.updated_count
            assert failed_count == 2

    async def test_bulk_update_by_pk_list_empty_list(
        self,
        database_connection: ExtendedAsyncSAEngine,
        int_row_class: type[UpdaterTestRowInt],
        sample_data: list[int],
    ) -> None:
        """Test batch update with empty PK list."""
        async with database_connection.begin_session() as db_sess:
            empty_ids: list[int] = []

            spec = IntPKBatchUpdaterSpec(new_status="processed")
            updater: BatchUpdater[UpdaterTestRowInt] = BatchUpdater(
                spec=spec,
                conditions=[_make_int_pk_in_condition(empty_ids)],
            )

            result = await execute_batch_updater(db_sess, updater)

            assert isinstance(result, BatchUpdaterResult)
            assert result.updated_count == 0


# --- Integrity error handling tests ---


class UpdaterTestRowWithUnique(Base):  # type: ignore[misc]
    """ORM model for updater integrity error testing with a unique constraint on name."""

    __tablename__ = "test_updater_unique"
    __table_args__ = (
        sa.UniqueConstraint("name", name="uq_test_updater_unique_name"),
        {"extend_existing": True},
    )

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    status: Mapped[str] = mapped_column(sa.String(20), nullable=False, default="pending")


class _DuplicateNameError(UniqueConstraintViolationError):
    """Test domain error for duplicate name."""

    error_type = "https://test/duplicate-name"
    error_title = "Name already exists."


class UniqueNameUpdaterSpec(UpdaterSpec[UpdaterTestRowWithUnique]):
    """Updater spec that triggers unique constraint violation."""

    def __init__(
        self,
        new_name: str,
        checks: Sequence[IntegrityErrorCheck] = (),
    ) -> None:
        self._new_name = new_name
        self._checks = checks

    @property
    def row_class(self) -> type[UpdaterTestRowWithUnique]:
        return UpdaterTestRowWithUnique

    def build_values(self) -> dict[str, Any]:
        return {"name": self._new_name}

    @property
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return self._checks


class UniqueNameBatchUpdaterSpec(BatchUpdaterSpec[UpdaterTestRowWithUnique]):
    """Batch updater spec that triggers unique constraint violation."""

    def __init__(
        self,
        new_name: str,
        checks: Sequence[IntegrityErrorCheck] = (),
    ) -> None:
        self._new_name = new_name
        self._checks = checks

    @property
    def row_class(self) -> type[UpdaterTestRowWithUnique]:
        return UpdaterTestRowWithUnique

    def build_values(self) -> dict[str, Any]:
        return {"name": self._new_name}

    @property
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return self._checks


class TestUpdaterIntegrityError:
    """Tests for integrity error handling in execute_updater."""

    @pytest.fixture
    async def unique_row_class(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[type[UpdaterTestRowWithUnique], None]:
        async with database_connection.begin() as conn:
            await conn.run_sync(
                lambda c: Base.metadata.create_all(c, [UpdaterTestRowWithUnique.__table__])
            )
        yield UpdaterTestRowWithUnique
        async with database_connection.begin() as conn:
            await conn.execute(sa.text("DROP TABLE IF EXISTS test_updater_unique CASCADE"))

    @pytest.fixture
    async def two_rows(
        self,
        database_connection: ExtendedAsyncSAEngine,
        unique_row_class: type[UpdaterTestRowWithUnique],
    ) -> AsyncGenerator[list[int], None]:
        ids: list[int] = []
        async with database_connection.begin_session() as db_sess:
            for name in ("alice", "bob"):
                row = UpdaterTestRowWithUnique(name=name, status="active")
                db_sess.add(row)
                await db_sess.flush()
                ids.append(row.id)
        yield ids

    async def test_integrity_error_with_matching_check(
        self,
        database_connection: ExtendedAsyncSAEngine,
        unique_row_class: type[UpdaterTestRowWithUnique],
        two_rows: list[int],
    ) -> None:
        """Matching check converts IntegrityError to domain error."""
        domain_error = _DuplicateNameError(extra_msg="name taken")
        checks = [
            IntegrityErrorCheck(
                violation_type=UniqueConstraintViolationError,
                error=domain_error,
            ),
        ]
        async with database_connection.begin_session() as db_sess:
            updater: Updater[UpdaterTestRowWithUnique] = Updater(
                spec=UniqueNameUpdaterSpec("bob", checks=checks),
                pk_value=two_rows[0],  # alice → bob (duplicate)
            )
            with pytest.raises(_DuplicateNameError) as exc_info:
                await execute_updater(db_sess, updater)
            assert exc_info.value is domain_error

    async def test_integrity_error_with_empty_checks(
        self,
        database_connection: ExtendedAsyncSAEngine,
        unique_row_class: type[UpdaterTestRowWithUnique],
        two_rows: list[int],
    ) -> None:
        """Empty checks raises parsed fallback (UniqueConstraintViolationError)."""
        async with database_connection.begin_session() as db_sess:
            updater: Updater[UpdaterTestRowWithUnique] = Updater(
                spec=UniqueNameUpdaterSpec("bob"),  # default empty checks
                pk_value=two_rows[0],  # alice → bob (duplicate)
            )
            with pytest.raises(UniqueConstraintViolationError):
                await execute_updater(db_sess, updater)

    async def test_integrity_error_with_non_matching_check(
        self,
        database_connection: ExtendedAsyncSAEngine,
        unique_row_class: type[UpdaterTestRowWithUnique],
        two_rows: list[int],
    ) -> None:
        """Non-matching check (wrong violation type) raises parsed fallback."""
        checks = [
            IntegrityErrorCheck(
                violation_type=ForeignKeyViolationError,
                error=_DuplicateNameError(extra_msg="should not match"),
            ),
        ]
        async with database_connection.begin_session() as db_sess:
            updater: Updater[UpdaterTestRowWithUnique] = Updater(
                spec=UniqueNameUpdaterSpec("bob", checks=checks),
                pk_value=two_rows[0],
            )
            with pytest.raises(UniqueConstraintViolationError):
                await execute_updater(db_sess, updater)


class TestBatchUpdaterIntegrityError:
    """Tests for integrity error handling in execute_batch_updater."""

    @pytest.fixture
    async def unique_row_class(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[type[UpdaterTestRowWithUnique], None]:
        async with database_connection.begin() as conn:
            await conn.run_sync(
                lambda c: Base.metadata.create_all(c, [UpdaterTestRowWithUnique.__table__])
            )
        yield UpdaterTestRowWithUnique
        async with database_connection.begin() as conn:
            await conn.execute(sa.text("DROP TABLE IF EXISTS test_updater_unique CASCADE"))

    @pytest.fixture
    async def two_rows(
        self,
        database_connection: ExtendedAsyncSAEngine,
        unique_row_class: type[UpdaterTestRowWithUnique],
    ) -> AsyncGenerator[list[int], None]:
        ids: list[int] = []
        async with database_connection.begin_session() as db_sess:
            for name in ("alice", "bob"):
                row = UpdaterTestRowWithUnique(name=name, status="active")
                db_sess.add(row)
                await db_sess.flush()
                ids.append(row.id)
        yield ids

    async def test_batch_integrity_error_with_matching_check(
        self,
        database_connection: ExtendedAsyncSAEngine,
        unique_row_class: type[UpdaterTestRowWithUnique],
        two_rows: list[int],
    ) -> None:
        """Matching check converts IntegrityError to domain error in batch update."""
        domain_error = _DuplicateNameError(extra_msg="name taken")
        checks = [
            IntegrityErrorCheck(
                violation_type=UniqueConstraintViolationError,
                error=domain_error,
            ),
        ]
        async with database_connection.begin_session() as db_sess:
            # Update all rows to have the same name → unique violation
            updater: BatchUpdater[UpdaterTestRowWithUnique] = BatchUpdater(
                spec=UniqueNameBatchUpdaterSpec("alice", checks=checks),
                conditions=[
                    lambda: UpdaterTestRowWithUnique.__table__.c.name == "bob",
                ],
            )
            with pytest.raises(_DuplicateNameError) as exc_info:
                await execute_batch_updater(db_sess, updater)
            assert exc_info.value is domain_error

    async def test_batch_integrity_error_with_empty_checks(
        self,
        database_connection: ExtendedAsyncSAEngine,
        unique_row_class: type[UpdaterTestRowWithUnique],
        two_rows: list[int],
    ) -> None:
        """Empty checks raises parsed fallback in batch update."""
        async with database_connection.begin_session() as db_sess:
            updater: BatchUpdater[UpdaterTestRowWithUnique] = BatchUpdater(
                spec=UniqueNameBatchUpdaterSpec("alice"),  # default empty checks
                conditions=[
                    lambda: UpdaterTestRowWithUnique.__table__.c.name == "bob",
                ],
            )
            with pytest.raises(UniqueConstraintViolationError):
                await execute_batch_updater(db_sess, updater)


# =============================================================================
# Bulk Updater Partial Tests (savepoint-based partial failure support)
# =============================================================================


class BulkUpdaterPartialTestRow(Base):  # type: ignore[misc]
    """ORM model for bulk updater partial testing.

    ``name`` carries a UNIQUE constraint so an update colliding with another row's
    name triggers a per-row integrity error.
    """

    __tablename__ = "test_bulk_updater_partial"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(sa.String(50), nullable=False, unique=True)
    value: Mapped[str | None] = mapped_column(sa.String(50), nullable=True)


class _FieldUpdaterSpec(UpdaterSpec[BulkUpdaterPartialTestRow]):
    """UpdaterSpec that applies the given column values to the target row."""

    def __init__(self, **values: Any) -> None:
        self._values = values

    @property
    def row_class(self) -> type[BulkUpdaterPartialTestRow]:
        return BulkUpdaterPartialTestRow

    def build_values(self) -> dict[str, Any]:
        return dict(self._values)


class TestBulkUpdaterPartial:
    """Tests for execute_bulk_updater_partial with savepoint-based partial failure support."""

    @pytest.fixture
    async def bulk_partial_row_class(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[type[BulkUpdaterPartialTestRow], None]:
        """Create the test table and return the row class."""
        async with database_connection.begin() as conn:
            await conn.run_sync(
                lambda c: Base.metadata.create_all(c, [BulkUpdaterPartialTestRow.__table__])
            )

        yield BulkUpdaterPartialTestRow

        async with database_connection.begin() as conn:
            await conn.execute(sa.text("DROP TABLE IF EXISTS test_bulk_updater_partial CASCADE"))

    @pytest.fixture
    async def rows_for_success(
        self,
        database_connection: ExtendedAsyncSAEngine,
        bulk_partial_row_class: type[BulkUpdaterPartialTestRow],
    ) -> None:
        """Seed three rows (name-1..name-3) with no value set."""
        async with database_connection.begin_session() as db_sess:
            for i in range(1, 4):
                db_sess.add(BulkUpdaterPartialTestRow(id=i, name=f"name-{i}", value=None))

    @pytest.fixture
    async def rows_abc(
        self,
        database_connection: ExtendedAsyncSAEngine,
        bulk_partial_row_class: type[BulkUpdaterPartialTestRow],
    ) -> None:
        """Seed rows id=1..3 with unique names alpha/beta/gamma."""
        async with database_connection.begin_session() as db_sess:
            db_sess.add(BulkUpdaterPartialTestRow(id=1, name="alpha", value=None))
            db_sess.add(BulkUpdaterPartialTestRow(id=2, name="beta", value=None))
            db_sess.add(BulkUpdaterPartialTestRow(id=3, name="gamma", value=None))

    @pytest.fixture
    async def rows_1_and_3(
        self,
        database_connection: ExtendedAsyncSAEngine,
        bulk_partial_row_class: type[BulkUpdaterPartialTestRow],
    ) -> None:
        """Seed only rows id=1 (alpha) and id=3 (gamma); id=2 is absent."""
        async with database_connection.begin_session() as db_sess:
            db_sess.add(BulkUpdaterPartialTestRow(id=1, name="alpha", value=None))
            db_sess.add(BulkUpdaterPartialTestRow(id=3, name="gamma", value=None))

    @pytest.fixture
    async def rows_alpha_to_epsilon(
        self,
        database_connection: ExtendedAsyncSAEngine,
        bulk_partial_row_class: type[BulkUpdaterPartialTestRow],
    ) -> None:
        """Seed rows id=1..5 with unique names alpha..epsilon."""
        async with database_connection.begin_session() as db_sess:
            for i, name in enumerate(["alpha", "beta", "gamma", "delta", "epsilon"], start=1):
                db_sess.add(BulkUpdaterPartialTestRow(id=i, name=name, value=None))

    async def test_all_updaters_succeed(
        self,
        database_connection: ExtendedAsyncSAEngine,
        rows_for_success: None,
    ) -> None:
        """3 updaters targeting existing rows → all 3 rows updated, errors is empty."""
        async with database_connection.begin_session() as db_sess:
            updaters = [
                Updater(spec=_FieldUpdaterSpec(value="v1"), pk_value=1),
                Updater(spec=_FieldUpdaterSpec(value="v2"), pk_value=2),
                Updater(spec=_FieldUpdaterSpec(value="v3"), pk_value=3),
            ]
            result = await execute_bulk_updater_partial(db_sess, updaters)

            assert isinstance(result, BulkUpdaterResult)
            assert result.success_count() == 3
            assert len(result.successes) == 3
            assert len(result.errors) == 0
            assert not result.has_failures()

            assert result.successes[0].id == 1
            assert result.successes[0].value == "v1"
            assert result.successes[2].id == 3
            assert result.successes[2].value == "v3"

            # Verify persisted values
            rows = (
                (
                    await db_sess.execute(
                        sa.select(BulkUpdaterPartialTestRow).order_by(BulkUpdaterPartialTestRow.id)
                    )
                )
                .scalars()
                .all()
            )
            assert [r.value for r in rows] == ["v1", "v2", "v3"]

    async def test_partial_failure_with_unique_constraint(
        self,
        database_connection: ExtendedAsyncSAEngine,
        rows_abc: None,
    ) -> None:
        """1 updater collides with an existing unique name → 2 successes + 1 error."""
        async with database_connection.begin_session() as db_sess:
            updaters = [
                Updater(spec=_FieldUpdaterSpec(value="v1"), pk_value=1),
                # Renaming beta → gamma collides with row 3's unique name
                Updater(spec=_FieldUpdaterSpec(name="gamma"), pk_value=2),
                Updater(spec=_FieldUpdaterSpec(value="v3"), pk_value=3),
            ]
            result = await execute_bulk_updater_partial(db_sess, updaters)

            assert result.success_count() == 2
            assert len(result.successes) == 2
            assert len(result.errors) == 1
            assert result.has_failures()

            assert result.successes[0].id == 1
            assert result.successes[0].value == "v1"
            assert result.successes[1].id == 3
            assert result.successes[1].value == "v3"

            error = result.errors[0]
            assert isinstance(error, BulkUpdaterError)
            assert error.index == 1  # Second updater in the list
            assert isinstance(error.exception, RepositoryIntegrityError)

            # The failed row keeps its original name
            row_2 = (
                await db_sess.execute(
                    sa.select(BulkUpdaterPartialTestRow).where(BulkUpdaterPartialTestRow.id == 2)
                )
            ).scalar_one()
            assert row_2.name == "beta"

    async def test_non_existent_pk_is_skipped(
        self,
        database_connection: ExtendedAsyncSAEngine,
        rows_1_and_3: None,
    ) -> None:
        """An updater targeting a non-existent PK is skipped (not an error)."""
        async with database_connection.begin_session() as db_sess:
            updaters = [
                Updater(spec=_FieldUpdaterSpec(value="v1"), pk_value=1),
                Updater(spec=_FieldUpdaterSpec(value="v2"), pk_value=2),  # Non-existent PK
                Updater(spec=_FieldUpdaterSpec(value="v3"), pk_value=3),
            ]
            result = await execute_bulk_updater_partial(db_sess, updaters)

            assert result.success_count() == 2
            assert len(result.successes) == 2
            assert len(result.errors) == 0
            assert not result.has_failures()

            assert result.successes[0].id == 1
            assert result.successes[1].id == 3

    async def test_empty_updater_list(
        self,
        database_connection: ExtendedAsyncSAEngine,
        bulk_partial_row_class: type[BulkUpdaterPartialTestRow],
    ) -> None:
        """An empty updater list returns an empty result."""
        async with database_connection.begin_session() as db_sess:
            updaters: list[Updater[BulkUpdaterPartialTestRow]] = []
            result = await execute_bulk_updater_partial(db_sess, updaters)

            assert isinstance(result, BulkUpdaterResult)
            assert result.success_count() == 0
            assert len(result.errors) == 0
            assert not result.has_failures()
