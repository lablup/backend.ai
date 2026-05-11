"""Verify that nullable v2 ``ModelDefinitionInput`` fields still result in
correct required-field enforcement after the revision merge chain.

This pins the BA-5983 behavior: the GraphQL/REST boundary accepts
all-optional fields, but ``to_resolved()`` at the persistence boundary
must still raise when no merge layer (request, preset, variant baseline)
supplies a required value.
"""

from __future__ import annotations

import functools
from dataclasses import dataclass

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


@dataclass(frozen=True)
class ResolvedExpectation:
    """Expected attributes on the resolved ``ModelConfig`` at ``models[0]``.

    Only the named-string fields participate; ``None`` means the
    corresponding nested object should not be asserted (the scenario
    does not exercise it).
    """

    name: str
    model_path: str
    service_port: int | None = None
    health_check_path: str | None = None


class TestModelDefinitionInputToDraft:
    """``ModelDefinitionInput.to_draft`` is the bridge between the
    all-optional DTO and the merge-chain draft. The conversion itself
    must never raise — required-field enforcement is deferred to
    ``to_resolved()`` after the merge — and must preserve every field
    the input carries (including ``None`` placeholders)."""

    @pytest.mark.parametrize(
        "input_dto",
        [
            pytest.param(ModelDefinitionInput(), id="empty"),
            pytest.param(
                ModelDefinitionInput(models=[ModelConfigInput(name="only-name")]),
                id="partial_name_only",
            ),
            pytest.param(
                ModelDefinitionInput(
                    models=[
                        ModelConfigInput(
                            name="m",
                            service=ModelServiceConfigInput(
                                port=8080,
                                health_check=ModelHealthCheckInput(path="/healthz"),
                            ),
                        )
                    ]
                ),
                id="nested_service_and_health_check",
            ),
        ],
    )
    def test_to_draft_preserves_input_shape(self, input_dto: ModelDefinitionInput) -> None:
        draft = input_dto.to_draft()
        assert isinstance(draft, ModelDefinitionDraft)
        assert draft.model_dump() == input_dto.model_dump()


class TestEmptyInputMergesWithBaseline:
    """Empty (all-null) request input must let lower-priority sources
    (variant baseline, preset) fill the required fields, and the merged
    draft must resolve cleanly."""

    @pytest.mark.parametrize(
        ("drafts", "expected"),
        [
            pytest.param(
                [
                    RevisionDraft(
                        model_definition=ModelDefinitionDraft(
                            models=[ModelConfigDraft(name="llama", model_path="/models/llama")],
                        ),
                    ),
                    RevisionDraft(model_definition=ModelDefinitionInput().to_draft()),
                ],
                ResolvedExpectation(name="llama", model_path="/models/llama"),
                id="variant_baseline_fills_required",
            ),
            pytest.param(
                [
                    RevisionDraft(
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
                            ],
                        ),
                    ),
                    RevisionDraft(model_definition=ModelDefinitionInput().to_draft()),
                ],
                ResolvedExpectation(
                    name="from-preset",
                    model_path="/preset/path",
                    service_port=9000,
                    health_check_path="/ready",
                ),
                id="preset_fills_nested_required",
            ),
            pytest.param(
                [
                    RevisionDraft(
                        model_definition=ModelDefinitionDraft(
                            models=[
                                ModelConfigDraft(name="baseline-name", model_path="/baseline/path"),
                            ],
                        ),
                    ),
                    RevisionDraft(
                        model_definition=ModelDefinitionInput(
                            models=[ModelConfigInput(name="user-name")],
                        ).to_draft(),
                    ),
                ],
                ResolvedExpectation(name="user-name", model_path="/baseline/path"),
                id="request_partial_overrides_baseline",
            ),
        ],
    )
    def test_merge_resolves_to_expected_values(
        self, drafts: list[RevisionDraft], expected: ResolvedExpectation
    ) -> None:
        merged = _merge(*drafts)

        assert merged.model_definition is not None
        resolved = merged.model_definition.to_resolved()
        model = resolved.models[0]
        assert model.name == expected.name
        assert model.model_path == expected.model_path
        if expected.service_port is not None:
            assert model.service is not None
            assert model.service.port == expected.service_port
        if expected.health_check_path is not None:
            assert model.service is not None
            assert model.service.health_check is not None
            assert model.service.health_check.path == expected.health_check_path


class TestMergeRaisesWhenAllSourcesAreEmpty:
    """When neither the request nor any baseline source supplies a
    required field, ``to_resolved()`` must raise at the persistence
    boundary — preserving the pre-BA-5983 contract.

    Each scenario layers a baseline draft (variant-style) together with
    a request draft so the merge actually combines fields across
    sources; the target required field remains unfilled in every layer
    and the resolved-time check fires on it specifically."""

    @pytest.mark.parametrize(
        ("drafts", "error_pattern"),
        [
            pytest.param(
                [
                    # baseline supplies model_path; request adds nothing.
                    RevisionDraft(
                        model_definition=ModelDefinitionDraft(
                            models=[ModelConfigDraft(model_path="/baseline/path")],
                        ),
                    ),
                    RevisionDraft(
                        model_definition=ModelDefinitionInput(
                            models=[ModelConfigInput()],
                        ).to_draft(),
                    ),
                ],
                r"ModelConfig\.name is required",
                id="name_unfilled_across_baseline_and_request",
            ),
            pytest.param(
                [
                    # baseline supplies name; request adds nothing.
                    RevisionDraft(
                        model_definition=ModelDefinitionDraft(
                            models=[ModelConfigDraft(name="baseline-name")],
                        ),
                    ),
                    RevisionDraft(
                        model_definition=ModelDefinitionInput(
                            models=[ModelConfigInput()],
                        ).to_draft(),
                    ),
                ],
                r"ModelConfig\.model_path is required",
                id="model_path_unfilled_across_baseline_and_request",
            ),
            pytest.param(
                [
                    # baseline supplies the outer ModelConfig fields;
                    # request adds an empty service (no port anywhere).
                    RevisionDraft(
                        model_definition=ModelDefinitionDraft(
                            models=[ModelConfigDraft(name="n", model_path="/p")],
                        ),
                    ),
                    RevisionDraft(
                        model_definition=ModelDefinitionInput(
                            models=[ModelConfigInput(service=ModelServiceConfigInput())],
                        ).to_draft(),
                    ),
                ],
                r"ModelServiceConfig\.port is required",
                id="service_port_unfilled_across_baseline_and_request",
            ),
            pytest.param(
                [
                    # baseline supplies a service with port; request adds
                    # an empty health_check (no path anywhere).
                    RevisionDraft(
                        model_definition=ModelDefinitionDraft(
                            models=[
                                ModelConfigDraft(
                                    name="n",
                                    model_path="/p",
                                    service=ModelServiceConfigDraft(port=8080),
                                )
                            ],
                        ),
                    ),
                    RevisionDraft(
                        model_definition=ModelDefinitionInput(
                            models=[
                                ModelConfigInput(
                                    service=ModelServiceConfigInput(
                                        health_check=ModelHealthCheckInput(),
                                    ),
                                )
                            ],
                        ).to_draft(),
                    ),
                ],
                r"ModelHealthCheck\.path is required",
                id="health_check_path_unfilled_across_baseline_and_request",
            ),
        ],
    )
    def test_required_field_unfilled_after_merge_raises(
        self, drafts: list[RevisionDraft], error_pattern: str
    ) -> None:
        merged = _merge(*drafts)

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
