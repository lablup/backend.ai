"""Verify the cross-enum legacy aliases for ModelDeploymentStatus and
EndpointLifecycle.

Historical ``deployment_history`` rows persist :class:`EndpointLifecycle`
values (lowercase ``destroying``/``destroyed``/``created``); current
readers materialise those rows through :class:`ModelDeploymentStatus`.
The two enums therefore each accept the other's name on lookup so a
single ``Enum(value)`` call resolves regardless of which form the row
carries.
"""

from __future__ import annotations

import pytest

from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.data.model_deployment.types import ModelDeploymentStatus


class TestModelDeploymentStatusLegacyAliases:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("destroying", ModelDeploymentStatus.STOPPING),
            ("DESTROYING", ModelDeploymentStatus.STOPPING),
            ("destroyed", ModelDeploymentStatus.STOPPED),
            ("DESTROYED", ModelDeploymentStatus.STOPPED),
            ("created", ModelDeploymentStatus.PENDING),
            ("CREATED", ModelDeploymentStatus.PENDING),
        ],
    )
    def test_lifecycle_value_resolves_to_v2_status(
        self, value: str, expected: ModelDeploymentStatus
    ) -> None:
        assert ModelDeploymentStatus(value) is expected

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("STOPPING", ModelDeploymentStatus.STOPPING),
            ("stopping", ModelDeploymentStatus.STOPPING),
            ("PENDING", ModelDeploymentStatus.PENDING),
            ("pending", ModelDeploymentStatus.PENDING),
            ("ready", ModelDeploymentStatus.READY),
        ],
    )
    def test_canonical_value_still_resolves(
        self, value: str, expected: ModelDeploymentStatus
    ) -> None:
        assert ModelDeploymentStatus(value) is expected


class TestEndpointLifecycleV2Aliases:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("STOPPING", EndpointLifecycle.DESTROYING),
            ("stopping", EndpointLifecycle.DESTROYING),
            ("STOPPED", EndpointLifecycle.DESTROYED),
            ("stopped", EndpointLifecycle.DESTROYED),
        ],
    )
    def test_v2_status_value_resolves_to_lifecycle(
        self, value: str, expected: EndpointLifecycle
    ) -> None:
        assert EndpointLifecycle(value) is expected

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("destroying", EndpointLifecycle.DESTROYING),
            ("destroyed", EndpointLifecycle.DESTROYED),
            ("pending", EndpointLifecycle.PENDING),
            ("ready", EndpointLifecycle.READY),
        ],
    )
    def test_canonical_lowercase_still_resolves(
        self, value: str, expected: EndpointLifecycle
    ) -> None:
        assert EndpointLifecycle(value) is expected
