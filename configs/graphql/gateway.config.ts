import {
  defineConfig,
  DisposableSymbols,
  WSTransport,
  WSTransportOptions,
  type GatewayPlugin,
} from '@graphql-hive/gateway';
import { Agent as HttpAgent } from 'node:http';
import { Agent as HttpsAgent } from 'node:https';
import type { Socket } from 'node:net';

const MANAGER_PROBE_PATH = '/health/readyz';
// WebSocket close code for a connection dropped without a close frame
const WS_ABNORMAL_CLOSURE = 1006;

// Returns the default when the variable is unset; rejects anything but a positive number
const readPositiveNumberEnv = (name: string, defaultValue: number): number => {
  const raw = process.env[name];
  if (raw === undefined || raw.trim() === '') {
    return defaultValue;
  }
  const value = Number(raw);
  if (!Number.isFinite(value) || value <= 0) {
    throw new Error(`${name} must be a positive number: ${raw}`);
  }
  return value;
};

const managerEndpoints = (process.env.BACKENDAI_MANAGER_ENDPOINTS || '')
  .split(',')
  .map((endpoint) => endpoint.trim())
  .filter((endpoint) => endpoint.length > 0)
  .map((endpoint) => new URL(endpoint).origin);
const managerRequestTimeoutMs = readPositiveNumberEnv('BACKENDAI_MANAGER_REQUEST_TIMEOUT', 60) * 1000;

// Errors raised before the connection to the manager is established, so the request never reached it
const isConnectFailure = (error: any): boolean => error?.syscall === 'connect';

// Destroys a socket that has not connected within timeoutMs with an error isConnectFailure accepts
const withConnectTimeout = <T extends HttpAgent>(agent: T, timeoutMs: number): T => {
  const createConnection = (agent as any).createConnection.bind(agent);
  (agent as any).createConnection = (options: any, callback: any) => {
    const socket: Socket = createConnection(options, callback);
    if (socket.connecting) {
      const timer = setTimeout(() => {
        socket.destroy(
          Object.assign(new Error(`connect ETIMEDOUT ${options.host}:${options.port}`), {
            code: 'ETIMEDOUT',
            syscall: 'connect',
          }),
        );
      }, timeoutMs);
      socket.once('connect', () => clearTimeout(timer));
      socket.once('close', () => clearTimeout(timer));
    }
    return socket;
  };
  return agent;
};

