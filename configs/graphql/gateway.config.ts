import { defineConfig, WSTransportOptions, type GatewayPlugin } from '@graphql-hive/gateway';

// Custom plugin to forward headers from context to subgraph requests
// This ensures headers (including JWT tokens) are included in each GraphQL operation
// execution after the WebSocket connection is established.
// Note: For WebSocket handshake authentication, the 'headers' option in transportEntries is used.
const useConnectionParamsToHeadersPlugin = (): GatewayPlugin => {
  return {
    onSubgraphExecute({ executionRequest, executor, setExecutor }) {
      // Always wrap executor to forward headers from context
      const originalExecutor = executor;
      const wrappedExecutor = async (execRequest: any) => {
        // Extract headers from execution request context
        let reqHeaders = execRequest.context.headers || {};
        let new_headers = {};
        if (reqHeaders["x-backendai-token"]) {
          new_headers = {
            "x-backendai-token": reqHeaders["x-backendai-token"]
          };
        }

        const modifiedRequest = {
          ...execRequest,
          extensions: {
            headers: new_headers,
          },
        };
        return originalExecutor(modifiedRequest);
      };

      setExecutor(wrappedExecutor);
    },
  };
};

export const gatewayConfig = defineConfig({
  plugins: (ctx) => [
    useConnectionParamsToHeadersPlugin(),
  ],
  propagateHeaders: {
    fromClientToSubgraphs({ context }) {
      let headers = context.headers || {};
      delete headers['content-length'];
      return headers;
    },
  },
  maskedErrors: false,
  logging: false,
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
      // NOTE: STRAWBERRY supports WebSocket subscriptions
      location: 'http://host.docker.internal:8091/admin/gql/strawberry',
    },
    '*.http': {
      options: {
        subscriptions: {
          kind: 'ws',
          headers: [
            ['x-backendai-token', '{context.headers.x-backendai-token}']
          ]
        },
      }
    },
  },
});
