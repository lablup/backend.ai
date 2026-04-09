import logging
from collections.abc import Mapping, Sequence
from typing import Any

import pyotp
from aiohttp import web

from ai.backend.common.dto.manager.auth.types import (
    AuthResponseType,
    RequireTwoFactorAuthResponse,
    RequireTwoFactorRegistrationResponse,
    TwoFactorType,
)
from ai.backend.common.logging_utils import BraceStyleAdapter
from ai.backend.common.plugin.hook import (
    HookHandler,
    HookPlugin,
    Reject,
)

from .config import TOTPConfig
from .utils import TokenParser

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class TOTPHook(HookPlugin):
    require_explicit_allow = True

    _plugin_config: TOTPConfig

    def __init__(self, plugin_config: Mapping[str, Any], local_config: Mapping[str, Any]) -> None:
        """
        Instantiate the plugin with the given initial configuration.
        """
        super().__init__(plugin_config, local_config)
        self._plugin_config = TOTPConfig(**plugin_config)
        self._token_parser = TokenParser(
            self._plugin_config.token_secret, self._plugin_config.token_lifetime
        )

    def get_handlers(self) -> Sequence[tuple[str, HookHandler]]:
        return [
            ("POST_AUTHORIZE", self.validate_otp),
        ]

    async def init(self, context: Any = None) -> None:
        pass

    async def cleanup(self) -> None:
        pass

    async def update_plugin_config(self, plugin_config: Mapping[str, Any]) -> None:
        self.plugin_config = plugin_config
        self._plugin_config = TOTPConfig(**plugin_config)
        self._token_parser.set_secret(self._plugin_config.token_secret)
        self._token_parser.set_lifetime(self._plugin_config.token_lifetime)

    async def validate_otp(
        self, request: web.Request, params: Any, user: Any, keypair: Any
    ) -> web.Response | None:
        if not user["totp_activated"]:
            if self._plugin_config.forced:
                token = self._token_parser.serialize(str(user["uuid"]))
                auth_data = RequireTwoFactorRegistrationResponse(
                    response_type=AuthResponseType.REQUIRE_TWO_FACTOR_REGISTRATION,
                    token=token,
                    type=TwoFactorType.TOTP,
                )
                return web.json_response(
                    data={
                        "data": auth_data.to_dict(),
                    },
                )
            log.info("TOTP.VALIDATE_OTP(TOTP not forced, user TOTP not activated)")
            return None
        if not user["totp_key"]:
            raise Reject("User activated TOTP but TOTP key does not exist")

        otp = params.get("stoken") or params.get("sToken") or params.get("otp")
        if not otp:
            auth_response = RequireTwoFactorAuthResponse(
                response_type=AuthResponseType.REQUIRE_TWO_FACTOR_AUTH,
                type=TwoFactorType.TOTP,
            )
            return web.json_response(
                data={
                    "data": auth_response.to_dict(),
                },
            )

        totp = pyotp.TOTP(user["totp_key"])
        if not totp.verify(otp):
            raise Reject("Invalid TOTP code provided")
        log.info("TOTP.VALIDATE_OTP(TOTP validated successfully)")
        return None
