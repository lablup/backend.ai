"""Loading legacy ``KeyPair`` objects by the owner's email."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from unittest.mock import MagicMock

import pytest

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.types import AccessKey, ResourceSlot
from ai.backend.manager.api.gql_legacy.keypair import KeyPair
from ai.backend.manager.api.gql_legacy.schema import GraphQueryContext
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.project import ProjectRow
from ai.backend.manager.models.rbac_models import RoleRow, UserRoleRow
from ai.backend.manager.models.replica_group import ReplicaGroupRow
from ai.backend.manager.models.resource_group import ResourceGroupRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRole, UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.entity_membership_cap import (
    EntityMembershipCapRow,
)
from ai.backend.manager.models.virtual_entity.entity_membership_field import (
    EntityMembershipFieldRow,
)
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.secret.types import SecretValue
from ai.backend.testutils.db import TableOrORM, with_tables
from ai.backend.testutils.virtual_entity import VirtualEntitySeeder

_DOMAIN = "kp-by-email"
_EMAIL = "alice@example.com"
_ACCESS_KEY = AccessKey("AKALICE")

_ALL_ROWS: list[TableOrORM] = [
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
    ContainerRegistryRow,
    ImageRow,
    VFolderRow,
    EndpointRow,
    SessionRow,
    AgentRow,
    KernelRow,
    ReplicaGroupRow,
    RoutingRow,
    ResourcePresetRow,
    VirtualEntityRow,
    ScopeBindingRow,
    EntityMembershipRow,
    EntityMembershipCapRow,
    EntityMembershipFieldRow,
]


class TestBatchLoadByEmail:
    @pytest.fixture
    async def db(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(database_connection, _ALL_ROWS):
            yield database_connection

    @pytest.fixture
    async def seeded(self, db: ExtendedAsyncSAEngine) -> None:
        domain_id = DomainID(uuid.uuid4())
        project_id = uuid.uuid4()
        user_id = uuid.uuid4()
        async with db.begin_session() as sess:
            sess.add(
                DomainRow(
                    id=domain_id,
                    name=_DOMAIN,
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={},
                    allowed_docker_registries=[],
                )
            )
            sess.add(
                UserResourcePolicyRow(
                    name="user-policy",
                    max_vfolder_count=10,
                    max_quota_scope_size=-1,
                    max_session_count_per_model_session=10,
                    max_customized_image_count=10,
                )
            )
            sess.add(
                ProjectResourcePolicyRow(
                    name="project-policy",
                    max_vfolder_count=10,
                    max_quota_scope_size=-1,
                    max_network_count=10,
                )
            )
            sess.add(
                KeyPairResourcePolicyRow(
                    name="keypair-policy",
                    max_concurrent_sessions=10,
                    max_concurrent_sftp_sessions=2,
                    max_containers_per_session=10,
                    idle_timeout=3600,
                )
            )
            await sess.flush()
            sess.add_all([
                UserRow(
                    uuid=user_id,
                    username="alice",
                    email=_EMAIL,
                    domain_name=_DOMAIN,
                    role=UserRole.USER,
                    resource_policy="user-policy",
                    domain_id=domain_id,
                ),
                ProjectRow(
                    id=project_id,
                    name="project",
                    domain_name=_DOMAIN,
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    resource_policy="project-policy",
                ),
            ])
            await sess.flush()
            sess.add(
                KeyPairRow(
                    access_key=_ACCESS_KEY,
                    secret_key=SecretValue("secret"),
                    user=user_id,
                    is_active=True,
                    resource_policy="keypair-policy",
                )
            )
            await sess.flush()
            await VirtualEntitySeeder().enroll_user_in_project(sess, project_id, user_id)
            await sess.commit()

    @pytest.fixture
    def graph_ctx(self, db: ExtendedAsyncSAEngine, seeded: None) -> GraphQueryContext:
        ctx = MagicMock(spec=GraphQueryContext)
        ctx.db = db
        return ctx

    async def test_loads_the_keypairs_of_the_requested_email(
        self, graph_ctx: GraphQueryContext
    ) -> None:
        loaded = await KeyPair.batch_load_by_email(graph_ctx, [_EMAIL])

        assert [
            [(keypair.access_key, keypair.user_id) for keypair in keypairs if keypair is not None]
            for keypairs in loaded
        ] == [[(_ACCESS_KEY, _EMAIL)]]
