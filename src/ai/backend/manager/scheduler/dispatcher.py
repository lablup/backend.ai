from __future__ import annotations

import asyncio
import logging
import uuid
from collections.abc import (
    Awaitable,
    Callable,
    Mapping,
    Sequence,
)
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from functools import partial
from typing import (
    Any,
    Optional,
    Union,
    cast,
)

import aiotools
import async_timeout
from dateutil.tz import tzutc
from sqlalchemy.exc import DBAPIError

from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.distributed import GlobalTimer
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.events.dispatcher import (
    EventProducer,
)
from ai.backend.common.events.event_types.kernel.types import (
    KernelLifecycleEventReason,
)
from ai.backend.common.events.event_types.model_serving.anycast import (
    RouteCreatedAnycastEvent,
)
from ai.backend.common.events.event_types.schedule.anycast import (
    DoCheckPrecondEvent,
    DoScaleEvent,
    DoScheduleEvent,
    DoStartSessionEvent,
)
from ai.backend.common.events.event_types.session.anycast import (
    DoUpdateSessionStatusEvent,
    SessionCancelledAnycastEvent,
    SessionCheckingPrecondAnycastEvent,
    SessionPreparingAnycastEvent,
    SessionScheduledAnycastEvent,
)
from ai.backend.common.events.event_types.session.broadcast import (
    SessionCancelledBroadcastEvent,
    SessionPreparingBroadcastEvent,
    SessionScheduledBroadcastEvent,
)
from ai.backend.common.json import dump_json_str
from ai.backend.common.plugin.hook import PASSED, HookResult
from ai.backend.common.types import (
    AgentId,
    AgentSelectionStrategy,
    ClusterMode,
    ResourceSlot,
    SessionId,
    SessionTypes,
    aobject,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.config.loader.legacy_etcd_loader import LegacyEtcdLoader
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.model_serving.types import EndpointLifecycle
from ai.backend.manager.models.kernel import USER_RESOURCE_OCCUPYING_KERNEL_STATUSES
from ai.backend.manager.types import DistributedLockFactory
from ai.backend.plugin.entrypoint import scan_entrypoints

from ..defs import SERVICE_MAX_RETRIES, START_SESSION_TIMEOUT_SEC, LockID
from ..errors.common import (
    GenericBadRequest,
    GenericForbidden,
)
from ..errors.kernel import SessionNotFound
from ..errors.resource import InstanceNotAvailable
from ..exceptions import convert_to_status_data
from ..models import (
    AgentRow,
    EndpointRow,
    KernelRow,
    RouteStatus,
    ScalingGroupOpts,
    SessionRow,
)
from ..models.utils import (
    execute_with_retry,
    retry_txn,
)
from ..registry import AgentRegistry
from ..repositories.schedule.repository import ScheduleRepository
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

__all__ = (
    "load_scheduler",
    "load_agent_selector",
    "SchedulerDispatcher",
)

# Memoization cache for scheduler and agent selector classes
_scheduler_class_cache: dict[str, type[AbstractScheduler]] = {}
_agent_selector_class_cache: dict[str, type[AbstractAgentSelector]] = {}

log = BraceStyleAdapter(logging.getLogger("ai.backend.manager.scheduler"))

_log_fmt: ContextVar[str] = ContextVar("_log_fmt")
_log_args: ContextVar[tuple[Any, ...]] = ContextVar("_log_args")


def _load_scheduler_class(name: str) -> type[AbstractScheduler]:
    """Load and memoize scheduler class by name."""
    if name not in _scheduler_class_cache:
        entry_prefix = "backendai_scheduler_v10"
        for entrypoint in scan_entrypoints(entry_prefix):
            if entrypoint.name == name:
                log.debug('loading scheduler plugin "{}" from {}', name, entrypoint.module)
                scheduler_cls = entrypoint.load()
                _scheduler_class_cache[name] = scheduler_cls
                return scheduler_cls
        raise ImportError("Cannot load the scheduler plugin", name)
    return _scheduler_class_cache[name]


def load_scheduler(
    name: str,
    sgroup_opts: ScalingGroupOpts,
    scheduler_config: Mapping[str, Any],
) -> AbstractScheduler:
    scheduler_cls = _load_scheduler_class(name)
    return scheduler_cls(sgroup_opts, scheduler_config)


def _load_agent_selector_class(name: str) -> type[AbstractAgentSelector]:
    """Load and memoize agent selector class by name."""
    if name not in _agent_selector_class_cache:
        entry_prefix = "backendai_agentselector_v10"
        for entrypoint in scan_entrypoints(entry_prefix):
            if entrypoint.name == name:
                log.debug('loading agent-selector plugin "{}" from {}', name, entrypoint.module)
                selector_cls = entrypoint.load()
                _agent_selector_class_cache[name] = selector_cls
                return selector_cls
        raise ImportError("Cannot load the agent-selector plugin", name)
    return _agent_selector_class_cache[name]


def load_agent_selector(
    name: str,
    sgroup_opts: ScalingGroupOpts,
    selector_config: Mapping[str, Any],
    agent_selection_resource_priority: list[str],
    legacy_etcd_loader: LegacyEtcdLoader,
) -> AbstractAgentSelector[AbstractResourceGroupState]:
    def create_agent_selector(
        selector_cls: type[AbstractAgentSelector[T_ResourceGroupState]],
    ) -> AbstractAgentSelector[T_ResourceGroupState]:
        # An extra inner function to parametrize the generic type arguments
        state_cls = selector_cls.get_state_cls()
        state_store = DefaultResourceGroupStateStore(state_cls, legacy_etcd_loader)
        return selector_cls(
            sgroup_opts,
            selector_config,
            agent_selection_resource_priority,
            state_store=state_store,
        )

    selector_cls = _load_agent_selector_class(name)
    return create_agent_selector(selector_cls)


@dataclass
class LoadSchedulerArgs:
    scheduler_name: str
    sgroup_opts: ScalingGroupOpts


@dataclass
class LoadAgentSelectorArgs:
    sgroup_opts: ScalingGroupOpts
    pending_session_id: uuid.UUID
    pending_session_type: SessionTypes


class SchedulerDispatcher(aobject):
    config_provider: ManagerConfigProvider
    registry: AgentRegistry
    etcd: AsyncEtcd
    schedule_repository: ScheduleRepository

    event_producer: EventProducer
    schedule_timer: GlobalTimer
    check_precond_timer: GlobalTimer
    session_start_timer: GlobalTimer
    scale_timer: GlobalTimer
    update_session_status_timer: GlobalTimer

    _valkey_live: ValkeyLiveClient
    _valkey_stat: ValkeyStatClient

    def __init__(
        self,
        config_provider: ManagerConfigProvider,
        etcd: AsyncEtcd,
        event_producer: EventProducer,
        lock_factory: DistributedLockFactory,
        registry: AgentRegistry,
        valkey_live: ValkeyLiveClient,
        valkey_stat: ValkeyStatClient,
        schedule_repository: ScheduleRepository,
    ) -> None:
        self.config_provider = config_provider
        self.etcd = etcd
        self.event_producer = event_producer
        self.registry = registry
        self.lock_factory = lock_factory
        self._valkey_live = valkey_live
        self._valkey_stat = valkey_stat
        self.schedule_repository = schedule_repository

    @classmethod
    async def create(
        cls,
        config_provider: ManagerConfigProvider,
        etcd: AsyncEtcd,
        event_producer: EventProducer,
        lock_factory: DistributedLockFactory,
        registry: AgentRegistry,
        valkey_live: ValkeyLiveClient,
        valkey_stat: ValkeyStatClient,
        schedule_repository: ScheduleRepository,
    ) -> SchedulerDispatcher:
        instance = cls(
            config_provider,
            etcd,
            event_producer,
            lock_factory,
            registry,
            valkey_live,
            valkey_stat,
            schedule_repository,
        )
        await instance.__ainit__()
        return instance

    async def __ainit__(self) -> None:
        self.schedule_timer = GlobalTimer(
            self.lock_factory(LockID.LOCKID_SCHEDULE_TIMER, 10.0),
            self.event_producer,
            lambda: DoScheduleEvent(),
            interval=10.0,
            task_name="schedule_timer",
        )
        self.session_start_timer = GlobalTimer(
            self.lock_factory(LockID.LOCKID_START_TIMER, 10.0),
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
        await self._valkey_live.close()
        await self._valkey_stat.close()
        log.info("Session scheduler stopped")

    async def schedule(
        self,
        event_name: str,
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
        await self._mark_scheduler_start(ScheduleType.SCHEDULE, event_name)
        known_slot_types = await self.config_provider.legacy_etcd_config_loader.get_resource_slots()
        sched_ctx = SchedulingContext(
            registry=self.registry,
            known_slot_types=known_slot_types,
        )

        lock_lifetime = self.config_provider.config.manager.session_schedule_lock_lifetime
        try:
            # The schedule() method should be executed with a global lock
            # as its individual steps are composed of many short-lived transactions.
            async with self.lock_factory(LockID.LOCKID_SCHEDULE, lock_lifetime):
                schedulable_scaling_groups = (
                    await self.schedule_repository.get_schedulable_scaling_groups()
                )
                for sgroup_name in schedulable_scaling_groups:
                    try:
                        await self._schedule_in_sgroup(
                            sched_ctx,
                            sgroup_name,
                        )
                        await self._update_scheduler_mark(
                            ScheduleType.SCHEDULE,
                            {
                                "resource_group": sgroup_name,
                            },
                        )
                    except Exception as e:
                        log.exception("schedule({}): scheduling error!\n{}", sgroup_name, repr(e))
                await self._update_scheduler_mark(
                    ScheduleType.SCHEDULE,
                    {
                        "finish_time": datetime.now(tzutc()).isoformat(),
                    },
                )
        except DBAPIError as e:
            if getattr(e.orig, "pgcode", None) == "55P03":
                log.info(
                    "schedule(): cancelled due to advisory lock timeout; "
                    "maybe another schedule() call is still running"
                )
                raise asyncio.CancelledError()
            raise

    def _load_scheduler(self, args: LoadSchedulerArgs) -> AbstractScheduler:
        global_scheduler_opts = {}
        if self.config_provider.config.plugins.scheduler:
            global_scheduler_opts = self.config_provider.config.plugins.scheduler.get(
                args.scheduler_name, {}
            )
        scheduler_config = {**global_scheduler_opts, **args.sgroup_opts.config}

        return load_scheduler(args.scheduler_name, args.sgroup_opts, scheduler_config)

    async def _load_agent_selector(self, args: LoadAgentSelectorArgs) -> AbstractAgentSelector:
        sgroup_opts = args.sgroup_opts

        # TODO: Remove "dynamic_config after refactoring.
        dynamic_config: dict[str, Any] = {}

        match sgroup_opts.agent_selection_strategy:
            case AgentSelectionStrategy.LEGACY:
                agselector_name = "legacy"
            case AgentSelectionStrategy.ROUNDROBIN:
                agselector_name = "roundrobin"
            case AgentSelectionStrategy.CONCENTRATED:
                if (
                    sgroup_opts.enforce_spreading_endpoint_replica
                    and SessionTypes(args.pending_session_type) == SessionTypes.INFERENCE
                ):
                    endpoint_id = await self.schedule_repository.get_endpoint_for_session(
                        SessionId(args.pending_session_id)
                    )
                    if endpoint_id:
                        dynamic_config[
                            "kernel_counts_at_same_endpoint"
                        ] = await self.schedule_repository.get_kernel_count_per_agent_at_endpoint(
                            endpoint_id, USER_RESOURCE_OCCUPYING_KERNEL_STATUSES
                        )

                agselector_name = "concentrated"
            case AgentSelectionStrategy.DISPERSED:
                agselector_name = "dispersed"
            case _ as unknown:
                raise ValueError(
                    f"Unknown agent selection strategy: {unknown!r}. Possible values: {[*AgentSelectionStrategy.__members__.keys()]}"
                )

        global_agselector_opts = {}
        if self.config_provider.config.plugins.agent_selector:
            global_agselector_opts = self.config_provider.config.plugins.agent_selector.get(
                agselector_name, {}
            )
        agselector_config = {
            **global_agselector_opts,
            **sgroup_opts.agent_selector_config,
            **dynamic_config,
        }

        agent_selection_resource_priority = (
            self.config_provider.config.manager.agent_selection_resource_priority
        )

        return load_agent_selector(
            agselector_name,
            sgroup_opts,
            agselector_config,
            agent_selection_resource_priority,
            self.config_provider.legacy_etcd_config_loader,
        )

    async def _schedule_in_sgroup(
        self,
        sched_ctx: SchedulingContext,
        sgroup_name: str,
    ) -> None:
        # Part 0: Load the scheduler and the agent selector.
        (
            scheduler_name,
            sgroup_opts,
        ) = await self.schedule_repository.get_scaling_group_info(sgroup_name)
        scheduler = self._load_scheduler(LoadSchedulerArgs(scheduler_name, sgroup_opts))
        (
            existing_sessions,
            pending_sessions,
            cancelled_sessions,
        ) = await self.schedule_repository.list_managed_sessions(
            sgroup_name, scheduler.sgroup_opts.pending_timeout
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

            candidate_agents = await self.schedule_repository.get_schedulable_agents_by_sgroup(
                sgroup_name
            )
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
            agent_selector = await self._load_agent_selector(
                LoadAgentSelectorArgs(
                    sgroup_opts,
                    pending_sess.id,
                    pending_sess.session_type,
                )
            )

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

                await self.schedule_repository.update_session_predicate_failure(
                    sched_ctx, pending_sess, status_update_data
                )
                if pending_sess.is_private:
                    await self.event_producer.anycast_and_broadcast_event(
                        SessionCancelledAnycastEvent(
                            pending_sess.id,
                            pending_sess.creation_id,
                            reason=KernelLifecycleEventReason.PENDING_TIMEOUT,
                        ),
                        SessionCancelledBroadcastEvent(
                            pending_sess.id,
                            pending_sess.creation_id,
                            reason=KernelLifecycleEventReason.PENDING_TIMEOUT,
                        ),
                    )
                # Predicate failures are *NOT* permanent errors.
                # We need to retry the scheduling afterwards.
                continue
            else:
                await self.schedule_repository.update_session_status_data(
                    pending_sess, status_update_data
                )

            # Part 4: Assign agent(s) via the agent selector.

            schedulable_sess = (
                await self.schedule_repository.get_schedulable_session_with_kernels_and_agents(
                    pending_sess.id
                )
            )

            if schedulable_sess is None:
                log.error("schedulable_sess is None for session {}", pending_sess.id)
                continue

            try:
                match ClusterMode(schedulable_sess.cluster_mode):
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
            await self.event_producer.anycast_event(DoCheckPrecondEvent())

    async def _filter_agent_by_container_limit(
        self, candidate_agents: list[AgentRow]
    ) -> list[AgentRow]:
        raw_value = await self.etcd.get("config/agent/max-container-count")
        if raw_value is None:
            return candidate_agents
        max_container_count = int(raw_value)

        agent_ids = [str(ag.id) for ag in candidate_agents]
        raw_counts = await self.registry.valkey_stat.get_agent_container_counts_batch(agent_ids)

        def _check(cnt: int) -> bool:
            return max_container_count > cnt

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

                if agent_id is not None:
                    (
                        available_slots,
                        occupied_slots,
                    ) = await self.schedule_repository.get_agent_available_slots(agent_id)

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

            agent_alloc_ctx = await self.schedule_repository.reserve_agent(
                sgroup_name,
                agent_id,
                sess_ctx.requested_slots,
            )
        except InstanceNotAvailable as sched_failure:
            log.debug(log_fmt + "no-available-instances", *log_args)

            async def _update_sched_failure(exc: InstanceNotAvailable) -> None:
                await self.schedule_repository._update_session_scheduling_failure(
                    sched_ctx, sess_ctx, exc.extra_msg
                )

            await execute_with_retry(partial(_update_sched_failure, sched_failure))
            raise
        except Exception as e:
            log.exception(
                log_fmt + "unexpected-error, during agent allocation",
                *log_args,
            )
            exc_data = convert_to_status_data(e, self.config_provider.config.debug.enabled)

            async def _update_generic_failure() -> None:
                await self.schedule_repository._update_session_generic_failure(
                    sched_ctx, sess_ctx, exc_data
                )

            await execute_with_retry(_update_generic_failure)
            raise

        async def _finalize_scheduled() -> None:
            await self.schedule_repository.finalize_single_node_session(
                sess_ctx.id, sgroup_name, agent_alloc_ctx
            )

        await execute_with_retry(_finalize_scheduled)
        await self.registry.event_producer.anycast_and_broadcast_event(
            SessionScheduledAnycastEvent(sess_ctx.id, sess_ctx.creation_id),
            SessionScheduledBroadcastEvent(sess_ctx.id, sess_ctx.creation_id),
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

        kernel_agent_bindings: list[KernelAgentBinding] = []
        # This outer transaction is rolled back when any exception occurs inside,
        # including scheduling failures of a kernel.
        # It ensures that occupied_slots are recovered when there are partial
        # scheduling failures.
        for kernel in sess_ctx.kernels:
            kernel = cast(KernelRow, kernel)
            agent_alloc_ctx: AgentAllocationContext | None = None
            agent_id: Optional[AgentId] = None
            agent: Optional[AgentRow] = kernel.agent_row
            try:
                if agent is not None:
                    # Check the resource availability of the manually designated agent
                    (
                        available_slots,
                        occupied_slots,
                    ) = await self.schedule_repository.get_agent_available_slots(agent.id)

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

                agent_alloc_ctx = await self.schedule_repository.reserve_agent(
                    sgroup_name,
                    agent_id,
                    sess_ctx.requested_slots,
                )
                candidate_agents = await self.schedule_repository.get_schedulable_agents_by_sgroup(
                    sgroup_name
                )
            except InstanceNotAvailable as sched_failure:
                log.debug(log_fmt + "no-available-instances", *log_args)

                async def _update_sched_failure(exc: InstanceNotAvailable) -> None:
                    await self.schedule_repository.update_kernel_scheduling_failure(
                        sched_ctx, sess_ctx, kernel.id, exc.extra_msg
                    )

                await execute_with_retry(partial(_update_sched_failure, sched_failure))
                raise
            except Exception as e:
                log.exception(
                    log_fmt + "unexpected-error, during agent allocation",
                    *log_args,
                )
                exc_data = convert_to_status_data(e, self.config_provider.config.debug.enabled)

                async def _update_generic_failure() -> None:
                    await self.schedule_repository.update_multinode_kernel_generic_failure(
                        sched_ctx, sess_ctx, kernel.id, exc_data
                    )

                await execute_with_retry(_update_generic_failure)
                raise
            else:
                assert agent_alloc_ctx is not None
                kernel_agent_bindings.append(KernelAgentBinding(kernel, agent_alloc_ctx, set()))

        assert len(kernel_agent_bindings) == len(sess_ctx.kernels)
        # Proceed to PREPARING only when all kernels are successfully scheduled.

        async def _finalize_scheduled() -> None:
            await self.schedule_repository.finalize_multi_node_session(
                sess_ctx.id, sgroup_name, kernel_agent_bindings
            )

        await execute_with_retry(_finalize_scheduled)
        await self.registry.event_producer.anycast_and_broadcast_event(
            SessionScheduledAnycastEvent(sess_ctx.id, sess_ctx.creation_id),
            SessionScheduledBroadcastEvent(sess_ctx.id, sess_ctx.creation_id),
        )

    async def check_precond(
        self,
        event_name: str,
    ) -> None:
        """
        Scan the scheduled sessions and perform the agent RPC calls to check and pull required images.

        This function DOES NOT transit session status.
        This function calls check-and-pull API and the API produces image pull events.
        Let event handlers transit session and kernel status from
        `ImagePullStartedEvent` and `ImagePullFinishedEvent` events.
        """
        await self._mark_scheduler_start(ScheduleType.CHECK_PRECONDITION, event_name)
        lock_lifetime = self.config_provider.config.manager.session_check_precondition_lock_lifetime
        try:
            async with self.lock_factory(LockID.LOCKID_CHECK_PRECOND, lock_lifetime):
                bindings: list[KernelAgentBinding] = []

                scheduled_sessions = await self.schedule_repository.transit_scheduled_to_preparing()
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
                    await self.registry.event_producer.anycast_event(
                        SessionCheckingPrecondAnycastEvent(
                            scheduled_session.id,
                            scheduled_session.creation_id,
                        ),
                    )
                # check_and_pull_images() spawns tasks through PersistentTaskGroup
                await self.registry.check_and_pull_images(bindings)

            await self._update_scheduler_mark(
                ScheduleType.CHECK_PRECONDITION,
                {
                    "finish_time": datetime.now(tzutc()).isoformat(),
                },
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
        event_name: str,
    ) -> None:
        """
        Scan the sessions ready to create and perform the agent RPC calls to create kernels.

        Session status transition: PREPARED -> CREATING
        """
        await self._mark_scheduler_start(ScheduleType.START, event_name)
        lock_lifetime = self.config_provider.config.manager.session_start_lock_lifetime
        try:
            async with self.lock_factory(LockID.LOCKID_START, lock_lifetime):
                known_slot_types = (
                    await self.config_provider.legacy_etcd_config_loader.get_resource_slots()
                )
                sched_ctx = SchedulingContext(
                    self.registry,
                    known_slot_types,
                )

                scheduled_sessions = (
                    await self.schedule_repository.mark_sessions_and_kernels_creating()
                )

                log.debug("starting(): starting {} session(s)", len(scheduled_sessions))
                async with (
                    async_timeout.timeout(delay=START_SESSION_TIMEOUT_SEC),
                    aiotools.PersistentTaskGroup() as tg,
                ):
                    for scheduled_session in scheduled_sessions:
                        await self.registry.event_producer.anycast_and_broadcast_event(
                            SessionPreparingAnycastEvent(
                                scheduled_session.id,
                                scheduled_session.creation_id,
                            ),
                            SessionPreparingBroadcastEvent(
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

            await self._update_scheduler_mark(
                ScheduleType.START,
                {
                    "finish_time": datetime.now(tzutc()).isoformat(),
                },
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

    async def scale_services(
        self,
        event_name: str,
    ) -> None:
        log.debug("scale_services(): triggered")
        # Altering inference sessions should only be done by invoking this method
        await self._mark_scheduler_start(ScheduleType.SCALE_SERVICES, event_name)
        await execute_with_retry(lambda: self.schedule_repository.autoscale_endpoints())
        routes_to_destroy = []
        endpoints_to_expand: dict[EndpointRow, Any] = {}
        endpoints_to_mark_terminated: set[EndpointRow] = set()
        rowcount = await self.schedule_repository.clean_zombie_routes()
        if rowcount > 0:
            log.info("Cleared {} zombie routes", rowcount)

        endpoints = await self.schedule_repository.get_endpoints_for_scaling()
        for endpoint in endpoints:
            active_routings = [
                r for r in endpoint.routings if r.status in RouteStatus.active_route_statuses()
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

                # we do not expect sessions to be spawned when the endpoint is about to be destroyed
                # so also delete routes in provisioning status

                routes_to_destroy += list(
                    sorted(
                        [
                            route
                            for route in active_routings
                            if route.status in endpoint.terminatable_route_statuses
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

        ids_of_session_to_destroy = [r.session for r in routes_to_destroy]
        target_sessions_to_destroy = (
            await self.schedule_repository.get_sessions_to_destroy_for_scaling(
                ids_of_session_to_destroy
            )
        )

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
        await self._update_scheduler_mark(
            ScheduleType.SCALE_SERVICES,
            {
                "down": dump_json_str([str(s.id) for s in target_sessions_to_destroy]),
            },
        )
        created_routes = []
        endpoint_create_data = []
        for endpoint, expand_count in endpoints_to_expand.items():
            log.debug("Creating {} session(s) for {}", expand_count, endpoint.name)
            endpoint_create_data.append((endpoint, expand_count))
        created_routes = await self.schedule_repository.create_routing_rows(endpoint_create_data)
        for route_id in created_routes:
            await self.event_producer.anycast_event(RouteCreatedAnycastEvent(route_id))
        await self._update_scheduler_mark(
            ScheduleType.SCALE_SERVICES,
            {
                "up": dump_json_str([str(e.id) for e in endpoints_to_expand.keys()]),
                "finish_time": datetime.now(tzutc()).isoformat(),
            },
        )

        await execute_with_retry(
            lambda: self.schedule_repository.destroy_terminated_endpoints_and_routes(
                endpoints_to_mark_terminated, already_destroyed_sessions
            )
        )

        await self.schedule_repository.delete_appproxy_endpoints_readonly(
            endpoints_to_mark_terminated, self.registry
        )

    async def update_session_status(
        self,
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
        except (asyncio.CancelledError, Exception) as e:
            status_data = convert_to_status_data(e, self.config_provider.config.debug.enabled)
            log.warning(log_fmt + "failed-starting", *log_args, exc_info=True)
            # TODO: instead of instantly cancelling upon exception, we could mark it as
            #       SCHEDULED and retry within some limit using status_data.

            async def _mark_session_cancelled() -> None:
                await self.schedule_repository._mark_session_cancelled(
                    sched_ctx, session, status_data
                )

            log.debug(log_fmt + "cleanup-start-failure: begin", *log_args)
            try:
                await execute_with_retry(_mark_session_cancelled)
                await self.registry.event_producer.anycast_and_broadcast_event(
                    SessionCancelledAnycastEvent(
                        session.id,
                        session.creation_id,
                        KernelLifecycleEventReason.FAILED_TO_START,
                    ),
                    SessionCancelledBroadcastEvent(
                        session.id,
                        session.creation_id,
                        KernelLifecycleEventReason.FAILED_TO_START,
                    ),
                )
                cid_map = await self.schedule_repository.get_container_info_for_destroyed_kernels(
                    session.id
                )
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

        await self.schedule_repository.apply_cancellation(session_ids)
        for item in cancelled_sessions:
            await self.event_producer.anycast_and_broadcast_event(
                SessionCancelledAnycastEvent(
                    item.id,
                    item.creation_id,
                    reason=KernelLifecycleEventReason.PENDING_TIMEOUT,
                ),
                SessionCancelledBroadcastEvent(
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
        async with self.registry.db.begin_session() as db_sess:
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
        async with self.registry.db.begin_readonly_session() as db_sess:
            return await self.registry.hook_plugin_ctx.dispatch(
                "PREDICATE",
                (
                    db_sess,
                    sched_ctx,
                    pending_sess,
                ),
            )

    def _schedule_key(self, schedule_type: ScheduleType) -> str:
        """
        Returns the Redis key for the given schedule type.
        """
        manager_id = self.config_provider.config.manager.id
        return f"manager.{manager_id}.{str(schedule_type)}"

    async def _mark_scheduler_start(
        self,
        schedule_type: ScheduleType,
        event_name: str,
    ) -> None:
        schedule_key = self._schedule_key(schedule_type)
        await self._valkey_live.replace_schedule_data(
            schedule_key,
            {
                "trigger_event": event_name,
                "execution_time": datetime.now(tzutc()).isoformat(),
            },
        )

    async def _update_scheduler_mark(
        self,
        schedule_type: ScheduleType,
        to_update: dict[str, Any],
    ) -> None:
        """
        Updates the scheduler mark for the given schedule type with the provided data.
        """
        schedule_key = self._schedule_key(schedule_type)
        await self._valkey_live.add_scheduler_metadata(
            schedule_key,
            to_update,
        )


class ScheduleType(StrEnum):
    SCHEDULE = "schedule"
    START = "start"
    CHECK_PRECONDITION = "check_precondition"
    SCALE_SERVICES = "scale_services"
