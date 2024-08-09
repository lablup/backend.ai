from __future__ import annotations

import asyncio
import hashlib
import itertools
import json
import logging
import uuid
from contextvars import ContextVar
from datetime import datetime, timedelta
from decimal import Decimal
from functools import partial
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Final,
    List,
    Optional,
    Sequence,
    Tuple,
    Union,
)

import aiotools
import async_timeout
import sqlalchemy as sa
from dateutil.tz import tzutc
from redis.asyncio import Redis
from redis.asyncio.client import Pipeline as RedisPipeline
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import noload, selectinload

from ai.backend.common import redis_helper
from ai.backend.common.defs import REDIS_LIVE_DB
from ai.backend.common.distributed import GlobalTimer
from ai.backend.common.events import (
    AgentStartedEvent,
    CoalescingOptions,
    DoPrepareEvent,
    DoScaleEvent,
    DoScheduleEvent,
    DoUpdateSessionStatusEvent,
    EventDispatcher,
    EventProducer,
    KernelLifecycleEventReason,
    RouteCreatedEvent,
    SessionCancelledEvent,
    SessionEnqueuedEvent,
    SessionPreparingEvent,
    SessionScheduledEvent,
    SessionTerminatedEvent,
)
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.plugin.hook import PASSED, HookResult
from ai.backend.common.types import (
    AgentId,
    ClusterMode,
    RedisConnectionInfo,
    ResourceSlot,
    RoundRobinState,
    SessionId,
    aobject,
)
from ai.backend.manager.models.session import _build_session_fetch_query
from ai.backend.manager.types import DistributedLockFactory
from ai.backend.plugin.entrypoint import scan_entrypoints

from ..api.exceptions import (
    GenericBadRequest,
    GenericForbidden,
    InstanceNotAvailable,
    SessionNotFound,
)
from ..defs import SERVICE_MAX_RETRIES, LockID
from ..exceptions import convert_to_status_data
from ..models import (
    AgentRow,
    AgentStatus,
    EndpointLifecycle,
    EndpointRow,
    KernelRow,
    KernelStatus,
    RouteStatus,
    RoutingRow,
    ScalingGroupOpts,
    ScalingGroupRow,
    SessionRow,
    SessionStatus,
    list_schedulable_agents_by_sgroup,
    recalc_agent_resource_occupancy,
    recalc_concurrency_used,
)
from ..models.utils import ExtendedAsyncSAEngine as SAEngine
from ..models.utils import execute_with_retry, sql_json_increment, sql_json_merge
from .predicates import (
    check_concurrency,
    check_dependencies,
    check_domain_resource_limit,
    check_group_resource_limit,
    check_keypair_resource_limit,
    check_pending_session_count_limit,
    check_pending_session_resource_limit,
    check_reserved_batch_session,
    check_user_resource_limit,
)
from .types import (
    AbstractScheduler,
    AgentAllocationContext,
    KernelAgentBinding,
    PendingSession,
    PredicateResult,
    SchedulingContext,
)

if TYPE_CHECKING:
    from ..config import LocalConfig, SharedConfig
    from ..registry import AgentRegistry

__all__ = (
    "load_scheduler",
    "SchedulerDispatcher",
)

log = BraceStyleAdapter(logging.getLogger("ai.backend.manager.scheduler"))

_log_fmt: ContextVar[str] = ContextVar("_log_fmt")
_log_args: ContextVar[Tuple[Any, ...]] = ContextVar("_log_args")

_key_schedule_prep_tasks: Final = "scheduler.preptasks"


def get_schedulable_group_id(agents: list[AgentRow]) -> str:
    return hashlib.md5("#".join(list(map(lambda agent: agent.id, agents))).encode()).hexdigest()


def load_scheduler(
    name: str,
    sgroup_opts: ScalingGroupOpts,
    scheduler_config: dict[str, Any],
) -> AbstractScheduler:
    entry_prefix = "backendai_scheduler_v10"
    for entrypoint in scan_entrypoints(entry_prefix):
        if entrypoint.name == name:
            log.debug('loading scheduler plugin "{}" from {}', name, entrypoint.module)
            scheduler_cls = entrypoint.load()
            return scheduler_cls(sgroup_opts, scheduler_config)
    raise ImportError("Cannot load the scheduler plugin", name)


StartTaskArgs = Tuple[
    Tuple[Any, ...],
    SchedulingContext,
    Tuple[PendingSession, List[KernelAgentBinding]],
    List[Tuple[str, Union[Exception, PredicateResult]]],
]


