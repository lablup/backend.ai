from __future__ import annotations

import asyncio
import itertools
import json
import logging
from collections import defaultdict
from collections.abc import (
    Awaitable,
    Callable,
    Mapping,
    Sequence,
)
from contextvars import ContextVar
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from functools import partial
from typing import (
    TYPE_CHECKING,
    Any,
    Optional,
    Union,
    cast,
)
from uuid import uuid4

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
from ai.backend.common.defs import REDIS_LIVE_DB, REDIS_STAT_DB
from ai.backend.common.distributed import GlobalTimer
from ai.backend.common.events import (
    AgentStartedEvent,
    CoalescingOptions,
    DoCheckPrecondEvent,
    DoScaleEvent,
    DoScheduleEvent,
    DoStartSessionEvent,
    DoUpdateSessionStatusEvent,
    EventDispatcher,
    EventProducer,
    KernelLifecycleEventReason,
    RouteCreatedEvent,
    SessionCancelledEvent,
    SessionCheckingPrecondEvent,
    SessionEnqueuedEvent,
    SessionPreparingEvent,
    SessionScheduledEvent,
    SessionTerminatedEvent,
)
from ai.backend.common.plugin.hook import PASSED, HookResult
from ai.backend.common.types import (
    AgentId,
    AgentSelectionStrategy,
    AutoScalingMetricComparator,
    AutoScalingMetricSource,
    ClusterMode,
    EndpointId,
    KernelId,
    RedisConnectionInfo,
    ResourceSlot,
    SessionId,
    aobject,
)
from ai.backend.logging import BraceStyleAdapter
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
    EndpointAutoScalingRuleRow,
    EndpointLifecycle,
    EndpointRow,
    EndpointStatistics,
    KernelRow,
    KernelStatistics,
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
from ..models.utils import (
    execute_with_retry,
    execute_with_txn_retry,
    retry_txn,
    sql_json_increment,
    sql_json_merge,
)
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
    AbstractAgentSelector,
    AbstractResourceGroupState,
    AbstractScheduler,
    AgentAllocationContext,
    DefaultResourceGroupStateStore,
    KernelAgentBinding,
    PredicateResult,
    SchedulingContext,
    T_ResourceGroupState,
)

if TYPE_CHECKING:
    from ..config import LocalConfig, SharedConfig
    from ..registry import AgentRegistry

__all__ = (
    "load_scheduler",
    "load_agent_selector",
    "SchedulerDispatcher",
)

log = BraceStyleAdapter(logging.getLogger("ai.backend.manager.scheduler"))

_log_fmt: ContextVar[str] = ContextVar("_log_fmt")
_log_args: ContextVar[tuple[Any, ...]] = ContextVar("_log_args")


def load_scheduler(
    name: str,
    sgroup_opts: ScalingGroupOpts,
    scheduler_config: Mapping[str, Any],
) -> AbstractScheduler:
    entry_prefix = "backendai_scheduler_v10"
    for entrypoint in scan_entrypoints(entry_prefix):
        if entrypoint.name == name:
            log.debug('loading scheduler plugin "{}" from {}', name, entrypoint.module)
            scheduler_cls = entrypoint.load()
            return scheduler_cls(sgroup_opts, scheduler_config)
    raise ImportError("Cannot load the scheduler plugin", name)


def load_agent_selector(
    name: str,
    sgroup_opts: ScalingGroupOpts,
    selector_config: Mapping[str, Any],
    agent_selection_resource_priority: list[str],
    shared_config: SharedConfig,
) -> AbstractAgentSelector[AbstractResourceGroupState]:
    def create_agent_selector(
        selector_cls: type[AbstractAgentSelector[T_ResourceGroupState]],
    ) -> AbstractAgentSelector[T_ResourceGroupState]:
        # An extra inner function to parametrize the generic type arguments
        state_cls = selector_cls.get_state_cls()
        state_store = DefaultResourceGroupStateStore(state_cls, shared_config)
        return selector_cls(
            sgroup_opts,
            selector_config,
            agent_selection_resource_priority,
            state_store=state_store,
        )

    entry_prefix = "backendai_agentselector_v10"
    for entrypoint in scan_entrypoints(entry_prefix):
        if entrypoint.name == name:
            log.debug('loading agent-selector plugin "{}" from {}', name, entrypoint.module)
            selector_cls = entrypoint.load()
            return create_agent_selector(selector_cls)
    raise ImportError("Cannot load the agent-selector plugin", name)


