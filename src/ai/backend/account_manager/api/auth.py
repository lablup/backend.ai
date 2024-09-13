import textwrap
import uuid
from datetime import datetime, timedelta
from typing import Annotated, cast

import aiohttp_cors
import sqlalchemy as sa
from aiohttp import web
from aiohttp.typedefs import Handler
from dateutil.tz import tzutc
from pydantic import AliasChoices, BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from ai.backend.common.auth.webapp import (
    decode_id_token,
    encode_access_token,
    encode_id_token,
    get_access_token_from_hdrs,
)
from ai.backend.common.types import AccessTokenPayload, IDTokenPayload

from ..config import ServerConfig
from ..context import RootContext
from ..defs import (
    ACCOUNT_MANAGER_APP_NAME,
    AUTH_REQUIRED_ATTR_KEY,
    BACKENDAI_APP_NAME,
    CLIENT_ROLE_ATTR_KEY,
)
from ..models.application import ApplicationRow, AssociationApplicationUserRow
from ..models.keypair import KeypairRow
from ..models.user import UserRow
from ..models.userprofile import UserProfileRow, compare_to_hashed_password
from ..types import (
    CORSOptions,
    UserRole,
    UserStatus,
    WebMiddleware,
)
from .exceptions import AuthorizationFailed
from .utils import RequestData, ResponseModel, auth_required, get_handler_attr, pydantic_api_handler


class TokenUtil:
    algorithm = "HS256"

    @classmethod
    def encode_id_token(
        cls,
        secret: str,
        lifespan: timedelta,
        user_id: uuid.UUID,
        application_id: uuid.UUID,
        current_dt: datetime | None = None,
        username: str | None = None,
        email: str | None = None,
        *,
        local_config: ServerConfig,
    ) -> str:
        now = current_dt if current_dt is not None else datetime.now(tzutc())
        issuer = str(local_config.account_manager.service_addr)

        expiration_dt = now + lifespan
        return encode_id_token(
            IDTokenPayload(
                iss=issuer,
                sub=user_id.hex,
                aud=application_id.hex,
                exp=int(expiration_dt.timestamp()),
                iat=int(now.timestamp()),
                preferred_username=username,
                email=email,
            ),
            secret=secret,
            algorithm=cls.algorithm,
        )

    @classmethod
    def encode_access_token(
        cls,
        secret: str,
        lifespan: timedelta,
        user_id: uuid.UUID,
        application_id: uuid.UUID,
        current_dt: datetime | None = None,
        *,
        local_config: ServerConfig,
    ) -> str:
        now = current_dt if current_dt is not None else datetime.now(tzutc())
        issuer = str(local_config.account_manager.service_addr)

        expiration_dt = now + lifespan
        return encode_access_token(
            AccessTokenPayload(
                iss=issuer,
                sub=user_id.hex,
                aud=application_id.hex,
                exp=int(expiration_dt.timestamp()),
                iat=int(now.timestamp()),
                client_id=user_id.hex,
                jti=uuid.uuid4().hex,
            ),
            secret=secret,
            algorithm=cls.algorithm,
        )

    @classmethod
    def decode_id_token(
        cls,
        token: str,
        secret: str,
    ) -> IDTokenPayload:
        return decode_id_token(
            token,
            secret=secret,
            algorithms=[cls.algorithm],
        )


class SignupRequestModel(RequestData):
    application_names: Annotated[
        list[str],
        Field(
            description="Applications to signup.",
            validation_alias=AliasChoices("applications", "applicationNames", "application_names"),
        ),
    ]
    username: Annotated[str, Field(description="Account's username.")]
    email: Annotated[
        str | None, Field(description="Account's email. Default is null.", default=None)
    ]
    password: Annotated[str, Field(description="Account's password.")]


class SignupResponseData(BaseModel):
    access_key: Annotated[str, Field(description="Account's access key.")]
    secret_key: Annotated[str, Field(description="Account's secret key.")]
    application_names: Annotated[
        set[str],
        Field(description="Application names that the account got registered successfully."),
    ]


