from __future__ import annotations

import asyncio
import itertools
import logging
from contextvars import ContextVar
from datetime import datetime, timedelta
from typing import (
    Any,
    Awaitable,
    Final,
    List,
    Sequence,
    Tuple,
    Union,
    TYPE_CHECKING,
    Optional,
)
from ai.backend.manager.models.kernel import KernelRow

import aiotools
from dateutil.tz import tzutc
import sqlalchemy as sa
from sqlalchemy.engine.row import Row
from sqlalchemy.exc import DBAPIError

from sqlalchemy.ext.asyncio import (
    AsyncConnection as SAConnection,
    AsyncSession as SASession,
)
from sqlalchemy.sql.expression import true

from ai.backend.common.distributed import GlobalTimer
from ai.backend.common.events import (
    AgentStartedEvent,
    CoalescingOptions,
    DoScheduleEvent,
    DoPrepareEvent,
    SessionCancelledEvent,
    SessionEnqueuedEvent,
    SessionPreparingEvent,
    SessionScheduledEvent,
    SessionTerminatedEvent,
    EventDispatcher,
    EventProducer,
)
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import (
    aobject,
    AgentId,
    AccessKey,
    ClusterMode,
    ResourceSlot,
)
from ai.backend.plugin.entrypoint import scan_entrypoints

from ai.backend.manager.types import DistributedLockFactory

from ..api.exceptions import GenericBadRequest, InstanceNotAvailable
from ..defs import (
    LockID,
)
from ..exceptions import convert_to_status_data
from ..models import (
    agents, kernels, scaling_groups, AgentRow,
    SessionRow, SessionStatus,
    recalc_agent_resource_occupancy,
    recalc_concurrency_used,
    AgentStatus, KernelStatus,
    AGENT_RESOURCE_OCCUPYING_SESSION_STATUSES,
)
from ..models.scaling_group import ScalingGroupOpts, ScalingGroupRow
from ..models.utils import (
    ExtendedAsyncSAEngine as SAEngine,
    execute_with_retry,
    sql_json_increment,
    sql_json_merge,
)
from .types import (
    PredicateResult,
    PendingSession,
    ExistingSession,
    SchedulingContext,
    AgentContext,
    AgentAllocationContext,
    AbstractScheduler,
    KernelAgentBinding,
)
from .predicates import (
    check_reserved_batch_session,
    check_concurrency,
    check_dependencies,
    check_keypair_resource_limit,
    check_group_resource_limit,
    check_domain_resource_limit,
    check_scaling_group,
)

if TYPE_CHECKING:
    from ..config import LocalConfig, SharedConfig
    from ..registry import AgentRegistry

__all__ = (
    'load_scheduler',
    'SchedulerDispatcher',
)

log = BraceStyleAdapter(logging.getLogger('ai.backend.manager.scheduler'))

_log_fmt: ContextVar[str] = ContextVar('_log_fmt')
_log_args: ContextVar[Tuple[Any, ...]] = ContextVar('_log_args')

_key_schedule_prep_tasks: Final = "scheduler.preptasks"


