"""Tests for max_priority exposure on the keypair resource policy GQL types."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from ai.backend.common.api_handlers import SENTINEL
from ai.backend.manager.api.gql.base import IntFilter
from ai.backend.manager.api.gql.resource_policy_v2.types.filters import (
    KeypairResourcePolicyV2Filter,
    KeypairResourcePolicyV2OrderField,
)
from ai.backend.manager.api.gql.resource_policy_v2.types.mutations import (
    CreateKeypairResourcePolicyInputGQL,
    UpdateKeypairResourcePolicyInputGQL,
)


@dataclass(frozen=True)
class _MaxPriorityCase:
    """A max_priority input value and the DTO value it must produce."""

    label: str
    given: int | None
    expected: int | None


class TestKeypairResourcePolicyMaxPriorityCreateInput:
    def test_omitted_max_priority_leaves_the_ceiling_uncapped(self) -> None:
        dto = CreateKeypairResourcePolicyInputGQL(
            name="test-policy",
            default_for_unspecified="LIMITED",
            total_resource_slots=[],
            max_session_lifetime=0,
            max_concurrent_sessions=10,
            max_containers_per_session=1,
            idle_timeout=600,
            allowed_vfolder_hosts=[],
        ).to_pydantic()

        assert dto.max_priority is None

    @pytest.mark.parametrize(
        "case",
        [
            _MaxPriorityCase(label="explicit_null", given=None, expected=None),
            _MaxPriorityCase(label="value", given=10, expected=10),
        ],
        ids=lambda case: case.label,
    )
    def test_given_max_priority_reaches_the_dto(self, case: _MaxPriorityCase) -> None:
        dto = CreateKeypairResourcePolicyInputGQL(
            name="test-policy",
            default_for_unspecified="LIMITED",
            total_resource_slots=[],
            max_session_lifetime=0,
            max_concurrent_sessions=10,
            max_containers_per_session=1,
            idle_timeout=600,
            allowed_vfolder_hosts=[],
            max_priority=case.given,
        ).to_pydantic()

        assert dto.max_priority == case.expected


class TestKeypairResourcePolicyMaxPriorityUpdateInput:
    def test_omitted_max_priority_is_a_noop(self) -> None:
        """An update that does not mention max_priority must not clear it."""
        dto = UpdateKeypairResourcePolicyInputGQL().to_pydantic()

        assert dto.max_priority is SENTINEL

    @pytest.mark.parametrize(
        "case",
        [
            _MaxPriorityCase(label="explicit_null", given=None, expected=None),
            _MaxPriorityCase(label="value", given=10, expected=10),
        ],
        ids=lambda case: case.label,
    )
    def test_given_max_priority_reaches_the_dto(self, case: _MaxPriorityCase) -> None:
        dto = UpdateKeypairResourcePolicyInputGQL(max_priority=case.given).to_pydantic()

        assert dto.max_priority == case.expected


class TestKeypairResourcePolicyMaxPriorityQueryOptions:
    def test_filter_carries_max_priority(self) -> None:
        dto = KeypairResourcePolicyV2Filter(max_priority=IntFilter(equals=10)).to_pydantic()

        assert dto.max_priority is not None
        assert dto.max_priority.equals == 10

    def test_filter_omits_max_priority_by_default(self) -> None:
        dto = KeypairResourcePolicyV2Filter().to_pydantic()

        assert dto.max_priority is None

    def test_order_field_exposes_max_priority(self) -> None:
        assert KeypairResourcePolicyV2OrderField.MAX_PRIORITY.value == "max_priority"
