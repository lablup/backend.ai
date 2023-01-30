from __future__ import annotations

import asyncio
import itertools
import logging
from contextvars import ContextVar
from datetime import datetime, timedelta
from functools import partial
from typing import TYPE_CHECKING, Any, Awaitable, Final, List, Optional, Sequence, Tuple, Union

import aiotools
import async_timeout
import sqlalchemy as sa
from dateutil.tz import tzutc
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import noload, selectinload

from ai.backend.common.distributed import GlobalTimer
from ai.backend.common.events import (
    AgentStartedEvent,
    CoalescingOptions,
    DoPrepareEvent,
    DoScheduleEvent,
    EventDispatcher,
    EventProducer,
    KernelLifecycleEventReason,
    SessionCancelledEvent,
    SessionEnqueuedEvent,
    SessionPreparingEvent,
    SessionScheduledEvent,
    SessionTerminatedEvent,
)
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import AgentId, ClusterMode, ResourceSlot, aobject
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.types import DistributedLockFactory
from ai.backend.plugin.entrypoint import scan_entrypoints

from ..api.exceptions import GenericBadRequest, InstanceNotAvailable
from ..defs import LockID
from ..exceptions import convert_to_status_data
from ..models import (
    AgentStatus,
    KernelRow,
    KernelStatus,
    ScalingGroupRow,
    SessionRow,
    SessionStatus,
    kernels,
    list_schedulable_agents_by_sgroup,
    recalc_agent_resource_occupancy,
    recalc_concurrency_used,
)
from ..models.scaling_group import ScalingGroupOpts
from ..models.utils import ExtendedAsyncSAEngine as SAEngine
from ..models.utils import execute_with_retry, sql_json_increment, sql_json_merge
from .predicates import (
    check_concurrency,
    check_dependencies,
    check_domain_resource_limit,
    check_group_resource_limit,
    check_keypair_resource_limit,
    check_reserved_batch_session,
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
        self.schedule_timer = GlobalTimer(
            self.lock_factory(LockID.LOCKID_SCHEDULE_TIMER, 10.0),
            self.event_producer,
            lambda: DoScheduleEvent(),
            interval=10.0,
        )
        self.prepare_timer = GlobalTimer(
            self.lock_factory(LockID.LOCKID_PREPARE_TIMER, 10.0),
            self.event_producer,
            lambda: DoPrepareEvent(),
            interval=10.0,
            initial_delay=5.0,
        )
        await self.schedule_timer.join()
        await self.prepare_timer.join()
        log.info("Session scheduler started")

    async def close(self) -> None:
        async with aiotools.TaskGroup() as tg:
            tg.create_task(self.prepare_timer.leave())
            tg.create_task(self.schedule_timer.leave())
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
                    except InstanceNotAvailable as e:
                        # Proceed to the next scaling group and come back later.
                        log.debug(
                            "schedule({}): instance not available ({})",
                            sgroup_name,
                            e.extra_msg,
                        )
                    except Exception as e:
                        log.exception("schedule({}): scheduling error!\n{}", sgroup_name, repr(e))
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
        async with self.db.begin_readonly_session() as db_sess:
            scheduler = await self._load_scheduler(db_sess, sgroup_name)
            existing_sessions, pending_sessions, cancelled_sessions = await _list_managed_sessions(
                db_sess, sgroup_name, scheduler.sgroup_opts.pending_timeout
            )

        if cancelled_sessions:
            now = datetime.now(tzutc())

            async def _apply_cancellation():
                async with self.db.begin_session() as db_sess:
                    query = (
                        sa.update(SessionRow)
                        .values(
                            status=SessionStatus.CANCELLED,
                            status_changed=now,
                            status_info="pending-timeout",
                            terminated_at=now,
                            status_history=sql_json_merge(
                                kernels.c.status_history,
                                (),
                                {
                                    SessionStatus.CANCELLED.name: now.isoformat(),
                                },
                            ),
                        )
                        .where(SessionRow.id.in_([item.id for item in cancelled_sessions]))
                    )
                    await db_sess.execute(query)

            await execute_with_retry(_apply_cancellation)
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
                    predicates: Sequence[Tuple[str, Awaitable[PredicateResult]]] = [
                        (
                            "reserved_time",
                            check_reserved_batch_session(db_sess, sched_ctx, sess_ctx),
                        ),
                        ("concurrency", check_concurrency(db_sess, sched_ctx, sess_ctx)),
                        ("dependencies", check_dependencies(db_sess, sched_ctx, sess_ctx)),
                        (
                            "keypair_resource_limit",
                            check_keypair_resource_limit(db_sess, sched_ctx, sess_ctx),
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
            has_failure = False
            failed_predicates = []
            passed_predicates = []
            for predicate_name, result in check_results:
                if isinstance(result, Exception):
                    has_failure = True
                    failed_predicates.append(
                        {
                            "name": predicate_name,
                            "msg": repr(result),
                        }
                    )
                    continue
                if result.passed:
                    passed_predicates.append(
                        {
                            "name": predicate_name,
                        }
                    )
                else:
                    failed_predicates.append(
                        {
                            "name": predicate_name,
                            "msg": result.message or "",
                        }
                    )
                    has_failure = True

            status_update_data = {
                "last_try": datetime.now(tzutc()).isoformat(),
                "failed_predicates": failed_predicates,
                "passed_predicates": passed_predicates,
            }
            if has_failure:
                log.debug(log_fmt + "predicate-checks-failed (temporary)", *log_args)

                async def _update() -> None:
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

                await execute_with_retry(_update)
                # Predicate failures are *NOT* permanent errors.
                # We need to retry the scheduling afterwards.
                continue
            else:

                async def _update() -> None:
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

                await execute_with_retry(_update)

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

            if schedulable_sess.cluster_mode == ClusterMode.SINGLE_NODE:
                await self._schedule_single_node_session(
                    sched_ctx,
                    scheduler,
                    sgroup_name,
                    candidate_agents,
                    schedulable_sess,
                    check_results,
                )
            elif schedulable_sess.cluster_mode == ClusterMode.MULTI_NODE:
                await self._schedule_multi_node_session(
                    sched_ctx,
                    scheduler,
                    sgroup_name,
                    candidate_agents,
                    schedulable_sess,
                    check_results,
                )
            else:
                raise RuntimeError(
                    f"should not reach here; unknown cluster_mode: {schedulable_sess.cluster_mode}",
                )
            num_scheduled += 1
        if num_scheduled > 0:
            await self.event_producer.produce_event(DoPrepareEvent())

    async def _schedule_single_node_session(
        self,
        sched_ctx: SchedulingContext,
        scheduler: AbstractScheduler,
        sgroup_name: str,
        candidate_agents: Sequence[AgentRow],
        sess_ctx: SessionRow,
        check_results: List[Tuple[str, Union[Exception, PredicateResult]]],
    ) -> None:
        """
        Finds and assigns an agent having resources enough to host the entire session.
        """
        log_fmt = _log_fmt.get("")
        log_args = _log_args.get(tuple())
        requested_architectures = set(k.architecture for k in sess_ctx.kernels)
        if len(requested_architectures) > 1:
            raise GenericBadRequest(
                "Cannot assign multiple kernels with different architecture"
                "on single node session",
            )
        requested_architecture = requested_architectures.pop()
        compatible_candidate_agents = [
            ag for ag in candidate_agents if ag.architecture == requested_architecture
        ]
        try:
            if not compatible_candidate_agents:
                raise InstanceNotAvailable(
                    extra_msg=(
                        f"No agents found to be compatible with the image acrhitecture "
                        f"(image[0]: {sess_ctx.main_kernel.image_ref}, "
                        f"arch: {requested_architecture})"
                    ),
                )

            # If sess_ctx.agent_id is already set for manual assignment by superadmin,
            # skip assign_agent_for_session().
            agent = sess_ctx.main_kernel.agent_row
            agent_id: AgentId
            if agent is not None:
                agent_id = agent.id
            else:
                # Let the scheduler check the resource availability and decide the target agent
                cand_agent = scheduler.assign_agent_for_session(
                    compatible_candidate_agents, sess_ctx
                )
                if cand_agent is None:
                    raise InstanceNotAvailable(
                        extra_msg=(
                            f"Could not find a contiguous resource region in any agent "
                            f"big enough to host the session "
                            f"({sess_ctx.id})"
                        ),
                    )
                assert cand_agent is not None
                agent_id = cand_agent
            async with self.db.begin_session() as agent_db_sess:
                query = sa.select(AgentRow.available_slots).where(AgentRow.id == agent_id)
                available_agent_slots = (await agent_db_sess.execute(query)).scalar()
                if available_agent_slots is None:
                    raise GenericBadRequest(f"No such agent: {agent_id}")
                assert isinstance(available_agent_slots, ResourceSlot)
                for key in available_agent_slots:
                    if available_agent_slots[key] >= sess_ctx.requested_slots[key]:
                        continue
                    else:
                        raise InstanceNotAvailable(
                            extra_msg=(
                                f"The designated agent ({agent_id}) does not have "
                                f"the enough remaining capacity ({key}, "
                                f"requested: {sess_ctx.requested_slots[key]}, "
                                f"available: {available_agent_slots[key]})."
                            ),
                        )
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
            exc_data = convert_to_status_data(e)

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
            async with self.db.begin_session() as db_sess:
                now = datetime.now(tzutc())
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
                    .where(KernelRow.session_id == sess_ctx.id)
                )
                await db_sess.execute(kernel_query)

                session_query = (
                    sa.update(SessionRow)
                    .values(
                        scaling_group_name=sgroup_name,
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

    async def _schedule_multi_node_session(
        self,
        sched_ctx: SchedulingContext,
        scheduler: AbstractScheduler,
        sgroup_name: str,
        candidate_agents: Sequence[AgentRow],
        sess_ctx: SessionRow,
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
                    agent = kernel.agent_row
                    if agent is not None:
                        # Check the resource availability of the manually designated agent
                        query = sa.select(AgentRow.available_slots).where(AgentRow.id == agent.id)
                        available_agent_slots = (await agent_db_sess.execute(query)).scalar()
                        if available_agent_slots is None:
                            raise GenericBadRequest(f"No such agent: {agent.id}")
                        for key in available_agent_slots:
                            if available_agent_slots[key] >= kernel.requested_slots[key]:
                                continue
                            else:
                                raise InstanceNotAvailable(
                                    extra_msg=(
                                        f"The designated agent ({agent.id}) does not have "
                                        f"the enough remaining capacity ({key}, "
                                        f"requested: {sess_ctx.requested_slots[key]}, "
                                        f"available: {available_agent_slots[key]})."
                                    ),
                                )
                    else:
                        # Each kernel may have different images and different architectures
                        compatible_candidate_agents = [
                            ag for ag in candidate_agents if ag.architecture == kernel.architecture
                        ]
                        if not compatible_candidate_agents:
                            raise InstanceNotAvailable(
                                extra_msg=(
                                    f"No agents found to be compatible with the image acrhitecture "
                                    f"(image: {kernel.image_ref}, "
                                    f"arch: {kernel.architecture})"
                                ),
                            )
                        # Let the scheduler check the resource availability and decide the target agent
                        agent = scheduler.assign_agent_for_kernel(
                            compatible_candidate_agents, kernel
                        )
                        if agent is None:
                            raise InstanceNotAvailable(
                                extra_msg=(
                                    f"Could not find a contiguous resource region in any agent "
                                    f"big enough to host a kernel in the session "
                                    f"({sess_ctx.id})"
                                ),
                            )
                    assert agent is not None

                    async def _reserve() -> None:
                        nonlocal agent_alloc_ctx, candidate_agents
                        async with agent_db_sess.begin_nested():
                            agent_alloc_ctx = await _reserve_agent(
                                sched_ctx,
                                agent_db_sess,
                                sgroup_name,
                                agent.id,
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
                    exc_data = convert_to_status_data(e)

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
                        .where(KernelRow.session_id == sess_ctx.id)
                    )
                    await db_sess.execute(kernel_query)

                session_query = (
                    sa.update(SessionRow)
                    .values(
                        scaling_group_name=sgroup_name,
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

        except DBAPIError as e:
            if getattr(e.orig, "pgcode", None) == "55P03":
                log.info(
                    "prepare(): cancelled due to advisory lock timeout; "
                    "maybe another prepare() call is still running"
                )
                raise asyncio.CancelledError()
            raise
        except asyncio.TimeoutError:
            log.warn("prepare(): timeout while executing start_session()")

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
            log.warning(log_fmt + "failed-starting: {1!r}", *log_args, status_data)
            # TODO: instead of instantly cancelling upon exception, we could mark it as
            #       SCHEDULED and retry within some limit using status_data.

            async def _mark_session_cancelled() -> None:
                async with self.db.begin() as db_conn:
                    affected_agents = set(k.agent for k in session.kernels)
                    for agent_id in affected_agents:
                        await recalc_agent_resource_occupancy(db_conn, agent_id)
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
