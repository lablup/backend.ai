"""Fixtures for scaling group service-direct integration tests.

These tests use real database connections because the scaling group has no REST
API v2 endpoints (only legacy GraphQL), so they cannot be tested via the client
SDK and cannot be placed in tests/component/.

This conftest overrides the guard fixtures in tests/unit/manager/services/conftest.py
to allow real database access in this specific subdirectory only.
"""

from __future__ import annotations

import secrets
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa
from sqlalchemy import text

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.typed_validators import HostPortPair as HostPortPairModel
from ai.backend.common.types import DefaultForUnspecified, ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.deployment_auto_scaling_policy import (
    DeploymentAutoScalingPolicyRow,
)
from ai.backend.manager.models.deployment_policy import DeploymentPolicyRow
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.models.deployment_revision_preset import DeploymentRevisionPresetRow
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.rbac_models import RoleRow, UserRoleRow
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role_permission_preset.row import (
    RolePermissionPresetRow,
)
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.models.replica_group import ReplicaGroupRow
from ai.backend.manager.models.resource_policy.row import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.runtime_variant import RuntimeVariantRow
from ai.backend.manager.models.scaling_group import (
    ScalingGroupForDomainRow,
    ScalingGroupForKeypairsRow,
    ScalingGroupForProjectRow,
    ScalingGroupRow,
)
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.models.virtual_scope.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_scope.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_scope.virtual_scope import VirtualScopeRow
from ai.backend.manager.repositories.db.engine import create_async_engine
from ai.backend.manager.repositories.scaling_group.repository import ScalingGroupRepository
from ai.backend.manager.services.scaling_group.processors import ScalingGroupProcessors
from ai.backend.manager.services.scaling_group.service import ScalingGroupService
from ai.backend.testutils.db import with_tables
from ai.backend.testutils.fixtures import DomainFactory, DomainFixtureData


@dataclass
class KeypairFixtureData:
    access_key: str
    secret_key: str


@dataclass
class UserFixtureData:
    user_uuid: uuid.UUID
    keypair: KeypairFixtureData
    email: str


# ---------------------------------------------------------------------------
# Override guard fixtures from tests/unit/manager/services/conftest.py
# ---------------------------------------------------------------------------


@pytest.fixture
async def database_engine(
    postgres_container: tuple[str, HostPortPairModel],
) -> AsyncIterator[ExtendedAsyncSAEngine]:
    """Real database engine for scaling group integration tests.

    Overrides the guard fixture in tests/unit/manager/services/conftest.py to
    allow real DB access for scaling group service-direct tests that cannot be
    tested via the client SDK.
    """
    _, addr = postgres_container
    url = f"postgresql+asyncpg://postgres:develove@{addr.host}:{addr.port}/testing"

    engine = create_async_engine(
        url,
        pool_size=8,
        pool_pre_ping=False,
        max_overflow=64,
    )

    yield engine

    await engine.dispose()


@pytest.fixture
async def database_fixture(
    database_engine: ExtendedAsyncSAEngine,
) -> AsyncIterator[None]:
    """Create all tables needed by scaling group tests, truncate on teardown.

    Overrides the guard fixture in tests/unit/manager/services/conftest.py.

    The purge and RBAC scope paths issue whole-entity SELECTs (batch purgers,
    virtual-scope writes), so the real rows are created instead of minimal stub
    tables, mirroring the repository-level test fixture.
    """
    async with database_engine.begin() as conn:
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))

    async with with_tables(
        database_engine,
        [
            # FK dependency order: parents before children
            DomainRow,
            ScalingGroupRow,
            AssociationScopesEntitiesRow,
            RoleRow,
            UserRoleRow,
            PermissionRow,
            RolePresetRow,
            RolePermissionPresetRow,
            VirtualScopeRow,
            EntityMembershipRow,
            ScopeBindingRow,
            ScalingGroupForDomainRow,
            ScalingGroupForProjectRow,
            UserResourcePolicyRow,
            ProjectResourcePolicyRow,
            KeyPairResourcePolicyRow,
            UserRow,
            KeyPairRow,
            ScalingGroupForKeypairsRow,
            GroupRow,
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
        ],
    ):
        yield


# ---------------------------------------------------------------------------
# Service / repository fixtures (moved from tests/component/scaling_group/conftest.py)
# ---------------------------------------------------------------------------


@pytest.fixture
def scaling_group_repository(database_engine: ExtendedAsyncSAEngine) -> ScalingGroupRepository:
    """Direct repository instance for association existence checks."""
    return ScalingGroupRepository(database_engine)


@pytest.fixture
def scaling_group_processors(database_engine: ExtendedAsyncSAEngine) -> ScalingGroupProcessors:
    repo = ScalingGroupRepository(database_engine)
    service = ScalingGroupService(repo)
    return ScalingGroupProcessors(
        service=service, action_monitors=[], validators=MagicMock(spec=ActionValidators)
    )


