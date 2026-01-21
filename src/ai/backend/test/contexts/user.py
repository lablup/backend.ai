from typing import override

from ai.backend.test.contexts.context import BaseTestContext, ContextName
from ai.backend.test.data.user import CreatedUserMeta


class CreatedUserContext(BaseTestContext[CreatedUserMeta]):
    @override
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.CREATED_USER_CONTEXT
