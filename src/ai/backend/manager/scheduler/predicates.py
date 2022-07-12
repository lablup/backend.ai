import logging
from datetime import datetime
from typing import List

import sqlalchemy as sa
from dateutil.tz import tzutc
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common import redis_helper
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import ResourceSlot, SessionTypes
from ai.backend.manager.models.session import SessionRow

from ..models import (
    DefaultForUnspecified,
    KeyPairResourcePolicyRow,
    check_all_dependencies,
    query_allowed_sgroups,
)
from ..models.utils import execute_with_retry, reenter_txn_session
from .types import PredicateResult, SchedulingContext

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
    db_sess: SASession,
    sched_ctx: SchedulingContext,
    sess_ctx: SessionRow,
) -> PredicateResult:
    """
    Check if a batch-type session should not be started for a certain amount of time.
    """
    if sess_ctx.session_type == SessionTypes.BATCH:
        starts_at = sess_ctx.starts_at

        if starts_at is not None and datetime.now(tzutc()) < starts_at:
            return PredicateResult(
                False,
                'Before start time',
            )
    return PredicateResult(True)


async def check_concurrency(
    db_sess: SASession,
    sched_ctx: SchedulingContext,
    sess_ctx: SessionRow,
) -> PredicateResult:

    resource_policy = sess_ctx.access_key_row.resource_policy_row
    if resource_policy is None:
        query = (
            sa.select(KeyPairResourcePolicyRow)
            .where(KeyPairResourcePolicyRow.name == sess_ctx.access_key_row.resource_policy)
        )
        result = await db_sess.execute(query)
        resource_policy = result.scalar()

    max_concurrent_sessions = resource_policy.max_concurrent_sessions
    ok, concurrency_used = await redis_helper.execute_script(
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
    db_sess: SASession,
    sched_ctx: SchedulingContext,
    sess_ctx: SessionRow,
) -> PredicateResult:
    pending_dependencies = await check_all_dependencies(db_sess, sess_ctx)
    err_msg = "Waiting dependency sessions to finish as success. ({})".format(
        ", ".join(f"{sess_row.name} ({sess_row.session_id})" for sess_row in pending_dependencies),
    ) if pending_dependencies else None
    all_success = not pending_dependencies
    return PredicateResult(all_success, err_msg)


async def check_keypair_resource_limit(
    db_sess: SASession,
    sched_ctx: SchedulingContext,
    sess_ctx: SessionRow,
) -> PredicateResult:
    resource_policy = sess_ctx.access_key_row.resource_policy_row
    if resource_policy is None:
        query = (
            sa.select(KeyPairResourcePolicyRow)
            .where(KeyPairResourcePolicyRow.name == sess_ctx.access_key_row.resource_policy)
        )
        result = await db_sess.execute(query)
        resource_policy = result.scalar()
    total_keypair_allowed = ResourceSlot.from_policy(resource_policy.get_map(),
                                                     sched_ctx.known_slot_types)
    key_occupied = await sched_ctx.registry.get_keypair_occupancy(
        sess_ctx.access_key, sess=db_sess)
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
    db_sess: SASession,
    sched_ctx: SchedulingContext,
    sess_ctx: SessionRow,
) -> PredicateResult:
    group_resource_slots = sess_ctx.group.total_resource_slots
    group_resource_policy = {'total_resource_slots': group_resource_slots,
                             'default_for_unspecified': DefaultForUnspecified.UNLIMITED}
    total_group_allowed = ResourceSlot.from_policy(group_resource_policy,
                                                   sched_ctx.known_slot_types)
    group_occupied = await sched_ctx.registry.get_group_occupancy(
        sess_ctx.group_id, sess=db_sess)
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
    db_sess: SASession,
    sched_ctx: SchedulingContext,
    sess_ctx: SessionRow,
) -> PredicateResult:
    domain_resource_slots = sess_ctx.domain.total_resource_slots
    domain_resource_policy = {
        'total_resource_slots': domain_resource_slots,
        'default_for_unspecified': DefaultForUnspecified.UNLIMITED,
    }
    total_domain_allowed = ResourceSlot.from_policy(domain_resource_policy,
                                                    sched_ctx.known_slot_types)
    domain_occupied = await sched_ctx.registry.get_domain_occupancy(
        sess_ctx.domain_name, sess=db_sess)
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
    db_sess: SASession,
    sched_ctx: SchedulingContext,
    sess_ctx: SessionRow,
) -> PredicateResult:

    async def _query():
        async with reenter_txn_session(sched_ctx.registry.db, db_sess) as _db_sess:
            return await query_allowed_sgroups(
                _db_sess,
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
    preferred_sgroup_name = sess_ctx.scaling_group_name
    if preferred_sgroup_name is not None:
        # Consider only the preferred scaling group.
        for sgroup in sgroups:
            if preferred_sgroup_name == sgroup.name:
                preferred_sgroup = sgroup
                break
        else:
            return PredicateResult(
                False,
                f"You do not have access to the scaling group '{preferred_sgroup_name}'.",
                permanent=True,
            )
        allowed_session_types = preferred_sgroup.scheduler_opts.allowed_session_types
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
            allowed_session_types = sgroup.scheduler_opts.allowed_session_types
            if sess_ctx.session_type.value.lower() in allowed_session_types:
                usable_sgroups.append(sgroup)
        if not usable_sgroups:
            return PredicateResult(
                False,
                f"No scaling groups accept the session type '{sess_ctx.session_type}'.",
                permanent=True,
            )
        target_sgroup_names = [sgroup.name for sgroup in usable_sgroups]
    assert target_sgroup_names
    log.debug("scaling groups considered for s:{} are {}", sess_ctx.id, target_sgroup_names)
    # No use of sess_ctx.target_sgroup_names anywhere, but should we update this field?
    # sess_ctx.target_sgroup_names.extend(target_sgroup_names)
    return PredicateResult(True)
