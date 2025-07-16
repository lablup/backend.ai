import pytest
from dataclasses import dataclass
from unittest.mock import MagicMock

from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.image.repositories import RepositoryArgs
from ai.backend.manager.repositories.metric.repositories import MetricRepositories
from ai.backend.manager.repositories.metric.repository import MetricRepository


class TestMetricRepositories:
    @pytest.fixture
    def mock_db(self):
        """Mock database engine for testing."""
        return MagicMock(spec=ExtendedAsyncSAEngine)

    @pytest.fixture
    def repository_args(self, mock_db):
        """Create RepositoryArgs for testing."""
        return RepositoryArgs(db=mock_db)

    def test_create(self, repository_args):
        """Test MetricRepositories.create() factory method."""
        repositories = MetricRepositories.create(repository_args)
        
        assert isinstance(repositories, MetricRepositories)
        assert isinstance(repositories.repository, MetricRepository)
        assert repositories.repository._db is repository_args.db

    def test_dataclass_structure(self, repository_args):
        """Test that MetricRepositories is a proper dataclass."""
        repositories = MetricRepositories.create(repository_args)
        
        # Check dataclass features
        assert hasattr(repositories, '__dataclass_fields__')
        assert 'repository' in repositories.__dataclass_fields__
        
        # Check field types
        from dataclasses import fields
        field_info = {f.name: f.type for f in fields(MetricRepositories)}
        assert field_info['repository'] == MetricRepository

    def test_multiple_create_calls(self, repository_args):
        """Test that multiple create calls produce independent instances."""
        repos1 = MetricRepositories.create(repository_args)
        repos2 = MetricRepositories.create(repository_args)
        
        assert repos1 is not repos2
        assert repos1.repository is not repos2.repository
        assert repos1.repository._db is repos2.repository._db  # Same DB reference

    def test_direct_instantiation(self, mock_db):
        """Test direct instantiation of MetricRepositories."""
        metric_repo = MetricRepository(mock_db)
        repositories = MetricRepositories(repository=metric_repo)
        
        assert repositories.repository is metric_repo
        assert repositories.repository._db is mock_db

    def test_repository_args_validation(self, mock_db):
        """Test that RepositoryArgs is properly used."""
        # Create custom RepositoryArgs to ensure it's being used correctly
        args = RepositoryArgs(db=mock_db)
        
        repositories = MetricRepositories.create(args)
        
        # The created repository should use the db from args
        assert repositories.repository._db is args.db

    def test_integration_with_repository_pattern(self, repository_args):
        """Test that MetricRepositories follows the repository pattern used in other domains."""
        repositories = MetricRepositories.create(repository_args)
        
        # Check that it has the expected structure
        assert hasattr(repositories, 'repository')
        
        # The repository should be ready to use
        assert repositories.repository is not None
        assert isinstance(repositories.repository, MetricRepository)