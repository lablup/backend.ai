"""Tests for the domain and project dotfiles ScheduleDBSource reads into a session's dotfile bundle."""

from __future__ import annotations

import uuid

import pytest
import sqlalchemy as sa

from ai.backend.common.types import AccessKey
from ai.backend.manager.data.dotfile.types import DotfileBundle, DotfileEntries, DotfileEntry
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.v2.reconciler.provider import ReconcileOpsProvider
from ai.backend.manager.repositories.scheduler.db_source.db_source import ScheduleDBSource
from ai.backend.manager.types import UserScope
from ai.backend.testutils.fixtures import DomainFixtureData

_DOMAIN_ENTRY = DotfileEntry(path=".bashrc", perm="644", data="domain")
_KEYPAIR_ENTRY = DotfileEntry(path=".bashrc", perm="600", data="keypair")
_PROJECT_ENTRY = DotfileEntry(path=".bashrc", perm="644", data="project")
_OTHER_KEYPAIR_ENTRY = DotfileEntry(path=".profile", perm="600", data="keypair")


class TestFetchDomainDotfiles:
    @pytest.fixture
    def db_source(self, db_with_cleanup: ExtendedAsyncSAEngine) -> ScheduleDBSource:
        return ScheduleDBSource(db_with_cleanup, ReconcileOpsProvider(db_with_cleanup))

    @pytest.fixture
    async def domain_with_dotfile(
        self, db_with_cleanup: ExtendedAsyncSAEngine, test_domain: DomainFixtureData
    ) -> DomainFixtureData:
        async with db_with_cleanup.begin_session() as db_sess:
            await db_sess.execute(
                sa.update(DomainRow)
                .where(DomainRow.name == test_domain.domain_name)
                .values(dotfiles=DotfileEntries(entries=(_DOMAIN_ENTRY,)).pack())
            )
        return test_domain

    @pytest.fixture
    async def keypair_with_same_path(
        self, db_with_cleanup: ExtendedAsyncSAEngine, test_access_key: AccessKey
    ) -> AccessKey:
        async with db_with_cleanup.begin_session() as db_sess:
            await db_sess.execute(
                sa.update(KeyPairRow)
                .where(KeyPairRow.access_key == test_access_key)
                .values(dotfiles=DotfileEntries(entries=(_KEYPAIR_ENTRY,)).pack())
            )
        return test_access_key

    async def _fetch(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        db_source: ScheduleDBSource,
        domain_name: str,
        access_key: AccessKey,
    ) -> DotfileBundle:
        scope = UserScope(
            domain_name=domain_name,
            group_id=uuid.UUID(int=0),
            user_uuid=uuid.uuid4(),
            user_role="user",
        )
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            return await db_source._fetch_dotfile_data(db_sess, scope, access_key)

    async def test_domain_dotfiles_are_included(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        db_source: ScheduleDBSource,
        domain_with_dotfile: DomainFixtureData,
        test_access_key: AccessKey,
    ) -> None:
        bundle = await self._fetch(
            db_with_cleanup, db_source, domain_with_dotfile.domain_name, test_access_key
        )

        assert bundle.dotfiles == (_DOMAIN_ENTRY,)

    async def test_keypair_dotfile_wins_over_domain_dotfile_on_the_same_path(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        db_source: ScheduleDBSource,
        domain_with_dotfile: DomainFixtureData,
        keypair_with_same_path: AccessKey,
    ) -> None:
        bundle = await self._fetch(
            db_with_cleanup, db_source, domain_with_dotfile.domain_name, keypair_with_same_path
        )

        assert bundle.dotfiles == (_KEYPAIR_ENTRY,)

    async def test_missing_domain_yields_no_domain_dotfiles(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        db_source: ScheduleDBSource,
        keypair_with_same_path: AccessKey,
    ) -> None:
        bundle = await self._fetch(
            db_with_cleanup, db_source, f"missing-{uuid.uuid4().hex[:8]}", keypair_with_same_path
        )

        assert bundle.dotfiles == (_KEYPAIR_ENTRY,)