class SchedulerDispatcher(aobject):
    config: LocalConfig
    shared_config: SharedConfig
    registry: AgentRegistry
    db: SAEngine

    event_dispatcher: EventDispatcher
    event_producer: EventProducer
    schedule_timer: GlobalTimer
    prepare_timer: GlobalTimer
    scale_timer: GlobalTimer

    redis_live: RedisConnectionInfo

    def __init__(
        self,
        local_config: LocalConfig,
        shared_config: SharedConfig,
        event_dispatcher: EventDispatcher,
        event_producer: EventProducer,
        lock_factory: DistributedLockFactory,
        registry: AgentRegistry,
    ) -> None:
        self.local_config = local_config
        self.shared_config = shared_config
        self.event_dispatcher = event_dispatcher
        self.event_producer = event_producer
        self.registry = registry
        self.lock_factory = lock_factory
        self.db = registry.db
        self.redis_live = redis_helper.get_redis_object(
            self.shared_config.data["redis"],
            name="scheduler.live",
            db=REDIS_LIVE_DB,
        )

    async def __ainit__(self) -> None:
        coalescing_opts: CoalescingOptions = {
            "max_wait": 0.5,
            "max_batch_size": 32,
        }
        # coalescing_opts = None
        evd = self.registry.event_dispatcher
        evd.consume(
            SessionEnqueuedEvent, None, self.schedule, coalescing_opts, name="dispatcher.enq"
        )
        evd.consume(
            SessionTerminatedEvent, None, self.schedule, coalescing_opts, name="dispatcher.term"
        )
        evd.consume(AgentStartedEvent, None, self.schedule)
        evd.consume(DoScheduleEvent, None, self.schedule, coalescing_opts)
        evd.consume(DoPrepareEvent, None, self.prepare)
        evd.consume(DoScaleEvent, None, self.scale_services)
        self.schedule_timer = GlobalTimer(
            self.lock_factory(LockID.LOCKID_SCHEDULE_TIMER, 10.0),
            self.event_producer,
            lambda: DoScheduleEvent(),
            interval=10.0,
            task_name="schedule_timer",
        )
        self.prepare_timer = GlobalTimer(
            self.lock_factory(LockID.LOCKID_PREPARE_TIMER, 10.0),
            self.event_producer,
            lambda: DoPrepareEvent(),
            interval=10.0,
            initial_delay=5.0,
            task_name="prepare_timer",
        )
        self.scale_timer = GlobalTimer(
            self.lock_factory(LockID.LOCKID_SCALE_TIMER, 10.0),
            self.event_producer,
            lambda: DoScaleEvent(),
            interval=10.0,
            initial_delay=7.0,
            task_name="scale_timer",
        )
        await self.schedule_timer.join()
        await self.prepare_timer.join()
        await self.scale_timer.join()
        log.info("Session scheduler started")

    async def close(self) -> None:
        async with aiotools.TaskGroup() as tg:
            tg.create_task(self.scale_timer.leave())
            tg.create_task(self.prepare_timer.leave())
            tg.create_task(self.schedule_timer.leave())
        await self.redis_live.close()
        log.info("Session scheduler stopped")

    async def schedule(
        self,
        context: None,
        source: AgentId,
        event: SessionEnqueuedEvent | SessionTerminatedEvent | AgentStartedEvent | DoScheduleEvent,
    ) -> None:
        """
        Trigger the scheduler to scan pending sessions and mark them scheduled if they fulfill
        the scheduling requirements.

        HoL blocking issue due to indefinitely preparing sessions will be mitigated because
        they will be treated as already "scheduled" sessions and the scheduler will continue to
        work on other pending sessions.

        Session status transition: PENDING -> SCHEDULED
        """
        log.debug("schedule(): triggered")
        manager_id = self.local_config["manager"]["id"]
        redis_key = f"manager.{manager_id}.schedule"

        def _pipeline(r: Redis) -> RedisPipeline:
            pipe = r.pipeline()
            pipe.delete(redis_key)
            pipe.hset(
                redis_key,
                mapping={
                    "trigger_event": event.__class__.name,
                    "execution_time": datetime.now(tzutc()).isoformat(),
                },
            )
            return pipe

        await redis_helper.execute(
            self.redis_live,
            _pipeline,
        )
        known_slot_types = await self.shared_config.get_resource_slots()
        sched_ctx = SchedulingContext(
            registry=self.registry,
            known_slot_types=known_slot_types,
        )

        try:
            # The schedule() method should be executed with a global lock
            # as its individual steps are composed of many short-lived transactions.
            async with self.lock_factory(LockID.LOCKID_SCHEDULE, 60):
                async with self.db.begin_readonly_session() as db_sess:
                    # query = (
                    #     sa.select(ScalingGroupRow)
                    #     .join(ScalingGroupRow.agents.and_(AgentRow.status == AgentStatus.ALIVE))
                    # )
                    query = (
                        sa.select(AgentRow.scaling_group)
                        .where(AgentRow.status == AgentStatus.ALIVE)
                        .group_by(AgentRow.scaling_group)
                    )
                    result = await db_sess.execute(query)
                    schedulable_scaling_groups = [row.scaling_group for row in result.fetchall()]
                for sgroup_name in schedulable_scaling_groups:
                    try:
                        await self._schedule_in_sgroup(
                            sched_ctx,
                            sgroup_name,
                        )
                        await redis_helper.execute(
                            self.redis_live,
                            lambda r: r.hset(
                                redis_key,
                                "resource_group",
                                sgroup_name,
                            ),
                        )
                    except Exception as e:
                        log.exception("schedule({}): scheduling error!\n{}", sgroup_name, repr(e))
                await redis_helper.execute(
                    self.redis_live,
                    lambda r: r.hset(
                        redis_key,
                        "finish_time",
                        datetime.now(tzutc()).isoformat(),
                    ),
                )
        except DBAPIError as e:
            if getattr(e.orig, "pgcode", None) == "55P03":
                log.info(
                    "schedule(): cancelled due to advisory lock timeout; "
                    "maybe another schedule() call is still running"
                )
                raise asyncio.CancelledError()
            raise

    async def _load_scheduler(
        self,
        db_sess: SASession,
        sgroup_name: str,
    ) -> AbstractScheduler:
        query = sa.select(ScalingGroupRow.scheduler, ScalingGroupRow.scheduler_opts).where(
            ScalingGroupRow.name == sgroup_name
        )
        result = await db_sess.execute(query)
        row = result.first()
        scheduler_name = row.scheduler
        sgroup_opts: ScalingGroupOpts = row.scheduler_opts
        global_scheduler_opts = {}
        if self.shared_config["plugins"]["scheduler"]:
            global_scheduler_opts = self.shared_config["plugins"]["scheduler"].get(
                scheduler_name, {}
            )
        scheduler_specific_config = {**global_scheduler_opts, **sgroup_opts.config}
        return load_scheduler(scheduler_name, sgroup_opts, scheduler_specific_config)

    async def _schedule_in_sgroup(
        self,
        sched_ctx: SchedulingContext,
        sgroup_name: str,
    ) -> None:
        async def _apply_cancellation(
            db_sess: SASession, session_ids: list[SessionId], reason="pending-timeout"
        ):
            now = datetime.now(tzutc())
            kernel_query = (
                sa.update(KernelRow)
                .values(
                    status=KernelStatus.CANCELLED,
                    status_info=reason,
                    terminated_at=now,
                    status_history=sql_json_merge(
                        KernelRow.status_history,
                        (),
                        {
                            KernelStatus.CANCELLED.name: now.isoformat(),
                        },
                    ),
                )
                .where(KernelRow.session_id.in_(session_ids))
            )
            await db_sess.execute(kernel_query)
            query = (
                sa.update(SessionRow)
                .values(
                    status=SessionStatus.CANCELLED,
                    status_info=reason,
                    terminated_at=now,
                    status_history=sql_json_merge(
                        SessionRow.status_history,
                        (),
                        {
                            SessionStatus.CANCELLED.name: now.isoformat(),
                        },
                    ),
                )
                .where(SessionRow.id.in_(session_ids))
            )
            await db_sess.execute(query)

        async with self.db.begin_readonly_session() as db_sess:
            scheduler = await self._load_scheduler(db_sess, sgroup_name)
            existing_sessions, pending_sessions, cancelled_sessions = await _list_managed_sessions(
                db_sess, sgroup_name, scheduler.sgroup_opts.pending_timeout
            )

        if cancelled_sessions:
            session_ids = [item.id for item in cancelled_sessions]

            async def _update():
                async with self.db.begin_session() as db_sess:
                    await _apply_cancellation(db_sess, session_ids)

            await execute_with_retry(_update)
            for item in cancelled_sessions:
                await self.event_producer.produce_event(
                    SessionCancelledEvent(
                        item.id,
                        item.creation_id,
                        reason=KernelLifecycleEventReason.PENDING_TIMEOUT,
                    ),
                )

        log.debug(
            "running scheduler (sgroup:{}, pending:{}, existing:{}, cancelled:{})",
            sgroup_name,
            len(pending_sessions),
            len(existing_sessions),
            len(cancelled_sessions),
        )
        zero = ResourceSlot()
        num_scheduled = 0
        while len(pending_sessions) > 0:
            async with self.db.begin_readonly_session() as db_sess:
                candidate_agents = await list_schedulable_agents_by_sgroup(db_sess, sgroup_name)
            total_capacity = sum((ag.available_slots for ag in candidate_agents), zero)

            picked_session_id = scheduler.pick_session(
                total_capacity,
                pending_sessions,
                existing_sessions,
            )
            if picked_session_id is None:
                # no session is picked.
                # continue to next sgroup.
                return
            for picked_idx, sess_ctx in enumerate(pending_sessions):
                if sess_ctx.id == picked_session_id:
                    break
            else:
                # no matching entry for picked session?
                raise RuntimeError("should not reach here")
            sess_ctx = pending_sessions.pop(picked_idx)
            log_fmt = "schedule(s:{}, type:{}, name:{}, ak:{}, cluster_mode:{}): "
            log_args = (
                sess_ctx.id,
                sess_ctx.session_type,
                sess_ctx.name,
                sess_ctx.access_key,
                sess_ctx.cluster_mode,
            )
            _log_fmt.set(log_fmt)
            _log_args.set(log_args)
            log.debug(log_fmt + "try-scheduling", *log_args)

            async def _check_predicates() -> List[Tuple[str, Union[Exception, PredicateResult]]]:
                check_results: List[Tuple[str, Union[Exception, PredicateResult]]] = []
                async with self.db.begin_session() as db_sess:
                    predicates: list[Tuple[str, Awaitable[PredicateResult]]] = [
                        (
                            "reserved_time",
                            check_reserved_batch_session(db_sess, sched_ctx, sess_ctx),
                        ),
                        ("dependencies", check_dependencies(db_sess, sched_ctx, sess_ctx)),
                        ("concurrency", check_concurrency(db_sess, sched_ctx, sess_ctx)),
                    ]
                    if not sess_ctx.is_private:
                        predicates += [
                            (
                                "pending_session_resource_limit",
                                check_pending_session_resource_limit(db_sess, sched_ctx, sess_ctx),
                            ),
                            (
                                "pending_session_count_limit",
                                check_pending_session_count_limit(db_sess, sched_ctx, sess_ctx),
                            ),
                            (
                                "keypair_resource_limit",
                                check_keypair_resource_limit(db_sess, sched_ctx, sess_ctx),
                            ),
                            (
                                "user_resource_limit",
                                check_user_resource_limit(db_sess, sched_ctx, sess_ctx),
                            ),
                            (
                                "user_group_resource_limit",
                                check_group_resource_limit(db_sess, sched_ctx, sess_ctx),
                            ),
                            (
                                "domain_resource_limit",
                                check_domain_resource_limit(db_sess, sched_ctx, sess_ctx),
                            ),
                        ]
                    for predicate_name, check_coro in predicates:
                        try:
                            check_results.append((predicate_name, await check_coro))
                        except DBAPIError:
                            raise
                        except Exception as e:
                            log.exception(log_fmt + "predicate-error", *log_args)
                            check_results.append((predicate_name, e))
                return check_results

            check_results = await execute_with_retry(_check_predicates)
            failed_predicates = []
            passed_predicates = []
            for predicate_name, result in check_results:
                if isinstance(result, Exception):
                    failed_predicates.append({
                        "name": predicate_name,
                        "msg": repr(result),
                    })
                    continue
                if result.passed:
                    passed_predicates.append({
                        "name": predicate_name,
                    })
                else:
                    failed_predicates.append({
                        "name": predicate_name,
                        "msg": result.message or "",
                    })

            async def _check_predicates_hook() -> HookResult:
                async with self.db.begin_readonly_session() as db_sess:
                    return await self.registry.hook_plugin_ctx.dispatch(
                        "PREDICATE",
                        (
                            db_sess,
                            sched_ctx,
                            sess_ctx,
                        ),
                    )

            hook_result = await execute_with_retry(_check_predicates_hook)
            match hook_result.src_plugin:
                case str():
                    hook_name = hook_result.src_plugin
                case list():
                    hook_name = f"({', '.join(hook_result.src_plugin)})"
                case _:
                    hook_name = ""

            if hook_result.status == PASSED:
                if hook_result.src_plugin:
                    # Append result only when plugin exists.
                    passed_predicates.append({"name": hook_name})
            else:
                failed_predicates.append({
                    "name": hook_name,
                    "msg": hook_result.reason or "",
                })

            status_update_data = {
                "last_try": datetime.now(tzutc()).isoformat(),
                "failed_predicates": failed_predicates,
                "passed_predicates": passed_predicates,
            }
            if failed_predicates:
                log.debug(log_fmt + "predicate-checks-failed (temporary)", *log_args)

                async def _cancel_failed_system_session() -> None:
                    async with self.db.begin_session() as db_sess:
                        await _rollback_predicate_mutations(
                            db_sess,
                            sched_ctx,
                            sess_ctx,
                        )
                        query = (
                            sa.update(SessionRow)
                            .values(
                                status_info="predicate-checks-failed",
                                status_data=sql_json_increment(
                                    SessionRow.status_data,
                                    ("scheduler", "retries"),
                                    parent_updates=status_update_data,
                                ),
                            )
                            .where(SessionRow.id == sess_ctx.id)
                        )
                        await db_sess.execute(query)
                        if sess_ctx.is_private:
                            await _apply_cancellation(db_sess, [sess_ctx.id])
                            await self.event_producer.produce_event(
                                SessionCancelledEvent(
                                    sess_ctx.id,
                                    sess_ctx.creation_id,
                                    reason=KernelLifecycleEventReason.PENDING_TIMEOUT,
                                )
                            )

                await execute_with_retry(_cancel_failed_system_session)
                # Predicate failures are *NOT* permanent errors.
                # We need to retry the scheduling afterwards.
                continue
            else:

                async def _update_session_status_data() -> None:
                    async with self.db.begin_session() as db_sess:
                        kernel_query = (
                            sa.update(KernelRow)
                            .where(KernelRow.session_id == sess_ctx.id)
                            .values(
                                status_data=sql_json_merge(
                                    KernelRow.status_data,
                                    ("scheduler",),
                                    obj=status_update_data,
                                ),
                            )
                        )
                        await db_sess.execute(kernel_query)
                        session_query = (
                            sa.update(SessionRow)
                            .where(SessionRow.id == sess_ctx.id)
                            .values(
                                status_data=sql_json_merge(
                                    SessionRow.status_data,
                                    ("scheduler",),
                                    obj=status_update_data,
                                ),
                            )
                        )
                        await db_sess.execute(session_query)

                await execute_with_retry(_update_session_status_data)

            async with self.db.begin_readonly_session() as db_sess:
                schedulable_sess = await SessionRow.get_session_by_id(
                    db_sess,
                    sess_ctx.id,
                    eager_loading_op=(
                        noload("*"),
                        selectinload(SessionRow.kernels).options(
                            noload("*"),
                            selectinload(KernelRow.agent_row).noload("*"),
                        ),
                    ),
                )

            agent_selection_resource_priority = self.local_config["manager"][
                "agent-selection-resource-priority"
            ]

            try:
                match schedulable_sess.cluster_mode:
                    case ClusterMode.SINGLE_NODE:
                        await self._schedule_single_node_session(
                            sched_ctx,
                            scheduler,
                            sgroup_name,
                            candidate_agents,
                            schedulable_sess,
                            agent_selection_resource_priority,
                            check_results,
                        )
                    case ClusterMode.MULTI_NODE:
                        await self._schedule_multi_node_session(
                            sched_ctx,
                            scheduler,
                            sgroup_name,
                            candidate_agents,
                            schedulable_sess,
                            agent_selection_resource_priority,
                            check_results,
                        )
                    case _:
                        log.exception(
                            f"should not reach here; unknown cluster_mode: {schedulable_sess.cluster_mode}"
                        )
                        continue
            except InstanceNotAvailable as e:
                # Proceed to the next pending session and come back later.
                log.debug(
                    "schedule({}): instance not available ({})",
                    sgroup_name,
                    e.extra_msg,
                )
                continue
            except GenericBadRequest as e:
                # Proceed to the next pending session and come back later.
                log.debug(
                    "schedule({}): bad request ({})",
                    sgroup_name,
                    e.extra_msg,
                )
                continue
            except Exception:
                # _schedule_{single,multi}_node_session() already handle general exceptions.
                # Proceed to the next pending session and come back later
                continue
            num_scheduled += 1
        if num_scheduled > 0:
            await self.event_producer.produce_event(DoPrepareEvent())

    async def _filter_agent_by_container_limit(
        self, candidate_agents: list[AgentRow]
    ) -> list[AgentRow]:
        raw_value = await self.shared_config.etcd.get("config/agent/max-container-count")
        if raw_value is None:
            return candidate_agents
        max_container_count = int(raw_value)

        async def _pipe_builder(r: Redis) -> RedisPipeline:
            pipe = r.pipeline()
            for ag in candidate_agents:
                await pipe.get(f"container_count.{ag.id}")
            return pipe

        raw_counts = await redis_helper.execute(self.registry.redis_stat, _pipe_builder)

        def _check(cnt: str | None) -> bool:
            _cnt = int(cnt) if cnt is not None else 0
            return max_container_count > _cnt

        return [ag for ag, count in zip(candidate_agents, raw_counts) if _check(count)]

    async def _schedule_single_node_session(
        self,
        sched_ctx: SchedulingContext,
        scheduler: AbstractScheduler,
        sgroup_name: str,
        candidate_agents: Sequence[AgentRow],
        sess_ctx: SessionRow,
        agent_selection_resource_priority: list[str],
        check_results: List[Tuple[str, Union[Exception, PredicateResult]]],
    ) -> None:
        """
        Finds and assigns an agent having resources enough to host the entire session.
        """
        log_fmt = _log_fmt.get("")
        log_args = _log_args.get(tuple())

        try:
            requested_architectures = set(k.architecture for k in sess_ctx.kernels)
            if len(requested_architectures) > 1:
                raise GenericBadRequest(
                    "Cannot assign multiple kernels with different architectures' single node session",
                )
            if not sess_ctx.kernels:
                raise GenericBadRequest(
                    f"The session {sess_ctx.id!r} does not have any child kernel."
                )
            requested_architecture = requested_architectures.pop()
            compatible_candidate_agents = [
                ag for ag in candidate_agents if ag.architecture == requested_architecture
            ]
            if not candidate_agents:
                raise InstanceNotAvailable(extra_msg="No agents are available for scheduling")
            if not compatible_candidate_agents:
                raise InstanceNotAvailable(
                    extra_msg=(
                        "No agents found to be compatible with the image architecture "
                        f"(image[0]: {sess_ctx.main_kernel.image_ref}, "
                        f"arch: {requested_architecture})"
                    ),
                )
            available_candidate_agents = await self._filter_agent_by_container_limit(
                compatible_candidate_agents
            )
            if not available_candidate_agents:
                raise InstanceNotAvailable(
                    extra_msg=(
                        "No agents found to be available because all agents have reached the hard"
                        " limit of the number of containers."
                    ),
                )

            # If sess_ctx.agent_id is already set for manual assignment by superadmin,
            # skip assign_agent_for_session().
            agent = sess_ctx.main_kernel.agent_row
            agent_id: AgentId | None = None
            if agent is not None:
                agent_id = agent.id

                async with self.db.begin_session() as db_sess:
                    result = (
                        await db_sess.execute(
                            sa.select([AgentRow.available_slots, AgentRow.occupied_slots]).where(
                                AgentRow.id == agent_id
                            )
                        )
                    ).fetchall()[0]

                if result is None:
                    raise GenericBadRequest(f"No such agent exist in DB: {agent_id}")

                available_slots, occupied_slots = result

                for key in available_slots.keys():
                    if (
                        available_slots[key] - occupied_slots.get(key, Decimal("0"))
                        >= sess_ctx.requested_slots[key]
                    ):
                        continue
                    else:
                        raise InstanceNotAvailable(
                            extra_msg=(
                                f"The designated agent ({agent_id}) does not have "
                                f"the enough remaining capacity ({key}, "
                                f"requested: {sess_ctx.requested_slots[key]}, "
                                f"remaining: {available_slots[key] - occupied_slots[key]})."
                            ),
                        )

            else:
                sorted_agents = sorted(compatible_candidate_agents, key=lambda agent: agent.id)

                if scheduler.sgroup_opts.roundrobin:
                    rr_state: (
                        RoundRobinState | None
                    ) = await sched_ctx.registry.shared_config.get_roundrobin_state(
                        sgroup_name, requested_architecture
                    )

                    if rr_state is not None:
                        schedulable_group_id = get_schedulable_group_id(sorted_agents)

                        if schedulable_group_id == rr_state.schedulable_group_id:
                            for i in range(len(sorted_agents)):
                                idx = (rr_state.next_index + i) % len(sorted_agents)
                                agent = sorted_agents[idx]

                                if (
                                    agent.available_slots - agent.occupied_slots
                                    > sess_ctx.requested_slots
                                ):
                                    agent_id = agent.id
                                    rr_state.next_index = (rr_state.next_index + i + 1) % len(
                                        sorted_agents
                                    )

                                    await sched_ctx.registry.shared_config.put_roundrobin_state(
                                        sgroup_name, requested_architecture, rr_state
                                    )
                                    break
                            else:
                                # fallback to the default behavior instead of raising an error for reducing code complexity
                                pass

                if agent_id is None:
                    # Let the scheduler check the resource availability and decide the target agent
                    cand_agent_id = scheduler.assign_agent_for_session(
                        compatible_candidate_agents,
                        sess_ctx,
                        scheduler.sgroup_opts.agent_selection_strategy,
                        agent_selection_resource_priority,
                    )
                    if cand_agent_id is None:
                        raise InstanceNotAvailable(
                            extra_msg=(
                                "Could not find a contiguous resource region in any agent big"
                                f" enough to host the session (id: {sess_ctx.id}, resource group:"
                                f" {sess_ctx.scaling_group_name})"
                            ),
                        )
                    agent_id = cand_agent_id

                    if scheduler.sgroup_opts.roundrobin:
                        await sched_ctx.registry.shared_config.put_roundrobin_state(
                            sgroup_name,
                            requested_architecture,
                            RoundRobinState(
                                schedulable_group_id=get_schedulable_group_id(
                                    sorted_agents,
                                ),
                                next_index=[
                                    (idx + 1) % len(sorted_agents)
                                    for idx, agent in enumerate(sorted_agents)
                                    if agent.id == agent_id
                                ][0],
                            ),
                        )

            async with self.db.begin_session() as agent_db_sess:
                agent_alloc_ctx = await _reserve_agent(
                    sched_ctx,
                    agent_db_sess,
                    sgroup_name,
                    agent_id,
                    sess_ctx.requested_slots,
                )
        except InstanceNotAvailable as sched_failure:
            log.debug(log_fmt + "no-available-instances", *log_args)

            async def _update_sched_failure(exc: InstanceNotAvailable) -> None:
                async with self.db.begin_session() as kernel_db_sess:
                    await _rollback_predicate_mutations(
                        kernel_db_sess,
                        sched_ctx,
                        sess_ctx,
                    )
                    query = (
                        sa.update(SessionRow)
                        .values(
                            status_info="no-available-instances",
                            status_data=sql_json_increment(
                                SessionRow.status_data,
                                ("scheduler", "retries"),
                                parent_updates={
                                    "last_try": datetime.now(tzutc()).isoformat(),
                                    "msg": exc.extra_msg,
                                },
                            ),
                        )
                        .where(SessionRow.id == sess_ctx.id)
                    )
                    await kernel_db_sess.execute(query)

            await execute_with_retry(partial(_update_sched_failure, sched_failure))
            raise
        except Exception as e:
            log.exception(
                log_fmt + "unexpected-error, during agent allocation",
                *log_args,
            )
            exc_data = convert_to_status_data(e, self.local_config["debug"]["enabled"])

            async def _update_generic_failure() -> None:
                async with self.db.begin_session() as kernel_db_sess:
                    await _rollback_predicate_mutations(
                        kernel_db_sess,
                        sched_ctx,
                        sess_ctx,
                    )
                    query = (
                        sa.update(SessionRow)
                        .values(
                            status_info="scheduler-error",
                            status_data=exc_data,
                        )
                        .where(SessionRow.id == sess_ctx.id)
                    )
                    await kernel_db_sess.execute(query)

            await execute_with_retry(_update_generic_failure)
            raise

        async def _finalize_scheduled() -> None:
            agent_ids: list[AgentId] = []
            async with self.db.begin_session() as db_sess:
                now = datetime.now(tzutc())
                for kernel in sess_ctx.kernels:
                    kernel_query = (
                        sa.update(KernelRow)
                        .values(
                            agent=agent_alloc_ctx.agent_id,
                            agent_addr=agent_alloc_ctx.agent_addr,
                            scaling_group=sgroup_name,
                            status=KernelStatus.SCHEDULED,
                            status_info="scheduled",
                            status_data={},
                            status_changed=now,
                            status_history=sql_json_merge(
                                KernelRow.status_history,
                                (),
                                {
                                    KernelStatus.SCHEDULED.name: now.isoformat(),
                                },
                            ),
                        )
                        .where(KernelRow.id == kernel.id)
                    )
                    await db_sess.execute(kernel_query)
                if agent_alloc_ctx.agent_id is not None:
                    agent_ids.append(agent_alloc_ctx.agent_id)

                session_query = (
                    sa.update(SessionRow)
                    .values(
                        scaling_group_name=sgroup_name,
                        agent_ids=agent_ids,
                        status=SessionStatus.SCHEDULED,
                        status_info="scheduled",
                        status_data={},
                        status_history=sql_json_merge(
                            SessionRow.status_history,
                            (),
                            {
                                SessionStatus.SCHEDULED.name: now.isoformat(),
                            },
                        ),
                    )
                    .where(SessionRow.id == sess_ctx.id)
                )
                await db_sess.execute(session_query)

        await execute_with_retry(_finalize_scheduled)
        await self.registry.event_producer.produce_event(
            SessionScheduledEvent(sess_ctx.id, sess_ctx.creation_id),
        )

    async def _schedule_multi_node_session(
        self,
        sched_ctx: SchedulingContext,
        scheduler: AbstractScheduler,
        sgroup_name: str,
        candidate_agents: Sequence[AgentRow],
        sess_ctx: SessionRow,
        agent_selection_resource_priority: list[str],
        check_results: List[Tuple[str, Union[Exception, PredicateResult]]],
    ) -> None:
        """
        Finds and assigns agents having resources enough to host each kernel in the session.
        """
        log_fmt = _log_fmt.get()
        log_args = _log_args.get()
        agent_query_extra_conds = None
        kernel_agent_bindings: List[KernelAgentBinding] = []
        async with self.db.begin_session() as agent_db_sess:
            # This outer transaction is rolled back when any exception occurs inside,
            # including scheduling failures of a kernel.
            # It ensures that occupied_slots are recovered when there are partial
            # scheduling failures.
            kernel: KernelRow
            for kernel in sess_ctx.kernels:
                agent_alloc_ctx: AgentAllocationContext | None = None
                try:
                    agent_id: Optional[AgentId] = None
                    agent: Optional[AgentRow] = kernel.agent_row
                    if agent is not None:
                        # Check the resource availability of the manually designated agent
                        result = (
                            await agent_db_sess.execute(
                                sa.select([
                                    AgentRow.available_slots,
                                    AgentRow.occupied_slots,
                                ]).where(AgentRow.id == agent.id)
                            )
                        ).fetchall()[0]

                        if result is None:
                            raise GenericBadRequest(f"No such agent exist in DB: {agent_id}")
                        available_slots, occupied_slots = result

                        for key in available_slots.keys():
                            if (
                                available_slots[key] - occupied_slots[key]
                                >= kernel.requested_slots[key]
                            ):
                                continue
                            else:
                                raise InstanceNotAvailable(
                                    extra_msg=(
                                        f"The designated agent ({agent.id}) does not have "
                                        f"the enough remaining capacity ({key}, "
                                        f"requested: {sess_ctx.requested_slots[key]}, "
                                        f"remaining: {available_slots[key] - occupied_slots[key]})."
                                    ),
                                )
                        agent_id = agent.id
                    else:
                        # Each kernel may have different images and different architectures
                        compatible_candidate_agents = [
                            ag for ag in candidate_agents if ag.architecture == kernel.architecture
                        ]
                        if not candidate_agents:
                            raise InstanceNotAvailable(
                                extra_msg="No agents are available for scheduling"
                            )
                        if not compatible_candidate_agents:
                            raise InstanceNotAvailable(
                                extra_msg=(
                                    "No agents found to be compatible with the image architecture "
                                    f"(image: {kernel.image_ref}, "
                                    f"arch: {kernel.architecture})"
                                ),
                            )
                        available_candidate_agents = await self._filter_agent_by_container_limit(
                            compatible_candidate_agents
                        )
                        if not available_candidate_agents:
                            raise InstanceNotAvailable(
                                extra_msg=(
                                    "No agents found to be available because all agents have"
                                    " reached the hard limit of the number of containers."
                                ),
                            )
                        # Let the scheduler check the resource availability and decide the target agent
                        agent_id = scheduler.assign_agent_for_kernel(
                            available_candidate_agents,
                            kernel,
                            scheduler.sgroup_opts.agent_selection_strategy,
                            agent_selection_resource_priority,
                        )
                        if agent_id is None:
                            raise InstanceNotAvailable(
                                extra_msg=(
                                    "Could not find a contiguous resource region in any agent big"
                                    f" enough to host a kernel in the session (id: {sess_ctx.id},"
                                    f" resource group: {sess_ctx.scaling_group_name})"
                                ),
                            )
                    assert agent_id is not None

                    async def _reserve() -> None:
                        nonlocal agent_alloc_ctx, candidate_agents
                        async with agent_db_sess.begin_nested():
                            agent_alloc_ctx = await _reserve_agent(
                                sched_ctx,
                                agent_db_sess,
                                sgroup_name,
                                agent_id,
                                kernel.requested_slots,
                                extra_conds=agent_query_extra_conds,
                            )
                            # Update the agent data to schedule the next kernel in the session
                            candidate_agents = await list_schedulable_agents_by_sgroup(
                                agent_db_sess,
                                sgroup_name,
                            )

                    await execute_with_retry(_reserve)
                except InstanceNotAvailable as sched_failure:
                    log.debug(log_fmt + "no-available-instances", *log_args)

                    async def _update_sched_failure(exc: InstanceNotAvailable) -> None:
                        async with self.db.begin_session() as agent_db_sess:
                            await _rollback_predicate_mutations(
                                agent_db_sess,
                                sched_ctx,
                                sess_ctx,
                            )
                            query = (
                                sa.update(KernelRow)
                                .values(
                                    status_info="no-available-instances",
                                    status_data=sql_json_increment(
                                        KernelRow.status_data,
                                        ("scheduler", "retries"),
                                        parent_updates={
                                            "last_try": datetime.now(tzutc()).isoformat(),
                                            "msg": exc.extra_msg,
                                        },
                                    ),
                                )
                                .where(KernelRow.id == kernel.id)
                            )
                            await agent_db_sess.execute(query)

                    await execute_with_retry(partial(_update_sched_failure, sched_failure))
                    raise
                except Exception as e:
                    log.exception(
                        log_fmt + "unexpected-error, during agent allocation",
                        *log_args,
                    )
                    exc_data = convert_to_status_data(e, self.local_config["debug"]["enabled"])

                    async def _update_generic_failure() -> None:
                        async with self.db.begin_session() as kernel_db_sess:
                            await _rollback_predicate_mutations(
                                kernel_db_sess,
                                sched_ctx,
                                sess_ctx,
                            )
                            query = (
                                sa.update(KernelRow)
                                .values(
                                    status_info="scheduler-error",
                                    status_data=exc_data,
                                )
                                .where(KernelRow.id == kernel.id)
                            )
                            await kernel_db_sess.execute(query)

                    await execute_with_retry(_update_generic_failure)
                    raise
                else:
                    assert agent_alloc_ctx is not None
                    kernel_agent_bindings.append(KernelAgentBinding(kernel, agent_alloc_ctx, set()))

        assert len(kernel_agent_bindings) == len(sess_ctx.kernels)
        # Proceed to PREPARING only when all kernels are successfully scheduled.

        async def _finalize_scheduled() -> None:
            agent_ids: list[AgentId] = []
            async with self.db.begin_session() as db_sess:
                for binding in kernel_agent_bindings:
                    now = datetime.now(tzutc())
                    kernel_query = (
                        sa.update(KernelRow)
                        .values(
                            agent=binding.agent_alloc_ctx.agent_id,
                            agent_addr=binding.agent_alloc_ctx.agent_addr,
                            scaling_group=sgroup_name,
                            status=KernelStatus.SCHEDULED,
                            status_info="scheduled",
                            status_data={},
                            status_changed=now,
                            status_history=sql_json_merge(
                                KernelRow.status_history,
                                (),
                                {
                                    KernelStatus.SCHEDULED.name: now.isoformat(),
                                },
                            ),
                        )
                        .where(KernelRow.id == binding.kernel.id)
                    )
                    await db_sess.execute(kernel_query)
                    if binding.agent_alloc_ctx.agent_id is not None:
                        agent_ids.append(binding.agent_alloc_ctx.agent_id)

                session_query = (
                    sa.update(SessionRow)
                    .values(
                        scaling_group_name=sgroup_name,
                        agent_ids=agent_ids,
                        status=SessionStatus.SCHEDULED,
                        status_info="scheduled",
                        status_data={},
                        # status_changed=now,
                        status_history=sql_json_merge(
                            SessionRow.status_history,
                            (),
                            {
                                SessionStatus.SCHEDULED.name: now.isoformat(),
                            },
                        ),
                    )
                    .where(SessionRow.id == sess_ctx.id)
                )
                await db_sess.execute(session_query)

        await execute_with_retry(_finalize_scheduled)
        await self.registry.event_producer.produce_event(
            SessionScheduledEvent(sess_ctx.id, sess_ctx.creation_id),
        )

    async def prepare(
        self,
        context: None,
        source: AgentId,
        event: DoPrepareEvent,
    ) -> None:
        """
        Scan the scheduled sessions and perform the agent RPC calls to begin preparation of them.
        Each RPC calls are done in separate asyncio tasks.

        Session status transition: SCHEDULED -> PREPARING
        """
        manager_id = self.local_config["manager"]["id"]
        redis_key = f"manager.{manager_id}.prepare"

        def _pipeline(r: Redis) -> RedisPipeline:
            pipe = r.pipeline()
            pipe.delete(redis_key)
            pipe.hset(
                redis_key,
                mapping={
                    "trigger_event": event.__class__.name,
                    "execution_time": datetime.now(tzutc()).isoformat(),
                },
            )
            return pipe

        await redis_helper.execute(
            self.redis_live,
            _pipeline,
        )
        known_slot_types = await self.shared_config.get_resource_slots()
        sched_ctx = SchedulingContext(
            self.registry,
            known_slot_types,
        )
        try:
            async with self.lock_factory(LockID.LOCKID_PREPARE, 600):
                now = datetime.now(tzutc())

                async def _mark_session_preparing() -> Sequence[SessionRow]:
                    async with self.db.begin_session() as db_sess:
                        update_query = (
                            sa.update(KernelRow)
                            .values(
                                status=KernelStatus.PREPARING,
                                status_changed=now,
                                status_info="",
                                status_data={},
                                status_history=sql_json_merge(
                                    KernelRow.status_history,
                                    (),
                                    {
                                        KernelStatus.PREPARING.name: now.isoformat(),
                                    },
                                ),
                            )
                            .where(
                                (KernelRow.status == KernelStatus.SCHEDULED),
                            )
                        )
                        await db_sess.execute(update_query)
                        update_sess_query = (
                            sa.update(SessionRow)
                            .values(
                                status=SessionStatus.PREPARING,
                                # status_changed=now,
                                status_info="",
                                status_data={},
                                status_history=sql_json_merge(
                                    SessionRow.status_history,
                                    (),
                                    {
                                        SessionStatus.PREPARING.name: now.isoformat(),
                                    },
                                ),
                            )
                            .where(SessionRow.status == SessionStatus.SCHEDULED)
                            .returning(SessionRow.id)
                        )
                        rows = (await db_sess.execute(update_sess_query)).fetchall()
                        if len(rows) == 0:
                            return []
                        target_session_ids = [r["id"] for r in rows]
                        select_query = (
                            sa.select(SessionRow)
                            .where(SessionRow.id.in_(target_session_ids))
                            .options(
                                noload("*"),
                                selectinload(SessionRow.kernels).noload("*"),
                            )
                        )
                        result = await db_sess.execute(select_query)
                        return result.scalars().all()

                scheduled_sessions: Sequence[SessionRow]
                scheduled_sessions = await execute_with_retry(_mark_session_preparing)
                log.debug("prepare(): preparing {} session(s)", len(scheduled_sessions))
                async with (
                    async_timeout.timeout(delay=50.0),
                    aiotools.PersistentTaskGroup() as tg,
                ):
                    for scheduled_session in scheduled_sessions:
                        await self.registry.event_producer.produce_event(
                            SessionPreparingEvent(
                                scheduled_session.id,
                                scheduled_session.creation_id,
                            ),
                        )
                        tg.create_task(
                            self.start_session(
                                sched_ctx,
                                scheduled_session,
                            )
                        )

                        await redis_helper.execute(
                            self.redis_live,
                            lambda r: r.hset(
                                redis_key, "resource_group", scheduled_session.scaling_group_name
                            ),
                        )
            await redis_helper.execute(
                self.redis_live,
                lambda r: r.hset(
                    redis_key,
                    "finish_time",
                    datetime.now(tzutc()).isoformat(),
                ),
            )
        except DBAPIError as e:
            if getattr(e.orig, "pgcode", None) == "55P03":
                log.info(
                    "prepare(): cancelled due to advisory lock timeout; "
                    "maybe another prepare() call is still running"
                )
                raise asyncio.CancelledError()
            raise
        except asyncio.TimeoutError:
            log.warning("prepare(): timeout while executing start_session()")

    async def scale_services(
        self,
        context: None,
        source: AgentId,
        event: DoScaleEvent,
    ) -> None:
        log.debug("scale_services(): triggered")
        # Altering inference sessions should only be done by invoking this method
        manager_id = self.local_config["manager"]["id"]
        redis_key = f"manager.{manager_id}.scale_services"

        def _pipeline(r: Redis) -> RedisPipeline:
            pipe = r.pipeline()
            pipe.delete(redis_key)
            pipe.hset(
                redis_key,
                mapping={
                    "trigger_event": event.__class__.name,
                    "execution_time": datetime.now(tzutc()).isoformat(),
                },
            )
            return pipe

        await redis_helper.execute(
            self.redis_live,
            _pipeline,
        )

        routes_to_destroy = []
        endpoints_to_expand: dict[EndpointRow, Any] = {}
        endpoints_to_mark_terminated: set[EndpointRow] = set()
        async with self.db.begin_session() as session:
            query = (
                sa.select(RoutingRow)
                .join(
                    RoutingRow.session_row.and_(
                        SessionRow.status.in_((SessionStatus.TERMINATED, SessionStatus.CANCELLED))
                    )
                )
                .where(RoutingRow.status.in_((RouteStatus.PROVISIONING, RouteStatus.TERMINATING)))
                .options(selectinload(RoutingRow.session_row))
            )
            result = await session.execute(query)
            zombie_routes = result.scalars().all()
            if len(zombie_routes) > 0:
                query = sa.delete(RoutingRow).where(
                    RoutingRow.id.in_([r.id for r in zombie_routes])
                )
                result = await session.execute(query)
                log.info("Cleared {} zombie routes", result.rowcount)

        async with self.db.begin_readonly_session() as session:
            endpoints = await EndpointRow.list(
                session,
                load_image=True,
                load_routes=True,
                status_filter=[EndpointLifecycle.CREATED, EndpointLifecycle.DESTROYING],
            )
        for endpoint in endpoints:
            active_routings = [
                r for r in endpoint.routings if r.status != RouteStatus.FAILED_TO_START
            ]
            desired_session_count = endpoint.desired_session_count
            if (
                endpoint.lifecycle_stage == EndpointLifecycle.DESTROYING
                and len(active_routings) == 0
            ):
                endpoints_to_mark_terminated.add(endpoint)
                continue

            if len(active_routings) > desired_session_count:
                # We need to scale down!
                destroy_count = len(active_routings) - desired_session_count
                routes_to_destroy += list(
                    sorted(
                        [
                            route
                            for route in active_routings
                            if (
                                route.status != RouteStatus.PROVISIONING
                                and route.status != RouteStatus.TERMINATING
                            )
                        ],
                        key=lambda r: r.status == RouteStatus.UNHEALTHY,
                    )
                )[:destroy_count]
                log.debug(
                    "Shrinking {} from {} to {}",
                    endpoint.name,
                    len(active_routings),
                    endpoint.desired_session_count,
                )
            elif len(active_routings) < desired_session_count:
                if endpoint.retries > SERVICE_MAX_RETRIES:
                    continue
                # We need to scale up!
                create_count = desired_session_count - len(active_routings)
                endpoints_to_expand[endpoint] = create_count
                log.debug(
                    "Expanding {} from {} to {}",
                    endpoint.name,
                    len(active_routings),
                    endpoint.desired_session_count,
                )

        async with self.db.begin_readonly_session() as db_session:
            ids_of_session_to_destroy = [r.session for r in routes_to_destroy]
            kernel_loading_op = (
                noload("*"),
                selectinload(SessionRow.kernels).options(
                    noload("*"),
                    selectinload(KernelRow.agent_row).noload("*"),
                ),
            )
            query = _build_session_fetch_query(
                SessionRow.id.in_(ids_of_session_to_destroy), eager_loading_op=kernel_loading_op
            )
            result = await db_session.execute(query)
            target_sessions_to_destroy = result.scalars().all()

        already_destroyed_sessions: list[SessionId] = []
        # TODO: Update logic to not to wait for sessions to actually terminate
        for session in target_sessions_to_destroy:
            try:
                await self.registry.destroy_session(
                    session,
                    forced=True,
                    reason=KernelLifecycleEventReason.SERVICE_SCALED_DOWN,
                )
            except (GenericForbidden, SessionNotFound):
                # Session already terminated while leaving routing alive
                already_destroyed_sessions.append(session.id)
        await redis_helper.execute(
            self.redis_live,
            lambda r: r.hset(
                redis_key,
                "down",
                json.dumps([str(s.id) for s in target_sessions_to_destroy]),
            ),
        )

        created_routes = []
        async with self.db.begin_session() as db_sess:
            for endpoint, expand_count in endpoints_to_expand.items():
                log.debug("Creating {} session(s) for {}", expand_count, endpoint.name)
                for _ in range(expand_count):
                    route_id = uuid.uuid4()
                    routing_row = RoutingRow(
                        route_id,
                        endpoint.id,
                        None,
                        endpoint.session_owner,
                        endpoint.domain,
                        endpoint.project,
                    )
                    db_sess.add(routing_row)
                    created_routes.append(route_id)
            await db_sess.commit()
        for route_id in created_routes:
            await self.event_producer.produce_event(RouteCreatedEvent(route_id))
        await redis_helper.execute(
            self.redis_live,
            lambda r: r.hset(
                redis_key,
                mapping={
                    "up": json.dumps([str(e.id) for e in endpoints_to_expand.keys()]),
                    "finish_time": datetime.now(tzutc()).isoformat(),
                },
            ),
        )

        async def _delete():
            async with self.db.begin_session() as db_sess:
                query = (
                    sa.update(EndpointRow)
                    .values({
                        "destroyed_at": sa.func.now(),
                        "lifecycle_stage": EndpointLifecycle.DESTROYED,
                    })
                    .where(EndpointRow.id.in_([e.id for e in endpoints_to_mark_terminated]))
                )
                await db_sess.execute(query)
                query = sa.delete(RoutingRow).where(
                    RoutingRow.session.in_(already_destroyed_sessions)
                )
                await db_sess.execute(query)

        await execute_with_retry(_delete)

        async with self.db.begin_readonly_session() as db_sess:
            for endpoint in endpoints_to_mark_terminated:
                try:
                    await self.registry.delete_appproxy_endpoint(
                        db_sess,
                        endpoint,
                    )
                except Exception as e:
                    log.warning("failed to communicate with AppProxy endpoint: {}", str(e))

    async def update_session_status(
        self,
        context: None,
        source: AgentId,
        event: DoUpdateSessionStatusEvent,
    ) -> None:
        log.debug("update_session_status(): triggered")
        candidates = await self.registry.get_status_updatable_sessions()

        async def _transit(session_id: SessionId):
            async with self.db.connect() as db_conn:
                row, is_transited = await self.registry.transit_session_status(db_conn, session_id)
            if is_transited:
                await self.registry.post_status_transition(row)

        async with aiotools.TaskGroup() as tg:
            for session_id in candidates:
                tg.create_task(_transit(session_id))

    async def start_session(
        self,
        sched_ctx: SchedulingContext,
        session: SessionRow,
    ) -> None:
        log_fmt = (
            "prepare(s:{0.id}, type:{0.session_type}, name:{0.name}, "
            "ak:{0.access_key}, cluster_mode:{0.cluster_mode}): "
        )
        log_args = (session,)
        log.debug(log_fmt + "try-starting", *log_args)
        try:
            assert len(session.kernels) > 0
            await self.registry.start_session(sched_ctx, session)
        except Exception as e:
            status_data = convert_to_status_data(e, self.local_config["debug"]["enabled"])
            log.warning(log_fmt + "failed-starting", *log_args, exc_info=True)
            # TODO: instead of instantly cancelling upon exception, we could mark it as
            #       SCHEDULED and retry within some limit using status_data.

            async def _mark_session_cancelled() -> None:
                async with self.db.begin() as db_conn:
                    affected_agents = set(k.agent for k in session.kernels)
                    await _rollback_predicate_mutations(db_conn, sched_ctx, session)
                    now = datetime.now(tzutc())
                    update_query = (
                        sa.update(KernelRow)
                        .values(
                            status=KernelStatus.CANCELLED,
                            status_changed=now,
                            status_info="failed-to-start",
                            status_data=status_data,
                            terminated_at=now,
                            status_history=sql_json_merge(
                                KernelRow.status_history,
                                (),
                                {
                                    KernelStatus.CANCELLED.name: now.isoformat(),
                                },
                            ),
                        )
                        .where(KernelRow.session_id == session.id)
                    )
                    await SASession(db_conn).execute(update_query)
                    update_sess_query = (
                        sa.update(SessionRow)
                        .values(
                            status=SessionStatus.CANCELLED,
                            # status_changed=now,
                            status_info="failed-to-start",
                            status_data=status_data,
                            terminated_at=now,
                            status_history=sql_json_merge(
                                SessionRow.status_history,
                                (),
                                {
                                    SessionStatus.CANCELLED.name: now.isoformat(),
                                },
                            ),
                        )
                        .where(SessionRow.id == session.id)
                    )
                    await SASession(db_conn).execute(update_sess_query)
                    for agent_id in affected_agents:
                        await recalc_agent_resource_occupancy(db_conn, agent_id)

            log.debug(log_fmt + "cleanup-start-failure: begin", *log_args)
            try:
                await execute_with_retry(_mark_session_cancelled)
                await self.registry.event_producer.produce_event(
                    SessionCancelledEvent(
                        session.id,
                        session.creation_id,
                        KernelLifecycleEventReason.FAILED_TO_START,
                    ),
                )
                async with self.db.begin_readonly_session() as db_sess:
                    query = sa.select(KernelRow.id, KernelRow.container_id).where(
                        KernelRow.session_id == session.id
                    )
                    rows = (await db_sess.execute(query)).fetchall()
                    cid_map = {row["id"]: row["container_id"] for row in rows}
                destroyed_kernels = [
                    {
                        "agent": k.agent,
                        "agent_addr": k.agent_addr,
                        "id": k.id,
                        "container_id": cid_map[k.id],
                    }
                    for k in session.kernels
                ]
                await self.registry.destroy_session_lowlevel(
                    session.id,
                    destroyed_kernels,
                )
                await self.registry.recalc_resource_usage()
            except Exception as destroy_err:
                log.error(log_fmt + "cleanup-start-failure: error", *log_args, exc_info=destroy_err)
            finally:
                log.debug(log_fmt + "cleanup-start-failure: done", *log_args)
        else:
            log.info(log_fmt + "started", *log_args)


