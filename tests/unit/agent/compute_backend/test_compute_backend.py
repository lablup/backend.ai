from __future__ import annotations

import uuid
from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import override

import pytest

from ai.backend.agent.compute_backend.backend import ComputeBackend
from ai.backend.agent.compute_backend.types import (
    InstanceHandle,
    InstanceId,
    InstanceInfo,
    InstanceSpec,
    InstanceStat,
    InstanceState,
)
from ai.backend.agent.errors.backend import InstanceNotFoundError
from ai.backend.agent.stats import Measurement
from ai.backend.common.docker import LabelName
from ai.backend.common.types import KernelId


class FakeComputeBackend(ComputeBackend):
    _instances: dict[InstanceId, InstanceInfo]
    _counter: int

    def __init__(self) -> None:
        self._instances = {}
        self._counter = 0

    @override
    async def create_instance(self, spec: InstanceSpec) -> InstanceHandle:
        self._counter += 1
        instance_id = InstanceId(f"fake-{self._counter}")
        labels = {**spec.labels, LabelName.KERNEL_ID: str(spec.kernel_id)}
        handle = InstanceHandle(instance_id=instance_id, kernel_id=spec.kernel_id)
        self._instances[instance_id] = InstanceInfo(
            handle=handle,
            state=InstanceState.RUNNING,
            image=spec.image,
            labels=labels,
        )
        return handle

    @override
    async def destroy_instance(self, handle: InstanceHandle) -> None:
        self._instances.pop(handle.instance_id, None)

    @override
    async def inspect_instance(self, handle: InstanceHandle) -> InstanceInfo:
        try:
            return self._instances[handle.instance_id]
        except KeyError:
            raise InstanceNotFoundError(f"instance {handle.instance_id} not found") from None

    @override
    async def list_instances(self) -> Sequence[InstanceInfo]:
        return [
            self._from_labels(info.handle.instance_id, info) for info in self._instances.values()
        ]

    @override
    async def collect_stats(self, handle: InstanceHandle) -> InstanceStat:
        return InstanceStat(
            instance_id=handle.instance_id,
            metrics={"cpu_util": Measurement(value=Decimal("1"))},
        )

    @staticmethod
    def _from_labels(instance_id: InstanceId, info: InstanceInfo) -> InstanceInfo:
        labels = info.labels
        kernel_id = KernelId(uuid.UUID(labels[LabelName.KERNEL_ID]))
        return InstanceInfo(
            handle=InstanceHandle(instance_id=instance_id, kernel_id=kernel_id),
            state=info.state,
            image=info.image,
            labels=labels,
        )


def _make_spec(labels: Mapping[str, str] | None = None) -> InstanceSpec:
    return InstanceSpec(
        kernel_id=KernelId(uuid.uuid4()),
        image="registry.example.com/base:latest",
        labels=dict(labels or {}),
    )


def test_abc_cannot_be_instantiated() -> None:
    with pytest.raises(TypeError):
        ComputeBackend()  # type: ignore[abstract]


def test_incomplete_subclass_cannot_be_instantiated() -> None:
    class Incomplete(ComputeBackend):
        @override
        async def create_instance(self, spec: InstanceSpec) -> InstanceHandle:
            raise NotImplementedError(spec)

    with pytest.raises(TypeError):
        Incomplete()  # type: ignore[abstract]


async def test_create_stamps_kernel_id_and_returns_handle() -> None:
    backend = FakeComputeBackend()
    spec = _make_spec()

    handle = await backend.create_instance(spec)

    assert handle.kernel_id == spec.kernel_id
    info = await backend.inspect_instance(handle)
    assert info.labels[LabelName.KERNEL_ID] == str(spec.kernel_id)


async def test_list_instances_self_describes_from_labels() -> None:
    backend = FakeComputeBackend()
    spec = _make_spec()
    handle = await backend.create_instance(spec)

    listed = await backend.list_instances()

    assert len(listed) == 1
    assert listed[0].handle.kernel_id == spec.kernel_id
    assert listed[0].handle.instance_id == handle.instance_id


async def test_destroy_is_idempotent() -> None:
    backend = FakeComputeBackend()
    handle = await backend.create_instance(_make_spec())

    await backend.destroy_instance(handle)
    await backend.destroy_instance(handle)

    assert await backend.list_instances() == []


async def test_inspect_missing_instance_raises() -> None:
    backend = FakeComputeBackend()
    handle = InstanceHandle(
        instance_id=InstanceId("does-not-exist"),
        kernel_id=KernelId(uuid.uuid4()),
    )

    with pytest.raises(InstanceNotFoundError):
        await backend.inspect_instance(handle)


async def test_collect_stats_returns_measurements() -> None:
    backend = FakeComputeBackend()
    handle = await backend.create_instance(_make_spec())

    stat = await backend.collect_stats(handle)

    assert stat.instance_id == handle.instance_id
    assert "cpu_util" in stat.metrics
