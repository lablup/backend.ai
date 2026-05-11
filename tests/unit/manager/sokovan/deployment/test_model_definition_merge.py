"""Verify that nullable v2 ``ModelDefinitionInput`` fields still result in
correct required-field enforcement after the revision merge chain.

This pins the BA-5983 behavior: the GraphQL/REST boundary accepts
all-optional fields, but ``to_resolved()`` at the persistence boundary
must still raise when no merge layer (request, preset, variant baseline)
supplies a required value.
"""

from __future__ import annotations

import functools

import pytest

from ai.backend.common.config import (
    ModelConfigDraft,
    ModelDefinitionDraft,
    ModelHealthCheckDraft,
    ModelServiceConfigDraft,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    ModelConfigInput,
    ModelDefinitionInput,
    ModelHealthCheckInput,
    ModelServiceConfigInput,
)
from ai.backend.manager.data.deployment.types import RevisionDraft


def _merge(*drafts: RevisionDraft) -> RevisionDraft:
    return functools.reduce(RevisionDraft.merge, drafts, RevisionDraft())


class TestModelDefinitionInputToDraft:
    """``ModelDefinitionInput.to_draft`` is the bridge between the
    all-optional DTO and the merge-chain draft. The conversion itself
    must never raise — required-field enforcement is deferred to
    ``to_resolved()`` after the merge."""

    def test_empty_input_yields_empty_draft(self) -> None:
        draft = ModelDefinitionInput().to_draft()
        assert isinstance(draft, ModelDefinitionDraft)
        assert draft.models is None

    def test_partial_input_preserves_nones(self) -> None:
        draft = ModelDefinitionInput(
            models=[ModelConfigInput(name="only-name")],
        ).to_draft()
        assert draft.models is not None
        assert draft.models[0].name == "only-name"
        assert draft.models[0].model_path is None

    def test_nested_service_input_round_trips(self) -> None:
        draft = ModelDefinitionInput(
            models=[
                ModelConfigInput(
                    name="m",
                    service=ModelServiceConfigInput(
                        port=8080,
                        health_check=ModelHealthCheckInput(path="/healthz"),
                    ),
                )
            ]
        ).to_draft()
        assert draft.models is not None
        svc = draft.models[0].service
        assert svc is not None
        assert svc.port == 8080
        assert svc.health_check is not None
        assert svc.health_check.path == "/healthz"


class TestEmptyInputMergesWithBaseline:
    """Empty (all-null) request input must let lower-priority sources
    (variant baseline, preset) fill the required fields, and the merged
    draft must resolve cleanly."""

    def test_baseline_fills_required_fields_when_request_is_empty(self) -> None:
        variant_baseline = RevisionDraft(
            model_definition=ModelDefinitionDraft(
                models=[
                    ModelConfigDraft(name="llama", model_path="/models/llama"),
                ]
            ),
        )
        request = RevisionDraft(model_definition=ModelDefinitionInput().to_draft())

        merged = _merge(variant_baseline, request)

        assert merged.model_definition is not None
        resolved = merged.model_definition.to_resolved()
        assert resolved.models[0].name == "llama"
        assert resolved.models[0].model_path == "/models/llama"

    def test_preset_fills_required_fields_when_request_is_empty(self) -> None:
        preset = RevisionDraft(
            model_definition=ModelDefinitionDraft(
                models=[
                    ModelConfigDraft(
                        name="from-preset",
                        model_path="/preset/path",
                        service=ModelServiceConfigDraft(
                            port=9000,
                            health_check=ModelHealthCheckDraft(path="/ready"),
                        ),
                    )
                ]
            ),
        )
        request = RevisionDraft(model_definition=ModelDefinitionInput().to_draft())

        merged = _merge(preset, request)

        assert merged.model_definition is not None
        resolved = merged.model_definition.to_resolved()
        assert resolved.models[0].name == "from-preset"
        assert resolved.models[0].model_path == "/preset/path"
        assert resolved.models[0].service is not None
        assert resolved.models[0].service.port == 9000
        assert resolved.models[0].service.health_check is not None
        assert resolved.models[0].service.health_check.path == "/ready"

    def test_request_partial_override_combines_with_baseline(self) -> None:
        variant_baseline = RevisionDraft(
            model_definition=ModelDefinitionDraft(
                models=[
                    ModelConfigDraft(name="baseline-name", model_path="/baseline/path"),
                ]
            ),
        )
        request = RevisionDraft(
            model_definition=ModelDefinitionInput(
                models=[ModelConfigInput(name="user-name")],
            ).to_draft(),
        )

        merged = _merge(variant_baseline, request)

        assert merged.model_definition is not None
        resolved = merged.model_definition.to_resolved()
        assert resolved.models[0].name == "user-name"
        assert resolved.models[0].model_path == "/baseline/path"


class TestMergeRaisesWhenAllSourcesAreEmpty:
    """When neither the request nor any baseline source supplies a
    required field, ``to_resolved()`` must raise at the persistence
    boundary — preserving the pre-BA-5983 contract."""

    @pytest.mark.parametrize(
        ("request_input", "error_pattern"),
        [
            pytest.param(
                ModelDefinitionInput(models=[ModelConfigInput(model_path="/p")]),
                r"ModelConfig\.name is required",
                id="missing_name",
            ),
            pytest.param(
                ModelDefinitionInput(models=[ModelConfigInput(name="n")]),
                r"ModelConfig\.model_path is required",
                id="missing_model_path",
            ),
            pytest.param(
                ModelDefinitionInput(
                    models=[
                        ModelConfigInput(
                            name="n",
                            model_path="/p",
                            service=ModelServiceConfigInput(),
                        )
                    ],
                ),
                r"ModelServiceConfig\.port is required",
                id="missing_service_port",
            ),
            pytest.param(
                ModelDefinitionInput(
                    models=[
                        ModelConfigInput(
                            name="n",
                            model_path="/p",
                            service=ModelServiceConfigInput(
                                port=8080,
                                health_check=ModelHealthCheckInput(),
                            ),
                        )
                    ],
                ),
                r"ModelHealthCheck\.path is required",
                id="missing_health_check_path",
            ),
        ],
    )
    def test_missing_required_field_raises(
        self, request_input: ModelDefinitionInput, error_pattern: str
    ) -> None:
        request = RevisionDraft(model_definition=request_input.to_draft())

        merged = _merge(request)

        assert merged.model_definition is not None
        with pytest.raises(ValueError, match=error_pattern):
            merged.model_definition.to_resolved()

    def test_empty_request_with_no_baseline_yields_empty_resolved(self) -> None:
        """A completely empty merge chain resolves to an empty ModelDefinition.

        The ``add_revision`` controller guards against this case separately
        (``model_definition.models must contain at least one entry``); the
        resolved type itself permits an empty models list.
        """
        request = RevisionDraft(model_definition=ModelDefinitionInput().to_draft())

        merged = _merge(request)

        assert merged.model_definition is not None
        resolved = merged.model_definition.to_resolved()
        assert resolved.models == []
