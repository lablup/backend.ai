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
        // Extract headers from execution request context.
        // Whitelist approach: only forward known-safe headers to subgraphs to
        // avoid leaking sensitive headers (cookies, authorization, etc.).
        // hive-gateway lowercases incoming header names, so keys are lowercase.
        const forwardedHeaderWhitelist = [
          "x-backendai-token",
          // Forwarding headers — required so the manager can resolve the real
          // client IP (e.g. for the my_client_ip GQL query). Without these,
          // extract_client_ip() falls back to the hive-gateway/HAProxy IP.
          "x-forwarded-for",
          "x-forwarded-proto",
          "x-forwarded-host",
          "x-real-ip",
          "forwarded",
        ];
        let reqHeaders = execRequest.context.headers || {};
        let new_headers: Record<string, string> = {};
        for (const key of forwardedHeaderWhitelist) {
          if (reqHeaders[key]) {
            new_headers[key] = reqHeaders[key];
          }
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
  disableIntrospection: {
    disableIf: () => true
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
