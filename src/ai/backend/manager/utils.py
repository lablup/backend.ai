from typing import Optional
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncConnection as SAConnection

from ai.backend.common.types import AccessKey

from .models import (
    UserRole,
)
from .models import association_projects_users as apus
from .models import (
    domains,
    keypair_resource_policies,
    keypairs,
    projects,
    users,
)


def check_if_requester_is_eligible_to_act_as_target_user(
    requester_role: UserRole,
    requester_domain: str,
    target_role: UserRole,
    target_domain: str,
) -> bool:
    if requester_role == UserRole.SUPERADMIN:
        pass
    elif requester_role == UserRole.DOMAIN_ADMIN:
        if requester_domain != target_domain:
            raise RuntimeError(
                (
                    "Domain-admins can perform operations on behalf of "
                    "other users in the same domain only."
                ),
            )
        if target_role == UserRole.SUPERADMIN:
            raise RuntimeError(
                "Domain-admins cannot perform operations on behalf of super-admins.",
            )
        pass
    else:
        raise RuntimeError(
            "Only admins can perform operations on behalf of other users.",
        )
    return True


async def check_if_requester_is_eligible_to_act_as_target_access_key(
    conn: SAConnection,
    requester_role: UserRole,
    requester_domain: str,
    target_access_key: AccessKey,
) -> bool:
    query = (
        sa.select([users.c.domain_name, users.c.role])
        .select_from(sa.join(keypairs, users, keypairs.c.user == users.c.uuid))
        .where(keypairs.c.access_key == target_access_key)
    )
    result = await conn.execute(query)
    row = result.first()
    if row is None:
        raise ValueError("Unknown owner access key")
    owner_domain = row["domain_name"]
    owner_role = row["role"]
    return check_if_requester_is_eligible_to_act_as_target_user(
        requester_role,
        requester_domain,
        owner_role,
        owner_domain,
    )


async def check_if_requester_is_eligible_to_act_as_target_user_uuid(
    conn: SAConnection,
    requester_role: UserRole,
    requester_domain: str,
    target_user_uuid: UUID,
) -> bool:
    query = (
        sa.select([users.c.domain_name, users.c.role])
        .select_from(users)
        .where(users.c.uuid == target_user_uuid)
    )
    result = await conn.execute(query)
    row = result.first()
    if row is None:
        raise ValueError("Unknown owner access key")
    owner_domain = row["domain_name"]
    owner_role = row["role"]
    return check_if_requester_is_eligible_to_act_as_target_user(
        requester_role,
        requester_domain,
        owner_role,
        owner_domain,
    )


async def query_userinfo(
    conn: SAConnection,
    requester_uuid: UUID,
    requester_access_key: AccessKey,
    requester_role: UserRole,
    requester_domain: str,
    keypair_resource_policy: dict,
    requesting_domain: str,
    requesting_project: str | UUID,
    query_on_behalf_of: Optional[AccessKey] = None,
) -> tuple[UUID, UUID, dict]:
    if query_on_behalf_of is not None and query_on_behalf_of != requester_access_key:
        await check_if_requester_is_eligible_to_act_as_target_access_key(
            conn,
            requester_role,
            requester_domain,
            query_on_behalf_of,
        )
        owner_access_key = query_on_behalf_of
    else:
        owner_access_key = requester_access_key

    owner_uuid = None
    project_id = None
    resource_policy = None

    if requester_access_key != owner_access_key:
        # Admin or superadmin is creating sessions for another user.
        # The check for admin privileges is already done in get_access_key_scope().
        query = (
            sa.select(
                [keypairs.c.user, keypairs.c.resource_policy, users.c.role, users.c.domain_name]
            )
            .select_from(sa.join(keypairs, users, keypairs.c.user == users.c.uuid))
            .where(keypairs.c.access_key == owner_access_key)
        )
        result = await conn.execute(query)
        row = result.first()
        owner_domain = row["domain_name"]
        owner_uuid = row["user"]
        owner_role = row["role"]
        query = (
            sa.select([keypair_resource_policies])
            .select_from(keypair_resource_policies)
            .where(keypair_resource_policies.c.name == row["resource_policy"])
        )
        result = await conn.execute(query)
        resource_policy = result.first()
    else:
        # Normal case when the user is creating her/his own session.
        owner_domain = requester_domain
        owner_uuid = requester_uuid
        owner_role = UserRole.USER
        resource_policy = keypair_resource_policy

    query = (
        sa.select([domains.c.name])
        .select_from(domains)
        .where(
            (domains.c.name == owner_domain) & (domains.c.is_active),
        )
    )
    qresult = await conn.execute(query)
    domain_name = qresult.scalar()
    if domain_name is None:
        raise ValueError("Invalid domain")

    if isinstance(requesting_project, str):
        project_match_query = projects.c.name == requesting_project
    else:
        project_match_query = projects.c.id == requesting_project
    if owner_role == UserRole.SUPERADMIN:
        # superadmin can spawn container in any designated domain/project.
        query = (
            sa.select([projects.c.id])
            .select_from(projects)
            .where(
                (projects.c.domain_name == requesting_domain)
                & (project_match_query)
                & (projects.c.is_active),
            )
        )
        qresult = await conn.execute(query)
        project_id = qresult.scalar()
    elif owner_role == UserRole.DOMAIN_ADMIN:
        # domain-admin can spawn container in any project in the same domain.
        if requesting_domain != owner_domain:
            raise ValueError("You can only set the domain to the owner's domain.")
        query = (
            sa.select([projects.c.id])
            .select_from(projects)
            .where(
                (projects.c.domain_name == owner_domain)
                & (project_match_query)
                & (projects.c.is_active),
            )
        )
        qresult = await conn.execute(query)
        project_id = qresult.scalar()
    else:
        # normal users can spawn containers in their project and domain.
        if requesting_domain != owner_domain:
            raise ValueError("You can only set the domain to your domain.")
        query = (
            sa.select([apus.c.project_id])
            .select_from(apus.join(projects, apus.c.project_id == projects.c.id))
            .where(
                (apus.c.user_id == owner_uuid)
                & (projects.c.domain_name == owner_domain)
                & (project_match_query)
                & (projects.c.is_active),
            )
        )
        qresult = await conn.execute(query)
        project_id = qresult.scalar()
    if project_id is None:
        raise ValueError("Invalid project")

    return owner_uuid, project_id, resource_policy
