from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
import enum
import logging
import math
from abc import ABCMeta, abstractmethod
from datetime import datetime, timedelta
from typing import (
    Any,
    ClassVar,
    DefaultDict,
    List,
    Mapping,
    MutableMapping,
    Sequence,
    Set,
    Type,
    TYPE_CHECKING,
    Union,
)

import sqlalchemy as sa
import trafaret as t
from dateutil.tz import tzutc
from sqlalchemy.engine import Row

import ai.backend.common.validators as tx
from ai.backend.common import msgpack, redis as redis_helper
from ai.backend.common.distributed import GlobalTimer
from ai.backend.common.events import (
    AbstractEvent,
    DoIdleCheckEvent,
    DoTerminateSessionEvent,
    EventDispatcher,
    EventHandler,
    EventProducer,
    ExecutionCancelledEvent,
    ExecutionFinishedEvent,
    ExecutionStartedEvent,
    ExecutionTimeoutEvent,
    SessionStartedEvent,
)
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import AccessKey, RedisConnectionInfo, SessionTypes
from ai.backend.common.utils import nmget

from .defs import DEFAULT_ROLE, REDIS_LIVE_DB, REDIS_STAT_DB, LockID
from .models import kernels, keypair_resource_policies, keypairs
from .models.kernel import LIVE_STATUS
from .types import DistributedLockFactory

if TYPE_CHECKING:
    from .config import SharedConfig
    from ai.backend.common.types import AgentId, KernelId, SessionId
    from sqlalchemy.ext.asyncio import (
        AsyncConnection as SAConnection,
    )
    from .models.utils import ExtendedAsyncSAEngine as SAEngine

log = BraceStyleAdapter(logging.getLogger("ai.backend.manager.idle"))


class AppStreamingStatus(enum.Enum):
    NO_ACTIVE_CONNECTIONS = 0
    HAS_ACTIVE_CONNECTIONS = 1


class ThresholdOperator(enum.Enum):
    AND = 'and'
    OR = 'or'


class IdleCheckerHost:

    check_interval: ClassVar[float] = 15.0

    def __init__(
        self,
        db: SAEngine,
        shared_config: SharedConfig,
        event_dispatcher: EventDispatcher,
        event_producer: EventProducer,
        lock_factory: DistributedLockFactory,
    ) -> None:
        self._checkers: list[BaseIdleChecker] = []
        self._frozen = False
        self._db = db
        self._shared_config = shared_config
        self._event_dispatcher = event_dispatcher
        self._event_producer = event_producer
        self._lock_factory = lock_factory
        self._redis_live = redis_helper.get_redis_object(
            self._shared_config.data['redis'],
            db=REDIS_LIVE_DB,
        )
        self._redis_stat = redis_helper.get_redis_object(
            self._shared_config.data['redis'],
            db=REDIS_STAT_DB,
        )

    def add_checker(self, checker: BaseIdleChecker):
        if self._frozen:
            raise RuntimeError("Cannot add a new idle checker after the idle checker host is frozen.")
        self._checkers.append(checker)

    async def start(self) -> None:
        self._frozen = True
        for checker in self._checkers:
            raw_config = await self._shared_config.etcd.get_prefix_dict(
                f"config/idle/checkers/{checker.name}",
            )
            await checker.populate_config(raw_config or {})
        self.timer = GlobalTimer(
            self._lock_factory(LockID.LOCKID_IDLE_CHECK_TIMER, self.check_interval),
            self._event_producer,
            lambda: DoIdleCheckEvent(),
            self.check_interval,
        )
        self._evh_idle_check = self._event_dispatcher.consume(
            DoIdleCheckEvent,
            None,
            self._do_idle_check,
        )
        await self.timer.join()

    async def shutdown(self) -> None:
        for checker in self._checkers:
            await checker.aclose()
        await self.timer.leave()
        self._event_dispatcher.unconsume(self._evh_idle_check)
        await self._redis_stat.close()
        await self._redis_live.close()

    async def update_app_streaming_status(
        self,
        session_id: SessionId,
        status: AppStreamingStatus,
    ) -> None:
        for checker in self._checkers:
            await checker.update_app_streaming_status(session_id, status)

    async def _do_idle_check(
        self,
        context: None,
        source: AgentId,
        event: DoIdleCheckEvent,
    ) -> None:
        log.debug("do_idle_check(): triggered")
        policy_cache: dict[AccessKey, Row] = {}
        async with self._db.begin_readonly() as conn:
            query = (
                sa.select([kernels])
                .select_from(kernels)
                .where(
                    (kernels.c.status.in_(LIVE_STATUS)) &
                    (kernels.c.cluster_role == DEFAULT_ROLE),
                )
            )
            result = await conn.execute(query)
            rows = result.fetchall()
            for session in rows:
                policy = policy_cache.get(session["access_key"], None)
                if policy is None:
                    query = (
                        sa.select([keypair_resource_policies])
                        .select_from(
                            sa.join(
                                keypairs,
                                keypair_resource_policies,
                                keypair_resource_policies.c.name == keypairs.c.resource_policy,
                            ),
                        )
                        .where(keypairs.c.access_key == session["access_key"])
                    )
                    result = await conn.execute(query)
                    policy = result.first()
                    assert policy is not None
                    policy_cache[session["access_key"]] = policy
                for checker in self._checkers:
                    if not (await checker.check_session(session, conn, policy)):
                        log.info(
                            "The {} idle checker triggered termination of s:{}",
                            checker.name, session['id'],
                        )
                        await self._event_producer.produce_event(
                            DoTerminateSessionEvent(session["id"], f"idle-{checker.name}"),
                        )
                        # If any one of checkers decided to terminate the session,
                        # we can skip over remaining checkers.
                        break


