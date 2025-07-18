import logging
from typing import Any, Optional

import sqlalchemy as sa
from sqlalchemy.orm.exc import NoResultFound

from ai.backend.common.events.event_types.model_serving.anycast import (
    ModelServiceStatusAnycastEvent,
    RouteCreatedAnycastEvent,
)
from ai.backend.common.types import (
    AgentId,
    ClusterMode,
    ImageAlias,
    ModelServiceStatus,
    SessionTypes,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.errors.kernel import SessionNotFound
from ai.backend.manager.registry import AgentRegistry

from ...models.endpoint import EndpointRow
from ...models.image import ImageIdentifier, ImageRow
from ...models.keypair import KeyPairRow
from ...models.routing import RouteStatus, RoutingRow
from ...models.session import KernelLoadingStrategy, SessionRow
from ...models.user import UserRow
from ...models.utils import (
    ExtendedAsyncSAEngine,
    execute_with_retry,
)
from ...types import UserScope
from ...utils import query_userinfo

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ModelServingEventHandler:
    def __init__(self, registry: AgentRegistry, db: ExtendedAsyncSAEngine) -> None:
        self._registry = registry
        self._db = db

    async def handle_model_service_status_update(
        self,
        context: None,
        source: AgentId,
        event: ModelServiceStatusAnycastEvent,
    ) -> None:
        log.info("HANDLE_MODEL_SERVICE_STATUS_UPDATE (source:{}, event:{})", source, event)
        try:
            async with self._registry.db.begin_readonly_session() as db_sess:
                session = await SessionRow.get_session(
                    db_sess,
                    event.session_id,
                    allow_stale=False,
                    kernel_loading_strategy=KernelLoadingStrategy.MAIN_KERNEL_ONLY,
                )
                route = await RoutingRow.get_by_session(db_sess, session.id, load_endpoint=True)
        except SessionNotFound:
            return
        except NoResultFound:
            return

        async def _update() -> None:
            async with self._db.begin_session() as db_sess:
                data: dict[str, Any] = {}
                match event.new_status:
                    case ModelServiceStatus.HEALTHY:
                        data["status"] = RouteStatus.HEALTHY
                    case ModelServiceStatus.UNHEALTHY:
                        data["status"] = RouteStatus.UNHEALTHY
                query = sa.update(RoutingRow).values(data).where(RoutingRow.id == route.id)
                await db_sess.execute(query)

        await execute_with_retry(_update)

    async def handle_route_creation(
        self,
        context: None,
        source: AgentId,
        event: RouteCreatedAnycastEvent,
    ) -> None:
        endpoint: Optional[EndpointRow] = None

        try:
            async with self._db.begin_readonly_session() as db_sess:
                log.debug("Route ID: {}", event.route_id)
                route = await RoutingRow.get(db_sess, event.route_id)
                endpoint = await EndpointRow.get(
                    db_sess, route.endpoint, load_image=True, load_model=True
                )

                query = sa.select(
                    sa.join(UserRow, KeyPairRow, KeyPairRow.user == UserRow.uuid)
                ).where(UserRow.uuid == endpoint.created_user)
                created_user = (await db_sess.execute(query)).fetchone()
                if endpoint.session_owner != endpoint.created_user:
                    query = sa.select(
                        sa.join(UserRow, KeyPairRow, KeyPairRow.user == UserRow.uuid)
                    ).where(UserRow.uuid == endpoint.session_owner)
                    session_owner = (await db_sess.execute(query)).fetchone()
                else:
                    session_owner = created_user

                _, group_id, resource_policy = await query_userinfo(
                    db_sess,
                    created_user.uuid,
                    created_user["access_key"],
                    created_user.role,
                    created_user.domain_name,
                    None,
                    endpoint.domain,
                    endpoint.project,
                    query_on_behalf_of=session_owner["access_key"],
                )

                image_row = await ImageRow.resolve(
                    db_sess,
                    [
                        ImageIdentifier(endpoint.image_row.name, endpoint.image_row.architecture),
                        ImageAlias(endpoint.image_row.name),
                    ],
                )

                environ = {**endpoint.environ}
                if "BACKEND_MODEL_NAME" not in environ:
                    environ["BACKEND_MODEL_NAME"] = endpoint.model_row.name

                await self._registry.create_session(
                    f"{endpoint.name}-{str(event.route_id)}",
                    image_row.image_ref,
                    UserScope(
                        domain_name=endpoint.domain,
                        group_id=group_id,
                        user_uuid=session_owner["uuid"],
                        user_role=session_owner["role"],
                    ),
                    session_owner["access_key"],
                    resource_policy,
                    SessionTypes.INFERENCE,
                    {
                        "mounts": [
                            endpoint.model,
                            *[m.vfid.folder_id for m in endpoint.extra_mounts],
                        ],
                        "mount_map": {
                            endpoint.model: endpoint.model_mount_destination,
                            **{
                                m.vfid.folder_id: m.kernel_path.as_posix()
                                for m in endpoint.extra_mounts
                            },
                        },
                        "mount_options": {
                            m.vfid.folder_id: {"permission": m.mount_perm}
                            for m in endpoint.extra_mounts
                        },
                        "model_definition_path": endpoint.model_definition_path,
                        "runtime_variant": endpoint.runtime_variant.value,
                        "environ": environ,
                        "scaling_group": endpoint.resource_group,
                        "resources": endpoint.resource_slots,
                        "resource_opts": endpoint.resource_opts,
                        "preopen_ports": None,
                        "agent_list": None,
                    },
                    ClusterMode(endpoint.cluster_mode),
                    endpoint.cluster_size,
                    bootstrap_script=endpoint.bootstrap_script,
                    startup_command=endpoint.startup_command,
                    tag=endpoint.tag,
                    callback_url=endpoint.callback_url,
                    enqueue_only=True,
                    route_id=route.id,
                    sudo_session_enabled=session_owner.sudo_session_enabled,
                )
        except Exception as e:
            log.exception("error while creating session:")
            error_data = {
                "type": "creation_failed",
                "errors": [
                    {
                        "src": "",
                        "name": e.__class__.__name__,
                        "repr": e.__repr__(),
                    }
                ],
            }

            async def _update():
                async with self._db.begin_session() as db_sess:
                    query = (
                        sa.update(RoutingRow)
                        .values({"status": RouteStatus.FAILED_TO_START, "error_data": error_data})
                        .where(RoutingRow.id == event.route_id)
                    )
                    await db_sess.execute(query)
                    if endpoint:
                        query = (
                            sa.update(EndpointRow)
                            .values({"retries": endpoint.retries + 1})
                            .where(EndpointRow.id == endpoint.id)
                        )
                        await db_sess.execute(query)

            await execute_with_retry(_update)
