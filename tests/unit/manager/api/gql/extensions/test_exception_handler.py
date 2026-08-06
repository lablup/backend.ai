"""Tests for the GraphQL error shape produced from a raised exception."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.manager.api.gql.extensions.exception_handler import to_graphql_error

_FIELD_DETAILS: list[dict[str, Any]] = [
    {"type": "flag_requires_args", "loc": ["value_type"], "msg": "only valid with 'args'."}
]


@dataclass(frozen=True)
class _ErrorCase:
    label: str
    error: Exception
    expected_code: str
    expected_message: str
    expected_data: list[dict[str, Any]] | None


class TestToGraphQLError:
    @pytest.mark.parametrize(
        "case",
        [
            _ErrorCase(
                label="client-error",
                error=InvalidAPIParameters("rank: must be >= 0"),
                expected_code="api_parsing_invalid-parameters",
                expected_message="Invalid or Missing API Parameters. (rank: must be >= 0)",
                expected_data=None,
            ),
            _ErrorCase(
                label="client-error-with-details",
                error=InvalidAPIParameters(
                    "value_type: only valid with 'args'.", extra_data=_FIELD_DETAILS
                ),
                expected_code="api_parsing_invalid-parameters",
                expected_message=(
                    "Invalid or Missing API Parameters. (value_type: only valid with 'args'.)"
                ),
                expected_data=_FIELD_DETAILS,
            ),
            _ErrorCase(
                label="unexpected-error",
                error=RuntimeError("boom"),
                expected_code="backendai_generic_internal-error",
                expected_message="boom",
                expected_data=None,
            ),
        ],
        ids=lambda case: case.label,
    )
    def test_error_is_rendered_for_the_client(self, case: _ErrorCase) -> None:
        error = to_graphql_error(case.error)

        assert error.message == case.expected_message
        assert error.extensions is not None
        assert error.extensions["code"] == case.expected_code
        assert error.extensions.get("data") == case.expected_data
