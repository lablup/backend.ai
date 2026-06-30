from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager
from types import SimpleNamespace
from typing import Any, cast
from uuid import uuid4

import aiohttp
import pytest
from sqlalchemy.exc import DBAPIError

from ai.backend.manager.container_registry import base as registry_base
from ai.backend.manager.container_registry.base import BaseContainerRegistry, all_updates
from ai.backend.manager.data.image.types import ImageData, ImageIdentifier, ImageStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


class _SqlStateError(Exception):
    sqlstate: str

    def __init__(self, sqlstate: str) -> None:
        self.sqlstate = sqlstate


class _FakeImageRow:
    image_ref: SimpleNamespace
    status: ImageStatus
    config_digest: str | None
    size_bytes: int | None
    accelerators: str | None
    labels: dict[str, str]
    is_local: bool
    _image_data: ImageData

    def __init__(self, canonical: str, architecture: str, image_data: ImageData) -> None:
        self.image_ref = SimpleNamespace(canonical=canonical, architecture=architecture)
        self.status = ImageStatus.ALIVE
        self.config_digest = None
        self.size_bytes = None
        self.accelerators = None
        self.labels = {}
        self.is_local = False
        self._image_data = image_data

    def to_dataclass(self) -> ImageData:
        return self._image_data


class _FakeSession:
    _db: _FakeDB

    def __init__(self, db: _FakeDB) -> None:
        self._db = db

    async def scalars(self, _stmt: Any) -> list[_FakeImageRow]:
        return [self._db.image_row]

    async def flush(self) -> None:
        self._db.flush_count += 1
        if self._db.flush_count == 1:
            raise DBAPIError(None, None, _SqlStateError("40001"))


class _FakeDB:
    image_row: _FakeImageRow
    begin_count: int
    flush_count: int

    def __init__(self, image_row: _FakeImageRow) -> None:
        self.image_row = image_row
        self.begin_count = 0
        self.flush_count = 0

    @asynccontextmanager
    async def begin_session(self) -> AsyncIterator[_FakeSession]:
        self.begin_count += 1
        yield _FakeSession(self)


class _TestRegistry(BaseContainerRegistry):
    async def fetch_repositories(
        self,
        _sess: aiohttp.ClientSession,
    ) -> AsyncIterator[str]:
        repositories: tuple[str, ...] = ()
        for repository in repositories:
            yield repository


class TestCommitRescanResult:
    @pytest.fixture
    def canonical(self) -> str:
        return "test-registry/test-project/python:3.12"

    @pytest.fixture
    def architecture(self) -> str:
        return "x86_64"

    @pytest.fixture
    def image_data(self) -> ImageData:
        return cast(ImageData, object())

    @pytest.fixture
    def image_row(
        self,
        canonical: str,
        architecture: str,
        image_data: ImageData,
    ) -> _FakeImageRow:
        return _FakeImageRow(canonical, architecture, image_data)

    @pytest.fixture
    def db(self, image_row: _FakeImageRow) -> _FakeDB:
        return _FakeDB(image_row)

    @pytest.fixture
    def registry_info(self) -> SimpleNamespace:
        return SimpleNamespace(
            url="https://registry.example.com",
            ssl_verify=True,
            username=None,
            password=None,
            project="test-project",
            registry_name="test-registry",
            id=uuid4(),
        )

    @pytest.fixture
    def registry(
        self,
        db: _FakeDB,
        registry_info: SimpleNamespace,
    ) -> _TestRegistry:
        return _TestRegistry(
            cast(ExtendedAsyncSAEngine, db),
            "test-registry",
            cast(Any, registry_info),
        )

    @pytest.fixture
    def update_key(self, canonical: str, architecture: str) -> ImageIdentifier:
        return ImageIdentifier(canonical, architecture)

    @pytest.fixture
    def updates(self, update_key: ImageIdentifier) -> dict[ImageIdentifier, dict[str, Any]]:
        return {
            update_key: {
                "config_digest": "sha256:updated",
                "size_bytes": 1024,
                "labels": {},
            },
        }

    @pytest.fixture
    def active_updates(
        self,
        updates: dict[ImageIdentifier, dict[str, Any]],
    ) -> Iterator[dict[ImageIdentifier, dict[str, Any]]]:
        token = all_updates.set(updates)
        try:
            yield updates
        finally:
            all_updates.reset(token)

    @pytest.fixture
    def no_rbac_creators(self, monkeypatch: pytest.MonkeyPatch) -> None:
        async def fake_execute_rbac_entity_creators(
            _session: _FakeSession,
            creators: list[Any],
        ) -> SimpleNamespace:
            assert creators == []
            return SimpleNamespace(rows=[])

        monkeypatch.setattr(
            registry_base,
            "execute_rbac_entity_creators",
            fake_execute_rbac_entity_creators,
        )

    async def test_retries_serialization_failure_without_losing_updates(
        self,
        registry: _TestRegistry,
        db: _FakeDB,
        image_row: _FakeImageRow,
        image_data: ImageData,
        update_key: ImageIdentifier,
        active_updates: dict[ImageIdentifier, dict[str, Any]],
        no_rbac_creators: None,
    ) -> None:
        result = await registry.commit_rescan_result()
        assert update_key in all_updates.get()

        assert active_updates[update_key]["config_digest"] == "sha256:updated"
        assert result == [image_data]
        assert db.begin_count == 2
        assert db.flush_count == 2
        assert image_row.config_digest == "sha256:updated"
        assert image_row.size_bytes == 1024
