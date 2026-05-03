import pickle
from typing import Any

import pytest
import tomli

from ai.backend.common.config import (
    ModelConfig,
    ModelDefinition,
    ModelDefinitionDraft,
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
            start_command=["base-cmd"],
            shell="/bin/base",
            port=9999,
            health_check=None,
        )
        override = ModelServiceConfig.model_construct(
            _fields_set=set(),
            pre_start_actions=[],
            start_command=[],
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
            start_command=[],
            port=2,
            health_check=base_hc,
        )
        override = ModelServiceConfig.model_construct(
            _fields_set={"health_check"},
            start_command=[],
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


class TestModelConfigs:
    def test_sanitize_inline_dicts(self) -> None:
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

    @pytest.fixture
    def model_definition_draft_with_minimal_service(self) -> ModelDefinitionDraft:
        return ModelDefinitionDraft.model_validate({
            "models": [
                {
                    "name": "demo",
                    "model_path": "/models/demo",
                    "service": {
                        "port": 8000,
                    },
                }
            ]
        })

    def test_model_service_config_draft_allows_missing_start_command(
        self, model_definition_draft_with_minimal_service: ModelDefinitionDraft
    ) -> None:
        model_definition = model_definition_draft_with_minimal_service
        resolved = model_definition.to_resolved()

        service = resolved.models[0].service
        assert service is not None
        assert service.start_command is None
        assert service.port == 8000

    def test_model_service_config_draft_rejects_string_start_command(self) -> None:
        with pytest.raises(ValueError):
            ModelDefinitionDraft.model_validate({
                "models": [
                    {
                        "name": "demo",
                        "model_path": "/models/demo",
                        "service": {
                            "start_command": "python serve.py",
                            "port": 8000,
                        },
                    }
                ]
            })

    def test_to_resolved_substitutes_model_path_placeholder(self) -> None:
        # The variant baseline keeps ``{model_path}`` so a single fixture
        # entry covers any mount destination; the placeholder is resolved
        # once, at the boundary between draft merge and persistence.
        draft = ModelDefinitionDraft.model_validate({
            "models": [
                {
                    "name": "demo",
                    "model_path": "/custom-mount",
                    "service": {
                        "start_command": ["vllm", "serve", "{model_path}"],
                        "port": 8000,
                    },
                }
            ]
        })

        resolved = draft.to_resolved()

        service = resolved.models[0].service
        assert service is not None
        assert service.start_command == ["vllm", "serve", "/custom-mount"]

    def test_to_resolved_substitutes_placeholder_with_named_flag(self) -> None:
        # SGLang-style: ``{model_path}`` lands after a flag; the
        # substitution touches the placeholder token only, not the flag.
        draft = ModelDefinitionDraft.model_validate({
            "models": [
                {
                    "name": "demo",
                    "model_path": "/data",
                    "service": {
                        "start_command": [
                            "python",
                            "-m",
                            "sglang.launch_server",
                            "--model-path",
                            "{model_path}",
                        ],
                        "port": 9001,
                    },
                }
            ]
        })

        resolved = draft.to_resolved()

        service = resolved.models[0].service
        assert service is not None
        assert service.start_command == [
            "python",
            "-m",
            "sglang.launch_server",
            "--model-path",
            "/data",
        ]

    def test_to_resolved_leaves_start_command_with_no_placeholder_unchanged(self) -> None:
        draft = ModelDefinitionDraft.model_validate({
            "models": [
                {
                    "name": "demo",
                    "model_path": "/models",
                    "service": {
                        "start_command": ["my-server", "--bind", "0.0.0.0"],
                        "port": 8000,
                    },
                }
            ]
        })

        resolved = draft.to_resolved()

        service = resolved.models[0].service
        assert service is not None
        assert service.start_command == ["my-server", "--bind", "0.0.0.0"]
