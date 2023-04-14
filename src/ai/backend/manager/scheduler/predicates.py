import logging
from datetime import datetime
from typing import Any, Optional

import sqlalchemy as sa
from dateutil.tz import tzutc
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common import redis_helper
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import ResourceSlot, SessionResult, SessionTypes

from ..defs import DEFAULT_ROLE
from ..models import (
    DefaultForUnspecified,
    DomainRow,
    GroupRow,
    KernelStatus,
    KeyPairResourcePolicyRow,
    KeyPairRow,
    SessionDependencyRow,
    SessionRow,
    kernels,
    keypair_resource_policies,
    keypairs,
)
from ..models.utils import execute_with_retry
from .types import PredicateResult, SchedulingContext

log = BraceStyleAdapter(logging.getLogger("ai.backend.manager.scheduler"))

_check_keypair_concurrency_script = """
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local result = {}
redis.call('SETNX', key, 0)
local count = tonumber(redis.call('GET', key))
if limit > 0 and count >= limit then
    result[1] = 0
    result[2] = count
    return result
end
redis.call('INCR', key)
result[1] = 1
result[2] = count + 1
return result
"""


async def check_reserved_batch_session(
    db_sess: SASession,
    sched_ctx: SchedulingContext,
    sess_ctx: SessionRow,
) -> PredicateResult:
    """
    Check if a batch-type session should not be started for a certain amount of time.
    """
    if sess_ctx.session_type == SessionTypes.BATCH:
        query = sa.select(SessionRow.starts_at).where(SessionRow.id == sess_ctx.id)
        starts_at = await db_sess.scalar(query)
        if starts_at is not None and datetime.now(tzutc()) < starts_at:
            return PredicateResult(
                False,
                "Before start time",
            )
    return PredicateResult(True)


async def check_concurrency(
    db_sess: SASession,
    sched_ctx: SchedulingContext,
    sess_ctx: SessionRow,
) -> PredicateResult:
    async def _get_max_concurrent_sessions() -> int:
        resouce_policy_q = sa.select(KeyPairRow.resource_policy).where(
            KeyPairRow.access_key == sess_ctx.access_key
        )
        select_query = sa.select(KeyPairResourcePolicyRow.max_concurrent_sessions).where(
            KeyPairResourcePolicyRow.name == resouce_policy_q.scalar_subquery()
        )
        result = await db_sess.execute(select_query)
        return result.scalar()

    max_concurrent_sessions = await execute_with_retry(_get_max_concurrent_sessions)
    ok, concurrency_used = await redis_helper.execute_script(
        sched_ctx.registry.redis_stat,
        "check_keypair_concurrency_used",
        _check_keypair_concurrency_script,
        [f"keypair.concurrency_used.{sess_ctx.access_key}"],
        [max_concurrent_sessions],
    )
    if ok == 0:
        return PredicateResult(
            False,
            f"You cannot run more than {max_concurrent_sessions} concurrent sessions",
        )
    log.debug(
        "number of concurrent sessions of ak:{0} = {1} / {2}",
        sess_ctx.access_key,
        concurrency_used,
        max_concurrent_sessions,
    )
    return PredicateResult(True)


async def check_dependencies(
    db_sess: SASession,
    sched_ctx: SchedulingContext,
    sess_ctx: SessionRow,
) -> PredicateResult:
    j = sa.join(
        SessionDependencyRow,
        SessionRow,
        SessionDependencyRow.depends_on == SessionRow.id,
    )
    query = (
        sa.select(
            SessionRow.id,
            SessionRow.name,
            SessionRow.result,
        )
        .select_from(j)
        .where(SessionDependencyRow.session_id == sess_ctx.id)
    )
    result = await db_sess.execute(query)
    rows = result.fetchall()
    pending_dependencies = []
    for row in rows:
        if row.result != SessionResult.SUCCESS:
            pending_dependencies.append(row)
    all_success = not pending_dependencies
    if all_success:
        return PredicateResult(True)
    return PredicateResult(
        False,
        "Waiting dependency sessions to finish as success. ({})".format(
            ", ".join(f"{row.name} ({row.id})" for row in pending_dependencies),
        ),
    )


async def check_keypair_resource_limit(
    db_sess: SASession,
    sched_ctx: SchedulingContext,
    sess_ctx: SessionRow,
) -> PredicateResult:
    resouce_policy_q = sa.select(KeyPairRow.resource_policy).where(
        KeyPairRow.access_key == sess_ctx.access_key
    )
    select_query = sa.select(KeyPairResourcePolicyRow).where(
        KeyPairResourcePolicyRow.name == resouce_policy_q.scalar_subquery()
    )
    result = await db_sess.execute(select_query)
    resource_policy = result.scalars().first()
    resource_policy_map = {
        "total_resource_slots": resource_policy.total_resource_slots,
        "default_for_unspecified": resource_policy.default_for_unspecified,
    }
    total_keypair_allowed = ResourceSlot.from_policy(
        resource_policy_map, sched_ctx.known_slot_types
    )
    key_occupied = await sched_ctx.registry.get_keypair_occupancy(
        sess_ctx.access_key, db_sess=db_sess
    )
    log.debug("keypair:{} current-occupancy: {}", sess_ctx.access_key, key_occupied)
    log.debug("keypair:{} total-allowed: {}", sess_ctx.access_key, total_keypair_allowed)
    if not (key_occupied + sess_ctx.requested_slots <= total_keypair_allowed):
        return PredicateResult(
            False,
            "Your keypair resource quota is exceeded. ({})".format(
                " ".join(
                    f"{k}={v}"
                    for k, v in total_keypair_allowed.to_humanized(
                        sched_ctx.known_slot_types
                    ).items()
                )
            ),
        )
    return PredicateResult(True)


