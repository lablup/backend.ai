"""
Session matching, rename and result writing in SessionDBSource, against a real database.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Protocol

import pytest
import sqlalchemy as sa
from dateutil.tz import tzutc

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.types import (
    AccessKey,
    ClusterMode,
    DefaultForUnspecified,
    KernelId,
    ResourceSlot,
    SessionId,
    SessionResult,
    SessionTypes,
)
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.defs import DEFAULT_ROLE
from ai.backend.manager.errors.kernel import SessionAlreadyExists, TooManySessionsMatched
from ai.backend.manager.models.agent.row import AgentRow
from ai.backend.manager.models.association_container_registries_groups.row import (
    AssociationContainerRegistriesGroupsRow,
)
from ai.backend.manager.models.container_registry.row import ContainerRegistryRow
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.image.row import ImageAliasRow, ImageRow
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.project.row import ProjectRow, ProjectType
from ai.backend.manager.models.resource_group.row import (
    ResourceGroupForDomainRow,
    ResourceGroupForKeypairsRow,
    ResourceGroupForProjectRow,
    ResourceGroupRow,
)
from ai.backend.manager.models.resource_group.types import ResourceGroupOpts
from ai.backend.manager.models.resource_policy.row import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_slot.row import AgentResourceRow, ResourceSlotTypeRow
from ai.backend.manager.models.session.row import SessionRow
from ai.backend.manager.models.session.updaters import SessionUpdater
from ai.backend.manager.models.user.row import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.session.db_source.db_source import SessionDBSource
from ai.backend.manager.secret.types import SecretValue
from ai.backend.manager.types import OptionalState
from ai.backend.testutils.db import with_tables

_DOMAIN_NAME = "match-domain"
_RESOURCE_GROUP_NAME = "match-rg"


@dataclass(frozen=True)
class _Owner:
    domain_id: DomainID
    resource_group_id: ResourceGroupID
    user_id: uuid.UUID
    project_id: uuid.UUID
    access_key: AccessKey


class _SessionFactory(Protocol):
    async def __call__(
        self,
        *,
        name: str,
        status: SessionStatus = SessionStatus.RUNNING,
        created_at: datetime | None = None,
        access_key: AccessKey | None = None,
        with_main_kernel: bool = False,
    ) -> SessionId: ...


@pytest.fixture
async def db_with_tables(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(
        database_connection,
        [
            # FK dependency order: parents before children
            DomainRow,
            ResourceGroupRow,
            ResourceSlotTypeRow,
            AgentRow,
            AgentResourceRow,
            UserResourcePolicyRow,
            ProjectResourcePolicyRow,
            KeyPairResourcePolicyRow,
            UserRow,
            ProjectRow,
            KeyPairRow,
            ResourceGroupForDomainRow,
            ResourceGroupForProjectRow,
            ResourceGroupForKeypairsRow,
            ContainerRegistryRow,
            AssociationContainerRegistriesGroupsRow,
            ImageRow,
            ImageAliasRow,
            SessionRow,
            KernelRow,
        ],
    ):
        yield database_connection


@pytest.fixture
def db_source(db_with_tables: ExtendedAsyncSAEngine) -> SessionDBSource:
    return SessionDBSource(db_with_tables, V2DBOpsProvider(db_with_tables))


async def _add_user_with_keypair(
    db: ExtendedAsyncSAEngine,
    *,
    domain_id: DomainID,
    username: str,
    access_key: AccessKey,
) -> uuid.UUID:
    user_id = uuid.uuid4()
    async with db.begin_session() as db_sess:
        db_sess.add(
            UserRow(
                uuid=user_id,
                username=username,
                email=f"{username}@example.com",
                password=None,
                need_password_change=False,
                full_name=username,
                description="",
                status=UserStatus.ACTIVE,
                status_info="",
                domain_name=_DOMAIN_NAME,
                role=UserRole.USER,
                resource_policy="match-user-policy",
                allowed_client_ip=None,
                totp_key=None,
                domain_id=domain_id,
            )
        )
        await db_sess.flush()
        db_sess.add(
            KeyPairRow(
                user=user_id,
                access_key=access_key,
                secret_key=SecretValue(f"secret-{access_key}"),
                is_active=True,
                is_admin=False,
                resource_policy="match-keypair-policy",
                rate_limit=1000,
            )
        )
    return user_id


@pytest.fixture
async def owner(db_with_tables: ExtendedAsyncSAEngine) -> _Owner:
    """A domain, resource group, project and one user with one keypair."""
    domain_id = DomainID(uuid.uuid4())
    resource_group_id = ResourceGroupID(uuid.uuid4())
    project_id = uuid.uuid4()
    async with db_with_tables.begin_session() as db_sess:
        db_sess.add(
            DomainRow(
                id=domain_id,
                name=_DOMAIN_NAME,
                description="",
                is_active=True,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts={},
                allowed_docker_registries=[],
                integration_id=None,
            )
        )
        db_sess.add(
            ResourceGroupRow(
                id=resource_group_id,
                name=_RESOURCE_GROUP_NAME,
                is_active=True,
                is_public=True,
                driver="static",
                driver_opts={},
                scheduler="fifo",
                scheduler_opts=ResourceGroupOpts(),
            )
        )
        db_sess.add(
            UserResourcePolicyRow(
                name="match-user-policy",
                max_vfolder_count=100,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=10,
                max_customized_image_count=10,
            )
        )
        db_sess.add(
            ProjectResourcePolicyRow(
                name="match-project-policy",
                max_vfolder_count=100,
                max_quota_scope_size=-1,
                max_network_count=10,
            )
        )
        db_sess.add(
            KeyPairResourcePolicyRow(
                name="match-keypair-policy",
                default_for_unspecified=DefaultForUnspecified.UNLIMITED,
                total_resource_slots=ResourceSlot(),
                max_session_lifetime=0,
                max_concurrent_sessions=10,
                max_concurrent_sftp_sessions=5,
                max_containers_per_session=1,
                idle_timeout=3600,
            )
        )
        await db_sess.flush()
        db_sess.add(
            ProjectRow(
                id=project_id,
                name="match-project",
                description="",
                is_active=True,
                domain_name=_DOMAIN_NAME,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts={},
                resource_policy="match-project-policy",
                type=ProjectType.GENERAL,
            )
        )
    access_key = AccessKey("AKIAMATCHOWNER0001")
    user_id = await _add_user_with_keypair(
        db_with_tables,
        domain_id=domain_id,
        username="match-owner",
        access_key=access_key,
    )
    return _Owner(
        domain_id=domain_id,
        resource_group_id=resource_group_id,
        user_id=user_id,
        project_id=project_id,
        access_key=access_key,
    )


@pytest.fixture
async def other_access_key(db_with_tables: ExtendedAsyncSAEngine, owner: _Owner) -> AccessKey:
    """The keypair of a second user in the same domain and project."""
    access_key = AccessKey("AKIAMATCHOTHER0001")
    await _add_user_with_keypair(
        db_with_tables,
        domain_id=owner.domain_id,
        username="match-other",
        access_key=access_key,
    )
    return access_key


@pytest.fixture
def add_session(db_with_tables: ExtendedAsyncSAEngine, owner: _Owner) -> _SessionFactory:
    """Insert a session of ``owner`` (or of another access key's user), optionally with a main kernel."""

    async def _add(
        *,
        name: str,
        status: SessionStatus = SessionStatus.RUNNING,
        created_at: datetime | None = None,
        access_key: AccessKey | None = None,
        with_main_kernel: bool = False,
    ) -> SessionId:
        session_id = SessionId(uuid.uuid4())
        key = access_key or owner.access_key
        created = created_at or datetime.now(tzutc())
        async with db_with_tables.begin_session() as db_sess:
            user_id = await db_sess.scalar(
                sa.select(KeyPairRow.user).where(KeyPairRow.access_key == key)
            )
            db_sess.add(
                SessionRow(
                    id=session_id,
                    creation_id=session_id.hex[:32],
                    name=name,
                    session_type=SessionTypes.INTERACTIVE,
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    cluster_size=1,
                    domain_id=owner.domain_id,
                    domain_name=_DOMAIN_NAME,
                    group_id=owner.project_id,
                    user_uuid=user_id,
                    access_key=key,
                    tag=None,
                    status=status,
                    status_info=None,
                    status_data=None,
                    status_history={},
                    result=SessionResult.UNDEFINED,
                    created_at=created,
                    terminated_at=None,
                    starts_at=None,
                    startup_command=None,
                    callback_url=None,
                    vfolder_mounts=[],
                    environ=None,
                    bootstrap_script=None,
                    use_host_network=False,
                    resource_group_id=owner.resource_group_id,
                    scaling_group_name=_RESOURCE_GROUP_NAME,
                )
            )
            await db_sess.flush()
            if with_main_kernel:
                db_sess.add(
                    KernelRow(
                        id=KernelId(uuid.uuid4()),
                        session_id=session_id,
                        session_name=name,
                        session_type=SessionTypes.INTERACTIVE,
                        domain_name=_DOMAIN_NAME,
                        group_id=owner.project_id,
                        user_uuid=user_id,
                        access_key=key,
                        cluster_mode=ClusterMode.SINGLE_NODE.value,
                        cluster_size=1,
                        cluster_role=DEFAULT_ROLE,
                        cluster_idx=0,
                        local_rank=0,
                        cluster_hostname="main",
                        scaling_group=_RESOURCE_GROUP_NAME,
                        resource_group_id=owner.resource_group_id,
                        image="cr.backend.ai/stable/python:latest",
                        architecture="x86_64",
                        registry="cr.backend.ai",
                        agent=None,
                        agent_addr=None,
                        container_id=None,
                        repl_in_port=2000,
                        repl_out_port=2001,
                        stdin_port=2002,
                        stdout_port=2003,
                        use_host_network=False,
                        status=KernelStatus.RUNNING,
                        status_info=None,
                        status_data=None,
                        status_history={},
                        status_changed=created,
                        result=SessionResult.UNDEFINED,
                        created_at=created,
                        terminated_at=None,
                        starts_at=None,
                        occupied_shares={},
                        environ=None,
                        vfolder_mounts=[],
                        attached_devices={},
                        resource_opts=None,
                        preopen_ports=None,
                        bootstrap_script=None,
                        startup_command=None,
                    )
                )
        return session_id

    return _add


class TestMatchSessions:
    async def test_id_match_shuts_out_name_matches(
        self, db_source: SessionDBSource, owner: _Owner, add_session: _SessionFactory
    ) -> None:
        target = await add_session(name="by-id-target")
        await add_session(name=str(target), status=SessionStatus.TERMINATED)

        matches = await db_source.match_sessions(str(target), owner.access_key)

        assert [row.id for row in matches] == [target]

    async def test_name_matches_come_newest_first(
        self, db_source: SessionDBSource, owner: _Owner, add_session: _SessionFactory
    ) -> None:
        base = datetime.now(tzutc())
        older = await add_session(
            name="dup", status=SessionStatus.TERMINATED, created_at=base - timedelta(hours=2)
        )
        newer = await add_session(name="dup", created_at=base - timedelta(hours=1))

        matches = await db_source.match_sessions("dup", owner.access_key)

        assert [row.id for row in matches] == [newer, older]

    async def test_name_matches_stop_at_ten(
        self, db_source: SessionDBSource, owner: _Owner, add_session: _SessionFactory
    ) -> None:
        base = datetime.now(tzutc())
        created = [
            await add_session(
                name="many",
                status=SessionStatus.TERMINATED,
                created_at=base - timedelta(minutes=offset),
            )
            for offset in range(11)
        ]

        matches = await db_source.match_sessions("many", owner.access_key)

        assert [row.id for row in matches] == created[:10]

    async def test_other_access_key_is_not_matched(
        self,
        db_source: SessionDBSource,
        owner: _Owner,
        other_access_key: AccessKey,
        add_session: _SessionFactory,
    ) -> None:
        await add_session(name="theirs", access_key=other_access_key)

        matches = await db_source.match_sessions("theirs", owner.access_key)

        assert matches == []

    async def test_no_match_returns_empty(
        self, db_source: SessionDBSource, owner: _Owner, add_session: _SessionFactory
    ) -> None:
        await add_session(name="present")

        matches = await db_source.match_sessions("absent", owner.access_key)

        assert matches == []


class TestUpdateSessionRename:
    @staticmethod
    def _rename(session_id: SessionId, name: str) -> SessionUpdater:
        return SessionUpdater(session_id=SessionID(session_id), name=OptionalState.update(name))

    async def test_live_namesake_raises_already_exists(
        self, db_source: SessionDBSource, add_session: _SessionFactory
    ) -> None:
        target = await add_session(name="renamed-me", with_main_kernel=True)
        await add_session(name="taken")

        with pytest.raises(SessionAlreadyExists):
            await db_source.update_session(self._rename(target, "taken"), session_name="taken")

    async def test_two_namesakes_raise_too_many_matched(
        self, db_source: SessionDBSource, add_session: _SessionFactory
    ) -> None:
        target = await add_session(name="renamed-me", with_main_kernel=True)
        await add_session(name="crowded", status=SessionStatus.ERROR)
        await add_session(name="crowded", status=SessionStatus.ERROR)

        with pytest.raises(TooManySessionsMatched):
            await db_source.update_session(self._rename(target, "crowded"), session_name="crowded")

    async def test_terminated_namesake_does_not_block(
        self,
        db_source: SessionDBSource,
        db_with_tables: ExtendedAsyncSAEngine,
        add_session: _SessionFactory,
    ) -> None:
        target = await add_session(name="renamed-me", with_main_kernel=True)
        await add_session(name="freed", status=SessionStatus.TERMINATED)

        result = await db_source.update_session(self._rename(target, "freed"), session_name="freed")

        assert result is not None
        assert result.name == "freed"
        async with db_with_tables.begin_readonly_session() as db_sess:
            kernel_names = list(
                await db_sess.scalars(
                    sa.select(KernelRow.session_name).where(KernelRow.session_id == target)
                )
            )
        assert kernel_names == ["freed"]


class TestSetSessionResult:
    @pytest.mark.parametrize(
        ("success", "expected"),
        [(True, SessionResult.SUCCESS), (False, SessionResult.FAILURE)],
    )
    async def test_writes_the_result(
        self,
        db_source: SessionDBSource,
        db_with_tables: ExtendedAsyncSAEngine,
        add_session: _SessionFactory,
        success: bool,
        expected: SessionResult,
    ) -> None:
        session_id = await add_session(name="batch")

        await db_source.set_session_result(session_id, success)

        async with db_with_tables.begin_readonly_session() as db_sess:
            result = await db_sess.scalar(
                sa.select(SessionRow.result).where(SessionRow.id == session_id)
            )
        assert result == expected
