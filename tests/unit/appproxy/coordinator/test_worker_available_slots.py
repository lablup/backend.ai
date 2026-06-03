from __future__ import annotations

import uuid

import pytest

from ai.backend.appproxy.common.types import AppMode, FrontendMode, ProxyProtocol
from ai.backend.appproxy.coordinator.errors import MissingFrontendConfigError
from ai.backend.appproxy.coordinator.models.worker import Worker


class TestCalculateAvailableSlots:
    def test_port_mode_uses_port_range_span(self) -> None:
        # span is inclusive on both ends: 10501..10800 -> 300 slots
        assert Worker.calculate_available_slots(FrontendMode.PORT, port_range=(10501, 10800)) == 300

    def test_port_mode_recomputes_when_range_changes(self) -> None:
        # BA-6270: a restart with a different port_range must yield a new slot count
        # instead of staying pinned to the value from the first registration.
        initial = Worker.calculate_available_slots(FrontendMode.PORT, port_range=(10501, 10600))
        expanded = Worker.calculate_available_slots(FrontendMode.PORT, port_range=(10501, 10800))
        assert initial == 100
        assert expanded == 300

    def test_wildcard_mode_is_unlimited(self) -> None:
        assert (
            Worker.calculate_available_slots(
                FrontendMode.WILDCARD_DOMAIN, wildcard_domain="*.example.com"
            )
            == -1
        )

    def test_port_mode_without_range_raises(self) -> None:
        with pytest.raises(MissingFrontendConfigError):
            Worker.calculate_available_slots(FrontendMode.PORT)

    def test_wildcard_mode_without_domain_raises(self) -> None:
        with pytest.raises(MissingFrontendConfigError):
            Worker.calculate_available_slots(FrontendMode.WILDCARD_DOMAIN)

    def test_create_uses_calculated_slots(self) -> None:
        worker = Worker.create(
            uuid.uuid4(),
            "worker-1",
            FrontendMode.PORT,
            ProxyProtocol.HTTP,
            "127.0.0.1",
            False,
            False,
            10200,
            [AppMode.INTERACTIVE],
            port_range=(10501, 10800),
        )
        assert worker.available_slots == 300
