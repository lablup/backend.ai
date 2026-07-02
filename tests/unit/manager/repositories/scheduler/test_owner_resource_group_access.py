"""Regression tests for BA-5888 — owner-only resource-group access at session enqueue.

Mirrors the test class previously kept under
``tests/unit/manager/sokovan/scheduling_controller/test_integration.py::TestOwnerOnlyScalingGroupForDelegation``
(deleted along with the legacy ``_resolve_scaling_group`` helper in #11250),
adapted to the current location of the check inside
``ScheduleDBSource.fetch_session_spec_contexts``.

When a session is enqueued — including delegated sessions where the spec
identity has been swapped to the owner's ``access_key`` — resource group
access MUST be resolved using that identity's allowlist only, never the
requester's, and never the union of both.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from datetime import timedelta
from unittest.mock import AsyncMock, patch

import pytest

from ai.backend.common.identifier.domain import DomainName
from ai.backend.common.identifier.project import ProjectID
from ai.backend.common.identifier.resource_group import ResourceGroupName
from ai.backend.common.identifier.session import SessionID
from ai.backend.common.types import AccessKey
from ai.backend.manager.data.session.draft import (
    SessionIdentityDraft,
    SessionScopeDraft,
    SessionSpecDraft,
)
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.resource_slot import AgentResourceRow, ResourceSlotTypeRow
from ai.backend.manager.models.scaling_group import ScalingGroupOpts, ScalingGroupRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.scheduler.db_source.db_source import ScheduleDBSource
from ai.backend.manager.repositories.scheduler.types.session_creation import AllowedScalingGroup
from ai.backend.testutils.db import with_tables

RG_NAME = "admin-only"


def _build_delegated_draft(
    *,
    owner_access_key: AccessKey,
    resource_group: str | None,
) -> SessionSpecDraft:
    """Build a draft mirroring what the service layer hands to
    :meth:`ScheduleDBSource.fetch_session_spec_contexts` after resolving
    ``owner_id``: identity carries the owner's access key.
    """
    return SessionSpecDraft(
        identity=SessionIdentityDraft(
            session_id=SessionID(uuid.uuid4()),
            creation_id="deleg-rg-test",
            session_name="deleg-rg-test",
            access_key=owner_access_key,
            user_uuid=uuid.uuid4(),
        ),
        scope=SessionScopeDraft(
            domain_name=DomainName("default"),
            project_id=ProjectID(uuid.uuid4()),
            resource_group_name=(ResourceGroupName(resource_group) if resource_group else None),
        ),
    )


@dataclass(frozen=True)
class RGAccessCase:
    """Parametrize input — names a scenario and pins its expected behavior.

    ``owner_has_access`` flags whether the spec identity is associated with
    the requested RG; the test resolves it into the mocked allowlist.
    """

    label: str
    owner_has_access: bool


class TestOwnerOnlyResourceGroupForDelegation:
    """RG access at enqueue time MUST follow the spec identity's allowlist."""

    @pytest.fixture
    def sample_owner_access_key(self) -> AccessKey:
        return AccessKey("AKIAOWNERONLY00000000")

    @pytest.fixture
    def sample_accessible_rg(self) -> AllowedScalingGroup:
        return AllowedScalingGroup(
            name=RG_NAME,
            is_private=False,
            scheduler_opts=ScalingGroupOpts(
                allowed_session_types=[],
                pending_timeout=timedelta(hours=1),
                config={},
            ),
        )

    @pytest.fixture
    async def db_with_rg(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Seed a single ``admin-only`` resource group row.

        The RG existence check inside ``fetch_session_spec_contexts`` runs
        before the access check, so without this row the code path would
        short-circuit on ``ScalingGroupNotFound`` and never exercise the
        invariant under test.
        """
        # Include the agent tables so the SG fetch's
        # ``selectinload(agents).selectinload(agent_resource_rows)`` chain
        # has tables to query, even though we seed no rows below.
        async with with_tables(
            database_connection,
            [ScalingGroupRow, ResourceSlotTypeRow, AgentRow, AgentResourceRow],
        ):
            async with database_connection.begin_session() as db_sess:
                db_sess.add(
                    ScalingGroupRow(
                        name=RG_NAME,
                        driver="static",
                        scheduler="fifo",
                        scheduler_opts=ScalingGroupOpts(
                            allowed_session_types=[],
                            pending_timeout=timedelta(hours=1),
                            config={},
                        ),
                        driver_opts={},
                        is_active=True,
                    )
                )
            yield database_connection

    @pytest.mark.parametrize(
        "case",
        [
            RGAccessCase(label="inaccessible_raises", owner_has_access=False),
            RGAccessCase(label="accessible_passes", owner_has_access=True),
        ],
        ids=lambda case: case.label,
    )
    async def test_rg_access_uses_spec_identity_access_key(
        self,
        db_with_rg: ExtendedAsyncSAEngine,
        sample_owner_access_key: AccessKey,
        sample_accessible_rg: AllowedScalingGroup,
        case: RGAccessCase,
    ) -> None:
        """Two scenarios share one invariant: the RG access lookup is scoped
        to the spec identity's access key. With an empty allowlist the
        request is rejected (``InvalidAPIParameters``); with a matching
        allowlist the access check passes (downstream DB reads then fail
        because we only seeded the RG row, but those failures are not
        ``InvalidAPIParameters``).
        """
        draft = _build_delegated_draft(
            owner_access_key=sample_owner_access_key,
            resource_group=RG_NAME,
        )
        allowed_rgs = [sample_accessible_rg] if case.owner_has_access else []

        db_source = ScheduleDBSource(db_with_rg)

        with patch.object(
            ScheduleDBSource,
            "_query_allowed_scaling_groups",
            new_callable=AsyncMock,
            return_value=allowed_rgs,
        ) as mock_query:
            if case.owner_has_access:
                with pytest.raises(Exception) as exc_info:
                    await db_source.fetch_session_spec_contexts(draft)
                assert not isinstance(exc_info.value, InvalidAPIParameters), (
                    f"RG access check must not raise when owner has access; got {exc_info.value!r}"
                )
            else:
                with pytest.raises(InvalidAPIParameters, match=RG_NAME):
                    await db_source.fetch_session_spec_contexts(draft)

        # Lookup MUST be scoped to the spec identity's access key — not
        # the requester's. This is the core invariant.
        mock_query.assert_awaited_once()
        assert mock_query.call_args.args[3] == sample_owner_access_key, (
            "Resource group lookup must use the spec identity's access key"
        )
