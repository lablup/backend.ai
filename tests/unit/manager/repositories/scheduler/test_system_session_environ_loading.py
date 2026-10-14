from __future__ import annotations

import uuid
from decimal import Decimal

import pytest

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.entity.system_session_environ import (
    SystemSessionEnvironID,
    SystemSessionEnvironScopeID,
)
from ai.backend.common.data.filter_specs import UUIDInMatchSpec
from ai.backend.common.data.system_session_environ.types import (
    SystemSessionEnvironScopeType,
    SystemSessionEnvironValueSource,
)
from ai.backend.common.types import AccessKey, SessionId
from ai.backend.manager.models.session.searchable_fields import SessionSearchableFields
from ai.backend.manager.models.session.searchers import SessionSearcher
from ai.backend.manager.models.specs.pagination import NoPagination
from ai.backend.manager.models.system_session_environ.row import SystemSessionEnvironRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.v2.reconciler.provider import ReconcileOpsProvider
from ai.backend.manager.repositories.scheduler.db_source.db_source import ScheduleDBSource
from ai.backend.testutils.fixtures import DomainFixtureData

from .conftest import create_pending_session_with_kernels


class TestSystemEnvironOfSessionsForStart:
    @pytest.fixture
    def db_source(self, db_with_cleanup: ExtendedAsyncSAEngine) -> ScheduleDBSource:
        return ScheduleDBSource(db_with_cleanup, ReconcileOpsProvider(db_with_cleanup))

    @pytest.fixture
    async def session_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_id: DomainID,
        test_domain: DomainFixtureData,
        test_scaling_group_id: ResourceGroupID,
        test_scaling_group_name: str,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_access_key: AccessKey,
        test_agent_id: str,
        resource_slot_types: None,
    ) -> SessionId:
        session_id, _ = await create_pending_session_with_kernels(
            db_with_cleanup,
            domain_id=test_domain_id,
            domain_name=test_domain.domain_name,
            resource_group_id=test_scaling_group_id,
            resource_group_name=test_scaling_group_name,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
            agent_assignments=[(test_agent_id, Decimal("1"), Decimal("1024"))],
        )
        return session_id

    @pytest.fixture
    async def rows_at_session_scopes(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_id: DomainID,
        test_group_id: uuid.UUID,
    ) -> set[SystemSessionEnvironID]:
        rows = [
            SystemSessionEnvironRow(
                value_source=SystemSessionEnvironValueSource.SESSION_ID,
                key="BACKENDAI_SESSION_ID",
                scope_type=SystemSessionEnvironScopeType.GLOBAL,
                scope_id=None,
            ),
            SystemSessionEnvironRow(
                value_source=SystemSessionEnvironValueSource.USER_EMAIL,
                key="BACKENDAI_USER_EMAIL",
                scope_type=SystemSessionEnvironScopeType.DOMAIN,
                scope_id=SystemSessionEnvironScopeID(test_domain_id),
            ),
            SystemSessionEnvironRow(
                value_source=SystemSessionEnvironValueSource.USER_NAME,
                key="BACKENDAI_USER_NAME",
                scope_type=SystemSessionEnvironScopeType.PROJECT,
                scope_id=SystemSessionEnvironScopeID(test_group_id),
            ),
        ]
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add_all(rows)
            await db_sess.flush()
            return {row.id for row in rows}

    @pytest.fixture
    async def rows_at_other_scopes(self, db_with_cleanup: ExtendedAsyncSAEngine) -> None:
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add_all([
                SystemSessionEnvironRow(
                    value_source=SystemSessionEnvironValueSource.USER_UUID,
                    key="BACKENDAI_USER_UUID",
                    scope_type=SystemSessionEnvironScopeType.DOMAIN,
                    scope_id=SystemSessionEnvironScopeID(uuid.uuid4()),
                ),
                SystemSessionEnvironRow(
                    value_source=SystemSessionEnvironValueSource.ACCESS_KEY,
                    key="BACKENDAI_ACCESS_KEY",
                    scope_type=SystemSessionEnvironScopeType.PROJECT,
                    scope_id=SystemSessionEnvironScopeID(uuid.uuid4()),
                ),
            ])

    async def test_carries_the_rows_at_the_global_scope_and_the_sessions_domain_and_project(
        self,
        db_source: ScheduleDBSource,
        session_id: SessionId,
        rows_at_session_scopes: set[SystemSessionEnvironID],
        rows_at_other_scopes: None,
    ) -> None:
        result = await db_source.search_sessions_with_kernels_and_user(
            SessionSearcher(
                pagination=NoPagination(),
                conditions=[
                    SessionSearchableFields.own.id.filter.in_(
                        UUIDInMatchSpec(values=[session_id], negated=False)
                    )
                ],
            )
        )

        assert {row.id for row in result.sessions[0].system_environ} == rows_at_session_scopes