class TestFetchProjectDotfiles:
    @pytest.fixture
    def db_source(self, db_with_cleanup: ExtendedAsyncSAEngine) -> ScheduleDBSource:
        return ScheduleDBSource(db_with_cleanup, ReconcileOpsProvider(db_with_cleanup))

    @pytest.fixture
    async def project_with_dotfile(
        self, db_with_cleanup: ExtendedAsyncSAEngine, test_group_id: uuid.UUID
    ) -> uuid.UUID:
        async with db_with_cleanup.begin_session() as db_sess:
            await db_sess.execute(
                sa.update(ProjectRow)
                .where(ProjectRow.id == test_group_id)
                .values(dotfiles=DotfileEntries(entries=(_PROJECT_ENTRY,)).pack())
            )
        return test_group_id

    @pytest.fixture
    async def project_without_dotfile(
        self, db_with_cleanup: ExtendedAsyncSAEngine, test_group_id: uuid.UUID
    ) -> uuid.UUID:
        async with db_with_cleanup.begin_session() as db_sess:
            await db_sess.execute(
                sa.update(ProjectRow)
                .where(ProjectRow.id == test_group_id)
                .values(dotfiles=DotfileEntries().pack())
            )
        return test_group_id

    @pytest.fixture
    async def keypair_with_same_path(
        self, db_with_cleanup: ExtendedAsyncSAEngine, test_access_key: AccessKey
    ) -> AccessKey:
        async with db_with_cleanup.begin_session() as db_sess:
            await db_sess.execute(
                sa.update(KeyPairRow)
                .where(KeyPairRow.access_key == test_access_key)
                .values(dotfiles=DotfileEntries(entries=(_KEYPAIR_ENTRY,)).pack())
            )
        return test_access_key

    @pytest.fixture
    async def keypair_with_other_path(
        self, db_with_cleanup: ExtendedAsyncSAEngine, test_access_key: AccessKey
    ) -> AccessKey:
        async with db_with_cleanup.begin_session() as db_sess:
            await db_sess.execute(
                sa.update(KeyPairRow)
                .where(KeyPairRow.access_key == test_access_key)
                .values(dotfiles=DotfileEntries(entries=(_OTHER_KEYPAIR_ENTRY,)).pack())
            )
        return test_access_key

    async def _fetch(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        db_source: ScheduleDBSource,
        domain_name: str,
        group_id: uuid.UUID,
        access_key: AccessKey,
    ) -> DotfileBundle:
        scope = UserScope(
            domain_name=domain_name,
            group_id=group_id,
            user_uuid=uuid.uuid4(),
            user_role="user",
        )
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            return await db_source._fetch_dotfile_data(db_sess, scope, access_key)

    async def test_project_dotfiles_join_the_bundle_before_keypair_dotfiles(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        db_source: ScheduleDBSource,
        test_domain: DomainFixtureData,
        project_with_dotfile: uuid.UUID,
        keypair_with_other_path: AccessKey,
    ) -> None:
        bundle = await self._fetch(
            db_with_cleanup,
            db_source,
            test_domain.domain_name,
            project_with_dotfile,
            keypair_with_other_path,
        )

        assert bundle.dotfiles == (_PROJECT_ENTRY, _OTHER_KEYPAIR_ENTRY)

    async def test_keypair_dotfile_wins_over_project_dotfile_on_the_same_path(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        db_source: ScheduleDBSource,
        test_domain: DomainFixtureData,
        project_with_dotfile: uuid.UUID,
        keypair_with_same_path: AccessKey,
    ) -> None:
        bundle = await self._fetch(
            db_with_cleanup,
            db_source,
            test_domain.domain_name,
            project_with_dotfile,
            keypair_with_same_path,
        )

        assert bundle.dotfiles == (_KEYPAIR_ENTRY,)

    async def test_project_without_dotfiles_adds_nothing(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        db_source: ScheduleDBSource,
        test_domain: DomainFixtureData,
        project_without_dotfile: uuid.UUID,
        keypair_with_same_path: AccessKey,
    ) -> None:
        bundle = await self._fetch(
            db_with_cleanup,
            db_source,
            test_domain.domain_name,
            project_without_dotfile,
            keypair_with_same_path,
        )

        assert bundle.dotfiles == (_KEYPAIR_ENTRY,)

    async def test_missing_project_yields_no_project_dotfiles(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        db_source: ScheduleDBSource,
        test_domain: DomainFixtureData,
        keypair_with_same_path: AccessKey,
    ) -> None:
        bundle = await self._fetch(
            db_with_cleanup,
            db_source,
            test_domain.domain_name,
            uuid.uuid4(),
            keypair_with_same_path,
        )

        assert bundle.dotfiles == (_KEYPAIR_ENTRY,)
