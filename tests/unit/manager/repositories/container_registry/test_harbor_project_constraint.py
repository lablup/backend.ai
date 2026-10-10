"""Tests for the check constraint that requires a project name on Harbor registries.

The rule used to live in Python on the way in, so only the paths that ran the validator
answered to it. It is a column constraint now: these tests write rows straight through a
session, which is the path that bypassed the validator before.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.manager.models.container_registry.row import ContainerRegistryRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.db import with_tables


class TestHarborProjectConstraint:
    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(database_connection, [ContainerRegistryRow]):
            yield database_connection

    def _row(
        self,
        *,
        registry_type: ContainerRegistryType,
        project: str | None,
    ) -> ContainerRegistryRow:
        name = f"reg-{uuid.uuid4().hex[:8]}.example.com"
        return ContainerRegistryRow(
            id=ContainerRegistryID(uuid.uuid4()),
            url=f"https://{name}",
            registry_name=name,
            type=registry_type,
            project=project,
        )

    @pytest.mark.parametrize(
        "registry_type",
        [ContainerRegistryType.HARBOR, ContainerRegistryType.HARBOR2],
    )
    @pytest.mark.parametrize("project", ["library", "team_a", "img.v2", "a-b.c_d"])
    async def test_harbor_takes_a_well_formed_project_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        registry_type: ContainerRegistryType,
        project: str,
    ) -> None:
        """Lowercase segments joined by one separator are accepted."""
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(self._row(registry_type=registry_type, project=project))

    @pytest.mark.parametrize(
        "registry_type",
        [ContainerRegistryType.HARBOR, ContainerRegistryType.HARBOR2],
    )
    async def test_harbor_without_a_project_is_refused(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        registry_type: ContainerRegistryType,
    ) -> None:
        """A Harbor registry addresses images through a project, so the column cannot be empty."""
        with pytest.raises(IntegrityError):
            async with db_with_cleanup.begin_session() as db_sess:
                db_sess.add(self._row(registry_type=registry_type, project=None))

    @pytest.mark.parametrize("project", ["", "Upper", "-lead", "trail-", "two__seps", "has space"])
    async def test_harbor_with_a_malformed_project_is_refused(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        project: str,
    ) -> None:
        """An empty name, an uppercase letter or a stray separator is refused."""
        with pytest.raises(IntegrityError):
            async with db_with_cleanup.begin_session() as db_sess:
                db_sess.add(self._row(registry_type=ContainerRegistryType.HARBOR2, project=project))

    @pytest.mark.parametrize("project", [None, "Anything Goes"])
    async def test_other_types_ignore_the_project(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        project: str | None,
    ) -> None:
        """Only Harbor addresses images through a project; the rest take any value."""
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(self._row(registry_type=ContainerRegistryType.DOCKER, project=project))

    async def test_turning_a_docker_registry_into_harbor_without_a_project_is_refused(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> None:
        """The constraint reads the row after the update, which an input check cannot."""
        row = self._row(registry_type=ContainerRegistryType.DOCKER, project=None)
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(row)

        with pytest.raises(IntegrityError):
            async with db_with_cleanup.begin_session() as db_sess:
                await db_sess.execute(
                    sa.update(ContainerRegistryRow)
                    .where(ContainerRegistryRow.id == row.id)
                    .values(type=ContainerRegistryType.HARBOR2)
                )

    async def test_clearing_the_project_of_a_harbor_registry_is_refused(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> None:
        """Same the other way around: the update names no type, only the project."""
        row = self._row(registry_type=ContainerRegistryType.HARBOR2, project="library")
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(row)

        with pytest.raises(IntegrityError):
            async with db_with_cleanup.begin_session() as db_sess:
                await db_sess.execute(
                    sa.update(ContainerRegistryRow)
                    .where(ContainerRegistryRow.id == row.id)
                    .values(project=None)
                )
