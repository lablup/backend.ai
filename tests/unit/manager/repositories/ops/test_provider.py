"""Tests for the DB ops wrapper (DBOpsProvider / ReadOps / WriteOps).

These verify observable contracts — the empty-scope constraint, real create/query/
update/purge outcomes, and that dependent inserts carry the resolved dependency — not
internal call wiring.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator, Sequence
from dataclasses import dataclass
from typing import Any
from unittest.mock import AsyncMock

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.manager.errors.repository import EmptySearchScopeError

# ORM relationship cluster registration: SQLAlchemy's global
# configure_mappers() must resolve every string relationship reachable from
# the rows this isolated test registers, so the whole domain cluster is
# imported here. _ORM_CLUSTER below keeps these imports from being pruned.
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.association_container_registries_groups import (
    AssociationContainerRegistriesGroupsRow,
)
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.clauses import QueryCondition
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
from ai.backend.manager.models.scopes import ExistenceCheck, SearchScope
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderInvitationRow, VFolderPermissionRow, VFolderRow
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    Creator,
    CreatorSpec,
    DependentCreatorSpec,
    ExistsQuerier,
    NoPagination,
    Purger,
    Querier,
    Updater,
    UpdaterSpec,
)
from ai.backend.manager.repositories.ops import DBOpsProvider, ReadOps
from ai.backend.testutils.db import with_tables

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


class OpsTestParentRow(Base):  # type: ignore[misc]
    __tablename__ = "test_ops_parent"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    domain_name: Mapped[str] = mapped_column(sa.String(64), nullable=False)


class OpsTestChildRow(Base):  # type: ignore[misc]
    __tablename__ = "test_ops_child"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    parent_id: Mapped[int] = mapped_column(
        sa.Integer, sa.ForeignKey("test_ops_parent.id"), nullable=False
    )
    label: Mapped[str] = mapped_column(sa.String(64), nullable=False)


@dataclass
class ParentCreatorSpec(CreatorSpec[OpsTestParentRow]):
    name: str
    domain_name: str

    def build_row(self) -> OpsTestParentRow:
        return OpsTestParentRow(name=self.name, domain_name=self.domain_name)


@dataclass
class ParentUpdaterSpec(UpdaterSpec[OpsTestParentRow]):
    new_name: str

    @property
    def row_class(self) -> type[OpsTestParentRow]:
        return OpsTestParentRow

    def build_values(self) -> dict[str, Any]:
        return {"name": self.new_name}


@dataclass(frozen=True)
class ChildDependency:
    parent_id: int


@dataclass
class ChildDependentCreatorSpec(DependentCreatorSpec[ChildDependency, OpsTestChildRow]):
    label: str

    def build_row(self, dependency: ChildDependency) -> OpsTestChildRow:
        return OpsTestChildRow(parent_id=dependency.parent_id, label=self.label)


@dataclass(frozen=True)
class ParentDomainScope(SearchScope):
    domain_name: str

    def to_condition(self) -> QueryCondition:
        return lambda: OpsTestParentRow.domain_name == self.domain_name

    @property
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return ()


@pytest.fixture
async def ops_tables(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[None, None]:
    async with with_tables(database_connection, [OpsTestParentRow, OpsTestChildRow]):
        yield


@pytest.fixture
def provider(database_connection: ExtendedAsyncSAEngine) -> DBOpsProvider:
    return DBOpsProvider(database_connection)


class TestScopeConstraint:
    async def test_with_scopes_rejects_empty_scopes(self) -> None:
        ops = ReadOps(AsyncMock())  # session is never touched before the guard raises
        querier = BatchQuerier(pagination=NoPagination())
        with pytest.raises(EmptySearchScopeError):
            await ops.batch_query_with_scopes(sa.select(OpsTestParentRow), querier, [])


class TestWriteRoundTrip:
    async def test_create_then_query(self, provider: DBOpsProvider, ops_tables: None) -> None:
        async with provider.write_ops() as w:
            created = await w.create(Creator(spec=ParentCreatorSpec(name="p1", domain_name="d1")))
        parent_id = created.row.id

        async with provider.read_ops() as r:
            fetched = await r.query(Querier(row_class=OpsTestParentRow, pk_value=parent_id))

        assert fetched is not None
        assert fetched.row.name == "p1"
        assert fetched.row.domain_name == "d1"

    async def test_update_reflected(self, provider: DBOpsProvider, ops_tables: None) -> None:
        async with provider.write_ops() as w:
            created = await w.create(Creator(spec=ParentCreatorSpec(name="p1", domain_name="d1")))
            parent_id = created.row.id
            await w.update(Updater(spec=ParentUpdaterSpec(new_name="p2"), pk_value=parent_id))

        async with provider.read_ops() as r:
            fetched = await r.query(Querier(row_class=OpsTestParentRow, pk_value=parent_id))

        assert fetched is not None
        assert fetched.row.name == "p2"

    async def test_purge_removes(self, provider: DBOpsProvider, ops_tables: None) -> None:
        async with provider.write_ops() as w:
            created = await w.create(Creator(spec=ParentCreatorSpec(name="p1", domain_name="d1")))
            parent_id = created.row.id
            await w.purge(Purger(row_class=OpsTestParentRow, pk_value=parent_id))

        async with provider.read_ops() as r:
            fetched = await r.query(Querier(row_class=OpsTestParentRow, pk_value=parent_id))

        assert fetched is None


class TestDependentCreate:
    async def test_bulk_create_dependent_carries_parent_id(
        self, provider: DBOpsProvider, ops_tables: None
    ) -> None:
        async with provider.write_ops() as w:
            parent = (
                await w.create(Creator(spec=ParentCreatorSpec(name="p", domain_name="d")))
            ).row
            dependency = ChildDependency(parent_id=parent.id)
            specs = [
                ChildDependentCreatorSpec(label="a"),
                ChildDependentCreatorSpec(label="b"),
            ]
            result = await w.bulk_create_dependent(specs, dependency)

        assert {child.label for child in result.rows} == {"a", "b"}
        assert all(child.parent_id == parent.id for child in result.rows)

    async def test_create_dependent_single(self, provider: DBOpsProvider, ops_tables: None) -> None:
        async with provider.write_ops() as w:
            parent = (
                await w.create(Creator(spec=ParentCreatorSpec(name="p", domain_name="d")))
            ).row
            dependency = ChildDependency(parent_id=parent.id)
            child = (
                await w.create_dependent(ChildDependentCreatorSpec(label="solo"), dependency)
            ).row

        assert child.parent_id == parent.id
        assert child.label == "solo"


@pytest.fixture
async def seeded_parent(
    database_connection: ExtendedAsyncSAEngine,
    ops_tables: None,
) -> None:
    """Seed a single ("p1", "d1") parent row directly, independent of the create op."""
    async with database_connection.begin() as conn:
        await conn.execute(sa.insert(OpsTestParentRow).values(name="p1", domain_name="d1"))


class TestExists:
    async def test_matching_condition_is_true_absent_is_false(
        self, provider: DBOpsProvider, seeded_parent: None
    ) -> None:
        async with provider.read_ops() as r:
            assert await r.exists(
                ExistsQuerier(
                    row_class=OpsTestParentRow,
                    conditions=[lambda: OpsTestParentRow.name == "p1"],
                )
            )
            assert not await r.exists(
                ExistsQuerier(
                    row_class=OpsTestParentRow,
                    conditions=[lambda: OpsTestParentRow.name == "absent"],
                )
            )

    async def test_conditions_are_anded(self, provider: DBOpsProvider, seeded_parent: None) -> None:
        async with provider.read_ops() as r:
            assert await r.exists(
                ExistsQuerier(
                    row_class=OpsTestParentRow,
                    conditions=[
                        lambda: OpsTestParentRow.name == "p1",
                        lambda: OpsTestParentRow.domain_name == "d1",
                    ],
                )
            )
            # name matches but domain_name does not — the AND must fail.
            assert not await r.exists(
                ExistsQuerier(
                    row_class=OpsTestParentRow,
                    conditions=[
                        lambda: OpsTestParentRow.name == "p1",
                        lambda: OpsTestParentRow.domain_name == "d2",
                    ],
                )
            )

    async def test_empty_conditions_false_on_empty_table(
        self, provider: DBOpsProvider, ops_tables: None
    ) -> None:
        async with provider.read_ops() as r:
            assert not await r.exists(ExistsQuerier(row_class=OpsTestParentRow))

    async def test_empty_conditions_true_when_any_row(
        self, provider: DBOpsProvider, seeded_parent: None
    ) -> None:
        async with provider.read_ops() as r:
            assert await r.exists(ExistsQuerier(row_class=OpsTestParentRow))


class TestScopeFiltering:
    async def test_with_scopes_filters_and_global_returns_all(
        self, provider: DBOpsProvider, ops_tables: None
    ) -> None:
        async with provider.write_ops() as w:
            await w.create(Creator(spec=ParentCreatorSpec(name="a", domain_name="d1")))
            await w.create(Creator(spec=ParentCreatorSpec(name="b", domain_name="d2")))

        async with provider.read_ops() as r:
            scoped = await r.batch_query_with_scopes(
                sa.select(OpsTestParentRow),
                BatchQuerier(pagination=NoPagination()),
                [ParentDomainScope(domain_name="d1")],
            )
            full = await r.batch_query_in_global(
                sa.select(OpsTestParentRow),
                BatchQuerier(pagination=NoPagination()),
            )

        assert {row[0].domain_name for row in scoped.rows} == {"d1"}
        assert len(full.rows) == 2
