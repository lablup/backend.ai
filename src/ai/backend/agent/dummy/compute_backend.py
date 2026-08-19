"""In-memory ComputeBackend for tests and local development.

Fully satisfies the ComputeBackend/ComputeInstance ABCs without touching
Docker/Kubernetes, so it can back service-glue unit tests. State is deterministic
and held in memory, which doubles as this backend's ground truth for `recover`.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import override

from ai.backend.agent.compute_backend.backend import ComputeBackend
from ai.backend.agent.compute_backend.instance import ComputeInstance
from ai.backend.agent.compute_backend.types import (
    InstanceHandle,
    InstanceId,
    InstanceInfo,
    InstanceSpec,
    InstanceStat,
    InstanceState,
)
from ai.backend.agent.errors.backend import (
    InstanceAlreadyExistsError,
    InstanceNotFoundError,
)
from ai.backend.agent.stats import Measurement
from ai.backend.common.docker import LabelName

_DEFAULT_STATS: Mapping[str, Measurement] = {
    "cpu_util": Measurement(value=Decimal("0"), capacity=Decimal("100")),
    "mem": Measurement(value=Decimal("0"), capacity=Decimal("0")),
}


class DummyInstance(ComputeInstance):
    _info: InstanceInfo
    _stats_metrics: Mapping[str, Measurement]

    def __init__(self, info: InstanceInfo, stats_metrics: Mapping[str, Measurement]) -> None:
        self._info = info
        self._stats_metrics = stats_metrics

    @property
    @override
    def info(self) -> InstanceInfo:
        return self._info

    @override
    async def collect_stats(self) -> InstanceStat:
        return InstanceStat(
            instance_id=self._info.handle.instance_id,
            metrics=dict(self._stats_metrics),
        )


class DummyComputeBackend(ComputeBackend):
    _instances: dict[InstanceId, DummyInstance]
    _stats_metrics: Mapping[str, Measurement]

    def __init__(self, *, stats_metrics: Mapping[str, Measurement] | None = None) -> None:
        self._instances = {}
        self._stats_metrics = dict(stats_metrics) if stats_metrics is not None else _DEFAULT_STATS

    @override
    async def create_instance(self, spec: InstanceSpec) -> ComputeInstance:
        instance_id = InstanceId(f"dummy-{spec.kernel_id}")
        if instance_id in self._instances:
            raise InstanceAlreadyExistsError(f"instance {instance_id} already exists")
        info = InstanceInfo(
            handle=InstanceHandle(instance_id=instance_id, kernel_id=spec.kernel_id),
            state=InstanceState.RUNNING,
            image=spec.image,
            labels={**spec.labels, LabelName.KERNEL_ID: str(spec.kernel_id)},
        )
        instance = DummyInstance(info, self._stats_metrics)
        self._instances[instance_id] = instance
        return instance

    @override
    async def destroy_instance(self, instance_id: InstanceId) -> None:
        self._instances.pop(instance_id, None)

    @override
    async def load_instance(self, instance_id: InstanceId) -> ComputeInstance:
        try:
            return self._instances[instance_id]
        except KeyError:
            raise InstanceNotFoundError(f"instance {instance_id} not found") from None

    @override
    async def list_instances(self) -> Sequence[ComputeInstance]:
        return list(self._instances.values())

    @override
    async def recover(self) -> None:
        # Memory is this backend's ground truth; nothing external to reconcile.
        return None
