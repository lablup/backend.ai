import pytest
from unittest.mock import MagicMock

from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.metric.repository import MetricRepository


class TestMetricRepository:
    @pytest.fixture
    def mock_db(self):
        """Mock database engine for testing."""
        return MagicMock(spec=ExtendedAsyncSAEngine)

    def test_init(self, mock_db):
        """Test MetricRepository initialization."""
        repository = MetricRepository(mock_db)
        
        assert repository._db is mock_db
        assert hasattr(repository, '_db')
        assert isinstance(repository._db, ExtendedAsyncSAEngine)

    def test_repository_decorator_exists(self):
        """Test that repository decorator is properly defined."""
        from ai.backend.manager.repositories.metric.repository import repository_decorator
        
        assert repository_decorator is not None
        assert callable(repository_decorator)

    def test_repository_structure(self, mock_db):
        """Test the basic structure of MetricRepository."""
        repository = MetricRepository(mock_db)
        
        # Check that it's a proper class instance
        assert isinstance(repository, MetricRepository)
        
        # Check that the class follows the repository pattern
        assert hasattr(repository, '__init__')
        assert hasattr(repository, '_db')

    def test_multiple_instances(self, mock_db):
        """Test creating multiple repository instances."""
        repo1 = MetricRepository(mock_db)
        repo2 = MetricRepository(mock_db)
        
        # Each instance should be independent
        assert repo1 is not repo2
        assert repo1._db is repo2._db  # But they share the same db reference

    def test_inheritance_compatibility(self):
        """Test that MetricRepository can be properly subclassed if needed."""
        class ExtendedMetricRepository(MetricRepository):
            def custom_method(self):
                return "custom"
        
        mock_db = MagicMock(spec=ExtendedAsyncSAEngine)
        extended_repo = ExtendedMetricRepository(mock_db)
        
        assert isinstance(extended_repo, MetricRepository)
        assert hasattr(extended_repo, 'custom_method')
        assert extended_repo.custom_method() == "custom"