# Backend.AI app proxy

## Purpose

The app proxy provides dynamic routing and load balancing for the service ports of sessions. Through an app proxy coordinator and app proxy worker architecture, it routes traffic to session services (Jupyter, SSH, TensorBoard, and so on) and balances load across the replicas of a session.

## Key Responsibilities

### 1. Dynamic Service Routing
- Route HTTP/WebSocket traffic to session services
- Manage service port mappings dynamically
- Support port-based and subdomain-based proxying
- Clean up routing rules automatically on session termination

### 2. Load Balancing
- Distribute traffic across the replicas of a session
- Round-robin and weighted balancing
- Distribute load across worker nodes
- Automatic failover and health checks

### 3. Service Discovery and Registration
- Register service routes from the manager
- Distributed service discovery based on etcd
- Register and deregister worker nodes automatically
- Synchronize the routing table in real time

### 4. SSL/TLS Termination
- Handle SSL termination for HTTPS traffic
- Certificate management and renewal
- SNI (Server Name Indication) support
- Secure WebSocket (WSS) connection handling

### 5. Metrics and Monitoring
- Track request count and latency
- Monitor worker and circuit status
- Expose Prometheus metrics
- Analyze traffic patterns

## Architecture

```
┌─────────────────────────────────────────┐
│    Coordinator (coordinator/)           │
│  ├── API (circuit/worker management)    │  ← REST API
│  ├── Circuit Manager                    │  ← Routing rules
│  ├── Database (PostgreSQL)              │  ← State storage
│  └── Health Checker                     │  ← Worker status
└─────────────────┬───────────────────────┘
                  │
      ┌───────────┼───────────┐
      │           │           │
      ↓           ↓           ↓
┌──────────┐ ┌──────────┐ ┌──────────┐
│ Worker 1 │ │ Worker 2 │ │ Worker N │  ← Distributed proxy
├──────────┤ ├──────────┤ ├──────────┤
│Frontend  │ │Frontend  │ │Frontend  │  ← Port/subdomain
├──────────┤ ├──────────┤ ├──────────┤
│Backend   │ │Backend   │ │Backend   │  ← HTTP/H2/TCP
└────┬─────┘ └────┬─────┘ └────┬─────┘
     │            │            │
     └────────────┼────────────┘
                  ↓
           ┌─────────────┐
           │    Agent    │ ← Container service ports
           └─────────────┘
```

## Directory Structure

```
appproxy/
├── common/              # Shared utilities and types
│   ├── types.py        # Common data types
│   └── utils.py        # Utility functions
├── coordinator/         # Central routing coordinator
│   ├── api/            # REST API endpoints
│   │   ├── circuit_v1.py   # Circuit management v1
│   │   ├── circuit_v2.py   # Circuit management v2
│   │   ├── worker_v1.py    # Worker management v1
│   │   ├── worker_v2.py    # Worker management v2
│   │   └── health.py       # Health check
│   ├── models/         # Database models
│   │   └── alembic/    # Migrations
│   ├── cli/            # CLI commands
│   ├── config.py       # Configuration management
│   ├── server.py       # Server entry point
│   ├── types.py        # Type definitions
│   └── health_checker.py  # Worker health check
├── worker/              # Distributed proxy worker
│   ├── api/            # Worker API
│   ├── proxy/          # Proxy implementation
│   │   ├── frontend/   # Frontend (port/subdomain)
│   │   └── backend/    # Backend (HTTP/H2/TCP/Traefik)
│   ├── cli/            # CLI commands
│   ├── config.py       # Configuration management
│   ├── server.py       # Server entry point
│   ├── types.py        # Type definitions
│   ├── metrics.py      # Metrics collection
│   └── coordinator_client.py  # Coordinator client
└── README.md            # Overall architecture documentation
```

## Core Concepts

### Circuit
A circuit represents a routing rule from the client to a session service:
- **Circuit Key**: Unique identifier (session ID + service name)
- **Frontend**: Client entry point (port or subdomain)
- **Backend**: Proxy implementation (HTTP, H2, TCP, Traefik)
- **Target**: Actual service location (Agent host:port)
- **Status**: HEALTHY, UNHEALTHY, PENDING

Circuit lifecycle:
1. The manager registers the circuit when it creates a session
2. The app proxy coordinator deploys the circuit to app proxy workers
3. The app proxy worker activates the proxy rules
4. Client traffic routes through the circuit
5. The circuit is deregistered automatically on session termination

### Frontend Types

