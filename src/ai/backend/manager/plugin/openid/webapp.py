import base64
import json
import logging
import random
import string
import time
import urllib.parse
import uuid
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, timedelta
from http import HTTPStatus
from typing import (
    Any,
    Final,
    cast,
    override,
)

import aiohttp
import aiohttp_cors
import httpx  # pants: no-infer-dep
import jwt
import yarl
from aiohttp import web
from authlib.common.security import generate_token  # pants: no-infer-dep
from authlib.integrations.base_client.errors import OAuthError  # pants: no-infer-dep
from authlib.integrations.httpx_client import AsyncOAuth2Client  # pants: no-infer-dep
from authlib.jose import jwt as joseJWT  # pants: no-infer-dep
from authlib.oauth2.rfc7523 import PrivateKeyJWT  # pants: no-infer-dep
from authlib.oidc.core import CodeIDToken  # pants: no-infer-dep
from cryptography import x509
from cryptography.hazmat.primitives import hashes

from ai.backend.common.cron import LocalCron, PeriodicTask
from ai.backend.common.data.entity.domain import DomainName
from ai.backend.common.data.entity.user import UserID
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.rest.types import CORSOptions, WebMiddleware
from ai.backend.manager.models.domain.lookups import DomainNameLookup
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.project.lookups import ProjectNameInDomainLookup
from ai.backend.manager.models.user import UserRole, UserStatus
from ai.backend.manager.models.user.creators import UserCreator
from ai.backend.manager.models.user.lookups import UserEmailLookup
from ai.backend.manager.plugin.webapp import WebappPlugin
from ai.backend.manager.repositories.auth.repository import AuthRepository

from .config import OIDCWebAppConfig
from .exceptions import (
    InvalidSession,
    OpenIDAccessDenied,
    OpenIDAuthenticationFailed,
    OpenIDDomainNotFound,
    OpenIDEndpointNotConfigured,
    OpenIDGroupNotAllowed,
    OpenIDProviderMisconfigured,
    OpenIDProviderUnavailable,
    OpenIDRedirectError,
)
from .valkey_client import ValkeyOpenIDClient

log = BraceStyleAdapter(logging.getLogger(__name__))

scope = "openid profile email"


async def ping(_request: web.Request) -> web.Response:
    return web.Response(status=200, body="Backend.AI OpenID Connect SSO plugin.")


def generate_random_string(length: int = 10) -> str:
    return "".join(random.choice(string.ascii_letters) for _ in range(length))


def encode_jwt_token(token_data: dict[str, Any], secret: str) -> str:
    return jwt.encode(token_data, secret, algorithm="HS256")


def generate_user_data(
    token: Mapping[str, Any], group_mapping: Mapping[str, Any], group_order: list[str]
) -> Mapping[str, Any]:
    """
    Generate user data from OAuth token data.
    """

    # Generate username.
    email = token["email"]
    # Generate password.
    password = None
    if not password:
        password = generate_random_string()

    full_name = token["name"]
    domain_name = "default"
    project_name = "default"
    user_resource_policy_name = "default"
    keypair_resource_policy_name = "default"
    group_found = False
    # Generate domain.
    if "groups" in token:
        for group_id in group_order:
            if group_id in token["groups"]:
                mapping_info = group_mapping[group_id]
                domain_name = mapping_info.get("domain") or "default"
                project_name = mapping_info.get("project") or "default"
                user_resource_policy_name = mapping_info.get("user_resource_policy") or "default"
                keypair_resource_policy_name = (
                    mapping_info.get("keypair_resource_policy") or "default"
                )
                group_found = True
                break

    if not group_found:
        raise OpenIDGroupNotAllowed

    return {
        "user": {
            "username": email,
            "email": email,
            "password": password,
            "need_password_change": False,
            "full_name": full_name,
            "description": "",
            "status": UserStatus.ACTIVE,
            "status_info": "openid-created",
            "domain_name": domain_name,
            "role": UserRole.USER,
            "resource_policy": user_resource_policy_name,
        },
        "project": project_name,
        "keypair_resource_policy": keypair_resource_policy_name,
    }


