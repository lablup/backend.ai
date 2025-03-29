import asyncio
import functools
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, Mapping, cast

import aiotools
import attrs
import sqlalchemy as sa
from dateutil.tz import tzutc
from redis.asyncio import Redis
from sqlalchemy.orm import load_only, selectinload
from sqlalchemy.sql.expression import null, true

from ai.backend.common import redis_helper
from ai.backend.common.bgtask import BackgroundTaskManager, ProgressReporter
from ai.backend.common.docker import ImageRef
from ai.backend.common.events import (
    AgentTerminatedEvent,
    BgtaskCancelledEvent,
    BgtaskDoneEvent,
    BgtaskFailedEvent,
    EventProducer,
)
from ai.backend.common.exception import BackendError, InvalidAPIParameters, UnknownImageReference
from ai.backend.common.plugin.monitor import GAUGE, ErrorPluginContext, StatsPluginContext
from ai.backend.common.types import ImageAlias, ImageRegistry, RedisConnectionInfo
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.api.exceptions import (
    InternalServerError,
    QuotaExceeded,
    SessionAlreadyExists,
    TaskTemplateNotFound,
    TooManySessionsMatched,
    UnknownImageReferenceError,
)
from ai.backend.manager.api.session import CustomizedImageVisibilityScope
from ai.backend.manager.api.utils import catch_unexpected, undefined
from ai.backend.manager.config import LocalConfig
from ai.backend.manager.defs import DEFAULT_ROLE
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.image import ImageIdentifier, ImageRow, ImageStatus, rescan_images
from ai.backend.manager.models.kernel import AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES, kernels
from ai.backend.manager.models.keypair import keypairs
from ai.backend.manager.models.session import KernelLoadingStrategy, SessionRow
from ai.backend.manager.models.session_template import session_templates
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.services.session.actions.commit_session import (
    CommitSessionAction,
    CommitSessionActionResult,
)
from ai.backend.manager.services.session.actions.complete import (
    CompleteAction,
    CompleteActionResult,
)
from ai.backend.manager.services.session.actions.convert_session_to_image import (
    ConvertSessionToImageAction,
    ConvertSessionToImageActionResult,
)
from ai.backend.manager.services.session.actions.create_cluster import (
    CreateClusterAction,
    CreateClusterActionResult,
)
from ai.backend.manager.services.session.actions.create_from_params import (
    CreateFromParamsAction,
    CreateFromParamsActionResult,
)
from ai.backend.manager.types import UserScope
from ai.backend.manager.utils import query_userinfo

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore


@attrs.define(slots=True, auto_attribs=True, init=False)
class PrivateContext:
    agent_lost_checker: asyncio.Task[None]
    stats_task: asyncio.Task[None]
    database_ptask_group: aiotools.PersistentTaskGroup
    rpc_ptask_group: aiotools.PersistentTaskGroup
    webhook_ptask_group: aiotools.PersistentTaskGroup


@catch_unexpected(log)
async def check_agent_lost(
    local_config: LocalConfig,
    event_producer: EventProducer,
    redis_live: RedisConnectionInfo,
    interval: float,
) -> None:
    try:
        now = datetime.now(tzutc())
        timeout = timedelta(seconds=local_config["manager"]["heartbeat-timeout"])

        async def _check_impl(r: Redis):
            async for agent_id, prev in r.hscan_iter("agent.last_seen"):
                prev = datetime.fromtimestamp(float(prev), tzutc())
                if now - prev > timeout:
                    await event_producer.produce_event(
                        AgentTerminatedEvent("agent-lost"), source=agent_id.decode()
                    )

        await redis_helper.execute(redis_live, _check_impl)
    except asyncio.CancelledError:
        pass


