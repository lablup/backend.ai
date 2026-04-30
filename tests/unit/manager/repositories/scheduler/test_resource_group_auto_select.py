"""Regression test for BA-5917 — resource-group auto-selection at session enqueue.

The legacy ``ScalingGroupResolver`` (deleted in #11250) auto-picked an
allowed RG when the caller omitted ``--scaling-group``. The draft-based
pipeline lost that behavior and started failing every such call with
``IncompleteSessionSpec("SessionSpec fields not resolved: scope.resource_group_name")``.

Restored as ``ScheduleDBSource.pick_default_resource_group``, which the
service layer calls when ``action.resource.resource_group`` is empty so
the draft handed to the controller already has a resolved scope.

``is_private`` filtering against ``session_type`` is intentionally NOT
done here — the legacy ``PublicPrivateFilterRule`` covered that and is
still pending restoration in a separate change.
"""

from __future__ import annotations

import uuid
from datetime import timedelta
from unittest.mock import AsyncMock, patch

import pytest

from ai.backend.common.identifier.project import ProjectID
from ai.backend.common.types import AccessKey
from ai.backend.manager.models.scaling_group import ScalingGroupOpts
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.scheduler.db_source.db_source import ScheduleDBSource
from ai.backend.manager.repositories.scheduler.types.session_creation import AllowedScalingGroup


class TestPickDefaultResourceGroup:
    """Auto-selection policy when the caller omits ``--scaling-group``."""

    @pytest.fixture
    def access_key(self) -> AccessKey:
        return AccessKey("AKIATEST00000000")

    @pytest.fixture
    def domain_name(self) -> str:
        return "default"

    @pytest.fixture
    def project_id(self) -> ProjectID:
        return ProjectID(uuid.uuid4())

    @pytest.fixture
    def scheduler_opts(self) -> ScalingGroupOpts:
        return ScalingGroupOpts(
            allowed_session_types=[],
            pending_timeout=timedelta(hours=1),
            config={},
        )

    @pytest.fixture
    def allowed_default_rg(self, scheduler_opts: ScalingGroupOpts) -> AllowedScalingGroup:
        return AllowedScalingGroup(
            name="default-rg",
            is_private=False,
            scheduler_opts=scheduler_opts,
        )

    @pytest.fixture
    def db_source(self, database_connection: ExtendedAsyncSAEngine) -> ScheduleDBSource:
        return ScheduleDBSource(database_connection)

    async def test_returns_first_allowed_rg(
        self,
        db_source: ScheduleDBSource,
        access_key: AccessKey,
        domain_name: str,
        project_id: ProjectID,
        allowed_default_rg: AllowedScalingGroup,
    ) -> None:
        """When the caller omits the scaling group, the resolver returns
        an RG from the owner's allowlist instead of letting the draft
        reach the spec finalizer with ``scope.resource_group_name = None``.
        """
        with patch.object(
            ScheduleDBSource,
            "_query_allowed_scaling_groups",
            new_callable=AsyncMock,
            return_value=[allowed_default_rg],
        ):
            picked = await db_source.pick_default_resource_group(
                access_key=access_key,
                domain_name=domain_name,
                project_id=project_id,
            )
        assert str(picked) == "default-rg"