async def check_group_resource_limit(
    db_sess: SASession,
    sched_ctx: SchedulingContext,
    sess_ctx: SessionRow,
) -> PredicateResult:
    query = sa.select(GroupRow.total_resource_slots).where(GroupRow.id == sess_ctx.group_id)
    group_resource_slots = await db_sess.scalar(query)
    group_resource_policy = {
        "total_resource_slots": group_resource_slots,
        "default_for_unspecified": DefaultForUnspecified.UNLIMITED,
    }
    total_group_allowed = ResourceSlot.from_policy(
        group_resource_policy, sched_ctx.known_slot_types
    )
    group_occupied = await sched_ctx.registry.get_group_occupancy(
        sess_ctx.group_id, db_sess=db_sess
    )
    log.debug("group:{} current-occupancy: {}", sess_ctx.group_id, group_occupied)
    log.debug("group:{} total-allowed: {}", sess_ctx.group_id, total_group_allowed)
    if not (group_occupied + sess_ctx.requested_slots <= total_group_allowed):
        return PredicateResult(
            False,
            "Your group resource quota is exceeded. ({})".format(
                " ".join(
                    f"{k}={v}"
                    for k, v in total_group_allowed.to_humanized(sched_ctx.known_slot_types).items()
                )
            ),
        )
    return PredicateResult(True)


async def check_domain_resource_limit(
    db_sess: SASession,
    sched_ctx: SchedulingContext,
    sess_ctx: SessionRow,
) -> PredicateResult:
    query = sa.select(DomainRow.total_resource_slots).where(DomainRow.name == sess_ctx.domain_name)
    domain_resource_slots = await db_sess.scalar(query)
    domain_resource_policy = {
        "total_resource_slots": domain_resource_slots,
        "default_for_unspecified": DefaultForUnspecified.UNLIMITED,
    }
    total_domain_allowed = ResourceSlot.from_policy(
        domain_resource_policy, sched_ctx.known_slot_types
    )
    domain_occupied = await sched_ctx.registry.get_domain_occupancy(
        sess_ctx.domain_name, db_sess=db_sess
    )
    log.debug("domain:{} current-occupancy: {}", sess_ctx.domain_name, domain_occupied)
    log.debug("domain:{} total-allowed: {}", sess_ctx.domain_name, total_domain_allowed)
    if not (domain_occupied + sess_ctx.requested_slots <= total_domain_allowed):
        return PredicateResult(
            False,
            "Your domain resource quota is exceeded. ({})".format(
                " ".join(
                    f"{k}={v}"
                    for k, v in total_domain_allowed.to_humanized(
                        sched_ctx.known_slot_types
                    ).items()
                )
            ),
        )
    return PredicateResult(True)


async def check_pending_session_limit(
    db_sess: SASession,
    sched_ctx: SchedulingContext,
    sess_ctx: SessionRow,
) -> PredicateResult:
    result = True
    failure_msgs = []

    kernel_query = (
        sa.select([kernels.c.occupied_slots])
        .select_from(kernels)
        .where(
            (kernels.c.status == KernelStatus.PENDING)
            & (kernels.c.cluster_role == DEFAULT_ROLE)
            & (kernels.c.access_key == sess_ctx.access_key)
        )
    )
    pending_kernels: list[dict[str, Any]] = (await db_sess.execute(kernel_query)).fetchall()

    j = sa.join(
        keypair_resource_policies,
        keypairs,
        keypair_resource_policies.c.name == keypairs.c.resource_policy,
    )
    policy_query = (
        sa.select(
            [
                keypair_resource_policies.c.max_pernding_sessions,
                keypair_resource_policies.c.max_pending_session_resource_slots,
            ]
        )
        .select_from(j)
        .where(keypairs.c.access_key == sess_ctx.access_key)
    )
    pending_session_policy: dict[str, Any] = (await db_sess.execute(policy_query)).first()

    max_pending_session: Optional[int] = pending_session_policy["max_pernding_sessions"]
    if max_pending_session is not None and max_pending_session > 0:
        if len(pending_kernels) >= max_pending_session:
            result = False
            failure_msgs.append(
                f"You cannot create more than {max_pending_session} pending session."
            )

    max_pending_session_resource: Optional[ResourceSlot] = pending_session_policy[
        "max_pernding_sessions"
    ]

    if max_pending_session_resource:
        current_pending_session_slots: ResourceSlot = sum(
            [kernel["occupied_slots"] for kernel in pending_kernels]
        )
        if current_pending_session_slots >= max_pending_session_resource:
            result = False
            msg = "Your pending session quota is exceeded. ({})".format(
                " ".join(
                    f"{k}={v}"
                    for k, v in current_pending_session_slots.to_humanized(
                        sched_ctx.known_slot_types
                    ).items()
                )
            )
            failure_msgs.append(msg)

    if not result:
        return PredicateResult(False, "\n".join(failure_msgs))
    log.debug(
        "number of concurrent pending sessions of ak:{0} = {1} / {2}",
        sess_ctx.access_key,
        len(pending_kernels),
        max_pending_session,
    )
    return PredicateResult(True)
