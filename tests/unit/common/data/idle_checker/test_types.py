from __future__ import annotations

import pytest
from pydantic import ValidationError

from ai.backend.common.data.idle_checker.types import (
    CheckerType,
    IdleCheckerSpec,
    NetworkTimeoutSpec,
    SessionLifetimeSpec,
    UtilizationSpec,
)


class TestIdleCheckerSpecValidation:
    def test_session_lifetime_with_matching_sub_spec_is_valid(self) -> None:
        spec = IdleCheckerSpec(
            type=CheckerType.SESSION_LIFETIME, session_lifetime=SessionLifetimeSpec()
        )
        assert spec.session_lifetime is not None
        assert spec.network is None
        assert spec.utilization is None

    def test_network_timeout_with_matching_sub_spec_is_valid(self) -> None:
        spec = IdleCheckerSpec(type=CheckerType.NETWORK_TIMEOUT, network=NetworkTimeoutSpec())
        assert spec.network is not None
        assert spec.session_lifetime is None
        assert spec.utilization is None

    def test_utilization_with_matching_sub_spec_is_valid(self) -> None:
        spec = IdleCheckerSpec(type=CheckerType.UTILIZATION, utilization=UtilizationSpec())
        assert spec.utilization is not None
        assert spec.session_lifetime is None
        assert spec.network is None

    def test_missing_sub_spec_raises(self) -> None:
        with pytest.raises(ValidationError):
            IdleCheckerSpec(type=CheckerType.NETWORK_TIMEOUT)

    def test_session_lifetime_with_wrong_sub_spec_raises(self) -> None:
        with pytest.raises(ValidationError):
            IdleCheckerSpec(
                type=CheckerType.SESSION_LIFETIME,
                session_lifetime=SessionLifetimeSpec(),
                network=NetworkTimeoutSpec(),
            )

    def test_utilization_with_cross_sub_spec_raises(self) -> None:
        with pytest.raises(ValidationError):
            IdleCheckerSpec(
                type=CheckerType.UTILIZATION,
                utilization=UtilizationSpec(),
                network=NetworkTimeoutSpec(),
            )


class TestIdleCheckerSpecJSONRoundTrip:
    """The JSONB column relies on ``model_dump(mode="json")`` / ``model_validate``."""

    def test_json_round_trip_preserves_type_and_sub_spec(self) -> None:
        original = IdleCheckerSpec(type=CheckerType.UTILIZATION, utilization=UtilizationSpec())

        dumped = original.model_dump(mode="json")
        assert dumped == {
            "type": CheckerType.UTILIZATION.value,
            "session_lifetime": None,
            "network": None,
            "utilization": {},
        }

        assert IdleCheckerSpec.model_validate(dumped) == original
