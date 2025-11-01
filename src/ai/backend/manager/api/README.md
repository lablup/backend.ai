# Manager REST API Entry Points

← [Back to Manager](../README.md)

## Overview

Manager REST API provides Backend.AI's main HTTP-based API endpoints. Built on the Starlette web framework, it offers various features including session creation, virtual folder management, and user management.

## Architecture

```
┌──────────────────────────────────────────┐
│         Client (SDK/CLI/Web UI)          │
└────────────────┬─────────────────────────┘
                 │
                 ↓ HTTP Request
┌────────────────────────────────────────────┐
│            REST API Handler                │
│         (Starlette Routes)                 │
│                                            │
│  - session.py (session creation/mgmt)      │
│  - vfolder.py (virtual folders)            │
│  - admin.py (admin tasks)                  │
│  - auth.py (authentication)                │
│  - scaling_group.py (scaling groups)       │
│  - ... (other endpoints)                   │
└────────────────┬───────────────────────────┘
                 │
                 ↓
┌────────────────────────────────────────────┐
│           Middleware Stack                 │
│                                            │
│  1. Authentication Middleware              │
│  2. Rate Limiting Middleware               │
│  3. Request Validation                     │
│  4. Error Handling Middleware              │
│  5. Metric Collection                      │
└────────────────┬───────────────────────────┘
                 │
                 ↓
┌────────────────────────────────────────────┐
│         Action Processor Layer             │
│                                            │
│  - Authorization (RBAC)                    │
│  - Action Validation                       │
│  - Audit Logging                           │
│  - Monitoring                              │
└────────────────┬───────────────────────────┘
                 │
                 ↓
┌────────────────────────────────────────────┐
│           Services Layer                   │
│                                            │
│  - Business Logic                          │
│  - External Service Orchestration          │
│  - Quota/Limit Enforcement                 │
└────────────────┬───────────────────────────┘
                 │
                 ↓
┌────────────────────────────────────────────┐
│         Repositories Layer                 │
│                                            │
│  - Data Access                             │
│  - Transaction Management                  │
└────────────────────────────────────────────┘
```

## Middleware Stack

### 1. Authentication Middleware

Handles authentication for API handlers with `@auth_required` decorator.

**Supported Authentication Methods:**
- **HMAC-SHA256 signature** (`Authorization` header)
- **JWT token** (`X-Backendai-Token` header)

### 2. Error Handling Middleware

Converts exceptions to appropriate HTTP responses.

## Actions Layer Integration

REST API handlers and GraphQL handlers invoke Action Processor to execute business logic.

**Handler Responsibilities:**
- Only handles HTTP request/response data conversion
- Creates Action objects and invokes Processor
- Does not implement business logic directly

See [Actions Layer Documentation](../actions/README.md) for details.

## Error Handling

Exceptions from each layer are converted to appropriate HTTP responses via Error Handling Middleware.

## Related Documentation

- [GraphQL API](./gql/README.md) - GraphQL endpoints
- [Actions Layer](../actions/README.md) - Action Processor details
- [Services Layer](../services/README.md) - Business logic
- [Event Stream API](./events.py) - Server-Sent Events
