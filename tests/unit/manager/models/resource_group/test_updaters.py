import uuid
from datetime import timedelta

import pytest

from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.types import PreemptionMode, PreemptionOrder, PreemptionVictimScope
from ai.backend.manager.data.resource_group.types import PreemptionConfig
from ai.backend.manager.models.resource_group.updaters import ResourceGroupUpdater
from ai.backend.manager.types import OptionalState


@pytest.fixture
def preemption_config() -> PreemptionConfig:
    return PreemptionConfig(
        enabled=True,
        preemptible_priority=3,
        order=PreemptionOrder.NEWEST,
        mode=PreemptionMode.RESCHEDULE,
        preemption_min_runtime=timedelta(seconds=30),
        victim_scope=PreemptionVictimScope.PROJECT,
    )


class TestResourceGroupUpdater:
    def test_preemption_is_bound_as_a_mapping_not_a_json_string(
        self, preemption_config: PreemptionConfig
    ) -> None:
        updater = ResourceGroupUpdater(
            resource_group_id=ResourceGroupID(uuid.uuid4()),
            preemption_config=OptionalState.update(preemption_config),
        )

        _column, _path, new_value = updater.build_values()["scheduler_opts"].clauses

        assert new_value.clause.value == {
            "enabled": True,
            "preemptible_priority": 3,
            "order": "newest",
            "mode": "reschedule",
            "preemption_min_runtime": 30.0,
            "victim_scope": "project",
        }
