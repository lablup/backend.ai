# GraphQL Federation Configuration

This directory holds the configuration files of the GraphQL federation router.

## Router: Hive Gateway

The project uses [The Guild's Hive Gateway](https://the-guild.dev/graphql/hive/docs/gateway) instead of Apollo Router to avoid subscription licensing requirements. Hive Gateway is fully compatible with Apollo Federation v1/v2 and provides native subscription support without license restrictions.

## Files

- `gateway.config.ts`: Hive Gateway configuration (host, port, subgraph URLs, metrics)
- `supergraph.yaml`: **Rover CLI configuration** for composing multiple subgraph schemas into a single supergraph schema
- `router.yaml`: Legacy Apollo Router configuration (kept for reference)

## Gateway Configuration

`gateway.config.ts` configures the gateway with:

- **Host/Port**: Listens on `0.0.0.0:4000` inside the container. The halfstack compose files publish the port on `127.0.0.1:4000` only
- **Supergraph Schema**: Loads from `/gateway/supergraph.graphql` (mounted from `docs/manager/graphql-reference/supergraph.graphql`)
- **Transport Entries**: Explicitly defines subgraph routing URLs
  - `graphene`: `http://host.docker.internal:8091/admin/gql`
  - `strawberry`: `http://host.docker.internal:8091/admin/gql/strawberry`
- **Prometheus Metrics**: Exposes metrics at the `/metrics` path
- **Error masking**: The `maskError` of `maskedErrors` replaces the message of gateway failures, manager HTTP errors, and manager errors whose code ends with `_internal-error` with `Unexpected error.`
  - Manager HTTP errors keep `status` and `statusText` in `extensions.response`. 4xx errors also keep `type`, `title`, `error_code`, and `msg` of `body` (WebUI reads them to detect an expired session)
  - Other manager GraphQL errors pass through unchanged

## Subgraphs

The federated graph consists of three subgraphs:

1. **graphene**: the legacy GraphQL API (`/admin/gql`)
   - Schema: `../../docs/manager/graphql-reference/schema.graphql`

2. **strawberry**: the v2 GraphQL API (`/admin/gql/strawberry`)
   - Schema: `../../docs/manager/graphql-reference/v2-schema.graphql`
   - Supports WebSocket subscriptions via the `graphql-ws` protocol

3. **public**: Unauthenticated fields (`/admin/gql/strawberry/public`)
   - Schema: `../../docs/manager/graphql-reference/v2-public-schema.graphql`
   - The only routing URL without authentication middleware: an anonymous query resolves here alone

## Schema Updates

### Supergraph Composition with Rover

Hive Gateway loads the composed supergraph schema from `docs/manager/graphql-reference/supergraph.graphql`. **Rover**, the Apollo Federation CLI tool, generates this single schema by composing the subgraph schemas.

The `supergraph.yaml` file is the Rover configuration that defines:
- **Subgraph names**: Identifiers for each subgraph (`graphene`, `strawberry`)
- **Routing URLs**: HTTP URLs for each subgraph service
- **Schema file locations**: Local paths to each subgraph's GraphQL schema

When a subgraph schema changes, regenerate the supergraph with Rover:

```bash
# From project root
rover supergraph compose --config configs/graphql/supergraph.yaml > docs/manager/graphql-reference/supergraph.graphql
```

This command:
1. Reads the subgraph configurations from `supergraph.yaml`
2. Loads and validates each subgraph schema from the specified file paths
3. Composes them into a single federated supergraph schema
4. Writes the result to `docs/manager/graphql-reference/supergraph.graphql`

After regenerating the supergraph, restart the gateway container:

```bash
docker compose -f docker-compose.halfstack-main.yml restart backendai-half-apollo-router
```

**Note**: Both `supergraph.yaml` (which generates `supergraph.graphql`) and `gateway.config.ts` must have matching routing URLs. The `transportEntries` in `gateway.config.ts` do not override the URLs in `@join__graph` directives. Update both configurations together so routing to each subgraph URL stays correct.

## Subscription Support

Hive Gateway provides built-in WebSocket subscription support:

- **graphql-ws**: Current WebSocket protocol (default)
- **subscriptions-transport-ws**: Legacy WebSocket protocol
- **SSE**: Server-Sent Events over HTTP
- **HTTP Callbacks**: Webhook-based subscriptions

The gateway negotiates the protocol with clients automatically based on the `Sec-WebSocket-Protocol` header.

## Monitoring

Hive Gateway exposes Prometheus metrics at the `/metrics` path:

- **URL**: `http://localhost:4000/metrics`
- **Metrics**:
  - `graphql_gateway_fetch_duration`: Duration of HTTP requests to upstream services
  - `graphql_gateway_subgraph_execute_duration`: Time spent executing queries on each subgraph
  - `graphql_gateway_subgraph_execute_errors`: Number of errors from subgraph execution

Prometheus scrapes the metrics automatically (configured in `prometheus.yaml`).

## Related documents

- [Hive Gateway Documentation](https://the-guild.dev/graphql/hive/docs/gateway)
- [Docker Deployment](https://the-guild.dev/graphql/hive/docs/gateway/deployment/docker)
- [Subscription Configuration](https://the-guild.dev/graphql/hive/docs/gateway/subscriptions)
- [Monitoring and Tracing](https://the-guild.dev/graphql/hive/docs/gateway/monitoring-tracing)
