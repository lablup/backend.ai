import { defineConfig, WSTransportOptions, type GatewayPlugin } from '@graphql-hive/gateway';
import { GraphQLError } from 'graphql';

// ErrorDetail.INTERNAL_ERROR at the end of a manager error code
const INTERNAL_ERROR_CODE_SUFFIX = '_internal-error';
// Fields of a manager 4xx response that clients read, e.g. to detect an expired session
const UPSTREAM_ERROR_BODY_FIELDS = ['type', 'title', 'error_code', 'msg'];

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
        let new_headers: Record<string, string> = {};
        if (reqHeaders["x-backendai-token"]) {
          new_headers["x-backendai-token"] = reqHeaders["x-backendai-token"];
        }
        // Forward X-Forwarded-For so the manager can resolve the real client IP
        // (e.g. for the my_client_ip GQL query). Without this, extract_client_ip()
        // falls back to the hive-gateway/HAProxy IP.
        if (reqHeaders["x-forwarded-for"]) {
          new_headers["x-forwarded-for"] = reqHeaders["x-forwarded-for"];
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

const isGraphQLErrorChain = (error: unknown): boolean => {
  let current = error;
  while (current instanceof GraphQLError && current.originalError) {
    current = current.originalError;
  }
  return current instanceof GraphQLError;
};

const pickUpstreamErrorResponse = (response: any) => {
  const { status, statusText, body } = response;
  if (status >= 500 || typeof body !== 'object' || body === null) {
    return { status, statusText };
  }
  return {
    status,
    statusText,
    body: Object.fromEntries(
      UPSTREAM_ERROR_BODY_FIELDS.filter((field) => field in body).map((field) => [field, body[field]]),
    ),
  };
};

// Replaces gateway failures, manager HTTP errors and manager internal errors with the generic
// message. Other GraphQL errors from the manager are the client's to read, so they pass as is.
const maskError = (error: any, message: string): Error => {
  const response = error?.extensions?.response;
  const code = error?.extensions?.code;
  const isInternalError = typeof code === 'string' && code.endsWith(INTERNAL_ERROR_CODE_SUFFIX);
  if (isGraphQLErrorChain(error) && !response && !isInternalError) {
    return error;
  }
  return new GraphQLError(message, {
    nodes: error?.nodes,
    path: error?.path,
    extensions: {
      code: 'INTERNAL_SERVER_ERROR',
      ...(response ? { response: pickUpstreamErrorResponse(response) } : {}),
    },
  });
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
  maskedErrors: { maskError },
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