async def create_user_if_not_exists(
    openid_user_data: Mapping[str, Any],
    group_mapping: Mapping[str, Any],
    group_order: list[str],
    auth_repository: AuthRepository,
    password_info: PasswordInfo,
) -> UserID:
    """Provision an OpenID user through the auth repository: the user scope, its
    default keypair, and the domain/project (model-store included) enrollments."""
    user_info = generate_user_data(openid_user_data, group_mapping, group_order)
    user_data = user_info["user"]
    existing_id = await auth_repository.lookup(UserEmailLookup(user_data["email"]))
    if existing_id is not None:
        log.info("OPENID.WEBAPP: found existing user ({})", user_data["email"])
        return existing_id

    domain_name = DomainName(user_data["domain_name"])
    domain_id = await auth_repository.lookup(DomainNameLookup(domain_name))
    if domain_id is None:
        raise OpenIDDomainNotFound(extra_msg=f"Domain '{domain_name}' does not exist")
    project_id = await auth_repository.lookup(
        ProjectNameInDomainLookup(domain_name, user_info["project"])
    )

    user_creator = UserCreator(
        domain_id=domain_id,
        email=user_data["email"],
        username=user_data["username"],
        password=password_info,
        need_password_change=user_data["need_password_change"],
        full_name=user_data["full_name"],
        description=user_data["description"],
        status=user_data["status"],
        status_info=user_data["status_info"],
        role=UserRole(user_data["role"]) if user_data["role"] is not None else None,
        resource_policy=user_data["resource_policy"],
    )
    creation = await auth_repository.create_user_with_keypair(
        user_creator,
        [project_id] if project_id is not None else [],
        keypair_resource_policy=user_info["keypair_resource_policy"],
    )
    log.info("OPENID.WEBAPP: new user created ({})", creation.user.email)
    return UserID(creation.user.uuid)


_JWKS_REFRESH_INTERVAL: Final[float] = 86400.0
_CLIENT_ASSERTION_LIFETIME: Final[int] = 300


class JwksRefreshTask(PeriodicTask):
    """Periodically refresh the OpenID JSON Web Key Set."""

    _app: Final[web.Application]

    def __init__(self, app: web.Application) -> None:
        self._app = app

    @property
    @override
    def name(self) -> str:
        return "openid.jwks_refresh"

    @property
    @override
    def interval(self) -> float:
        return _JWKS_REFRESH_INTERVAL

    @property
    @override
    def initial_delay(self) -> float:
        return 0.0

    @override
    async def run(self) -> None:
        async with aiohttp.ClientSession() as sess:
            async with sess.get(self._app["openid.jwks_uri"]) as resp:
                self._app["openid.jwks"] = await resp.json()
                log.info("Updated JSON Web Key Set")


