"""Tests for the projects the legacy agent query reads off an access key."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass

import pytest

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.api.gql_legacy.agent import _query_domain_groups_by_ak
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.deployment_auto_scaling_policy import DeploymentAutoScalingPolicyRow
from ai.backend.manager.models.deployment_policy import DeploymentPolicyRow
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.models.deployment_revision_preset import DeploymentRevisionPresetRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.project import AssocGroupUserRow, ProjectRow
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
from ai.backend.manager.models.runtime_variant import RuntimeVariantRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import (
    PasswordHashAlgorithm,
    PasswordInfo,
    UserRole,
    UserRow,
    UserStatus,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.entity_membership_cap import EntityMembershipCapRow
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.secret.types import SecretValue
from ai.backend.testutils.db import with_tables
from ai.backend.testutils.virtual_entity import VirtualEntitySeeder


@dataclass
class _Membership:
    access_key: str
    domain_name: str
    graph_project_id: uuid.UUID
    other_domain_project_id: uuid.UUID


class TestQueryDomainGroupsByAccessKey:
    @pytest.fixture
    async def db_engine(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
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
                AssocGroupUserRow,
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
                VirtualEntityRow,
                EntityMembershipRow,
                EntityMembershipCapRow,
                ScopeBindingRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def membership(self, db_engine: ExtendedAsyncSAEngine) -> _Membership:
        """A user enrolled in the graph in one project of each of two domains, and left
        only in the legacy table in a third project of their own domain."""
        domain_names = [f"dom-{uuid.uuid4().hex[:8]}", f"dom-{uuid.uuid4().hex[:8]}"]
        domain_ids = [DomainID(uuid.uuid4()), DomainID(uuid.uuid4())]
        user_id = uuid.uuid4()
        access_key = f"AKTEST{uuid.uuid4().hex[:14].upper()}"
        graph_project_id = uuid.uuid4()
        other_domain_project_id = uuid.uuid4()
        legacy_project_id = uuid.uuid4()

        async with db_engine.begin_session() as db_sess:
            for domain_id, domain_name in zip(domain_ids, domain_names, strict=True):
                db_sess.add(
                    DomainRow(
                        id=domain_id,
                        name=domain_name,
                        description="",
                        is_active=True,
                        total_resource_slots=ResourceSlot(),
                        allowed_vfolder_hosts={},
                        allowed_docker_registries=[],
                    )
                )
            user_policy = UserResourcePolicyRow(
                name=f"upol-{uuid.uuid4().hex[:8]}",
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=0,
                max_customized_image_count=0,
            )
            project_policy = ProjectResourcePolicyRow(
                name=f"ppol-{uuid.uuid4().hex[:8]}",
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_network_count=0,
            )
            keypair_policy = KeyPairResourcePolicyRow(
                name=f"kpol-{uuid.uuid4().hex[:8]}",
                max_concurrent_sessions=1,
                max_concurrent_sftp_sessions=1,
                max_containers_per_session=1,
                idle_timeout=0,
            )
            db_sess.add_all([user_policy, project_policy, keypair_policy])
            await db_sess.flush()

            db_sess.add(
                UserRow(
                    uuid=user_id,
                    username=f"user-{user_id.hex[:8]}",
                    email=f"{user_id.hex[:8]}@example.com",
                    password=PasswordInfo(
                        password="dummy",
                        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                        rounds=100_000,
                        salt_size=32,
                    ),
                    need_password_change=False,
                    status=UserStatus.ACTIVE,
                    status_info="active",
                    domain_name=domain_names[0],
                    role=UserRole.USER,
                    resource_policy=user_policy.name,
                    domain_id=domain_ids[0],
                )
            )
            await db_sess.flush()
            db_sess.add(
                KeyPairRow(
                    access_key=access_key,
                    secret_key=SecretValue("test_secret_key"),
                    user=user_id,
                    is_active=True,
                    is_default=True,
                    resource_policy=keypair_policy.name,
                )
            )
            for project_id, domain_name in [
                (graph_project_id, domain_names[0]),
                (other_domain_project_id, domain_names[1]),
                (legacy_project_id, domain_names[0]),
            ]:
                db_sess.add(
                    ProjectRow(
                        id=project_id,
                        name=f"proj-{project_id.hex[:8]}",
                        domain_name=domain_name,
                        resource_policy=project_policy.name,
                    )
                )
            await db_sess.flush()

            seeder = VirtualEntitySeeder()
            await seeder.enroll_user_in_project(db_sess, graph_project_id, user_id)
            await seeder.enroll_user_in_project(db_sess, other_domain_project_id, user_id)
            db_sess.add(AssocGroupUserRow(group_id=legacy_project_id, user_id=user_id))

        return _Membership(
            access_key=access_key,
            domain_name=domain_names[0],
            graph_project_id=graph_project_id,
            other_domain_project_id=other_domain_project_id,
        )

    async def test_reads_graph_membership_in_the_domain(
        self,
        db_engine: ExtendedAsyncSAEngine,
        membership: _Membership,
    ) -> None:
        async with db_engine.begin_readonly() as conn:
            domain_name, _, project_ids = await _query_domain_groups_by_ak(
                conn, membership.access_key, None
            )

        assert domain_name == membership.domain_name
        assert project_ids == [membership.graph_project_id]