class BaseIdleChecker(metaclass=ABCMeta):

    name: ClassVar[str] = "base"

    def __init__(
        self,
        event_dispatcher: EventDispatcher,
        redis_live: RedisConnectionInfo,
        redis_stat: RedisConnectionInfo,
    ) -> None:
        self._event_dispatcher = event_dispatcher
        self._redis_live = redis_live
        self._redis_stat = redis_stat

    async def aclose(self) -> None:
        pass

    @abstractmethod
    async def populate_config(self, config: Mapping[str, Any]) -> None:
        raise NotImplementedError

    async def update_app_streaming_status(
        self,
        session_id: SessionId,
        status: AppStreamingStatus,
    ) -> None:
        pass

    @abstractmethod
    async def check_session(self, session: Row, dbconn: SAConnection, policy: Row) -> bool:
        """
        Return True if the session should be kept alive or
        return False if the session should be terminated.
        """
        return True


class TimeoutIdleChecker(BaseIdleChecker):
    """
    Checks the idleness of a session by the elapsed time since last used.
    The usage means processing of any computation requests, such as
    query/batch-mode code execution and having active service-port connections.
    """

    name: ClassVar[str] = "timeout"

    _config_iv = t.Dict(
        {
            t.Key("threshold", default="10m"): tx.TimeDuration(),
        },
    ).allow_extra("*")

    idle_timeout: timedelta
    _evhandlers: List[EventHandler[None, AbstractEvent]]

    def __init__(
        self,
        event_dispatcher: EventDispatcher,
        redis_live: RedisConnectionInfo,
        redis_stat: RedisConnectionInfo,
    ) -> None:
        super().__init__(event_dispatcher, redis_live, redis_stat)
        d = self._event_dispatcher
        self._evhandlers = [
            d.consume(SessionStartedEvent, None, self._session_started_cb),  # type: ignore
            d.consume(ExecutionStartedEvent, None, self._execution_started_cb),  # type: ignore
            d.consume(ExecutionFinishedEvent, None, self._execution_exited_cb),  # type: ignore
            d.consume(ExecutionTimeoutEvent, None, self._execution_exited_cb),  # type: ignore
            d.consume(ExecutionCancelledEvent, None, self._execution_exited_cb),  # type: ignore
        ]

    async def aclose(self) -> None:
        for _evh in self._evhandlers:
            self._event_dispatcher.unconsume(_evh)

    async def populate_config(self, raw_config: Mapping[str, Any]) -> None:
        config = self._config_iv.check(raw_config)
        self.idle_timeout = config["threshold"]
        log.info(
            "TimeoutIdleChecker: default idle_timeout = {0:,} seconds",
            self.idle_timeout.total_seconds(),
        )

    async def update_app_streaming_status(
        self,
        session_id: SessionId,
        status: AppStreamingStatus,
    ) -> None:
        if status == AppStreamingStatus.HAS_ACTIVE_CONNECTIONS:
            await self._disable_timeout(session_id)
        elif status == AppStreamingStatus.NO_ACTIVE_CONNECTIONS:
            await self._update_timeout(session_id)

    async def _disable_timeout(self, session_id: SessionId) -> None:
        log.debug(f"TimeoutIdleChecker._disable_timeout({session_id})")
        await redis_helper.execute(
            self._redis_live,
            lambda r: r.set(
                f"session.{session_id}.last_access", "0", xx=True,
            ),
        )

    async def _update_timeout(self, session_id: SessionId) -> None:
        log.debug(f"TimeoutIdleChecker._update_timeout({session_id})")
        t = await redis_helper.execute(self._redis_live, lambda r: r.time())
        t = t[0] + (t[1] / (10**6))
        await redis_helper.execute(
            self._redis_live,
            lambda r: r.set(
                f"session.{session_id}.last_access",
                f"{t:.06f}",
                ex=max(86400, int(self.idle_timeout.total_seconds() * 2)),
            ),
        )

    async def _session_started_cb(
        self,
        context: None,
        source: AgentId,
        event: SessionStartedEvent,
    ) -> None:
        await self._update_timeout(event.session_id)

    async def _execution_started_cb(
        self,
        context: None,
        source: AgentId,
        event: ExecutionStartedEvent,
    ) -> None:
        await self._disable_timeout(event.session_id)

    async def _execution_exited_cb(
        self,
        context: None,
        source: AgentId,
        event: ExecutionFinishedEvent | ExecutionTimeoutEvent | ExecutionCancelledEvent,
    ) -> None:
        await self._update_timeout(event.session_id)

    async def check_session(self, session: Row, dbconn: SAConnection, policy: Row) -> bool:
        session_id = session["id"]
        if session["session_type"] == SessionTypes.BATCH:
            return True
        active_streams = await redis_helper.execute(
            self._redis_live,
            lambda r: r.zcount(
                f"session.{session_id}.active_app_connections",
                float('-inf'), float('+inf'),
            ),
        )
        if active_streams is not None and active_streams > 0:
            return True
        t = await redis_helper.execute(self._redis_live, lambda r: r.time())
        t = t[0] + (t[1] / (10**6))
        raw_last_access = \
            await redis_helper.execute(
                self._redis_live,
                lambda r: r.get(f"session.{session_id}.last_access"),
            )
        if raw_last_access is None or raw_last_access == "0":
            return True
        last_access = float(raw_last_access)
        # serves as the default fallback if keypair resource policy's idle_timeout is "undefined"
        idle_timeout = self.idle_timeout.total_seconds()
        # setting idle_timeout:
        # - zero/inf means "infinite"
        # - negative means "undefined"
        if policy["idle_timeout"] >= 0:
            idle_timeout = float(policy["idle_timeout"])
        if (
            (idle_timeout <= 0)
            or (math.isinf(idle_timeout) and idle_timeout > 0)
            or (t - last_access <= idle_timeout)
        ):
            return True
        return False


