import shutil
import tempfile
from contextlib import asynccontextmanager as actxmgr
from pathlib import Path
from typing import AsyncIterator, Optional, override

from ai.backend.client.config import APIConfig
from ai.backend.client.session import AsyncSession
from ai.backend.test.contexts.auth import EndpointContext, LoginCredentialContext
from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.tester import TestSpecMetaContext
from ai.backend.test.templates.template import (
    WrapperTestTemplate,
)


class LoginTemplate(WrapperTestTemplate):
    @property
    def name(self) -> str:
        return "login"

    @override
    @actxmgr
    async def _context(self) -> AsyncIterator[None]:
        spec_meta = TestSpecMetaContext.current()
        test_id = spec_meta.test_id
        test_id_str = str(test_id)
        credential_dep = LoginCredentialContext.current()
        endpoint_dep = EndpointContext.current()

        api_config = APIConfig(
            endpoint=endpoint_dep.login_endpoint,
            endpoint_type="session",
        )
        async with AsyncSession(config=api_config) as session:
            await _login(
                session=session,
                test_id=test_id_str,
                user_id=credential_dep.user_id,
                password=credential_dep.password,
                otp=credential_dep.otp,
            )
            with ClientSessionContext.with_current(session):
                try:
                    yield
                finally:
                    await _logout(session=session, test_id=test_id_str)


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
