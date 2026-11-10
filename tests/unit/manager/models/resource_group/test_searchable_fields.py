"""Tests for the resource group search field declarations."""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
import sqlalchemy as sa

from ai.backend.manager.models.agent.row import AgentRow
from ai.backend.manager.models.container_registry.row import ContainerRegistryRow
from ai.backend.manager.models.deployment_auto_scaling_policy.row import (
    DeploymentAutoScalingPolicyRow,
)
from ai.backend.manager.models.deployment_policy.row import DeploymentPolicyRow
from ai.backend.manager.models.deployment_revision.row import DeploymentRevisionRow
from ai.backend.manager.models.deployment_revision_preset.row import DeploymentRevisionPresetRow
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.endpoint.row import EndpointRow
from ai.backend.manager.models.image.row import ImageRow
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.rbac_models.user_role.row import UserRoleRow
from ai.backend.manager.models.replica_group.row import ReplicaGroupRow
from ai.backend.manager.models.resource_group.row import ResourceGroupRow
from ai.backend.manager.models.resource_group.searchable_fields import (
    ResourceGroupSearchableFields,
)
from ai.backend.manager.models.resource_policy.row import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_preset.row import ResourcePresetRow
from ai.backend.manager.models.routing.row import RoutingRow
from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow
from ai.backend.manager.models.session.row import SessionRow
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder.row import VFolderRow
from ai.backend.testutils.db import TableOrORM, with_tables

# Define the tables list in FK dependency order for mapper initialization
_WITH_TABLES: list[TableOrORM] = [
    DomainRow,
    ResourceGroupRow,
    UserResourcePolicyRow,
    ProjectResourcePolicyRow,
    KeyPairResourcePolicyRow,
    UserRoleRow,
    UserRow,
    KeyPairRow,
    ProjectRow,
    ContainerRegistryRow,
    ImageRow,
    VFolderRow,
    EndpointRow,
    DeploymentPolicyRow,
    DeploymentAutoScalingPolicyRow,
    RuntimeVariantRow,
    DeploymentRevisionPresetRow,
    DeploymentRevisionRow,
    SessionRow,
    AgentRow,
    KernelRow,
    ReplicaGroupRow,
    RoutingRow,
    ResourcePresetRow,
]


@pytest.fixture
async def db_with_tables(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    """Database connection with tables created for SQLAlchemy mapper initialization."""
    async with with_tables(database_connection, _WITH_TABLES):
        yield database_connection


class TestScalingGroupOrdersCursor:
    """Tests for cursor-related orders in ScalingGroupOrders."""

    def test_name_ascending(self) -> None:
        """Test that name() with ascending=True returns ascending order."""
        order = ResourceGroupSearchableFields.own.name.order.apply(ascending=True)
        assert isinstance(order, sa.sql.ClauseElement)
        # Check the modifier shows ASC
        order_str = str(order)
        assert "ASC" in order_str or "asc" in order_str.lower()

    def test_name_descending(self) -> None:
        """Test that name() with ascending=False returns descending order."""
        order = ResourceGroupSearchableFields.own.name.order.apply(ascending=False)
        assert isinstance(order, sa.sql.ClauseElement)
        # Check the modifier shows DESC
        order_str = str(order)
        assert "DESC" in order_str or "desc" in order_str.lower()
