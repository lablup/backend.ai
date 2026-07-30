"""The three input states must survive serialization as three distinct wire shapes.

A field the caller never mentioned must be absent from the body, an explicit ``None``
must survive as a JSON null, and a value must survive as itself. Collapsing any two of
these makes "leave this alone" and "clear this" indistinguishable to the server.

``SENTINEL`` is the DTO-side default for the first state and must never be assigned by a
caller: ``Sentinel.TOKEN`` is ``enum.auto()``, so ``mode="json"`` renders it as the
integer ``1``, which an int-typed field re-parses as a value.
"""

from __future__ import annotations

import importlib
import pkgutil
from dataclasses import dataclass
from typing import Any, get_args

import pytest

import ai.backend.common.dto.manager.v2 as v2_dto
from ai.backend.common.api_handlers import SENTINEL, BaseRequestModel, Sentinel

# Mirrors client/v2/base_client.py, which is what actually puts a request on the wire.
_WIRE_DUMP_KWARGS: dict[str, Any] = {"mode": "json", "exclude_unset": True}


def _sentinel_fields() -> list[tuple[type[BaseRequestModel], str]]:
    found: list[tuple[type[BaseRequestModel], str]] = []
    for module in pkgutil.iter_modules(v2_dto.__path__):
        try:
            request_module = importlib.import_module(f"{v2_dto.__name__}.{module.name}.request")
        except ModuleNotFoundError:
            continue
        for attribute in vars(request_module).values():
            if not (isinstance(attribute, type) and issubclass(attribute, BaseRequestModel)):
                continue
            if attribute.__module__ != request_module.__name__:
                continue
            for name, info in attribute.model_fields.items():
                if Sentinel in get_args(info.annotation):
                    found.append((attribute, name))
    return found


@dataclass(frozen=True)
class _WireExpectation:
    key_present: bool
    value: Any


@dataclass(frozen=True)
class _StateCase:
    label: str
    kwargs: dict[str, Any]
    expected: _WireExpectation


class TestSentinelWireProtocol:
    def test_every_sentinel_field_defaults_to_sentinel(self) -> None:
        offenders = [
            f"{cls.__module__.rsplit('.', 2)[-2]}.{cls.__name__}.{name}"
            for cls, name in _sentinel_fields()
            if cls.model_fields[name].default is not SENTINEL
        ]
        assert offenders == [], (
            "Sentinel-typed fields must default to SENTINEL so that a field the caller "
            f"never mentioned means 'no change': {offenders}"
        )

    @pytest.mark.parametrize(
        "case",
        [
            _StateCase(
                label="unmentioned",
                kwargs={},
                expected=_WireExpectation(key_present=False, value=None),
            ),
            _StateCase(
                label="explicit-null",
                kwargs={"field": None},
                expected=_WireExpectation(key_present=True, value=None),
            ),
            _StateCase(
                label="value",
                kwargs={"field": "a-value"},
                expected=_WireExpectation(key_present=True, value="a-value"),
            ),
        ],
        ids=lambda case: case.label,
    )
    def test_state_survives_serialization(self, case: _StateCase) -> None:
        class _Model(BaseRequestModel):
            field: str | Sentinel | None = SENTINEL

        dumped = _Model(**case.kwargs).model_dump(**_WIRE_DUMP_KWARGS)
        assert ("field" in dumped) is case.expected.key_present
        if case.expected.key_present:
            assert dumped["field"] == case.expected.value

    def test_assigning_sentinel_leaks_it_onto_the_wire(self) -> None:
        """Why callers omit the field instead of assigning SENTINEL.

        An int-typed field re-parses the leaked ``1`` as a value, so a caller that
        assigns SENTINEL to say "no change" would set the column to 1 instead.
        """

        class _Model(BaseRequestModel):
            count: int | Sentinel | None = SENTINEL

        leaked = _Model(count=SENTINEL).model_dump(**_WIRE_DUMP_KWARGS)
        assert leaked == {"count": 1}
        assert _Model.model_validate(leaked).count == 1
