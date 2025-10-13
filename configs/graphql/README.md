# GraphQL Federation Configuration

This directory contains configuration files for the GraphQL federation router.

## Router: Cosmo Router

We use [WunderGraph Cosmo Router](https://cosmo-docs.wundergraph.com/) instead of Apollo Router to avoid subscription licensing requirements. Cosmo Router is fully compatible with Apollo Federation v1/v2 and provides native subscription support without license restrictions.

## Files

- `cosmo-graph.yaml`: Input configuration defining subgraphs and their schemas
- `router-config.json`: Generated execution configuration for Cosmo Router (do not edit manually)
- `router.yaml`: Legacy Apollo Router configuration (kept for reference)
- `supergraph.yaml`: Legacy supergraph composition configuration (kept for reference)

## Subgraphs

The federated graph consists of two subgraphs:

1. **graphene**: Legacy GraphQL API (`/admin/gql`)
   - Schema: `../../docs/manager/graphql-reference/schema.graphql`

2. **strawberry**: New GraphQL API (`/admin/gql/strawberry`)
   - Schema: `../../docs/manager/graphql-reference/v2-schema.graphql`
   - Supports WebSocket subscriptions via `graphql-ws` protocol

## Schema Composition Workflow

When subgraph schemas are modified, you must regenerate the router execution config:

```bash
# From project root
./scripts/compose-graphql-router.sh
```

After regenerating the config, restart the router container:

```bash
docker compose -f docker-compose.halfstack-main.yml restart backendai-half-apollo-router
```

## Development

The router runs in `DEV_MODE=true` for development environments, which enables:
- Enhanced logging
- Development UI
- Hot reload capabilities

## Subscription Support

Cosmo Router supports multiple subscription protocols:

- **graphql-ws** (default): Modern WebSocket protocol
- **SSE** (Server-Sent Events): HTTP-based alternative
- **Multipart HTTP**: Streaming over standard HTTP

The strawberry subgraph is configured to use `graphql-ws` protocol for subscriptions.

## Resources

- [Cosmo Router Documentation](https://cosmo-docs.wundergraph.com/router)
- [Cosmo CLI (wgc)](https://cosmo-docs.wundergraph.com/cli)
- [Subscription Configuration](https://cosmo-docs.wundergraph.com/router/subscriptions)
