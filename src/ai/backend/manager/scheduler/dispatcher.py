from __future__ import annotations

import asyncio
import logging
import pkg_resources
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

import aiotools
from dateutil.tz import tzutc
import sqlalchemy as sa
from sqlalchemy.engine.row import Row
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import (
    AsyncConnection as SAConnection,
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
    ClusterMode,
    ResourceSlot,
)

from ai.backend.manager.types import DistributedLockFactory

from ..api.exceptions import GenericBadRequest, InstanceNotAvailable
from ..defs import (
    LockID,
)
from ..exceptions import convert_to_status_data
from ..models import (
    agents, kernels, scaling_groups,
    recalc_agent_resource_occupancy,
    recalc_concurrency_used,
    AgentStatus, KernelStatus,
    AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES,
)
from ..models.scaling_group import ScalingGroupOpts
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
    for entrypoint in pkg_resources.iter_entry_points(entry_prefix):
        if entrypoint.name == name:
            log.debug('loading scheduler plugin "{}" from {}', name, entrypoint.module_name)
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
                async with self.db.begin_readonly() as conn:
                    query = (
                        sa.select([agents.c.scaling_group])
                        .select_from(agents)
                        .where(agents.c.status == AgentStatus.ALIVE)
                        .group_by(agents.c.scaling_group)
                    )
                    result = await conn.execute(query)
                    schedulable_scaling_groups = [
                        row.scaling_group for row in result.fetchall()
                    ]
                for sgroup_name in schedulable_scaling_groups:
                    try:
                        await self._schedule_in_sgroup(
                            sched_ctx, sgroup_name,
                        )
                    except InstanceNotAvailable:
                        # Proceed to the next scaling group and come back later.
                        log.debug('schedule({}): instance not available', sgroup_name)
                    except Exception as e:
                        log.exception('schedule({}): scheduling error!\n{}', sgroup_name, repr(e))
        except DBAPIError as e:
            if getattr(e.orig, 'pgcode', None) == '55P03':
                log.info("schedule(): cancelled due to advisory lock timeout; "
                         "maybe another schedule() call is still running")
                raise asyncio.CancelledError()
            raise

    async def _load_scheduler(
        self,
        db_conn: SAConnection,
        sgroup_name: str,
    ) -> AbstractScheduler:
        query = (
            sa.select([scaling_groups.c.scheduler, scaling_groups.c.scheduler_opts])
            .select_from(scaling_groups)
            .where(scaling_groups.c.name == sgroup_name)
        )
        result = await db_conn.execute(query)
        row = result.first()
        scheduler_name = row['scheduler']
        sgroup_opts: ScalingGroupOpts = row['scheduler_opts']
        global_scheduler_opts = {}
        if self.shared_config['plugins']['scheduler']:
            global_scheduler_opts = self.shared_config['plugins']['scheduler'].get(scheduler_name, {})
        scheduler_specific_config = {**global_scheduler_opts, **sgroup_opts.config}
        return load_scheduler(scheduler_name, sgroup_opts, scheduler_specific_config)

    async def _schedule_in_sgroup(
        self,
        sched_ctx: SchedulingContext,
        sgroup_name: str,
    ) -> None:
        async with self.db.begin_readonly() as kernel_db_conn:
            scheduler = await self._load_scheduler(kernel_db_conn, sgroup_name)
            pending_session_rows, cancelled_session_rows = \
                await _list_pending_sessions(kernel_db_conn, scheduler, sgroup_name)
            pending_sessions = PendingSession.from_rows(pending_session_rows)
            existing_sessions = await _list_existing_sessions(kernel_db_conn, sgroup_name)

        if cancelled_session_rows:
            now = datetime.now(tzutc())

            async def _apply_cancellation():
                async with self.db.begin() as db_conn:
                    query = kernels.update().values({
                        'status': KernelStatus.CANCELLED,
                        'status_changed': now,
                        'status_info': "pending-timeout",
                        'terminated_at': now,
                    }).where(kernels.c.session_id.in_([
                        item['session_id'] for item in cancelled_session_rows
                    ]))
                    await db_conn.execute(query)

            await execute_with_retry(_apply_cancellation)
            for item in cancelled_session_rows:
                await self.event_producer.produce_event(
                    SessionCancelledEvent(
                        item['session_id'],
                        item['session_creation_id'],
                        reason="pending timeout",
                    ),
                )

        log.debug(
            "running scheduler (sgroup:{}, pending:{}, existing:{}, cancelled:{})",
            sgroup_name, len(pending_sessions), len(existing_sessions), len(cancelled_session_rows),
        )
        zero = ResourceSlot()
        num_scheduled = 0
        while len(pending_sessions) > 0:

            async with self.db.begin_readonly() as conn:
                candidate_agents = await _list_agents_by_sgroup(conn, sgroup_name)
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
                if sess_ctx.session_id == picked_session_id:
                    break
            else:
                # no matching entry for picked session?
                raise RuntimeError('should not reach here')
            sess_ctx = pending_sessions.pop(picked_idx)
            requested_architectures = set([
                x.image_ref.architecture for x in sess_ctx.kernels
            ])
            candidate_agents = list(
                filter(
                    lambda x: x.architecture in requested_architectures,
                    candidate_agents,
                ),
            )

            log_fmt = 'schedule(s:{}, type:{}, name:{}, ak:{}, cluster_mode:{}): '
            log_args = (
                sess_ctx.session_id,
                sess_ctx.session_type,
                sess_ctx.session_name,
                sess_ctx.access_key,
                sess_ctx.cluster_mode,
            )
            _log_fmt.set(log_fmt)
            _log_args.set(log_args)
            log.debug(log_fmt + 'try-scheduling', *log_args)

            async def _check_predicates() -> List[Tuple[str, Union[Exception, PredicateResult]]]:
                check_results: List[Tuple[str, Union[Exception, PredicateResult]]] = []
                async with self.db.begin() as kernel_db_conn:
                    predicates: Sequence[Tuple[str, Awaitable[PredicateResult]]] = [
                        (
                            'reserved_time',
                            check_reserved_batch_session(kernel_db_conn, sched_ctx, sess_ctx),
                        ),
                        ('concurrency', check_concurrency(kernel_db_conn, sched_ctx, sess_ctx)),
                        ('dependencies', check_dependencies(kernel_db_conn, sched_ctx, sess_ctx)),
                        (
                            'keypair_resource_limit',
                            check_keypair_resource_limit(kernel_db_conn, sched_ctx, sess_ctx),
                        ),
                        (
                            'user_group_resource_limit',
                            check_group_resource_limit(kernel_db_conn, sched_ctx, sess_ctx),
                        ),
                        (
                            'domain_resource_limit',
                            check_domain_resource_limit(kernel_db_conn, sched_ctx, sess_ctx),
                        ),
                        (
                            'scaling_group_resource_limit',
                            check_scaling_group(kernel_db_conn, sched_ctx, sess_ctx),
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
                    async with self.db.begin() as conn:
                        await _rollback_predicate_mutations(
                            conn, sched_ctx, sess_ctx,
                        )
                        query = kernels.update().values({
                            'status_info': "predicate-checks-failed",
                            'status_data': sql_json_increment(
                                kernels.c.status_data,
                                ('scheduler', 'retries'),
                                parent_updates={
                                    'last_try': datetime.now(tzutc()).isoformat(),
                                    'failed_predicates': failed_predicates,
                                    'passed_predicates': passed_predicates,
                                },
                            ),
                        }).where(kernels.c.id == sess_ctx.session_id)
                        await conn.execute(query)

                await execute_with_retry(_update)
                # Predicate failures are *NOT* permanent errors.
                # We need to retry the scheduling afterwards.
                continue
            else:
                async def _update() -> None:
                    async with self.db.begin() as conn:
                        query = kernels.update().values({
                            'status_data': sql_json_merge(
                                kernels.c.status_data,
                                ('scheduler',),
                                {
                                    'last_try': datetime.now(tzutc()).isoformat(),
                                    'failed_predicates': failed_predicates,
                                    'passed_predicates': passed_predicates,
                                },
                            ),
                        }).where(kernels.c.id == sess_ctx.session_id)
                        await conn.execute(query)

                await execute_with_retry(_update)

            if sess_ctx.cluster_mode == ClusterMode.SINGLE_NODE:
                # Single node session can't have multiple containers with different arch
                if len(requested_architectures) > 1:
                    raise GenericBadRequest(
                        'Cannot assign multiple kernels with different architecture'
                        'on single node session',
                    )
                requested_architecture = requested_architectures.pop()
                candidate_agents = list(
                    filter(
                        lambda x: x.architecture == requested_architecture,
                        candidate_agents,
                    ),
                )
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
        candidate_agents: Sequence[AgentContext],
        sess_ctx: PendingSession,
        check_results: List[Tuple[str, Union[Exception, PredicateResult]]],
    ) -> None:
        # Assign agent resource per session.
        log_fmt = _log_fmt.get("")
        log_args = _log_args.get(tuple())
        try:
            # If sess_ctx.agent_id is already set for manual assignment by superadmin,
            # skip assign_agent_for_session().
            agent_id = None
            if sess_ctx.agent_id is not None:
                agent_id = sess_ctx.agent_id
            else:
                agent_id = scheduler.assign_agent_for_session(candidate_agents, sess_ctx)
            async with self.db.begin() as agent_db_conn:
                query = (
                    sa.select([agents.c.available_slots])
                    .select_from(agents)
                    .where(agents.c.id == agent_id)
                )
                available_agent_slots = (await agent_db_conn.execute(query)).scalar()
                # if pass the available test
                if available_agent_slots is None:
                    raise InstanceNotAvailable("There is no such agent.")
                for key in available_agent_slots:
                    if available_agent_slots[key] >= sess_ctx.requested_slots[key]:
                        continue
                    else:
                        raise InstanceNotAvailable(
                            "The resource slot does not have the enough remaining capacity.",
                        )
                agent_alloc_ctx = await _reserve_agent(
                    sched_ctx, agent_db_conn, sgroup_name, agent_id, sess_ctx.requested_slots,
                )
        except InstanceNotAvailable:
            log.debug(log_fmt + 'no-available-instances', *log_args)

            async def _update() -> None:
                async with self.db.begin() as kernel_db_conn:
                    await _rollback_predicate_mutations(
                        kernel_db_conn, sched_ctx, sess_ctx,
                    )
                    query = kernels.update().values({
                        'status_info': "no-available-instances",
                        'status_data': sql_json_increment(
                            kernels.c.status_data,
                            ('scheduler', 'retries'),
                            parent_updates={
                                'last_try': datetime.now(tzutc()).isoformat(),
                            },
                        ),
                    }).where(kernels.c.id == sess_ctx.session_id)
                    await kernel_db_conn.execute(query)

            await execute_with_retry(_update)
            raise
        except Exception as e:
            log.exception(
                log_fmt + 'unexpected-error, during agent allocation',
                *log_args,
            )
            exc_data = convert_to_status_data(e)

            async def _update() -> None:
                async with self.db.begin() as kernel_db_conn:
                    await _rollback_predicate_mutations(
                        kernel_db_conn, sched_ctx, sess_ctx,
                    )
                    query = kernels.update().values({
                        'status_info': "scheduler-error",
                        'status_data': exc_data,
                    }).where(kernels.c.id == sess_ctx.session_id)
                    await kernel_db_conn.execute(query)

            await execute_with_retry(_update)
            raise

        async def _finalize_scheduled() -> None:
            async with self.db.begin() as kernel_db_conn:
                query = kernels.update().values({
                    'agent': agent_alloc_ctx.agent_id,
                    'agent_addr': agent_alloc_ctx.agent_addr,
                    'scaling_group': sgroup_name,
                    'status': KernelStatus.SCHEDULED,
                    'status_info': 'scheduled',
                    'status_data': {},
                    'status_changed': datetime.now(tzutc()),
                }).where(kernels.c.session_id == sess_ctx.session_id)
                await kernel_db_conn.execute(query)

        await execute_with_retry(_finalize_scheduled)
        await self.registry.event_producer.produce_event(
            SessionScheduledEvent(sess_ctx.session_id, sess_ctx.session_creation_id),
        )

    async def _schedule_multi_node_session(
        self,
        sched_ctx: SchedulingContext,
        scheduler: AbstractScheduler,
        sgroup_name: str,
        candidate_agents: Sequence[AgentContext],
        sess_ctx: PendingSession,
        check_results: List[Tuple[str, Union[Exception, PredicateResult]]],
    ) -> None:
        # Assign agent resource per kernel in the session.
        log_fmt = _log_fmt.get()
        log_args = _log_args.get()
        agent_query_extra_conds = None
        kernel_agent_bindings: List[KernelAgentBinding] = []
        async with self.db.begin() as agent_db_conn:
            # This outer transaction is rolled back when any exception occurs inside,
            # including scheduling failures of a kernel.
            # It ensures that occupied_slots are recovered when there are partial
            # scheduling failures.
            for kernel in sess_ctx.kernels:
                agent_alloc_ctx: AgentAllocationContext | None = None
                try:
                    agent_id: AgentId | None
                    if kernel.agent_id is not None:
                        agent_id = kernel.agent_id
                    else:
                        # limit agent candidates with requested image architecture
                        candidate_agents = list(
                            filter(
                                lambda x: x.architecture == kernel.image_ref.architecture,
                                candidate_agents,
                            ),
                        )
                        agent_id = scheduler.assign_agent_for_kernel(candidate_agents, kernel)
                    assert agent_id is not None

                    query = (
                        sa.select([agents.c.available_slots])
                        .select_from(agents)
                        .where(agents.c.id == agent_id)
                    )
                    available_agent_slots = (await agent_db_conn.execute(query)).scalar()
                    if available_agent_slots is None:
                        raise InstanceNotAvailable("There is no such agent.")
                    available_test_pass = False
                    for key in available_agent_slots:
                        if available_agent_slots[key] >= kernel.requested_slots[key]:
                            available_test_pass = True
                            continue
                        else:
                            raise InstanceNotAvailable(
                                "The resource slot does not have the enough remaining capacity.",
                            )
                    if available_test_pass:

                        async def _reserve() -> None:
                            nonlocal agent_alloc_ctx, candidate_agents
                            async with agent_db_conn.begin_nested():
                                agent_alloc_ctx = await _reserve_agent(
                                    sched_ctx, agent_db_conn,
                                    sgroup_name, agent_id, kernel.requested_slots,
                                    extra_conds=agent_query_extra_conds,
                                )
                                candidate_agents = await _list_agents_by_sgroup(
                                    agent_db_conn, sgroup_name,
                                )

                        await execute_with_retry(_reserve)
                except InstanceNotAvailable:
                    log.debug(log_fmt + 'no-available-instances', *log_args)

                    async def _update() -> None:
                        async with self.db.begin() as kernel_db_conn:
                            await _rollback_predicate_mutations(
                                kernel_db_conn, sched_ctx, sess_ctx,
                            )
                            query = kernels.update().values({
                                'status_info': "no-available-instances",
                                'status_data': sql_json_increment(
                                    kernels.c.status_data,
                                    ('scheduler', 'retries'),
                                    parent_updates={
                                        'last_try': datetime.now(tzutc()).isoformat(),
                                    },
                                ),
                            }).where(kernels.c.id == kernel.kernel_id)
                            await kernel_db_conn.execute(query)

                    await execute_with_retry(_update)
                    raise
                except Exception as e:
                    log.exception(
                        log_fmt + 'unexpected-error, during agent allocation',
                        *log_args,
                    )
                    exc_data = convert_to_status_data(e)

                    async def _update() -> None:
                        async with self.db.begin() as kernel_db_conn:
                            await _rollback_predicate_mutations(
                                kernel_db_conn, sched_ctx, sess_ctx,
                            )
                            query = kernels.update().values({
                                'status_info': "scheduler-error",
                                'status_data': exc_data,
                            }).where(kernels.c.id == kernel.kernel_id)
                            await kernel_db_conn.execute(query)

                    await execute_with_retry(_update)
                    raise
                else:
                    assert agent_alloc_ctx is not None
                    kernel_agent_bindings.append(KernelAgentBinding(kernel, agent_alloc_ctx))

        assert len(kernel_agent_bindings) == len(sess_ctx.kernels)
        # Proceed to PREPARING only when all kernels are successfully scheduled.

        async def _finalize_scheduled() -> None:
            async with self.db.begin() as kernel_db_conn:
                for binding in kernel_agent_bindings:
                    query = kernels.update().values({
                        'agent': binding.agent_alloc_ctx.agent_id,
                        'agent_addr': binding.agent_alloc_ctx.agent_addr,
                        'scaling_group': sgroup_name,
                        'status': KernelStatus.SCHEDULED,
                        'status_info': 'scheduled',
                        'status_data': {},
                        'status_changed': datetime.now(tzutc()),
                    }).where(kernels.c.id == binding.kernel.kernel_id)
                    await kernel_db_conn.execute(query)

        await execute_with_retry(_finalize_scheduled)
        await self.registry.event_producer.produce_event(
            SessionScheduledEvent(sess_ctx.session_id, sess_ctx.session_creation_id),
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

                async def _mark_session_preparing() -> Sequence[PendingSession]:
                    async with self.db.begin() as conn:
                        update_query = (
                            sa.update(kernels)
                            .values({
                                'status': KernelStatus.PREPARING,
                                'status_changed': now,
                                'status_info': "",
                                'status_data': {},
                            })
                            .where(
                                (kernels.c.status == KernelStatus.SCHEDULED),
                            )
                            .returning(kernels.c.id)
                        )
                        rows = (await conn.execute(update_query)).fetchall()
                        if len(rows) == 0:
                            return []
                        target_kernel_ids = [r['id'] for r in rows]
                        select_query = (
                            PendingSession.base_query()
                            .where(
                                kernels.c.id.in_(target_kernel_ids),
                            )
                        )
                        rows = (await conn.execute(select_query)).fetchall()
                        return PendingSession.from_rows(rows)

                scheduled_sessions = await execute_with_retry(_mark_session_preparing)
                log.debug("prepare(): preparing {} session(s)", len(scheduled_sessions))
                async with aiotools.TaskGroup() as tg:
                    for scheduled_session in scheduled_sessions:
                        await self.registry.event_producer.produce_event(
                            SessionPreparingEvent(
                                scheduled_session.session_id,
                                scheduled_session.session_creation_id,
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
        session: PendingSession,
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
                async with self.db.begin() as db_conn:
                    affected_agents = set(k.agent_id for k in session.kernels)
                    for agent_id in affected_agents:
                        await recalc_agent_resource_occupancy(db_conn, agent_id)
                    await _rollback_predicate_mutations(db_conn, sched_ctx, session)
                    now = datetime.now(tzutc())
                    update_query = sa.update(kernels).values({
                        'status': KernelStatus.CANCELLED,
                        'status_changed': now,
                        'status_info': "failed-to-start",
                        'status_data': status_data,
                        'terminated_at': now,
                    }).where(kernels.c.session_id == session.session_id)
                    await db_conn.execute(update_query)

            log.debug(log_fmt + 'cleanup-start-failure: begin', *log_args)
            try:
                await execute_with_retry(_mark_session_cancelled)
                await self.registry.event_producer.produce_event(
                    SessionCancelledEvent(
                        session.session_id,
                        session.session_creation_id,
                        "failed-to-start",
                    ),
                )
                async with self.db.begin_readonly() as db_conn:
                    query = (
                        sa.select([kernels.c.id, kernels.c.container_id])
                        .where(kernels.c.session_id == session.session_id)
                    )
                    rows = (await db_conn.execute(query)).fetchall()
                    cid_map = {row['id']: row['container_id'] for row in rows}
                destroyed_kernels = [
                    {
                        "agent": k.agent_id,
                        "agent_addr": k.agent_addr,
                        "id": k.kernel_id,
                        "container_id": cid_map[k.kernel_id],
                    }
                    for k in session.kernels
                ]
                await self.registry.destroy_session_lowlevel(
                    session.session_id, destroyed_kernels,
                )
                await self.registry.recalc_resource_usage()
            except Exception as destroy_err:
                log.error(log_fmt + 'cleanup-start-failure: error', *log_args, exc_info=destroy_err)
            finally:
                log.debug(log_fmt + 'cleanup-start-failure: done', *log_args)
        else:
            log.info(log_fmt + 'started', *log_args)


async def _list_pending_sessions(
    db_conn: SAConnection,
    scheduler: AbstractScheduler,
    sgroup_name: str,
) -> tuple[list[Row], list[Row]]:
    """
    Return two lists of pending sessions and to-be-cancelled sessions due to pending timeout.
    """
    pending_timeout: timedelta = scheduler.sgroup_opts.pending_timeout
    query = (
        PendingSession.base_query()
        .where(
            (kernels.c.status == KernelStatus.PENDING) &
            (
                (kernels.c.scaling_group == sgroup_name)
            ),
        )
    )
    rows = (await db_conn.execute(query)).fetchall()
    candidate_rows = []
    cancelled_rows = []
    now = datetime.now(tzutc())
    for row in rows:
        elapsed_pending_time = now - row['created_at']
        if pending_timeout.total_seconds() > 0 and elapsed_pending_time >= pending_timeout:
            cancelled_rows.append(row)
        else:
            candidate_rows.append(row)
    return candidate_rows, cancelled_rows


async def _list_existing_sessions(
    db_conn: SAConnection,
    sgroup_name: str,
) -> List[ExistingSession]:
    query = (
        ExistingSession.base_query()
        .where(
            (kernels.c.status.in_(AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES)) &
            (kernels.c.scaling_group == sgroup_name),
        )
    )
    rows = (await db_conn.execute(query)).fetchall()
    return ExistingSession.from_rows(rows)


async def _list_agents_by_sgroup(
    db_conn: SAConnection,
    sgroup_name: str,
) -> Sequence[AgentContext]:
    query = (
        sa.select([
            agents.c.id,
            agents.c.architecture,
            agents.c.addr,
            agents.c.scaling_group,
            agents.c.available_slots,
            agents.c.occupied_slots,
        ])
        .select_from(agents)
        .where(
            (agents.c.status == AgentStatus.ALIVE) &
            (agents.c.scaling_group == sgroup_name) &
            (agents.c.schedulable == true()),
        )
    )
    items = []
    for row in (await db_conn.execute(query)):
        item = AgentContext(
            row['id'],
            row['addr'],
            row['architecture'],
            row['scaling_group'],
            row['available_slots'],
            row['occupied_slots'],
        )
        items.append(item)
    return items


async def _reserve_agent(
    sched_ctx: SchedulingContext,
    db_conn: SAConnection,
    scaling_group: str,
    agent_id: Optional[AgentId],
    requested_slots: ResourceSlot,
    extra_conds: Any = None,
) -> AgentAllocationContext:
    query = (
        sa.select([agents.c.occupied_slots])
        .select_from(agents)
        .where(agents.c.id == agent_id)
        .with_for_update()
    )
    if extra_conds is not None:
        query = query.where(extra_conds)
    current_occupied_slots = (await db_conn.execute(query)).scalar()
    if current_occupied_slots is None:
        raise RuntimeError(f"No agent matching condition: {extra_conds}")
    update_query = (
        sa.update(agents)
        .values({
            'occupied_slots': current_occupied_slots + requested_slots,
        })
        .where(agents.c.id == agent_id)
    )
    await db_conn.execute(update_query)
    # Get the agent address for later RPC calls
    query = (sa.select([agents.c.addr])
               .where(agents.c.id == agent_id))
    agent_addr = await db_conn.scalar(query)
    assert agent_addr is not None
    return AgentAllocationContext(agent_id, agent_addr, scaling_group)


async def _rollback_predicate_mutations(
    db_conn: SAConnection,
    sched_ctx: SchedulingContext,
    session: PendingSession,
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
    await recalc_concurrency_used(db_conn, sched_ctx.registry.redis_stat, session.access_key)
