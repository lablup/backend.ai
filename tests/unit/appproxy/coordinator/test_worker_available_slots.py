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


def _make_port_worker(port_range: tuple[int, int]) -> Worker:
    return Worker.create(
        uuid.uuid4(),
        "worker-1",
        FrontendMode.PORT,
        ProxyProtocol.HTTP,
        "127.0.0.1",
        False,
        False,
        10200,
        [AppMode.INTERACTIVE],
        port_range=port_range,
    )


class TestRefreshAvailableSlots:
    """Regression tests for BA-6270: available_slots must track port_range on restart."""

    def test_expanding_port_range_increases_slots(self) -> None:
        worker = _make_port_worker((10501, 10600))
        assert worker.available_slots == 100

        worker.port_range = (10501, 10800)
        worker.refresh_available_slots()

        assert worker.available_slots == 300

    def test_shrinking_port_range_decreases_slots(self) -> None:
        worker = _make_port_worker((10501, 10800))
        assert worker.available_slots == 300

        worker.port_range = (10501, 10600)
        worker.refresh_available_slots()

        assert worker.available_slots == 100

    def test_switch_to_wildcard_mode_sets_unlimited(self) -> None:
        worker = _make_port_worker((10501, 10600))

        worker.frontend_mode = FrontendMode.WILDCARD_DOMAIN
        worker.port_range = None
        worker.wildcard_domain = "*.example.com"
        worker.refresh_available_slots()

        assert worker.available_slots == -1

    def test_refresh_without_port_range_raises(self) -> None:
        worker = _make_port_worker((10501, 10600))
        worker.port_range = None
        with pytest.raises(MissingFrontendConfigError):
            worker.refresh_available_slots()
