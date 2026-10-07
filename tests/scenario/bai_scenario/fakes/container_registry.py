"""Stand-in for the registry a scan reads a tag from.

The scanner picks its client from the registry row and opens its own HTTP session, so
nothing can be handed in. This swaps that session for one answering with the tag it was built from.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator, Mapping
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, field
from typing import Any, Self
from unittest.mock import patch

import aiohttp
import yarl

from ai.backend.common.json import dump_json_str
from ai.backend.manager.container_registry.base import BaseContainerRegistry
from ai.backend.manager.data.container_registry.types import ContainerRegistryData

CONFIG_SIZE = 10
"""레지스트리가 알려 주는 이미지 설정의 크기. 레이어가 없으므로 이미지 크기가 곧 이 값이다."""


@dataclass(frozen=True)
class ServedTag:
    """레지스트리가 내놓는 태그 하나와 그 태그에 담긴 아키텍처들."""

    repository: str
    tag: str
    architectures: tuple[str, ...]


@dataclass(frozen=True)
class _Reply:
    status: int = 200
    payload: Any = None
    headers: Mapping[str, str] = field(default_factory=dict)

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_: object) -> None:
        return None

    async def read(self) -> bytes:
        return dump_json_str(self.payload).encode()

    async def json(self) -> Any:
        return self.payload

    def raise_for_status(self) -> None:
        if self.status >= 400:
            raise aiohttp.ClientError(f"HTTP {self.status}")


class _RegistrySession:
    """Answers GETs by path; any other path is a 404."""

    _replies: dict[str, _Reply]

    def __init__(self, replies: dict[str, _Reply]) -> None:
        self._replies = replies

    def get(self, url: yarl.URL | str, **_: Any) -> _Reply:
        return self._replies.get(yarl.URL(url).path, _Reply(status=404))


def _replies_for(served: ServedTag) -> dict[str, _Reply]:
    repository = f"/v2/{served.repository}"
    replies = {
        "/v2/": _Reply(),
        f"{repository}/manifests/{served.tag}": _Reply(
            payload={
                "manifests": [
                    {"digest": f"sha256:{arch}", "platform": {"os": "linux", "architecture": arch}}
                    for arch in served.architectures
                ]
            },
            headers={"Content-Type": BaseContainerRegistry.MEDIA_TYPE_DOCKER_MANIFEST_LIST},
        ),
    }
    for arch in served.architectures:
        replies[f"{repository}/manifests/sha256:{arch}"] = _Reply(
            payload={
                "config": {"digest": f"sha256:config-{arch}", "size": CONFIG_SIZE},
                "layers": [],
            }
        )
        replies[f"{repository}/blobs/sha256:config-{arch}"] = _Reply(
            payload={"architecture": arch, "config": {"Labels": {}}}
        )
    return replies


@contextmanager
def serving(registry: ContainerRegistryData, served: ServedTag) -> Iterator[None]:
    """Answer the registry's requests with ``served``; any other tag is a 404."""
    session = _RegistrySession(_replies_for(served))

    @asynccontextmanager
    async def prepare_client_session(
        _registry: BaseContainerRegistry,
    ) -> AsyncIterator[tuple[yarl.URL, _RegistrySession]]:
        yield yarl.URL(registry.url), session

    with patch.object(BaseContainerRegistry, "prepare_client_session", prepare_client_session):
        yield