@pydantic_api_handler(SignupRequestModel)
async def signup(
    request: web.Request,
    params: SignupRequestModel,
) -> ResponseModel[SignupResponseData]:
    """
    Sign up to Backend.AI applications.
    """
    root_ctx: RootContext = request.app["_root.context"]
    api_config = root_ctx.shared_config
    if api_config.allow_admin_only_to_create_user:
        raise AuthorizationFailed

    require_verification = api_config.signup_requires_verification

    async def _get_or_create_user(db_session: AsyncSession) -> tuple[uuid.UUID, str, str]:
        _stmt = (
            sa.select(UserProfileRow)
            .where(UserProfileRow.username == params.username)
            .options(
                joinedload(UserProfileRow.user_row).options(selectinload(UserRow.keypair_rows))
            )
        )
        profile_row = cast(UserProfileRow | None, await db_session.scalar(_stmt))
        if profile_row is None:
            user_id = cast(
                uuid.UUID, await db_session.scalar(sa.insert(UserRow).returning(UserRow.uuid))
            )
            if require_verification:
                status = UserStatus.BEFORE_VERIFICATION
            else:
                status = UserStatus.ACTIVE

            await db_session.execute(
                sa.insert(UserProfileRow).values(
                    username=params.username,
                    email=params.email,
                    password=params.password,
                    user_id=user_id,
                    status=status,
                )
            )
            ak, sk = await KeypairRow.create_keypair(user_id, db_session=db_session)
        else:
            now = datetime.now(tzutc())
            user_id = cast(uuid.UUID, profile_row.user_row.uuid)
            keypair_rows = cast(list[KeypairRow], profile_row.user_row.keypair_rows)
            for kp in keypair_rows:
                if not kp.is_expired(now):
                    ak, sk = kp.access_key, kp.secret_key
                    break
            else:
                # Create new keypairs.
                ak, sk = await KeypairRow.create_keypair(user_id, db_session=db_session)

        return user_id, ak, sk

    async def _register_to_app(db_session: AsyncSession, user_id: uuid.UUID) -> set[str]:
        """
        Register user to applications.
        Return a set of application names that user gets registered successfully.
        """
        valid_app_ids: list[uuid.UUID] = []
        valid_app_names: set[str] = set()
        _apps = sa.select(ApplicationRow).where(ApplicationRow.name.in_(params.application_names))
        app_rows = cast(list[ApplicationRow], (await db_session.scalars(_apps)).all())
        for app_row in app_rows:
            valid_app_ids.append(app_row.id)
            valid_app_names.add(app_row.name)

        await db_session.execute(
            sa.insert(AssociationApplicationUserRow),
            [
                {
                    "user_id": user_id,
                    "application_id": app_id,
                }
                for app_id in valid_app_ids
            ],
        )

        return valid_app_names

    async with root_ctx.db.connect() as db_conn:
        user_id, ak, sk = await root_ctx.db.execute_with_txn_retry(_get_or_create_user, db_conn)
        valid_app_names = await root_ctx.db.execute_with_txn_retry(
            _register_to_app, db_conn, user_id=user_id
        )
    return ResponseModel(
        status=201,
        data=SignupResponseData(
            access_key=ak,
            secret_key=sk,
            application_names=valid_app_names,
        ),
    )


class AuthorizeRequestModel(RequestData):
    username: Annotated[str, Field(description="Account's username.")]
    password: Annotated[str, Field(description="Account's password.")]
    application_name: Annotated[
        str,
        Field(
            description=textwrap.dedent("Name of application to login. Default is `backend.ai`."),
            default=BACKENDAI_APP_NAME,
        ),
    ]


class AuthorizeResponseData(BaseModel):
    id_token: Annotated[str, Field()]
    application_names: Annotated[list[str], Field()]
    redirect_url: Annotated[str | None, Field(default=None)]


@pydantic_api_handler(AuthorizeRequestModel)
async def authorize(
    request: web.Request,
    params: AuthorizeRequestModel,
) -> ResponseModel[AuthorizeResponseData]:
    """
    1. Check user exists
    2. Check the application name
    3. Issue an ID token according to the application name
    """
    root_ctx: RootContext = request.app["_root.context"]

    async with root_ctx.db.begin_readonly_session() as db_session:
        stmt = (
            sa.select(UserProfileRow)
            .where(UserProfileRow.username == params.username)
            .options(
                joinedload(UserProfileRow.user_row).options(
                    # selectinload(UserRow.keypair_rows),
                    selectinload(UserRow.app_assoc_rows).options(
                        joinedload(AssociationApplicationUserRow.application_row)
                    ),
                )
            )
        )
        profile_row = cast(UserProfileRow | None, await db_session.scalar(stmt))
    if profile_row is None:
        raise AuthorizationFailed
    match profile_row.status:
        case UserStatus.ACTIVE:
            pass
        case UserStatus.INACTIVE:
            raise AuthorizationFailed
        case UserStatus.BEFORE_VERIFICATION:
            raise AuthorizationFailed
        case UserStatus.DELETED:
            raise AuthorizationFailed

    if not compare_to_hashed_password(params.password, profile_row.password):
        raise AuthorizationFailed

    redirect_url = None
    app_id = None
    app_names = []
    user_row = cast(UserRow, profile_row.user_row)
    for assoc_row in user_row.app_assoc_rows:
        app_row = cast(ApplicationRow, assoc_row.application_row)
        app_names.append(app_row.name)
        if app_row.name == params.application_name:
            redirect_url = cast(str, app_row.redirect_to)
            app_id = cast(uuid.UUID, app_row.id)
            token_secret = app_row.token_secret
            token_lifespan = app_row.token_lifespan
            break
    else:
        raise AuthorizationFailed
    now = datetime.now(tzutc())

    id_token = TokenUtil.encode_id_token(
        token_secret,
        token_lifespan,
        user_row.uuid,
        app_id,
        now,
        params.username,
        profile_row.email,
        local_config=root_ctx.local_config,
    )

    return ResponseModel(
        data=AuthorizeResponseData(
            id_token=id_token,
            application_names=app_names,
            redirect_url=redirect_url,
        )
    )


