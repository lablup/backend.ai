import logging
from datetime import datetime

import sqlalchemy as sa
from dateutil.tz import tzutc
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common import redis_helper
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import ResourceSlot, SessionResult, SessionTypes

from ..models import (
    DefaultForUnspecified,
    DomainRow,
    KeyPairResourcePolicyRow,
    KeyPairRow,
    ProjectRow,
    SessionDependencyRow,
    SessionRow,
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
            "You cannot run more than " f"{max_concurrent_sessions} concurrent sessions",
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


async def check_project_resource_limit(
    db_sess: SASession,
    sched_ctx: SchedulingContext,
    sess_ctx: SessionRow,
) -> PredicateResult:
    query = sa.select(ProjectRow.total_resource_slots).where(ProjectRow.id == sess_ctx.project_id)
    project_resource_slots = await db_sess.scalar(query)
    project_resource_policy = {
        "total_resource_slots": project_resource_slots,
        "default_for_unspecified": DefaultForUnspecified.UNLIMITED,
    }
    total_project_allowed = ResourceSlot.from_policy(
        project_resource_policy, sched_ctx.known_slot_types
    )
    project_occupied = await sched_ctx.registry.get_project_occupancy(
        sess_ctx.group_id, db_sess=db_sess
    )
    log.debug("project:{} current-occupancy: {}", sess_ctx.project_id, project_occupied)
    log.debug("project:{} total-allowed: {}", sess_ctx.project_id, total_project_allowed)
    if not (project_occupied + sess_ctx.requested_slots <= total_project_allowed):
        return PredicateResult(
            False,
            "Your project resource quota is exceeded. ({})".format(
                " ".join(
                    f"{k}={v}"
                    for k, v in total_project_allowed.to_humanized(
                        sched_ctx.known_slot_types
                    ).items()
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
