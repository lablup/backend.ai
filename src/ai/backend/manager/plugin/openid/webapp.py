import functools
import json
import logging
import random
import string
import urllib.parse
import uuid
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, timedelta
from typing import (
    Any,
)

import aiohttp
import aiohttp_cors
import aiotools
import jwt
import sqlalchemy as sa
import yarl
from aiohttp import web
from authlib.common.security import generate_token  # pants: no-infer-dep
from authlib.integrations.httpx_client import AsyncOAuth2Client  # pants: no-infer-dep
from authlib.jose import jwt as joseJWT  # pants: no-infer-dep
from authlib.oidc.core import CodeIDToken  # pants: no-infer-dep
from sqlalchemy.ext.asyncio import AsyncConnection

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.rest.types import CORSOptions, WebMiddleware
from ai.backend.manager.models.group import association_groups_users, groups
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.keypair import KeyPairRow, generate_keypair, generate_ssh_keypair
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.plugin.webapp import WebappPlugin
from ai.backend.manager.repositories.base.creator import Creator, execute_creator
from ai.backend.manager.repositories.permission_controller.creators import UserRoleCreatorSpec
from ai.backend.manager.repositories.permission_controller.role_manager import (
    RoleManager,
    UserSystemRoleSpec,
)

from . import __version__
from .config import OIDCPluginConfig
from .valkey_client import ValkeyOpenIDClient

log = BraceStyleAdapter(logging.getLogger(__name__))

scope = "openid profile email"


class OpenIDError(Exception):
    pass


async def ping(_request: web.Request) -> web.Response:
    return web.Response(status=200, body=f"Backend.AI OpenID Connect SSO plugin ({__version__}).")


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
        raise OpenIDError("User does not belong to group allowed to access this resource")

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


def generate_keypair_data(
    token: Mapping[str, Any], user_uuid: uuid.UUID, resource_policy: str
) -> Mapping[str, Any]:
    ak, sk = generate_keypair()
    pubkey, privkey = generate_ssh_keypair()
    return {
        "user_id": token["email"],
        "access_key": ak,
        "secret_key": sk,
        "is_active": True,
        "is_admin": False,
        "resource_policy": resource_policy,
        "rate_limit": 10000,
        "num_queries": 0,
        "user": user_uuid,
        "ssh_public_key": pubkey,
        "ssh_private_key": privkey,
    }


async def associate_user_with_group(
    conn: AsyncConnection, user: sa.engine.row.Row[Any], group_name: str
) -> None:
    query = (
        sa.select(groups.c.id)
        .select_from(groups)
        .where(groups.c.domain_name == user.domain_name)
        .where(groups.c.name == group_name)
    )
    group_id = await conn.scalar(query)
    if group_id:
        query = association_groups_users.insert().values({
            "user_id": user.uuid,
            "group_id": group_id,
        })
        await conn.execute(query)


async def create_user_if_not_exists(
    openid_user_data: Mapping[str, Any],
    group_mapping: Mapping[str, Any],
    group_order: list[str],
    db: ExtendedAsyncSAEngine,
    password_info: PasswordInfo,
) -> sa.engine.row.Row[Any]:
    async with db.begin_session() as dbsess:
        conn = await dbsess.connection()
        # Check if user exists
        user_info = generate_user_data(openid_user_data, group_mapping, group_order)
        user_data = user_info["user"]
        query = sa.select(UserRow).where(UserRow.email == user_data["email"])
        result = await dbsess.execute(query)
        user = result.scalars().one_or_none()

        if not user:
            # Create a user.
            user = UserRow(
                username=user_data["username"],
                email=user_data["email"],
                password=password_info,
                need_password_change=user_data["need_password_change"],
                full_name=user_data["full_name"],
                description=user_data["description"],
                status=user_data["status"],
                status_info=user_data["status_info"],
                domain_name=user_data["domain_name"],
                role=user_data["role"],
                resource_policy=user_data["resource_policy"],
            )
            dbsess.add(user)
            await dbsess.flush()

            # Create a keypair for the user.
            keypair_data = generate_keypair_data(
                openid_user_data, user.uuid, user_info["keypair_resource_policy"]
            )
            keypair = KeyPairRow(
                user_id=keypair_data["user_id"],
                access_key=keypair_data["access_key"],
                secret_key=keypair_data["secret_key"],
                is_active=keypair_data["is_active"],
                is_admin=keypair_data["is_admin"],
                resource_policy=keypair_data["resource_policy"],
                rate_limit=keypair_data["rate_limit"],
                num_queries=keypair_data["num_queries"],
                user=keypair_data["user"],
                ssh_public_key=keypair_data["ssh_public_key"],
                ssh_private_key=keypair_data["ssh_private_key"],
            )
            dbsess.add(keypair)
            await dbsess.flush()

            # Associate the user with the default and model-store group, if exists.
            await associate_user_with_group(conn, user, user_info["project"])
            await associate_user_with_group(conn, user, "model-store")

            # Add `main_access_key` value to new user column.
            user.main_access_key = keypair_data["access_key"]

            # Create RBAC system role and map user to role
            role_manager = RoleManager()
            role_spec = UserSystemRoleSpec(user_id=user.uuid)
            role = await role_manager.create_system_role(dbsess, role_spec)
            user_role_creator = Creator(
                spec=UserRoleCreatorSpec(user_id=user.uuid, role_id=role.id)
            )
            await execute_creator(dbsess, user_role_creator)

            log.info("OPENID.WEBAPP: new user created ({})", user.email)
        else:
            # There is an active Backend.AI user. Do nothing.
            log.info("OPENID.WEBAPP: found existing user ({})", user.email)
    return user


