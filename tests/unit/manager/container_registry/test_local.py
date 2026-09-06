"""Tests for scanning images from the local Docker daemon (``type=local`` registry)."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.manager.container_registry.base import (
    RescanCounts,
    all_updates,
    concurrency_sema,
    progress_reporter,
    rescan_counts,
)
from ai.backend.manager.container_registry.local import LocalRegistry

# A Docker Engine 29 (API 1.55) image-inspect response: `Config` carries no `Image` key,
# and `ContainerConfig` is gone entirely.
DOCKER_29_INSPECT: dict[str, Any] = {
    "Id": "sha256:2140e699b3beaf7f96a0081fd9c9406bc3832b435cdb60dfa2d261f7d2f34a1c",
    "RepoTags": ["ngc-pytorch:26.07-py3"],
    "RepoDigests": [],
    "Architecture": "amd64",
    "Size": 10574521716,
    "Config": {
        "Env": ["CUDA_VERSION=13.3.1.008"],
        "Labels": None,
    },
}

# A pre-29 response, which still carries `Config.Image` and `ContainerConfig`.
DOCKER_LEGACY_INSPECT: dict[str, Any] = {
    **DOCKER_29_INSPECT,
    "Config": {
        **DOCKER_29_INSPECT["Config"],
        "Image": "sha256:abcdef",
    },
    "ContainerConfig": {"Image": "sha256:abcdef"},
}


@pytest.fixture
def scan_context() -> Iterator[None]:
    """Bind the context variables that the scanner writes its results into."""
    tokens = (
        all_updates.set({}),
        rescan_counts.set(RescanCounts()),
        concurrency_sema.set(AsyncMock()),
        progress_reporter.set(None),
    )
    try:
        yield
    finally:
        all_updates.reset(tokens[0])
        rescan_counts.reset(tokens[1])
        concurrency_sema.reset(tokens[2])
        progress_reporter.reset(tokens[3])


@pytest.fixture
def registry() -> LocalRegistry:
    db = MagicMock()

    @asynccontextmanager
    async def _begin_readonly_session() -> AsyncIterator[MagicMock]:
        session = MagicMock()
        session.scalar = AsyncMock(return_value=0)
        yield session

    db.begin_readonly_session = _begin_readonly_session

    registry_info = MagicMock()
    registry_info.url = "http://docker"
    return LocalRegistry(db, "local", registry_info)


def _session_returning(payload: dict[str, Any]) -> MagicMock:
    response = MagicMock()
    response.json = AsyncMock(return_value=payload)

    @asynccontextmanager
    async def _get(_url: Any) -> AsyncIterator[MagicMock]:
        yield response

    session = MagicMock()
    session.get = _get
    return session


class TestScanTagLocal:
    @pytest.mark.parametrize(
        ("label", "inspect_response"),
        [
            ("docker-29", DOCKER_29_INSPECT),
            ("docker-legacy", DOCKER_LEGACY_INSPECT),
        ],
    )
    async def test_scans_image_regardless_of_config_image_presence(
        self,
        registry: LocalRegistry,
        scan_context: None,
        label: str,
        inspect_response: dict[str, Any],
    ) -> None:
        """`Config.Image` is absent on Docker Engine 29; the scan must not depend on it."""
        await registry._scan_tag_local(
            _session_returning(inspect_response), {}, "ngc-pytorch", "26.07-py3"
        )

        updates = all_updates.get()
        assert rescan_counts.get().skipped == 0, label
        assert len(updates) == 1, label
        (key,) = updates
        assert key.canonical == "local/ngc-pytorch:26.07-py3"
        assert key.architecture == "x86_64"

    async def test_vanilla_image_allows_every_accelerator(
        self,
        registry: LocalRegistry,
        scan_context: None,
    ) -> None:
        """An image without Backend.AI labels is registered with an unrestricted accel set."""
        await registry._scan_tag_local(
            _session_returning(DOCKER_29_INSPECT), {}, "ngc-pytorch", "26.07-py3"
        )

        (update,) = all_updates.get().values()
        assert update["accels"] == "*"
        assert update["labels"] == {}
        assert update["size_bytes"] == DOCKER_29_INSPECT["Size"]

    async def test_image_already_known_from_a_remote_registry_is_skipped(
        self,
        registry: LocalRegistry,
        scan_context: None,
    ) -> None:
        """The same config digest coming from a remote registry wins over the local copy."""

        @asynccontextmanager
        async def _begin_readonly_session() -> AsyncIterator[MagicMock]:
            session = MagicMock()
            session.scalar = AsyncMock(return_value=1)
            yield session

        setattr(registry.db, "begin_readonly_session", _begin_readonly_session)

        await registry._scan_tag_local(
            _session_returning(DOCKER_29_INSPECT), {}, "ngc-pytorch", "26.07-py3"
        )

        assert all_updates.get() == {}
        assert rescan_counts.get().skipped == 1
