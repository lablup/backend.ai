from __future__ import annotations

from typing import override

import pytest

from ai.backend.agent.compute_backend.backend import ComputeBackend
from ai.backend.agent.compute_backend.instance import ComputeInstance
from ai.backend.agent.compute_backend.types import InstanceInfo, InstanceSpec


def test_backend_abc_cannot_be_instantiated() -> None:
    with pytest.raises(TypeError):
        ComputeBackend()  # type: ignore[abstract]


def test_instance_abc_cannot_be_instantiated() -> None:
    with pytest.raises(TypeError):
        ComputeInstance()  # type: ignore[abstract]


def test_incomplete_backend_subclass_cannot_be_instantiated() -> None:
    class Incomplete(ComputeBackend):
        @override
        async def create_instance(self, spec: InstanceSpec) -> ComputeInstance:
            raise NotImplementedError(spec)

    with pytest.raises(TypeError):
        Incomplete()  # type: ignore[abstract]


def test_incomplete_instance_subclass_cannot_be_instantiated() -> None:
    class Incomplete(ComputeInstance):
        @property
        @override
        def info(self) -> InstanceInfo:
            raise NotImplementedError

    with pytest.raises(TypeError):
        Incomplete()  # type: ignore[abstract]
