"""Guard: an omitted GQL input field must not clear the value it maps to.

``PydanticInputMixin.to_pydantic()`` skips only ``strawberry.UNSET``; a field
declared with ``default=None`` reaches the DTO as an explicit null. For a DTO
field that accepts ``Sentinel``, the adapters read that null as "clear this
column", so omitting the field in a mutation wipes the stored value.
"""

from __future__ import annotations

import dataclasses
import types
import typing
from dataclasses import dataclass
from typing import Any

import pytest

import ai.backend.manager.api.gql.schema  # noqa: F401  (imports every GQL type module)
from ai.backend.common.api_handlers import Sentinel
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin
from ai.backend.manager.api.gql.resource_policy_v2.types.mutations import (
    UpdateKeypairResourcePolicyInputGQL,
)


@dataclass(frozen=True)
class _SentinelBackedField:
    """A GQL input field whose DTO counterpart distinguishes "omitted" from "null"."""

    qualname: str
    input_class_name: str
    defaults_to_null: bool


def _accepts_sentinel(annotation: Any) -> bool:
    if annotation is Sentinel:
        return True
    if typing.get_origin(annotation) in (typing.Union, types.UnionType):
        return any(_accepts_sentinel(arg) for arg in typing.get_args(annotation))
    return False


@pytest.fixture(scope="module")
def sentinel_backed_fields() -> list[_SentinelBackedField]:
    input_classes: set[type] = set()
    pending: list[type] = list(PydanticInputMixin.__subclasses__())
    while pending:
        candidate = pending.pop()
        if candidate in input_classes:
            continue
        input_classes.add(candidate)
        pending.extend(candidate.__subclasses__())

    fields: list[_SentinelBackedField] = []
    for input_cls in input_classes:
        dto_cls = getattr(input_cls, "__dto_type__", None)
        if dto_cls is None or not dataclasses.is_dataclass(input_cls):
            continue
        model_fields = getattr(dto_cls, "model_fields", {})
        for field in dataclasses.fields(input_cls):
            dto_field = model_fields.get(field.name)
            if dto_field is None or not _accepts_sentinel(dto_field.annotation):
                continue
            fields.append(
                _SentinelBackedField(
                    qualname=f"{input_cls.__module__}.{input_cls.__name__}.{field.name}",
                    input_class_name=input_cls.__name__,
                    defaults_to_null=field.default is None,
                )
            )
    return fields


class TestSentinelBackedInputDefaults:
    def test_no_sentinel_backed_field_defaults_to_null(
        self, sentinel_backed_fields: list[_SentinelBackedField]
    ) -> None:
        offenders = sorted(f.qualname for f in sentinel_backed_fields if f.defaults_to_null)

        assert offenders == [], (
            "these fields default to null instead of strawberry.UNSET, so omitting them"
            f" in a mutation clears the stored value: {offenders}"
        )

    def test_the_walk_reaches_the_input_types_it_is_meant_to_cover(
        self, sentinel_backed_fields: list[_SentinelBackedField]
    ) -> None:
        """A broken walk would make the check above vacuously pass."""
        covered = {f.input_class_name for f in sentinel_backed_fields}

        assert "UpdateKeypairResourcePolicyInputGQL" in covered
        assert "UpdateModelCardInputGQL" in covered
        assert len(sentinel_backed_fields) > 50

    def test_omitted_field_reaches_the_dto_as_sentinel(self) -> None:
        dto = UpdateKeypairResourcePolicyInputGQL().to_pydantic()

        assert isinstance(dto.max_pending_session_count, Sentinel)
