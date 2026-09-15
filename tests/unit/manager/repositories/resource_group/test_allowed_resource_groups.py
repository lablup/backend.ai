import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from datetime import UTC, datetime

import pytest

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.types import DefaultForUnspecified, ResourceSlot
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.project import ProjectRow
from ai.backend.manager.models.resource_group import (
    ResourceGroupForDomainRow,
    ResourceGroupForKeypairsRow,
    ResourceGroupForProjectRow,
    ResourceGroupOpts,
    ResourceGroupRow,
    query_allowed_sgroups,
)
from ai.backend.manager.models.resource_group.searchers import AllowedResourceGroupsSearch
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.secret.types import SecretValue
from ai.backend.testutils.db import with_tables


@dataclass(frozen=True)
class _Owner:
    domain_id: DomainID
    domain_name: str
    project_id: ProjectID
    user_id: UserID
    access_key: str


class TestAllowedResourceGroupsSearch:
    @pytest.fixture
    async def db(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                DomainRow,
                ResourceGroupRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRow,
                KeyPairRow,
                ProjectRow,
                ResourceGroupForDomainRow,
                ResourceGroupForProjectRow,
                ResourceGroupForKeypairsRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def owner(self, db: ExtendedAsyncSAEngine) -> _Owner:
        domain_id = DomainID(uuid.uuid4())
        domain_name = f"domain-{uuid.uuid4().hex[:8]}"
        project_id = ProjectID(uuid.uuid4())
        user_id = UserID(uuid.uuid4())
        access_key = "AKTESTALLOWED0001"
        policy = "default"
        async with db.begin_session() as sess:
            sess.add(
                DomainRow(
                    id=domain_id,
                    name=domain_name,
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                )
            )
            sess.add(
                UserResourcePolicyRow(
                    name=policy,
                    max_vfolder_count=0,
                    max_quota_scope_size=-1,
                    max_session_count_per_model_session=10,
                    max_customized_image_count=10,
                )
            )
            sess.add(
                ProjectResourcePolicyRow(
                    name=policy,
                    max_vfolder_count=0,
                    max_quota_scope_size=-1,
                    max_network_count=3,
                )
            )
            sess.add(
                KeyPairResourcePolicyRow(
                    name=policy,
                    default_for_unspecified=DefaultForUnspecified.LIMITED,
                    total_resource_slots=ResourceSlot(),
                    max_session_lifetime=0,
                    max_concurrent_sessions=10,
                    max_concurrent_sftp_sessions=1,
                    max_containers_per_session=1,
                    idle_timeout=0,
                    allowed_vfolder_hosts={},
                )
            )
            await sess.flush()
            sess.add(
                UserRow(
                    uuid=user_id,
                    username=f"user-{uuid.uuid4().hex[:8]}",
                    email=f"user-{uuid.uuid4().hex[:8]}@example.com",
                    password=PasswordInfo(
                        password="test_password",
                        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                        rounds=100_000,
                        salt_size=32,
                    ),
                    domain_id=domain_id,
                    need_password_change=False,
                    status=UserStatus.ACTIVE,
                    status_info="active",
                    created_at=datetime.now(tz=UTC),
                    domain_name=domain_name,
                    resource_policy=policy,
                )
            )
            sess.add(
                ProjectRow(
                    id=project_id,
                    name=f"project-{uuid.uuid4().hex[:8]}",
                    is_active=True,
                    created_at=datetime.now(tz=UTC),
                    domain_name=domain_name,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={},
                    resource_policy=policy,
                )
            )
            await sess.flush()
            sess.add(
                KeyPairRow(
                    user=user_id,
                    access_key=access_key,
                    secret_key=SecretValue("test-secret"),
                    is_active=True,
                    is_admin=False,
                    resource_policy=policy,
                    rate_limit=1000,
                )
            )
        return _Owner(domain_id, domain_name, project_id, user_id, access_key)

    async def _add_resource_group(
        self, db: ExtendedAsyncSAEngine, name: str, *, is_active: bool = True
    ) -> ResourceGroupRow:
        row = ResourceGroupRow(
            name=name,
            is_active=is_active,
            is_public=True,
            created_at=datetime.now(tz=UTC),
            driver="static",
            driver_opts={},
            scheduler="fifo",
            scheduler_opts=ResourceGroupOpts(),
            use_host_network=False,
        )
        async with db.begin_session() as sess:
            sess.add(row)
        return row

    async def test_matches_the_legacy_query(self, db: ExtendedAsyncSAEngine, owner: _Owner) -> None:
        by_domain = await self._add_resource_group(db, "rg-c-domain")
        by_project = await self._add_resource_group(db, "rg-a-project")
        by_keypair = await self._add_resource_group(db, "rg-b-keypair")
        inactive = await self._add_resource_group(db, "rg-d-inactive", is_active=False)
        await self._add_resource_group(db, "rg-e-unrelated")
        async with db.begin_session() as sess:
            sess.add_all([
                ResourceGroupForDomainRow(
                    resource_group_id=by_domain.id, domain_id=owner.domain_id
                ),
                ResourceGroupForDomainRow(resource_group_id=inactive.id, domain_id=owner.domain_id),
                ResourceGroupForProjectRow(resource_group_id=by_project.id, group=owner.project_id),
                ResourceGroupForKeypairsRow(
                    resource_group_id=by_keypair.id, access_key=owner.access_key
                ),
            ])

        async with db.begin_readonly() as conn:
            legacy = await query_allowed_sgroups(
                conn, owner.domain_name, owner.project_id, owner.access_key
            )
        search = AllowedResourceGroupsSearch(
            domain_id=owner.domain_id, project_ids=[owner.project_id], user_id=owner.user_id
        )
        async with V2DBOpsProvider(db).read_ops() as r:
            result = await r.search_with_scopes(search.operation_scopes(), search.searcher())

        assert [rg.name for rg in result.items] == ["rg-a-project", "rg-b-keypair", "rg-c-domain"]
        assert [rg.name for rg in result.items] == [row.name for row in legacy]