async def update_jwks(app: web.Application, _interval: float) -> None:
    async with aiohttp.ClientSession() as sess:
        async with sess.get(app["openid.jwks_uri"]) as resp:
            app["openid.jwks"] = await resp.json()
            log.info("Updated JSON Web Key Set")


class OIDCWebAppPlugin(WebappPlugin):
    require_explicit_allow = True

    _config: OIDCPluginConfig

    def __init__(self, plugin_config: Mapping[str, Any], local_config: Mapping[str, Any]) -> None:
        super().__init__(plugin_config, local_config)
        self._config = OIDCPluginConfig(**plugin_config)

    async def init(self, context: Any = None) -> None:
        pass

    async def cleanup(self) -> None:
        pass

    async def update_plugin_config(self, new_etcd_config: Mapping[str, Any]) -> None:
        self.plugin_config = new_etcd_config
        self._config = OIDCPluginConfig(**new_etcd_config)

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
                    raise OpenIDError(f"both well_known and {key} not configured")
                app[f"openid.{key}"] = value

        app["openid.jwks_refresh_task"] = aiotools.create_timer(
            functools.partial(update_jwks, app), 86400
        )

        root_app = app["_root_app"]
        config_provider = root_app["_config_provider"]
        valkey_profile_target = config_provider.config.redis.to_valkey_profile_target()
        app["valkey_client"] = await ValkeyOpenIDClient.create(
            valkey_profile_target.profile_target("openid"),
            db_id=8,
        )

    async def _webapp_shutdown(self, app: web.Application) -> None:
        app["openid.jwks_refresh_task"].cancel()
        await app["openid.jwks_refresh_task"]

        valkey_client: ValkeyOpenIDClient = app["valkey_client"]
        await valkey_client.close()

    async def login(self, request: web.Request) -> web.Response:
        post_data = await request.post()
        redirect_to = post_data.get("redirect_to", None)
        force = post_data.get("force", "false")
        openid_config = self._config.openid
        authorization_endpoint = request.app["openid.authorization_endpoint"]

        redirect_uri = yarl.URL(self._config.login_uri)

        client = AsyncOAuth2Client(
            openid_config.client_id,
            openid_config.client_secret,
            scope=scope,
            proxies={},
            code_challenge_method="S256",
        )
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

        return web.HTTPFound(uri)

    async def redirect(self, request: web.Request) -> web.Response:
        root_app = request.app["_root_app"]
        config_provider = root_app["_config_provider"]
        db = root_app["_db"]
        openid_config = self._config.openid
        token_endpoint = request.app["openid.token_endpoint"]
        state = urllib.parse.parse_qs(request.query["state"])
        if "redirect" in state:
            redirect_uri = yarl.URL(state["redirect"][0])
        else:
            redirect_uri = yarl.URL(self._config.login_uri)

        valkey_client: ValkeyOpenIDClient = request.app["valkey_client"]
        code_verifier = await valkey_client.get_openid_key(state["session"][0])

        client = AsyncOAuth2Client(
            openid_config.client_id,
            openid_config.client_secret,
            scope=scope,
            proxies={},
            code_challenge_method="S256",
        )

        try:
            token = await client.fetch_token(
                token_endpoint,
                authorization_response=str(request.url),
                code_verifier=code_verifier,
                redirect_uri=str(redirect_uri.with_path("/func/openid/redirect")),
            )

            claims = joseJWT.decode(
                token["id_token"], request.app["openid.jwks"], claims_cls=CodeIDToken
            )
            claims.validate()
        except Exception as e:
            log.exception("Failed to handle token: %s", e)
            log.info("OPENID.WEBAPP: request not authenticated")
            return web.HTTPUnauthorized(reason="Not authenticated by OpenID Provider")

        log.info("OPENID.WEBAPP: authorized ({})", json.dumps(claims))
        config = config_provider.config
        password_info = PasswordInfo(
            password=generate_random_string(),
            algorithm=config.auth.password_hash_algorithm,
            rounds=config.auth.password_hash_rounds,
            salt_size=config.auth.password_hash_salt_size,
        )
        user = await create_user_if_not_exists(
            claims,
            openid_config.group_mapping,
            [x.strip() for x in openid_config.group_order.split(",")],
            db,
            password_info,
        )
        force = state.get("force", ["false"])[0].lower() == "true"
        token_data = {
            "user": str(user.uuid),
            "email": user.email,
            "exp": datetime.now(UTC) + timedelta(seconds=60),
            "force": force,
        }
        token = encode_jwt_token(token_data, self._config.secret)
        return web.HTTPFound(redirect_uri.update_query({"sToken": token}))

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
