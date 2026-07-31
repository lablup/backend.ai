from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from ai.backend.manager.api.gql.idle_checker.types import (
    IdleCheckerSpecInputGQL,
    NetworkTimeoutIdleCheckerSpecInputGQL,
    SessionLifetimeIdleCheckerSpecInputGQL,
    UtilizationIdleCheckerSpecInputGQL,
    UtilizationIdleCheckerThresholdInputGQL,
)


class TestIdleCheckerInputs:
    def test_session_lifetime_spec_converts_to_dto(self) -> None:
        input_ = IdleCheckerSpecInputGQL(
            session_lifetime=SessionLifetimeIdleCheckerSpecInputGQL(max_lifetime_seconds=3600)
        )

        dto = input_.to_pydantic()

        assert dto.session_lifetime is not None
        assert dto.session_lifetime.max_lifetime_seconds == 3600

    def test_network_spec_converts_to_dto(self) -> None:
        input_ = IdleCheckerSpecInputGQL(
            network=NetworkTimeoutIdleCheckerSpecInputGQL(max_network_inactivity_seconds=600)
        )

        dto = input_.to_pydantic()

        assert dto.network is not None
        assert dto.network.max_network_inactivity_seconds == 600

    def test_utilization_spec_converts_to_dto(self) -> None:
        preset_id = uuid4()
        input_ = IdleCheckerSpecInputGQL(
            utilization=UtilizationIdleCheckerSpecInputGQL(
                max_underutilized_duration_seconds=900,
                threshold=UtilizationIdleCheckerThresholdInputGQL(
                    preset_id=preset_id,
                    threshold=Decimal("0.25"),
                ),
            )
        )

        dto = input_.to_pydantic()

        assert dto.utilization is not None
        assert dto.utilization.max_underutilized_duration_seconds == 900
        assert dto.utilization.threshold.preset_id == preset_id
        assert dto.utilization.threshold.threshold == Decimal("0.25")
