"""Tests for removing an image from a Harbor v2 registry."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
import yarl

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.docker import ImageRef
from ai.backend.manager.container_registry.harbor import HarborRegistry_v2
from ai.backend.manager.models.container_registry.row import ContainerRegistryRow


@dataclass(frozen=True)
class _NestedRepositoryUntag:
    registry: HarborRegistry_v2
    image: ImageRef
    client_session: MagicMock


class TestHarborRegistryV2Untag:
    @pytest.fixture
    def nested_repository_untag(self) -> _NestedRepositoryUntag:
        delete_response = MagicMock(status=200)
        client_session = MagicMock()
        client_session.delete.return_value.__aenter__.return_value = delete_response
        return _NestedRepositoryUntag(
            registry=HarborRegistry_v2(
                MagicMock(),
                "harbor.example.com",
                ContainerRegistryRow(
                    id=ContainerRegistryID(uuid4()),
                    url="https://harbor.example.com",
                    registry_name="harbor.example.com",
                    type=ContainerRegistryType.HARBOR2,
                    project="stable",
                ),
            ),
            image=ImageRef(
                name="ngc/pytorch",
                project="stable",
                tag="24.07-py3",
                registry="harbor.example.com",
                architecture="x86_64",
                is_local=False,
            ),
            client_session=client_session,
        )

    async def test_a_nested_repository_is_addressed_as_one_path_segment(
        self, nested_repository_untag: _NestedRepositoryUntag
    ) -> None:
        @asynccontextmanager
        async def mocked_client_session() -> AsyncIterator[tuple[yarl.URL, MagicMock]]:
            yield (
                nested_repository_untag.registry.registry_url,
                nested_repository_untag.client_session,
            )

        with patch.object(
            nested_repository_untag.registry, "prepare_client_session", mocked_client_session
        ):
            await nested_repository_untag.registry.untag(nested_repository_untag.image)

        (artifact_url,) = nested_repository_untag.client_session.delete.call_args.args
        assert artifact_url.raw_path == (
            "/api/v2.0/projects/stable/repositories/ngc%252Fpytorch/artifacts/24.07-py3"
        )
