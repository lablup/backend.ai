from datetime import datetime
import logging
from typing import (
    List,
)

from dateutil.tz import tzutc
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncConnection as SAConnection

from ai.backend.common import redis
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import (
    ResourceSlot,
    SessionResult,
    SessionTypes,
)

from ..models import (
    domains, groups, kernels,
    keypair_resource_policies,
    session_dependencies,
    query_allowed_sgroups,
    DefaultForUnspecified,
)
from ..models.utils import execute_with_retry, reenter_txn
from .types import (
    SchedulingContext,
    PendingSession,
    PredicateResult,
)

log = BraceStyleAdapter(logging.getLogger('ai.backend.manager.scheduler'))

_check_keypair_concurrency_script = '''
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
'''


async def check_reserved_batch_session(
    db_conn: SAConnection,
    sched_ctx: SchedulingContext,
    sess_ctx: PendingSession,
) -> PredicateResult:
    """
    Check if a batch-type session should not be started for a certain amount of time.
    """
    if sess_ctx.session_type == SessionTypes.BATCH:
        query = (
            sa.select([kernels.c.starts_at])
            .select_from(kernels)
            .where(kernels.c.id == sess_ctx.session_id)
        )
        starts_at = await db_conn.scalar(query)
        if starts_at is not None and datetime.now(tzutc()) < starts_at:
            return PredicateResult(
                False,
                'Before start time',
            )
    return PredicateResult(True)


async def check_concurrency(
    db_conn: SAConnection,
    sched_ctx: SchedulingContext,
    sess_ctx: PendingSession,
) -> PredicateResult:

    async def _get_max_concurrent_sessions() -> int:
        select_query = (
            sa.select([keypair_resource_policies])
            .select_from(keypair_resource_policies)
            .where(keypair_resource_policies.c.name == sess_ctx.resource_policy)
        )
        result = await db_conn.execute(select_query)
        return result.first()['max_concurrent_sessions']

    max_concurrent_sessions = await execute_with_retry(_get_max_concurrent_sessions)
    ok, concurrency_used = await redis.execute_script(
        sched_ctx.registry.redis_stat,
        'check_keypair_concurrency_used',
        _check_keypair_concurrency_script,
        [f"keypair.concurrency_used.{sess_ctx.access_key}"],
        [max_concurrent_sessions],
    )
    if ok == 0:
        return PredicateResult(
            False,
            "You cannot run more than "
            f"{max_concurrent_sessions} concurrent sessions",
        )
    log.debug(
        'number of concurrent sessions of ak:{0} = {1} / {2}',
        sess_ctx.access_key,
        concurrency_used,
        max_concurrent_sessions,
    )
    return PredicateResult(True)


async def check_dependencies(
    db_conn: SAConnection,
    sched_ctx: SchedulingContext,
    sess_ctx: PendingSession,
) -> PredicateResult:
    j = sa.join(
        session_dependencies,
        kernels,
        session_dependencies.c.depends_on == kernels.c.session_id,
    )
    query = (
        sa.select([
            kernels.c.session_id,
            kernels.c.session_name,
            kernels.c.result,
        ])
        .select_from(j)
        .where(session_dependencies.c.session_id == sess_ctx.session_id)
    )
    result = await db_conn.execute(query)
    rows = result.fetchall()
    pending_dependencies = []
    for row in rows:
        if row['result'] != SessionResult.SUCCESS:
            pending_dependencies.append(row)
    all_success = (not pending_dependencies)
    if all_success:
        return PredicateResult(True)
    return PredicateResult(
        False,
        "Waiting dependency sessions to finish as success. ({})".format(
            ", ".join(f"{row['session_name']} ({row['session_id']})" for row in pending_dependencies),
        ),
    )


async def check_keypair_resource_limit(
    db_conn: SAConnection,
    sched_ctx: SchedulingContext,
    sess_ctx: PendingSession,
) -> PredicateResult:
    query = (
        sa.select([keypair_resource_policies])
        .select_from(keypair_resource_policies)
        .where(keypair_resource_policies.c.name == sess_ctx.resource_policy)
    )
    result = await db_conn.execute(query)
    resource_policy = result.first()
    total_keypair_allowed = ResourceSlot.from_policy(resource_policy,
                                                     sched_ctx.known_slot_types)
    key_occupied = await sched_ctx.registry.get_keypair_occupancy(
        sess_ctx.access_key, conn=db_conn)
    log.debug('keypair:{} current-occupancy: {}', sess_ctx.access_key, key_occupied)
    log.debug('keypair:{} total-allowed: {}', sess_ctx.access_key, total_keypair_allowed)
    if not (key_occupied + sess_ctx.requested_slots <= total_keypair_allowed):
        return PredicateResult(
            False,
            "Your keypair resource quota is exceeded. ({})"
            .format(' '.join(
                f'{k}={v}' for k, v in
                total_keypair_allowed.to_humanized(sched_ctx.known_slot_types).items()
            )),
        )
    return PredicateResult(True)


