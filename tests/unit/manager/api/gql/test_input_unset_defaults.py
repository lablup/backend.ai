"""Guard: an omitted GQL input field must not clear the column it maps to.

``PydanticInputMixin.to_pydantic()`` skips only ``strawberry.UNSET``; a field
declared with ``default=None`` reaches the DTO as an explicit null. Where the
adapter maps that null to ``TriState.nullify()``, omitting the field in an
update mutation wipes the stored value.

The cases below are every field an adapter clears on null.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from ai.backend.common.api_handlers import SENTINEL
from ai.backend.manager.api.gql.domain_v2.types.mutations import UpdateDomainInputGQL
from ai.backend.manager.api.gql.login_client_type.types import UpdateLoginClientTypeInputGQL
from ai.backend.manager.api.gql.project_v2.types.mutations import UpdateProjectInputGQL
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin
from ai.backend.manager.api.gql.resource_policy_v2.types.mutations import (
    UpdateKeypairResourcePolicyInputGQL,
    UpdateUserResourcePolicyInputGQL,
)


@dataclass(frozen=True)
class _NullifiedOnNullCase:
    """A GQL input field whose adapter clears the column when it receives a null."""

    input_class: type[PydanticInputMixin[Any]]
    field_name: str


@pytest.mark.parametrize(
    "case",
    [
        _NullifiedOnNullCase(UpdateKeypairResourcePolicyInputGQL, "max_priority"),
        _NullifiedOnNullCase(UpdateKeypairResourcePolicyInputGQL, "max_pending_session_count"),
        _NullifiedOnNullCase(
            UpdateKeypairResourcePolicyInputGQL, "max_pending_session_resource_slots"
        ),
        _NullifiedOnNullCase(UpdateUserResourcePolicyInputGQL, "max_concurrent_logins"),
        _NullifiedOnNullCase(UpdateDomainInputGQL, "description"),
        _NullifiedOnNullCase(UpdateDomainInputGQL, "integration_name"),
        _NullifiedOnNullCase(UpdateProjectInputGQL, "description"),
        _NullifiedOnNullCase(UpdateProjectInputGQL, "integration_name"),
        _NullifiedOnNullCase(UpdateLoginClientTypeInputGQL, "description"),
    ],
    ids=lambda case: f"{case.input_class.__name__}.{case.field_name}",
)
class TestOmittedFieldIsANoop:
    def test_omitting_the_field_reaches_the_dto_as_sentinel(
        self, case: _NullifiedOnNullCase
    ) -> None:
        dto = case.input_class().to_pydantic()

        assert getattr(dto, case.field_name) is SENTINEL

    def test_passing_null_explicitly_still_reaches_the_dto_as_null(
        self, case: _NullifiedOnNullCase
    ) -> None:
        dto = case.input_class(**{case.field_name: None}).to_pydantic()

        assert getattr(dto, case.field_name) is None

    def test_the_field_carries_no_schema_default(self, case: _NullifiedOnNullCase) -> None:
        """A null default in the SDL is what makes graphql-core fill in omitted fields."""
        field = next(
            f
            for f in case.input_class.__dataclass_fields__.values()  # type: ignore[attr-defined]
            if f.name == case.field_name
        )

        assert field.default is not None