class SessionLifetimeChecker(BaseIdleChecker):

    name: ClassVar[str] = "session_lifetime"

    async def populate_config(self, config: Mapping[str, Any]) -> None:
        pass

    async def check_session(self, session: Row, dbconn: SAConnection, policy: Row) -> bool:
        now = await dbconn.scalar(sa.select(sa.func.now()))
        if policy["max_session_lifetime"] > 0:
            # TODO: once per-status time tracking is implemented, let's change created_at
            #       to the timestamp when the session entered PREPARING status.
            if now - session["created_at"] >= timedelta(seconds=policy["max_session_lifetime"]):
                return False
        return True


class UtilizationIdleChecker(BaseIdleChecker):
    """
    Checks the idleness of a session by the average utilization of compute devices.
    """

    name: ClassVar[str] = "utilization"

    _config_iv = t.Dict(
        {
            t.Key("time-window", default="10m"): tx.TimeDuration(),
            t.Key("initial-grace-period", default="5m"): tx.TimeDuration(),
            t.Key("thresholds-check-operator", default=ThresholdOperator.AND):
            tx.Enum(ThresholdOperator),
            t.Key("resource-thresholds"): t.Dict(
                {
                    t.Key("cpu_util", default=None): t.Null | t.Dict({t.Key("average"): t.Float}),
                    t.Key("mem", default=None): t.Null | t.Dict({t.Key("average"): t.Float}),
                    t.Key("cuda_util", default=None): t.Null | t.Dict({t.Key("average"): t.Float}),
                    t.Key("cuda_mem", default=None): t.Null | t.Dict({t.Key("average"): t.Float}),
                },
            ),
        },
    ).allow_extra("*")

    resource_thresholds: MutableMapping[str, Union[int, float, Decimal]]
    thresholds_check_operator: str
    time_window: timedelta
    initial_grace_period: timedelta
    _evhandlers: List[EventHandler[None, AbstractEvent]]
    slot_resource_map: Mapping[str, Set[str]] = {
        'cpu': {'cpu_util'},
        'mem': {'mem'},
        'cuda': {'cuda_util', 'cuda_mem'},
    }

    async def populate_config(self, raw_config: Mapping[str, Any]) -> None:
        config = self._config_iv.check(raw_config)
        self.resource_thresholds = {
            k: nmget(v, 'average') for k, v in config.get('resource-thresholds').items()
        }
        self.thresholds_check_operator = config.get("thresholds-check-operator")
        self.time_window = config.get("time-window")
        self.initial_grace_period = config.get("initial-grace-period")

        thresholds_log = " ".join([f"{k}({threshold})," for k,
                                   threshold in self.resource_thresholds.items()])
        log.info(
            f"UtilizationIdleChecker(%): {thresholds_log} "
            f"thresholds-check-operator(\"{self.thresholds_check_operator}\"), "
            f"time-window({self.time_window.total_seconds()}s)",
        )

    async def check_session(self, session: Row, dbconn: SAConnection, policy: Row) -> bool:
        session_id = session["id"]
        interval = IdleCheckerHost.check_interval
        window_size = int(self.time_window.total_seconds() / interval)
        occupied_slots = session["occupied_slots"]
        unavailable_resources: Set[str] = set()

        util_series_key = f"session.{session_id}.util_series"
        util_last_collected_key = f"session.{session_id}.util_last_collected"

        # Wait until the time "interval" is passed after the last udpated time.
        t = await redis_helper.execute(self._redis_live, lambda r: r.time())
        t = t[0] + (t[1] / (10**6))
        raw_util_last_collected = await redis_helper.execute(
            self._redis_live,
            lambda r: r.get(util_last_collected_key),
        )
        util_last_collected = float(raw_util_last_collected) if raw_util_last_collected else 0
        if t - util_last_collected < interval:
            return True

        # Respect initial grace period (no termination of the session)
        now = datetime.now(tzutc())
        if now - session["created_at"] <= self.initial_grace_period:
            return True

        # Merge same type of (exclusive) resources as a unique resource with the values added.
        # Example: {cuda.device: 0, cuda.shares: 0.5} -> {cuda: 0.5}.
        unique_res_map: DefaultDict[str, Any] = defaultdict(Decimal)
        for k, v in occupied_slots.items():
            unique_key = k.split('.')[0]
            unique_res_map[unique_key] += v

        # Do not take into account unallocated resources. For example, do not garbage collect
        # a session without GPU even if cuda_util is configured in resource-thresholds.
        for slot in unique_res_map:
            if unique_res_map[slot] == 0:
                unavailable_resources.update(self.slot_resource_map[slot])

        # Respect idle_timeout, from keypair resource policy, over time_window.
        if policy["idle_timeout"] >= 0:
            window_size = int(float(policy["idle_timeout"]) / interval)
        if (window_size <= 0) or (math.isinf(window_size) and window_size > 0):
            return True

        # Get current utilization data from all containers of the session.
        if session["cluster_size"] > 1:
            query = (
                sa.select([kernels.c.id])
                .select_from(kernels)
                .where(
                    (kernels.c.session_id == session_id) &
                    (kernels.c.status.in_(LIVE_STATUS)),
                )
            )
            result = await dbconn.execute(query)
            rows = result.fetchall()
            kernel_ids = [k["id"] for k in rows]
        else:
            kernel_ids = [session_id]
        current_utilizations = await self.get_current_utilization(kernel_ids, occupied_slots)
        if current_utilizations is None:
            return True

        # Update utilization time-series data.
        not_enough_data = False
        raw_util_series = await redis_helper.execute(self._redis_live, lambda r: r.get(util_series_key))

        try:
            util_series = msgpack.unpackb(raw_util_series, use_list=True)
        except TypeError:
            util_series = {k: [] for k in self.resource_thresholds.keys()}

        for k in util_series:
            util_series[k].append(current_utilizations[k])
            if len(util_series[k]) > window_size:
                util_series[k].pop(0)
            else:
                not_enough_data = True
        await redis_helper.execute(
            self._redis_live,
            lambda r: r.set(
                util_series_key,
                msgpack.packb(util_series),
                ex=max(86400, int(self.time_window.total_seconds() * 2)),
            ),
        )
        await redis_helper.execute(
            self._redis_live,
            lambda r: r.set(
                util_last_collected_key,
                f"{t:.06f}",
                ex=max(86400, int(self.time_window.total_seconds() * 2)),
            ),
        )

        if not_enough_data:
            return True

        # Check over-utilized (not to be collected) resources.
        avg_utils = {k: sum(v) / len(v) for k, v in util_series.items()}
        sufficiently_utilized = {
            k: (float(avg_utils[k]) >= float(threshold))
            for k, threshold in self.resource_thresholds.items()
            if (threshold is not None) and (k not in unavailable_resources)
        }

        if len(sufficiently_utilized) < 1:
            check_result = True
        elif self.thresholds_check_operator == ThresholdOperator.OR:
            check_result = all(sufficiently_utilized.values())
        else:  # "and" operation is the default
            check_result = any(sufficiently_utilized.values())
        if not check_result:
            log.info("utilization timeout: {} ({}, {})",
                     session_id, avg_utils, self.thresholds_check_operator)
        return check_result

    async def get_current_utilization(
        self,
        kernel_ids: Sequence[KernelId],
        occupied_slots: Mapping[str, Any],
    ) -> Mapping[str, float] | None:
        """
        Return the current utilization key-value pairs of multiple kernels, possibly the
        components of a cluster session. If there are multiple kernel_ids, this method
        will return the averaged values over the kernels for each utilization.
        """
        try:
            utilizations = {k: 0.0 for k in self.resource_thresholds.keys()}
            live_stat = {}
            for kernel_id in kernel_ids:
                raw_live_stat = await redis_helper.execute(
                    self._redis_stat,
                    lambda r: r.get(str(kernel_id)),
                )
                live_stat = msgpack.unpackb(raw_live_stat)
                kernel_utils = {
                    k: float(nmget(live_stat, f"{k}.pct", 0.0))
                    for k in self.resource_thresholds.keys()
                }

                utilizations = {
                    k: utilizations[k] + kernel_utils[k]
                    for k in self.resource_thresholds.keys()
                }
            utilizations = {
                k: utilizations[k] / len(kernel_ids)
                for k in self.resource_thresholds.keys()
            }

            # NOTE: Manual calculation of mem utilization.
            # mem.capacity does not report total amount of memory allocated to
            # the container, and mem.pct always report >90% even when nothing is
            # executing. So, we just replace it with the value of occupied slot.
            mem_slots = float(occupied_slots.get('mem', 0))
            mem_current = float(nmget(live_stat, "mem.current", 0.0))
            utilizations['mem'] = mem_current / mem_slots * 100 if mem_slots > 0 else 0
            return utilizations
        except Exception as e:
            log.warning("Unable to collect utilization for idleness check", exc_info=e)
            return None


