# GraphQL Federation Configuration

This directory contains configuration files for the GraphQL federation router.

## Router: Hive Gateway

We use [The Guild's Hive Gateway](https://the-guild.dev/graphql/hive/docs/gateway) instead of Apollo Router to avoid subscription licensing requirements. Hive Gateway is fully compatible with Apollo Federation v1/v2 and provides native subscription support without license restrictions.

## Files

- `gateway.config.ts`: Hive Gateway configuration (host, port, subgraph endpoints, metrics)
- `supergraph.yaml`: Rover CLI configuration for composing subgraphs
- `router.yaml`: Legacy Apollo Router configuration (kept for reference)

## Gateway Configuration

The gateway is configured via `gateway.config.ts` which includes:

- **Host/Port**: Binds to `0.0.0.0:4000` for external access
- **Supergraph Schema**: Loads from `/gateway/supergraph.graphql` (mounted from `docs/manager/graphql-reference/supergraph.graphql`)
- **Transport Entries**: Explicitly defines subgraph routing URLs
  - `graphene`: `http://host.docker.internal:8091/admin/gql`
  - `strawberry`: `http://host.docker.internal:8091/admin/gql/strawberry`
- **Prometheus Metrics**: Exposes metrics at `/metrics` endpoint

## Subgraphs

The federated graph consists of two subgraphs:

1. **graphene**: Legacy GraphQL API (`/admin/gql`)
   - Schema: `../../docs/manager/graphql-reference/schema.graphql`

2. **strawberry**: New GraphQL API (`/admin/gql/strawberry`)
   - Schema: `../../docs/manager/graphql-reference/v2-schema.graphql`
   - Supports WebSocket subscriptions via `graphql-ws` protocol

## Schema Updates

Hive Gateway loads the composed supergraph schema from `docs/manager/graphql-reference/supergraph.graphql`.

When subgraph schemas are modified, regenerate the supergraph using Rover (Apollo Federation CLI):

```bash
# From project root
rover supergraph compose --config configs/graphql/supergraph.yaml > docs/manager/graphql-reference/supergraph.graphql
```

The `supergraph.yaml` file defines:
- Subgraph names and routing URLs
- Schema file locations for each subgraph

After regenerating the supergraph, restart the gateway container:

```bash
docker compose -f docker-compose.halfstack-main.yml restart backendai-half-apollo-router
```

**Note**: While the supergraph schema contains routing URLs in `@join__graph` directives, we explicitly override them in `gateway.config.ts` using `transportEntries` to ensure correct routing to each subgraph endpoint.

## Subscription Support

Hive Gateway provides built-in WebSocket subscription support:

- **graphql-ws**: Modern WebSocket protocol (default)
- **subscriptions-transport-ws**: Legacy WebSocket protocol
- **SSE**: Server-Sent Events over HTTP
- **HTTP Callbacks**: Webhook-based subscriptions

The gateway automatically negotiates the protocol with clients based on the `Sec-WebSocket-Protocol` header.

## Monitoring

Hive Gateway exposes Prometheus metrics at the `/metrics` endpoint:

- **Endpoint**: `http://localhost:4000/metrics`
- **Metrics**:
  - `graphql_gateway_fetch_duration`: Duration of HTTP requests to upstream services
  - `graphql_gateway_subgraph_execute_duration`: Time spent executing queries on each subgraph
  - `graphql_gateway_subgraph_execute_errors`: Number of errors from subgraph execution

The metrics are automatically scraped by Prometheus (configured in `prometheus.yaml`).

## Resources

- [Hive Gateway Documentation](https://the-guild.dev/graphql/hive/docs/gateway)
- [Docker Deployment](https://the-guild.dev/graphql/hive/docs/gateway/deployment/docker)
- [Subscription Configuration](https://the-guild.dev/graphql/hive/docs/gateway/subscriptions)
- [Monitoring and Tracing](https://the-guild.dev/graphql/hive/docs/gateway/monitoring-tracing)
