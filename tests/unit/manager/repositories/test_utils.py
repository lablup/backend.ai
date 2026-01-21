from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Any

import pytest
import sqlalchemy as sa
from dateutil.tz import tzutc
from sqlalchemy.engine import Row

from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.defs import DEFAULT_ROLE
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.deployment_auto_scaling_policy import DeploymentAutoScalingPolicyRow
from ai.backend.manager.models.deployment_policy import DeploymentPolicyRow
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow, kernels
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac_models import UserRoleRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.scaling_group import ScalingGroupOpts, ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import (
    ExtendedAsyncSAEngine,
    agg_to_array,
    agg_to_str,
    sql_json_merge,
)
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.testutils.db import with_tables


def create_test_password_info(password: str) -> PasswordInfo:
    """Create a PasswordInfo object for testing with default PBKDF2 algorithm."""
    return PasswordInfo(
        password=password,
        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
        rounds=100_000,
        salt_size=32,
    )


@pytest.fixture
async def db_with_cleanup(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    """Database connection with tables created for test_utils tests."""
    async with with_tables(
        database_connection,
        [
            # FK dependency order: parents before children
            DomainRow,
            ScalingGroupRow,
            UserResourcePolicyRow,
            ProjectResourcePolicyRow,
            KeyPairResourcePolicyRow,
            UserRoleRow,
            UserRow,
            KeyPairRow,
            GroupRow,
            ImageRow,
            VFolderRow,
            EndpointRow,
            DeploymentPolicyRow,
            DeploymentAutoScalingPolicyRow,
            DeploymentRevisionRow,
            SessionRow,
            AgentRow,
            KernelRow,
            RoutingRow,
            ResourcePresetRow,
        ],
    ):
        yield database_connection


@pytest.fixture
async def session_info(
    db_with_cleanup: ExtendedAsyncSAEngine,
) -> AsyncGenerator[tuple[str, Any], None]:
    """Create test session data for sql_json_merge and aggregate function tests."""
    user_uuid = str(uuid.uuid4()).replace("-", "")
    postfix = str(uuid.uuid4()).split("-")[1]
    domain_name = str(uuid.uuid4()).split("-")[0]
    group_id = str(uuid.uuid4()).replace("-", "")
    group_name = str(uuid.uuid4()).split("-")[0]
    sgroup_name = str(uuid.uuid4()).split("-")[0]
    session_id = str(uuid.uuid4()).replace("-", "")
    session_creation_id = str(uuid.uuid4()).replace("-", "")
    resource_policy_name = str(uuid.uuid4()).replace("-", "")

    async with db_with_cleanup.begin_session() as db_sess:
        scaling_group = ScalingGroupRow(
            name=sgroup_name,
            driver="test",
            scheduler="test",
            scheduler_opts=ScalingGroupOpts(),
        )
        db_sess.add(scaling_group)

        domain = DomainRow(name=domain_name, total_resource_slots={})
        db_sess.add(domain)

        user_resource_policy = UserResourcePolicyRow(
            name=resource_policy_name,
            max_vfolder_count=0,
            max_quota_scope_size=-1,
            max_session_count_per_model_session=10,
            max_customized_image_count=10,
        )
        db_sess.add(user_resource_policy)

        project_resource_policy = ProjectResourcePolicyRow(
            name=resource_policy_name,
            max_vfolder_count=0,
            max_quota_scope_size=-1,
            max_network_count=3,
        )
        db_sess.add(project_resource_policy)

        group = GroupRow(
            id=group_id,
            name=group_name,
            domain_name=domain_name,
            total_resource_slots={},
            resource_policy=resource_policy_name,
        )
        db_sess.add(group)

        user = UserRow(
            uuid=user_uuid,
            email=f"tc.runner-{postfix}@lablup.com",
            username=f"TestCaseRunner-{postfix}",
            password=create_test_password_info("test_password"),
            domain_name=domain_name,
            resource_policy=resource_policy_name,
        )
        db_sess.add(user)

        sess = SessionRow(
            id=session_id,
            creation_id=session_creation_id,
            cluster_size=1,
            domain_name=domain_name,
            scaling_group_name=sgroup_name,
            group_id=group_id,
            user_uuid=user_uuid,
            vfolder_mounts={},
        )
        db_sess.add(sess)

        kern = KernelRow(
            session_id=session_id,
            domain_name=domain_name,
            group_id=group_id,
            user_uuid=user_uuid,
            cluster_role=DEFAULT_ROLE,
            occupied_slots={},
            repl_in_port=0,
            repl_out_port=0,
            stdin_port=0,
            stdout_port=0,
            vfolder_mounts={},
        )
        db_sess.add(kern)

        await db_sess.commit()
        yield session_id, db_sess


async def _select_kernel_row(
    conn: Any,
    session_id: str | uuid.UUID,
) -> Row:
    query = kernels.select().select_from(kernels).where(kernels.c.session_id == session_id)
    kernel, *_ = await conn.execute(query)
    return kernel


@pytest.mark.asyncio
async def test_sql_json_merge__default(session_info: tuple[str, Any]) -> None:
    session_id, conn = session_info
    expected: dict[str, Any] | None = None
    kernel = await _select_kernel_row(conn, session_id)
    assert kernel is not None
    assert kernel.status_history == expected


@pytest.mark.asyncio
async def test_sql_json_merge__deeper_object(session_info: tuple[str, Any]) -> None:
    session_id, conn = session_info
    timestamp = datetime.now(tzutc()).isoformat()
    expected = {
        "kernel": {
            "session": {
                "PENDING": timestamp,
                "PREPARING": timestamp,
            },
        },
    }
    query = (
        kernels.update()
        .values({
            "status_history": sql_json_merge(
                kernels.c.status_history,
                ("kernel", "session"),
                {
                    "PENDING": timestamp,
                    "PREPARING": timestamp,
                },
            ),
        })
        .where(kernels.c.session_id == session_id)
    )
    await conn.execute(query)
    kernel = await _select_kernel_row(conn, session_id)
    assert kernel is not None
    assert kernel.status_history == expected


@pytest.mark.asyncio
async def test_sql_json_merge__append_values(session_info: tuple[str, Any]) -> None:
    session_id, conn = session_info
    timestamp = datetime.now(tzutc()).isoformat()
    expected = {
        "kernel": {
            "session": {
                "PENDING": timestamp,
                "PREPARING": timestamp,
                "TERMINATED": timestamp,
                "TERMINATING": timestamp,
            },
        },
    }
    query = (
        kernels.update()
        .values({
            "status_history": sql_json_merge(
                kernels.c.status_history,
                ("kernel", "session"),
                {
                    "PENDING": timestamp,
                    "PREPARING": timestamp,
                },
            ),
        })
        .where(kernels.c.session_id == session_id)
    )
    await conn.execute(query)
    query = (
        kernels.update()
        .values({
            "status_history": sql_json_merge(
                kernels.c.status_history,
                ("kernel", "session"),
                {
                    "TERMINATING": timestamp,
                    "TERMINATED": timestamp,
                },
            ),
        })
        .where(kernels.c.session_id == session_id)
    )
    await conn.execute(query)
    kernel = await _select_kernel_row(conn, session_id)
    assert kernel is not None
    assert kernel.status_history == expected


@pytest.mark.asyncio
async def test_sql_json_merge__kernel_status_history(session_info: tuple[str, Any]) -> None:
    session_id, conn = session_info
    timestamp = datetime.now(tzutc()).isoformat()
    expected = {
        "PENDING": timestamp,
        "PREPARING": timestamp,
        "TERMINATING": timestamp,
        "TERMINATED": timestamp,
    }
    query = (
        kernels.update()
        .values({
            "status_history": sql_json_merge(
                kernels.c.status_history,
                (),
                {
                    "PENDING": timestamp,
                    "PREPARING": timestamp,
                },
            ),
        })
        .where(kernels.c.session_id == session_id)
    )
    await conn.execute(query)
    query = (
        kernels.update()
        .values({
            "status_history": sql_json_merge(
                kernels.c.status_history,
                (),
                {
                    "TERMINATING": timestamp,
                    "TERMINATED": timestamp,
                },
            ),
        })
        .where(kernels.c.session_id == session_id)
    )
    await conn.execute(query)
    kernel = await _select_kernel_row(conn, session_id)
    assert kernel is not None
    assert kernel.status_history == expected


@pytest.mark.asyncio
async def test_sql_json_merge__mixed_formats(session_info: tuple[str, Any]) -> None:
    session_id, conn = session_info
    timestamp = datetime.now(tzutc()).isoformat()
    expected = {
        "PENDING": timestamp,
        "kernel": {
            "PREPARING": timestamp,
        },
    }
    query = (
        kernels.update()
        .values({
            "status_history": sql_json_merge(
                kernels.c.status_history,
                (),
                {
                    "PENDING": timestamp,
                },
            ),
        })
        .where(kernels.c.session_id == session_id)
    )
    await conn.execute(query)
    await _select_kernel_row(conn, session_id)
    query = (
        kernels.update()
        .values({
            "status_history": sql_json_merge(
                kernels.c.status_history,
                ("kernel",),
                {
                    "PREPARING": timestamp,
                },
            ),
        })
        .where(kernels.c.session_id == session_id)
    )
    await conn.execute(query)
    kernel = await _select_kernel_row(conn, session_id)
    assert kernel is not None
    assert kernel.status_history == expected


@pytest.mark.asyncio
async def test_sql_json_merge__json_serializable_types(session_info: tuple[str, Any]) -> None:
    session_id, conn = session_info
    expected = {
        "boolean": True,
        "integer": 10101010,
        "float": 1010.1010,
        "string": "10101010",
        "list": [
            10101010,
            "10101010",
        ],
        "dict": {
            "10101010": 10101010,
        },
    }
    query = (
        kernels.update()
        .values({
            "status_history": sql_json_merge(
                kernels.c.status_history,
                (),
                expected,
            ),
        })
        .where(kernels.c.session_id == session_id)
    )
    await conn.execute(query)
    kernel = await _select_kernel_row(conn, session_id)
    assert kernel is not None
    assert kernel.status_history == expected


@pytest.mark.asyncio
async def test_agg_to_str(session_info: tuple[str, Any]) -> None:
    session_id, conn = session_info
    test_data1, test_data2 = "hello", "world"
    expected = "hello,world"

    # Insert more kernel data
    result = await conn.execute(sa.select(kernels).where(kernels.c.session_id == session_id))
    orig_kernel = result.first()
    assert orig_kernel is not None
    orig_mapping = orig_kernel._mapping
    kernel_data = {
        "session_id": session_id,
        "domain_name": orig_mapping["domain_name"],
        "group_id": orig_mapping["group_id"],
        "user_uuid": orig_mapping["user_uuid"],
        "cluster_role": "sub",
        "occupied_slots": {},
        "requested_slots": {},
        "repl_in_port": 0,
        "repl_out_port": 0,
        "stdin_port": 0,
        "stdout_port": 0,
        "vfolder_mounts": {},
    }
    await conn.execute(
        sa.insert(kernels).values({
            "tag": test_data1,
            **kernel_data,
        })
    )
    await conn.execute(
        sa.insert(kernels).values({
            "tag": test_data2,
            **kernel_data,
        })
    )

    # Fetch Session's kernel and check `kernels_tag` field
    query = (
        sa.select(SessionRow, agg_to_str(KernelRow.tag).label("kernels_tag"))
        .select_from(sa.join(SessionRow, KernelRow))
        .where(SessionRow.id == session_id)
        .group_by(SessionRow)
    )
    result = await conn.execute(query)
    session = result.first()
    assert session is not None
    assert session._mapping["kernels_tag"] == expected

    # Delete test kernel data explicitly
    await conn.execute(
        sa.delete(kernels).where(
            (kernels.c.tag == test_data1) & (kernels.c.session_id == session_id)
        )
    )
    await conn.execute(
        sa.delete(kernels).where(
            (kernels.c.tag == test_data2) & (kernels.c.session_id == session_id)
        )
    )


@pytest.mark.asyncio
async def test_agg_to_array(session_info: tuple[str, Any]) -> None:
    session_id, conn = session_info
    test_data1, test_data2 = "a", "b"
    expected = ["a", "b", None]

    # Insert more kernel data
    result = await conn.execute(sa.select(kernels).where(kernels.c.session_id == session_id))
    orig_kernel = result.first()
    assert orig_kernel is not None
    orig_mapping = orig_kernel._mapping
    kernel_data = {
        "session_id": session_id,
        "domain_name": orig_mapping["domain_name"],
        "group_id": orig_mapping["group_id"],
        "user_uuid": orig_mapping["user_uuid"],
        "cluster_role": "sub",
        "occupied_slots": {},
        "requested_slots": {},
        "repl_in_port": 0,
        "repl_out_port": 0,
        "stdin_port": 0,
        "stdout_port": 0,
        "vfolder_mounts": {},
    }
    await conn.execute(
        sa.insert(kernels).values({
            "tag": test_data1,
            **kernel_data,
        })
    )
    await conn.execute(
        sa.insert(kernels).values({
            "tag": test_data2,
            **kernel_data,
        })
    )

    # Fetch Session's kernel and check `kernels_tag` field
    query = (
        sa.select(SessionRow, agg_to_array(KernelRow.tag).label("kernels_tag"))
        .select_from(sa.join(SessionRow, KernelRow))
        .where(SessionRow.id == session_id)
        .group_by(SessionRow)
    )
    result = await conn.execute(query)
    session = result.first()
    assert session is not None
    assert session._mapping["kernels_tag"] == expected

    # Delete test kernel data explicitly
    await conn.execute(
        sa.delete(kernels).where(
            (kernels.c.tag == test_data1) & (kernels.c.session_id == session_id)
        )
    )
    await conn.execute(
        sa.delete(kernels).where(
            (kernels.c.tag == test_data2) & (kernels.c.session_id == session_id)
        )
    )
