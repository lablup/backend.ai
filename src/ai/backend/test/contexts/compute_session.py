from typing import Any, Optional, override
from uuid import UUID

from pydantic.dataclasses import dataclass

from ai.backend.common.types import ClusterMode
from ai.backend.test.contexts.context import BaseTestContext, ContextName


@dataclass
class ClusterConfigArgs:
    cluster_mode: ClusterMode
    cluster_size: int


class ClusterConfigContext(BaseTestContext[ClusterConfigArgs]):
    @override
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.CLUSTER_CONFIGS


@dataclass
class SessionCreationContextArgs:
    image: str
    architecture: str
    resources: dict[str, Any]
    startup_command: Optional[str]
    timeout: float
    cluster_mode: Optional[ClusterMode]  # Optional for manual injection
    cluster_size: Optional[int]  # Optional for manual injection


class SessionCreationContext(BaseTestContext[SessionCreationContextArgs]):
    @override
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.SESSION_CREATION


@dataclass
class SessionTemplateContextArgs:
    content: str
    template_id: Optional[UUID]


class SessionTemplateContext(BaseTestContext[SessionTemplateContextArgs]):
    @override
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.SESSION_TEMPLATE


class CreatedSessionTemplateIDContext(BaseTestContext[UUID]):
    @override
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.CREATED_SESSION_TEMPLATE_ID


class CreatedSessionIDContext(BaseTestContext[UUID]):
    @override
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.CREATED_SESSION_ID
