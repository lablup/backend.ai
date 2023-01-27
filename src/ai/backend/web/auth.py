import json
import re
from abc import abstractmethod
from typing import List, Optional

from aiohttp import web

from ai.backend.client.config import APIConfig
from ai.backend.client.session import AsyncSession as APISession
from ai.backend.common.web.session import get_session

from . import user_agent


async def get_api_session(
    request: web.Request,
    override_api_endpoint: Optional[str] = None,
) -> APISession:
    config = request.app["config"]
    api_endpoint = config["api"]["endpoint"][0]
    if override_api_endpoint is not None:
        api_endpoint = override_api_endpoint
    session = await get_session(request)
    if not session.get("authenticated", False):
        raise web.HTTPUnauthorized(
            text=json.dumps(
                {
                    "type": "https://api.backend.ai/probs/auth-failed",
                    "title": "Unauthorized access",
                }
            ),
            content_type="application/problem+json",
        )
    if "token" not in session:
        raise web.HTTPUnauthorized(
            text=json.dumps(
                {
                    "type": "https://api.backend.ai/probs/auth-failed",
                    "title": "Unauthorized access",
                }
            ),
            content_type="application/problem+json",
        )
    token = session["token"]
    if token["type"] != "keypair":
        raise web.HTTPBadRequest(
            text=json.dumps(
                {
                    "type": "https://api.backend.ai/probs/invalid-auth-params",
                    "title": "Incompatible auth token type.",
                }
            ),
            content_type="application/problem+json",
        )
    ak, sk = token["access_key"], token["secret_key"]
    api_config = APIConfig(
        domain=config["api"]["domain"],
        endpoint=api_endpoint,
        endpoint_type="api",
        access_key=ak,
        secret_key=sk,
        user_agent=user_agent,
        skip_sslcert_validation=not config["api"]["ssl_verify"],
    )
    return APISession(config=api_config, proxy_mode=True)


async def get_anonymous_session(
    request: web.Request,
    override_api_endpoint: Optional[str] = None,
) -> APISession:
    config = request.app["config"]
    api_endpoint = config["api"]["endpoint"][0]
    if override_api_endpoint is not None:
        api_endpoint = override_api_endpoint
    api_config = APIConfig(
        domain=config["api"]["domain"],
        endpoint=api_endpoint,
        endpoint_type="api",
        access_key="",
        secret_key="",
        user_agent=user_agent,
        skip_sslcert_validation=not config["api"]["ssl_verify"],
    )
    return APISession(config=api_config, proxy_mode=True)



class BasePasswordChecker:
    """
    Base class for password strength checkers.
    """
    @abstractmethod
    async def check(self, password: str) -> (bool, str):
        """
        Check the strength of the given password. The returned list contains
        a boolean value indicating whether the password is strong enough,
        and a message describing the reason of insecurity.
        """


class PasswordLengthChecker(BasePasswordChecker):
    def __init__(
        self,
        *,
        min_length: int = 9,
        min_alphabet: int = 1,
        min_digit: int = 1,
        min_special: int = 1,
    ):
        self.min_length = min_length
        self.min_alphabet = min_alphabet
        self.min_digit = min_digit
        self.min_special = min_special
        return super().__init__()

    async def check(self, password: str) -> (bool, str):
        if not password:
            return False, "Empty password"
        error_msg = (
            f"Password should be at least {self.min_length} characters with "
            f"{self.min_alphabet} alphabet(s), {self.min_digit} number(s), and "
            f"{self.min_special} special character(s)"
        )
        if len(password) < self.min_length:
            return False, error_msg
        if len(re.findall(r"[A-Za-z]", password)) < self.min_alphabet:
            return False, error_msg
        if len(re.findall(r"[0-9]", password)) < self.min_digit:
            return False, error_msg
        if len(re.findall(r"[~`!@#$%^&*(),.?\-=_+;:'\"{}\[\]|<>/]", password)) < self.min_special:
            return False, error_msg
        return True, ""