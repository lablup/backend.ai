from typing import override
from uuid import UUID

from ai.backend.test.contexts.context import BaseTestContext, ContextName
from ai.backend.test.tester.config import (
    BatchSessionConfig,
    ClusterConfig,
    SessionConfig,
)


class SessionConfigContext(BaseTestContext[SessionConfig]):
    @override
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.SESSION


class BatchSessionConfigContext(BaseTestContext[BatchSessionConfig]):
    @override
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.BATCH_SESSION


class ClusterConfigContext(BaseTestContext[ClusterConfig]):
    @override
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.CLUSTER_CONFIG


# TODO: Move these contexts to the other file
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