def load_scheduler(
    name: str,
    sgroup_opts: ScalingGroupOpts,
    scheduler_config: dict[str, Any],
) -> AbstractScheduler:
    entry_prefix = 'backendai_scheduler_v10'
    for entrypoint in scan_entrypoints(entry_prefix):
        if entrypoint.name == name:
            log.debug('loading scheduler plugin "{}" from {}', name, entrypoint.module)
            scheduler_cls = entrypoint.load()
            return scheduler_cls(sgroup_opts, scheduler_config)
    raise ImportError('Cannot load the scheduler plugin', name)


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
            'max_wait': 0.5,
            'max_batch_size': 32,
        }
        # coalescing_opts = None
        evd = self.registry.event_dispatcher
        evd.consume(SessionEnqueuedEvent, None, self.schedule, coalescing_opts, name="dispatcher.enq")
        evd.consume(SessionTerminatedEvent, None, self.schedule, coalescing_opts, name="dispatcher.term")
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
        log.info('Session scheduler started')

    async def close(self) -> None:
        async with aiotools.TaskGroup() as tg:
            tg.create_task(self.prepare_timer.leave())
            tg.create_task(self.schedule_timer.leave())
        log.info('Session scheduler stopped')

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
        log.debug('schedule(): triggered')
        known_slot_types = await self.shared_config.get_resource_slots()
        sched_ctx = SchedulingContext(
            registry=self.registry,
            known_slot_types=known_slot_types,
        )

        try:
            # The schedule() method should be executed with a global lock
            # as its individual steps are composed of many short-lived transactions.
            async with self.lock_factory(LockID.LOCKID_SCHEDULE, 60):
                async with self.db.begin_session() as db_sess:
                    schedulable_scaling_groups = await AgentRow.list_alive_agents_scaling_group(db_sess)
                    for sgroup in schedulable_scaling_groups:
                        try:
                            await self._schedule_in_sgroup(
                                db_sess, sched_ctx, sgroup,
                            )
                        except InstanceNotAvailable:
                            # Proceed to the next scaling group and come back later.
                            log.debug('schedule({}): instance not available', sgroup.name)
                        except Exception as e:
                            log.exception('schedule({}): scheduling error!\n{}', sgroup.name, repr(e))
        except DBAPIError as e:
            if getattr(e.orig, 'pgcode', None) == '55P03':
                log.info("schedule(): cancelled due to advisory lock timeout; "
                         "maybe another schedule() call is still running")
                raise asyncio.CancelledError()
            raise

    async def _load_scheduler(
        self,
        sgroup: ScalingGroupRow,
    ) -> AbstractScheduler:
        scheduler_name = sgroup.scheduler
        sgroup_opts: ScalingGroupOpts = sgroup.scheduler_opts
        global_scheduler_opts = {}
        if self.shared_config['plugins']['scheduler']:
            global_scheduler_opts = self.shared_config['plugins']['scheduler'].get(scheduler_name, {})
        scheduler_specific_config = {**global_scheduler_opts, **sgroup_opts.config}
        return load_scheduler(scheduler_name, sgroup_opts, scheduler_specific_config)

    async def _schedule_in_sgroup(
        self,
        db_sess: SASession,
        sched_ctx: SchedulingContext,
        sgroup: ScalingGroupRow,
    ) -> None:
        scheduler = await self._load_scheduler(sgroup)
        existing_sessions, pending_sessions, cancelled_sessions = \
            await _list_managed_sessions(db_sess, scheduler, sgroup)

        if cancelled_sessions:
            now = datetime.now(tzutc())

            async def _apply_cancellation():
                async with self.db.begin_session() as db_sess:
                    for session in cancelled_sessions:
                        await SessionRow.update_session_kernels(
                            db_sess, session,
                            kernel_data={
                                'status': KernelStatus.CANCELLED,
                                'status_changed': now,
                                'status_info': 'pending-timeout',
                                'terminated_at': now,
                            },
                        )

            await execute_with_retry(_apply_cancellation)
            for sess in cancelled_sessions:
                await self.event_producer.produce_event(
                    SessionCancelledEvent(
                        sess.id,
                        sess.creation_id,
                        reason="pending timeout",
                    ),
                )

        sgroup_name = sgroup.name
        log.debug(
            "running scheduler (sgroup:{}, pending:{}, existing:{}, cancelled:{})",
            sgroup_name, len(pending_sessions), len(existing_sessions), len(cancelled_sessions),
        )
        zero = ResourceSlot()
        num_scheduled = 0
        
        while pending_sessions:

            async with self.db.begin_readonly_session() as sess:
                candidate_agents = await AgentRow.list_agents_by_sgroup(sess, sgroup_name)
                total_capacity = sum((ag.available_slots for ag in candidate_agents), zero)

            sess_ctx = scheduler.pick_session(
                total_capacity,
                pending_sessions,
                existing_sessions,
            )
            if sess_ctx is None:
                # no session is picked.
                # continue to next sgroup.
                return
            pending_sessions = [s for s in pending_sessions if s is not sess_ctx]

            log_fmt = 'schedule(s:{}, type:{}, name:{}, ak:{}, cluster_mode:{}): '
            log_args = (
                sess_ctx.id,
                sess_ctx.session_type,
                sess_ctx.name,
                sess_ctx.access_key,
                sess_ctx.cluster_mode,
            )
            _log_fmt.set(log_fmt)
            _log_args.set(log_args)
            log.debug(log_fmt + 'try-scheduling', *log_args)

            async def _check_predicates() -> List[Tuple[str, Union[Exception, PredicateResult]]]:
                check_results: List[Tuple[str, Union[Exception, PredicateResult]]] = []
                async with self.db.begin_session() as kernel_db_sess:
                    predicates: Sequence[Tuple[str, Awaitable[PredicateResult]]] = [
                        (
                            'reserved_time',
                            check_reserved_batch_session(kernel_db_sess, sched_ctx, sess_ctx),
                        ),
                        ('concurrency', check_concurrency(kernel_db_sess, sched_ctx, sess_ctx)),
                        ('dependencies', check_dependencies(kernel_db_sess, sched_ctx, sess_ctx)),
                        (
                            'keypair_resource_limit',
                            check_keypair_resource_limit(kernel_db_sess, sched_ctx, sess_ctx),
                        ),
                        (
                            'user_group_resource_limit',
                            check_group_resource_limit(kernel_db_sess, sched_ctx, sess_ctx),
                        ),
                        (
                            'domain_resource_limit',
                            check_domain_resource_limit(kernel_db_sess, sched_ctx, sess_ctx),
                        ),
                        (
                            'scaling_group_resource_limit',
                            check_scaling_group(kernel_db_sess, sched_ctx, sess_ctx),
                        ),
                    ]
                    for predicate_name, check_coro in predicates:
                        try:
                            check_results.append((predicate_name, await check_coro))
                        except DBAPIError:
                            raise
                        except Exception as e:
                            log.exception(log_fmt + 'predicate-error', *log_args)
                            check_results.append((predicate_name, e))
                return check_results

            check_results = await execute_with_retry(_check_predicates)
            has_failure = False
            has_permanent_failure = False
            failed_predicates = []
            passed_predicates = []
            for predicate_name, result in check_results:
                if isinstance(result, Exception):
                    has_failure = True
                    failed_predicates.append({
                        'name': predicate_name,
                        'msg': repr(result),
                    })
                    continue
                if result.passed:
                    passed_predicates.append({
                        'name': predicate_name,
                    })
                else:
                    failed_predicates.append({
                        'name': predicate_name,
                        'msg': result.message or "",
                    })
                    has_failure = True
                    if result.permanent:
                        has_permanent_failure = True  # noqa
            if has_failure:
                log.debug(log_fmt + 'predicate-checks-failed (temporary)', *log_args)
                # TODO: handle has_permanent_failure as cancellation
                #  - An early implementation of it has caused DB query blocking due to
                #    the inclusion of the kernels.status field. :(
                #    Let's fix it.

                async def _update() -> None:
                    async with self.db.begin_session() as sess:
                        await _rollback_predicate_mutations(
                            sess, sched_ctx, sess_ctx,
                        )
                        await SessionRow.update_session_kernels(
                            sess, sess_ctx,
                            kernel_data={
                                'status_info': 'predicate-checks-failed',
                                'status_data': sql_json_increment(
                                    KernelRow.status_data,
                                    ('scheduler', 'retries'),
                                    parent_updates={
                                        'last_try': datetime.now(tzutc()).isoformat(),
                                        'failed_predicates': failed_predicates,
                                        'passed_predicates': passed_predicates,
                                    },
                                ),
                            },
                        )

                await execute_with_retry(_update)
                # Predicate failures are *NOT* permanent errors.
                # We need to retry the scheduling afterwards.
                continue
            else:
                async def _update() -> None:
                    async with self.db.begin_session() as sess:
                        await SessionRow.update_session_kernels(
                            sess, sess_ctx,
                            kernel_data={
                                'status_data': sql_json_merge(
                                    KernelRow.status_data,
                                    ('scheduler',),
                                    {
                                        'last_try': datetime.now(tzutc()).isoformat(),
                                        'failed_predicates': failed_predicates,
                                        'passed_predicates': passed_predicates,
                                    },
                                ),
                            },
                        )

                await execute_with_retry(_update)

            if sess_ctx.cluster_mode == ClusterMode.SINGLE_NODE:
                requested_architecture = sess_ctx.kernels[0].image.architecture
                # Single node session can't have multiple containers with different arch
                if any(
                    kernel.image.architecture != requested_architecture
                    for kernel in sess_ctx.kernels
                ):
                    raise GenericBadRequest(
                        'Cannot assign multiple kernels with different architecture'
                        'on single node session',
                    )
                candidate_agents = [ag for ag in candidate_agents if ag.architecture == requested_architecture]
                await self._schedule_single_node_session(
                    sched_ctx,
                    scheduler,
                    sgroup_name,
                    candidate_agents,
                    sess_ctx,
                    check_results,
                )
            elif sess_ctx.cluster_mode == ClusterMode.MULTI_NODE:
                await self._schedule_multi_node_session(
                    sched_ctx,
                    scheduler,
                    sgroup_name,
                    candidate_agents,
                    sess_ctx,
                    check_results,
                )
            else:
                raise RuntimeError(
                    f"should not reach here; unknown cluster_mode: {sess_ctx.cluster_mode}",
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
        # Assign agent resource per session.
        log_fmt = _log_fmt.get("")
        log_args = _log_args.get(tuple())
        try:
            # If sess_ctx.agent_id is already set for manual assignment by superadmin,
            # skip assign_agent_for_session().
            agent = None
            agent = sess_ctx.main_kernel.agent
            if agent is None:
                agent = scheduler.assign_agent_for_session(candidate_agents, sess_ctx)
            available_agent_slots = agent.available_slots
            if available_agent_slots is None:
                raise InstanceNotAvailable("There is no such agent.")
            if any(
                val > available_agent_slots[slot]
                for slot, val in sess_ctx.requested_slots.items()
            ):
                raise InstanceNotAvailable(
                    "The resource slot does not have the enough remaining capacity.",
                )

            async with self.db.begin_session() as agent_db_sess:
                agent_alloc_ctx = await _reserve_agent(
                    agent_db_sess,
                    sched_ctx, sgroup_name, agent, sess_ctx.requested_slots,
                )
        except InstanceNotAvailable:
            log.debug(log_fmt + 'no-available-instances', *log_args)

            async def _update() -> None:
                async with self.db.begin_session() as kernel_db_sess:
                    await _rollback_predicate_mutations(
                        kernel_db_sess, sched_ctx, sess_ctx,
                    )
                    await SessionRow.update_session_kernels(
                        kernel_db_sess, sess_ctx,
                        kernel_data={
                            'status_info': 'no-available-instances',
                            'status_data': sql_json_increment(
                                KernelRow.status_data,
                                ('scheduler', 'retries'),
                                parent_updates={
                                    'last_try': datetime.now(tzutc()).isoformat(),
                                },
                            ),
                        },
                    )

            await execute_with_retry(_update)
            raise
        except Exception as e:
            log.exception(
                log_fmt + 'unexpected-error, during agent allocation',
                *log_args,
            )
            exc_data = convert_to_status_data(e)

            async def _update() -> None:
                async with self.db.begin_session() as kernel_db_sess:
                    await _rollback_predicate_mutations(
                        kernel_db_sess, sched_ctx, sess_ctx,
                    )
                    await SessionRow.update_session_kernels(
                        kernel_db_sess, sess_ctx,
                        kernel_data={
                            'status_info': 'scheduler-error',
                            'status_data': exc_data,
                        },
                    )

            await execute_with_retry(_update)
            raise

        async def _finalize_scheduled() -> None:
            async with self.db.begin_session() as kernel_db_sess:
                await SessionRow.update_session_kernels(
                    kernel_db_sess, sess_ctx,
                    kernel_data={
                        'agent_id': agent_alloc_ctx.id,
                        'agent_addr': agent_alloc_ctx.addr,
                        'scaling_group': sgroup_name,
                        'status': KernelStatus.SCHEDULED,
                        'status_info': 'scheduled',
                        'status_data': {},
                        'status_changed': datetime.now(tzutc()),
                    },
                )

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
        # Assign agent resource per kernel in the session.
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
                agent_alloc_ctx: AgentRow | None = None
                try:
                    agent = kernel.agent
                    if agent is None:
                        # limit agent candidates with requested image architecture
                        candidate_agents = [ag for ag in candidate_agents if ag.architecture == kernel.image.architecture]
                        agent = scheduler.assign_agent_for_kernel(candidate_agents, kernel)
                    assert agent is not None

                    available_agent_slots = agent.available_slots
                    if available_agent_slots is None:
                        raise InstanceNotAvailable("There is no such agent.")
                    if any(
                        val > available_agent_slots[slot]
                        for slot, val in kernel.requested_slots.items()
                    ):
                        raise InstanceNotAvailable(
                            "The resource slot does not have the enough remaining capacity.",
                        )

                    async def _reserve() -> Tuple[AgentRow, List[AgentRow]]:
                        async with agent_db_sess.begin_nested():
                            allocated_agent = await _reserve_agent(
                                agent_db_sess, sched_ctx,
                                sgroup_name, agent, kernel.requested_slots,
                                extra_conds=agent_query_extra_conds,
                            )
                            candidate_agents = await AgentRow.list_agents_by_sgroup(
                                agent_db_sess, sgroup_name,
                            )
                        return allocated_agent, candidate_agents

                    agent_alloc_ctx, candidate_agents = await execute_with_retry(_reserve)
                except InstanceNotAvailable:
                    log.debug(log_fmt + 'no-available-instances', *log_args)

                    async def _update() -> None:
                        async with self.db.begin_session() as kernel_db_sess:
                            await _rollback_predicate_mutations(
                                kernel_db_sess, sched_ctx, sess_ctx,
                            )
                            await SessionRow.update_session_kernels(
                                kernel_db_sess, sess_ctx,
                                kernel_data={
                                    'status_info': 'no-available-instances',
                                    'status_data': sql_json_increment(
                                        kernels.c.status_data,
                                        ('scheduler', 'retries'),
                                        parent_updates={
                                            'last_try': datetime.now(tzutc()).isoformat(),
                                        },
                                    ),
                                },
                                extra_cond=(KernelRow.id == kernel.id),
                            )

                    await execute_with_retry(_update)
                    raise
                except Exception as e:
                    log.exception(
                        log_fmt + 'unexpected-error, during agent allocation',
                        *log_args,
                    )
                    exc_data = convert_to_status_data(e)

                    async def _update() -> None:
                        async with self.db.begin_session() as kernel_db_sess:
                            await _rollback_predicate_mutations(
                                kernel_db_sess, sched_ctx, sess_ctx,
                            )
                            await SessionRow.update_session_kernels(
                                kernel_db_sess, sess_ctx,
                                kernel_data={
                                    'status_info': 'scheduler-error',
                                    'status_data': exc_data,
                                },
                                updated_kernel=kernel,
                            )

                    await execute_with_retry(_update)
                    raise
                else:
                    assert agent_alloc_ctx is not None
                    kernel_agent_bindings.append(KernelAgentBinding(kernel, agent_alloc_ctx))

        assert len(kernel_agent_bindings) == len(sess_ctx.kernels)
        # Proceed to PREPARING only when all kernels are successfully scheduled.

        async def _finalize_scheduled() -> None:
            async with self.db.begin_session() as kernel_db_sess:
                for binding in kernel_agent_bindings:
                    await SessionRow.update_session_kernels(
                        kernel_db_sess, sess_ctx,
                        kernel_data={
                            'agent_id': binding.agent_alloc_ctx.id,
                            'agent_addr': binding.agent_alloc_ctx.addr,
                            'scaling_group': sgroup_name,
                            'status': KernelStatus.SCHEDULED,
                            'status_info': 'scheduled',
                            'status_data': {},
                            'status_changed': datetime.now(tzutc()),
                        },
                        extra_cond=(KernelRow.agent_id == binding.agent_alloc_ctx.id)
                    )

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
                        target_sessions = await SessionRow.get_sessions_by_status(
                            db_sess, status=SessionStatus.SCHEDULED,
                        )
                        for session in target_sessions:
                            await SessionRow.update_session_kernels(
                                db_sess, session,
                                kernel_update={
                                    'status': KernelStatus.PREPARING,
                                    'status_changed': now,
                                    'status_info': "",
                                    'status_data': {},
                                },
                            )
                        return target_sessions

                scheduled_sessions: List[SessionRow]
                scheduled_sessions = await execute_with_retry(_mark_session_preparing)
                log.debug("prepare(): preparing {} session(s)", len(scheduled_sessions))
                async with aiotools.TaskGroup() as tg:
                    for scheduled_session in scheduled_sessions:
                        await self.registry.event_producer.produce_event(
                            SessionPreparingEvent(
                                scheduled_session.id,
                                scheduled_session.creation_id,
                            ),
                        )
                        tg.create_task(self.start_session(
                            sched_ctx,
                            scheduled_session,
                        ))

        except DBAPIError as e:
            if getattr(e.orig, 'pgcode', None) == '55P03':
                log.info("prepare(): cancelled due to advisory lock timeout; "
                         "maybe another prepare() call is still running")
                raise asyncio.CancelledError()
            raise

    async def start_session(
        self,
        sched_ctx: SchedulingContext,
        session: SessionRow,
    ) -> None:
        log_fmt = "prepare(s:{0.session_id}, type:{0.session_type}, name:{0.session_name}, " \
                  "ak:{0.access_key}, cluster_mode:{0.cluster_mode}): "
        log_args = (session, )
        log.debug(log_fmt + 'try-starting', *log_args)
        try:
            assert len(session.kernels) > 0
            await self.registry.start_session(sched_ctx, session)
        except Exception as e:
            status_data = convert_to_status_data(e, self.local_config['debug']['enabled'])
            log.warning(log_fmt + 'failed-starting: {1!r}', *log_args, status_data)
            # TODO: instead of instantly cancelling upon exception, we could mark it as
            #       SCHEDULED and retry within some limit using status_data.

            async def _mark_session_cancelled() -> None:
                async with self.db.begin_session() as db_sess:
                    affected_agents = set(k.agent for k in session.kernels)
                    for agent in affected_agents:
                        await recalc_agent_resource_occupancy(db_sess, agent)
                    await _rollback_predicate_mutations(db_sess, sched_ctx, session)
                    now = datetime.now(tzutc())
                    await SessionRow.update_session_kernels(
                        db_sess, session,
                        kernel_data={
                            'status': KernelStatus.CANCELLED,
                            'status_changed': now,
                            'status_info': "failed-to-start",
                            'status_data': status_data,
                            'terminated_at': now,
                        },
                    )

            log.debug(log_fmt + 'cleanup-start-failure: begin', *log_args)
            try:
                await execute_with_retry(_mark_session_cancelled)
                await self.registry.event_producer.produce_event(
                    SessionCancelledEvent(
                        session.id,
                        session.creation_id,
                        "failed-to-start",
                    ),
                )
                async with self.db.begin_readonly_session() as db_sess:
                    query = (
                        sa.select(KernelRow.id, KernelRow.container_id)
                        .where(KernelRow.session_id == session.id)
                    )
                    kerns = (await db_sess.execute(query)).scalars().all()
                    # rows = (await db_sess.execute(query)).fetchall()
                    cid_map = {kern.id: kern.container_id for kern in kerns}
                destroyed_kernels = [
                    {
                        "agent": k.agent_id,
                        "agent_addr": k.agent_addr,
                        "id": k.id,
                        "container_id": cid_map[k.id],
                    }
                    for k in session.kernels
                ]
                await self.registry.destroy_session_lowlevel(
                    session.id, destroyed_kernels,
                )
                await self.registry.recalc_resource_usage()
            except Exception as destroy_err:
                log.error(log_fmt + 'cleanup-start-failure: error', *log_args, exc_info=destroy_err)
            finally:
                log.debug(log_fmt + 'cleanup-start-failure: done', *log_args)
        else:
            log.info(log_fmt + 'started', *log_args)


async def _list_managed_sessions(
    db_sess: SASession,
    scheduler: AbstractScheduler,
    sgroup: ScalingGroupRow,
) -> Tuple[List[SessionRow], List[SessionRow], List[SessionRow]]:
    """
    Return three lists of sessions.
    first is a list of existing sessions,
    second is pending sessions and third is to-be-cancelled sessions due to pending timeout.
    """

    session_ids = [s.id for s in sgroup.sessions]
    managed_sessions: List[SessionRow]
    managed_sessions = await SessionRow.get_managed_sessions(db_sess, session_ids)

    pending_timeout: timedelta = scheduler.sgroup_opts.pending_timeout
    candidates: List[SessionRow] = []
    cancelleds: List[SessionRow] = []
    existings: List[SessionRow] = []

    now = datetime.now(tzutc())
    key_func = lambda s: (s.status, s.created_at)
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
    db_sess: SASession,
    sched_ctx: SchedulingContext,
    scaling_group: str,
    agent: AgentRow,
    requested_slots: ResourceSlot,
    extra_conds = None,
) -> AgentRow:
    current_occupied_slots = agent.occupied_slots
    if current_occupied_slots is None:
        raise RuntimeError(f"No agent available. condition = `{extra_conds}`")
    agent.occupied_slots = current_occupied_slots + requested_slots

    # Explicitly flush dirty agent data on db session
    await db_sess.flush()
    return agent


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
    await recalc_concurrency_used(db_sess, sched_ctx.registry.redis_stat, AccessKey(session.kp_access_key))
