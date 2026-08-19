from __future__ import annotations

import uuid
from collections.abc import Mapping
from decimal import Decimal

import pytest

from ai.backend.agent.compute_backend.types import (
    InstanceId,
    InstanceSpec,
    InstanceState,
)
from ai.backend.agent.dummy.compute_backend import DummyComputeBackend
from ai.backend.agent.errors.backend import (
    InstanceAlreadyExistsError,
    InstanceNotFoundError,
)
from ai.backend.agent.stats import Measurement
from ai.backend.common.docker import LabelName
from ai.backend.common.types import KernelId


def _make_spec(labels: Mapping[str, str] | None = None) -> InstanceSpec:
    return InstanceSpec(
        kernel_id=KernelId(uuid.uuid4()),
        image="registry.example.com/base:latest",
        labels=dict(labels or {}),
    )


async def test_create_returns_instance_stamped_with_kernel_id() -> None:
    backend = DummyComputeBackend()
    spec = _make_spec()

    instance = await backend.create_instance(spec)

    info = instance.info
    assert info.handle.kernel_id == spec.kernel_id
    assert info.handle.instance_id == InstanceId(f"dummy-{spec.kernel_id}")
    assert info.state == InstanceState.RUNNING
    assert info.image == spec.image
    assert info.labels[LabelName.KERNEL_ID] == str(spec.kernel_id)


async def test_create_preserves_caller_labels() -> None:
    backend = DummyComputeBackend()
    spec = _make_spec(labels={"ai.backend.session-id": "abc"})

    instance = await backend.create_instance(spec)

    assert instance.info.labels["ai.backend.session-id"] == "abc"


async def test_create_twice_for_same_kernel_raises() -> None:
    backend = DummyComputeBackend()
    spec = _make_spec()
    await backend.create_instance(spec)

    with pytest.raises(InstanceAlreadyExistsError):
        await backend.create_instance(spec)


async def test_create_after_destroy_succeeds() -> None:
    backend = DummyComputeBackend()
    spec = _make_spec()
    instance = await backend.create_instance(spec)

    await backend.destroy_instance(instance.info.handle.instance_id)
    recreated = await backend.create_instance(spec)

    assert recreated.info.handle.kernel_id == spec.kernel_id


async def test_load_returns_created_instance() -> None:
    backend = DummyComputeBackend()
    spec = _make_spec()
    created = await backend.create_instance(spec)

    loaded = await backend.load_instance(created.info.handle.instance_id)

    assert loaded.info.handle.kernel_id == spec.kernel_id


async def test_load_missing_instance_raises() -> None:
    backend = DummyComputeBackend()

    with pytest.raises(InstanceNotFoundError):
        await backend.load_instance(InstanceId("does-not-exist"))


async def test_list_instances_returns_current_instances() -> None:
    backend = DummyComputeBackend()
    spec = _make_spec()
    created = await backend.create_instance(spec)

    listed = await backend.list_instances()

    assert len(listed) == 1
    assert listed[0].info.handle.instance_id == created.info.handle.instance_id
    assert listed[0].info.labels[LabelName.KERNEL_ID] == str(spec.kernel_id)


async def test_destroy_removes_instance_and_is_idempotent() -> None:
    backend = DummyComputeBackend()
    created = await backend.create_instance(_make_spec())
    instance_id = created.info.handle.instance_id

    await backend.destroy_instance(instance_id)
    await backend.destroy_instance(instance_id)

    assert await backend.list_instances() == []
    with pytest.raises(InstanceNotFoundError):
        await backend.load_instance(instance_id)


async def test_recover_preserves_tracked_instances() -> None:
    backend = DummyComputeBackend()
    created = await backend.create_instance(_make_spec())

    await backend.recover()

    listed = await backend.list_instances()
    assert [i.info.handle.instance_id for i in listed] == [created.info.handle.instance_id]


async def test_collect_stats_on_instance() -> None:
    metrics = {"cpu_util": Measurement(value=Decimal("42"), capacity=Decimal("100"))}
    backend = DummyComputeBackend(stats_metrics=metrics)
    instance = await backend.create_instance(_make_spec())

    stat = await instance.collect_stats()

    assert stat.instance_id == instance.info.handle.instance_id
    assert stat.metrics["cpu_util"].value == Decimal("42")


async def test_create_load_destroy_roundtrip_as_service_backend() -> None:
    backend = DummyComputeBackend()
    spec = _make_spec()

    instance = await backend.create_instance(spec)
    instance_id = instance.info.handle.instance_id
    assert (await backend.load_instance(instance_id)).info.state == InstanceState.RUNNING

    await backend.destroy_instance(instance_id)
    with pytest.raises(InstanceNotFoundError):
        await backend.load_instance(instance_id)
