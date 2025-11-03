from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Optional, Self, override

import pytest

from ai.backend.common.exception import (
    ASTParsingFailed,
    InvalidParameter,
    UnsupportedFieldType,
    UnsupportedOperation,
)
from ai.backend.manager.api.gql.base import StringFilter
from ai.backend.manager.api.types import BaseMinilangFilterConverter, BaseMinilangOrderConverter


class TestBaseMinilangFilterConverter:
    @pytest.fixture
    def sample_filter_class(self) -> Any:
        """Create a concrete implementation of BaseMinilangFilterConverter for testing."""

        @dataclass
        class SampleFilter(BaseMinilangFilterConverter):
            id: Optional[StringFilter] = None
            name: Optional[StringFilter] = None
            email: Optional[StringFilter] = None
            status: Optional[StringFilter] = None
            active: Optional[StringFilter] = None
            role: Optional[StringFilter] = None
            department: Optional[StringFilter] = None

            AND: Optional[list[Self]] = None
            OR: Optional[list[Self]] = None
            NOT: Optional[list[Self]] = None

            @override
            @classmethod
            def _create_from_condition(cls, field: str, operator: str, value: Any) -> Self:
                match field.lower():
                    case "id":
                        return cls(id=cls._create_string_filter(operator, value))
                    case "name":
                        return cls(name=cls._create_string_filter(operator, value))
                    case "email":
                        return cls(email=cls._create_string_filter(operator, value))
                    case "status":
                        return cls(status=cls._create_string_filter(operator, value))
                    case "active":
                        return cls(active=cls._create_string_filter(operator, value))
                    case "role":
                        return cls(role=cls._create_string_filter(operator, value))
                    case "department":
                        return cls(department=cls._create_string_filter(operator, value))
                    case _:
                        raise UnsupportedFieldType(f"Unsupported filter field: {field}")

        return SampleFilter

    @pytest.mark.parametrize(
        ("query", "field", "attribute", "expected"),
        [
            ('id == "user123"', "id", "equals", "user123"),
            ('status != "inactive"', "status", "not_equals", "inactive"),
            ('email == "user+test@example.com"', "email", "equals", "user+test@example.com"),
            ('name ilike "%john%"', "name", "i_contains", "john"),
            ('name like "%Test%"', "name", "contains", "Test"),
            ('email like "%@Company.com"', "email", "ends_with", "@Company.com"),
            ('name ilike "%래블업%"', "name", "i_contains", "래블업"),
            ('name like "백엔드닷에이아이%"', "name", "starts_with", "백엔드닷에이아이"),
            ("active == true", "active", "equals", "True"),
            ("active == false", "active", "equals", "False"),
            ("status == null", "status", "equals", "None"),
            ('name like "test"', "name", "equals", "test"),  # No wildcards
            ('name like "%%"', "name", "contains", ""),  # Both wildcards with empty string
            ('name == ""', "name", "equals", ""),  # Empty string
            ('name == "test\\"name"', "name", "equals", 'test"name'),  # Escaped quotes
        ],
    )
    def test_basic_operators(
        self, sample_filter_class: Any, query: str, field: str, attribute: str, expected: str
    ) -> None:
        result = sample_filter_class.from_minilang(query)

        # Verify the specific field filter
        field_filter = getattr(result, field)
        assert field_filter is not None

        # Verify the expected attribute and value is set correctly
        assert getattr(field_filter, attribute) == expected

    @pytest.mark.parametrize(
        ("query", "expected_conditions"),
        [
            (
                '(role == "admin") & (department == "Engineering")',
                [("role", "equals", "admin"), ("department", "equals", "Engineering")],
            ),
            (
                '(email ilike "%@company.com%") & (status == "active") & (name ilike "%admin%")',
                [
                    ("email", "i_contains", "@company.com"),
                    ("status", "equals", "active"),
                    ("name", "i_contains", "admin"),
                ],
            ),
            (
                '(name like "Admin%") & (role == "superuser") & (status != "active") & (department == "devops")',
                [
                    ("name", "starts_with", "Admin"),
                    ("role", "equals", "superuser"),
                    ("status", "not_equals", "active"),
                    ("department", "equals", "devops"),
                ],
            ),
        ],
    )
    def test_multiple_filters_with_and(
        self,
        sample_filter_class: Any,
        query: str,
        expected_conditions: list[tuple[str, str, str]],
    ) -> None:
        result = sample_filter_class.from_minilang(query)

        # Verify that result has AND structure
        assert result.AND is not None

        # Recursively check all AND filters
        def check_filter(f: Any, field: str, attribute: str, expected: str) -> bool:
            # Check direct field
            field_filter = getattr(f, field, None)
            if (field_filter is not None) and (getattr(field_filter, attribute, None) == expected):
                return True

            # Check nested AND recursively
            if f.AND is not None:
                for nested in f.AND:
                    if check_filter(nested, field, attribute, expected):
                        return True

            return False

        # Verify each expected condition
        for field, attribute, expected in expected_conditions:
            assert check_filter(result, field, attribute, expected), (
                f"Expected {field}.{attribute}={expected} not found in AND filters"
            )

    @pytest.mark.parametrize(
        ("query", "expected_conditions"),
        [
            (
                '(status == "invited") | (status != "registered")',
                [("status", "equals", "invited"), ("status", "not_equals", "registered")],
            ),
            (
                '(department == "Sales") | (department ilike "Market%")',
                [("department", "equals", "Sales"), ("department", "i_starts_with", "Market")],
            ),
            (
                '(status == "active") | (status != "pending") | (status == "invited")',
                [
                    ("status", "equals", "active"),
                    ("status", "not_equals", "pending"),
                    ("status", "equals", "invited"),
                ],
            ),
            (
                '(role == "admin") | (role == "superadmin") | (role == "user") | (role == "monitor")',
                [
                    ("role", "equals", "admin"),
                    ("role", "equals", "superadmin"),
                    ("role", "equals", "user"),
                    ("role", "equals", "monitor"),
                ],
            ),
        ],
    )
    def test_multiple_filters_with_or(
        self,
        sample_filter_class: Any,
        query: str,
        expected_conditions: list[tuple[str, str, str]],
    ) -> None:
        result = sample_filter_class.from_minilang(query)

        # Verify that result has OR structure
        assert result.OR is not None

        # Recursively check all OR filters
        def check_filter(f: Any, field: str, attribute: str, expected: str) -> bool:
            # Check direct field
            field_filter = getattr(f, field, None)
            if field_filter is not None and getattr(field_filter, attribute, None) == expected:
                return True

            # Check nested OR recursively
            if f.OR is not None:
                for nested in f.OR:
                    if check_filter(nested, field, attribute, expected):
                        return True

            return False

        # Verify each expected condition
        for field, attribute, expected in expected_conditions:
            assert check_filter(result, field, attribute, expected), (
                f"Expected {field}.{attribute}={expected} not found in OR filters"
            )

    @pytest.mark.parametrize(
        ("query", "and_conditions", "or_conditions"),
        [
            (
                '(name ilike "%admin%") & ((status == "active") | (status != "pending"))',
                [("name", "i_contains", "admin")],
                [("status", "equals", "active"), ("status", "not_equals", "pending")],
            ),
            (
                '(email ilike "%@company.com") & ((role == "admin") | (role != "manager"))',
                [("email", "i_ends_with", "@company.com")],
                [("role", "equals", "admin"), ("role", "not_equals", "manager")],
            ),
            (
                '(active == true) & ((department ilike "%Sales%") | (department == "Marketing"))',
                [("active", "equals", "True")],
                [("department", "i_contains", "Sales"), ("department", "equals", "Marketing")],
            ),
            (
                '(id == "user123") & ((status == "active") | (status == "invited"))',
                [("id", "equals", "user123")],
                [("status", "equals", "active"), ("status", "equals", "invited")],
            ),
        ],
    )
    def test_mixed_and_or_filters(
        self,
        sample_filter_class: Any,
        query: str,
        and_conditions: list[tuple[str, str, str]],
        or_conditions: list[tuple[str, str, str]],
    ) -> None:
        result = sample_filter_class.from_minilang(query)

        # Recursively check all filters (both AND and OR chains)
        def check_filter(f: Any, field: str, attribute: str, expected: str) -> bool:
            # Check direct field
            field_filter = getattr(f, field, None)
            if field_filter is not None and getattr(field_filter, attribute, None) == expected:
                return True

            # Check nested AND
            if f.AND is not None:
                for nested in f.AND:
                    if check_filter(nested, field, attribute, expected):
                        return True

            # Check nested OR
            if f.OR is not None:
                for nested in f.OR:
                    if check_filter(nested, field, attribute, expected):
                        return True

            return False

        # Verify AND conditions
        for field, attribute, expected in and_conditions:
            assert check_filter(result, field, attribute, expected), (
                f"AND condition {field}.{attribute}={expected} not found"
            )

        # Verify OR conditions
        for field, attribute, expected in or_conditions:
            assert check_filter(result, field, attribute, expected), (
                f"OR condition {field}.{attribute}={expected} not found"
            )

    @pytest.mark.parametrize(
        ("query", "expected_exception"),
        [
            ('invalid_field == "test"', UnsupportedFieldType),
            ("", ASTParsingFailed),  # Empty string
            ("   ", ASTParsingFailed),  # Whitespace only
            ("name == ", ASTParsingFailed),  # Missing value
            ('name "test"', ASTParsingFailed),  # Missing operator
            ('== "test"', ASTParsingFailed),  # Missing field
            ('(name == "test"', ASTParsingFailed),  # Unmatched left parenthesis
            ('name == "test")', ASTParsingFailed),  # Unmatched right parenthesis
            ('name === "test"', UnsupportedOperation),  # Invalid operator
            (
                'name == "test" & & status == "active"',
                ASTParsingFailed,
            ),  # Consecutive logical operators
            ('name == "test" &', ASTParsingFailed),  # Trailing logical operator
            ('& name == "test"', ASTParsingFailed),  # Leading logical operator
        ],
    )
    def test_malformed_expressions_raise_error(
        self, sample_filter_class: Any, query: str, expected_exception: type[Exception]
    ) -> None:
        with pytest.raises(expected_exception):
            sample_filter_class.from_minilang(query)


