# Legacy GraphQL (Graphene) - DEPRECATED

← [Back to Manager](../../README.md)

## ⚠️ DEPRECATED

**This GraphQL implementation is no longer in use.**

New GraphQL endpoint development should use the **Strawberry**-based [New GraphQL API](../../api/gql/README.md).

This directory provides only some Graphene-based endpoints for backward compatibility and is gradually being migrated to Strawberry.

## Developer Guide

### Developing New Endpoints

**❌ Don't:**
- Add new types or queries with Graphene
- Create new files in `models/gql_models/`

**✅ Do:**
- Define new types with Strawberry
- Create new files in `api/gql/`
- Refer to [Strawberry Documentation](../../api/gql/README.md)

### Modifying Existing Endpoints

If you need to modify existing Graphene endpoints:

1. **Urgent bug fixes**: Direct modification of Graphene code is acceptable
2. **Feature additions/changes**: Migrate to Strawberry first, then work on it

## Related Documentation

- **[Strawberry GraphQL API](../../api/gql/README.md)** - New GraphQL API implementation
- **[Manager Overview](../../README.md)** - Manager component architecture
