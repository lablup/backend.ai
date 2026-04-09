import logging
from typing import Any

import sqlalchemy as sa
import yarl
from sqlalchemy.exc import NoResultFound

from ai.backend.common.dto.manager.v2.runtime_variant_preset.types import (
    PresetTarget,
    PresetValueType,
)
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
from ai.backend.manager.data.deployment.types import RouteHealthStatus, RouteStatus
from ai.backend.manager.errors.kernel import SessionNotFound
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.image import ImageIdentifier, ImageRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.runtime_variant_preset.row import RuntimeVariantPresetRow
from ai.backend.manager.models.session import KernelLoadingStrategy, SessionRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import (
    ExtendedAsyncSAEngine,
    execute_with_retry,
)
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.types import UserScope
from ai.backend.manager.utils import query_userinfo_from_session

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ModelServingEventHandler:
    def __init__(self, registry: AgentRegistry, db: ExtendedAsyncSAEngine) -> None:
        self._registry = registry
        self._db = db

    async def handle_model_service_status_update(
        self,
        _context: None,
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
                        data["health_status"] = RouteHealthStatus.HEALTHY
                    case ModelServiceStatus.UNHEALTHY:
                        data["health_status"] = RouteHealthStatus.UNHEALTHY
                query = sa.update(RoutingRow).values(data).where(RoutingRow.id == route.id)
                await db_sess.execute(query)

        await execute_with_retry(_update)

    async def handle_route_creation(
        self,
        _context: None,
        _source: AgentId,
        event: RouteCreatedAnycastEvent,
    ) -> None:
        endpoint: EndpointRow | None = None

        try:
            async with self._db.begin_readonly_session() as db_sess:
                log.debug("Route ID: {}", event.route_id)
                route = await RoutingRow.get(db_sess, event.route_id)
                endpoint = await EndpointRow.get(db_sess, route.endpoint, load_revisions=True)

                # Get the current revision for revision-level fields
                current_rev = endpoint._find_current_revision()
                if current_rev is None:
                    raise ValueError(f"No current revision for endpoint {endpoint.id}")

                query = sa.select(
                    sa.join(UserRow, KeyPairRow, KeyPairRow.user == UserRow.uuid)
                ).where(UserRow.uuid == endpoint.created_user)
                created_user = (await db_sess.execute(query)).fetchone()
                if created_user is None:
                    raise ValueError(f"Created user not found for endpoint {endpoint.id}")
                if endpoint.session_owner != endpoint.created_user:
                    query = sa.select(
                        sa.join(UserRow, KeyPairRow, KeyPairRow.user == UserRow.uuid)
                    ).where(UserRow.uuid == endpoint.session_owner)
                    session_owner = (await db_sess.execute(query)).fetchone()
                    if session_owner is None:
                        raise ValueError(f"Session owner not found for endpoint {endpoint.id}")
                else:
                    session_owner = created_user

                user_info = await query_userinfo_from_session(
                    db_sess,
                    created_user.uuid,
                    created_user.access_key,
                    created_user.role,
                    created_user.domain_name,
                    None,
                    endpoint.domain,
                    endpoint.project,
                    query_on_behalf_of=session_owner.access_key,
                )
                group_id = user_info.group_id
                resource_policy = user_info.resource_policy

                if current_rev.image_row is None:
                    raise ValueError(f"Image not found for endpoint {endpoint.id}")
                image_row = await ImageRow.resolve(
                    db_sess,
                    [
                        ImageIdentifier(
                            current_rev.image_row.name, current_rev.image_row.architecture
                        ),
                        ImageAlias(current_rev.image_row.name),
                    ],
                )

                environ = {**(current_rev.environ or {})}
                startup_command = current_rev.startup_command
                if "BACKEND_MODEL_NAME" not in environ:
                    # Look up the model VFolder name for BACKEND_MODEL_NAME
                    if current_rev.model is not None:
                        model_row = await VFolderRow.get(db_sess, current_rev.model)
                        if model_row is not None:
                            environ["BACKEND_MODEL_NAME"] = model_row.name

                # Resolve preset_values into environ and startup_command args
                if current_rev.preset_values:
                    preset_ids = [pv.preset_id for pv in current_rev.preset_values]
                    stmt = sa.select(RuntimeVariantPresetRow).where(
                        RuntimeVariantPresetRow.id.in_(preset_ids)
                    )
                    vp_rows = (await db_sess.execute(stmt)).scalars().all()
                    vp_map = {row.id: row for row in vp_rows}
                    args_parts: list[str] = []
                    for pv in current_rev.preset_values:
                        vp = vp_map.get(pv.preset_id)
                        if vp is None:
                            continue
                        if vp.preset_target == PresetTarget.ENV:
                            environ[vp.key] = pv.value
                        elif vp.preset_target == PresetTarget.ARGS:
                            if vp.value_type == PresetValueType.FLAG:
                                if (pv.value or "").strip().lower() in ("true", "1"):
                                    args_parts.append(vp.key)
                            else:
                                args_parts.append(f"{vp.key} {pv.value}")
                    if args_parts and startup_command:
                        startup_command = f"{startup_command} {' '.join(args_parts)}"
                    elif args_parts:
                        startup_command = " ".join(args_parts)

                await self._registry.create_session(
                    f"{endpoint.name}-{event.route_id!s}",
                    image_row.image_ref,
                    UserScope(
                        domain_name=endpoint.domain,
                        group_id=group_id,
                        user_uuid=session_owner.uuid,
                        user_role=session_owner.role,
                    ),
                    session_owner.access_key,
                    resource_policy,
                    SessionTypes.INFERENCE,
                    {
                        "mounts": [
                            current_rev.model,
                            *[m.vfid.folder_id for m in current_rev.extra_mounts],
                        ],
                        "mount_map": {
                            current_rev.model: current_rev.model_mount_destination,
                            **{
                                m.vfid.folder_id: m.kernel_path.as_posix()
                                for m in current_rev.extra_mounts
                            },
                        },
                        "mount_options": {
                            m.vfid.folder_id: {"permission": m.mount_perm}
                            for m in current_rev.extra_mounts
                        },
                        "model_definition_path": current_rev.model_definition_path,
                        "runtime_variant": current_rev.runtime_variant,
                        "environ": environ,
                        "scaling_group": endpoint.resource_group,
                        "resources": current_rev.resource_slots,
                        "resource_opts": current_rev.resource_opts,
                        "preopen_ports": None,
                        "agent_list": None,
                    },
                    ClusterMode(current_rev.cluster_mode),
                    current_rev.cluster_size,
                    bootstrap_script=current_rev.bootstrap_script,
                    startup_command=startup_command,
                    tag=endpoint.tag,
                    callback_url=(
                        yarl.URL(current_rev.callback_url) if current_rev.callback_url else None
                    ),
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

            async def _update() -> None:
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
