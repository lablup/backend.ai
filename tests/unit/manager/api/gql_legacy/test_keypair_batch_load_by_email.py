"""Loading legacy ``KeyPair`` objects by the owner's email."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
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
_ALICE = "alice@example.com"
_BOB = "bob@example.com"
_ALICE_ACTIVE_AK = AccessKey("AKALICEACTIVE")
_ALICE_INACTIVE_AK = AccessKey("AKALICEINACTIVE")
_BOB_AK = AccessKey("AKBOB")

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


@dataclass(frozen=True)
class _LoadCase:
    emails: list[str]
    expected_access_keys: list[set[AccessKey]]
    is_active: bool | None = None
    domain_name: str | None = None


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
        alice_id = uuid.uuid4()
        bob_id = uuid.uuid4()
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
                    uuid=alice_id,
                    username="alice",
                    email=_ALICE,
                    domain_name=_DOMAIN,
                    role=UserRole.USER,
                    resource_policy="user-policy",
                    domain_id=domain_id,
                ),
                UserRow(
                    uuid=bob_id,
                    username="bob",
                    email=_BOB,
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
            sess.add_all([
                KeyPairRow(
                    access_key=_ALICE_ACTIVE_AK,
                    secret_key=SecretValue("secret"),
                    user=alice_id,
                    is_active=True,
                    resource_policy="keypair-policy",
                ),
                KeyPairRow(
                    access_key=_ALICE_INACTIVE_AK,
                    secret_key=SecretValue("secret"),
                    user=alice_id,
                    is_active=False,
                    resource_policy="keypair-policy",
                ),
                KeyPairRow(
                    access_key=_BOB_AK,
                    secret_key=SecretValue("secret"),
                    user=bob_id,
                    is_active=True,
                    resource_policy="keypair-policy",
                ),
            ])
            await sess.flush()
            seeder = VirtualEntitySeeder()
            await seeder.enroll_user_in_project(sess, project_id, alice_id)
            await seeder.enroll_user_in_project(sess, project_id, bob_id)
            await sess.commit()

    @pytest.fixture
    def graph_ctx(self, db: ExtendedAsyncSAEngine, seeded: None) -> GraphQueryContext:
        ctx = MagicMock(spec=GraphQueryContext)
        ctx.db = db
        return ctx

    @pytest.mark.parametrize(
        "case",
        [
            _LoadCase(
                emails=[_ALICE, _BOB],
                expected_access_keys=[{_ALICE_ACTIVE_AK, _ALICE_INACTIVE_AK}, {_BOB_AK}],
            ),
            _LoadCase(
                emails=[_BOB, _ALICE],
                expected_access_keys=[{_BOB_AK}, {_ALICE_ACTIVE_AK, _ALICE_INACTIVE_AK}],
            ),
            _LoadCase(
                emails=["nobody@example.com"],
                expected_access_keys=[set()],
            ),
            _LoadCase(
                emails=[_ALICE],
                is_active=True,
                expected_access_keys=[{_ALICE_ACTIVE_AK}],
            ),
            _LoadCase(
                emails=[_ALICE],
                is_active=False,
                expected_access_keys=[{_ALICE_INACTIVE_AK}],
            ),
            _LoadCase(
                emails=[_ALICE],
                domain_name=_DOMAIN,
                expected_access_keys=[{_ALICE_ACTIVE_AK, _ALICE_INACTIVE_AK}],
            ),
            _LoadCase(
                emails=[_ALICE],
                domain_name="other-domain",
                expected_access_keys=[set()],
            ),
        ],
        ids=lambda case: "+".join(case.emails)
        + f"|is_active={case.is_active}|domain_name={case.domain_name}",
    )
    async def test_keypairs_are_grouped_under_the_requested_email(
        self, graph_ctx: GraphQueryContext, case: _LoadCase
    ) -> None:
        loaded = await KeyPair.batch_load_by_email(
            graph_ctx,
            case.emails,
            domain_name=case.domain_name,
            is_active=case.is_active,
        )

        assert [
            {keypair.access_key for keypair in keypairs if keypair is not None}
            for keypairs in loaded
        ] == case.expected_access_keys
        assert all(
            keypair is not None and keypair.user_id == email
            for email, keypairs in zip(case.emails, loaded, strict=True)
            for keypair in keypairs
        )
