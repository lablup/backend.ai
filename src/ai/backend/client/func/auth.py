import json
from typing import Any, Optional

from ..auth import encrypt_payload
from ..request import Request
from .base import BaseFunction, api_function

__all__ = ("Auth",)


def _put_secure_body(rqst: Request, data: Any) -> None:
    if rqst.config.endpoint.scheme == "https":
        rqst.set_json(data)
    else:
        rqst.headers["X-BackendAI-Encoded"] = "true"
        raw_body = json.dumps(data).encode()
        encoded_body = encrypt_payload(str(rqst.config.endpoint), raw_body)
        rqst.set_content(encoded_body)


class Auth(BaseFunction):
    """
    Provides the function interface for login session management and authorization.
    """

    @api_function
    @classmethod
    async def login(cls, user_id: str, password: str, otp: Optional[str] = None) -> dict:
        """
        Log-in into the endpoint with the given user ID and password.
        It creates a server-side web session and return
        a dictionary with ``"authenticated"`` boolean field and
        JSON-encoded raw cookie data.
        """
        rqst = Request("POST", "/server/login")
        body = {
            "username": user_id,
            "password": password,
        }
        if otp:
            body["otp"] = otp
        _put_secure_body(rqst, body)
        async with rqst.fetch(anonymous=True) as resp:
            data = await resp.json()
            data["cookies"] = resp.raw_response.cookies
            data["config"] = {
                "username": user_id,
            }
            return data

    @api_function
    @classmethod
    async def logout(cls) -> None:
        """
        Log-out from the endpoint.
        It clears the server-side web session.
        """
        rqst = Request("POST", "/server/logout")
        async with rqst.fetch() as resp:
            resp.raw_response.raise_for_status()

    @api_function
    @classmethod
    async def update_password(
        cls, old_password: str, new_password: str, new_password2: str
    ) -> dict:
        """
        Update user's password. This API works only for account owner.
        """
        rqst = Request("POST", "/auth/update-password")
        body = {
            "old_password": old_password,
            "new_password": new_password,
            "new_password2": new_password2,
        }
        _put_secure_body(rqst, body)
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def update_password_no_auth(
        cls, domain: str, user_id: str, current_password: str, new_password: str
    ) -> dict:
        """
        Update user's password. This is used to update `EXPIRED` password only.
        This function fetch a request to manager.
        """

        rqst = Request("POST", "/auth/update-password-no-auth")
        body = {
            "domain": domain,
            "username": user_id,
            "current_password": current_password,
            "new_password": new_password,
        }
        _put_secure_body(rqst, body)
        async with rqst.fetch(anonymous=True) as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def update_password_no_auth_in_session(
        cls, user_id: str, current_password: str, new_password: str
    ) -> dict:
        """
        Update user's password. This is used to update `EXPIRED` password only.
        This function fetch a request to webserver.
        """

        rqst = Request("POST", "/server/update-password-no-auth")
        body = {
            "username": user_id,
            "current_password": current_password,
            "new_password": new_password,
        }
        _put_secure_body(rqst, body)
        async with rqst.fetch(anonymous=True) as resp:
            return await resp.json()
