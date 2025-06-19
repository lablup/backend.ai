from typing import override

from ai.backend.test.contexts.context import BaseTestContext, ContextName
from ai.backend.test.data.session import CreatedSessionMeta, SessionDependency
from ai.backend.test.tester.dependency import (
    BatchSessionDep,
    BootstrapScriptDep,
    ClusterDep,
    CodeExecutionDep,
    SessionDep,
    SessionImagifyDep,
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


class BootstrapScriptContext(BaseTestContext[BootstrapScriptDep]):
    @override
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.BOOTSTRAP_SCRIPT


class ClusterContext(BaseTestContext[ClusterDep]):
    @override
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.CLUSTER_CONFIG


class CodeExecutionContext(BaseTestContext[CodeExecutionDep]):
    @override
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.CODE_EXECUTION


class CreatedSessionTemplateIDContext(BaseTestContext[str]):
    @override
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.CREATED_SESSION_TEMPLATE_ID


class CreatedSessionMetaContext(BaseTestContext[CreatedSessionMeta]):
    @override
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.CREATED_SESSION_META


class SessionDependencyContext(BaseTestContext[SessionDependency]):
    @override
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.SESSION_DEPENDENCY


class SessionImagifyContext(BaseTestContext[SessionImagifyDep]):
    @override
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.SESSION_IMAGIFY
