# Manager GraphQL API (Strawberry)

← [Back to Manager API](../README.md)

## Overview

Manager GraphQL API is a GraphQL interface built using the Strawberry framework.

## Architecture

```
┌──────────────────────────────────────────┐
│      Client (Web UI/SDK)                 │
└────────────────┬─────────────────────────┘
                 │
                 ↓ GraphQL Request
┌────────────────────────────────────────────┐
│        GraphQL Schema (Strawberry)         │
│                                            │
│  ┌─────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Query  │  │ Mutation │  │Subscript.│   │
│  └─────────┘  └──────────┘  └──────────┘   │
└────────────────┬───────────────────────────┘
                 │
                 ↓
┌────────────────────────────────────────────┐
│           Resolver Layer                   │
└────────────────┬───────────────────────────┘
                 │
                 ↓
┌────────────────────────────────────────────┐
│         Data Loader Layer                  │
└────────────────┬───────────────────────────┘
                 │
                 ↓
┌────────────────────────────────────────────┐
│       Action Processor Layer               │
└────────────────┬───────────────────────────┘
                 │
                 ↓
┌────────────────────────────────────────────┐
│         Services Layer                     │
└────────────────────────────────────────────┘
```

## Key Principles

### Python Type Hints-Based
Schemas are defined based on Python type hints using the Strawberry framework.

### Using DataLoader
DataLoader is used to solve N+1 query problems.

### Service Layer Invocation
All business logic is processed through the Services Layer.

### Common Error Handling
Raise `BackendAIError` to connect to common error handling middleware.

### Real-time Subscription
Provides real-time updates via WebSocket.

## Schema Reference

For detailed GraphQL schema information, refer to the [GraphQL Reference](../../../../docs/manager/graphql-reference) documentation.

## Related Documentation

- [Manager API Overview](../README.md)
- [Legacy GraphQL (Graphene)](../../models/gql_models/README.md) - DEPRECATED
- [Services Layer](../../services/README.md)
- [Repositories Layer](../../repositories/README.md)

## Migration from Graphene

Currently migrating from Graphene to Strawberry. New features are implemented in Strawberry, and existing Graphene code is gradually migrated.
