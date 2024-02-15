import json
import logging
import uuid
from typing import TYPE_CHECKING, Any, List, Mapping, Tuple

import aiohttp_cors
import sqlalchemy as sa
import trafaret as t
import yaml
from aiohttp import web

from ai.backend.common import validators as tx
from ai.backend.common.logging import BraceStyleAdapter

from ..models import (
    TemplateType,
    UserRole,
    domains,
    keypairs,
    projects,
    query_accessible_session_templates,
    session_templates,
    users,
)
from ..models import association_projects_users as apus
from ..models.session_template import check_cluster_template
from .auth import auth_required
from .exceptions import InvalidAPIParameters, TaskTemplateNotFound
from .manager import READ_ALLOWED, server_status_required
from .types import CORSOptions, Iterable, WebMiddleware
from .utils import check_api_params, get_access_key_scopes

if TYPE_CHECKING:
    from .context import RootContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


@server_status_required(READ_ALLOWED)
@auth_required
@check_api_params(
    t.Dict(
        {
            tx.AliasedKey(
                ["project", "projectName", "project_name", "group", "groupName", "group_name"],
                default="default",
            ): t.String,
            tx.AliasedKey(["domain", "domainName", "domain_name"], default="default"): t.String,
            t.Key("owner_access_key", default=None): t.Null | t.String,
            t.Key("payload"): t.String,
        },
    )
)
async def create(request: web.Request, params: Any) -> web.Response:
    if params["domain"] is None:
        params["domain"] = request["user"]["domain_name"]
    requester_access_key, owner_access_key = await get_access_key_scopes(request, params)
    requester_uuid = request["user"]["uuid"]
    log.info(
        "CLUSTER_TEMPLATE.CREATE (ak:{0}/{1})",
        requester_access_key,
        owner_access_key if owner_access_key != requester_access_key else "*",
    )
    user_uuid = request["user"]["uuid"]

    root_ctx: RootContext = request.app["_root.context"]

    async with root_ctx.db.begin() as conn:
        if requester_access_key != owner_access_key:
            # Admin or superadmin is creating sessions for another user.
            # The check for admin privileges is already done in get_access_key_scope().
            query = (
                sa.select([keypairs.c.user, users.c.role, users.c.domain_name])
                .select_from(sa.join(keypairs, users, keypairs.c.user == users.c.uuid))
                .where(keypairs.c.access_key == owner_access_key)
            )
            result = await conn.execute(query)
            row = result.first()
            owner_domain = row["domain_name"]
            owner_uuid = row["user"]
            owner_role = row["role"]
        else:
            # Normal case when the user is creating her/his own session.
            owner_domain = request["user"]["domain_name"]
            owner_uuid = requester_uuid
            owner_role = UserRole.USER

        query = (
            sa.select([domains.c.name])
            .select_from(domains)
            .where(
                (domains.c.name == owner_domain) & (domains.c.is_active),
            )
        )
        qresult = await conn.execute(query)
        domain_name = qresult.scalar()
        if domain_name is None:
            raise InvalidAPIParameters("Invalid domain")

        if owner_role == UserRole.SUPERADMIN:
            # superadmin can spawn container in any designated domain/project.
            query = (
                sa.select([projects.c.id])
                .select_from(projects)
                .where(
                    (projects.c.domain_name == params["domain"])
                    & (projects.c.name == params["project"])
                    & (projects.c.is_active),
                )
            )
            qresult = await conn.execute(query)
            project_id = qresult.scalar()
        elif owner_role == UserRole.ADMIN:
            # domain-admin can spawn container in any project in the same domain.
            if params["domain"] != owner_domain:
                raise InvalidAPIParameters("You can only set the domain to the owner's domain.")
            query = (
                sa.select([projects.c.id])
                .select_from(projects)
                .where(
                    (projects.c.domain_name == owner_domain)
                    & (projects.c.name == params["project"])
                    & (projects.c.is_active),
                )
            )
            qresult = await conn.execute(query)
            project_id = qresult.scalar()
        else:
            # normal users can spawn containers in their project and domain.
            if params["domain"] != owner_domain:
                raise InvalidAPIParameters("You can only set the domain to your domain.")
            query = (
                sa.select([apus.c.project_id])
                .select_from(apus.join(projects, apus.c.project_id == projects.c.id))
                .where(
                    (apus.c.user_id == owner_uuid)
                    & (projects.c.domain_name == owner_domain)
                    & (projects.c.name == params["project"])
                    & (projects.c.is_active),
                )
            )
            qresult = await conn.execute(query)
            project_id = qresult.scalar()
        if project_id is None:
            raise InvalidAPIParameters("Invalid project")

        log.debug("Params: {0}", params)
        try:
            body = json.loads(params["payload"])
        except json.JSONDecodeError:
            try:
                body = yaml.safe_load(params["payload"])
            except (yaml.YAMLError, yaml.MarkedYAMLError):
                raise InvalidAPIParameters("Malformed payload")
        template_data = check_cluster_template(body)
        template_id = uuid.uuid4().hex
        resp = {
            "id": template_id,
            "user": user_uuid.hex,
        }
        query = session_templates.insert().values({
            "id": template_id,
            "domain_name": params["domain"],
            "project_id": project_id,
            "user_uuid": user_uuid,
            "name": template_data["metadata"]["name"],
            "template": template_data,
            "type": TemplateType.CLUSTER,
        })
        result = await conn.execute(query)
        assert result.rowcount == 1
    return web.json_response(resp)


