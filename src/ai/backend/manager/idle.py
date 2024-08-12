from __future__ import annotations

import asyncio
import enum
import logging
import math
from abc import ABCMeta, abstractmethod
from collections import UserDict, defaultdict
from datetime import datetime, timedelta
from decimal import Decimal
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    DefaultDict,
    Final,
    List,
    Mapping,
    MutableMapping,
    NamedTuple,
    Optional,
    Sequence,
    Set,
    Type,
    Union,
    cast,
)

import aiotools
import sqlalchemy as sa
import trafaret as t
from aiotools import TaskGroupError
from sqlalchemy.engine import Row

import ai.backend.common.validators as tx
from ai.backend.common import msgpack, redis_helper
from ai.backend.common.defs import REDIS_LIVE_DB, REDIS_STAT_DB
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
    KernelLifecycleEventReason,
    SessionStartedEvent,
)
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import (
    AccessKey,
    BinarySize,
    RedisConnectionInfo,
    SessionTypes,
)
from ai.backend.common.utils import nmget

from .defs import DEFAULT_ROLE, LockID
from .models.kernel import LIVE_STATUS, kernels
from .models.keypair import keypairs
from .models.resource_policy import keypair_resource_policies
from .models.user import users
from .types import DistributedLockFactory

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncConnection as SAConnection

    from ai.backend.common.types import AgentId, KernelId, SessionId

    from .config import SharedConfig
    from .models.utils import ExtendedAsyncSAEngine as SAEngine

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

DEFAULT_CHECK_INTERVAL: Final = 15.0
# idle checker's remaining time should be -1 when the remaining time is negative
IDLE_TIMEOUT_VALUE: Final = -1


class IdleCheckerError(TaskGroupError):
    """
    An exception that is a collection of multiple idle checkers.
    """


def parse_unit(resource_name: str, value: float | int) -> float | int:
    if resource_name.find("mem") == -1:
        return value
    return BinarySize(int(value))


def calculate_remaining_time(
    now: datetime,
    idle_baseline: datetime,
    timeout_period: timedelta,
    grace_period_end: Optional[datetime] = None,
) -> float:
    if grace_period_end is None:
        baseline = idle_baseline
    else:
        baseline = max(idle_baseline, grace_period_end)
    remaining = baseline - now + timeout_period
    return remaining.total_seconds()


async def get_redis_now(redis_obj: RedisConnectionInfo) -> float:
    t = await redis_helper.execute(redis_obj, lambda r: r.time())
    return t[0] + (t[1] / (10**6))


async def get_db_now(dbconn: SAConnection) -> datetime:
    return await dbconn.scalar(sa.select(sa.func.now()))


class UtilizationExtraInfo(NamedTuple):
    avg_util: float
    threshold: float


class UtilizationResourceReport(UserDict):
    __slots__ = ("data",)

    data: dict[str, UtilizationExtraInfo]

    @classmethod
    def from_avg_threshold(
        cls,
        avg_utils: Mapping[str, float],
        thresholds: Mapping[str, Union[int, float, Decimal, None]],
        exclusions: set[str],
    ) -> UtilizationResourceReport:
        data: dict[str, UtilizationExtraInfo] = {
            k: UtilizationExtraInfo(float(avg_utils[k]), float(threshold))
            for k, threshold in thresholds.items()
            if (threshold is not None) and (k not in exclusions)
        }
        return cls(data)

    def to_dict(self, apply_unit: bool = True) -> dict[str, UtilizationExtraInfo]:
        if apply_unit:
            return {
                k: UtilizationExtraInfo(parse_unit(k, v[0]), parse_unit(k, v[1]))
                for k, v in self.data.items()
            }
        return {**self.data}

    @property
    def utilization_result(self) -> dict[str, bool]:
        return {k: v.avg_util >= v.threshold for k, v in self.data.items()}


class AppStreamingStatus(enum.Enum):
    NO_ACTIVE_CONNECTIONS = 0
    HAS_ACTIVE_CONNECTIONS = 1


