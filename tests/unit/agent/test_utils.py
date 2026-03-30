from __future__ import annotations

import tempfile
from typing import Any, cast

import pytest

from ai.backend.agent import utils


def test_read_sysfs() -> None:
    with tempfile.NamedTemporaryFile("w") as f:
        f.write("10")
        f.flush()
        int_val = utils.read_sysfs(f.name, int)
        assert isinstance(int_val, int)
        assert int_val == 10
        str_val = utils.read_sysfs(f.name, str)
        assert isinstance(str_val, str)
        assert str_val == "10"
        float_val = utils.read_sysfs(f.name, float)
        assert isinstance(float_val, float)
        assert float_val == 10.0

    with tempfile.NamedTemporaryFile("w") as f:
        f.write("1")
        f.flush()
        bool_val = utils.read_sysfs(f.name, bool)
        assert isinstance(bool_val, bool)
        assert bool_val is True
        f.seek(0, 0)
        f.write("0")
        f.flush()
        bool_val = utils.read_sysfs(f.name, bool)
        assert isinstance(bool_val, bool)
        assert bool_val is False

    default_val = utils.read_sysfs("/tmp/xxxxx-non-existent-file", int)
    assert isinstance(default_val, int)
    assert default_val == 0

    custom_default_val = utils.read_sysfs("/tmp/xxxxx-non-existent-file", int, -1)
    assert isinstance(custom_default_val, int)
    assert custom_default_val == -1

    with pytest.raises(TypeError):
        utils.read_sysfs("/tmp/xxxxx-non-existent-file", object)  # type: ignore[arg-type]

    with pytest.raises(TypeError):
        utils.read_sysfs("/tmp/xxxxx-non-existent-file", object, -1)  # type: ignore[arg-type]


def test_update_nested_dict() -> None:
    o1: dict[str, Any] = {
        "a": 1,
        "b": 2,
    }
    utils.update_nested_dict(o1, {"a": 3, "c": 4})
    assert o1 == {
        "a": 3,
        "b": 2,
        "c": 4,
    }

    o2: dict[str, Any] = {
        "a": {
            "x": 1,
        },
        "b": 2,
    }
    with pytest.raises(TypeError):
        utils.update_nested_dict(o2, {"a": 3})

    o3: dict[str, Any] = {
        "a": {
            "x": 1,
        },
        "b": 2,
    }
    utils.update_nested_dict(o3, {"a": {"x": 3, "y": 4}, "b": 5})
    assert cast(dict[str, Any], o3["a"]) == {
        "x": 3,
        "y": 4,
    }
    assert o3["b"] == 5

    o4: dict[str, Any] = {
        "a": [1, 2],
        "b": 3,
    }
    utils.update_nested_dict(o4, {"a": [4, 5], "b": 6})
    assert cast(list[Any], o4["a"]) == [1, 2, 4, 5]
    assert o4["b"] == 6
