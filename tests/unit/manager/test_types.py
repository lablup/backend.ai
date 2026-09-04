"""Tests for TriState and OptionalState partial-update wrappers."""

from __future__ import annotations

import pytest
from graphql import Undefined as GraphQLUndefined
from strawberry import UNSET

from ai.backend.common.api_handlers import UNDEFINED
from ai.backend.manager.types import OptionalState, TriState, _TriStateEnum

# ============================================================================
# TriState Tests
# ============================================================================


class TestTriStateFromInput:
    """Test TriState.from_input() conversions."""

    def test_from_input_undefined_is_nop(self) -> None:
        """Scenario 1: from_input(UNDEFINED) → is_nop() True, optional_value() None."""
        ts: TriState[str] = TriState.from_input(UNDEFINED)
        assert ts.is_nop() is True
        assert ts.optional_value() is None

    def test_from_input_none_is_nullify(self) -> None:
        """Scenario 2: from_input(None) → is_nullify() True."""
        ts: TriState[str] = TriState.from_input(None)
        assert ts.is_nullify() is True

    def test_from_input_value_is_update(self) -> None:
        """Scenario 3: from_input("x") → is_update() True, value() == "x"."""
        ts: TriState[str] = TriState.from_input("x")
        assert ts.is_update() is True
        assert ts.value() == "x"

    def test_from_input_falsy_values_are_update(self) -> None:
        """Scenario 4: falsy-but-valid values (0, "", []) → update, not nop/nullify."""
        # Zero
        ts_int: TriState[int] = TriState.from_input(0)
        assert ts_int.is_update() is True
        assert ts_int.value() == 0

        # Empty string
        ts_str: TriState[str] = TriState.from_input("")
        assert ts_str.is_update() is True
        assert ts_str.value() == ""

        # Empty list
        ts_list: TriState[list[int]] = TriState.from_input([])
        assert ts_list.is_update() is True
        assert ts_list.value() == []


class TestTriStateFromNullable:
    """Test TriState.from_nullable() conversions."""

    def test_from_nullable_none_is_nop(self) -> None:
        """Scenario 5a: from_nullable(None) → nop (legacy unchanged behaviour)."""
        ts: TriState[str] = TriState.from_nullable(None)
        assert ts.is_nop() is True

    def test_from_nullable_value_is_update(self) -> None:
        """Scenario 5b: from_nullable(1) → update (legacy unchanged behaviour)."""
        ts: TriState[int] = TriState.from_nullable(1)
        assert ts.is_update() is True
        assert ts.value() == 1


class TestTriStateFromGraphQL:
    """Test TriState.from_graphql() conversions."""

    def test_from_graphql_none_is_nullify(self) -> None:
        """Scenario 6a: from_graphql(None) → nullify."""
        ts: TriState[str] = TriState.from_graphql(None)
        assert ts.is_nullify() is True

    def test_from_graphql_strawberry_unset_is_nop(self) -> None:
        """Scenario 6b: from_graphql(strawberry.UNSET) → nop."""
        ts: TriState[str] = TriState.from_graphql(UNSET)
        assert ts.is_nop() is True

    def test_from_graphql_graphql_undefined_is_nop(self) -> None:
        """Scenario 6c: from_graphql(graphql.Undefined) → nop."""
        ts: TriState[str] = TriState.from_graphql(GraphQLUndefined)
        assert ts.is_nop() is True

    def test_from_graphql_value_is_update(self) -> None:
        """Scenario 6d: from_graphql(value) → update."""
        ts: TriState[str] = TriState.from_graphql("value")
        assert ts.is_update() is True
        assert ts.value() == "value"


class TestTriStateValue:
    """Test TriState.value() access."""

    def test_value_raises_when_nop(self) -> None:
        """Scenario 7a: value() raises ValueError when state is nop."""
        ts: TriState[str] = TriState.nop()
        with pytest.raises(ValueError, match="Not allowed to get value when state is not UPDATE"):
            ts.value()

    def test_value_raises_when_nullify(self) -> None:
        """Scenario 7b: value() raises ValueError when state is nullify."""
        ts: TriState[str] = TriState.nullify()
        with pytest.raises(ValueError, match="Not allowed to get value when state is not UPDATE"):
            ts.value()


class TestTriStateMap:
    """Test TriState.map() preserves state."""

    def test_map_update_applies_function(self) -> None:
        """Scenario 8a: map() on update applies function to value."""
        ts: TriState[int] = TriState.update(5)
        mapped: TriState[int] = ts.map(lambda x: x * 2)
        assert mapped.is_update() is True
        assert mapped.value() == 10

    def test_map_nullify_stays_nullify(self) -> None:
        """Scenario 8b: map() on nullify stays nullify."""
        ts: TriState[int] = TriState.nullify()
        mapped: TriState[int] = ts.map(lambda x: x * 2)
        assert mapped.is_nullify() is True

    def test_map_nop_stays_nop(self) -> None:
        """Scenario 8c: map() on nop stays nop."""
        ts: TriState[int] = TriState.nop()
        mapped: TriState[int] = ts.map(lambda x: x * 2)
        assert mapped.is_nop() is True


