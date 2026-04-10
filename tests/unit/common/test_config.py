import pickle
from typing import Any

import tomli

from ai.backend.common.config import (
    ModelConfig,
    ModelDefinition,
    ModelServiceConfig,
    merge,
    override_key,
)


def test_override_key() -> None:
    sample: dict[str, Any] = {
        "a": {
            "b": 0,
        },
        "c": 1,
    }
    override_key(sample, ("a", "b"), -1)
    assert sample["a"]["b"] == -1
    assert sample["c"] == 1

    sample = {
        "a": {
            "b": 0,
        },
        "c": 1,
    }
    override_key(sample, ("c",), -1)
    assert sample["a"]["b"] == 0
    assert sample["c"] == -1


def test_merge() -> None:
    left = {
        "a": {
            "a": 5,
            "b": 0,
        },
        "c": 1,
    }
    right = {
        "a": {
            "b": 2,
            "c": 3,
        },
        "x": 10,
    }
    result = merge(left, right)
    assert result == {
        "a": {
            "a": 5,
            "b": 2,
            "c": 3,
        },
        "c": 1,
        "x": 10,
    }


def _make_model_definition(
    start_command: list[str],
    pre_start_actions: list[dict[str, Any]] | None = None,
) -> ModelDefinition:
    service_kwargs: dict[str, Any] = {
        "start_command": start_command,
        "port": 8080,
    }
    if pre_start_actions is not None:
        service_kwargs["pre_start_actions"] = pre_start_actions
    return ModelDefinition(
        models=[
            ModelConfig(
                name="test-model",
                model_path="/models",
                service=ModelServiceConfig(**service_kwargs),
            )
        ]
    )


def test_model_definition_merge_replaces_start_command_wholesale() -> None:
    """Atomic list fields like start_command must be replaced wholesale.

    Regression test for index-based list merging that left tail elements
    from the base when the override provided a shorter list.
    """
    base = _make_model_definition(
        start_command=[
            "python3",
            "-m",
            "vllm.entrypoints.openai.api_server",
            "--model",
            "/models",
            "--served-model-name",
            "test",
            "--host",
            "0.0.0.0",
            "--port",
            "8080",
        ],
    )
    override = _make_model_definition(
        start_command=["python3", "-m", "http.server", "8080"],
    )

    merged = base.merge(override)

    assert merged.models[0].service is not None
    assert merged.models[0].service.start_command == [
        "python3",
        "-m",
        "http.server",
        "8080",
    ]


def test_model_definition_merge_replaces_pre_start_actions_wholesale() -> None:
    """Atomic list fields like pre_start_actions must be replaced wholesale."""
    base = _make_model_definition(
        start_command=["python3", "app.py"],
        pre_start_actions=[
            {"action": "run_command", "args": {"command": ["echo", "base-1"]}},
            {"action": "run_command", "args": {"command": ["echo", "base-2"]}},
            {"action": "run_command", "args": {"command": ["echo", "base-3"]}},
        ],
    )
    override = _make_model_definition(
        start_command=["python3", "app.py"],
        pre_start_actions=[
            {"action": "run_command", "args": {"command": ["echo", "override"]}},
        ],
    )

    merged = base.merge(override)

    assert merged.models[0].service is not None
    assert len(merged.models[0].service.pre_start_actions) == 1


def test_sanitize_inline_dicts() -> None:
    sample = """
    [section]
    a = { x = 1, y = 1 }
    b = { x = 1, y = { t = 2, u = 2 } }
    """

    result = tomli.loads(sample)
    assert isinstance(result["section"]["a"], dict)
    assert isinstance(result["section"]["b"], dict)
    assert isinstance(result["section"]["b"]["y"], dict)

    # Also ensure the result is picklable.
    data = pickle.dumps(result)
    result = pickle.loads(data)
    assert result == {
        "section": {
            "a": {"x": 1, "y": 1},
            "b": {"x": 1, "y": {"t": 2, "u": 2}},
        },
    }
