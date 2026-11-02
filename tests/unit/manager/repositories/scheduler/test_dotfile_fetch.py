from __future__ import annotations

import uuid

import pytest
import sqlalchemy as sa

from ai.backend.common import msgpack
from ai.backend.common.types import AccessKey, SecretKey
from ai.backend.manager.data.dotfile.types import DotfileEntry
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.scheduler.db_source.db_source import ScheduleDBSource
from ai.backend.manager.types import UserScope

_USER = DotfileEntry(path=".bashrc", perm="600", data="user")
_PROJECT = DotfileEntry(path=".profile", perm="644", data="project")
_DOMAIN = DotfileEntry(path=".vimrc", perm="644", data="domain")


def _pack(entries: list[DotfileEntry]) -> bytes:
    return msgpack.packb([{"path": e.path, "perm": e.perm, "data": e.data} for e in entries])


@pytest.fixture
async def dotfile_scope(
    db_with_cleanup: ExtendedAsyncSAEngine,
    test_user_uuid: uuid.UUID,
    test_group_id: uuid.UUID,
    test_domain_name: str,
    test_access_key: AccessKey,
) -> UserScope:
    async with db_with_cleanup.begin_session() as session:
        await session.execute(
            sa.update(GroupRow)
            .where(GroupRow.id == test_group_id)
            .values(dotfiles=_pack([_PROJECT]))
        )
        await session.execute(
            sa.update(DomainRow)
            .where(DomainRow.name == test_domain_name)
            .values(dotfiles=_pack([_DOMAIN]))
        )
        await session.execute(
            sa.update(KeyPairRow)
            .where(KeyPairRow.access_key == test_access_key)
            .values(
                dotfiles=_pack([_USER]),
                ssh_public_key="public",
                ssh_private_key="private",
            )
        )
    return UserScope(
        domain_name=test_domain_name,
        group_id=test_group_id,
        user_uuid=test_user_uuid,
        user_role="user",
    )


async def test_fetches_keypair_group_domain_in_priority_order(
    db_with_cleanup: ExtendedAsyncSAEngine,
    dotfile_scope: UserScope,
    test_access_key: AccessKey,
) -> None:
    source = ScheduleDBSource(db_with_cleanup)
    async with db_with_cleanup.begin_readonly_session() as session:
        result = await source._fetch_dotfile_data(session, dotfile_scope, test_access_key)
    # Keypair > group > domain, reversed so higher-priority entries win on apply
    assert result.dotfiles == (_DOMAIN, _PROJECT, _USER)
    assert result.ssh_keypair is not None
    assert result.ssh_keypair.public_key == "public"
    assert result.ssh_keypair.private_key == "private"


async def test_keypair_without_ssh_keys_has_no_keypair(
    db_with_cleanup: ExtendedAsyncSAEngine,
    dotfile_scope: UserScope,
    test_access_key: AccessKey,
) -> None:
    async with db_with_cleanup.begin_session() as session:
        await session.execute(
            sa.update(KeyPairRow)
            .where(KeyPairRow.access_key == test_access_key)
            .values(ssh_public_key=None, ssh_private_key=None)
        )
    source = ScheduleDBSource(db_with_cleanup)
    async with db_with_cleanup.begin_readonly_session() as session:
        result = await source._fetch_dotfile_data(session, dotfile_scope, test_access_key)
    assert result.ssh_keypair is None


async def test_delegated_key_uses_its_own_dotfiles(
    db_with_cleanup: ExtendedAsyncSAEngine,
    dotfile_scope: UserScope,
    test_user_uuid: uuid.UUID,
    test_domain_name: str,
    test_group_id: uuid.UUID,
    test_keypair_resource_policy_name: str,
) -> None:
    delegated = AccessKey(f"AKIA{uuid.uuid4().hex[:16].upper()}")
    delegated_entry = DotfileEntry(path=".gitconfig", perm="644", data="delegated")
    async with db_with_cleanup.begin_session() as session:
        session.add(
            KeyPairRow(
                access_key=delegated,
                secret_key=SecretKey(f"SK{uuid.uuid4().hex}"),
                is_active=True,
                is_admin=False,
                resource_policy=test_keypair_resource_policy_name,
                rate_limit=1000,
                num_queries=0,
                user_id=f"delegated-{uuid.uuid4().hex[:8]}@test.com",
                user=test_user_uuid,
                dotfiles=_pack([delegated_entry]),
            )
        )
    scope = UserScope(
        domain_name=test_domain_name,
        group_id=test_group_id,
        user_uuid=uuid.uuid4(),
        user_role="user",
    )
    source = ScheduleDBSource(db_with_cleanup)
    async with db_with_cleanup.begin_readonly_session() as session:
        result = await source._fetch_dotfile_data(session, scope, delegated)
    assert result.dotfiles == (_DOMAIN, _PROJECT, delegated_entry)


@pytest.mark.parametrize(
    "path", ["/etc/stored", "/home/config/kconfig.dat", "../config/x", "kconfig.dat"]
)
async def test_skips_stored_paths_by_the_path_rule(
    db_with_cleanup: ExtendedAsyncSAEngine,
    dotfile_scope: UserScope,
    test_access_key: AccessKey,
    path: str,
) -> None:
    stored = DotfileEntry(path=path, perm="644", data="stored")
    async with db_with_cleanup.begin_session() as session:
        await session.execute(
            sa.update(KeyPairRow)
            .where(KeyPairRow.access_key == test_access_key)
            .values(dotfiles=_pack([stored, _USER]))
        )
        await session.execute(
            sa.update(DomainRow)
            .where(DomainRow.name == dotfile_scope.domain_name)
            .values(dotfiles=_pack([stored, _DOMAIN]))
        )
    source = ScheduleDBSource(db_with_cleanup)
    async with db_with_cleanup.begin_readonly_session() as session:
        result = await source._fetch_dotfile_data(session, dotfile_scope, test_access_key)
    # Keypair > group > domain, reversed so higher-priority entries win on apply;
    # the stored entry from keypair and domain is dropped, the project entry stays
    assert result.dotfiles == (_DOMAIN, _PROJECT, _USER)