class TestTriStateUpdateDict:
    """Test TriState.update_dict() state effects."""

    def test_update_dict_update_sets_key(self) -> None:
        """Scenario 9a: update_dict() on update sets key."""
        ts: TriState[str] = TriState.update("value")
        d: dict[str, object] = {}
        ts.update_dict(d, "field")
        assert d == {"field": "value"}

    def test_update_dict_nullify_sets_key_to_none(self) -> None:
        """Scenario 9b: update_dict() on nullify sets key to None."""
        ts: TriState[str] = TriState.nullify()
        d: dict[str, object] = {"field": "old"}
        ts.update_dict(d, "field")
        assert d == {"field": None}

    def test_update_dict_nop_leaves_dict_untouched(self) -> None:
        """Scenario 9c: update_dict() on nop leaves dict untouched."""
        ts: TriState[str] = TriState.nop()
        d: dict[str, object] = {"field": "old"}
        ts.update_dict(d, "field")
        assert d == {"field": "old"}


# ============================================================================
# OptionalState Tests
# ============================================================================


class TestOptionalStateFromInput:
    """Test OptionalState.from_input() conversions."""

    def test_from_input_undefined_is_nop(self) -> None:
        """Scenario 10a: from_input(UNDEFINED) → nop."""
        os: OptionalState[int] = OptionalState.from_input(UNDEFINED)
        # nop state: optional_value() returns None
        assert os.optional_value() is None

    def test_from_input_value_is_update(self) -> None:
        """Scenario 10b: from_input(5) → update with value() == 5."""
        os: OptionalState[int] = OptionalState.from_input(5)
        assert os.value() == 5
        assert os.optional_value() == 5

    def test_from_input_none_raises_error(self) -> None:
        """Scenario 11: from_input(None) raises ValueError."""
        with pytest.raises(ValueError, match="OptionalState cannot be NULLIFY"):
            OptionalState.from_input(None)


class TestOptionalStateConstructor:
    """Test OptionalState constructor validation."""

    def test_constructor_with_nullify_raises_error(self) -> None:
        """Scenario 12: Constructing with NULLIFY state raises ValueError."""
        with pytest.raises(ValueError, match="OptionalState cannot be NULLIFY"):
            OptionalState(state=_TriStateEnum.NULLIFY, value=None)


class TestOptionalStateFromGraphQL:
    """Test OptionalState.from_graphql() conversions."""

    def test_from_graphql_strawberry_unset_is_nop(self) -> None:
        """Scenario 13a: from_graphql(strawberry.UNSET) → nop."""
        os: OptionalState[int] = OptionalState.from_graphql(UNSET)
        # nop state: optional_value() returns None
        assert os.optional_value() is None

    def test_from_graphql_none_raises_error(self) -> None:
        """Scenario 13b: from_graphql(None) raises ValueError."""
        with pytest.raises(ValueError, match="OptionalState cannot be NULLIFY"):
            OptionalState.from_graphql(None)


class TestOptionalStateMap:
    """Test OptionalState.map() for update and nop."""

    def test_map_update_applies_function(self) -> None:
        """Scenario 14a: map() on update applies function to value."""
        os: OptionalState[int] = OptionalState.update(3)
        mapped: OptionalState[int] = os.map(lambda x: x + 10)
        assert mapped.value() == 13
        assert mapped.optional_value() == 13

    def test_map_nop_stays_nop(self) -> None:
        """Scenario 14b: map() on nop stays nop."""
        os: OptionalState[int] = OptionalState.nop()
        mapped: OptionalState[int] = os.map(lambda x: x + 10)
        # nop state: optional_value() returns None
        assert mapped.optional_value() is None


class TestOptionalStateUpdateDict:
    """Test OptionalState.update_dict() for update and nop."""

    def test_update_dict_update_sets_key(self) -> None:
        """OptionalState.update_dict() on update sets key."""
        os: OptionalState[str] = OptionalState.update("data")
        d: dict[str, object] = {}
        os.update_dict(d, "field")
        assert d == {"field": "data"}

    def test_update_dict_nop_leaves_dict_untouched(self) -> None:
        """OptionalState.update_dict() on nop leaves dict untouched."""
        os: OptionalState[str] = OptionalState.nop()
        d: dict[str, object] = {"field": "old"}
        os.update_dict(d, "field")
        assert d == {"field": "old"}
