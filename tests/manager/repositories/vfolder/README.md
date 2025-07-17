# VFolder Repository Layer Test Strategy

## Overview

This document outlines the testing strategy for the VFolder repository layer, which provides data access abstraction for VFolder operations in Backend.AI.

## Repository Layer Architecture

The VFolder repository layer consists of two main components:

1. **VfolderRepository**: Handles regular user operations with permission validation
2. **AdminVfolderRepository**: Provides admin-only operations bypassing standard validations

## Testing Approach

### 1. Unit Testing Strategy

#### Mocking Strategy
- **Database Engine**: Mock `ExtendedAsyncSAEngine` to avoid actual database connections
- **SQLAlchemy Session**: Use `AsyncMock` to simulate database sessions
- **Model Objects**: Mock `VFolderRow`, `UserRow`, and other model objects
- **Query Results**: Mock query execution results and row objects

#### Test Coverage Areas

##### VfolderRepository Tests (`test_vfolder_repository.py`)
- **Read Operations**:
  - `get_by_id_validated`: Tests permission validation and access control
  - `get_by_id`: Tests basic retrieval without validation
  - `list_accessible_vfolders`: Tests filtering based on user permissions
  
- **Write Operations**:
  - `create_vfolder`: Tests basic vfolder creation
  - `create_vfolder_with_permission`: Tests creation with owner permission setup
  - `update_vfolder_attribute`: Tests attribute modification
  
- **Permission Management**:
  - `get_vfolder_permissions`: Tests permission retrieval
  - Access control validation in various methods

##### AdminVfolderRepository Tests (`test_admin_vfolder_repository.py`)
- **Force Operations** (bypass validation):
  - `get_by_id_force`: Admin retrieval without permission checks
  - `update_vfolder_status_force`: Direct status updates
  - `delete_vfolder_force`: Hard deletion
  - `update_vfolder_attribute_force`: Unrestricted updates
  - `move_vfolders_to_trash_force`: Batch trash operations

### 2. Scenario-Based Testing (`test_vfolder_scenarios.py`)

Tests based on the business scenarios from `test_scenarios/vfolder.md`:

#### Creation Scenarios
- **1.1 Personal VFolder**: User-owned storage with quota
- **1.2 Project VFolder**: Group-owned shared storage
- **1.3 Model Storage**: Read-only model repository
- **1.6 Unmanaged VFolder**: External path mounting (admin only)

#### Management Scenarios
- **Move to Trash**: Soft deletion with status updates
- **Permission Management**: Owner and shared access control
- **Quota Handling**: QuotaScopeID management

### 3. Key Testing Patterns

#### Repository Method Pattern
```python
@pytest.mark.asyncio
async def test_repository_method(repository, mock_db_engine):
    # Given - Setup mocks
    mock_session = AsyncMock(spec=AsyncSession)
    mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session
    
    # Mock internal methods
    with patch.object(repository, "_get_vfolder_by_id", return_value=mock_row):
        with patch.object(repository, "_vfolder_row_to_data", return_value=expected_data):
            # When - Execute method
            result = await repository.method_under_test(params)
            
            # Then - Assert results
            assert result == expected_data
```

#### Permission Validation Pattern
```python
# Test allowed access
with patch("query_accessible_vfolders", return_value=[vfolder_dict]):
    result = await repository.get_by_id_validated(vfolder_id, user_id, domain)
    assert result is not None

# Test denied access
with patch("query_accessible_vfolders", return_value=[]):
    with pytest.raises(VFolderNotFound):
        await repository.get_by_id_validated(vfolder_id, user_id, domain)
```

### 4. Mock Data Fixtures

#### Standard Fixtures
- `mock_db_engine`: Database engine mock
- `sample_vfolder_row`: Standard VFolder model mock
- `sample_user_row`: User model mock
- Repository instances with mocked dependencies

#### Data Consistency
- Ensure mocked data follows actual model constraints
- Use realistic UUIDs and QuotaScopeIDs
- Maintain proper relationships between entities

### 5. Error Testing

#### Exception Scenarios
- **VFolderNotFound**: Non-existent or inaccessible vfolders
- **Database Errors**: Connection and transaction failures
- **Permission Errors**: Unauthorized access attempts

### 6. Integration Considerations

While these are unit tests, they should:
- Reflect actual database schema constraints
- Follow the same transaction patterns as production
- Test the repository decorator behavior
- Ensure proper session management

## Running the Tests

```bash
# Run all repository tests
pants test tests/repositories/vfolder::

# Run specific test file
pants test tests/repositories/vfolder/test_vfolder_repository.py

# Run with coverage
pants test --test-use-coverage tests/repositories/vfolder::
```

## Best Practices

1. **Isolation**: Each test should be completely independent
2. **Clarity**: Test names should clearly describe the scenario
3. **Completeness**: Test both success and failure paths
4. **Maintainability**: Use fixtures and helpers to reduce duplication
5. **Documentation**: Comment complex test setups and assertions

## Future Enhancements

1. **Performance Testing**: Add tests for query optimization
2. **Concurrency Testing**: Test transaction isolation and race conditions
3. **Migration Testing**: Ensure repository compatibility across schema changes
4. **Metric Testing**: Verify repository decorator metrics collection