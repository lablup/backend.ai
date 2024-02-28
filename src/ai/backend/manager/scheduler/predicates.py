import logging
from datetime import datetime

import sqlalchemy as sa
from dateutil.tz import tzutc
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import load_only, noload

from ai.backend.common import redis_helper
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import ResourceSlot, SessionResult, SessionTypes

from ..models import (
    DefaultForUnspecified,
    DomainRow,
    GroupRow,
    KeyPairResourcePolicyRow,
    KeyPairRow,
    SessionDependencyRow,
    SessionRow,
    UserRow,
)
from ..models.session import SessionStatus
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
        if sess_ctx.is_private:
            concurrent_session_column = KeyPairResourcePolicyRow.max_concurrent_sftp_sessions
        else:
            concurrent_session_column = KeyPairResourcePolicyRow.max_concurrent_sessions
        select_query = sa.select(concurrent_session_column).where(
            KeyPairResourcePolicyRow.name == resouce_policy_q.scalar_subquery()
        )
        result = await db_sess.execute(select_query)
        return result.scalar()

    max_concurrent_sessions = await execute_with_retry(_get_max_concurrent_sessions)
    if sess_ctx.is_private:
        redis_key = f"keypair.sftp_concurrency_used.{sess_ctx.access_key}"
    else:
        redis_key = f"keypair.concurrency_used.{sess_ctx.access_key}"
    ok, concurrency_used = await redis_helper.execute_script(
        sched_ctx.registry.redis_stat,
        "check_keypair_concurrency_used",
        _check_keypair_concurrency_script,
        [redis_key],
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
            SessionRow.status,
            SessionRow.result,
        )
        .select_from(j)
        .where(SessionDependencyRow.session_id == sess_ctx.id)
    )
    result = await db_sess.execute(query)
    rows = result.fetchall()
    pending_dependencies = []
    for row in rows:
        if row.result != SessionResult.SUCCESS or row.status != SessionStatus.TERMINATED:
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


async def check_user_resource_limit(
    db_sess: SASession,
    sched_ctx: SchedulingContext,
    sess_ctx: SessionRow,
) -> PredicateResult:
    main_ak = (
        sa.select(UserRow.main_access_key)
        .where(UserRow.uuid == sess_ctx.user_uuid)
        .scalar_subquery()
    )
    resouce_policy_q = sa.select(KeyPairRow.resource_policy).where(KeyPairRow.access_key == main_ak)
    select_query = sa.select(KeyPairResourcePolicyRow).where(
        KeyPairResourcePolicyRow.name == resouce_policy_q.scalar_subquery()
    )
    resource_policy: KeyPairResourcePolicyRow | None = (await db_sess.scalars(select_query)).first()
    if resource_policy is None:
        return PredicateResult(
            False,
            f"User has no main-keypair or the main-keypair has no keypair resource policy (uid: {sess_ctx.user_uuid})",
        )

    resource_policy_map = {
        "total_resource_slots": resource_policy.total_resource_slots,
        "default_for_unspecified": resource_policy.default_for_unspecified,
    }
    total_main_keypair_allowed = ResourceSlot.from_policy(
        resource_policy_map, sched_ctx.known_slot_types
    )
    user_occupied = await sched_ctx.registry.get_user_occupancy(sess_ctx.user_uuid, db_sess=db_sess)
    log.debug("user:{} current-occupancy: {}", sess_ctx.user_uuid, user_occupied)
    log.debug("user:{} total-allowed: {}", sess_ctx.user_uuid, total_main_keypair_allowed)
    if not (user_occupied + sess_ctx.requested_slots <= total_main_keypair_allowed):
        return PredicateResult(
            False,
            "Your main-keypair resource quota is exceeded. ({})".format(
                " ".join(
                    f"{k}={v}"
                    for k, v in total_main_keypair_allowed.to_humanized(
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


async def check_pending_session_count_limit(
    db_sess: SASession,
    sched_ctx: SchedulingContext,
    sess_ctx: SessionRow,
) -> PredicateResult:
    result = True
    failure_msgs = []

    query = (
        sa.select(SessionRow)
        .where(
            (SessionRow.access_key == sess_ctx.access_key)
            & (SessionRow.status == SessionStatus.PENDING)
        )
        .options(noload("*"), load_only(SessionRow.requested_slots))
    )
    pending_sessions: list[SessionRow] = (await db_sess.scalars(query)).all()

    # TODO: replace keypair resource policies with user resource policies
    j = sa.join(
        KeyPairResourcePolicyRow,
        KeyPairRow,
        KeyPairResourcePolicyRow.name == KeyPairRow.resource_policy,
    )
    policy_stmt = (
        sa.select(KeyPairResourcePolicyRow)
        .select_from(j)
        .where(KeyPairRow.access_key == sess_ctx.access_key)
        .options(
            noload("*"),
            load_only(
                KeyPairResourcePolicyRow.max_pending_session_count,
            ),
        )
    )
    policy: KeyPairResourcePolicyRow = (await db_sess.scalars(policy_stmt)).first()

    pending_count_limit: int | None = policy.max_pending_session_count
    if pending_count_limit is not None:
        if len(pending_sessions) >= pending_count_limit:
            result = False
            failure_msgs.append(
                f"You cannot create more than {pending_count_limit} pending session(s)."
            )

    log.debug(
        "access key:{} number of pending sessions: {} / {}",
        sess_ctx.access_key,
        len(pending_sessions),
        pending_count_limit,
    )
    if not result:
        return PredicateResult(False, "\n".join(failure_msgs))
    return PredicateResult(True)


async def check_pending_session_resource_limit(
    db_sess: SASession,
    sched_ctx: SchedulingContext,
    sess_ctx: SessionRow,
) -> PredicateResult:
    result = True
    failure_msgs = []

    query = (
        sa.select(SessionRow)
        .where(
            (SessionRow.access_key == sess_ctx.access_key)
            & (SessionRow.status == SessionStatus.PENDING)
        )
        .options(noload("*"), load_only(SessionRow.requested_slots))
    )
    pending_sessions: list[SessionRow] = (await db_sess.scalars(query)).all()

    # TODO: replace keypair resource policies with user resource policies
    j = sa.join(
        KeyPairResourcePolicyRow,
        KeyPairRow,
        KeyPairResourcePolicyRow.name == KeyPairRow.resource_policy,
    )
    policy_stmt = (
        sa.select(KeyPairResourcePolicyRow)
        .select_from(j)
        .where(KeyPairRow.access_key == sess_ctx.access_key)
        .options(
            noload("*"),
            load_only(
                KeyPairResourcePolicyRow.max_pending_session_resource_slots,
            ),
        )
    )
    policy: KeyPairResourcePolicyRow = (await db_sess.scalars(policy_stmt)).first()

    pending_resource_limit: ResourceSlot | None = policy.max_pending_session_resource_slots
    if pending_resource_limit is not None and pending_resource_limit:
        current_pending_session_slots: ResourceSlot = sum(
            [session.requested_slots for session in pending_sessions], start=ResourceSlot()
        )
        if current_pending_session_slots >= pending_resource_limit:
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
        log.debug(
            "access key:{} current-occupancy of pending sessions: {}",
            sess_ctx.access_key,
            current_pending_session_slots,
        )
        log.debug(
            "access key:{} total-allowed of pending sessions: {}",
            sess_ctx.access_key,
            pending_resource_limit,
        )
    if not result:
        return PredicateResult(False, "\n".join(failure_msgs))
    return PredicateResult(True)
