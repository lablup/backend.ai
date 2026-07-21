import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.common.types import AccessKey, ResourceSlot, SessionId
from ai.backend.manager.data.fair_share import ProjectUserIds
from ai.backend.manager.data.sokovan import SessionWorkload, SystemSnapshot
from ai.backend.manager.repositories.fair_share import FairShareRepository
from ai.backend.manager.sokovan.scheduler.provisioner.sequencers.fair_share import (
    FairShareSequencer,
)


async def test_loads_factors_by_resource_group_id() -> None:
    resource_group_id = ResourceGroupID(uuid.uuid4())
    project_id = uuid.uuid4()
    user_id = uuid.uuid4()
    workload = SessionWorkload(
        session_id=SessionId(uuid.uuid4()),
        access_key=AccessKey("user"),
        requested_slots=ResourceSlot(cpu=Decimal("1")),
        user_uuid=user_id,
        group_id=project_id,
        domain_name="default",
        scaling_group="default",
        resource_group_id=resource_group_id,
        priority=0,
    )
    repository = MagicMock(spec=FairShareRepository)
    repository.get_user_fair_share_factors_batch = AsyncMock(return_value={})
    sequencer = FairShareSequencer(repository)

    result = await sequencer.sequence(
        resource_group_id,
        MagicMock(spec=SystemSnapshot),
        [workload],
    )

    assert result == [workload]
    repository.get_user_fair_share_factors_batch.assert_awaited_once_with(
        resource_group_id,
        [ProjectUserIds(project_id=project_id, user_ids=frozenset({user_id}))],
    )
