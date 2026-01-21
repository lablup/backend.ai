---
Author: BoKeum Kim (bkkim@lablup.com)
Status: Draft
Created: 2026-01-21
Created-Version: 26.1.0
Target-Version: 26.1.0
Implemented-Version:
---

# BEP-1036: Add GraphQL Endpoint Without Authentication

## Motivation

Currently, all GraphQL endpoints in Backend.AI require authentication. However, there is a need for unauthenticated endpoints to:

1. **Health Check & Status Verification**: Verify that the entire GraphQL Federation stack (Web Server, Hive Gateway, Manager) is operational without requiring user credentials.
2. **Client Connectivity Testing**: Allow CLI tools and Web UI to verify connectivity to the Backend.AI API before attempting authentication.
3. **Service Discovery**: Enable clients to discover available services and capabilities without authentication.
4. **Monitoring & Observability**: Allow external monitoring systems to check service health without managing authentication credentials.

The current architecture requires authentication at multiple layers:
- **Manager**: `CustomGraphQLView` sets `auth_required=True` and checks `request.get("is_authorized", False)`
- **Webserver**: Uses `web_handler_with_jwt` which generates JWT tokens from authenticated sessions
- **Hive Gateway**: Forwards authentication headers to subgraphs

This makes it impossible to verify end-to-end connectivity without valid credentials.

## Current Design

### Endpoints

- `POST /admin/graphql` - Legacy Graphene endpoint (authenticated)
- `POST /admin/gql` - Graphene endpoint (authenticated)
- `GET/POST /admin/gql/strawberry` - Strawberry endpoint (authenticated)

### Data Flow (Current)

There are two access patterns:

**1. CLI → Manager (Direct)**
```
┌─────────┐         ┌─────────────┐
│   CLI   │────────►│   Manager   │
│ (HMAC)  │         │ (Auth Check)│
└─────────┘         └─────────────┘
```

**2. Web UI → Webserver → Hive Gateway → Manager**
```
┌─────────┐    ┌───────────┐    ┌──────────────┐    ┌─────────────┐
│ Web UI  │───►│ Webserver │───►│ Hive Gateway │───►│   Manager   │
│         │    │ (JWT Auth)│    │ (Federation) │    │ (Auth Check)│
└─────────┘    └───────────┘    └──────────────┘    └─────────────┘
```

## Proposed Design

### Architecture Overview

Add a parallel set of unauthenticated endpoints at each layer:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         GraphQL Endpoint Topology                            │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────┐                          ┌─────────┐                            │
│  │ Web UI  │                          │   CLI   │                            │
│  └────┬────┘                          └────┬────┘                            │
│       │                                    │                                 │
│       ▼                                    │                                 │
│  ┌───────────────────────────┐             │                                 │
│  │        Webserver          │             │                                 │
│  ├───────────────────────────┤             │                                 │
│  │ /func/admin/gql     (Auth)│─────────┐   │                                 │
│  │ /func/admin/gql/public    │─────┐   │   │                                 │
│  └───────────────────────────┘     │   │   │                                 │
│                                    │   │   │                                 │
│       ┌────────────────────────────┘   │   │                                 │
│       │                                │   │                                 │
│       ▼                                ▼   │                                 │
│  ┌────────────────────────────────────────────┐                              │
│  │              Hive Gateway                  │                              │
│  │  (Single instance, multiple endpoints)     │                              │
│  ├────────────────────────────────────────────┤                              │
│  │  /admin/gql         → GRAPHENE/STRAWBERRY  │                              │
│  │  /admin/gql/public  → PUBLIC               │ ◄── NEW                      │
│  └─────────────────────┬──────────────────────┘                              │
│                        │                       │                             │
│                        ▼                       ▼                             │
│  ┌──────────────────────────────────────────────────────────────┐            │
│  │                          Manager                             │            │
│  ├──────────────────────────────────────────────────────────────┤            │
│  │  /admin/gql             (Graphene, Auth)                     │            │
│  │  /admin/gql/strawberry  (Strawberry, Auth)                   │            │
│  │  /admin/gql/public      (Strawberry, No Auth) ◄── NEW        │            │
│  └──────────────────────────────────────────────────────────────┘            │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 1. Manager: Public GraphQL Endpoint

**New View Class** (`src/ai/backend/manager/api/admin.py`)

```python
class PublicGraphQLView(GraphQLView):
    """GraphQL view for unauthenticated public endpoints."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        set_handler_attr(self, "auth_required", False)  # No auth required

    async def __call__(self, request: web.Request) -> web.StreamResponse:
        return await super().__call__(request)  # No is_authorized check

    async def get_context(self, request, response) -> PublicGQLContext:
        # Return limited context with minimal dependencies
        ...
```

**New Schema** (`src/ai/backend/manager/api/gql/public_schema.py`)

```python
@strawberry.type
class PublicQuery:
    @strawberry.field
    async def server_info(self, info: strawberry.Info) -> ServerInfo:
        """Get basic server information (version, status)."""
        ...

    @strawberry.field
    async def health(self, info: strawberry.Info) -> HealthStatus:
        """Check system health status."""
        ...

# No mutations, no subscriptions
public_schema = strawberry.Schema(query=PublicQuery)
```

**Route Registration**

Register at `/admin/gql/public` (GET/POST)

### 2. Hive Gateway: Add Public Endpoint (Single Instance)

Use the same Gateway instance with an additional endpoint and transport entry.

**Update `gateway.config.ts`**

```typescript
// Add PUBLIC transport entry
transportEntries: {
  GRAPHENE: { location: '...8091/admin/gql' },
  STRAWBERRY: { location: '...8091/admin/gql/strawberry' },
  PUBLIC: { location: '...8091/admin/gql/public' },  // NEW
},
```

**Add `supergraph-public.graphql`**

Create a separate supergraph schema that:
- Only includes `PUBLIC` subgraph
- Defines `Query` with `serverInfo` and `health` fields
- No `Mutation` or `Subscription`

**Gateway Routing Options**

Single gateway, path-based routing
- `/admin/gql` → existing supergraph (auth required)
- `/admin/gql/public` → public supergraph (no auth)

### 3. Webserver: Public Endpoint Handler
Use already existing `anon_web_handler`

```python
# Already exists in server.py
anon_web_handler = partial(web_handler, is_anonymous=True)
```

**Route Registration** (`src/ai/backend/web/server.py`)

```python
if config.apollo_router.enabled:
    # Public GraphQL endpoint (no auth, same Gateway, different path)
    cors.add(app.router.add_route("GET", "/func/admin/gql/public", anon_web_handler))
    cors.add(app.router.add_route("POST", "/func/admin/gql/public", anon_web_handler))

    # legacy handler requires authentication
    supergraph_handler = partial(
        web_handler_with_jwt, api_endpoints=list(config.apollo_router.endpoints)
    )
```

## Security Considerations

### Rate Limiting

Public endpoints MUST implement rate limiting to prevent abuse.

### Query Depth Limiting

Use `QueryDepthLimiter` extension with strict limits (e.g., max_depth=3).

### Exposed Information

The public endpoint should only expose:
- Server version and status
- Health check status
- Available API capabilities

It must NOT expose:
- User information
- Session data
- Configuration details
- Internal system information

## References

- [BEP-1010: New GQL](BEP-1010-new-gql.md) - GraphQL Migration to Strawberry
- [Strawberry GraphQL Documentation](https://strawberry.rocks/)
- [Hive Gateway Documentation](https://the-guild.dev/graphql/hive/docs/gateway)
