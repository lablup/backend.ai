---
Author: HyeokJin Kim (hyeokjin@lablup.com)
Status: Implemented
Created: 2026-01-06
Created-Version: 26.1.0
Target-Version: 26.1.0
Implemented-Version: 26.1.0
---

# GQL StringFilter Enhancement

## Related Issues

- JIRA: BA-3640

## Motivation

The `StringFilter` GraphQL input type should provide a complete set of string matching operations:

| Operation | Basic | Case-insensitive | NOT | Case-insensitive NOT |
|-----------|-------|------------------|-----|---------------------|
| equals | `equals` | `iEquals` | `notEquals` | `iNotEquals` |
| contains | `contains` | `iContains` | `notContains` | `iNotContains` |
| starts_with | `startsWith` | `iStartsWith` | `notStartsWith` | `iNotStartsWith` |
| ends_with | `endsWith` | `iEndsWith` | `notEndsWith` | `iNotEndsWith` |

**Total: 16 filter fields**

However, the previous `build_query_condition()` method only implemented **4 of these fields**:
- `equals`, `iEquals`
- `contains`, `iContains`

The remaining fields were silently ignored, causing confusion and unexpected behavior.

## Current Design (Before Enhancement)

```python
@strawberry.input
class StringFilter:
    contains: Optional[str] = None
    starts_with: Optional[str] = None
    ends_with: Optional[str] = None
    equals: Optional[str] = None
    not_equals: Optional[str] = None

    i_contains: Optional[str] = strawberry.field(name="iContains", default=None)
    i_starts_with: Optional[str] = strawberry.field(name="iStartsWith", default=None)
    i_ends_with: Optional[str] = strawberry.field(name="iEndsWith", default=None)
    i_equals: Optional[str] = strawberry.field(name="iEquals", default=None)
    i_not_equals: Optional[str] = strawberry.field(name="iNotEquals", default=None)

    def build_query_condition(
        self,
        contains_factory: Callable[[str, bool], QueryCondition],
        equals_factory: Callable[[str, bool], QueryCondition],
    ) -> Optional[QueryCondition]:
        # Only 4 fields are handled, others are silently ignored
        if self.equals:
            return equals_factory(self.equals, False)
        if self.i_equals:
            return equals_factory(self.i_equals, True)
        if self.contains:
            return contains_factory(self.contains, False)
        if self.i_contains:
            return contains_factory(self.i_contains, True)
        return None
```

### Problems

1. **Silent failure**: Most filter fields are ignored without any error or warning
2. **Incomplete API**: Users cannot use `starts_with`, `ends_with`, or any negation operations
3. **Missing NOT variants**: No `not_contains`, `not_starts_with`, `not_ends_with` fields
4. **Factory signature limitation**: Current factory signature `Callable[[str, bool], QueryCondition]` cannot express negation

## Proposed Design

### StringMatchSpec Dataclass

Introduce a dataclass to encapsulate match parameters:

```python
@dataclass(frozen=True)
class StringMatchSpec:
    """Specification for string matching operations."""
    value: str
    case_insensitive: bool
    negated: bool
```

All fields are required with no defaults to ensure explicit specification of matching behavior.

### Updated Factory Signature

Change factory parameters to use `StringMatchSpec`:

```python
def build_query_condition(
    self,
    contains_factory: Callable[[StringMatchSpec], QueryCondition],
    equals_factory: Callable[[StringMatchSpec], QueryCondition],
    starts_with_factory: Callable[[StringMatchSpec], QueryCondition],
    ends_with_factory: Callable[[StringMatchSpec], QueryCondition],
) -> Optional[QueryCondition]:
    """Build a query condition from this filter using the provided factory callables.

    Args:
        contains_factory: Factory for LIKE '%value%' operations
        equals_factory: Factory for exact match (=) operations
        starts_with_factory: Factory for LIKE 'value%' operations
        ends_with_factory: Factory for LIKE '%value' operations

    Returns:
        QueryCondition if any filter field is set, None otherwise
    """
    # equals operations
    if self.equals:
        return equals_factory(
            StringMatchSpec(self.equals, case_insensitive=False, negated=False)
        )
    if self.i_equals:
        return equals_factory(
            StringMatchSpec(self.i_equals, case_insensitive=True, negated=False)
        )
    if self.not_equals:
        return equals_factory(
            StringMatchSpec(self.not_equals, case_insensitive=False, negated=True)
        )
    if self.i_not_equals:
        return equals_factory(
            StringMatchSpec(self.i_not_equals, case_insensitive=True, negated=True)
        )

    # contains operations
    if self.contains:
        return contains_factory(
            StringMatchSpec(self.contains, case_insensitive=False, negated=False)
        )
    if self.i_contains:
        return contains_factory(
            StringMatchSpec(self.i_contains, case_insensitive=True, negated=False)
        )
    if self.not_contains:
        return contains_factory(
            StringMatchSpec(self.not_contains, case_insensitive=False, negated=True)
        )
    if self.i_not_contains:
        return contains_factory(
            StringMatchSpec(self.i_not_contains, case_insensitive=True, negated=True)
        )

    # starts_with operations
    if self.starts_with:
        return starts_with_factory(
            StringMatchSpec(self.starts_with, case_insensitive=False, negated=False)
        )
    if self.i_starts_with:
        return starts_with_factory(
            StringMatchSpec(self.i_starts_with, case_insensitive=True, negated=False)
        )
    if self.not_starts_with:
        return starts_with_factory(
            StringMatchSpec(self.not_starts_with, case_insensitive=False, negated=True)
        )
    if self.i_not_starts_with:
        return starts_with_factory(
            StringMatchSpec(self.i_not_starts_with, case_insensitive=True, negated=True)
        )

    # ends_with operations
    if self.ends_with:
        return ends_with_factory(
            StringMatchSpec(self.ends_with, case_insensitive=False, negated=False)
        )
    if self.i_ends_with:
        return ends_with_factory(
            StringMatchSpec(self.i_ends_with, case_insensitive=True, negated=False)
        )
    if self.not_ends_with:
        return ends_with_factory(
            StringMatchSpec(self.not_ends_with, case_insensitive=False, negated=True)
        )
    if self.i_not_ends_with:
        return ends_with_factory(
            StringMatchSpec(self.i_not_ends_with, case_insensitive=True, negated=True)
        )

    return None
```

