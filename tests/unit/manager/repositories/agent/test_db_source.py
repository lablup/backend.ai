from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.types import ImageCanonical, ImageID
from ai.backend.manager.data.image.types import ImageIdentifier, ImageType
from ai.backend.manager.models.container_registry.row import ContainerRegistryRow
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.image.row import ImageAliasRow, ImageRow
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.resource_policy.row import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.agent.db_source.db_source import AgentDBSource
from ai.backend.manager.repositories.ops.v2.share.provider import ShareOpsProvider
from ai.backend.testutils.db import with_tables

_PYTHON = "cr.backend.ai/stable/python:3.11"
_PYTORCH = "cr.backend.ai/stable/pytorch:2.0"


class TestImageIdLookups:
    @pytest.fixture
    async def db_with_tables(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                DomainRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRow,
                KeyPairRow,
                ProjectRow,
                ContainerRegistryRow,
                ImageRow,
                ImageAliasRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def images(self, db_with_tables: ExtendedAsyncSAEngine) -> dict[str, ImageID]:
        """Three images keyed by "<canonical>@<architecture>": python on two architectures and pytorch."""
        registry_id = uuid.uuid4()
        specs = [
            (_PYTHON, "x86_64", "sha256:python-x86"),
            (_PYTHON, "aarch64", "sha256:python-arm"),
            (_PYTORCH, "x86_64", "sha256:pytorch-x86"),
        ]
        async with db_with_tables.begin_session() as db_session:
            db_session.add(
                ContainerRegistryRow(
                    id=ContainerRegistryID(registry_id),
                    url="https://cr.backend.ai",
                    registry_name="cr.backend.ai",
                    type=ContainerRegistryType.HARBOR2,
                    project="stable",
                    username="test",
                    password="test",
                )
            )
            await db_session.flush()
            rows = [
                ImageRow(
                    name=canonical,
                    project="stable",
                    registry="cr.backend.ai",
                    registry_id=registry_id,
                    image=canonical.split("/")[-1].split(":")[0],
                    tag=canonical.split(":")[-1],
                    architecture=architecture,
                    config_digest=digest,
                    size_bytes=1000,
                    type=ImageType.COMPUTE,
                    accelerators=None,
                    resources={},
                    labels={},
                )
                for canonical, architecture, digest in specs
            ]
            db_session.add_all(rows)
            await db_session.flush()
            return {f"{row.name}@{row.architecture}": ImageID(row.id) for row in rows}

    @pytest.fixture
    def db_source(self, db_with_tables: ExtendedAsyncSAEngine) -> AgentDBSource:
        return AgentDBSource(db_with_tables, ShareOpsProvider(db_with_tables))

    async def test_identifiers_match_on_canonical_and_architecture(
        self, db_source: AgentDBSource, images: dict[str, ImageID]
    ) -> None:
        image_ids = await db_source.image_ids_by_identifiers([
            ImageIdentifier(canonical=ImageCanonical(_PYTHON), architecture="x86_64"),
            ImageIdentifier(canonical=ImageCanonical(_PYTORCH), architecture="x86_64"),
        ])

        assert set(image_ids) == {images[f"{_PYTHON}@x86_64"], images[f"{_PYTORCH}@x86_64"]}

    async def test_identifiers_skip_other_architecture(
        self, db_source: AgentDBSource, images: dict[str, ImageID]
    ) -> None:
        image_ids = await db_source.image_ids_by_identifiers([
            ImageIdentifier(canonical=ImageCanonical(_PYTHON), architecture="aarch64"),
        ])

        assert image_ids == [images[f"{_PYTHON}@aarch64"]]

    async def test_identifiers_unknown_returns_empty(
        self, db_source: AgentDBSource, images: dict[str, ImageID]
    ) -> None:
        image_ids = await db_source.image_ids_by_identifiers([
            ImageIdentifier(canonical=ImageCanonical(_PYTORCH), architecture="aarch64"),
        ])

        assert image_ids == []

    async def test_digest_matches_config_digest(
        self, db_source: AgentDBSource, images: dict[str, ImageID]
    ) -> None:
        image_ids = await db_source.image_ids_by_digest(["sha256:python-arm", "sha256:pytorch-x86"])

        assert set(image_ids) == {images[f"{_PYTHON}@aarch64"], images[f"{_PYTORCH}@x86_64"]}

    async def test_digest_unknown_returns_empty(
        self, db_source: AgentDBSource, images: dict[str, ImageID]
    ) -> None:
        image_ids = await db_source.image_ids_by_digest(["sha256:unknown"])

        assert image_ids == []
