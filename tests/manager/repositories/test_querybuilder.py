"""
Tests for GenericQueryBuilder functionality.
Tests the generic pagination logic with focused unit tests.
"""

import uuid
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from ai.backend.manager.models.gql_relay import ConnectionPaginationOrder
from ai.backend.manager.repositories.types import (
    FilterApplier,
    GenericQueryBuilder,
    ModelConverter,
    OrderingApplier,
    PaginationOptions,
    PaginationQueryResult,
)
from ai.backend.manager.types import OffsetBasedPaginationOptions


class MockFilterApplier(FilterApplier):
    """Mock filter applier for testing"""

    def apply_filters(self, stmt: Any, filters: Any) -> Any:
        return stmt


class MockOrderingApplier(OrderingApplier):
    """Mock ordering applier for testing"""

    def apply_ordering(self, stmt: Any, ordering: Any) -> tuple[Any, list[tuple[Any, bool]]]:
        order_clauses = []

        if ordering and hasattr(ordering, "order_by"):
            for field_name, desc in ordering.order_by:
                mock_column = MagicMock()
                mock_column.name = field_name
                order_clauses.append((mock_column, desc))

        return stmt, order_clauses


class MockModelConverter(ModelConverter):
    """Mock model converter for testing"""

    def convert_to_data(self, model: Any) -> Any:
        return {
            "id": getattr(model, "id", "test-id"),
            "name": getattr(model, "name", "test"),
            "converted": True,
        }


