# Consolidate admin_repository into repository

## Overview

This document tracks the consolidation of `admin_repository.py` into `repository.py` across 7 domains to eliminate code duplication and maintain a single source of truth for business logic.

## Affected Domains

1. container_registry (lowest duplication - pilot domain)
2. session (low duplication)
3. image (medium duplication)
4. group (high duplication)
5. model_serving (medium-high duplication)
6. user (high duplication)
7. domain (highest duplication)

## Unified Architecture Pattern

### Design Principles

1. **Single Source of Truth**: All business logic lives in one place
2. **Permission Parameterization**: Use `skip_permission_check: bool = False` to control validation
3. **Composition Over Duplication**: Reuse validated methods within force methods
4. **Backward Compatibility**: Maintain existing method signatures during transition

### Method Naming Convention

Instead of separate `*_validated` and `*_force` methods, we'll use:

```python
# Unified method signature
async def operation_name(
    self,
    # ... business parameters
    skip_permission_check: bool = False,  # New parameter
) -> ReturnType:
    """
    Performs the operation with optional permission checking.

    Args:
        skip_permission_check: If True, bypasses permission validation (superadmin only)
    """
    if not skip_permission_check:
        # Permission validation logic
        await self._validate_permissions(...)

    # Core business logic (shared for both paths)
    ...
```

### Transitional Approach

To maintain backward compatibility during migration:

1. **Phase 1 - Consolidate**: Move all methods to unified repository
2. **Phase 2 - Add Adapters**: Keep `*_validated` and `*_force` as thin wrappers
3. **Phase 3 - Update Services**: Services call unified methods directly
4. **Phase 4 - Remove Wrappers**: Clean up adapter methods

Example transition:

```python
class DomainRepository:
    # New unified method
    async def create_domain(
        self,
        creator: Creator[DomainRow],
        skip_permission_check: bool = False,
    ) -> DomainData:
        if not skip_permission_check:
            # Validate permissions
            await self._validate_domain_creation_permissions(...)

        # Core business logic
        ...

    # Backward compatible wrappers (will be removed in Phase 4)
    async def create_domain_validated(
        self, creator: Creator[DomainRow]
    ) -> DomainData:
        return await self.create_domain(creator, skip_permission_check=False)

    async def create_domain_force(
        self, creator: Creator[DomainRow]
    ) -> DomainData:
        return await self.create_domain(creator, skip_permission_check=True)
```

### Repository Wiring Changes

**Before:**
```python
@dataclass
class DomainRepositories:
    repository: DomainRepository
    admin_repository: AdminDomainRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        repository = DomainRepository(args.db)
        admin_repository = AdminDomainRepository(args.db)
        return cls(repository=repository, admin_repository=admin_repository)
```

**After:**
```python
@dataclass
class DomainRepositories:
    repository: DomainRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        repository = DomainRepository(args.db)
        return cls(repository=repository)
```

### Service Layer Changes

**Before:**
```python
class DomainService:
    _repository: DomainRepository
    _admin_repository: AdminDomainRepository

    async def create_domain(self, action: CreateDomainAction):
        if action.user_info.role == UserRole.SUPERADMIN:
            return await self._admin_repository.create_domain_force(...)
        else:
            return await self._repository.create_domain_validated(...)
```

**After (Phase 3):**
```python
class DomainService:
    _repository: DomainRepository

    async def create_domain(self, action: CreateDomainAction):
        skip_permission_check = action.user_info.role == UserRole.SUPERADMIN
        return await self._repository.create_domain(
            ...,
            skip_permission_check=skip_permission_check,
        )
```

## Implementation Order

### Priority 1: Low Duplication Domains (Pilot)

1. **container_registry** - Uses composition pattern already (~5% duplication)
   - 4 methods to consolidate
   - Serves as proof of concept

2. **session** - Minimal admin operations (~10% duplication)
   - Few methods to consolidate
   - Simple permission checks

### Priority 2: Medium Duplication Domains

3. **image** - Admin wraps operations (~20% duplication)
   - Moderate complexity

4. **group** - Complex deletion logic (~40% duplication)
   - Requires careful testing

5. **model_serving** - Duplicated getters (~50% duplication)
   - Many endpoint operations

### Priority 3: High Duplication Domains

6. **user** - Shared helpers via composition (~30% duplication)
   - Complex business logic
   - Many helper methods

7. **domain** - Highest verbatim duplication (~60% duplication)
   - Most complex consolidation
   - Many duplicated helpers

