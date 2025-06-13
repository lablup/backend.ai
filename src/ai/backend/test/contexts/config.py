from typing import override
from uuid import UUID

from ai.backend.test.contexts.context import BaseTestContext, ContextName
from ai.backend.test.tester.config import (
    BatchSessionConfig,
    ClusterConfig,
    EndpointConfig,
    ImageConfig,
    KeyPairConfig,
    LoginCredentialConfig,
    SessionConfig,
    SessionTemplateConfig,
    SSEConfig,
)


class KeypairConfigContext(BaseTestContext[KeyPairConfig]):
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.KEYPAIR


class LoginCredentialConfigContext(BaseTestContext[LoginCredentialConfig]):
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.LOGIN_CREDENTIAL


class EndpointConfigContext(BaseTestContext[EndpointConfig]):
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.ENDPOINT


class SessionConfigContext(BaseTestContext[SessionConfig]):
    @override
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.SESSION


class SSEConfigContext(BaseTestContext[SSEConfig]):
    @override
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.SSE


class ImageConfigContext(BaseTestContext[ImageConfig]):
    @override
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.IMAGE


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


class SessionTemplateConfigContext(BaseTestContext[SessionTemplateConfig]):
    @override
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.SESSION_TEMPLATE


# TODO: Move these contexts to the other file
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