async def _list_managed_sessions(
    db_sess: SASession,
    sgroup_name: str,
    pending_timeout: timedelta,
) -> Tuple[List[SessionRow], List[SessionRow], List[SessionRow]]:
    """
    Return three lists of sessions.
    first is a list of existing sessions,
    second is pending sessions and third is to-be-cancelled sessions due to pending timeout.
    """

    managed_sessions = await SessionRow.get_sgroup_managed_sessions(db_sess, sgroup_name)

    candidates: List[SessionRow] = []
    cancelleds: List[SessionRow] = []
    existings: List[SessionRow] = []

    now = datetime.now(tzutc())
    key_func = lambda s: (s.status.value, s.created_at)
    for status, sessions in itertools.groupby(
        sorted(managed_sessions, key=key_func),
        key=lambda s: s.status,
    ):
        if status != SessionStatus.PENDING:
            existings.extend(sessions)
            continue
        for sess in sessions:
            elapsed_pending_time = now - sess.created_at
            if pending_timeout.total_seconds() > 0 and elapsed_pending_time >= pending_timeout:
                cancelleds.append(sess)
            else:
                candidates.append(sess)

    return existings, candidates, cancelleds


async def _reserve_agent(
    sched_ctx: SchedulingContext,
    db_sess: SASession,
    scaling_group: str,
    agent_id: Optional[AgentId],
    requested_slots: ResourceSlot,
    extra_conds: Any = None,
) -> AgentAllocationContext:
    query = sa.select(AgentRow.occupied_slots).where(AgentRow.id == agent_id).with_for_update()
    if extra_conds is not None:
        query = query.where(extra_conds)
    current_occupied_slots = (await db_sess.execute(query)).scalar()
    if current_occupied_slots is None:
        raise RuntimeError(f"No agent matching condition: {extra_conds}")
    update_query = (
        sa.update(AgentRow)
        .values(
            occupied_slots=(current_occupied_slots + requested_slots),
        )
        .where(AgentRow.id == agent_id)
    )
    await db_sess.execute(update_query)
    # Get the agent address for later RPC calls
    query = sa.select(AgentRow.addr).where(AgentRow.id == agent_id)
    agent_addr = await db_sess.scalar(query)
    assert agent_addr is not None
    return AgentAllocationContext(agent_id, agent_addr, scaling_group)


async def _rollback_predicate_mutations(
    db_sess: SASession,
    sched_ctx: SchedulingContext,
    session: SessionRow,
) -> None:
    """
    Rollback any changes performed by predicates.

    NOTE: We don't use the DB-level transaction rollback because we need to
    store the "ERROR" status to corresponding rows in the kernels table.
    """

    # Instead of decrementing concurrency_used, we recalculate the access_key's usage,
    # because asynchronous container launch failures and agent failures
    # (especially with multi-node multi-container cluster sessions)
    # may accumulate up multiple subtractions, resulting in
    # negative concurrency_occupied values.
    log.debug("recalculate concurrency used in rollback predicates (ak: {})", session.access_key)
    await recalc_concurrency_used(db_sess, sched_ctx.registry.redis_stat, session.access_key)
