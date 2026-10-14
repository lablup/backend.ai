from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from typing import Any
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from ai.backend.agent.containerd.profile.base import KernelLaunch, LaunchPlan
from ai.backend.agent.containerd.profile.loader import load_runtime_profiles
from ai.backend.agent.errors.containerd import RuntimeProfileLoadError
from ai.backend.common.types import SlotName

from .conftest import FakeProfile

SCAN_TARGET = "ai.backend.agent.containerd.profile.loader.scan_entrypoints"


class FakeEntryPoint:
    name: str
    value: str
    _factory: Any
    _load_error: Exception | None

    def __init__(self, name: str, factory: Any, *, load_error: Exception | None = None) -> None:
        self.name = name
        self.value = f"fake.module:{name}"
        self._factory = factory
        self._load_error = load_error

    def load(self) -> Any:
        if self._load_error is not None:
            raise self._load_error
        return self._factory


class NoPlanProfile:
    name = "broken"

    def accepts(self, slots: Mapping[SlotName, Decimal]) -> bool:
        return True


@dataclass(frozen=True)
class DataclassProfile:
    name: str

    def accepts(self, slots: Mapping[SlotName, Decimal]) -> bool:
        return True

    def plan(self, kernel: KernelLaunch) -> LaunchPlan:
        raise NotImplementedError


def _factory_for(name: str) -> Any:
    return lambda options: FakeProfile(name, accepts=True)


class TestLoadRuntimeProfilesSuccess:
    def test_returns_profiles_in_config_order_regardless_of_scan_order(
        self, mocker: MockerFixture
    ) -> None:
        mocker.patch(
            SCAN_TARGET,
            return_value=[
                FakeEntryPoint("b", _factory_for("b")),
                FakeEntryPoint("a", _factory_for("a")),
            ],
        )

        profiles = load_runtime_profiles(["a", "b"], {})

        assert [p.name for p in profiles] == ["a", "b"]

    def test_options_table_is_passed_to_the_factory(self, mocker: MockerFixture) -> None:
        factory = MagicMock(side_effect=lambda options: FakeProfile("a", accepts=True))
        mocker.patch(SCAN_TARGET, return_value=[FakeEntryPoint("a", factory)])

        load_runtime_profiles(["a"], {"a": {"standin-image": "ref"}})

        factory.assert_called_once_with({"standin-image": "ref"})

    def test_missing_options_table_defaults_to_empty(self, mocker: MockerFixture) -> None:
        factory = MagicMock(side_effect=lambda options: FakeProfile("a", accepts=True))
        mocker.patch(SCAN_TARGET, return_value=[FakeEntryPoint("a", factory)])

        load_runtime_profiles(["a"], {})

        factory.assert_called_once_with({})

    def test_profile_with_a_plain_name_attribute_loads(self, mocker: MockerFixture) -> None:
        mocker.patch(
            SCAN_TARGET,
            return_value=[FakeEntryPoint("a", lambda options: DataclassProfile("a"))],
        )

        profiles = load_runtime_profiles(["a"], {})

        assert [p.name for p in profiles] == ["a"]


class TestLoadRuntimeProfilesException:
    def test_name_not_installed(self, mocker: MockerFixture) -> None:
        mocker.patch(SCAN_TARGET, return_value=[])

        with pytest.raises(RuntimeProfileLoadError, match="'coco-tdx' is not installed"):
            load_runtime_profiles(["coco-tdx"], {})

    def test_runc_must_not_be_listed(self, mocker: MockerFixture) -> None:
        scan = mocker.patch(SCAN_TARGET)

        with pytest.raises(RuntimeProfileLoadError, match="built in"):
            load_runtime_profiles(["runc"], {})

        scan.assert_not_called()

    def test_name_listed_twice(self, mocker: MockerFixture) -> None:
        scan = mocker.patch(SCAN_TARGET)

        with pytest.raises(RuntimeProfileLoadError, match="listed twice"):
            load_runtime_profiles(["a", "a"], {})

        scan.assert_not_called()

    def test_load_failure_is_chained(self, mocker: MockerFixture) -> None:
        cause = ImportError("no module")
        mocker.patch(
            SCAN_TARGET,
            return_value=[FakeEntryPoint("a", None, load_error=cause)],
        )

        with pytest.raises(RuntimeProfileLoadError, match="failed to load") as exc_info:
            load_runtime_profiles(["a"], {})

        assert exc_info.value.__cause__ is cause

    def test_factory_failure(self, mocker: MockerFixture) -> None:
        def factory(options: Mapping[str, Any]) -> FakeProfile:
            raise ValueError("bad options")

        mocker.patch(SCAN_TARGET, return_value=[FakeEntryPoint("a", factory)])

        with pytest.raises(RuntimeProfileLoadError, match="bad options"):
            load_runtime_profiles(["a"], {})

    def test_factory_returns_an_object_without_plan(self, mocker: MockerFixture) -> None:
        mocker.patch(
            SCAN_TARGET,
            return_value=[FakeEntryPoint("broken", lambda options: NoPlanProfile())],
        )

        with pytest.raises(RuntimeProfileLoadError, match="does not implement RuntimeProfile"):
            load_runtime_profiles(["broken"], {})

    def test_profile_name_differs_from_entry_point_name(self, mocker: MockerFixture) -> None:
        mocker.patch(
            SCAN_TARGET,
            return_value=[FakeEntryPoint("a", lambda options: FakeProfile("other", accepts=True))],
        )

        with pytest.raises(RuntimeProfileLoadError, match="reports the name 'other'"):
            load_runtime_profiles(["a"], {})

    def test_scanner_runtime_error(self, mocker: MockerFixture) -> None:
        mocker.patch(SCAN_TARGET, side_effect=RuntimeError("duplicate registration"))

        with pytest.raises(RuntimeProfileLoadError, match="duplicate registration"):
            load_runtime_profiles(["a"], {})


class TestLoadRuntimeProfilesEdge:
    def test_empty_names_skip_the_scan(self, mocker: MockerFixture) -> None:
        scan = mocker.patch(SCAN_TARGET)

        assert load_runtime_profiles([], {}) == []
        scan.assert_not_called()

    def test_options_for_an_unlisted_profile_are_ignored(self, mocker: MockerFixture) -> None:
        factory = MagicMock(side_effect=lambda options: FakeProfile("a", accepts=True))
        mocker.patch(SCAN_TARGET, return_value=[FakeEntryPoint("a", factory)])

        load_runtime_profiles(["a"], {"a": {"k": 1}, "other": {"k": 2}})

        factory.assert_called_once_with({"k": 1})
