from typing import override
from uuid import UUID

from ai.backend.test.contexts.context import BaseTestContext, ContextName
from ai.backend.test.tester.config import (
    BatchSessionConfig,
    ClusterConfig,
    SessionConfig,
)


class SessionContext(BaseTestContext[SessionConfig]):
    @override
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.SESSION


class BatchSessionContext(BaseTestContext[BatchSessionConfig]):
    @override
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.BATCH_SESSION


class ClusterContext(BaseTestContext[ClusterConfig]):
    @override
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.CLUSTER_CONFIG


class CreatedSessionTemplateIDContext(BaseTestContext[str]):
    @override
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.CREATED_SESSION_TEMPLATE_ID


class CreatedSessionIDContext(BaseTestContext[UUID]):
    @override
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.CREATED_SESSION_ID
