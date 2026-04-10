"""Tests for InternalDataRule."""

from __future__ import annotations

from typing import Any, cast
from unittest.mock import MagicMock
from uuid import UUID

import pytest

from ai.backend.common.types import AccessKey, ClusterMode, KernelEnqueueingConfig, SessionTypes
from ai.backend.manager.repositories.scheduler.types.session_creation import (
    ContainerUserInfo,
    ScalingGroupNetworkInfo,
    SessionCreationContext,
    SessionCreationSpec,
)
from ai.backend.manager.sokovan.scheduling_controller.preparers.internal_data import (
    InternalDataRule,
)
from ai.backend.manager.types import UserScope


@pytest.fixture
def internal_data_rule() -> InternalDataRule:
    return InternalDataRule()


@pytest.fixture
def test_user_scope() -> UserScope:
    return UserScope(
        domain_name="test-domain",
        group_id=UUID("00000000-0000-0000-0000-000000000001"),
        user_uuid=UUID("00000000-0000-0000-0000-000000000002"),
        user_role="user",
    )


@pytest.fixture
def basic_context() -> SessionCreationContext:
    return SessionCreationContext(
        scaling_group_network=ScalingGroupNetworkInfo(
            use_host_network=False,
            wsproxy_addr=None,
        ),
        allowed_scaling_groups=[],
        image_infos={},
        vfolder_mounts=[],
        dotfile_data={},
        container_user_info=ContainerUserInfo(),
    )


def _make_spec(
    user_scope: UserScope,
    creation_spec: dict[str, Any],
    internal_data: dict[str, Any] | None = None,
) -> SessionCreationSpec:
    return SessionCreationSpec(
        session_creation_id="test-001",
        session_name="test-session",
        access_key=AccessKey("test-key"),
        user_scope=user_scope,
        session_type=SessionTypes.INFERENCE,
        cluster_mode=ClusterMode.SINGLE_NODE,
        cluster_size=1,
        priority=10,
        resource_policy={},
        kernel_specs=[
            cast(KernelEnqueueingConfig, {"image_ref": MagicMock(canonical="test-image")})
        ],
        creation_spec=creation_spec,
        internal_data=internal_data,
    )


class TestInternalDataRule:
    """Tests for InternalDataRule.prepare()."""

    def test_model_definition_forwarded_to_internal_data(
        self,
        internal_data_rule: InternalDataRule,
        basic_context: SessionCreationContext,
        test_user_scope: UserScope,
    ) -> None:
        """Model definition from creation_spec should be forwarded to internal_data."""
        model_definition = {
            "models": [
                {
                    "name": "vllm-model",
                    "model_path": "/models",
                    "service": {
                        "start_command": "vllm serve",
                        "port": 8000,
                        "health_check": {
                            "path": "/health",
                            "initial_delay": 300,
                            "max_retries": 30,
                            "max_wait_time": 20,
                        },
                    },
                }
            ]
        }
        spec = _make_spec(
            test_user_scope,
            creation_spec={
                "model_definition_path": "model-definition.yaml",
                "model_definition": model_definition,
                "runtime_variant": "vllm",
            },
        )
        preparation_data: dict[str, Any] = {}

        internal_data_rule.prepare(spec, basic_context, preparation_data)

        result = preparation_data["internal_data"]
        assert result["model_definition"] == model_definition
        assert result["model_definition_path"] == "model-definition.yaml"
        assert result["runtime_variant"] == "vllm"

    def test_model_definition_absent_when_not_in_creation_spec(
        self,
        internal_data_rule: InternalDataRule,
        basic_context: SessionCreationContext,
        test_user_scope: UserScope,
    ) -> None:
        """When creation_spec has no model_definition, internal_data should not contain it."""
        spec = _make_spec(
            test_user_scope,
            creation_spec={
                "model_definition_path": "model-definition.yaml",
                "runtime_variant": "vllm",
            },
        )
        preparation_data: dict[str, Any] = {}

        internal_data_rule.prepare(spec, basic_context, preparation_data)

        result = preparation_data["internal_data"]
        assert "model_definition" not in result
        assert result["model_definition_path"] == "model-definition.yaml"

    def test_model_definition_none_not_forwarded(
        self,
        internal_data_rule: InternalDataRule,
        basic_context: SessionCreationContext,
        test_user_scope: UserScope,
    ) -> None:
        """When model_definition is None, it should not be forwarded."""
        spec = _make_spec(
            test_user_scope,
            creation_spec={
                "model_definition": None,
                "runtime_variant": "vllm",
            },
        )
        preparation_data: dict[str, Any] = {}

        internal_data_rule.prepare(spec, basic_context, preparation_data)

        result = preparation_data["internal_data"]
        assert "model_definition" not in result

    def test_existing_internal_data_preserved(
        self,
        internal_data_rule: InternalDataRule,
        basic_context: SessionCreationContext,
        test_user_scope: UserScope,
    ) -> None:
        """Pre-existing internal_data fields should be preserved."""
        model_definition = {"models": [{"name": "test", "model_path": "/models"}]}
        spec = _make_spec(
            test_user_scope,
            creation_spec={
                "model_definition": model_definition,
                "runtime_variant": "vllm",
            },
            internal_data={"existing_key": "existing_value"},
        )
        preparation_data: dict[str, Any] = {}

        internal_data_rule.prepare(spec, basic_context, preparation_data)

        result = preparation_data["internal_data"]
        assert result["existing_key"] == "existing_value"
        assert result["model_definition"] == model_definition
