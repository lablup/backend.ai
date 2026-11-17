from __future__ import annotations

from datetime import datetime
from typing import Any

import pytest
from pydantic import BaseModel, ConfigDict

from ai.backend.common.data.partial import PartialRecord, selectable
from ai.backend.common.errors.partial_record import (
    FrozenPartialRecordError,
    InvalidPartialRecordError,
    NotSelectedError,
)
from ai.backend.common.tristate.unset import UNSET, Unset


class _Group(PartialRecord):
    count: int
    status: str = selectable()
    created_at_max: datetime | None = selectable()


@pytest.fixture
def status_only() -> _Group:
    return _Group(count=3, status="ok")


@pytest.fixture
def null_created_at() -> _Group:
    return _Group(count=0, created_at_max=None)


class TestRead:
    def test_selected_field_returns_value(self, status_only: _Group) -> None:
        assert status_only.count == 3
        assert status_only.status == "ok"

    def test_field_selected_as_none_returns_none(self, null_created_at: _Group) -> None:
        assert null_created_at.created_at_max is None

    def test_unselected_field_raises(self, status_only: _Group) -> None:
        with pytest.raises(NotSelectedError):
            _ = status_only.created_at_max

    def test_undeclared_name_raises_attribute_error(self, status_only: _Group) -> None:
        name = "missing"
        with pytest.raises(AttributeError):
            getattr(status_only, name)

    def test_class_keeps_no_marker(self) -> None:
        assert "status" not in vars(_Group)
        assert "created_at_max" not in vars(_Group)


class TestSelection:
    def test_selected_fields_in_declaration_order(self) -> None:
        group = _Group(created_at_max=None, status="ok", count=1)
        assert group.selected_fields() == ("count", "status", "created_at_max")

    def test_selected_fields_skip_unselected(self, status_only: _Group) -> None:
        assert status_only.selected_fields() == ("count", "status")

    def test_is_selected(self, null_created_at: _Group) -> None:
        assert null_created_at.is_selected("created_at_max")
        assert not null_created_at.is_selected("status")


class TestConstruction:
    def test_missing_required_field_rejected(self) -> None:
        values: dict[str, Any] = {"status": "ok"}
        with pytest.raises(InvalidPartialRecordError):
            _Group(**values)

    def test_undeclared_field_rejected(self) -> None:
        values: dict[str, Any] = {"count": 1, "bogus": 2}
        with pytest.raises(InvalidPartialRecordError):
            _Group(**values)

    def test_default_other_than_selectable_rejected(self) -> None:
        with pytest.raises(InvalidPartialRecordError):

            class _WithDefault(PartialRecord):
                count: int = 0


class TestFrozen:
    def test_assigning_selected_field_rejected(self, status_only: _Group) -> None:
        with pytest.raises(FrozenPartialRecordError):
            setattr(status_only, "status", "failed")

    def test_assigning_unselected_field_rejected(self, status_only: _Group) -> None:
        with pytest.raises(FrozenPartialRecordError):
            setattr(status_only, "created_at_max", None)


class TestEquality:
    def test_same_selection_and_values_equal(self, status_only: _Group) -> None:
        assert status_only == _Group(count=3, status="ok")
        assert hash(status_only) == hash(_Group(count=3, status="ok"))

    def test_unselected_differs_from_none(self) -> None:
        assert _Group(count=0) != _Group(count=0, created_at_max=None)


class _GroupResponse(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    count: int
    status: str | Unset = UNSET
    created_at_max: datetime | None | Unset = UNSET


class _GroupMapper:
    def to_response(self, group: _Group) -> _GroupResponse:
        return _GroupResponse(
            count=group.count,
            status=group.or_missing(lambda: group.status),
            created_at_max=group.or_missing(lambda: group.created_at_max),
        )


class TestOrMissing:
    def test_selected_field_returns_value(self, status_only: _Group) -> None:
        assert status_only.or_missing(lambda: status_only.status) == "ok"

    def test_unselected_field_returns_missing(self, status_only: _Group) -> None:
        assert status_only.or_missing(lambda: status_only.created_at_max) is UNSET

    def test_unselected_field_is_left_out_of_json(self, status_only: _Group) -> None:
        response = _GroupMapper().to_response(status_only)

        assert response.model_dump(mode="json") == {"count": 3, "status": "ok"}

    def test_field_selected_as_none_is_null_in_json(self, null_created_at: _Group) -> None:
        response = _GroupMapper().to_response(null_created_at)

        assert response.model_dump(mode="json") == {"count": 0, "created_at_max": None}