class IssueAccessTokenRequestModel(RequestData):
    id_token: Annotated[str, Field(description="ID token.")]


class AccessTokenData(BaseModel):
    access_token: Annotated[str, Field()]


@pydantic_api_handler(IssueAccessTokenRequestModel)
async def issue_access_token(
    request: web.Request,
    params: IssueAccessTokenRequestModel,
) -> ResponseModel[AccessTokenData]:
    root_ctx: RootContext = request.app["_root.context"]

    async with root_ctx.db.begin_readonly_session() as db_session:
        app_query = sa.select(ApplicationRow).where(ApplicationRow.name == ACCOUNT_MANAGER_APP_NAME)
        app_row = cast(ApplicationRow, await db_session.scalar(app_query))
        secret = app_row.token_secret
        lifespan = app_row.token_lifespan

        id_token = TokenUtil.decode_id_token(params.id_token, secret)
        user_id = uuid.UUID(id_token.sub)
        app_id = uuid.UUID(id_token.aud)
        user_query = sa.select(UserRow).where(UserRow.uuid == user_id)
        user_row = cast(UserRow | None, await db_session.scalar(user_query))
        if user_row is None:
            raise AuthorizationFailed

    access_token = TokenUtil.encode_access_token(
        secret,
        lifespan,
        user_row.uuid,
        app_id,
        local_config=root_ctx.local_config,
    )

    return ResponseModel(
        data=AccessTokenData(access_token=access_token),
    )


@web.middleware
async def auth_middleware(request: web.Request, handler: Handler) -> web.StreamResponse:
    root_ctx: RootContext = request.app["_root.context"]
    request["is_authorized"] = False

    if not get_handler_attr(request, AUTH_REQUIRED_ATTR_KEY, False):
        return await handler(request)

    # Extract auth header
    api_config = root_ctx.shared_config
    auth_hdr = request.headers.get("Authorization")
    if auth_hdr is None:
        raise AuthorizationFailed
    payload = get_access_token_from_hdrs(auth_hdr, api_config.access_token_secret)

    async with root_ctx.db.begin_readonly_session() as db_session:
        stmt = (
            sa.select(UserRow)
            .where(UserRow.uuid == payload.sub)
            .options(selectinload(UserRow.user_profile_rows))
        )
        user_row = cast(UserRow | None, await db_session.scalar(stmt))
        if user_row is None:
            raise AuthorizationFailed

        user_role = UserRole.USER
        for profile_row in user_row.user_profile_rows:
            role = cast(UserRole, profile_row.role)
            match role:
                case UserRole.ADMIN:
                    user_role = role
                case UserRole.USER:
                    pass
        request.update({CLIENT_ROLE_ATTR_KEY: user_role})

    return await handler(request)


class VerifyUserRequestModel(RequestData):
    username: Annotated[str, Field(description="Username of the account to verify.")]


@auth_required(UserRole.ADMIN)
@pydantic_api_handler(VerifyUserRequestModel)
async def verify_user(
    request: web.Request,
    params: VerifyUserRequestModel,
) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]

    async with root_ctx.db.connect() as db_conn:

        async def _check_and_verify(db_session: AsyncSession) -> None:
            stmt = sa.select(UserProfileRow).where(UserProfileRow.username == params.username)
            profile_row = cast(UserProfileRow | None, await db_session.scalar(stmt))
            if profile_row is None:
                raise AuthorizationFailed
            profile_row.status = UserStatus.ACTIVE

        await root_ctx.db.execute_with_txn_retry(_check_and_verify, db_conn)

    return web.Response(status=201)


class SignoutRequestModel(RequestData):
    application_names: Annotated[
        str,
        Field(
            description="Applications to signup.",
            validation_alias=AliasChoices("applications", "applicationNames", "application_names"),
        ),
    ]
    username: Annotated[str, Field(description="Account's username.")]
    email: Annotated[
        str | None, Field(description="Account's email. Default is null.", default=None)
    ]
    password: Annotated[str, Field(description="Account's password.")]


# @auth_required
# @pydantic_api_handler(SignoutRequestModel)
# async def signout(
#     request: web.Request,
#     params: SignoutRequestModel,
# ) -> web.Response:
#     pass


async def init(app: web.Application) -> None:
    pass


async def shutdown(app: web.Application) -> None:
    pass


def create_app(
    default_cors_options: CORSOptions,
) -> tuple[web.Application, list[WebMiddleware]]:
    app = web.Application()
    app["prefix"] = "auth"
    app.on_startup.append(init)
    app.on_shutdown.append(shutdown)
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    add_route = app.router.add_route
    cors.add(add_route("POST", "/authorize", authorize))
    cors.add(add_route("POST", "/token", issue_access_token))
    # cors.add(add_route("POST", "/refresh", refresh))
    cors.add(add_route("POST", "/signup", signup))
    # cors.add(add_route("POST", "/signout", signout))
    return app, []
