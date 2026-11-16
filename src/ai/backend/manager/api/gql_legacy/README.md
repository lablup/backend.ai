# Legacy GraphQL (Graphene) - DEPRECATED

← [Back to Manager](../../README.md)

## ⚠️ DEPRECATED

**This GraphQL implementation is no longer in use.**

New GraphQL endpoint development should use the [Strawberry GraphQL API](../../api/gql/README.md).

This directory provides only some Graphene-based endpoints for backward compatibility and is gradually being migrated to Strawberry.

## Developer Guide

### Developing New Endpoints

**❌ Do not:**
- Add new types or queries with Graphene
- Create new files in `api/gql_legacy/`

**✅ Do:**
- Define new types with Strawberry
- Create new files in `api/gql/`
- See [Strawberry documentation](../../api/gql/README.md)

### Modifying Existing Endpoints

If you need to modify existing Graphene endpoints:

1. **Urgent defect fixes**: Modify Graphene code directly.
2. **Feature additions and changes**: Migrate to Strawberry first, then make the change.

## Related documents

- **[Strawberry GraphQL API](../../api/gql/README.md)** - New GraphQL API implementation
- **[Manager Overview](../../README.md)** - the manager component architecture
