from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import NamedTuple

import pytest

from ai.backend.appproxy.common.types import AppMode, FrontendMode, ProxyProtocol
from ai.backend.appproxy.coordinator.errors import MissingFrontendConfigError
from ai.backend.appproxy.coordinator.models.worker import Worker


class PortRange(NamedTuple):
    start: int
    end: int


@dataclass(frozen=True)
class RangeChangeCase:
    """A restart that changes a worker's port_range and the slot count it should yield."""

    initial: PortRange
    updated: PortRange
    expected_available_slots: int


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


class TestCreate:
    def test_create_initializes_available_slots(self) -> None:
        worker = make_port_worker(PortRange(start=10501, end=10600))
        assert worker.available_slots == 100


class TestRefreshAvailableSlots:
    """Regression tests: available_slots must track the frontend config on restart."""

    @pytest.mark.parametrize(
        "case",
        [
            RangeChangeCase(
                initial=PortRange(start=10501, end=10600),
                updated=PortRange(start=10501, end=10800),
                expected_available_slots=300,
            ),
            RangeChangeCase(
                initial=PortRange(start=10501, end=10800),
                updated=PortRange(start=10501, end=10600),
                expected_available_slots=100,
            ),
            RangeChangeCase(
                initial=PortRange(start=10501, end=10600),
                updated=PortRange(start=10501, end=10600),
                expected_available_slots=100,
            ),
            RangeChangeCase(
                initial=PortRange(start=10501, end=10501),
                updated=PortRange(start=10501, end=10501),
                expected_available_slots=1,
            ),
        ],
        ids=["expand", "shrink", "unchanged", "single-port"],
    )
    def test_refresh_after_port_range_change(self, case: RangeChangeCase) -> None:
        worker = make_port_worker(case.initial)
        worker.port_range = case.updated
        worker.refresh_available_slots()
        assert worker.available_slots == case.expected_available_slots

    @pytest.mark.parametrize("port_worker", [PortRange(start=10501, end=10600)], indirect=True)
    def test_switch_to_wildcard_mode_sets_unlimited(self, port_worker: Worker) -> None:
        port_worker.frontend_mode = FrontendMode.WILDCARD_DOMAIN
        port_worker.port_range = None
        port_worker.wildcard_domain = "*.example.com"
        port_worker.refresh_available_slots()
        assert port_worker.available_slots == -1

    @pytest.mark.parametrize("port_worker", [PortRange(start=10501, end=10600)], indirect=True)
    def test_refresh_without_port_range_raises(self, port_worker: Worker) -> None:
        port_worker.port_range = None
        with pytest.raises(MissingFrontendConfigError):
            port_worker.refresh_available_slots()

    @pytest.mark.parametrize("port_worker", [PortRange(start=10501, end=10600)], indirect=True)
    def test_refresh_without_wildcard_domain_raises(self, port_worker: Worker) -> None:
        port_worker.frontend_mode = FrontendMode.WILDCARD_DOMAIN
        port_worker.port_range = None
        port_worker.wildcard_domain = None
        with pytest.raises(MissingFrontendConfigError):
            port_worker.refresh_available_slots()
