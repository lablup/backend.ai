"""Integration tests for upserter with real database."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any

import pytest
import sqlalchemy as sa

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
    BulkUpserter,
    BulkUpserterResult,
    Upserter,
    UpserterResult,
    UpserterSpec,
    execute_bulk_upserter,
    execute_upserter,
)

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


class UpserterTestRow(Base):  # type: ignore[misc]
    """ORM model for upserter testing with PK as business key."""

    __tablename__ = "test_upserter_orm"
    __table_args__ = {"extend_existing": True}

    name = sa.Column(sa.String(50), primary_key=True)  # PK is business key
    value = sa.Column(sa.String(100), nullable=True)


class SimpleUpserterSpec(UpserterSpec[UpserterTestRow]):
    """Simple upserter spec for testing."""

    def __init__(self, name: str, value: str | None = None) -> None:
        self._name = name
        self._value = value

    @property
    def row_class(self) -> type[UpserterTestRow]:
        return UpserterTestRow

    def build_insert_values(self) -> dict[str, Any]:
        return {"name": self._name, "value": self._value}

    def build_update_values(self) -> dict[str, Any]:
        # On conflict (PK), only update value
        return {"value": self._value}


class TestUpserterBasic:
    """Tests for upserter operations."""

    @pytest.fixture
    async def upserter_row_class(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[type[UpserterTestRow], None]:
        """Create ORM test table with unique constraint on name and return row class."""
        async with database_connection.begin() as conn:
            await conn.run_sync(lambda c: Base.metadata.create_all(c, [UpserterTestRow.__table__]))

        yield UpserterTestRow

        async with database_connection.begin() as conn:
            await conn.execute(sa.text("DROP TABLE IF EXISTS test_upserter_orm CASCADE"))

    async def test_upsert_insert_new_row(
        self,
        database_connection: ExtendedAsyncSAEngine,
        upserter_row_class: type[UpserterTestRow],
    ) -> None:
        """Test upserting a new row (insert case)."""
        async with database_connection.begin_session() as db_sess:
            spec = SimpleUpserterSpec(name="new-item", value="initial-value")
            upserter: Upserter[UpserterTestRow] = Upserter(spec=spec)

            result = await execute_upserter(db_sess, upserter, index_elements=["name"])

            assert isinstance(result, UpserterResult)
            assert result.row.name == "new-item"
            assert result.row.value == "initial-value"

            table = upserter_row_class.__table__
            count_result = await db_sess.execute(sa.select(sa.func.count()).select_from(table))
            assert count_result.scalar() == 1

    async def test_upsert_update_existing_row(
        self,
        database_connection: ExtendedAsyncSAEngine,
        upserter_row_class: type[UpserterTestRow],
    ) -> None:
        """Test upserting an existing row (update case)."""
        table = upserter_row_class.__table__
        async with database_connection.begin_session() as db_sess:
            # First insert
            await db_sess.execute(table.insert().values(name="existing-item", value="old-value"))
            count_result = await db_sess.execute(sa.select(sa.func.count()).select_from(table))
            assert count_result.scalar() == 1

            # Upsert should update
            spec = SimpleUpserterSpec(name="existing-item", value="new-value")
            upserter: Upserter[UpserterTestRow] = Upserter(spec=spec)

            result = await execute_upserter(db_sess, upserter, index_elements=["name"])

            assert result.row.name == "existing-item"
            assert result.row.value == "new-value"

            # Should still be 1 row (updated, not inserted)
            count_result = await db_sess.execute(sa.select(sa.func.count()).select_from(table))
            assert count_result.scalar() == 1

            # Verify the value was actually updated
            row_result = await db_sess.execute(
                sa.select(table).where(table.c.name == "existing-item")
            )
            row = row_result.fetchone()
            assert row is not None
            assert row.value == "new-value"


class TestBulkUpserter:
    """Tests for bulk upserter operations (multiple UpserterSpec instances)."""

    @pytest.fixture
    async def upserter_row_class(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[type[UpserterTestRow], None]:
        """Create ORM test table."""
        async with database_connection.begin() as conn:
            await conn.run_sync(lambda c: Base.metadata.create_all(c, [UpserterTestRow.__table__]))

        yield UpserterTestRow

        async with database_connection.begin() as conn:
            await conn.execute(sa.text("DROP TABLE IF EXISTS test_upserter_orm CASCADE"))

    async def test_bulk_upsert_all_new_rows(
        self,
        database_connection: ExtendedAsyncSAEngine,
        upserter_row_class: type[UpserterTestRow],
    ) -> None:
        """Test bulk upserting when all rows are new (insert case)."""
        async with database_connection.begin_session() as db_sess:
            specs = [
                SimpleUpserterSpec(name="item-1", value="value-1"),
                SimpleUpserterSpec(name="item-2", value="value-2"),
                SimpleUpserterSpec(name="item-3", value="value-3"),
            ]
            bulk_upserter: BulkUpserter[UpserterTestRow] = BulkUpserter(specs=specs)

            result = await execute_bulk_upserter(db_sess, bulk_upserter, index_elements=["name"])

            assert isinstance(result, BulkUpserterResult)
            assert result.upserted_count == 3

            table = upserter_row_class.__table__
            count_result = await db_sess.execute(sa.select(sa.func.count()).select_from(table))
            assert count_result.scalar() == 3

    async def test_bulk_upsert_all_existing_rows(
        self,
        database_connection: ExtendedAsyncSAEngine,
        upserter_row_class: type[UpserterTestRow],
    ) -> None:
        """Test bulk upserting when all rows exist (update case)."""
        table = upserter_row_class.__table__
        async with database_connection.begin_session() as db_sess:
            # Pre-insert rows
            await db_sess.execute(
                table.insert().values([
                    {"name": "item-1", "value": "old-1"},
                    {"name": "item-2", "value": "old-2"},
                ])
            )

            specs = [
                SimpleUpserterSpec(name="item-1", value="new-1"),
                SimpleUpserterSpec(name="item-2", value="new-2"),
            ]
            bulk_upserter: BulkUpserter[UpserterTestRow] = BulkUpserter(specs=specs)

            result = await execute_bulk_upserter(db_sess, bulk_upserter, index_elements=["name"])

            assert isinstance(result, BulkUpserterResult)
            assert result.upserted_count == 2

            # Verify values were updated
            row_result = await db_sess.execute(
                sa.select(table.c.name, table.c.value).order_by(table.c.name)
            )
            rows = row_result.fetchall()
            assert len(rows) == 2
            assert rows[0].value == "new-1"
            assert rows[1].value == "new-2"

    async def test_bulk_upsert_mixed_insert_update(
        self,
        database_connection: ExtendedAsyncSAEngine,
        upserter_row_class: type[UpserterTestRow],
    ) -> None:
        """Test bulk upserting with mix of new and existing rows."""
        table = upserter_row_class.__table__
        async with database_connection.begin_session() as db_sess:
            # Pre-insert one row
            await db_sess.execute(table.insert().values({"name": "existing", "value": "old"}))

            specs = [
                SimpleUpserterSpec(name="existing", value="updated"),
                SimpleUpserterSpec(name="new-1", value="value-1"),
                SimpleUpserterSpec(name="new-2", value="value-2"),
            ]
            bulk_upserter: BulkUpserter[UpserterTestRow] = BulkUpserter(specs=specs)

            result = await execute_bulk_upserter(db_sess, bulk_upserter, index_elements=["name"])

            assert isinstance(result, BulkUpserterResult)
            assert result.upserted_count == 3

            count_result = await db_sess.execute(sa.select(sa.func.count()).select_from(table))
            assert count_result.scalar() == 3

            # Verify existing row was updated
            row_result = await db_sess.execute(
                sa.select(table.c.value).where(table.c.name == "existing")
            )
            assert row_result.scalar() == "updated"

    async def test_bulk_upsert_empty_specs(
        self,
        database_connection: ExtendedAsyncSAEngine,
        upserter_row_class: type[UpserterTestRow],
    ) -> None:
        """Test bulk upsert with empty specs list."""
        async with database_connection.begin_session() as db_sess:
            specs: list[SimpleUpserterSpec] = []
            bulk_upserter: BulkUpserter[UpserterTestRow] = BulkUpserter(specs=specs)

            result = await execute_bulk_upserter(db_sess, bulk_upserter, index_elements=["name"])

            assert isinstance(result, BulkUpserterResult)
            assert result.upserted_count == 0