# ---------------------------------------------------------------------------
# Seed-data fixtures (lightweight versions of component conftest fixtures)
# ---------------------------------------------------------------------------


@pytest.fixture
async def resource_policy_fixture(
    database_engine: ExtendedAsyncSAEngine,
    database_fixture: None,
) -> AsyncIterator[str]:
    """Insert keypair and user resource policies; yield shared policy name."""
    policy_name = f"policy-{secrets.token_hex(6)}"
    async with database_engine.begin() as conn:
        await conn.execute(
            sa.insert(KeyPairResourcePolicyRow.__table__).values(
                name=policy_name,
                default_for_unspecified=DefaultForUnspecified.UNLIMITED,
                total_resource_slots=ResourceSlot(),
                max_session_lifetime=0,
                max_concurrent_sessions=5,
                max_containers_per_session=1,
                idle_timeout=3600,
                allowed_vfolder_hosts=VFolderHostPermissionMap(),
            )
        )
        await conn.execute(
            sa.insert(UserResourcePolicyRow.__table__).values(
                name=policy_name,
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=10,
                max_customized_image_count=3,
            )
        )
    yield policy_name
    # Cleanup handled by database_fixture TRUNCATE CASCADE


@pytest.fixture
async def domain_fixture(
    domain_factory: DomainFactory,
    database_engine: ExtendedAsyncSAEngine,
    database_fixture: None,
) -> DomainFixtureData:
    """Insert a test domain and yield its identifiers."""
    return await domain_factory(database_engine, name=f"domain-{secrets.token_hex(6)}")
    # Cleanup handled by database_fixture TRUNCATE CASCADE


@pytest.fixture
async def admin_user_fixture(
    database_engine: ExtendedAsyncSAEngine,
    domain_fixture: DomainFixtureData,
    resource_policy_fixture: str,
) -> AsyncIterator[Any]:
    """Insert an admin user and keypair; yield UserFixtureData."""
    unique_id = secrets.token_hex(4)
    email = f"admin-{unique_id}@test.local"
    user_uuid = uuid.uuid4()
    access_key = f"AKTEST{secrets.token_hex(7).upper()}"
    secret_key = secrets.token_hex(20)

    async with database_engine.begin() as conn:
        await conn.execute(
            sa.insert(UserRow.__table__).values(
                uuid=str(user_uuid),
                username=f"admin-{unique_id}",
                email=email,
                need_password_change=False,
                status=UserStatus.ACTIVE,
                domain_name=domain_fixture.domain_name,
                resource_policy=resource_policy_fixture,
                role=UserRole.SUPERADMIN,
            )
        )
        await conn.execute(
            sa.insert(KeyPairRow.__table__).values(
                user_id=email,
                access_key=access_key,
                secret_key=secret_key,
                is_active=True,
                resource_policy=resource_policy_fixture,
                rate_limit=30000,
                num_queries=0,
                is_admin=True,
                user=str(user_uuid),
            )
        )
    yield UserFixtureData(
        user_uuid=user_uuid,
        keypair=KeypairFixtureData(access_key=access_key, secret_key=secret_key),
        email=email,
    )
    # Cleanup handled by database_fixture TRUNCATE CASCADE


@pytest.fixture
async def regular_user_fixture(
    database_engine: ExtendedAsyncSAEngine,
    domain_fixture: DomainFixtureData,
    resource_policy_fixture: str,
) -> AsyncIterator[Any]:
    """Insert a regular user and keypair; yield UserFixtureData."""
    unique_id = secrets.token_hex(4)
    email = f"user-{unique_id}@test.local"
    user_uuid = uuid.uuid4()
    access_key = f"AKTEST{secrets.token_hex(7).upper()}"
    secret_key = secrets.token_hex(20)

    async with database_engine.begin() as conn:
        await conn.execute(
            sa.insert(UserRow.__table__).values(
                uuid=str(user_uuid),
                username=f"user-{unique_id}",
                email=email,
                need_password_change=False,
                status=UserStatus.ACTIVE,
                domain_name=domain_fixture.domain_name,
                resource_policy=resource_policy_fixture,
                role=UserRole.USER,
            )
        )
        await conn.execute(
            sa.insert(KeyPairRow.__table__).values(
                user_id=email,
                access_key=access_key,
                secret_key=secret_key,
                is_active=True,
                resource_policy=resource_policy_fixture,
                rate_limit=30000,
                num_queries=0,
                is_admin=False,
                user=str(user_uuid),
            )
        )
    yield UserFixtureData(
        user_uuid=user_uuid,
        keypair=KeypairFixtureData(access_key=access_key, secret_key=secret_key),
        email=email,
    )
    # Cleanup handled by database_fixture TRUNCATE CASCADE