class SchedulerDispatcher(aobject):
    config: LocalConfig
    shared_config: SharedConfig
    registry: AgentRegistry
    db: SAEngine

    event_dispatcher: EventDispatcher
    event_producer: EventProducer
    schedule_timer: GlobalTimer
    check_precond_timer: GlobalTimer
    session_start_timer: GlobalTimer
    scale_timer: GlobalTimer
    update_session_status_timer: GlobalTimer

    redis_live: RedisConnectionInfo
    redis_stat: RedisConnectionInfo

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
        self.redis_stat = redis_helper.get_redis_object(
            self.shared_config.data["redis"],
            name="stat",
            db=REDIS_STAT_DB,
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
        evd.consume(DoStartSessionEvent, None, self.start)
        evd.consume(DoCheckPrecondEvent, None, self.check_precond)
        evd.consume(DoScaleEvent, None, self.scale_services)
        evd.consume(DoUpdateSessionStatusEvent, None, self.update_session_status)
        self.schedule_timer = GlobalTimer(
            self.lock_factory(LockID.LOCKID_SCHEDULE_TIMER, 10.0),
            self.event_producer,
            lambda: DoScheduleEvent(),
            interval=10.0,
            task_name="schedule_timer",
        )
        self.session_start_timer = GlobalTimer(
            self.lock_factory(LockID.LOCKID_PREPARE_TIMER, 10.0),
            self.event_producer,
            lambda: DoStartSessionEvent(),
            interval=10.0,
            initial_delay=5.0,
            task_name="session_start_timer",
        )
        self.check_precond_timer = GlobalTimer(
            self.lock_factory(LockID.LOCKID_CHECK_PRECOND_TIMER, 10.0),
            self.event_producer,
            lambda: DoCheckPrecondEvent(),
            interval=10.0,
            initial_delay=5.0,
            task_name="check_precond_timer",
        )
        self.scale_timer = GlobalTimer(
            self.lock_factory(LockID.LOCKID_SCALE_TIMER, 10.0),
            self.event_producer,
            lambda: DoScaleEvent(),
            interval=10.0,
            initial_delay=7.0,
            task_name="scale_timer",
        )
        self.update_session_status_timer = GlobalTimer(
            self.lock_factory(LockID.LOCKID_SESSION_STATUS_UPDATE_TIMER, 10.0),
            self.event_producer,
            lambda: DoUpdateSessionStatusEvent(),
            interval=7.0,
            initial_delay=3.0,
            task_name="update_session_status_timer",
        )
        await self.schedule_timer.join()
        await self.check_precond_timer.join()
        await self.session_start_timer.join()
        await self.scale_timer.join()
        await self.update_session_status_timer.join()
        log.info("Session scheduler started")

    async def close(self) -> None:
        async with aiotools.TaskGroup() as tg:
            tg.create_task(self.scale_timer.leave())
            tg.create_task(self.check_precond_timer.leave())
            tg.create_task(self.session_start_timer.leave())
            tg.create_task(self.schedule_timer.leave())
            tg.create_task(self.update_session_status_timer.leave())
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
    ) -> tuple[AbstractScheduler, AbstractAgentSelector]:
        query = sa.select(ScalingGroupRow.scheduler, ScalingGroupRow.scheduler_opts).where(
            ScalingGroupRow.name == sgroup_name
        )
        result = await db_sess.execute(query)
        row = result.first()
        scheduler_name = row.scheduler
        sgroup_opts: ScalingGroupOpts = row.scheduler_opts
        match sgroup_opts.agent_selection_strategy:
            # The names correspond to the entrypoint names (backendai_agentselector_v10).
            case AgentSelectionStrategy.LEGACY:
                agselector_name = "legacy"
            case AgentSelectionStrategy.ROUNDROBIN:
                agselector_name = "roundrobin"
            case AgentSelectionStrategy.CONCENTRATED:
                agselector_name = "concentrated"
            case AgentSelectionStrategy.DISPERSED:
                agselector_name = "dispersed"
            case _ as unknown:
                raise ValueError(
                    f"Unknown agent selection strategy: {unknown!r}. Possible values: {[*AgentSelectionStrategy.__members__.keys()]}"
                )

        global_scheduler_opts = {}
        global_agselector_opts = {}
        if self.shared_config["plugins"]["scheduler"]:
            global_scheduler_opts = self.shared_config["plugins"]["scheduler"].get(
                scheduler_name, {}
            )
        scheduler_config = {**global_scheduler_opts, **sgroup_opts.config}
        if self.shared_config["plugins"]["agent-selector"]:
            global_agselector_opts = self.shared_config["plugins"]["agent-selector"].get(
                agselector_name, {}
            )
        agselector_config = {**global_agselector_opts, **sgroup_opts.agent_selector_config}
        agent_selection_resource_priority = self.local_config["manager"][
            "agent-selection-resource-priority"
        ]

        scheduler = load_scheduler(
            scheduler_name,
            sgroup_opts,
            scheduler_config,
        )
        agent_selector = load_agent_selector(
            agselector_name,
            sgroup_opts,
            agselector_config,
            agent_selection_resource_priority,
            self.shared_config,
        )
        return scheduler, agent_selector

    async def _schedule_in_sgroup(
        self,
        sched_ctx: SchedulingContext,
        sgroup_name: str,
    ) -> None:
        # Part 0: Load the scheduler and the agent selector.

        async with self.db.begin_readonly_session() as db_sess:
            scheduler, agent_selector = await self._load_scheduler(db_sess, sgroup_name)
            existing_sessions, pending_sessions, cancelled_sessions = await _list_managed_sessions(
                db_sess, sgroup_name, scheduler.sgroup_opts.pending_timeout
            )
        await self.flush_cancelled_sessions(cancelled_sessions)
        current_priority, pending_sessions = scheduler.prioritize(pending_sessions)

        log.debug(
            "running scheduler (sgroup:{}, pending:{} at prio:{}, existing:{}, cancelled:{})",
            sgroup_name,
            len(pending_sessions),
            current_priority,
            len(existing_sessions),
            len(cancelled_sessions),
        )
        num_scheduled = 0
        while len(pending_sessions) > 0:
            # Part 1: Choose the pending session to try scheduling.

            async with self.db.begin_readonly_session() as db_sess:
                candidate_agents = await list_schedulable_agents_by_sgroup(db_sess, sgroup_name)
            total_capacity = sum((ag.available_slots for ag in candidate_agents), ResourceSlot())
            picked_session_id = scheduler.pick_session(
                total_capacity,
                pending_sessions,
                existing_sessions,
            )
            if picked_session_id is None:
                # no session is picked.
                # continue to next sgroup.
                return
            for picked_idx, pending_sess in enumerate(pending_sessions):
                if pending_sess.id == picked_session_id:
                    break
            else:
                # no matching entry for picked session?
                raise RuntimeError("should not reach here")
            pending_sess = pending_sessions.pop(picked_idx)
            log_fmt = "schedule(s:{}, prio:{}, type:{}, name:{}, ak:{}, cluster_mode:{}): "
            log_args = (
                pending_sess.id,
                pending_sess.priority,
                pending_sess.session_type,
                pending_sess.name,
                pending_sess.access_key,
                pending_sess.cluster_mode,
            )
            _log_fmt.set(log_fmt)
            _log_args.set(log_args)
            log.debug(log_fmt + "try-scheduling", *log_args)

            # Part 2: Predicate checks with predicate hook plugins

            check_results = []
            failed_predicates = []
            passed_predicates = []
            async for attempt in retry_txn():
                with attempt:
                    check_results = await self.check_predicates(
                        sched_ctx,
                        pending_sess,
                        exc_handler=lambda _: log.exception(log_fmt + "predicate-error", *log_args),
                    )
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

            hook_result = HookResult(status=PASSED, src_plugin=[], result=[])
            async for attempt in retry_txn():
                with attempt:
                    hook_result = await self.check_predicates_hook(sched_ctx, pending_sess)
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

            # Part 3: Interpret the predicate check results

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
                            pending_sess,
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
                            .where(SessionRow.id == pending_sess.id)
                        )
                        await db_sess.execute(query)
                        if pending_sess.is_private:
                            await _apply_cancellation(db_sess, [pending_sess.id])
                            await self.event_producer.produce_event(
                                SessionCancelledEvent(
                                    pending_sess.id,
                                    pending_sess.creation_id,
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
                            .where(KernelRow.session_id == pending_sess.id)
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
                            .where(SessionRow.id == pending_sess.id)
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

            # Part 4: Assign agent(s) via the agent selector.

            async with self.db.begin_readonly_session() as db_sess:
                schedulable_sess = await SessionRow.get_session_by_id(
                    db_sess,
                    pending_sess.id,
                    eager_loading_op=(
                        noload("*"),
                        selectinload(SessionRow.kernels).options(
                            noload("*"),
                            selectinload(KernelRow.agent_row).noload("*"),
                        ),
                    ),
                )

            try:
                match schedulable_sess.cluster_mode:
                    case ClusterMode.SINGLE_NODE:
                        await self._schedule_single_node_session(
                            sched_ctx,
                            agent_selector,
                            sgroup_name,
                            candidate_agents,
                            schedulable_sess,
                            check_results,
                        )
                    case ClusterMode.MULTI_NODE:
                        await self._schedule_multi_node_session(
                            sched_ctx,
                            agent_selector,
                            sgroup_name,
                            candidate_agents,
                            schedulable_sess,
                            check_results,
                        )
                    case _:
                        log.exception(
                            f"should not reach here; unknown cluster_mode: {schedulable_sess.cluster_mode}"
                        )
                        continue
                # For complex schedulers like DRF, they may need internal state updates
                # based on the scheduling result.
                scheduler.update_allocation(schedulable_sess)
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
            await self.event_producer.produce_event(DoCheckPrecondEvent())

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
        agent_selector: AbstractAgentSelector,
        sgroup_name: str,
        candidate_agents: Sequence[AgentRow],
        sess_ctx: SessionRow,
        check_results: list[tuple[str, Union[Exception, PredicateResult]]],
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
                        f"(image[0]: {sess_ctx.main_kernel.image}, "
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
                # Let the agent selector decide the target agent
                cand_agent_id = await agent_selector.assign_agent_for_session(
                    compatible_candidate_agents,
                    sess_ctx,
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
        agent_selector: AbstractAgentSelector,
        sgroup_name: str,
        candidate_agents: Sequence[AgentRow],
        sess_ctx: SessionRow,
        check_results: list[tuple[str, Union[Exception, PredicateResult]]],
    ) -> None:
        """
        Finds and assigns agents having resources enough to host each kernel in the session.
        """
        log_fmt = _log_fmt.get()
        log_args = _log_args.get()
        agent_query_extra_conds = None

        kernel_agent_bindings: list[KernelAgentBinding] = []
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
                                    f"(image: {kernel.image}, "
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
                        # Let the agent selector decide the target agent
                        agent_id = await agent_selector.assign_agent_for_kernel(
                            available_candidate_agents,
                            kernel,
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

    async def check_precond(
        self,
        context: None,
        source: AgentId,
        event: DoCheckPrecondEvent,
    ) -> None:
        """
        Scan the scheduled sessions and perform the agent RPC calls to check and pull required images.

        This function DOES NOT transit session status.
        This function calls check-and-pull API and the API produces image pull events.
        Let event handlers transit session and kernel status from
        `ImagePullStartedEvent` and `ImagePullFinishedEvent` events.
        """
        manager_id = self.local_config["manager"]["id"]
        redis_key = f"manager.{manager_id}.check_precondition"

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
        try:
            async with self.lock_factory(LockID.LOCKID_CHECK_PRECOND, 600):
                bindings: list[KernelAgentBinding] = []

                async def _transit_scheduled_to_preparing(
                    db_session: SASession,
                ) -> list[SessionRow]:
                    now = datetime.now(timezone.utc)
                    scheduled_sessions = await SessionRow.get_sessions_by_status(
                        db_session, SessionStatus.SCHEDULED, load_kernel_image=True
                    )
                    for row in scheduled_sessions:
                        for kernel_row in row.kernels:
                            _kernel_row = cast(KernelRow, kernel_row)
                            _kernel_row.set_status(KernelStatus.PREPARING, status_changed_at=now)
                        row.set_status(SessionStatus.PREPARING, status_changed_at=now)
                    return scheduled_sessions

                async with self.db.connect() as db_conn:
                    scheduled_sessions = await execute_with_txn_retry(
                        _transit_scheduled_to_preparing, self.db.begin_session, db_conn
                    )
                log.debug(
                    "check_precond(): checking-precond {} session(s)", len(scheduled_sessions)
                )
                for scheduled_session in scheduled_sessions:
                    for kernel in scheduled_session.kernels:
                        bindings.append(
                            KernelAgentBinding(
                                kernel=kernel,
                                agent_alloc_ctx=AgentAllocationContext(
                                    kernel.agent, kernel.agent_addr, kernel.scaling_group
                                ),
                                allocated_host_ports=set(),
                            )
                        )
                    await self.registry.event_producer.produce_event(
                        SessionCheckingPrecondEvent(
                            scheduled_session.id,
                            scheduled_session.creation_id,
                        ),
                    )
                # check_and_pull_images() spawns tasks through PersistentTaskGroup
                await self.registry.check_and_pull_images(bindings)

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
                    "check_precond(): cancelled due to advisory lock timeout; "
                    "maybe another check_precond() call is still running"
                )
                raise asyncio.CancelledError()
            raise
        except asyncio.TimeoutError:
            log.warning("check_precond(): timeout while executing start_session()")

    async def start(
        self,
        context: None,
        source: AgentId,
        event: DoStartSessionEvent,
    ) -> None:
        """
        Scan the sessions ready to create and perform the agent RPC calls to create kernels.

        Session status transition: PREPARED -> CREATING
        """
        manager_id = self.local_config["manager"]["id"]
        redis_key = f"manager.{manager_id}.start"

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
        try:
            async with self.lock_factory(LockID.LOCKID_START_TIMER, 600):
                now = datetime.now(timezone.utc)
                known_slot_types = await self.shared_config.get_resource_slots()
                sched_ctx = SchedulingContext(
                    self.registry,
                    known_slot_types,
                )

                async def _mark_session_and_kernel_creating(
                    db_session: SASession,
                ) -> list[SessionRow]:
                    session_rows = await SessionRow.get_sessions_by_status(
                        db_session, SessionStatus.PREPARED
                    )
                    for row in session_rows:
                        for kernel_row in row.kernels:
                            _kernel_row = cast(KernelRow, kernel_row)
                            _kernel_row.set_status(KernelStatus.CREATING, status_changed_at=now)
                        row.set_status(SessionStatus.CREATING, status_changed_at=now)
                    return session_rows

                async with self.db.connect() as db_conn:
                    scheduled_sessions = await execute_with_txn_retry(
                        _mark_session_and_kernel_creating, self.db.begin_session, db_conn
                    )

                log.debug("starting(): starting {} session(s)", len(scheduled_sessions))
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
                    redis_key,
                    "finish_time",
                    datetime.now(tzutc()).isoformat(),
                ),
            )
        except DBAPIError as e:
            if getattr(e.orig, "pgcode", None) == "55P03":
                log.info(
                    "start(): cancelled due to advisory lock timeout; "
                    "maybe another start() call is still running"
                )
                raise asyncio.CancelledError()
            raise
        except asyncio.TimeoutError:
            log.warning("start(): timeout while executing start_session()")

    async def _autoscale_endpoints(
        self,
        session: SASession,
    ) -> None:
        current_datetime = datetime.now(tz=UTC)
        rules = await EndpointAutoScalingRuleRow.list(session, load_endpoint=True)

        # currently auto scaling supports two types of stat as source: kernel and endpoint
        # to fetch aggregated kernel metrics among every kernels managed by a single endpoint
        # we first need to collect every routings, and then the sessions tied to each routing,
        # and finally the child kernels of each session
        endpoints = await EndpointRow.batch_load(
            session, [rule.endpoint for rule in rules], load_routes=True
        )
        endpoint_by_id = {endpoint.id: endpoint for endpoint in endpoints}
        metric_requested_sessions: list[SessionId] = []
        metric_requested_kernels: list[KernelId] = []
        metric_requested_endpoints: list[EndpointId] = []

        kernel_statistics_by_id: dict[KernelId, Any] = {}
        endpoint_statistics_by_id: dict[EndpointId, Any] = {}
        kernels_by_session_id: dict[SessionId, list[KernelRow]] = defaultdict(lambda: [])

        for rule in rules:
            match rule.metric_source:
                case AutoScalingMetricSource.KERNEL:
                    metric_requested_sessions += [
                        route.session for route in endpoint_by_id[rule.endpoint].routings
                    ]
                case AutoScalingMetricSource.INFERENCE_FRAMEWORK:
                    metric_requested_endpoints.append(rule.endpoint)

        kernel_rows = await KernelRow.batch_load_by_session_id(
            session, list(metric_requested_sessions)
        )
        for kernel in kernel_rows:
            kernels_by_session_id[kernel.session_id].append(kernel)
            metric_requested_kernels.append(kernel)

        # to speed up and lower the pressure to the redis we must load every metrics
        # in bulk, not querying each key at once
        kernel_live_stats = await KernelStatistics.batch_load_by_kernel_impl(
            self.redis_stat,
            cast(list[SessionId], list(metric_requested_kernels)),
        )
        endpoint_live_stats = await EndpointStatistics.batch_load_by_endpoint_impl(
            self.redis_stat,
            cast(list[SessionId], list(metric_requested_endpoints)),
        )

        kernel_statistics_by_id = {
            kernel_id: metric
            for kernel_id, metric in zip(metric_requested_kernels, kernel_live_stats)
        }
        endpoint_statistics_by_id = {
            endpoint_id: metric
            for endpoint_id, metric in zip(metric_requested_endpoints, endpoint_live_stats)
        }

        log_skip_due_to_missing_metric = partial(
            log.warning,
            "AUTOSCALE(e:{0.endpoint}, rule:{0.id}): skipping the rule because metric {0.metric_name} does not exist",
        )

        for rule in rules:
            should_trigger = False
            match rule.metric_source:
                # kernel metrics should be evaluated by the average of the metric across every kernels
                case AutoScalingMetricSource.KERNEL:
                    metric_aggregated_value = Decimal("0")
                    metric_found_kernel_count = 0
                    for route in endpoint_by_id[rule.endpoint].routings:
                        for kernel in kernels_by_session_id[route.session]:
                            if not kernel_statistics_by_id[kernel.id]:
                                continue
                            live_stat = kernel_statistics_by_id[kernel.id]
                            if rule.metric_name not in live_stat:
                                continue
                            metric_found_kernel_count += 1
                            metric_aggregated_value += Decimal(
                                live_stat[rule.metric_name]["current"]
                            )
                    if metric_found_kernel_count == 0:
                        log_skip_due_to_missing_metric(rule)
                        continue
                    current_value = metric_aggregated_value / Decimal(metric_found_kernel_count)
                case AutoScalingMetricSource.INFERENCE_FRAMEWORK:
                    if not endpoint_statistics_by_id[rule.endpoint]:
                        log_skip_due_to_missing_metric(rule)
                        continue
                    live_stat = endpoint_statistics_by_id[rule.endpoint]
                    if rule.metric_name not in live_stat:
                        log_skip_due_to_missing_metric(rule)
                        continue
                    current_value = Decimal(live_stat[rule.metric_name]["current"]) / len(
                        endpoint_by_id[rule.endpoint].routings
                    )
                case _:
                    raise NotImplementedError

            match rule.comparator:
                case AutoScalingMetricComparator.LESS_THAN:
                    should_trigger = current_value < rule.threshold
                case AutoScalingMetricComparator.LESS_THAN_OR_EQUAL:
                    should_trigger = current_value <= rule.threshold
                case AutoScalingMetricComparator.GREATER_THAN:
                    should_trigger = current_value > rule.threshold
                case AutoScalingMetricComparator.GREATER_THAN_OR_EQUAL:
                    should_trigger = current_value >= rule.threshold

            log.debug(
                "AUTOSCALE(e:{}, rule:{}): {} {} {}: {}",
                rule.endpoint,
                rule.id,
                current_value,
                rule.comparator,
                rule.threshold,
                should_trigger,
            )
            if should_trigger:
                new_replica_count = max(0, rule.endpoint_row.replicas + rule.step_size)
                if (rule.min_replicas is not None and new_replica_count < rule.min_replicas) or (
                    rule.max_replicas is not None and new_replica_count > rule.max_replicas
                ):
                    log.info(
                        "AUTOSCALE(e:{}, rule:{}): ignored the new replica count {} ({}) [min: {}, max: {}]",
                        rule.endpoint,
                        rule.id,
                        new_replica_count,
                        rule.step_size,
                        rule.min_replicas,
                        rule.max_replicas,
                    )
                    continue
                if rule.last_triggered_at is None or rule.last_triggered_at < (
                    current_datetime - timedelta(seconds=rule.cooldown_seconds)
                ):
                    # changes applied here will be reflected at consequent queries (at `scale_services()`)
                    # so we do not have to propagate the changes on the function level
                    rule.endpoint_row.replicas = new_replica_count
                    rule.last_triggered_at = current_datetime
                    log.info(
                        "AUTOSCALE(e:{}, rule:{}): applied the new replica count {} ({})",
                        rule.endpoint,
                        rule.id,
                        new_replica_count,
                        rule.step_size,
                    )
                else:
                    log.info(
                        "AUTOSCALE(e:{}, rule:{}): ignored the new replica count {} ({}) as the rule is on a cooldown period until {}",
                        rule.endpoint,
                        rule.id,
                        new_replica_count,
                        rule.step_size,
                        rule.last_triggered_at + timedelta(seconds=rule.cooldown_seconds),
                    )

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

        async def _autoscale_txn() -> None:
            async with self.db.begin_session(commit_on_end=True) as session:
                await self._autoscale_endpoints(session)

        await execute_with_retry(_autoscale_txn)

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
            replicas = endpoint.replicas
            if (
                endpoint.lifecycle_stage == EndpointLifecycle.DESTROYING
                and len(active_routings) == 0
            ):
                endpoints_to_mark_terminated.add(endpoint)
                continue

            if len(active_routings) > replicas:
                # We need to scale down!
                destroy_count = len(active_routings) - replicas
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
                    endpoint.replicas,
                )
            elif len(active_routings) < replicas:
                if endpoint.retries > SERVICE_MAX_RETRIES:
                    continue
                # We need to scale up!
                create_count = replicas - len(active_routings)
                endpoints_to_expand[endpoint] = create_count
                log.debug(
                    "Expanding {} from {} to {}",
                    endpoint.name,
                    len(active_routings),
                    endpoint.replicas,
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
                    route_id = uuid4()
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
        candidates = await self.registry.session_lifecycle_mgr.get_status_updatable_sessions()
        await self.registry.session_lifecycle_mgr.transit_session_status(candidates)

    async def start_session(
        self,
        sched_ctx: SchedulingContext,
        session: SessionRow,
    ) -> None:
        log_fmt = (
            "start-session(s:{0.id}, type:{0.session_type}, name:{0.name}, "
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
                async with self.db.begin_session() as db_session:
                    affected_agents = set(k.agent for k in session.kernels)
                    await _rollback_predicate_mutations(db_session, sched_ctx, session)
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
                    await db_session.execute(update_query)
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
                    await db_session.execute(update_sess_query)
                    for agent_id in affected_agents:
                        await recalc_agent_resource_occupancy(db_session, agent_id)

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

    async def flush_cancelled_sessions(self, cancelled_sessions: Sequence[SessionRow]) -> None:
        if not cancelled_sessions:
            return
        session_ids = [item.id for item in cancelled_sessions]

        async for attempt in retry_txn():
            with attempt:
                async with self.db.begin_session() as db_sess:
                    await _apply_cancellation(db_sess, session_ids)
        for item in cancelled_sessions:
            await self.event_producer.produce_event(
                SessionCancelledEvent(
                    item.id,
                    item.creation_id,
                    reason=KernelLifecycleEventReason.PENDING_TIMEOUT,
                ),
            )

    async def check_predicates(
        self,
        sched_ctx: SchedulingContext,
        pending_sess: SessionRow,
        *,
        exc_handler: Callable[[Exception], None] | None = None,
    ) -> list[tuple[str, Union[Exception, PredicateResult]]]:
        check_results: list[tuple[str, Union[Exception, PredicateResult]]] = []
        async with self.db.begin_session() as db_sess:
            predicates: list[tuple[str, Awaitable[PredicateResult]]] = [
                (
                    "reserved_time",
                    check_reserved_batch_session(db_sess, sched_ctx, pending_sess),
                ),
                ("dependencies", check_dependencies(db_sess, sched_ctx, pending_sess)),
                ("concurrency", check_concurrency(db_sess, sched_ctx, pending_sess)),
            ]
            if not pending_sess.is_private:
                predicates += [
                    (
                        "pending_session_resource_limit",
                        check_pending_session_resource_limit(db_sess, sched_ctx, pending_sess),
                    ),
                    (
                        "pending_session_count_limit",
                        check_pending_session_count_limit(db_sess, sched_ctx, pending_sess),
                    ),
                    (
                        "keypair_resource_limit",
                        check_keypair_resource_limit(db_sess, sched_ctx, pending_sess),
                    ),
                    (
                        "user_resource_limit",
                        check_user_resource_limit(db_sess, sched_ctx, pending_sess),
                    ),
                    (
                        "user_group_resource_limit",
                        check_group_resource_limit(db_sess, sched_ctx, pending_sess),
                    ),
                    (
                        "domain_resource_limit",
                        check_domain_resource_limit(db_sess, sched_ctx, pending_sess),
                    ),
                ]
            for predicate_name, check_coro in predicates:
                try:
                    check_results.append((predicate_name, await check_coro))
                except DBAPIError:
                    raise
                except Exception as e:
                    if exc_handler is not None:
                        exc_handler(e)
                    check_results.append((predicate_name, e))
        return check_results

    async def check_predicates_hook(
        self,
        sched_ctx: SchedulingContext,
        pending_sess: SessionRow,
    ) -> HookResult:
        async with self.db.begin_readonly_session() as db_sess:
            return await self.registry.hook_plugin_ctx.dispatch(
                "PREDICATE",
                (
                    db_sess,
                    sched_ctx,
                    pending_sess,
                ),
            )


async def _apply_cancellation(
    db_sess: SASession, session_ids: list[SessionId], reason="pending-timeout"
) -> None:
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


async def _list_managed_sessions(
    db_sess: SASession,
    sgroup_name: str,
    pending_timeout: timedelta,
) -> tuple[list[SessionRow], list[SessionRow], list[SessionRow]]:
    """
    Return three lists of sessions.
    first is a list of existing sessions,
    second is pending sessions and third is to-be-cancelled sessions due to pending timeout.
    """

    managed_sessions = await SessionRow.get_sgroup_managed_sessions(db_sess, sgroup_name)

    candidates: list[SessionRow] = []
    cancelleds: list[SessionRow] = []
    existings: list[SessionRow] = []

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
    extra_conds: Optional[Any] = None,
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
