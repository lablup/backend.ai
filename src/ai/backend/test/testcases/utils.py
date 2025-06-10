import shutil
import tempfile
from pathlib import Path
from typing import Optional

from ai.backend.client.session import AsyncSession


def get_test_temp_dir(test_id: str) -> Path:
    temp_base = Path(tempfile.gettempdir()) / "backend_ai_tests"
    temp_dir = temp_base / test_id
    return temp_dir


async def login(
    session: AsyncSession,
    test_id: str,
    user_id: str,
    password: str,
    otp: Optional[str] = None,
) -> None:
    temp_dir = get_test_temp_dir(test_id)
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


async def logout(session: AsyncSession, test_id: str) -> None:
    try:
        await session.Auth.logout()
    except Exception as e:
        print(f"Failed to logout: {e}")

    temp_dir = get_test_temp_dir(test_id)
    if temp_dir.exists():
        try:
            shutil.rmtree(temp_dir)
        except Exception as e:
            print(f"Failed to clean up temp directory: {e}")
