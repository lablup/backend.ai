from __future__ import annotations

import uuid
from typing import NamedTuple

import pytest

from ai.backend.appproxy.common.types import AppMode, FrontendMode, ProxyProtocol
from ai.backend.appproxy.coordinator.errors import MissingFrontendConfigError
from ai.backend.appproxy.coordinator.models.worker import Worker


class PortRange(NamedTuple):
    start: int
    end: int


class RangeChangeCase(NamedTuple):
    """A restart that changes a worker's port_range and the slot count it should yield."""

    initial: PortRange
    updated: PortRange
    expected_slots: int


def make_port_worker(port_range: PortRange) -> Worker:
    """A PORT-mode worker created with the given port_range."""
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


@pytest.fixture
def port_worker(request: pytest.FixtureRequest) -> Worker:
    """A PORT-mode worker created with the port_range given via indirect param."""
    return make_port_worker(request.param)


class TestCalculateAvailableSlots:
    @pytest.mark.parametrize(
        ("port_range", "expected"),
        [
            (PortRange(10501, 10800), 300),
            (PortRange(10501, 10600), 100),
            (PortRange(10501, 10501), 1),
        ],
    )
    def test_port_mode_span(self, port_range: PortRange, expected: int) -> None:
        assert (
            Worker._calculate_available_slots(FrontendMode.PORT, port_range=port_range) == expected
        )

    def test_wildcard_mode_is_unlimited(self) -> None:
        assert (
            Worker._calculate_available_slots(
                FrontendMode.WILDCARD_DOMAIN, wildcard_domain="*.example.com"
            )
            == -1
        )

    @pytest.mark.parametrize(
        "frontend_mode",
        [FrontendMode.PORT, FrontendMode.WILDCARD_DOMAIN],
    )
    def test_missing_config_raises(self, frontend_mode: FrontendMode) -> None:
        # PORT without port_range / WILDCARD_DOMAIN without wildcard_domain.
        with pytest.raises(MissingFrontendConfigError):
            Worker._calculate_available_slots(frontend_mode)


class TestRefreshAvailableSlots:
    """Regression tests: available_slots must track port_range on restart."""

    @pytest.mark.parametrize(
        "case",
        [
            RangeChangeCase(PortRange(10501, 10600), PortRange(10501, 10800), 300),
            RangeChangeCase(PortRange(10501, 10800), PortRange(10501, 10600), 100),
            RangeChangeCase(PortRange(10501, 10600), PortRange(10501, 10600), 100),
        ],
        ids=["expand", "shrink", "unchanged"],
    )
    def test_refresh_after_port_range_change(self, case: RangeChangeCase) -> None:
        worker = make_port_worker(case.initial)
        worker.port_range = case.updated
        worker.refresh_available_slots()
        assert worker.available_slots == case.expected_slots

    @pytest.mark.parametrize("port_worker", [PortRange(10501, 10600)], indirect=True)
    def test_switch_to_wildcard_mode_sets_unlimited(self, port_worker: Worker) -> None:
        port_worker.frontend_mode = FrontendMode.WILDCARD_DOMAIN
        port_worker.port_range = None
        port_worker.wildcard_domain = "*.example.com"
        port_worker.refresh_available_slots()
        assert port_worker.available_slots == -1

    @pytest.mark.parametrize("port_worker", [PortRange(10501, 10600)], indirect=True)
    def test_refresh_without_port_range_raises(self, port_worker: Worker) -> None:
        port_worker.port_range = None
        with pytest.raises(MissingFrontendConfigError):
            port_worker.refresh_available_slots()