class OIDCWebAppPlugin(WebappPlugin):
    require_explicit_allow = True

    _config: OIDCWebAppConfig

    def __init__(self, plugin_config: Mapping[str, Any], local_config: Mapping[str, Any]) -> None:
        super().__init__(plugin_config, local_config)
        self._config = OIDCWebAppConfig(**plugin_config)

    @override
    async def init(self, context: Any = None) -> None:
        pass

    @override
    async def cleanup(self) -> None:
        pass

    @override
    async def update_plugin_config(self, new_etcd_config: Mapping[str, Any]) -> None:
        self.plugin_config = new_etcd_config
        self._config = OIDCWebAppConfig(**new_etcd_config)

    async def _webapp_init(self, app: web.Application) -> None:
        openid_config = self._config.openid

        if openid_config.well_known is not None:
            async with aiohttp.ClientSession() as sess:
                async with sess.get(openid_config.well_known) as resp:
                    app["openid.well_known"] = await resp.json()
                    for key in ("authorization_endpoint", "token_endpoint", "jwks_uri"):
                        app[f"openid.{key}"] = app["openid.well_known"][key]
        else:
            for key in ("authorization_endpoint", "token_endpoint", "jwks_uri"):
                value = getattr(openid_config, key)
                if value is None:
                    raise OpenIDEndpointNotConfigured(
                        extra_msg=f"both well_known and {key} not configured"
                    )
                app[f"openid.{key}"] = value

        app["openid.jwks_refresh_cron"] = LocalCron([JwksRefreshTask(app)])
        await app["openid.jwks_refresh_cron"].start()

        root_app = app["_root_app"]
        config_provider = root_app["_config_provider"]
        valkey_profile_target = config_provider.config.redis.to_valkey_profile_target()
        app["valkey_client"] = await ValkeyOpenIDClient.create(
            valkey_profile_target.profile_target("openid"),
            db_id=8,
        )

    async def _webapp_shutdown(self, app: web.Application) -> None:
        await app["openid.jwks_refresh_cron"].stop()

        valkey_client: ValkeyOpenIDClient = app["valkey_client"]
        await valkey_client.close()

    def _create_oauth2_client(self, token_endpoint: str) -> AsyncOAuth2Client:
        openid_config = self._config.openid
        if openid_config.private_key is None or openid_config.certificate is None:
            return AsyncOAuth2Client(
                openid_config.client_id,
                openid_config.client_secret,
                scope=scope,
                proxies={},
                code_challenge_method="S256",
            )
        certificate = x509.load_pem_x509_certificate(openid_config.certificate.encode())
        thumbprint = base64.urlsafe_b64encode(certificate.fingerprint(hashes.SHA256()))
        now = int(time.time())
        client = AsyncOAuth2Client(
            openid_config.client_id,
            openid_config.private_key,
            token_endpoint_auth_method=PrivateKeyJWT.name,
            scope=scope,
            proxies={},
            code_challenge_method="S256",
        )
        client.register_client_auth_method(
            PrivateKeyJWT(
                token_endpoint,
                claims={"nbf": now, "exp": now + _CLIENT_ASSERTION_LIFETIME},
                headers={"typ": "JWT", "x5t#S256": thumbprint.rstrip(b"=").decode()},
                alg=openid_config.client_assertion_alg,
            )
        )
        return client

    async def login(self, request: web.Request) -> web.Response:
        post_data = await request.post()
        redirect_to = post_data.get("redirect_to", None)
        force = post_data.get("force", "false")
        authorization_endpoint = request.app["openid.authorization_endpoint"]

        redirect_uri = yarl.URL(self._config.login_uri)

        client = self._create_oauth2_client(request.app["openid.token_endpoint"])
        session_key = str(uuid.uuid4())
        code_verifier = generate_token(48)
        valkey_client: ValkeyOpenIDClient = request.app["valkey_client"]
        await valkey_client.set_openid_key(session_key, code_verifier)

        uri, _ = client.create_authorization_url(
            authorization_endpoint,
            state=urllib.parse.urlencode({
                "redirect": redirect_to or "",
                "session": session_key,
                "force": force,
            }),
            code_verifier=code_verifier,
            redirect_uri=str(redirect_uri.with_path("/func/openid/redirect")),
        )

        return web.Response(
            status=HTTPStatus.FOUND,
            headers={"Location": uri},
            # Legacy body that aiohttp's HTTP*Redirect filled in.
            text=f"{HTTPStatus.FOUND.value}: {HTTPStatus.FOUND.phrase}",
        )

    async def redirect(self, request: web.Request) -> web.Response:
        state = urllib.parse.parse_qs(request.query.get("state", ""))
        if "redirect" in state:
            redirect_uri = yarl.URL(state["redirect"][0])
        else:
            redirect_uri = yarl.URL(self._config.login_uri)
        try:
            stoken = await self._authorize(request, state, redirect_uri)
        except OpenIDRedirectError as e:
            self._log_authorization_failure(e)
            return self._redirect_to(redirect_uri, {"bai_error": e.error_slug()})
        except Exception:
            log.exception("openid authorization failed")
            return self._redirect_to(redirect_uri, {"bai_error": "internal-server-error"})
        return self._redirect_to(redirect_uri, {"sToken": stoken})

    def _log_authorization_failure(self, error: OpenIDRedirectError) -> None:
        detail = str(error.__cause__) if error.__cause__ is not None else str(error)
        if error.is_client_error():
            log.trace("openid authorization rejected", error_type=error.error_slug(), error=detail)
        elif isinstance(error, OpenIDProviderUnavailable):
            log.warning("openid provider unavailable", error_type=error.error_slug(), error=detail)
        else:
            log.error("openid authorization failed", error_type=error.error_slug(), error=detail)

    def _provider_error(self, error: OAuthError) -> OpenIDRedirectError:
        match error.error:
            case (
                "access_denied"
                | "consent_required"
                | "interaction_required"
                | "login_required"
                | "account_selection_required"
            ):
                return OpenIDAccessDenied()
            case "invalid_grant":
                return InvalidSession()
            case "server_error" | "temporarily_unavailable":
                return OpenIDProviderUnavailable()
            case (
                "invalid_client"
                | "unauthorized_client"
                | "invalid_scope"
                | "invalid_request"
                | "unsupported_response_type"
                | "unsupported_grant_type"
                | "invalid_request_uri"
                | "invalid_request_object"
                | "request_not_supported"
                | "request_uri_not_supported"
                | "registration_not_supported"
            ):
                return OpenIDProviderMisconfigured()
            case _:
                return OpenIDAuthenticationFailed()

    def _redirect_to(self, redirect_uri: yarl.URL, query: Mapping[str, str]) -> web.Response:
        return web.Response(
            status=HTTPStatus.FOUND,
            headers={"Location": str(redirect_uri.update_query(query))},
            # Legacy body that aiohttp's HTTP*Redirect filled in.
            text=f"{HTTPStatus.FOUND.value}: {HTTPStatus.FOUND.phrase}",
        )

    async def _authorize(
        self, request: web.Request, state: Mapping[str, list[str]], redirect_uri: yarl.URL
    ) -> str:
        if "error" in request.query:
            callback_error = OAuthError(
                error=request.query["error"],
                description=request.query.get("error_description"),
            )
            raise self._provider_error(callback_error) from callback_error
        if "session" not in state:
            raise InvalidSession(reason="OpenID state carries no session")

        root_app = request.app["_root_app"]
        config_provider = root_app["_config_provider"]
        auth_repository = cast(AuthRepository, root_app["_auth_repository"])
        openid_config = self._config.openid
        token_endpoint = request.app["openid.token_endpoint"]

        valkey_client: ValkeyOpenIDClient = request.app["valkey_client"]
        code_verifier = await valkey_client.get_openid_key(state["session"][0])

        client = self._create_oauth2_client(token_endpoint)

        try:
            token = await client.fetch_token(
                token_endpoint,
                authorization_response=str(request.url),
                code_verifier=code_verifier,
                redirect_uri=str(redirect_uri.with_path("/func/openid/redirect")),
            )
        except OAuthError as e:
            raise self._provider_error(e) from e
        except httpx.HTTPError as e:
            raise OpenIDProviderUnavailable from e
        try:
            claims = joseJWT.decode(
                token["id_token"], request.app["openid.jwks"], claims_cls=CodeIDToken
            )
            claims.validate()
        except Exception as e:
