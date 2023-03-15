import logging
from typing import TYPE_CHECKING, Any, Iterable

import aiohttp_cors
import aiotools
import attrs
import sqlalchemy as sa
import trafaret as t
from aiohttp import web

from ai.backend.common import validators as tx
from ai.backend.common.docker import ImageRef, validate_image_labels
from ai.backend.common.exception import AliasResolutionFailed
from ai.backend.common.logging import BraceStyleAdapter

from ..models.domain import domains
from ..models.endpoint import EndpointRow
from ..models.image import ImageRow
from ..models.scaling_group import query_allowed_sgroups
from .auth import auth_required
from .exceptions import ImageNotFound, InvalidAPIParameters, ScalingGroupNotFound
from .manager import ALL_ALLOWED, READ_ALLOWED, server_status_required
from .types import CORSOptions, WebMiddleware
from .utils import check_api_params

if TYPE_CHECKING:
    from .context import RootContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


@auth_required
@server_status_required(READ_ALLOWED)
@check_api_params(
    t.Dict(
        {
            tx.AliasedKey(["project_id", "projectId"]): tx.UUID,
        }
    ),
)
async def list_(request: web.Request, params: Any) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    access_key = request["keypair"]["access_key"]
    project_id = params["project_id"]

    log.info("ENDPOINT.LIST (email:{}, ak:{})", request["user"]["email"], access_key)
    async with root_ctx.db.begin_readonly_session() as db_sess:
        query = sa.select(EndpointRow).where(EndpointRow.project_id == project_id)
        result = await db_sess.execute(query)
        rows = result.scalars().all()
    return web.json_response(rows, status=200)


@auth_required
@server_status_required(ALL_ALLOWED)
@check_api_params(
    t.Dict(
        {
            t.Key("url"): t.String,
            tx.AliasedKey(["image_ref", "imageRef"]): t.String,
            tx.AliasedKey(
                ["group", "groupName", "group_name", "project", "project_name", "projectName"],
                default="default",
            ): t.String,
            tx.AliasedKey(["domain", "domainName", "domain_name"], default="default"): t.String,
            tx.AliasedKey(["resource_slots", "resourceSlots"], default=dict): t.Mapping(
                t.String, t.Any
            ),
            tx.AliasedKey(
                [
                    "resource_group",
                    "resource_group_name",
                    "resourceGroup",
                    "scaling_group",
                    "scalingGroup",
                ],
                default=None,
            ): t.String
            | t.Null,
        }
    ),
)
async def create(request: web.Request, params: Any) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    access_key = request["keypair"]["access_key"]

    log.info("ENDPOINT.CREATE (email:{}, ak:{})", request["user"]["email"], access_key)
    # Resolve the image reference.
    try:
        async with root_ctx.db.begin_readonly_session() as session:
            image_row = await ImageRow.resolve(
                session,
                [
                    ImageRef(params["image_ref"], ["*"], params["architecture"]),
                    params["image_ref"],
                ],
            )
            img_id = image_row.id
        requested_image_ref = image_row.image_ref
        parsed_labels: dict[str, Any] = validate_image_labels(image_row.labels)
        parsed_labels["ai.backend.model-path"] = "model-path"
        try:
            parsed_labels["ai.backend.model-path"]
        except KeyError:
            raise InvalidAPIParameters("Given image does not have model-path label")
        # service_ports: dict[str, ServicePort] = {
        #     item["name"]: item for item in parsed_labels["ai.backend.service-ports"]
        # }
        # endpoints: Sequence[str] = parsed_labels["ai.backend.endpoint-ports"]
        async with root_ctx.db.begin_readonly_session() as db_sess:
            query = sa.select([domains.c.allowed_docker_registries]).where(
                domains.c.name == params["domain"]
            )
            allowed_registries = await db_sess.scalar(query)
            if requested_image_ref.registry not in allowed_registries:
                raise AliasResolutionFailed
    except AliasResolutionFailed:
        raise ImageNotFound("unknown alias or disallowed registry")

    resource_group = params["resource_group"]
    if resource_group is None:
        async with root_ctx.db.begin_readonly() as db_conn:
            candidates = await query_allowed_sgroups(
                db_conn, params["domain"], params["group"], access_key
            )
            if not candidates:
                raise ScalingGroupNotFound("You have no resource groups allowed to use.")
            resource_group = candidates[0]["name"]
    async with root_ctx.db.begin_session() as db_sess:
        query = (
            sa.insert(EndpointRow)
            .values(
                {
                    "url": params["url"],
                    "image_id": img_id,
                    "model_id": params["model"],
                    "project_id": params["group"],
                    "domain_name": params["domain"],
                    "resource_group_name": resource_group,
                }
            )
            .returning(EndpointRow.id)
        )
        result = (await db_sess.execute(query)).first()
    resp = {
        "url": params["url"],
        "image_id": img_id,
        "image_ref": params["image_ref"],
        "model_id": params["model"],
        "project_id": params["group"],
        "domain_name": params["domain"],
        "resource_group_name": resource_group,
        "id": result["id"],
    }
    return web.json_response(resp, status=201)


@auth_required
@server_status_required(READ_ALLOWED)
@check_api_params(
    t.Dict(
        {
            tx.AliasedKey(["endpoint_id", "endpointId"]): tx.UUID,
        }
    ),
)
async def delete(request: web.Request, params: Any) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    access_key = request["keypair"]["access_key"]

    log.info("ENDPOINT.DELETE (email:{}, ak:{})", request["user"]["email"], access_key)

    async with root_ctx.db.begin_session() as db_sess:
        query = sa.delete(EndpointRow).where(EndpointRow.id == params["endpoint_id"])
        await db_sess.execute(query)

    return web.Response(status=204)


@attrs.define(slots=True, auto_attribs=True, init=False)
class PrivateContext:
    database_ptask_group: aiotools.PersistentTaskGroup


async def init(app: web.Application) -> None:
    app_ctx: PrivateContext = app["endpoint.context"]
    app_ctx.database_ptask_group = aiotools.PersistentTaskGroup()


async def shutdown(app: web.Application) -> None:
    app_ctx: PrivateContext = app["endpoint.context"]
    await app_ctx.database_ptask_group.shutdown()


def create_app(
    default_cors_options: CORSOptions,
) -> tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app["prefix"] = "endpoint"
    app["api_versions"] = (4, 5)
    app.on_startup.append(init)
    app.on_shutdown.append(shutdown)
    app["endpoint.context"] = PrivateContext()
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    root_resource = cors.add(app.router.add_resource(r""))
    cors.add(root_resource.add_route("GET", list_))
    cors.add(root_resource.add_route("POST", create))
    cors.add(root_resource.add_route("DELETE", delete))
    return app, []
