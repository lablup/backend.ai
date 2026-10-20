"""User, project and domain dotfiles share one bundle for all creation paths."""

from __future__ import annotations

import uuid

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainName
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.user import UserEntityType
from ai.backend.common.types import AccessKey, SecretKey
from ai.backend.manager.data.dotfile.types import DotfileEntries, DotfileEntry
from ai.backend.manager.data.session.draft import (
    SessionIdentityDraft,
    SessionResourceSpecDraft,
    SessionScopeDraft,
    SessionSpecDraft,
)
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.dotfile.row import DotfileRow
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.ops.v2.reconciler.provider import ReconcileOpsProvider
from ai.backend.manager.repositories.scheduler.db_source.db_source import ScheduleDBSource
from ai.backend.manager.secret.types import SecretValue
from ai.backend.manager.types import UserScope
from ai.backend.testutils.fixtures import DomainFixtureData

_USER = DotfileEntry(path=".bashrc", perm="600", data="user")
_PROJECT = DotfileEntry(path=".profile", perm="644", data="project")
_DOMAIN = DotfileEntry(path=".vimrc", perm="644", data="domain")
_STALE = DotfileEntry(path=".bashrc", perm="644", data="stale keypair")


@pytest.fixture
async def dotfile_scope(
    db_with_cleanup: ExtendedAsyncSAEngine,
    test_user_uuid: uuid.UUID,
    test_group_id: uuid.UUID,
    test_domain: DomainFixtureData,
    test_access_key: AccessKey,
) -> UserScope:
    async with db_with_cleanup.begin_session() as session:
        await session.execute(
            sa.insert(VirtualEntityRow).values(
                entity_type=UserEntityType(), entity_id=test_user_uuid
            )
        )
        await session.execute(
            sa.insert(DotfileRow).values(
                entity_type=UserEntityType(),
                entity_id=test_user_uuid,
                path=_USER.path,
                perm=_USER.perm,
                data=_USER.data,
                is_default=True,
            )
        )
        await session.execute(
            sa.insert(DotfileRow).values(
                entity_type=UserEntityType(),
                entity_id=test_user_uuid,
                path=".ignored",
                perm="600",
                data="non-default",
                is_default=False,
            )
        )
        await session.execute(
            sa.update(ProjectRow)
            .where(ProjectRow.id == test_group_id)
            .values(dotfiles=DotfileEntries((_STALE, _PROJECT)).pack())
        )
        await session.execute(
            sa.update(DomainRow)
            .where(DomainRow.name == test_domain.domain_name)
            .values(
                dotfiles=DotfileEntries((
                    _STALE,
                    DotfileEntry(_PROJECT.path, "644", "domain"),
                    _DOMAIN,
                )).pack()
            )
        )
        await session.execute(
            sa.update(KeyPairRow)
            .where(KeyPairRow.access_key == test_access_key)
            .values(
                is_default=True,
                ssh_public_key="public",
                ssh_private_key="private",
            )
        )
    return UserScope(
        domain_name=test_domain.domain_name,
        group_id=test_group_id,
        user_uuid=test_user_uuid,
        user_role="user",
    )


@pytest.fixture
async def second_access_key(
    db_with_cleanup: ExtendedAsyncSAEngine,
    dotfile_scope: UserScope,
    test_keypair_resource_policy_name: str,
) -> AccessKey:
    key = AccessKey(f"AKIA{uuid.uuid4().hex[:16].upper()}")
    async with db_with_cleanup.begin_session() as session:
        session.add(
            KeyPairRow(
                access_key=key,
                secret_key=SecretValue(SecretKey("secret")),
                user=dotfile_scope.user_uuid,
                is_active=True,
                is_admin=False,
                resource_policy=test_keypair_resource_policy_name,
            )
        )
    return key


class TestFetchDotfiles:
    @pytest.mark.parametrize("has_default", [True, False])
    @pytest.mark.parametrize("key_kind", ["default", "non_default", "none"])
    async def test_enqueue_dotfiles_for_selected_key(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        dotfile_scope: UserScope,
        test_access_key: AccessKey,
        second_access_key: AccessKey,
        key_kind: str,
        has_default: bool,
    ) -> None:
        if not has_default:
            async with db_with_cleanup.begin() as conn:
                await conn.execute(sa.update(DotfileRow).values(is_default=False))
        keys = {"default": test_access_key, "non_default": second_access_key, "none": None}
        draft = SessionSpecDraft(
            resource_spec=SessionResourceSpecDraft(
                identity=SessionIdentityDraft(
                    user_uuid=dotfile_scope.user_uuid, access_key=keys[key_kind]
                ),
            ),
            scope=SessionScopeDraft(
                domain_name=DomainName(dotfile_scope.domain_name),
                project_id=ProjectID(dotfile_scope.group_id),
            ),
        )
        source = ScheduleDBSource(db_with_cleanup, ReconcileOpsProvider(db_with_cleanup))
        async with db_with_cleanup.begin_readonly_session() as session:
            result = await source._fetch_user_enqueue_fetch(session, draft)
        expected_dotfiles = (
            () if key_kind == "none" else (_DOMAIN, _PROJECT, _USER if has_default else _STALE)
        )
        assert result.dotfiles.dotfiles == expected_dotfiles
        if key_kind == "default":
            assert result.dotfiles.ssh_keypair is not None
            assert result.dotfiles.ssh_keypair.public_key == "public"
            assert result.dotfiles.ssh_keypair.private_key == "private"
        else:
            assert result.dotfiles.ssh_keypair is None

    async def test_delegated_key_uses_its_owners_dotfiles(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        dotfile_scope: UserScope,
        test_access_key: AccessKey,
    ) -> None:
        requester_scope = UserScope(
            domain_name=dotfile_scope.domain_name,
            group_id=dotfile_scope.group_id,
            user_uuid=uuid.uuid4(),
            user_role="user",
        )
        source = ScheduleDBSource(db_with_cleanup, ReconcileOpsProvider(db_with_cleanup))
        async with db_with_cleanup.begin_readonly_session() as session:
            result = await source._fetch_dotfile_data(session, requester_scope, test_access_key)
        assert result.dotfiles == (_DOMAIN, _PROJECT, _USER)
        assert result.ssh_keypair is not None
        assert result.ssh_keypair.public_key == "public"
        assert result.ssh_keypair.private_key == "private"