### Example Adapter Implementation

```python
class ScalingGroupFilterAdapter:
    @staticmethod
    def build_name_filter(spec: StringMatchSpec) -> QueryCondition:
        column = ScalingGroupRow.name
        if spec.case_insensitive:
            column = sa.func.lower(column)
            value = spec.value.lower()
        else:
            value = spec.value

        condition = column == value
        if spec.negated:
            condition = sa.not_(condition)
        return condition

    @staticmethod
    def build_name_contains_filter(spec: StringMatchSpec) -> QueryCondition:
        column = ScalingGroupRow.name
        if spec.case_insensitive:
            condition = column.ilike(f"%{spec.value}%")
        else:
            condition = column.like(f"%{spec.value}%")

        if spec.negated:
            condition = sa.not_(condition)
        return condition

    @staticmethod
    def build_name_starts_with_filter(spec: StringMatchSpec) -> QueryCondition:
        column = ScalingGroupRow.name
        if spec.case_insensitive:
            condition = column.ilike(f"{spec.value}%")
        else:
            condition = column.like(f"{spec.value}%")

        if spec.negated:
            condition = sa.not_(condition)
        return condition

    @staticmethod
    def build_name_ends_with_filter(spec: StringMatchSpec) -> QueryCondition:
        column = ScalingGroupRow.name
        if spec.case_insensitive:
            condition = column.ilike(f"%{spec.value}")
        else:
            condition = column.like(f"%{spec.value}")

        if spec.negated:
            condition = sa.not_(condition)
        return condition
```

## Migration / Compatibility

### Breaking Changes

1. **Factory signature change**: `Callable[[str, bool], QueryCondition]` → `Callable[[StringMatchSpec], QueryCondition]`
2. **New required parameters**: `starts_with_factory` and `ends_with_factory` are required

### Backward Compatibility

- All existing filter fields remain available with the same GraphQL names
- No changes to GraphQL schema or client-facing API

### Migration Steps

1. Add `StringMatchSpec` dataclass to `ai.backend.manager.api.gql.base`
2. Update `StringFilter.build_query_condition()` signature
3. Update all adapter implementations that use `build_query_condition()`
4. Add unit tests for all filter field combinations

## Implementation Plan

### Phase 1: Core Changes
- Add `StringMatchSpec` dataclass
- Update `StringFilter.build_query_condition()` method signature and implementation

### Phase 2: Adapter Updates
- Update `ScalingGroupFilterGQL` adapter
- Update other adapters using `StringFilter` (search codebase for usages)

### Phase 3: Testing
- Add unit tests for all 16 filter fields
- Add unit tests for negation operations
- Add integration tests for GraphQL queries

## Design Decisions

### Complete NOT Variants

We decided to add all NOT variants (not_contains, i_not_contains, not_starts_with, i_not_starts_with, not_ends_with, i_not_ends_with) to provide complete negation coverage:

- **Consistency**: All 4 operations (equals, contains, starts_with, ends_with) now have the same 4 variants (basic, case-insensitive, NOT, case-insensitive NOT)
- **API completeness**: Users can perform any combination of string matching without workarounds
- **Future-proof**: No need to add more fields later

### No Default Values in StringMatchSpec

`StringMatchSpec` requires all fields explicitly:
- `value: str` - the search value
- `case_insensitive: bool` - whether to ignore case
- `negated: bool` - whether to negate the condition

This design ensures that calling code explicitly specifies all matching behavior, reducing bugs from incorrect defaults.

## References

- [BEP-1010: New GQL](BEP-1010-new-gql.md)
- [Strawberry GraphQL Documentation](https://strawberry.rocks/)
