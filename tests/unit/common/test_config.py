import pickle
from typing import Any

import tomli

from ai.backend.common.config import (
    ModelConfig,
    ModelDefinition,
    ModelHealthCheck,
    ModelMetadata,
    ModelServiceConfig,
    _merge_config,
    _merge_definition,
    _merge_metadata,
    _merge_service_config,
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


class TestMergeFieldCoverage:
    """Verify merge functions handle every declared field.

    When a field is added to a config model but the corresponding merge
    function is not updated, these tests will fail because the new field
    will be missing from the result's model_fields_set.
    """

    def test_merge_metadata(self) -> None:
        base = ModelMetadata.model_construct(
            _fields_set=set(ModelMetadata.model_fields),
            author="base",
            title="base",
            version="base",
            created="base",
            last_modified="base",
            description="base",
            task="base",
            category="base",
            architecture="base",
            framework=["base"],
            label=["base"],
            license="base",
            min_resource={"base": 1},
        )
        override = ModelMetadata.model_construct(_fields_set=set())
        result = _merge_metadata(base, override)
        missing = set(ModelMetadata.model_fields) - result.model_fields_set
        assert not missing, f"_merge_metadata() does not handle: {missing}"

    def test_merge_service_config(self) -> None:
        base = ModelServiceConfig.model_construct(
            _fields_set=set(ModelServiceConfig.model_fields),
            pre_start_actions=[],
            start_command="base-cmd",
            shell="/bin/base",
            port=9999,
            health_check=None,
        )
        override = ModelServiceConfig.model_construct(
            _fields_set=set(),
            pre_start_actions=[],
            start_command="",
            shell="",
            port=2,
            health_check=None,
        )
        result = _merge_service_config(base, override)
        missing = set(ModelServiceConfig.model_fields) - result.model_fields_set
        assert not missing, f"_merge_service_config() does not handle: {missing}"

    def test_merge_service_config_health_check_subfields(self) -> None:
        base_hc = ModelHealthCheck.model_construct(
            _fields_set=set(ModelHealthCheck.model_fields),
            interval=99.0,
            path="/base",
            max_retries=99,
            max_wait_time=99.0,
            expected_status_code=201,
            initial_delay=99.0,
        )
        override_hc = ModelHealthCheck.model_construct(
            _fields_set=set(),
            path="",
        )
        base = ModelServiceConfig.model_construct(
            _fields_set={"health_check"},
            start_command="",
            port=2,
            health_check=base_hc,
        )
        override = ModelServiceConfig.model_construct(
            _fields_set={"health_check"},
            start_command="",
            port=2,
            health_check=override_hc,
        )
        result = _merge_service_config(base, override)
        assert result.health_check is not None
        missing = set(ModelHealthCheck.model_fields) - result.health_check.model_fields_set
        assert not missing, f"health_check merge does not handle: {missing}"

    def test_merge_config(self) -> None:
        base = ModelConfig.model_construct(
            _fields_set=set(ModelConfig.model_fields),
            name="base",
            model_path="/base",
            service=None,
            metadata=None,
        )
        override = ModelConfig.model_construct(
            _fields_set=set(),
            name="",
            model_path="",
        )
        result = _merge_config(base, override)
        missing = set(ModelConfig.model_fields) - result.model_fields_set
        assert not missing, f"_merge_config() does not handle: {missing}"

    def test_merge_definition(self) -> None:
        base = ModelDefinition.model_construct(
            _fields_set=set(ModelDefinition.model_fields),
            models=[],
        )
        override = ModelDefinition.model_construct(_fields_set=set())
        result = _merge_definition(base, override)
        missing = set(ModelDefinition.model_fields) - result.model_fields_set
        assert not missing, f"_merge_definition() does not handle: {missing}"


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