@catch_unexpected(log)
async def report_stats(
    db: ExtendedAsyncSAEngine,
    stats_monitor: StatsPluginContext,
    registry: AgentRegistry,
    interval: float,
) -> None:
    try:
        stats_monitor = stats_monitor
        await stats_monitor.report_metric(
            GAUGE, "ai.backend.manager.coroutines", len(asyncio.all_tasks())
        )

        all_inst_ids = [inst_id async for inst_id in registry.enumerate_instances()]
        await stats_monitor.report_metric(
            GAUGE, "ai.backend.manager.agent_instances", len(all_inst_ids)
        )

        async with db.begin_readonly() as conn:
            query = (
                sa.select([sa.func.count()])
                .select_from(kernels)
                .where(
                    (kernels.c.cluster_role == DEFAULT_ROLE)
                    & (kernels.c.status.in_(AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES)),
                )
            )
            n = await conn.scalar(query)
            await stats_monitor.report_metric(GAUGE, "ai.backend.manager.active_kernels", n)
            subquery = (
                sa.select([sa.func.count()])
                .select_from(keypairs)
                .where(keypairs.c.is_active == true())
                .group_by(keypairs.c.user_id)
            )
            query = sa.select([sa.func.count()]).select_from(subquery.alias())
            n = await conn.scalar(query)
            await stats_monitor.report_metric(GAUGE, "ai.backend.users.has_active_key", n)

            subquery = subquery.where(keypairs.c.last_used != null())
            query = sa.select([sa.func.count()]).select_from(subquery.alias())
            n = await conn.scalar(query)
            await stats_monitor.report_metric(GAUGE, "ai.backend.users.has_used_key", n)

            """
            query = sa.select([sa.func.count()]).select_from(usage)
            n = await conn.scalar(query)
            await stats_monitor.report_metric(
                GAUGE, 'ai.backend.manager.accum_kernels', n)
            """
    except (sa.exc.InterfaceError, ConnectionRefusedError):
        log.warning("report_stats(): error while connecting to PostgreSQL server")


