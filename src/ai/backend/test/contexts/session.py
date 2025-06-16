from typing import override
from uuid import UUID

from ai.backend.test.contexts.context import BaseTestContext, ContextName
from ai.backend.test.tester.config import (
    BatchSessionDep,
    ClusterDep,
    SessionDep,
)


class SessionContext(BaseTestContext[SessionDep]):
    @override
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.SESSION


class BatchSessionContext(BaseTestContext[BatchSessionDep]):
    @override
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.BATCH_SESSION


class ClusterContext(BaseTestContext[ClusterDep]):
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
