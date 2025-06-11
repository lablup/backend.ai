import shutil
import tempfile
from contextlib import asynccontextmanager as actxmgr
from pathlib import Path
from typing import AsyncIterator, Optional, override

from ai.backend.client.session import AsyncSession
from ai.backend.test.contexts.client_session import AsyncSessionContext
from ai.backend.test.contexts.tester import TestIDContext
from ai.backend.test.templates.template import TestTemplate, WrapperTestTemplate


class LoginTemplate(WrapperTestTemplate):
    def __init__(
        self, template: TestTemplate, user_id: str, password: str, otp: Optional[str] = None
    ) -> None:
        super().__init__(template)
        self.user_id = user_id
        self.password = password
        self.otp = otp

    @property
    def name(self) -> str:
        return "login"

    @override
    @actxmgr
    async def context(self) -> AsyncIterator[None]:
        test_id = TestIDContext.get_current()
        test_id_str = str(test_id)
        client_session = AsyncSessionContext.get_current()
        endpoint = EndpointContext.get_current()
        api_config = APIConfig(
            endpoint=endpoint.endpoint,
            endpoint_type=endpoint.endpoint_type,
        )

        await _login(
            session=client_session,
            test_id=test_id_str,
            user_id=self.user_id,
            password=self.password,
            otp=self.otp,
        )
        try:
            yield
        finally:
            await _logout(session=client_session, test_id=test_id_str)


def _get_test_temp_dir(test_id: str) -> Path:
    temp_base = Path(tempfile.gettempdir()) / "backend_ai_tests"
    temp_dir = temp_base / test_id
    return temp_dir


async def _login(
    session: AsyncSession,
    test_id: str,
    user_id: str,
    password: str,
    otp: Optional[str] = None,
) -> None:
    temp_dir = _get_test_temp_dir(test_id)
    temp_dir.mkdir(parents=True, exist_ok=True)

    cookie_file = temp_dir / "cookie.dat"
    if cookie_file.exists():
        try:
            session.aiohttp_session.cookie_jar.load(cookie_file)  # type: ignore
            return
        except Exception:
            pass

    result = await session.Auth.login(user_id=user_id, password=password, otp=otp)
    if not result["authenticated"]:
        raise ValueError("Login failed: " + result.get("data", {}).get("details", "Unknown error"))

    session.aiohttp_session.cookie_jar.update_cookies(result["cookies"])
    session.aiohttp_session.cookie_jar.save(cookie_file)  # type: ignore


async def _logout(session: AsyncSession, test_id: str) -> None:
    try:
        await session.Auth.logout()
    except Exception as e:
        print(f"Failed to logout: {e}")

    temp_dir = _get_test_temp_dir(test_id)
    if temp_dir.exists():
        try:
            shutil.rmtree(temp_dir)
        except Exception as e:
            print(f"Failed to clean up temp directory: {e}")