@auth_required
@server_status_required(READ_ALLOWED)
@check_api_params(
    t.Dict({
        t.Key("all", default=False): t.ToBool,
        tx.AliasedKey(["project_id", "projectId", "group_id", "groupId"], default=None): (
            tx.UUID | t.String | t.Null
        ),
    }),
)
async def list_template(request: web.Request, params: Any) -> web.Response:
    resp = []
    root_ctx: RootContext = request.app["_root.context"]
    access_key = request["keypair"]["access_key"]
    domain_name = request["user"]["domain_name"]
    user_role = request["user"]["role"]
    user_uuid = request["user"]["uuid"]

    log.info("CLUSTER_TEMPLATE.LIST (ak:{})", access_key)
    async with root_ctx.db.begin() as conn:
        entries: List[Mapping[str, Any]]
        if request["is_superadmin"] and params["all"]:
            j = session_templates.join(
                users, session_templates.c.user_uuid == users.c.uuid, isouter=True
            ).join(projects, session_templates.c.project_id == projects.c.id, isouter=True)
            query = (
                sa.select([session_templates, users.c.email, projects.c.name], use_labels=True)
                .select_from(j)
                .where(
                    (session_templates.c.is_active)
                    & (session_templates.c.type == TemplateType.CLUSTER),
                )
            )
            result = await conn.execute(query)
            entries = []
            for row in result:
                is_owner = True if row.session_templates_user == user_uuid else False
                entries.append({
                    "name": row.session_templates_name,
                    "id": row.session_templates_id,
                    "created_at": row.session_templates_created_at,
                    "is_owner": is_owner,
                    "user": (
                        str(row.session_templates_user_uuid)
                        if row.session_templates_user_uuid
                        else None
                    ),
                    "project": (
                        str(row.session_templates_group_id)
                        if row.session_templates_group_id
                        else None
                    ),
                    "user_email": row.users_email,
                    "project_name": row.projects_name,
                })
        else:
            extra_conds = None
            if params["project_id"] is not None:
                extra_conds = session_templates.c.project_id == params["project_id"]
            entries = await query_accessible_session_templates(
                conn,
                user_uuid,
                TemplateType.CLUSTER,
                user_role=user_role,
                domain_name=domain_name,
                allowed_types=["user", "project"],
                extra_conds=extra_conds,
            )

        for entry in entries:
            resp.append({
                "name": entry["name"],
                "id": entry["id"].hex,
                "created_at": str(entry["created_at"]),
                "is_owner": entry["is_owner"],
                "user": str(entry["user"]),
                "user_email": entry["user_email"],
                "group": entry["project_name"],  # legacy
                "group_name": entry["project_name"],  # legacy
                "project_name": entry["project_name"],
                "type": "user" if entry["user"] is not None else "project",
            })
        return web.json_response(resp)