class TestGenericQueryBuilder:
    """Test cases for GenericQueryBuilder"""

    @pytest.fixture
    def mock_model_class(self):
        """Create mock model class with SQLAlchemy-like attributes"""
        mock_model = MagicMock()
        mock_model.id = MagicMock()
        mock_model.name = MagicMock()
        mock_model.created_at = MagicMock()
        return mock_model

    @pytest.fixture
    def generic_paginator(self, mock_model_class):
        """Create GenericQueryBuilder instance with mock components"""
        return GenericQueryBuilder(
            model_class=mock_model_class,
            filter_applier=MockFilterApplier(),
            ordering_applier=MockOrderingApplier(),
            model_converter=MockModelConverter(),
            cursor_type_name="TestModel",
        )

    def test_paginator_initialization(self, generic_paginator, mock_model_class):
        """Test GenericQueryBuilder initialization"""
        assert generic_paginator.model_class == mock_model_class
        assert isinstance(generic_paginator.filter_applier, MockFilterApplier)
        assert isinstance(generic_paginator.ordering_applier, MockOrderingApplier)
        assert isinstance(generic_paginator.model_converter, MockModelConverter)
        assert generic_paginator.cursor_type_name == "TestModel"

    def test_protocol_compliance(self, generic_paginator):
        """Test that the applier classes properly implement the protocols"""
        # Test filter applier
        filter_applier = generic_paginator.filter_applier
        mock_stmt = MagicMock()
        mock_filters = MagicMock()

        result = filter_applier.apply_filters(mock_stmt, mock_filters)
        assert result == mock_stmt  # Our mock returns the statement as-is

        # Test ordering applier
        ordering_applier = generic_paginator.ordering_applier
        mock_ordering = MagicMock()
        mock_ordering.order_by = [("name", False), ("id", True)]

        stmt_result, order_clauses = ordering_applier.apply_ordering(mock_stmt, mock_ordering)
        assert stmt_result == mock_stmt
        assert len(order_clauses) == 2
        assert not order_clauses[0][1]  # ASC
        assert order_clauses[1][1]  # DESC

        # Test model converter
        model_converter = generic_paginator.model_converter
        mock_model = MagicMock()
        mock_model.id = "test-id"
        mock_model.name = "test-name"

        converted = model_converter.convert_to_data(mock_model)
        assert converted["id"] == "test-id"
        assert converted["name"] == "test-name"
        assert converted["converted"]

    def test_filter_applier_interface(self):
        """Test that FilterApplier interface works correctly"""
        applier = MockFilterApplier()
        mock_stmt = MagicMock()
        mock_filters = {"name": "test"}

        result = applier.apply_filters(mock_stmt, mock_filters)
        assert result == mock_stmt

    def test_ordering_applier_interface(self):
        """Test that OrderingApplier interface works correctly"""
        applier = MockOrderingApplier()
        mock_stmt = MagicMock()

        # Test with no ordering
        stmt, clauses = applier.apply_ordering(mock_stmt, None)
        assert stmt == mock_stmt
        assert clauses == []

        # Test with ordering
        mock_ordering = MagicMock()
        mock_ordering.order_by = [("name", False), ("created_at", True)]

        stmt, clauses = applier.apply_ordering(mock_stmt, mock_ordering)
        assert stmt == mock_stmt
        assert len(clauses) == 2

    def test_model_converter_interface(self):
        """Test that ModelConverter interface works correctly"""
        converter = MockModelConverter()
        mock_model = MagicMock()
        mock_model.id = uuid.uuid4()
        mock_model.name = "test-model"

        result = converter.convert_to_data(mock_model)
        assert result["id"] == mock_model.id
        assert result["name"] == "test-model"
        assert result["converted"]

    @patch("ai.backend.manager.repositories.types.getattr")
    def test_build_lexicographic_cursor_conditions_structure(self, mock_getattr, generic_paginator):
        """Test that cursor condition building has correct structure without SQLAlchemy operations"""
        # Mock getattr to return mock columns that don't perform actual SQL operations
        mock_id_column = MagicMock()
        mock_getattr.return_value = mock_id_column

        # Mock the comparison operations to return mock objects instead of actual SQL
        mock_id_column.__gt__ = MagicMock(return_value=MagicMock())
        mock_id_column.__lt__ = MagicMock(return_value=MagicMock())

        cursor_uuid = uuid.uuid4()

        # Test empty order clauses - forward
        conditions = generic_paginator.build_lexicographic_cursor_conditions(
            order_clauses=[],
            cursor_uuid=cursor_uuid,
            pagination_order=ConnectionPaginationOrder.FORWARD,
        )
        assert len(conditions) == 1
        mock_id_column.__gt__.assert_called_once_with(cursor_uuid)

        # Reset mock
        mock_id_column.__gt__.reset_mock()
        mock_id_column.__lt__.reset_mock()

        # Test empty order clauses - backward
        conditions = generic_paginator.build_lexicographic_cursor_conditions(
            order_clauses=[],
            cursor_uuid=cursor_uuid,
            pagination_order=ConnectionPaginationOrder.BACKWARD,
        )
        assert len(conditions) == 1
        mock_id_column.__lt__.assert_called_once_with(cursor_uuid)

    @patch("ai.backend.manager.repositories.types.getattr")
    @patch("sqlalchemy.select")
    @patch("sqlalchemy.and_")
    @patch("sqlalchemy.or_")
    def test_build_lexicographic_cursor_conditions_with_ordering(
        self, mock_or, mock_and, mock_select, mock_getattr, generic_paginator
    ):
        """Test cursor condition building with order clauses"""
        # Mock getattr to return different columns
        mock_id_column = MagicMock()
        mock_other_column = MagicMock()

        def getattr_side_effect(obj, attr, default=None):
            if attr == "id":
                return mock_id_column
            return mock_other_column

        mock_getattr.side_effect = getattr_side_effect

        # Mock column comparison operations
        for column in [mock_id_column, mock_other_column]:
            column.__gt__ = MagicMock(return_value=MagicMock())
            column.__lt__ = MagicMock(return_value=MagicMock())
            column.__eq__ = MagicMock(return_value=MagicMock())

        # Mock select to return a mock subquery
        mock_select.return_value.where.return_value.scalar_subquery.return_value = MagicMock()

        # Mock and_ to return a mock condition
        mock_and.return_value = MagicMock()

        cursor_uuid = uuid.uuid4()
        order_clauses = [(mock_other_column, False)]  # Order by column ASC

        # Test forward pagination
        conditions = generic_paginator.build_lexicographic_cursor_conditions(
            order_clauses=order_clauses,
            cursor_uuid=cursor_uuid,
            pagination_order=ConnectionPaginationOrder.FORWARD,
        )

        # Should have 2 conditions: one for column comparison, one for ID comparison
        assert len(conditions) == 2

    def test_paginator_attributes_accessible(self, generic_paginator):
        """Test that all paginator attributes are accessible"""
        # Test that we can access all the required attributes
        assert hasattr(generic_paginator, "model_class")
        assert hasattr(generic_paginator, "filter_applier")
        assert hasattr(generic_paginator, "ordering_applier")
        assert hasattr(generic_paginator, "model_converter")
        assert hasattr(generic_paginator, "cursor_type_name")

        # Test that the build method exists
        assert hasattr(generic_paginator, "build_lexicographic_cursor_conditions")
        assert callable(generic_paginator.build_lexicographic_cursor_conditions)

    def test_ordering_applier_returns_correct_structure(self):
        """Test ordering applier returns the expected tuple structure"""
        applier = MockOrderingApplier()
        mock_stmt = MagicMock()
        mock_ordering = MagicMock()
        mock_ordering.order_by = [("field1", True), ("field2", False)]

        stmt, clauses = applier.apply_ordering(mock_stmt, mock_ordering)

        # Verify return structure
        assert stmt is not None
        assert isinstance(clauses, list)
        assert len(clauses) == 2

        # Verify clause structure
        for clause in clauses:
            assert isinstance(clause, tuple)
            assert len(clause) == 2
            # First element should be column-like, second should be boolean
            assert isinstance(clause[1], bool)

    def test_model_converter_handles_various_models(self):
        """Test model converter works with different model structures"""
        converter = MockModelConverter()

        # Test with minimal model
        minimal_model = MagicMock()
        minimal_model.id = "minimal-id"

        result = converter.convert_to_data(minimal_model)
        assert result["id"] == "minimal-id"
        assert result["converted"]

        # Test with rich model
        rich_model = MagicMock()
        rich_model.id = "rich-id"
        rich_model.name = "rich-name"
        rich_model.description = "rich-description"

        result = converter.convert_to_data(rich_model)
        assert result["id"] == "rich-id"
        assert result["name"] == "rich-name"
        assert result["converted"]

    def test_pagination_order_enum_values(self):
        """Test that pagination order enum values are correct"""
        assert ConnectionPaginationOrder.FORWARD.value == "forward"
        assert ConnectionPaginationOrder.BACKWARD.value == "backward"

    def test_generic_paginator_type_parameters(self, generic_paginator):
        """Test that generic paginator maintains proper typing structure"""
        # This test verifies that the generic typing structure is preserved
        # Even though we can't fully test the generic types at runtime,
        # we can verify the structure is maintained

        assert generic_paginator.model_class is not None
        assert generic_paginator.filter_applier is not None
        assert generic_paginator.ordering_applier is not None
        assert generic_paginator.model_converter is not None

        # Test that the interfaces are properly implemented
        assert hasattr(generic_paginator.filter_applier, "apply_filters")
        assert hasattr(generic_paginator.ordering_applier, "apply_ordering")
        assert hasattr(generic_paginator.model_converter, "convert_to_data")

    @patch("sqlalchemy.select")
    def test_build_pagination_queries_offset_based(self, mock_select, generic_paginator):
        """Test query building for offset-based pagination"""
        # Mock SQLAlchemy select
        mock_stmt = MagicMock()
        mock_select.return_value = mock_stmt

        # Create offset-based pagination
        pagination = PaginationOptions(offset=OffsetBasedPaginationOptions(offset=10, limit=20))

        # Call query building method
        query_result = generic_paginator.build_pagination_queries(pagination=pagination)

        # Verify result structure
        assert isinstance(query_result, PaginationQueryResult)
        assert query_result.data_query is not None
        assert query_result.pagination_order is None  # offset-based doesn't use pagination_order

        # Verify SQLAlchemy methods were called
        mock_select.assert_called()

    def test_convert_rows_to_data_forward(self, generic_paginator):
        """Test row conversion for forward pagination"""
        # Create mock rows
        mock_rows = [MagicMock(), MagicMock(), MagicMock()]
        for i, row in enumerate(mock_rows):
            row.id = f"id-{i}"
            row.name = f"name-{i}"

        # Convert rows
        result = generic_paginator.convert_rows_to_data(
            rows=mock_rows, pagination_order=ConnectionPaginationOrder.FORWARD
        )

        # Verify conversion
        assert len(result) == 3
        assert result[0]["id"] == "id-0"
        assert result[1]["id"] == "id-1"
        assert result[2]["id"] == "id-2"

    def test_convert_rows_to_data_backward(self, generic_paginator):
        """Test row conversion for backward pagination"""
        # Create mock rows
        mock_rows = [MagicMock(), MagicMock(), MagicMock()]
        for i, row in enumerate(mock_rows):
            row.id = f"id-{i}"
            row.name = f"name-{i}"

        # Convert rows with backward pagination
        result = generic_paginator.convert_rows_to_data(
            rows=mock_rows, pagination_order=ConnectionPaginationOrder.BACKWARD
        )

        # Verify order is reversed
        assert len(result) == 3
        assert result[0]["id"] == "id-2"  # Reversed
        assert result[1]["id"] == "id-1"
        assert result[2]["id"] == "id-0"

    def test_pagination_separation_of_concerns(self, generic_paginator):
        """Test that paginator only handles query building, not DB execution"""
        # Verify the paginator doesn't have database-related methods
        assert not hasattr(generic_paginator, "execute")
        assert not hasattr(generic_paginator, "session")
        assert not hasattr(generic_paginator, "db")

        # Verify it has query building methods
        assert hasattr(generic_paginator, "build_pagination_queries")
        assert hasattr(generic_paginator, "convert_rows_to_data")
        assert hasattr(generic_paginator, "build_lexicographic_cursor_conditions")

    @patch("sqlalchemy.select")
    def test_build_pagination_queries_with_filters(self, mock_select, generic_paginator):
        """Test query building with filters applied"""
        mock_stmt = MagicMock()
        mock_select.return_value = mock_stmt

        # Create pagination with filters
        pagination = PaginationOptions(offset=OffsetBasedPaginationOptions(offset=0, limit=10))
        mock_filters = MagicMock()

        # Build queries
        query_result = generic_paginator.build_pagination_queries(
            pagination=pagination, filters=mock_filters
        )

        # Verify result structure
        assert isinstance(query_result, PaginationQueryResult)
        assert query_result.data_query is not None
        assert query_result.pagination_order is None  # offset-based doesn't use pagination_order


