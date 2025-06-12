from dataclasses import dataclass
from typing import Any

from ai.backend.common.types import ClusterMode
from ai.backend.test.testcases.context import BaseTestContext


class ComputeSessionContext(BaseTestContext[str]):
    pass


@dataclass
class SessionCreationContextArgs:
    image_canonical: str
    image_resources: dict[str, Any]

    # TODO: Remove them
    cluster_mode: ClusterMode
    cluster_size: int


class SessionCreationContext(BaseTestContext[SessionCreationContextArgs]):
    pass
