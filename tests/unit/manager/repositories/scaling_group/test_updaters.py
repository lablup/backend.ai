from datetime import timedelta

import pytest

from ai.backend.common.types import PreemptionMode, PreemptionOrder
from ai.backend.manager.data.scaling_group.types import PreemptionConfig
from ai.backend.manager.repositories.scaling_group.updaters import (
    ScalingGroupSchedulerConfigUpdaterSpec,
)
from ai.backend.manager.types import OptionalState


@pytest.fixture
def preemption_config() -> PreemptionConfig:
    return PreemptionConfig(
        enabled=True,
        preemptible_priority=3,
        order=PreemptionOrder.NEWEST,
        mode=PreemptionMode.RESCHEDULE,
        preemption_min_runtime=timedelta(seconds=30),
    )


class TestSchedulerConfigUpdater:
    def test_preemption_is_bound_as_a_mapping_not_a_json_string(
        self, preemption_config: PreemptionConfig
    ) -> None:
        spec = ScalingGroupSchedulerConfigUpdaterSpec(
            preemption_config=OptionalState.update(preemption_config)
        )

        _column, _path, new_value = spec.build_values()["scheduler_opts"].clauses

        assert new_value.clause.value == {
            "enabled": True,
            "preemptible_priority": 3,
            "order": "newest",
            "mode": "reschedule",
            "preemption_min_runtime": 30.0,
        }
