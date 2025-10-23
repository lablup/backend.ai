import { defineConfig, WSTransportOptions, type GatewayPlugin } from '@graphql-hive/gateway';

// Custom plugin to convert WebSocket connectionParams to HTTP headers
// This allows authentication parameters sent via WebSocket connection_init
// to be forwarded as HTTP headers when the gateway makes federation requests to subgraphs
const useConnectionParamsToHeadersPlugin = (): GatewayPlugin => {
  return {
    onSubgraphExecute({ executionRequest, executor, setExecutor }) {
      // Access WebSocket connectionParams from context
      const connectionParams = executionRequest.context?.connectionParams;

      if (connectionParams && typeof connectionParams === 'object') {
        // Wrap executor to inject connectionParams as HTTP headers
        const originalExecutor = executor;
        const wrappedExecutor = async (execRequest: any) => {
          // Extract Authorization header from context if it exists
          const authorization = execRequest.context?.headers?.authorization;

          // Merge connectionParams with Authorization (if present)
          const mergedHeaders = {
            ...connectionParams,
          };

          if (authorization) {
            mergedHeaders.authorization = authorization;
          }
          mergedHeaders.host = execRequest.context?.headers?.host;
          // Content type too
          mergedHeaders['content-type'] = execRequest.context?.headers?.['content-type'];
          mergedHeaders['Date'] = execRequest.context?.headers?.['date'];

          console.log('Merged headers (Authorization + connectionParams):', mergedHeaders);
          console.log('execRequest.info?.operation?.operation:', execRequest.info?.operation?.operation);
          console.log('execRequest.operationType:', execRequest.operationType);

          const modifiedRequest = {
            ...execRequest,
            extensions: {
              ...execRequest.extensions,
              headers: mergedHeaders,
            },
          };

          return originalExecutor(modifiedRequest);
        };

        setExecutor(wrappedExecutor);
      }
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
      location: 'http://host.docker.internal:8091/admin/gql/strawberry',
    },
    '*.http': {
      options: {
        subscriptions: {
          kind: 'ws',
          options: {
            connectionParams: {
              token: '{context.headers.authorization}'
            }
          } satisfies WSTransportOptions
        }
      }
    }
  },
});