async def check_group_resource_limit(
    db_conn: SAConnection,
    sched_ctx: SchedulingContext,
    sess_ctx: PendingSession,
) -> PredicateResult:
    query = (sa.select([groups.c.total_resource_slots])
               .where(groups.c.id == sess_ctx.group_id))
    group_resource_slots = await db_conn.scalar(query)
    group_resource_policy = {'total_resource_slots': group_resource_slots,
                             'default_for_unspecified': DefaultForUnspecified.UNLIMITED}
    total_group_allowed = ResourceSlot.from_policy(group_resource_policy,
                                                   sched_ctx.known_slot_types)
    group_occupied = await sched_ctx.registry.get_group_occupancy(
        sess_ctx.group_id, conn=db_conn)
    log.debug('group:{} current-occupancy: {}', sess_ctx.group_id, group_occupied)
    log.debug('group:{} total-allowed: {}', sess_ctx.group_id, total_group_allowed)
    if not (group_occupied + sess_ctx.requested_slots <= total_group_allowed):
        return PredicateResult(
            False,
            "Your group resource quota is exceeded. ({})"
            .format(' '.join(
                f'{k}={v}' for k, v in
                total_group_allowed.to_humanized(sched_ctx.known_slot_types).items()
            )),
        )
    return PredicateResult(True)


async def check_domain_resource_limit(
    db_conn: SAConnection,
    sched_ctx: SchedulingContext,
    sess_ctx: PendingSession,
) -> PredicateResult:
    query = (sa.select([domains.c.total_resource_slots])
               .where(domains.c.name == sess_ctx.domain_name))
    domain_resource_slots = await db_conn.scalar(query)
    domain_resource_policy = {
        'total_resource_slots': domain_resource_slots,
        'default_for_unspecified': DefaultForUnspecified.UNLIMITED,
    }
    total_domain_allowed = ResourceSlot.from_policy(domain_resource_policy,
                                                    sched_ctx.known_slot_types)
    domain_occupied = await sched_ctx.registry.get_domain_occupancy(
        sess_ctx.domain_name, conn=db_conn)
    log.debug('domain:{} current-occupancy: {}', sess_ctx.domain_name, domain_occupied)
    log.debug('domain:{} total-allowed: {}', sess_ctx.domain_name, total_domain_allowed)
    if not (domain_occupied + sess_ctx.requested_slots <= total_domain_allowed):
        return PredicateResult(
            False,
            'Your domain resource quota is exceeded. ({})'
            .format(' '.join(
                f'{k}={v}' for k, v in
                total_domain_allowed.to_humanized(sched_ctx.known_slot_types).items()
            )),
        )
    return PredicateResult(True)


async def check_scaling_group(
    db_conn: SAConnection,
    sched_ctx: SchedulingContext,
    sess_ctx: PendingSession,
) -> PredicateResult:

    async def _query():
        async with reenter_txn(sched_ctx.registry.db, db_conn) as _conn:
            return await query_allowed_sgroups(
                _conn,
                sess_ctx.domain_name,
                sess_ctx.group_id,
                sess_ctx.access_key,
            )

    sgroups = await execute_with_retry(_query)
    if not sgroups:
        return PredicateResult(
            False,
            "You do not have any scaling groups allowed to use.",
            permanent=True,
        )
    target_sgroup_names: List[str] = []
    preferred_sgroup_name = sess_ctx.scaling_group
    if preferred_sgroup_name is not None:
        # Consider only the preferred scaling group.
        for sgroup in sgroups:
            if preferred_sgroup_name == sgroup['name']:
                break
        else:
            return PredicateResult(
                False,
                f"You do not have access to the scaling group '{preferred_sgroup_name}'.",
                permanent=True,
            )
        allowed_session_types = sgroup['scheduler_opts'].allowed_session_types
        if sess_ctx.session_type.value.lower() not in allowed_session_types:
            return PredicateResult(
                False,
                f"The scaling group '{preferred_sgroup_name}' does not accept "
                f"the session type '{sess_ctx.session_type}'. ",
                permanent=True,
            )
        target_sgroup_names = [preferred_sgroup_name]
    else:
        # Consider all allowed scaling groups.
        usable_sgroups = []
        for sgroup in sgroups:
            allowed_session_types = sgroup['scheduler_opts'].allowed_session_types
            if sess_ctx.session_type.value.lower() in allowed_session_types:
                usable_sgroups.append(sgroup)
        if not usable_sgroups:
            return PredicateResult(
                False,
                f"No scaling groups accept the session type '{sess_ctx.session_type}'.",
                permanent=True,
            )
        target_sgroup_names = [sgroup['name'] for sgroup in usable_sgroups]
    assert target_sgroup_names
    log.debug("scaling groups considered for s:{} are {}", sess_ctx.session_id, target_sgroup_names)
    sess_ctx.target_sgroup_names.extend(target_sgroup_names)
    return PredicateResult(True)