class TestBaseMinilangOrderConverter:
    @pytest.fixture
    def sample_order_converter(self) -> Any:
        class SampleOrderField(StrEnum):
            ID = "id"
            NAME = "name"
            STATUS = "status"
            CREATED_AT = "created_at"
            UPDATED_AT = "updated_at"
            EMAIL = "email"

        @dataclass
        class SampleOrderingOptions:
            order_by: list[tuple[SampleOrderField, bool]]

        class SampleOrderConverter(
            BaseMinilangOrderConverter[SampleOrderField, SampleOrderingOptions]
        ):
            @override
            def _convert_field(self, parsed_expr: dict[str, bool]) -> dict[SampleOrderField, bool]:
                result = {}
                for name, asc in parsed_expr.items():
                    try:
                        result[SampleOrderField(name)] = asc
                    except ValueError:
                        raise InvalidParameter(f"Invalid field name: {name}")
                return result

            @override
            def _create_ordering_option(
                self, order_by: dict[SampleOrderField, bool]
            ) -> SampleOrderingOptions:
                order_list = [(field, not asc) for field, asc in order_by.items()]
                return SampleOrderingOptions(order_by=order_list)

        return SampleOrderConverter()

    @pytest.mark.parametrize(
        ("query", "expected_fields", "expected_order_condition_count"),
        [
            ("+id", {"id": False}, 1),
            ("+name,+status", {"name": False, "status": False}, 2),
            ("  +name,-status  ", {"name": False, "status": True}, 2),  # With whitespace
            ("+name,-created_at,status", {"name": False, "created_at": True, "status": False}, 3),
            (
                "+id , -name , status",
                {"id": False, "name": True, "status": False},
                3,
            ),  # With whitespace
        ],
    )
    def test_multiple_fields_ordering(
        self,
        sample_order_converter: Any,
        query: str,
        expected_fields: dict[str, bool],
        expected_order_condition_count: int,
    ) -> None:
        result = sample_order_converter.from_minilang(query)
        assert len(result.order_by) == expected_order_condition_count

        field_to_desc = {field.value: desc for field, desc in result.order_by}
        assert field_to_desc == expected_fields

    @pytest.mark.parametrize(
        ("query", "error_match"),
        [
            ("", "Order expression cannot be empty"),
            ("   ", "Order expression cannot be empty"),
            ("+", "Field name in order expression cannot be empty"),
            ("-", "Field name in order expression cannot be empty"),
            ("+invalid_field", "Invalid field name"),
            ("+name,-invalid,-status", "Invalid field name"),
        ],
    )
    def test_order_error_cases(
        self, sample_order_converter: Any, query: str, error_match: str
    ) -> None:
        with pytest.raises(InvalidParameter, match=error_match):
            sample_order_converter.from_minilang(query)
