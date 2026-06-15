"""Regression tests for GQL revision input → draft merge (BA-6490)."""

from __future__ import annotations

from ai.backend.common.config import (
    ModelConfigDraft,
    ModelDefinitionDraft,
    ModelServiceConfigDraft,
)
from ai.backend.manager.api.gql.deployment.types.revision import (
    ModelConfigInputGQL,
    ModelDefinitionInputGQL,
    ModelHealthCheckInputGQL,
    ModelServiceConfigInputGQL,
)


def _variant_baseline_draft() -> ModelDefinitionDraft:
    return ModelDefinitionDraft(
        models=[
            ModelConfigDraft(
                name="vllm-model",
                model_path="/models",
                service=ModelServiceConfigDraft(port=8000),
            )
        ]
    )


def test_health_check_without_port_preserves_baseline_port() -> None:
    # Health check enabled, port omitted (materialized as explicit None by GQL).
    request_input = ModelDefinitionInputGQL(
        models=[
            ModelConfigInputGQL(
                service=ModelServiceConfigInputGQL(
                    health_check=ModelHealthCheckInputGQL(enable=True, initial_delay=1.0),
                ),
            )
        ]
    )

    request_draft = request_input.to_pydantic().to_draft()
    merged = _variant_baseline_draft().merge(request_draft)
    resolved = merged.to_resolved()

    service = resolved.models[0].service
    assert service is not None
    assert service.port == 8000
    assert service.health_check is not None
    assert service.health_check.enable is True
    assert service.health_check.initial_delay == 1.0


def test_explicit_port_overrides_baseline_port() -> None:
    request_input = ModelDefinitionInputGQL(
        models=[
            ModelConfigInputGQL(
                service=ModelServiceConfigInputGQL(
                    port=9000,
                    health_check=ModelHealthCheckInputGQL(enable=True),
                ),
            )
        ]
    )

    merged = _variant_baseline_draft().merge(request_input.to_pydantic().to_draft())
    resolved = merged.to_resolved()

    service = resolved.models[0].service
    assert service is not None
    assert service.port == 9000