class ThresholdOperator(enum.Enum):
    AND = "and"
    OR = "or"


class RemainingTimeType(enum.StrEnum):
    GRACE_PERIOD = "grace_period"
    EXPIRE_AFTER = "expire_after"


class IdleCheckerHost:
    check_interval: ClassVar[float] = DEFAULT_CHECK_INTERVAL

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
            self._shared_config.data["redis"],
            name="idle.live",
            db=REDIS_LIVE_DB,
        )
        self._redis_stat = redis_helper.get_redis_object(
            self._shared_config.data["redis"],
            name="idle.stat",
            db=REDIS_STAT_DB,
        )
        self._grace_period_checker: NewUserGracePeriodChecker = NewUserGracePeriodChecker(
            event_dispatcher, self._redis_live, self._redis_stat
        )

    def add_checker(self, checker: BaseIdleChecker):
        if self._frozen:
            raise RuntimeError(
                "Cannot add a new idle checker after the idle checker host is frozen."
            )
        self._checkers.append(checker)

    async def start(self) -> None:
        self._frozen = True
        raw_config = await self._shared_config.etcd.get_prefix_dict(
            "config/idle/checkers",
        )
        raw_config = cast(Mapping[str, Mapping[str, Any]], raw_config)
        await self._grace_period_checker.populate_config(
            raw_config.get(self._grace_period_checker.name) or {}
        )
        for checker in self._checkers:
            await checker.populate_config(raw_config.get(checker.name) or {})
        self.timer = GlobalTimer(
            self._lock_factory(LockID.LOCKID_IDLE_CHECK_TIMER, self.check_interval),
            self._event_producer,
            lambda: DoIdleCheckEvent(),
            self.check_interval,
            task_name="idle_checker",
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
            j = sa.join(kernels, users, kernels.c.user_uuid == users.c.uuid)
            query = (
                sa.select([
                    kernels.c.id,
                    kernels.c.access_key,
                    kernels.c.session_id,
                    kernels.c.session_type,
                    kernels.c.created_at,
                    kernels.c.occupied_slots,
                    kernels.c.cluster_size,
                    users.c.created_at.label("user_created_at"),
                ])
                .select_from(j)
                .where(
                    (kernels.c.status.in_(LIVE_STATUS))
                    & (kernels.c.cluster_role == DEFAULT_ROLE)
                    & (kernels.c.session_type != SessionTypes.INFERENCE),
                )
            )
            result = await conn.execute(query)
            rows = result.fetchall()
            for kernel in rows:
                grace_period_end = await self._grace_period_checker.get_grace_period_end(kernel)
                policy = policy_cache.get(kernel["access_key"], None)
                if policy is None:
                    query = (
                        sa.select([
                            keypair_resource_policies.c.max_session_lifetime,
                            keypair_resource_policies.c.idle_timeout,
                        ])
                        .select_from(
                            sa.join(
                                keypairs,
                                keypair_resource_policies,
                                keypair_resource_policies.c.name == keypairs.c.resource_policy,
                            ),
                        )
                        .where(keypairs.c.access_key == kernel["access_key"])
                    )
                    result = await conn.execute(query)
                    policy = result.first()
                    assert policy is not None
                    policy_cache[kernel["access_key"]] = policy

                check_task = [
                    checker.check_idleness(
                        kernel, conn, policy, self._redis_live, grace_period_end=grace_period_end
                    )
                    for checker in self._checkers
                ]
                check_results = await asyncio.gather(*check_task, return_exceptions=True)
                terminated = False
                errors = []
                for checker, result in zip(self._checkers, check_results):
                    if isinstance(result, aiotools.TaskGroupError):
                        errors.extend(result.__errors__)
                        continue
                    elif isinstance(result, Exception):
                        # mark to be destroyed afterwards
                        errors.append(result)
                        continue
                    if not result:
                        log.info(
                            "The {} idle checker triggered termination of s:{}",
                            checker.name,
                            kernel["session_id"],
                        )
                        if not terminated:
                            terminated = True
                            await self._event_producer.produce_event(
                                DoTerminateSessionEvent(
                                    kernel["session_id"],
                                    checker.terminate_reason,
                                ),
                            )
                if errors:
                    raise IdleCheckerError("idle checker(s) raise errors", errors)

    async def get_idle_check_report(
        self,
        session_id: SessionId,
    ) -> dict[str, Any]:
        return {
            checker.name: {
                "remaining": await checker.get_checker_result(self._redis_live, session_id),
                "remaining_time_type": checker.remaining_time_type.value,
                "extra": await checker.get_extra_info(session_id),
            }
            for checker in self._checkers
        }


class AbstractIdleCheckReporter(metaclass=ABCMeta):
    remaining_time_type: RemainingTimeType
    name: ClassVar[str] = "base"
    report_key: ClassVar[str] = "base"
    extra_info_key: ClassVar[str] = "base_extra"

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

    @classmethod
    def get_report_key(cls, session_id: SessionId) -> str:
        return f"session.{session_id}.{cls.name}.report"

    @abstractmethod
    async def get_extra_info(self, session_id: SessionId) -> Optional[dict[str, Any]]:
        return None

    @abstractmethod
    async def get_checker_result(
        self,
        redis_obj: RedisConnectionInfo,
        session_id: SessionId,
    ) -> Optional[float]:
        """
        Get check result of the given session.
        """
        pass

    async def set_remaining_time_report(
        self, redis_obj: RedisConnectionInfo, session_id: SessionId, remaining: float
    ) -> None:
        await redis_helper.execute(
            redis_obj,
            lambda r: r.set(
                self.get_report_key(session_id),
                msgpack.packb(remaining),
                ex=int(DEFAULT_CHECK_INTERVAL) * 10,
            ),
        )


class AbstractIdleChecker(metaclass=ABCMeta):
    terminate_reason: KernelLifecycleEventReason

    @abstractmethod
    async def check_idleness(
        self,
        kernel: Row,
        dbconn: SAConnection,
        policy: Row,
        redis_obj: RedisConnectionInfo,
        *,
        grace_period_end: Optional[datetime] = None,
    ) -> bool:
        """
        Check the kernel is whether idle or not.
        And report the result to Redis.
        """
        return True


class NewUserGracePeriodChecker(AbstractIdleCheckReporter):
    remaining_time_type: RemainingTimeType = RemainingTimeType.GRACE_PERIOD
    name: ClassVar[str] = "user_grace_period"
    report_key: ClassVar[str] = "user_grace_period"
    user_initial_grace_period: Optional[timedelta] = None

    _config_iv = t.Dict(
        {
            t.Key("user_initial_grace_period", default=None): t.Null | tx.TimeDuration(),
        },
    ).allow_extra("*")

    async def populate_config(self, raw_config: Mapping[str, Any]) -> None:
        config = self._config_iv.check(raw_config)
        self.user_initial_grace_period = config["user_initial_grace_period"]
        _grace_period = (
            self.user_initial_grace_period.total_seconds()
            if self.user_initial_grace_period is not None
            else None
        )

        log.info(
            f"NewUserGracePeriodChecker: default period = {_grace_period} seconds",
        )

    async def get_extra_info(self, session_id: SessionId) -> Optional[dict[str, Any]]:
        return None

    async def del_remaining_time_report(
        self, redis_obj: RedisConnectionInfo, session_id: SessionId
    ) -> None:
        await redis_helper.execute(
            redis_obj,
            lambda r: r.delete(
                self.get_report_key(session_id),
            ),
        )

    async def get_grace_period_end(
        self,
        kernel: Row,
    ) -> Optional[datetime]:
        """
        Calculate the user's initial grace period for idle checkers.
        During the user's initial grace period, the checker does not calculate the time remaining until expiration
        and does not yield any extra information such as average utilization.
        """
        if self.user_initial_grace_period is None:
            return None
        user_created_at: datetime = kernel["user_created_at"]
        return user_created_at + self.user_initial_grace_period

    @property
    def grace_period_const(self) -> float:
        return (
            self.user_initial_grace_period.total_seconds()
            if self.user_initial_grace_period is not None
            else 0
        )

    async def get_checker_result(
        self,
        redis_obj: RedisConnectionInfo,
        session_id: SessionId,
    ) -> Optional[float]:
        key = self.get_report_key(session_id)
        data = await redis_helper.execute(redis_obj, lambda r: r.get(key))
        return msgpack.unpackb(data) if data is not None else None


class BaseIdleChecker(AbstractIdleChecker, AbstractIdleCheckReporter):
    pass


class NetworkTimeoutIdleChecker(BaseIdleChecker):
    """
    Checks the idleness of a session by the elapsed time since last used.
    The usage means processing of any computation requests, such as
    query/batch-mode code execution and having active service-port connections.
    """

    terminate_reason: KernelLifecycleEventReason = KernelLifecycleEventReason.IDLE_TIMEOUT
    remaining_time_type: RemainingTimeType = RemainingTimeType.EXPIRE_AFTER
    name: ClassVar[str] = "network_timeout"
    report_key: ClassVar[str] = "network_timeout"
    extra_info_key: ClassVar[str] = "network_timeout_timeout_extra"

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
        (d.subscribe(SessionStartedEvent, None, self._session_started_cb),)  # type: ignore
        self._evhandlers = [
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
            "NetworkTimeoutIdleChecker: default idle_timeout = {0:,} seconds",
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
        log.debug(f"NetworkTimeoutIdleChecker._disable_timeout({session_id})")
        await redis_helper.execute(
            self._redis_live,
            lambda r: r.set(
                f"session.{session_id}.last_access",
                "0",
                xx=True,
            ),
        )

    async def _update_timeout(self, session_id: SessionId) -> None:
        log.debug(f"NetworkTimeoutIdleChecker._update_timeout({session_id})")
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
        log.debug("Got SessionStartedEvent")
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

    async def get_extra_info(self, session_id: SessionId) -> Optional[dict[str, Any]]:
        return None

    async def check_idleness(
        self,
        kernel: Row,
        dbconn: SAConnection,
        policy: Row,
        redis_obj: RedisConnectionInfo,
        *,
        grace_period_end: Optional[datetime] = None,
    ) -> bool:
        """
        Check the kernel is timeout or not.
        And save remaining time until timeout of kernel to Redis.
        """
        session_id = kernel["session_id"]

        if kernel["session_type"] == SessionTypes.BATCH:
            return True

        active_streams = await redis_helper.execute(
            self._redis_live,
            lambda r: r.zcount(
                f"session.{session_id}.active_app_connections",
                float("-inf"),
                float("+inf"),
            ),
        )
        if active_streams is not None and active_streams > 0:
            return True
        now: float = await get_redis_now(self._redis_live)
        raw_last_access = await redis_helper.execute(
            self._redis_live,
            lambda r: r.get(f"session.{session_id}.last_access"),
        )
        if raw_last_access is None or raw_last_access == "0":
            return True
        last_access = float(raw_last_access)
        # serves as the default fallback if keypair resource policy's idle_timeout is "undefined"
        idle_timeout: float = self.idle_timeout.total_seconds()
        # setting idle_timeout:
        # - zero/inf means "infinite"
        # - negative means "undefined"
        if policy["idle_timeout"] >= 0:
            idle_timeout = float(policy["idle_timeout"])
        if (idle_timeout <= 0) or (math.isinf(idle_timeout) and idle_timeout > 0):
            return True
        tz = grace_period_end.tzinfo if grace_period_end is not None else None
        remaining = calculate_remaining_time(
            datetime.fromtimestamp(now, tz=tz),
            datetime.fromtimestamp(last_access, tz=tz),
            timedelta(seconds=idle_timeout),
            grace_period_end,
        )
        await self.set_remaining_time_report(
            redis_obj, session_id, remaining if remaining > 0 else IDLE_TIMEOUT_VALUE
        )
        return remaining >= 0

    async def get_checker_result(
        self,
        redis_obj: RedisConnectionInfo,
        session_id: SessionId,
    ) -> Optional[float]:
        key = self.get_report_key(session_id)
        data = await redis_helper.execute(redis_obj, lambda r: r.get(key))
        return msgpack.unpackb(data) if data is not None else None


class SessionLifetimeChecker(BaseIdleChecker):
    terminate_reason: KernelLifecycleEventReason = KernelLifecycleEventReason.IDLE_SESSION_LIFETIME
    remaining_time_type: RemainingTimeType = RemainingTimeType.EXPIRE_AFTER
    name: ClassVar[str] = "session_lifetime"
    report_key: ClassVar[str] = "session_lifetime"
    extra_info_key: ClassVar[str] = "session_lifetime_extra"

    async def populate_config(self, raw_config: Mapping[str, Any]) -> None:
        pass

    async def get_extra_info(self, session_id: SessionId) -> Optional[dict[str, Any]]:
        return None

    async def check_idleness(
        self,
        kernel: Row,
        dbconn: SAConnection,
        policy: Row,
        redis_obj: RedisConnectionInfo,
        *,
        grace_period_end: Optional[datetime] = None,
    ) -> bool:
        """
        Check the kernel has been living longer than resource policy's `max_session_lifetime`.
        And save remaining time until `max_session_lifetime` of kernel to Redis.
        """

        session_id = kernel["session_id"]
        if (max_session_lifetime := policy["max_session_lifetime"]) > 0:
            # TODO: once per-status time tracking is implemented, let's change created_at
            #       to the timestamp when the session entered PREPARING status.
            idle_timeout = timedelta(seconds=max_session_lifetime)
            now: datetime = await get_db_now(dbconn)
            kernel_created_at: datetime = kernel["created_at"]
            remaining = calculate_remaining_time(
                now, kernel_created_at, idle_timeout, grace_period_end
            )
            await self.set_remaining_time_report(
                redis_obj, session_id, remaining if remaining > 0 else IDLE_TIMEOUT_VALUE
            )
            return remaining > 0
        return True

    async def get_checker_result(
        self,
        redis_obj: RedisConnectionInfo,
        session_id: SessionId,
    ) -> Optional[float]:
        key = self.get_report_key(session_id)
        data = await redis_helper.execute(redis_obj, lambda r: r.get(key))
        return msgpack.unpackb(data) if data is not None else None


class UtilizationIdleChecker(BaseIdleChecker):
    """
    Checks the idleness of a session by the average utilization of compute devices.
    """

    terminate_reason: KernelLifecycleEventReason = KernelLifecycleEventReason.IDLE_UTILIZATION
    remaining_time_type: RemainingTimeType = RemainingTimeType.GRACE_PERIOD
    name: ClassVar[str] = "utilization"
    report_key: ClassVar[str] = "utilization"
    extra_info_key: ClassVar[str] = "utilization_extra"

    _config_iv = t.Dict(
        {
            t.Key("time-window", default="10m"): tx.TimeDuration(),
            t.Key("initial-grace-period", default="5m"): tx.TimeDuration(),
            t.Key("thresholds-check-operator", default=ThresholdOperator.AND): tx.Enum(
                ThresholdOperator
            ),
            t.Key("resource-thresholds", default=None): t.Null
            | t.Dict(
                {
                    t.Key("cpu_util", default=None): t.Null | t.Dict({t.Key("average"): t.Float}),
                    t.Key("mem", default=None): t.Null | t.Dict({t.Key("average"): t.Float}),
                    t.Key("cuda_util", default=None): t.Null | t.Dict({t.Key("average"): t.Float}),
                    t.Key("cuda_mem", default=None): t.Null | t.Dict({t.Key("average"): t.Float}),
                    t.Key("atom_mem", default=None): t.Null | t.Dict({t.Key("average"): t.Float}),
                },
            ),
        },
    ).allow_extra("*")

    resource_thresholds: MutableMapping[str, Union[int, float, Decimal, None]]
    thresholds_check_operator: ThresholdOperator
    time_window: timedelta
    initial_grace_period: timedelta
    _evhandlers: List[EventHandler[None, AbstractEvent]]
    slot_prefix_to_utilization_metric_map: Mapping[str, Set[str]] = {
        "cpu": {"cpu_util"},
        "mem": {"mem"},
        "cuda": {"cuda_util", "cuda_mem"},
        "atom": {"atom_mem"},
    }

    async def populate_config(self, raw_config: Mapping[str, Any]) -> None:
        config = self._config_iv.check(raw_config)
        raw_resource_thresholds = config.get("resource-thresholds")
        if raw_resource_thresholds is not None:
            self.resource_thresholds = {
                k: nmget(v, "average") for k, v in raw_resource_thresholds.items()
            }
        else:
            resources: list[str] = []
            for r in self.slot_prefix_to_utilization_metric_map.values():
                resources = [*resources, *r]
            self.resource_thresholds = {r: None for r in resources}
        self.thresholds_check_operator: ThresholdOperator = config.get("thresholds-check-operator")
        self.time_window = config.get("time-window")
        self.initial_grace_period = config.get("initial-grace-period")

        thresholds_log = " ".join([
            f"{k}({threshold})," for k, threshold in self.resource_thresholds.items()
        ])
        log.info(
            f"UtilizationIdleChecker(%): {thresholds_log} "
            f'thresholds-check-operator("{self.thresholds_check_operator}"), '
            f"time-window({self.time_window.total_seconds()}s)"
        )

    def get_extra_info_key(self, session_id: SessionId) -> str:
        return f"session.{session_id}.{self.extra_info_key}"

    async def get_extra_info(self, session_id: SessionId) -> Optional[dict[str, Any]]:
        data = await redis_helper.execute(
            self._redis_live,
            lambda r: r.get(
                self.get_extra_info_key(session_id),
            ),
        )
        return msgpack.unpackb(data) if data is not None else None

    def get_time_window(self, policy: Row) -> timedelta:
        # Respect idle_timeout, from keypair resource policy, over time_window.
        if (idle_timeout := policy["idle_timeout"]) >= 0:
            return timedelta(seconds=idle_timeout)
        return self.time_window

    def _get_last_collected_key(self, session_id: SessionId) -> str:
        return f"session.{session_id}.util_last_collected"

    def _get_first_collected_key(self, session_id: SessionId) -> str:
        return f"session.{session_id}.util_first_collected"

    async def check_idleness(
        self,
        kernel: Row,
        dbconn: SAConnection,
        policy: Row,
        redis_obj: RedisConnectionInfo,
        *,
        grace_period_end: Optional[datetime] = None,
    ) -> bool:
        """
        Check the the average utilization of kernel and whether it exceeds the threshold or not.
        And save the average utilization of kernel to Redis.
        """
        session_id = kernel["session_id"]

        interval = IdleCheckerHost.check_interval
        # time_window: Utilization is calculated within this window.
        time_window: timedelta = self.get_time_window(policy)
        occupied_slots = kernel["occupied_slots"]
        unavailable_resources: Set[str] = set()

        util_series_key = f"session.{session_id}.util_series"
        util_first_collected_key = self._get_first_collected_key(session_id)
        util_last_collected_key = self._get_last_collected_key(session_id)

        # window_size: the length of utilization reports.
        window_size = int(time_window.total_seconds() / interval)
        if (window_size <= 0) or (math.isinf(window_size) and window_size > 0):
            return True

        # Wait until the time "interval" is passed after the last udpated time.
        t = await redis_helper.execute(self._redis_live, lambda r: r.time())
        util_now: float = t[0] + (t[1] / (10**6))
        raw_util_last_collected = cast(
            bytes | None,
            await redis_helper.execute(
                self._redis_live,
                lambda r: r.get(util_last_collected_key),
            ),
        )
        util_last_collected: float = (
            float(raw_util_last_collected) if raw_util_last_collected else 0.0
        )
        if util_now - util_last_collected < interval:
            return True

        raw_util_first_collected = cast(
            bytes | None,
            await redis_helper.execute(
                self._redis_live,
                lambda r: r.get(util_first_collected_key),
            ),
        )
        if raw_util_first_collected is None:
            util_first_collected = util_now
            await redis_helper.execute(
                self._redis_live,
                lambda r: r.set(
                    util_first_collected_key,
                    f"{util_now:.06f}",
                    ex=max(86400, int(self.time_window.total_seconds() * 2)),
                ),
            )
        else:
            util_first_collected = float(raw_util_first_collected)

        # Report time remaining until the first time window is full as expire time
        db_now: datetime = await get_db_now(dbconn)
        kernel_created_at: datetime = kernel["created_at"]
        if grace_period_end is not None:
            start_from = max(grace_period_end, kernel_created_at)
        else:
            start_from = kernel_created_at
        total_initial_grace_period_end = start_from + self.initial_grace_period
        remaining = calculate_remaining_time(
            db_now, kernel_created_at, time_window, total_initial_grace_period_end
        )
        await self.set_remaining_time_report(
            redis_obj, session_id, remaining if remaining > 0 else IDLE_TIMEOUT_VALUE
        )

        # Respect initial grace period (no calculation of utilization and no termination of the session)
        if db_now <= total_initial_grace_period_end:
            return True

        # Merge same type of (exclusive) resources as a unique resource with the values added.
        # Example: {cuda.device: 0, cuda.shares: 0.5} -> {cuda: 0.5}.
        unique_res_map: DefaultDict[str, Decimal] = defaultdict(Decimal)
        for slot_name, alloc in occupied_slots.items():
            unique_key = slot_name.split(".")[0]
            unique_res_map[unique_key] += alloc

        # Do not take into account unallocated resources. For example, do not garbage collect
        # a session without GPU even if cuda_util is configured in resource-thresholds.
        for slot_prefix, util_metric in self.slot_prefix_to_utilization_metric_map.items():
            if unique_res_map.get(slot_prefix, 0) == 0:
                unavailable_resources.update(util_metric)

        # Get current utilization data from all containers of the session.
        if kernel["cluster_size"] > 1:
            query = sa.select([kernels.c.id]).where(
                (kernels.c.session_id == session_id) & (kernels.c.status.in_(LIVE_STATUS)),
            )
            rows = (await dbconn.execute(query)).fetchall()
            kernel_ids = [k["id"] for k in rows]
        else:
            kernel_ids = [kernel["id"]]
        current_utilizations = await self.get_current_utilization(kernel_ids, occupied_slots)
        if current_utilizations is None:
            return True

        # Update utilization time-series data.
        raw_util_series = await redis_helper.execute(
            self._redis_live, lambda r: r.get(util_series_key)
        )

        try:
            util_series: dict[str, list[float]] = msgpack.unpackb(raw_util_series, use_list=True)
        except TypeError:
            util_series = {k: [] for k in self.resource_thresholds.keys()}

        do_idle_check: bool = True

        for k in util_series:
            util_series[k].append(current_utilizations[k])
            if len(util_series[k]) > window_size:
                util_series[k].pop(0)
            else:
                do_idle_check = False

        # Do not skip idleness-check if the current time passed the time window
        if util_now - util_first_collected >= time_window.total_seconds():
            do_idle_check = True

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
                f"{util_now:.06f}",
                ex=max(86400, int(self.time_window.total_seconds() * 2)),
            ),
        )

        def _avg(util_list: list[float]) -> float:
            try:
                return sum(util_list) / len(util_list)
            except ZeroDivisionError:
                return 0.0

        avg_utils: Mapping[str, float] = {k: _avg(v) for k, v in util_series.items()}

        util_avg_thresholds = UtilizationResourceReport.from_avg_threshold(
            avg_utils, self.resource_thresholds, unavailable_resources
        )
        report = {
            "thresholds_check_operator": self.thresholds_check_operator.value,
            "resources": util_avg_thresholds.to_dict(),
        }
        await redis_helper.execute(
            self._redis_live,
            lambda r: r.set(
                self.get_extra_info_key(session_id),
                msgpack.packb(report),
                ex=int(DEFAULT_CHECK_INTERVAL) * 10,
            ),
        )

        if not do_idle_check:
            return True

        # Check over-utilized (not to be collected) resources.
        sufficiently_utilized = util_avg_thresholds.utilization_result
        check_result = True
        if len(sufficiently_utilized) < 1:
            check_result = True
        elif self.thresholds_check_operator == ThresholdOperator.OR:
            check_result = all(sufficiently_utilized.values())
        else:  # "and" operation is the default
            check_result = any(sufficiently_utilized.values())
        if not check_result:
            log.info(
                "utilization timeout: {} ({}, {})",
                session_id,
                avg_utils,
                self.thresholds_check_operator,
            )
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
            divider = len(kernel_ids) if kernel_ids else 1
            for kernel_id in kernel_ids:
                raw_live_stat = cast(
                    bytes | None,
                    await redis_helper.execute(
                        self._redis_stat,
                        lambda r: r.get(str(kernel_id)),
                    ),
                )
                if raw_live_stat is None:
                    log.warning(
                        f"Utilization data not found or failed to fetch utilization data, abort idle check (k:{kernel_id})"
                    )
                    return None
                live_stat = cast(dict[str, Any], msgpack.unpackb(raw_live_stat))
                kernel_utils = {
                    k: float(nmget(live_stat, f"{k}.pct", 0.0))
                    for k in self.resource_thresholds.keys()
                }

                utilizations = {
                    k: utilizations[k] + kernel_utils[k] for k in self.resource_thresholds.keys()
                }
            utilizations = {k: utilizations[k] / divider for k in self.resource_thresholds.keys()}

            # NOTE: Manual calculation of mem utilization.
            # mem.capacity does not report total amount of memory allocated to
            # the container, and mem.pct always report >90% even when nothing is
            # executing. So, we just replace it with the value of occupied slot.
            mem_slots = float(occupied_slots.get("mem", 0))
            mem_current = float(nmget(live_stat, "mem.current", 0.0))
            utilizations["mem"] = mem_current / mem_slots * 100 if mem_slots > 0 else 0
            return utilizations
        except Exception as e:
            _msg = f"Unable to collect utilization for idleness check (kernels:{kernel_ids})"
            log.warning(_msg, exc_info=e)
            return None

    async def get_checker_result(
        self,
        redis_obj: RedisConnectionInfo,
        session_id: SessionId,
    ) -> Optional[float]:
        key = self.get_report_key(session_id)
        data = await redis_helper.execute(redis_obj, lambda r: r.get(key))
        return msgpack.unpackb(data) if data is not None else None


checker_registry: Mapping[str, Type[BaseIdleChecker]] = {
    NetworkTimeoutIdleChecker.name: NetworkTimeoutIdleChecker,
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
    checker_host = IdleCheckerHost(
        db,
        shared_config,
        event_dispatcher,
        event_producer,
        lock_factory,
    )
    checker_init_args = (event_dispatcher, checker_host._redis_live, checker_host._redis_stat)
    log.info("Initializing idle checker: user_initial_grace_period, session_lifetime")
    checker_host.add_checker(SessionLifetimeChecker(*checker_init_args))  # enabled by default
    enabled_checkers = await shared_config.etcd.get("config/idle/enabled")
    if enabled_checkers:
        for checker_name in enabled_checkers.split(","):
            checker_name = checker_name.strip()
            checker_cls = checker_registry.get(checker_name, None)
            if checker_cls is None:
                log.warning("ignoring an unknown idle checker name: {}", checker_name)
                continue
            log.info("Initializing idle checker: {}", checker_name)
            checker_instance = checker_cls(*checker_init_args)
            checker_host.add_checker(checker_instance)
    return checker_host
