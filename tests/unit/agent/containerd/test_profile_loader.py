from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from ai.backend.agent.containerd.profile.base import LaunchPlan
from ai.backend.agent.containerd.profile.loader import load_runtime_profile
from ai.backend.agent.containerd.profile.runc import RuncProfile
from ai.backend.agent.errors.containerd import RuntimeProfileLoadError
from ai.backend.common.types import KernelCreationConfig


class _Profile:
    def __init__(self, name: str, options: Mapping[str, Any]) -> None:
        self._name = name
        self.options = options

    @property
    def name(self) -> str:
        return self._name

    def plan(
        self, kernel_config: KernelCreationConfig, *, trusted_storage_path: Path | None = None
    ) -> LaunchPlan:
        return LaunchPlan("io.example.v1")


def _install(mocker: MockerFixture, name: str, factory: Callable[[Mapping[str, Any]], Any]) -> None:
    ep = MagicMock(value="pkg:factory")
    ep.name = name
    ep.load.return_value = factory
    mocker.patch("ai.backend.agent.containerd.profile.loader.scan_entrypoints", return_value=[ep])


def test_runc_is_built_in() -> None:
    assert isinstance(load_runtime_profile("runc", {}), RuncProfile)


def test_entry_point_receives_its_options_table(mocker: MockerFixture) -> None:
    _install(mocker, "x", lambda options: _Profile("x", options))

    profile = load_runtime_profile("x", {"x": {"k": 1}, "y": {"k": 2}})

    assert isinstance(profile, _Profile)
    assert profile.options == {"k": 1}


def test_unknown_profile_is_refused(mocker: MockerFixture) -> None:
    _install(mocker, "x", lambda options: _Profile("x", options))

    with pytest.raises(RuntimeProfileLoadError, match="'y' is not installed"):
        load_runtime_profile("y", {})


def test_failing_factory_is_refused(mocker: MockerFixture) -> None:
    def broken(options: Mapping[str, Any]) -> Any:
        raise ValueError("bad table")

    _install(mocker, "x", broken)

    with pytest.raises(RuntimeProfileLoadError, match="failed to load: bad table"):
        load_runtime_profile("x", {})


def test_profile_whose_name_raises_is_refused(mocker: MockerFixture) -> None:
    class _Broken:
        @property
        def name(self) -> str:
            raise RuntimeError("no name")

    _install(mocker, "x", lambda options: _Broken())

    with pytest.raises(RuntimeProfileLoadError, match="failed to load: no name"):
        load_runtime_profile("x", {})


@pytest.mark.parametrize("made", [lambda options: _Profile("other", options), lambda options: 1])
def test_object_that_is_not_the_named_profile_is_refused(
    mocker: MockerFixture, made: Callable[[Mapping[str, Any]], Any]
) -> None:
    _install(mocker, "x", made)

    with pytest.raises(RuntimeProfileLoadError, match="does not implement"):
        load_runtime_profile("x", {})
