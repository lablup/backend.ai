from contextlib import asynccontextmanager as actxmgr
from contextvars import ContextVar
from typing import AsyncIterator, Optional, override

from ai.backend.client.session import AsyncSession
from ai.backend.test.testcases.context import BaseTestContext
from ai.backend.test.testcases.root import test_run_context
from ai.backend.test.testcases.template import TestTemplate, WrapperTestTemplate
from ai.backend.test.testcases.utils import login, logout


class AuthenticationContext(BaseTestContext):
    _ctxvar: ContextVar[Optional[str]]

    def __init__(self) -> None:
        self._ctxvar = ContextVar("auth_context", default=None)

    def get_current(self) -> AsyncSession:
        return super().get_current()


authentication_context = AuthenticationContext()


class AuthenticationWrapperTemplate(WrapperTestTemplate):
    def __init__(
        self, template: TestTemplate, user_id: str, password: str, otp: Optional[str] = None
    ) -> None:
        super().__init__(template)
        self.user_id = user_id
        self.password = password
        self.otp = otp

    @property
    def name(self) -> str:
        return "auth-test"

    @override
    @actxmgr
    async def context(self) -> AsyncIterator[None]:
        test_id = test_run_context.get_test_id()
        async with AsyncSession() as session:
            await login(
                session=session,
                test_id=test_id,
                user_id=self.user_id,
                password=self.password,
                otp=self.otp,
            )

            async with authentication_context.with_current(session):
                try:
                    yield
                finally:
                    await logout(session=session, test_id=test_id)
