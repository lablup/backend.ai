import { defineConfig } from '@graphql-hive/gateway';

export const gatewayConfig = defineConfig({
  propagateHeaders: {
    fromClientToSubgraphs({ request }) {
      let headers = Object.fromEntries(request.headers.entries());
      delete headers['content-length'];
      return headers;
    }
  },
  supergraph: '/gateway/supergraph.graphql',
  graphqlEndpoint: '/admin/gql',
  skipValidation: true,
  transportEntries: {
    GRAPHENE: {
      // Location points to the manager's GraphQL path
      // This is configured for halfstack's Docker environment
      // NOTE: This must be changed in production environments
      location: 'http://host.docker.internal:8091/admin/gql',
    },
    STRAWBERRY: {
      // Location points to the manager's GraphQL path
      // This is configured for halfstack's Docker environment
      // NOTE: This must be changed in production environments
      location: 'http://host.docker.internal:8091/admin/gql/strawberry',
    },
    '*.http': {
      options: {
        subscriptions: {
          kind: 'ws',
        }
      }
    }
  },
});