checker_registry: Mapping[str, Type[BaseIdleChecker]] = {
    TimeoutIdleChecker.name: TimeoutIdleChecker,
    UtilizationIdleChecker.name: UtilizationIdleChecker,
}


async def init_idle_checkers(
    db: SAEngine,
    shared_config: SharedConfig,
    event_dispatcher: EventDispatcher,
    event_producer: EventProducer,
    lock_factory: DistributedLockFactory,
) -> IdleCheckerHost:
    """
    Create an instance of session idleness checker
    from the given configuration and using the given event dispatcher.
    """
    checker_host = IdleCheckerHost(db, shared_config, event_dispatcher, event_producer, lock_factory)
    checker_init_args = (event_dispatcher, checker_host._redis_live, checker_host._redis_stat)
    log.info("Initializing idle checker: session_lifetime")
    checker_host.add_checker(SessionLifetimeChecker(*checker_init_args))  # enabled by default
    enabled_checkers = await shared_config.etcd.get("config/idle/enabled")
    if enabled_checkers:
        for checker_name in enabled_checkers.split(","):
            checker_cls = checker_registry.get(checker_name, None)
            if checker_cls is None:
                log.warning("ignoring an unknown idle checker name: {}", checker_name)
                continue
            log.info("Initializing idle checker: {}", checker_name)
            checker_instance = checker_cls(*checker_init_args)
            checker_host.add_checker(checker_instance)
    return checker_host