@auth_required
@server_status_required(READ_ALLOWED)
@check_api_params(
    t.Dict({
        t.Key("format", default="yaml"): t.Null | t.Enum("yaml", "json"),
        t.Key("owner_access_key", default=None): t.Null | t.String,
    }),
)
async def get(request: web.Request, params: Any) -> web.Response:
    if params["format"] not in ["yaml", "json"]:
        raise InvalidAPIParameters('format should be "yaml" or "json"')
    requester_access_key, owner_access_key = await get_access_key_scopes(request, params)
    log.info(
        "CLUSTER_TEMPLATE.GET (ak:{0}/{1})",
        requester_access_key,
        owner_access_key if owner_access_key != requester_access_key else "*",
    )

    template_id = request.match_info["template_id"]
    root_ctx: RootContext = request.app["_root.context"]

    async with root_ctx.db.begin() as conn:
        query = (
            sa.select([session_templates.c.template])
            .select_from(session_templates)
            .where(
                (session_templates.c.id == template_id)
                & (session_templates.c.is_active)
                & (session_templates.c.type == TemplateType.CLUSTER),
            )
        )
        template = await conn.scalar(query)
        if not template:
            raise TaskTemplateNotFound
    template = json.loads(template)
    if params["format"] == "yaml":
        body = yaml.dump(template)
        return web.Response(text=body, content_type="text/yaml")
    else:
        return web.json_response(template)


@auth_required
@server_status_required(READ_ALLOWED)
@check_api_params(
    t.Dict({
        t.Key("payload"): t.String,
        t.Key("owner_access_key", default=None): t.Null | t.String,
    }),
)
async def put(request: web.Request, params: Any) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    template_id = request.match_info["template_id"]

    requester_access_key, owner_access_key = await get_access_key_scopes(request, params)
    log.info(
        "CLUSTER_TEMPLATE.PUT (ak:{0}/{1})",
        requester_access_key,
        owner_access_key if owner_access_key != requester_access_key else "*",
    )

    async with root_ctx.db.begin() as conn:
        query = (
            sa.select([session_templates.c.id])
            .select_from(session_templates)
            .where(
                (session_templates.c.id == template_id)
                & (session_templates.c.is_active)
                & (session_templates.c.type == TemplateType.CLUSTER),
            )
        )
        result = await conn.scalar(query)
        if not result:
            raise TaskTemplateNotFound
        try:
            body = json.loads(params["payload"])
        except json.JSONDecodeError:
            body = yaml.safe_load(params["payload"])
        except (yaml.YAMLError, yaml.MarkedYAMLError):
            raise InvalidAPIParameters("Malformed payload")
        template_data = check_cluster_template(body)
        query = (
            sa.update(session_templates)
            .values(template=template_data, name=template_data["metadata"]["name"])
            .where((session_templates.c.id == template_id))
        )
        result = await conn.execute(query)
        assert result.rowcount == 1

        return web.json_response({"success": True})


@auth_required
@server_status_required(READ_ALLOWED)
@check_api_params(
    t.Dict({
        t.Key("owner_access_key", default=None): t.Null | t.String,
    }),
)
async def delete(request: web.Request, params: Any) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    template_id = request.match_info["template_id"]

    requester_access_key, owner_access_key = await get_access_key_scopes(request, params)
    log.info(
        "CLUSTER_TEMPLATE.DELETE (ak:{0}/{1})",
        requester_access_key,
        owner_access_key if owner_access_key != requester_access_key else "*",
    )

    async with root_ctx.db.begin() as conn:
        query = (
            sa.select([session_templates.c.id])
            .select_from(session_templates)
            .where(
                (session_templates.c.id == template_id)
                & (session_templates.c.is_active)
                & (session_templates.c.type == TemplateType.CLUSTER),
            )
        )
        result = await conn.scalar(query)
        if not result:
            raise TaskTemplateNotFound

        query = (
            sa.update(session_templates)
            .values(is_active=False)
            .where((session_templates.c.id == template_id))
        )
        result = await conn.execute(query)
        assert result.rowcount == 1

        return web.json_response({"success": True})


async def init(app: web.Application) -> None:
    pass


async def shutdown(app: web.Application) -> None:
    pass


def create_app(
    default_cors_options: CORSOptions,
) -> Tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app.on_startup.append(init)
    app.on_shutdown.append(shutdown)
    app["api_versions"] = (4, 5)
    app["prefix"] = "template/cluster"
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    cors.add(app.router.add_route("POST", "", create))
    cors.add(app.router.add_route("GET", "", list_template))
    template_resource = cors.add(app.router.add_resource(r"/{template_id}"))
    cors.add(template_resource.add_route("GET", get))
    cors.add(template_resource.add_route("PUT", put))
    cors.add(template_resource.add_route("DELETE", delete))

    return app, []
