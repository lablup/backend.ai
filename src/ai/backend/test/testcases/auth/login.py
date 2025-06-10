from contextlib import asynccontextmanager as actxmgr
from typing import AsyncIterator, Optional, override

from ai.backend.client.session import AsyncSession
from ai.backend.test.testcases.context import BaseTestContext
from ai.backend.test.testcases.root import TestRunContext
from ai.backend.test.testcases.template import TestTemplate, WrapperTestTemplate
from ai.backend.test.testcases.utils import login, logout


class AuthenticationContext(BaseTestContext[AsyncSession]):
    pass


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
        test_id = TestRunContext.get_test_id()
        async with AsyncSession() as session:
            await login(
                session=session,
                test_id=test_id,
                user_id=self.user_id,
                password=self.password,
                otp=self.otp,
            )

            async with AuthenticationContext.with_current(session):
                try:
                    yield
                finally:
                    await logout(session=session, test_id=test_id)
