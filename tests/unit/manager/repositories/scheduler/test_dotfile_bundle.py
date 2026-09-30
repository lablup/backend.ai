"""Tests for the project dotfile merge in ``ScheduleDBSource._fetch_dotfile_data``.

The project dotfiles used to be read through ``query_group_dotfiles`` in
``models/project/row.py``; the query now lives in the caller. These tests pin the
merge behaviour the method keeps: project entries join the bundle, a keypair entry
shadows the project entry on the same path, and the final order is reversed so the
higher-priority entry overwrites when the agent applies them in list order.
"""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import sqlalchemy as sa

from ai.backend.common.types import AccessKey
from ai.backend.manager.data.dotfile.types import DotfileEntries, DotfileEntry
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.scheduler.db_source.db_source import ScheduleDBSource
from ai.backend.manager.types import UserScope
from ai.backend.testutils.fixtures import DomainFixtureData


def _pack(*entries: DotfileEntry) -> bytes:
    return DotfileEntries(entries=entries).pack()


async def _set_dotfiles(
    db: ExtendedAsyncSAEngine,
    *,
    access_key: AccessKey,
    keypair_dotfiles: bytes,
    group_id: uuid.UUID,
    group_dotfiles: bytes,
) -> None:
    async with db.begin_session() as db_sess:
        await db_sess.execute(
            sa.update(KeyPairRow)
            .where(KeyPairRow.access_key == access_key)
            .values(dotfiles=keypair_dotfiles)
        )
        await db_sess.execute(
            sa.update(ProjectRow).where(ProjectRow.id == group_id).values(dotfiles=group_dotfiles)
        )


async def _fetch_bundle_paths(
    db: ExtendedAsyncSAEngine,
    *,
    domain_name: str,
    group_id: uuid.UUID,
    user_uuid: uuid.UUID,
    access_key: AccessKey,
) -> list[DotfileEntry]:
    db_source = ScheduleDBSource(db, MagicMock())
    user_scope = UserScope(
        domain_name=domain_name,
        group_id=group_id,
        user_uuid=user_uuid,
        user_role="user",
    )
    async with db.begin_readonly_session() as db_sess:
        bundle = await db_source._fetch_dotfile_data(db_sess, user_scope, access_key)
    return list(bundle.dotfiles)


async def test_project_dotfiles_join_the_bundle(
    db_with_cleanup: ExtendedAsyncSAEngine,
    test_domain: DomainFixtureData,
    test_group_id: uuid.UUID,
    test_user_uuid: uuid.UUID,
    test_access_key: AccessKey,
) -> None:
    keypair_entry = DotfileEntry(path=".keypairrc", perm="644", data="keypair")
    group_entry = DotfileEntry(path=".grouprc", perm="600", data="group")
    await _set_dotfiles(
        db_with_cleanup,
        access_key=test_access_key,
        keypair_dotfiles=_pack(keypair_entry),
        group_id=test_group_id,
        group_dotfiles=_pack(group_entry),
    )

    entries = await _fetch_bundle_paths(
        db_with_cleanup,
        domain_name=test_domain.domain_name,
        group_id=test_group_id,
        user_uuid=test_user_uuid,
        access_key=test_access_key,
    )

    # Reversed order: the keypair entry is applied last and so wins.
    assert entries == [group_entry, keypair_entry]


async def test_keypair_dotfile_shadows_the_project_path(
    db_with_cleanup: ExtendedAsyncSAEngine,
    test_domain: DomainFixtureData,
    test_group_id: uuid.UUID,
    test_user_uuid: uuid.UUID,
    test_access_key: AccessKey,
) -> None:
    keypair_entry = DotfileEntry(path=".shared", perm="644", data="from-keypair")
    group_entry = DotfileEntry(path=".shared", perm="600", data="from-group")
    await _set_dotfiles(
        db_with_cleanup,
        access_key=test_access_key,
        keypair_dotfiles=_pack(keypair_entry),
        group_id=test_group_id,
        group_dotfiles=_pack(group_entry),
    )

    entries = await _fetch_bundle_paths(
        db_with_cleanup,
        domain_name=test_domain.domain_name,
        group_id=test_group_id,
        user_uuid=test_user_uuid,
        access_key=test_access_key,
    )

    assert entries == [keypair_entry]


async def test_empty_project_dotfiles_add_nothing(
    db_with_cleanup: ExtendedAsyncSAEngine,
    test_domain: DomainFixtureData,
    test_group_id: uuid.UUID,
    test_user_uuid: uuid.UUID,
    test_access_key: AccessKey,
) -> None:
    keypair_entry = DotfileEntry(path=".keypairrc", perm="644", data="keypair")
    await _set_dotfiles(
        db_with_cleanup,
        access_key=test_access_key,
        keypair_dotfiles=_pack(keypair_entry),
        group_id=test_group_id,
        group_dotfiles=_pack(),
    )

    entries = await _fetch_bundle_paths(
        db_with_cleanup,
        domain_name=test_domain.domain_name,
        group_id=test_group_id,
        user_uuid=test_user_uuid,
        access_key=test_access_key,
    )

    assert entries == [keypair_entry]