class TestGenericQueryBuilderStructure:
    """Test the structure and composition of GenericQueryBuilder"""

    def test_paginator_composition_pattern(self):
        """Test that the paginator follows composition pattern correctly"""
        mock_model = MagicMock()
        filter_applier = MockFilterApplier()
        ordering_applier = MockOrderingApplier()
        model_converter = MockModelConverter()

        paginator = GenericQueryBuilder(
            model_class=mock_model,
            filter_applier=filter_applier,
            ordering_applier=ordering_applier,
            model_converter=model_converter,
            cursor_type_name="CompositionTest",
        )

        # Verify composition
        assert paginator.filter_applier is filter_applier
        assert paginator.ordering_applier is ordering_applier
        assert paginator.model_converter is model_converter
        assert paginator.cursor_type_name == "CompositionTest"

    def test_protocol_interfaces_structure(self):
        """Test that protocol interfaces have correct structure"""
        # Test FilterApplier protocol
        filter_applier = MockFilterApplier()
        assert callable(filter_applier.apply_filters)

        # Test OrderingApplier protocol
        ordering_applier = MockOrderingApplier()
        assert callable(ordering_applier.apply_ordering)

        # Test ModelConverter protocol
        model_converter = MockModelConverter()
        assert callable(model_converter.convert_to_data)

    def test_paginator_can_be_extended(self):
        """Test that paginator can be extended for different model types"""

        # Create specialized appliers
        class SpecialFilterApplier(MockFilterApplier):
            def apply_filters(self, stmt, filters):
                # Specialized filtering logic
                return stmt

        class SpecialOrderingApplier(MockOrderingApplier):
            def apply_ordering(self, stmt, ordering):
                # Specialized ordering logic
                return stmt, []

        class SpecialModelConverter(MockModelConverter):
            def convert_to_data(self, model):
                # Specialized conversion logic
                return {"specialized": True, "id": getattr(model, "id", "special-id")}

        # Create paginator with specialized components
        mock_model = MagicMock()
        paginator = GenericQueryBuilder(
            model_class=mock_model,
            filter_applier=SpecialFilterApplier(),
            ordering_applier=SpecialOrderingApplier(),
            model_converter=SpecialModelConverter(),
            cursor_type_name="Specialized",
        )

        # Test that specialized components work
        mock_model_instance = MagicMock()
        mock_model_instance.id = "special-test-id"

        result = paginator.model_converter.convert_to_data(mock_model_instance)
        assert result["specialized"]
        assert result["id"] == "special-test-id"
