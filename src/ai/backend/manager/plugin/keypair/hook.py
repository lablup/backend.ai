from __future__ import annotations

import hashlib
import hmac
import logging
import re
from collections.abc import Mapping, Sequence
from typing import Any

import sqlalchemy as sa
import trafaret as t
from aiohttp import web
from dateutil.parser import parse as dateutil_parse

from ai.backend.common.logging_utils import BraceStyleAdapter
from ai.backend.common.plugin.hook import HookHandler, HookPlugin, Reject
from ai.backend.common.utils import nmget
from ai.backend.manager.errors.auth import AuthorizationFailed, InvalidAuthParameters
from ai.backend.manager.models.keypair import KeyPairRow, keypairs
from ai.backend.manager.models.user import UserStatus, users

from .utils import deserialize_stoken

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

plugin_config_checker = t.Dict({
    t.Key("auth_token_name", default="sToken"): t.Null | t.String,
}).allow_extra("*")


DEFAULT_STOKEN_COOKIE_VALUE = "BackendAI"


class KeypairAuthHookPlugin(HookPlugin):
    def __init__(self, plugin_config: Mapping[str, Any], local_config: Mapping[str, Any]) -> None:
        super().__init__(plugin_config, local_config)
        self.plugin_config = plugin_config_checker.check(self.plugin_config)

    def get_handlers(self) -> Sequence[tuple[str, HookHandler]]:
        return [
            ("AUTHORIZE", self.authorize),
        ]

    async def update_plugin_config(self, plugin_config: Mapping[str, Any]) -> None:
        self.plugin_config = plugin_config

    async def init(self, context: Any = None) -> None:
        pass

    async def cleanup(self) -> None:
        pass

    def parse_token(self, token: str) -> tuple[str, str, str] | None:
        pattern = r"BackendAI signMethod=(?P<sign_method>[A-Z0-9-]+), credential=(?P<access_key>\w+):(?P<signature>\w+)"
        match = re.search(pattern, token)
        if match:
            sign_method = match.group("sign_method")
            access_key = match.group("access_key")
            signature = match.group("signature")
            return (sign_method, access_key, signature)
        return None

    async def sign_token(self, sign_method: str, secret_key: str, params: Mapping[str, Any]) -> str:
        try:
            mac_type, hash_type = map(lambda s: s.lower(), sign_method.split("-"))
            if mac_type != "hmac":
                raise InvalidAuthParameters("Unsupported signing method (MAC type)")
            if hash_type not in hashlib.algorithms_guaranteed:
                raise InvalidAuthParameters("Unsupported signing method (hash type)")

            date_obj = dateutil_parse(params["date"])
            date = date_obj.isoformat()
            endpoint = params["endpoint"]
            api_version = params["api_version"]
            if date is None:
                raise InvalidAuthParameters("Request date is missing")
            if endpoint is None:
                raise InvalidAuthParameters("Request endpoint is missing")
            if api_version is None:
                raise InvalidAuthParameters("API version is missing")

            body = b""
            body_hash = hashlib.new(hash_type, body).hexdigest()
            sign_bytes = (
                "{0}\n{1}\n{2}\nhost:{3}\ncontent-type:{4}\nx-{name}-version:{5}\n{6}".format(
                    "POST",
                    "/authorize/keypair",
                    date,
                    endpoint,
                    "application/json",
                    api_version,
                    body_hash,
                    name="backendai",
                )
            ).encode()
            sign_key = hmac.new(
                secret_key.encode(), date_obj.strftime("%Y%m%d").encode(), hash_type
            ).digest()
            sign_key = hmac.new(sign_key, endpoint.encode(), hash_type).digest()
            return hmac.new(sign_key, sign_bytes, hash_type).hexdigest()
        except ValueError:
            raise AuthorizationFailed("Invalid signature") from None

    async def authorize(
        self,
        request: web.Request,
        params: Mapping[str, Any],
    ) -> Any:
        root_app = request.app["_root_app"]
        db = root_app["_db"]
        config_provider = root_app["_config_provider"]
        shared_config = await config_provider.legacy_etcd_config_loader.load()
        plugin_config = nmget(shared_config, "plugins.webapp.keypair_auth")
        auth_token_name = self.plugin_config["auth_token_name"]

        try:
            body = await request.json()
        except Exception:
            body = {}

        stoken = params[auth_token_name]
        if stoken:
            secret = plugin_config["secret"]
            try:
                payload = deserialize_stoken(stoken, secret)
                query = sa.select(KeyPairRow).where(KeyPairRow.access_key == payload.access_key)
                async with db.begin_readonly_session() as db_session:
                    keypair_row = await db_session.scalar(query)
                    user_id = keypair_row.user

            except Exception:
                try:
                    result = self.parse_token(stoken)
                    if not result:
                        raise Reject("invalid authentication token")
                    sign_method, access_key, signature = result

                    async with db.begin() as conn:
                        query = (
                            sa.select(keypairs.c.user, keypairs.c.secret_key)
                            .select_from(keypairs)
                            .where(keypairs.c.access_key == access_key)
                        )
                        result = await conn.execute(query)
                        keypair = result.fetchone()

                    sign_params = {
                        "date": body.get("date"),
                        "endpoint": body.get("endpoint"),
                        "api_version": body.get("api_version"),
                    }
                    generated_token = await self.sign_token(
                        sign_method, keypair.secret_key, sign_params
                    )
                    if generated_token != signature:
                        raise Reject("Invalid auth token")
                    user_id = keypair.user

                except Exception as e:
                    log.error("AUTHORIZE_KEYPAIR_HOOK: invalid auth token {}", stoken)
                    log.error(repr(e))
                    raise Reject("Invalid auth token") from None

        else:
            return None  # no-op for normal login

        async with db.begin() as conn:
            query = sa.select(users).select_from(users).where(users.c.uuid == user_id)
            result = await conn.execute(query)
            user = result.fetchone()
            if not user:
                raise Reject("No such user with access key")
            if user.status != UserStatus.ACTIVE:
                raise Reject("user is inactivated with access key")
            return user