// Opens each subgraph request or subscription on a ready manager in BACKENDAI_MANAGER_ENDPOINTS
// (comma-separated origins). Without the list, the transportEntries locations are used as is.
const useManagerPoolPlugin = (): GatewayPlugin => {
  const managers = managerEndpoints;
  if (managers.length === 0) {
    return {};
  }
  const intervalMs = readPositiveNumberEnv('BACKENDAI_MANAGER_HEALTH_CHECK_INTERVAL', 10) * 1000;
  const probeTimeoutMs = readPositiveNumberEnv('BACKENDAI_MANAGER_HEALTH_CHECK_PROBE_TIMEOUT', 3) * 1000;
  const failureThreshold = readPositiveNumberEnv('BACKENDAI_MANAGER_HEALTH_CHECK_FAILURE_THRESHOLD', 3);
  const connectTimeoutMs = readPositiveNumberEnv('BACKENDAI_MANAGER_CONNECT_TIMEOUT', 3) * 1000;
  const httpAgent = withConnectTimeout(new HttpAgent({ keepAlive: true }), connectTimeoutMs);
  const httpsAgent = withConnectTimeout(new HttpsAgent({ keepAlive: true }), connectTimeoutMs);
  const readyManagers = new Set<string>(managers);
  const failureCounts = new Map<string, number>(managers.map((manager) => [manager, 0]));
  const probingManagers = new Set<string>();
  // Keyed by the manager-specific subscription location
  const wsExecutors = new Map<string, any>();
  // Callbacks that end the subscriptions open on each subscription location
  const subscriptionClosers = new Map<string, Set<() => void>>();
  let cursor = 0;
  let timer: ReturnType<typeof setInterval> | undefined;

  const pickManager = (): string => {
    const candidates = managers.filter((manager) => readyManagers.has(manager));
    if (candidates.length === 0) {
      throw new Error('No ready manager is available');
    }
    return candidates[cursor++ % candidates.length];
  };
  const relocate = (location: string, manager: string): string => {
    const url = new URL(location);
    return `${manager}${url.pathname}${url.search}`;
  };
  // The health check returns the manager to the pool once it responds
  const dropManager = (manager: string) => {
    readyManagers.delete(manager);
  };
  const closeSubscriptions = (location: string) => {
    const closers = subscriptionClosers.get(location);
    subscriptionClosers.delete(location);
    closers?.forEach((close) => close());
  };
  // Ends the subscription with an error when the WS connection to its manager drops,
  // instead of waiting for the WS client to retry the same manager
  const subscribeOnManager = (executor: any, location: string) =>
    async function* (executionRequest: any) {
      const source = await executor(executionRequest);
      if (!source?.[Symbol.asyncIterator]) {
        yield source;
        return;
      }
      const iterator = source[Symbol.asyncIterator]();
      // The WS transport's iterator ends a pending next() with the error passed to throw()
      const close = () => {
        void iterator.throw?.(new Error('Lost the connection to the manager'));
      };
      let closers = subscriptionClosers.get(location);
      if (!closers) {
        closers = new Set();
        subscriptionClosers.set(location, closers);
      }
      closers.add(close);
      try {
        while (true) {
          const result = await iterator.next();
          if (result.done) {
            return;
          }
          yield result.value;
        }
      } finally {
        subscriptionClosers.get(location)?.delete(close);
        await iterator.return?.();
      }
    };
  // A 503 removes the manager at once; other failures remove it after the threshold
  const probe = async (manager: string) => {
    if (probingManagers.has(manager)) {
      return;
    }
    probingManagers.add(manager);
    let status: number | undefined;
    try {
      const response = await fetch(`${manager}${MANAGER_PROBE_PATH}`, {
        signal: AbortSignal.timeout(probeTimeoutMs),
      });
      status = response.status;
      await response.body?.cancel();
    } catch {
      status = undefined;
    } finally {
      probingManagers.delete(manager);
    }
    if (status !== undefined && status >= 200 && status < 300) {
      failureCounts.set(manager, 0);
      readyManagers.add(manager);
      return;
    }
    const failureCount = failureCounts.get(manager)! + 1;
    failureCounts.set(manager, failureCount);
    if (status === 503 || failureCount >= failureThreshold) {
      readyManagers.delete(manager);
    }
  };
  const probeAll = () => Promise.allSettled(managers.map(probe));

  return {
    onPluginInit() {
      void probeAll();
      timer = setInterval(probeAll, intervalMs);
    },
    onFetch({ url, setURL, fetchFn, setFetchFn, executionRequest }) {
      if (!executionRequest) {
        return;
      }
      let manager: string;
      try {
        manager = pickManager();
      } catch (error) {
        // A throw from this hook leaves the upstream timeout's rejection unhandled and ends the process
        setFetchFn(() => Promise.reject(error));
        return;
      }
      setURL(relocate(url, manager));
      // A request that could not connect is resent once to another manager
      setFetchFn(async (targetUrl: string, options: any, ...rest: any[]) => {
        const agent = targetUrl.startsWith('https:') ? httpsAgent : httpAgent;
        const fetchOnManager = async (target: string) => {
          try {
            return await fetchFn(relocate(targetUrl, target), { ...options, agent }, ...rest);
          } catch (error) {
            if (isConnectFailure(error)) {
              dropManager(target);
            }
            throw error;
          }
        };
        try {
          return await fetchOnManager(manager);
        } catch (error) {
          if (!isConnectFailure(error) || readyManagers.size === 0) {
            throw error;
          }
          return fetchOnManager(pickManager());
        }
      });
    },
    onSubgraphExecute({ executionRequest, transportEntry, setExecutor, log }) {
      const subscriptions = transportEntry?.options?.subscriptions;
      if (
        executionRequest.operationType !== 'subscription' ||
        !transportEntry?.location ||
        subscriptions?.kind !== 'ws'
      ) {
        return;
      }
      const manager = pickManager();
      const location = relocate(transportEntry.location, manager);
      let executor = wsExecutors.get(location);
      if (!executor) {
        // Same entry the HTTP transport hands to the WS transport for subscriptions
        executor = WSTransport.getSubgraphExecutor({
          transportEntry: {
            ...transportEntry,
            kind: 'ws',
            location,
            headers: subscriptions.headers,
            options: {
              ...transportEntry.options,
              ...subscriptions.options,
              subscriptions: undefined,
            },
          },
          log,
        } as any, (client: any) => {
          client.on('closed', (event: any) => {
            if (event?.code === WS_ABNORMAL_CLOSURE) {
              dropManager(manager);
              closeSubscriptions(location);
            }
          });
        });
        wsExecutors.set(location, executor);
      }
      setExecutor(subscribeOnManager(executor, location));
    },
    async onDispose() {
      clearInterval(timer);
      await Promise.allSettled(
        Array.from(wsExecutors.values()).map((executor) => executor[DisposableSymbols.asyncDispose]()),
      );
      wsExecutors.clear();
    },
  };
};

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
        if (reqHeaders["x-backendai-act-as"]) {
          new_headers["x-backendai-act-as"] = reqHeaders["x-backendai-act-as"];
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

export const gatewayConfig = defineConfig({
  plugins: (ctx) => [
    // Must come first: the next plugin wraps the executor this one sets
    useManagerPoolPlugin(),
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
  // With the manager list, requests fail after BACKENDAI_MANAGER_REQUEST_TIMEOUT seconds (default 60).
  // Subscriptions are excluded since the timeout would end them.
  upstreamTimeout:
    managerEndpoints.length > 0
      ? ({ executionRequest }) =>
          executionRequest?.operationType === 'subscription' ? undefined : managerRequestTimeoutMs
      : undefined,
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
    PUBLIC: {
      // Location points to the manager's GraphQL path
      // This is configured for halfstack's Docker environment
      // NOTE: This must be changed in production environments
      // NOTE: PUBLIC carries no auth middleware, so anonymous queries resolve here
      location: 'http://host.docker.internal:8091/admin/gql/strawberry/public',
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
