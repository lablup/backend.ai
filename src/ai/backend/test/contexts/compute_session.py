from dataclasses import dataclass
from typing import Any, Optional
from uuid import UUID

from ai.backend.common.types import ClusterMode
from ai.backend.test.testcases.context import BaseTestContext


@dataclass
class SessionCreationFromImageContextArgs:
    canonical: str
    resources: dict[str, Any]


@dataclass
class SessionCreationFromTemplateContextArgs:
    content: str
    template_id: UUID


@dataclass
class SessionCreationContextArgs:
    image: Optional[SessionCreationFromImageContextArgs]
    template: Optional[SessionCreationFromTemplateContextArgs]

    # TODO: Remove them
    cluster_mode: ClusterMode
    cluster_size: int


class SessionCreationContext(BaseTestContext[SessionCreationContextArgs]):
    pass


class CreatedSessionIDContext(BaseTestContext[UUID]):
    pass


# TODO: Inject and use this
class BatchSessionCommandContext(BaseTestContext[str]):
    pass