#### Port-based Frontend
- Assign a unique port per service (for example, 30001, 30002)
- Requires port forwarding in NAT environments
- Simple and direct access
- Requires firewall rule management

#### Subdomain-based Frontend
- Assign a subdomain per service (for example, `session-123.backend.ai`)
- Secure connection via SSL certificate
- Only ports 80/443 exposed
- Requires wildcard DNS

### Backend Types

A backend handles the actual proxy implementation:

#### HTTP Backend
- Standard HTTP/1.1 proxy
- WebSocket upgrade support
- Request header modification and forwarding
- Suitable for simple services

#### H2 Backend
- HTTP/2 protocol support
- Multiplexing and streaming
- Suitable for high-performance services
- Bidirectional communication support

#### TCP Backend
- Raw TCP proxy
- Protocol-independent
- Used for SSH, databases, and so on
- Minimal overhead

#### Traefik Backend

- Traefik integration
- Advanced routing rules
- Middleware chains
- Both app proxy plugins are required: the Rust/WASM plugin in [backend.ai-appproxy-worker-traefik](https://github.com/lablup/backend.ai-appproxy-worker-traefik) handles cookie/JWT authentication; the [Go plugin in this repository](../../../../third-party-plugins/appproxy-traefik-plugin-go/) tracks circuit access, session access and WebSocket activity.
- See [Traefik Integration Guide](../../../../docs/app-proxy/traefik-integration.md) for detailed configuration

### Load Balancing Strategies

#### Round Robin
- Select app proxy workers in order
- Equal traffic distribution
- Simple and predictable
- Default strategy

#### Weighted
- Assign weights based on worker capacity
- Traffic distribution proportional to performance
- Suitable for heterogeneous worker environments
- Dynamic weight adjustment possible

#### Least Connections
- Select the worker with the fewest current connections
- Effective for long-lived connections
- Balances worker load
- Requires real-time metrics

## App proxy coordinator details

### Circuit Management
The app proxy coordinator manages the full lifecycle of circuits:
- Circuit registration and deregistration
- Circuit deployment to app proxy workers
- Circuit status monitoring
- Automatic redeployment on failure

### App proxy worker management
App proxy worker registration and status tracking:
- Automatic worker registration and deregistration
- Periodic heartbeat reception
- App proxy worker capacity and load monitoring
- Select target app proxy workers for circuit deployment

### Health Check
The app proxy coordinator checks worker status periodically:
- **Interval**: 5 seconds (default)
- **Timeout**: 2 seconds
- **Retries**: 3 attempts
- **Recovery**: Automatic circuit redeployment

## App proxy worker details

### Proxy Handling
The app proxy worker handles the actual traffic proxying:
1. Receive the client request
2. Look up the routing rule by circuit key
3. Select the appropriate backend
4. Forward the request to the target
5. Stream the response
6. Record metrics

### Frontend Handling

#### Port-based
The app proxy worker allocates service-specific ports dynamically from the specified port range.

#### Subdomain-based
The app proxy worker handles subdomain requests with a wildcard SSL certificate.

### Backend Selection
The backend is selected automatically based on the service type:
- **HTTP services**: HTTP or H2 backend
- **WebSocket**: HTTP backend (with upgrade support)
- **SSH/DB**: TCP backend
- **Complex routing**: Traefik backend

## Communication Protocols

### Manager → app proxy coordinator
- **Protocol**: gRPC or REST
- **Port**: 6120 (default)
- **Authentication**: API key
- **Operations**:
  - Register and deregister circuits
  - Query worker information
  - Check health status

### Client → app proxy worker
- **Protocol**: HTTP/HTTPS, WebSocket/WSS
- **Port**: 6130 (default) or dynamic ports
- **Operations**:
  - Access services (Jupyter, SSH, and so on)
  - WebSocket connections
  - File download and upload

### App proxy worker → app proxy coordinator
- **Protocol**: REST API
- **Operations**:
  - App proxy worker registration and heartbeat
  - Circuit status updates
  - Metrics reporting

### App proxy worker → Agent
- **Protocol**: HTTP/WebSocket or TCP
- **Operations**:
  - Forward traffic to the actual service ports
  - Access container services

## Service Access Flow

```
1. User accesses session service (e.g., Jupyter)
   ↓
2. Manager registers circuit with Coordinator
   ↓
3. Coordinator selects appropriate worker
   ↓
4. Coordinator deploys circuit to worker
   ↓
5. Worker activates proxy rules
   ↓
6. User browser connects to worker URL
   ↓
7. Worker routes through circuit to Agent
   ↓
8. Agent forwards request to container port
   ↓
9. Container generates response
   ↓
10. Worker streams response to user
```

## Load Balancing Scenarios

### Single Session, Multiple Workers
```
Client → Worker Pool → Agent (Single Container)
         ├─ Worker 1
         ├─ Worker 2
         └─ Worker N
```
Distribute traffic across workers to mitigate network bottlenecks

### Multiple Session Replicas
```
Client → Worker → Agent Pool
                  ├─ Agent 1 (Container Replica 1)
                  ├─ Agent 2 (Container Replica 2)
                  └─ Agent N (Container Replica N)
```
Provide high availability by balancing load across the replicas of a session

## Configuration

See `configs/app-proxy-coordinator/halfstack.toml` and `configs/app-proxy-worker/halfstack.toml` for configuration file examples.

### Key Configuration Items

**App proxy coordinator**:
- PostgreSQL database connection
- App proxy worker health check interval
- etcd connection information

**App proxy worker**:
- App proxy coordinator connection information
- Frontend mode (port or subdomain)
- Backend timeout settings

## Infrastructure Dependencies

The app proxy consists of the app proxy coordinator and the app proxy worker, each with different infrastructure dependencies.

### App proxy coordinator infrastructure

#### PostgreSQL (Database)
- **Purpose**:
  - Store circuit routing rules
  - Manage app proxy worker registration information
  - Store health check status
- **Halfstack Port**: 8101 (shared with the manager)
- **Key Tables**:
  - `circuits` - Circuit routing information
  - `workers` - App proxy worker registration and status
- **Schema Management**: Alembic migrations

#### etcd (Service Discovery)
- **Purpose**:
  - App proxy worker auto-discovery
  - Distributed configuration management
  - Circuit synchronization
- **Halfstack Port**: 8121
- **Key Paths**:
  - `/appproxy/workers/{worker_id}` - App proxy worker information
  - `/appproxy/circuits/{circuit_key}` - Circuit configuration

### App proxy worker infrastructure

#### App proxy coordinator connection
- **Purpose**:
  - Receive circuit deployments
  - Send heartbeat signals
  - Report metrics
- **Protocol**: REST API
- **Halfstack Port**: 6120 (app proxy coordinator)

### Observability Infrastructure

#### Prometheus (Metrics Collection)
- **App proxy coordinator endpoint**: `http://localhost:6120/metrics`
- **App proxy worker endpoint**: `http://localhost:6130/metrics`
- **Key Metrics**:
  - App proxy coordinator: circuit and worker management metrics
  - App proxy worker: proxy request and performance metrics
- **Service Discovery**: Automatic registration via the manager HTTP service discovery

#### Loki (Log Aggregation)
- **Purpose**:
  - Circuit creation and deletion events
  - App proxy worker registration and deregistration events
  - Proxy request logs
  - Health check and error logs
- **Log Labels**:
  - `component` - app proxy coordinator or app proxy worker
  - `circuit_key` - Circuit identifier
  - `worker_id` - App proxy worker identifier

#### Tempo (Distributed Tracing)
- **Purpose**:
  - Trace full requests through Circuit → App proxy worker → Agent
  - Analyze proxy latency
  - Identify performance bottlenecks
- **Trace Transmission**: OpenTelemetry SDK

### Halfstack Configuration

**Recommended**: Use the `./scripts/install-dev.sh` script to set up the development environment.

#### Starting Development Environment
```bash
# Setup development environment via script (recommended)
./scripts/install-dev.sh

# Start Coordinator
./backend.ai app-proxy-coordinator start-server

# Start Worker
./backend.ai app-proxy-worker start-server
```

#### PostgreSQL Schema Migration
```bash
# Use App Proxy-specific Alembic configuration
./py -m alembic -c alembic-appproxy.ini upgrade head
```

## Metrics and Monitoring

### Logs
- Circuit creation and deletion events
- App proxy worker registration and deregistration events
- Proxy request tracking
- Health check results
- Errors and warnings

## Development

See [README.md](./README.md) for development setup instructions.

## Related documents

- [App proxy coordinator README](./coordinator/README.md) - app proxy coordinator details
- [App proxy worker README](./worker/README.md) - app proxy worker details
- [Traefik Integration Guide](../../../../docs/app-proxy/traefik-integration.md) - Traefik mode configuration and setup
- [Manager component](../manager/README.md) - API gateway
- [Agent component](../agent/README.md) - Container management
- [Overall architecture](../README.md) - System-wide architecture
