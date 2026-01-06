---
# Author: Full name and email of the proposal author
Author: Your Full Name (email@example.com)
# Status: Draft | Accepted | Implemented | Rejected | Superseded
Status: Draft
# Created: Date when this proposal was first created (YYYY-MM-DD)
Created: 2025-01-01
# Created-Version: Backend.AI version when this proposal was created (YY.Sprint.Patch)
Created-Version: 25.1.0
# Target-Version: Expected version for implementation (fill when Accepted)
Target-Version:
# Implemented-Version: Actual version where this was implemented (fill when Implemented)
Implemented-Version:
---

# Title

## Related Issues

- JIRA: BA-XXXX
- GitHub: #XXXX

## Motivation

Why is this change needed? What problem does it solve?

Example:
> Currently, `StringFilter` only supports 4 out of 10 defined filter fields.
> Users expect all filter fields to work, but `starts_with`, `ends_with`, and `not_equals` are silently ignored.
> This causes confusion and unexpected query results.

## Current Design

Describe the current state or design that this proposal aims to change.

Example:
> ```python
> def build_query_condition(
>     self,
>     contains_factory: Callable[[str, bool], QueryCondition],
>     equals_factory: Callable[[str, bool], QueryCondition],
> ) -> Optional[QueryCondition]:
>     # Only 4 fields are handled, others are ignored
> ```

## Proposed Design

Describe the new design or changes being proposed.

Example:
> ```python
> @dataclass
> class StringMatchSpec:
>     value: str
>     case_insensitive: bool = False
>     negated: bool = False
>
> def build_query_condition(
>     self,
>     contains_factory: Callable[[StringMatchSpec], QueryCondition],
>     equals_factory: Callable[[StringMatchSpec], QueryCondition],
>     starts_with_factory: Callable[[StringMatchSpec], QueryCondition],
>     ends_with_factory: Callable[[StringMatchSpec], QueryCondition],
> ) -> Optional[QueryCondition]:
>     # All fields are now handled
> ```

## Migration / Compatibility

Describe backward compatibility considerations and migration plan if applicable.

Example:
> ### Backward Compatibility
> - Existing `build_query_condition()` calls will require updates
> - New factory parameters are required (no default values)
>
> ### Breaking Changes
> - Factory signature changed from `Callable[[str, bool], QueryCondition]` to `Callable[[StringMatchSpec], QueryCondition]`
>
> ### Migration Steps
> 1. Update all adapter implementations to use new `StringMatchSpec`
> 2. Add `starts_with_factory` and `ends_with_factory` to all callers
> 3. Test all filter combinations

## Implementation Plan

Outline the implementation steps and priorities.

Example:
> 1. **Phase 1**: Core changes
>    - Add `StringMatchSpec` dataclass
>    - Update `StringFilter.build_query_condition()` signature
>
> 2. **Phase 2**: Adapter updates
>    - Update `ScalingGroupFilterGQL` adapter
>    - Update other adapters using `StringFilter`
>
> 3. **Phase 3**: Testing
>    - Add unit tests for all filter field combinations
>    - Add integration tests for GraphQL queries

## Open Questions

List any unresolved questions or items that need further discussion.

Example:
> - Should we add `not_contains`, `not_starts_with`, `not_ends_with` fields to `StringFilter`?
> - Should factory parameters be optional with default `None` for backward compatibility?

## References

- Link to related documents, discussions, or external resources

Example:
> - [BEP-1010: New GQL](BEP-1010-new-gql.md)
> - [Strawberry GraphQL Documentation](https://strawberry.rocks/)