class SessionService:
    _db: ExtendedAsyncSAEngine
    _agent_registry: AgentRegistry
    _redis_live: RedisConnectionInfo
    _local_config: LocalConfig
    _stats_monitor: StatsPluginContext
    _app_ctx: PrivateContext
    _event_producer: EventProducer
    _background_task_manager: BackgroundTaskManager
    _error_monitor: ErrorPluginContext

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        agent_registry: AgentRegistry,
        redis_live: RedisConnectionInfo,
        local_config: LocalConfig,
        stats_monitor: StatsPluginContext,
        event_producer: EventProducer,
        background_task_manager: BackgroundTaskManager,
        error_monitor: ErrorPluginContext,
    ) -> None:
        self._db = db
        self._agent_registry = agent_registry
        self._redis_live = redis_live
        self._local_config = local_config
        self._stats_monitor = stats_monitor
        self._event_producer = event_producer
        self._background_task_manager = background_task_manager
        self._error_monitor = error_monitor
        self.init_app_ctx()

    def init_app_ctx(self) -> None:
        app_ctx: PrivateContext = PrivateContext()
        app_ctx.database_ptask_group = aiotools.PersistentTaskGroup()
        app_ctx.rpc_ptask_group = aiotools.PersistentTaskGroup()
        app_ctx.webhook_ptask_group = aiotools.PersistentTaskGroup()

        # Scan ALIVE agents
        app_ctx.agent_lost_checker = aiotools.create_timer(
            functools.partial(
                check_agent_lost, self._local_config, self._event_producer, self._redis_live
            ),
            1.0,
        )
        app_ctx.agent_lost_checker.set_name("agent_lost_checker")
        app_ctx.stats_task = aiotools.create_timer(
            functools.partial(report_stats, self._db, self._stats_monitor, self._agent_registry),
            5.0,
        )
        app_ctx.stats_task.set_name("stats_task")
        self.app_ctx = app_ctx

    async def commit_session(self, action: CommitSessionAction) -> CommitSessionActionResult:
        session_name = action.session_name
        owner_access_key = action.owner_access_key
        filename = action.filename

        myself = asyncio.current_task()
        assert myself is not None

        try:
            async with self._db.begin_readonly_session() as db_sess:
                session = await SessionRow.get_session(
                    db_sess,
                    session_name,
                    owner_access_key,
                    kernel_loading_strategy=KernelLoadingStrategy.MAIN_KERNEL_ONLY,
                )

            resp: Mapping[str, Any] = await asyncio.shield(
                self._app_ctx.rpc_ptask_group.create_task(
                    self._agent_registry.commit_session_to_file(session, filename),
                ),
            )
        except BackendError:
            log.exception("COMMIT_SESSION: exception")
            raise

        return CommitSessionActionResult(
            session_row=session,
            commit_result=resp,
        )

    async def complete(self, action: CompleteAction) -> CompleteActionResult:
        session_name = action.session_name
        owner_access_key = action.owner_access_key
        code = action.code
        options = action.options or {}

        resp = {
            "result": {
                "status": "finished",
                "completions": [],
            },
        }
        async with self._db.begin_readonly_session() as db_sess:
            session = await SessionRow.get_session(
                db_sess,
                session_name,
                owner_access_key,
                kernel_loading_strategy=KernelLoadingStrategy.MAIN_KERNEL_ONLY,
            )
        try:
            await self._agent_registry.increment_session_usage(session)
            resp["result"] = cast(
                Dict[str, Any],
                await self._agent_registry.get_completions(session, code, opts=options),
            )
        except AssertionError:
            raise InvalidAPIParameters
        except BackendError:
            log.exception("COMPLETE: exception")
            raise
        return CompleteActionResult(
            session_row=session,
            result=resp,
        )

    async def convert_session_to_image(
        self, action: ConvertSessionToImageAction
    ) -> ConvertSessionToImageActionResult:
        session_name = action.session_name
        owner_access_key = action.owner_access_key
        image_name = action.image_name
        image_visibility = action.image_visibility
        image_owner_id = action.image_owner_id

        myself = asyncio.current_task()
        assert myself is not None

        if image_visibility != CustomizedImageVisibilityScope.USER:
            raise InvalidAPIParameters(f"Unsupported visibility scope {image_visibility}")

        async with self._db.begin_readonly_session() as db_sess:
            session = await SessionRow.get_session(
                db_sess,
                session_name,
                owner_access_key,
                kernel_loading_strategy=KernelLoadingStrategy.MAIN_KERNEL_ONLY,
                eager_loading_op=[selectinload(SessionRow.group)],
            )

        project: GroupRow = session.group
        if not project.container_registry:
            raise InvalidAPIParameters(
                "Project not ready to convert session image (registry configuration not populated)"
            )

        registry_hostname = project.container_registry["registry"]
        registry_project = project.container_registry["project"]

        async with self._db.begin_readonly_session() as db_session:
            query = (
                sa.select(ContainerRegistryRow)
                .where(
                    (ContainerRegistryRow.registry_name == registry_hostname)
                    & (ContainerRegistryRow.project == registry_project)
                )
                .options(
                    load_only(
                        ContainerRegistryRow.url,
                        ContainerRegistryRow.username,
                        ContainerRegistryRow.password,
                        ContainerRegistryRow.project,
                    )
                )
            )

            registry_conf = cast(ContainerRegistryRow | None, await db_session.scalar(query))

            if not registry_conf:
                raise InvalidAPIParameters(
                    f"Project {registry_project} not found in registry {registry_hostname}."
                )

        async with self._db.begin_readonly_session() as db_sess:
            image_row = await ImageRow.resolve(
                db_sess,
                [ImageIdentifier(session.main_kernel.image, session.main_kernel.architecture)],
            )

        base_image_ref = image_row.image_ref

        async def _commit_and_upload(reporter: ProgressReporter) -> None:
            reporter.total_progress = 3
            await reporter.update(message="Commit started")
            try:
                # remove any existing customized related tag from base canonical
                filtered_tag_set = [
                    x for x in base_image_ref.tag.split("-") if not x.startswith("customized_")
                ]

                if base_image_ref.name == "":
                    new_name = base_image_ref.project
                else:
                    new_name = base_image_ref.name

                new_canonical = f"{registry_hostname}/{registry_project}/{new_name}:{'-'.join(filtered_tag_set)}"

                async with self._db.begin_readonly_session() as sess:
                    # check if user has passed its limit of customized image count
                    query = (
                        sa.select([sa.func.count()])
                        .select_from(ImageRow)
                        .where(
                            (
                                ImageRow.labels["ai.backend.customized-image.owner"].as_string()
                                == f"{image_visibility.value}:{image_owner_id}"
                            )
                        )
                        .where(ImageRow.status == ImageStatus.ALIVE)
                    )
                    existing_image_count = await sess.scalar(query)

                    customized_image_count_limit = action.max_customized_image_count
                    if customized_image_count_limit <= existing_image_count:
                        raise QuotaExceeded(
                            extra_msg="You have reached your customized image count quota",
                            extra_data={
                                "limit": customized_image_count_limit,
                                "current": existing_image_count,
                            },
                        )

                    # check if image with same name exists and reuse ID it if is
                    query = sa.select(ImageRow).where(
                        sa.and_(
                            ImageRow.name.like(f"{new_canonical}%"),
                            ImageRow.labels["ai.backend.customized-image.owner"].as_string()
                            == f"{image_visibility.value}:{image_owner_id}",
                            ImageRow.labels["ai.backend.customized-image.name"].as_string()
                            == image_name,
                            ImageRow.status == ImageStatus.ALIVE,
                        )
                    )
                    existing_row = await sess.scalar(query)

                    customized_image_id: str
                    if existing_row:
                        customized_image_id = existing_row.labels["ai.backend.customized-image.id"]
                        log.debug("reusing existing customized image ID {}", customized_image_id)
                    else:
                        customized_image_id = str(uuid.uuid4())

                new_canonical += f"-customized_{customized_image_id.replace('-', '')}"
                new_image_ref = ImageRef.from_image_str(
                    new_canonical,
                    None,
                    registry_hostname,
                    architecture=base_image_ref.architecture,
                    is_local=base_image_ref.is_local,
                )

                image_labels = {
                    "ai.backend.customized-image.owner": f"{image_visibility.value}:{image_owner_id}",
                    "ai.backend.customized-image.name": image_name,
                    "ai.backend.customized-image.id": customized_image_id,
                }
                match image_visibility:
                    case CustomizedImageVisibilityScope.USER:
                        image_labels["ai.backend.customized-image.user.email"] = action.user_email

                # commit image with new tag set
                resp = await self._agent_registry.commit_session(
                    session,
                    new_image_ref,
                    extra_labels=image_labels,
                )
                async for event, _ in self._background_task_manager.poll_bgtask_event(
                    uuid.UUID(resp["bgtask_id"])
                ):
                    match event:
                        case BgtaskDoneEvent():
                            await reporter.update(increment=1, message="Committed image")
                            break
                        case BgtaskFailedEvent():
                            raise BackendError(extra_msg=event.message)
                        case BgtaskCancelledEvent():
                            raise BackendError(extra_msg="Operation cancelled")

                if not new_image_ref.is_local:
                    # push image to registry from local agent
                    image_registry = ImageRegistry(
                        name=registry_hostname,
                        url=str(registry_conf.url),
                        username=registry_conf.username,
                        password=registry_conf.password,
                    )
                    resp = await self._agent_registry.push_image(
                        session.main_kernel.agent,
                        new_image_ref,
                        image_registry,
                    )
                    async for event, _ in self._background_task_manager.poll_bgtask_event(
                        uuid.UUID(resp["bgtask_id"])
                    ):
                        match event:
                            case BgtaskDoneEvent():
                                break
                            case BgtaskFailedEvent():
                                raise BackendError(extra_msg=event.message)
                            case BgtaskCancelledEvent():
                                raise BackendError(extra_msg="Operation cancelled")

                await reporter.update(increment=1, message="Pushed image to registry")
                # rescan updated image only
                await rescan_images(
                    self._db,
                    new_image_ref.canonical,
                    registry_project,
                    reporter=reporter,
                )
                await reporter.update(increment=1, message="Completed")
            except BackendError:
                log.exception("CONVERT_SESSION_TO_IMAGE: exception")
                raise

        task_id = await self._background_task_manager.start(_commit_and_upload)
        return ConvertSessionToImageActionResult(task_id=task_id, session_row=session)

    async def create_cluster(self, action: CreateClusterAction) -> CreateClusterActionResult:
        template_id = action.template_id
        user_id = action.user_id
        user_role = action.user_role
        sudo_session_enabled = action.sudo_session_enabled
        keypair_resource_policy = action.keypair_resource_policy
        requester_access_key = action.requester_access_key
        owner_access_key = action.owner_access_key
        domain_name = action.domain_name
        group_name = action.group_name
        scaling_group_name = action.scaling_group_name
        session_name = action.session_name
        session_type = action.session_type
        enqueue_only = action.enqueue_only
        max_wait_seconds = action.max_wait_seconds
        tag = action.tag

        async with self._db.begin_readonly() as conn:
            query = (
                sa.select([session_templates.c.template])
                .select_from(session_templates)
                .where(
                    (session_templates.c.id == template_id) & session_templates.c.is_active,
                )
            )
            template = await conn.scalar(query)
            log.debug("task template: {}", template)
            if not template:
                raise TaskTemplateNotFound

            try:
                _owner_uuid, group_id, resource_policy = await query_userinfo(
                    conn,
                    user_id,
                    requester_access_key,
                    user_role,
                    domain_name,
                    keypair_resource_policy,
                    domain_name,
                    group_name,
                    query_on_behalf_of=(
                        None if owner_access_key is undefined else owner_access_key
                    ),
                )

            except ValueError as e:
                raise InvalidAPIParameters(str(e))

        try:
            resp = await self._agent_registry.create_cluster(
                template,
                session_name,
                UserScope(
                    domain_name=domain_name,
                    group_id=group_id,
                    user_uuid=user_id,
                    user_role=user_role,
                ),
                owner_access_key,
                resource_policy,
                scaling_group_name,
                session_type,
                tag,
                enqueue_only=enqueue_only,
                max_wait_seconds=max_wait_seconds,
                sudo_session_enabled=sudo_session_enabled,
            )
            return CreateClusterActionResult(result=resp, session_id=resp["kernelId"])
        except TooManySessionsMatched:
            raise SessionAlreadyExists
        except BackendError:
            log.exception("GET_OR_CREATE: exception")
            raise
        except UnknownImageReference:
            raise UnknownImageReferenceError("Unknown image reference!")
        except Exception:
            await self._error_monitor.capture_exception()
            log.exception("GET_OR_CREATE: unexpected error!")
            raise InternalServerError

    async def create_from_params(
        self, action: CreateFromParamsAction
    ) -> CreateFromParamsActionResult:
        user_id = action.user_id
        user_role = action.user_role
        sudo_session_enabled = action.sudo_session_enabled
        keypair_resource_policy = action.keypair_resource_policy
        requester_access_key = action.requester_access_key
        owner_access_key = action.owner_access_key
        domain_name = action.domain_name
        group_name = action.group_name
        config = action.config
        cluster_size = action.cluster_size
        cluster_mode = action.cluster_mode
        session_name = action.session_name
        session_type = action.session_type
        enqueue_only = action.enqueue_only
        max_wait_seconds = action.max_wait_seconds
        tag = action.tag
        image = action.image
        architecture = action.architecture
        priority = action.priority
        bootstrap_script = action.bootstrap_script
        dependencies = action.dependencies
        startup_command = action.startup_command
        starts_at = action.starts_at
        batch_timeout = action.batch_timeout
        callback_url = action.callback_url
        reuse_if_exists = action.reuse_if_exists

        async with self._db.begin_readonly() as conn:
            owner_uuid, group_id, resource_policy = await query_userinfo(
                conn,
                user_id,
                requester_access_key,
                user_role,
                domain_name,
                keypair_resource_policy,
                domain_name,
                group_name,
                query_on_behalf_of=(None if owner_access_key is undefined else owner_access_key),
            )

        try:
            async with self._db.begin_session() as session:
                image_row = await ImageRow.resolve(
                    session,
                    [
                        ImageIdentifier(
                            image,
                            architecture,
                        ),
                        ImageAlias(image),
                    ],
                )

            resp = await self._agent_registry.create_session(
                session_name,
                image_row.image_ref,
                UserScope(
                    domain_name=domain_name,
                    group_id=group_id,
                    user_uuid=user_id,
                    user_role=user_role,
                ),
                owner_access_key,
                resource_policy,
                session_type,
                config,
                cluster_mode,
                cluster_size,
                reuse=reuse_if_exists,
                priority=priority,
                enqueue_only=enqueue_only,
                max_wait_seconds=max_wait_seconds,
                bootstrap_script=bootstrap_script,
                dependencies=dependencies,
                startup_command=startup_command,
                starts_at_timestamp=starts_at,
                batch_timeout=batch_timeout,
                tag=tag,
                callback_url=callback_url,
                sudo_session_enabled=sudo_session_enabled,
            )
            return CreateFromParamsActionResult(session_id=resp["sessionId"], result=resp)
        except UnknownImageReference:
            raise UnknownImageReferenceError(f"Unknown image reference: {image}")
        except BackendError:
            log.exception("GET_OR_CREATE: exception")
            raise
        except Exception:
            await self._error_monitor.capture_exception(context={"user": owner_uuid})
            log.exception("GET_OR_CREATE: unexpected error!")
            raise InternalServerError
