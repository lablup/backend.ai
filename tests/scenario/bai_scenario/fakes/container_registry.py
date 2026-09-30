"""Stand-in for the registry a rescan reads a tag from.

The scanner picks its client from the registry row and reaches the registry over HTTP,
so nothing can be handed in. This answers those requests with the tag it was built from.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass

from aioresponses import aioresponses

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


@contextmanager
def serving(registry: ContainerRegistryData, served: ServedTag) -> Iterator[None]:
    """Answer the registry's requests with ``served``; any other tag is a 404."""
    base = f"{registry.url}/v2"
    repository = f"{base}/{served.repository}"
    with aioresponses() as mocked:
        mocked.get(f"{base}/", status=200, repeat=True)
        mocked.get(
            f"{repository}/manifests/{served.tag}",
            payload={
                "manifests": [
                    {
                        "digest": f"sha256:{arch}",
                        "platform": {"os": "linux", "architecture": arch},
                    }
                    for arch in served.architectures
                ]
            },
            headers={"Content-Type": BaseContainerRegistry.MEDIA_TYPE_DOCKER_MANIFEST_LIST},
            repeat=True,
        )
        for arch in served.architectures:
            mocked.get(
                f"{repository}/manifests/sha256:{arch}",
                payload={
                    "config": {"digest": f"sha256:config-{arch}", "size": CONFIG_SIZE},
                    "layers": [],
                },
                repeat=True,
            )
            mocked.get(
                f"{repository}/blobs/sha256:config-{arch}",
                payload={"architecture": arch, "config": {"Labels": {}}},
                repeat=True,
            )
        mocked.get(re.compile(rf"^{re.escape(repository)}/manifests/.*$"), status=404, repeat=True)
        yield