<<<<<<< HEAD
            log.exception("Failed to handle token: %s", e)
            log.info("OPENID.WEBAPP: request not authenticated")
=======
>>>>>>> 33a0f0cc (feat(BA-8222): support certificate client authentication in the openid plugin (#15153))
            raise OpenIDAuthenticationFailed from e

        log.info("OPENID.WEBAPP: authorized ({})", json.dumps(claims))
        config = config_provider.config
        password_info = PasswordInfo(
            password=generate_random_string(),
            algorithm=config.auth.password_hash_algorithm,
            rounds=config.auth.password_hash_rounds,
            salt_size=config.auth.password_hash_salt_size,
        )
        user_id = await create_user_if_not_exists(
            claims,
            openid_config.group_mapping,
            [x.strip() for x in openid_config.group_order.split(",")],
            auth_repository,
            password_info,
        )
        force = state.get("force", ["false"])[0].lower() == "true"
        token_data = {
            "user": str(user_id),
            "email": claims["email"],
            "exp": datetime.now(UTC) + timedelta(seconds=60),
            "force": force,
        }
        return encode_jwt_token(token_data, self._config.secret)

    @override
    async def create_app(
        self,
        cors_options: CORSOptions,
    ) -> tuple[web.Application, Sequence[WebMiddleware]]:
        app = web.Application()
        app["prefix"] = "openid"
        app["api_versions"] = (4, 5, 6)
        app.on_startup.append(self._webapp_init)
        app.on_shutdown.append(self._webapp_shutdown)
        cors = aiohttp_cors.setup(app, defaults=cors_options)
        cors.add(app.router.add_route("GET", "/redirect", self.redirect))
        cors.add(app.router.add_route("POST", "/login", self.login))
        return app, []
