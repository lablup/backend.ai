from __future__ import annotations

import uuid

from ai.backend.common.service_discovery.service_discovery import (
    ServiceEndpoint,
    ServiceMetadata,
)


def _manager_worker() -> ServiceMetadata:
    """One worker's registration. Its siblings share the listening socket."""
    return ServiceMetadata(
        display_name="manager-i-core1",
        service_group="manager",
        version="26.9.0a4",
        endpoint=ServiceEndpoint(
            address="10.0.0.1",
            port=8081,
            protocol="http",
            prometheus_address="10.0.0.1:18080",
        ),
    )


def test_workers_of_one_endpoint_register_under_one_id() -> None:
    ids = {_manager_worker().id for _ in range(4)}

    assert len(ids) == 1


def test_the_id_survives_a_restart() -> None:
    """A restart re-registers the same endpoint, so it must reuse the entry.

    A fresh id would leave the old one behind until the sweep clears it, and would
    restart every Prometheus series carrying it.
    """
    before = _manager_worker().id
    after = _manager_worker().id

    assert before == after


def test_a_different_endpoint_gets_a_different_id() -> None:
    other = ServiceMetadata(
        display_name="manager-i-core2",
        service_group="manager",
        version="26.9.0a4",
        endpoint=ServiceEndpoint(
            address="10.0.0.2",
            port=8081,
            protocol="http",
            prometheus_address="10.0.0.2:18080",
        ),
    )

    assert other.id != _manager_worker().id


def test_a_different_group_on_one_address_stays_distinct() -> None:
    agent = ServiceMetadata(
        display_name="agent-cpu1",
        service_group="agent",
        version="26.9.0a4",
        endpoint=ServiceEndpoint(
            address="10.0.0.1",
            port=8081,
            protocol="http",
            prometheus_address="10.0.0.1:18080",
        ),
    )

    assert agent.id != _manager_worker().id


def test_an_explicit_id_is_left_alone() -> None:
    given = uuid.uuid4()

    meta = ServiceMetadata(
        id=given,
        display_name="route",
        service_group="model-service",
        version="1.0",
        endpoint=ServiceEndpoint(
            address="10.0.0.9",
            port=9000,
            protocol="http",
            prometheus_address="10.0.0.9:9000",
        ),
    )

    assert meta.id == given