## Test Strategy

### Existing Test Coverage

- **domain**: 15 tests (test_admin_repository.py, test_domain.py)
- **group**: 9 tests (test_admin_repository.py) - **Need more tests**
- **user**: 17 tests (test_user_repository.py)
- **session**: **No dedicated tests** - **Need tests**
- **image**: **No dedicated tests** - **Need tests**
- **model_serving**: 24 tests (test_admin_repository.py)
- **container_registry**: 21 tests (test_container_registry_repository.py)

### Testing Approach

For each domain consolidation:

1. **Before Consolidation**: Run existing tests to establish baseline
2. **During Consolidation**:
   - Keep all existing test files
   - Tests should pass with backward-compatible wrappers
3. **After Consolidation**:
   - Add tests for new unified methods
   - Verify both `skip_permission_check=True` and `False` paths
4. **Service Integration**: Run service-level tests to ensure integration works

### Test Migration

- Merge `test_admin_repository.py` tests into `test_repository.py`
- Update test fixtures in `conftest.py` to use unified repository
- Ensure tests cover both permission paths

## Helper Method Consolidation

### Common Patterns

Many helper methods are duplicated across repository.py and admin_repository.py:

```python
# Instead of duplicating in both files
class DomainRepository:
    async def _get_domain_user_count(self, conn: SAConnection, domain_name: str) -> int:
        """Shared helper - used by both validated and force operations"""
        query = sa.select([sa.func.count()]).select_from(users).where(...)
        return await conn.scalar(query)

    async def _domain_has_active_kernels(self, conn: SAConnection, domain_name: str) -> bool:
        """Shared helper - used by both validated and force operations"""
        query = sa.select([sa.func.count()]).select_from(kernels).where(...)
        return await conn.scalar(query) > 0
```

### Helper Categories

1. **Getters** (`_get_*_by_*`) - Move to unified repository
2. **Validators** (`_check_*`, `_validate_*`) - Move to unified repository
3. **Deleters** (`_delete_*`) - Move to unified repository
4. **Business Logic** (`_create_*`, `_update_*`) - Move to unified repository

## File Changes Per Domain

### container_registry (Pilot)

**Files to modify:**
- `src/ai/backend/manager/repositories/container_registry/repository.py` - Add consolidated methods
- `src/ai/backend/manager/repositories/container_registry/admin_repository.py` - Remove (delegation only)
- `src/ai/backend/manager/repositories/container_registry/repositories.py` - Remove admin_repository field
- `src/ai/backend/manager/services/container_registry/*.py` - Update imports

**Files to delete (after service migration):**
- `src/ai/backend/manager/repositories/container_registry/admin_repository.py`

### Repeat for Other Domains

Similar pattern for: session, image, group, model_serving, user, domain

## Migration Checklist (Per Domain)

- [ ] Read and understand both repository.py and admin_repository.py
- [ ] Identify duplicated helper methods
- [ ] Run existing tests to establish baseline
- [ ] Consolidate helper methods into repository.py
- [ ] Add `skip_permission_check` parameter to methods
- [ ] Keep backward-compatible `*_validated` and `*_force` wrappers
- [ ] Run tests to verify backward compatibility
- [ ] Update service layer to use unified methods
- [ ] Update repositories.py wiring
- [ ] Remove `*_validated` and `*_force` wrappers
- [ ] Delete admin_repository.py file
- [ ] Update test files (merge test_admin_repository.py into test_repository.py)
- [ ] Run all tests to verify consolidation

## Current Status

### Completed
- ✅ Analysis of existing architecture
- ✅ Design of unified repository pattern
- ✅ Test coverage assessment

### In Progress
- 🔄 Implementation planning

### Pending
- ⏳ container_registry consolidation (pilot)
- ⏳ session consolidation
- ⏳ image consolidation
- ⏳ group consolidation
- ⏳ model_serving consolidation
- ⏳ user consolidation
- ⏳ domain consolidation
- ⏳ Service layer updates
- ⏳ Processors.py wiring updates
- ⏳ Final test suite run

## Notes

- Start with container_registry as it already uses composition pattern
- The `skip_permission_check` parameter is more explicit than having separate method names
- Backward-compatible wrappers prevent breaking changes during migration
- Services can be updated gradually (Phase 3)
- Test infrastructure should validate both permission paths

## Related Issues

- Group domain needs additional regression tests before consolidation
- Session and Image domains lack dedicated repository tests
