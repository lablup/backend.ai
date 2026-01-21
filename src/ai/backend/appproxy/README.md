# Backend.AI App Proxy

## Purpose

The App Proxy provides dynamic routing and load balancing for service ports of computing sessions. Through a Coordinator-Worker architecture, it efficiently routes traffic to session services (Jupyter, SSH, TensorBoard, etc.) and supports load balancing across multiple session replicas.

## Key Responsibilities

### 1. Dynamic Service Routing
- Route HTTP/WebSocket traffic to session services
- Dynamically manage service port mappings
- Support port-based and subdomain-based proxying
- Automatic cleanup of routing rules on session termination

### 2. Load Balancing
- Distribute traffic across multiple session replicas
- Round-robin and weighted balancing
- Load distribution across worker nodes
- Automatic failover and health checks

### 3. Service Discovery and Registration
- Register service routes from Manager
- etcd-based distributed service discovery
- Automatic worker node registration and deregistration
- Real-time routing table synchronization

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
A circuit represents a routing rule from client to session service:
- **Circuit Key**: Unique identifier (session ID + service name)
- **Frontend**: Client entry point (port or subdomain)
- **Backend**: Proxy implementation (HTTP, H2, TCP, Traefik)
- **Target**: Actual service location (Agent host:port)
- **Status**: HEALTHY, UNHEALTHY, PENDING

Circuit Lifecycle:
1. Manager registers circuit on session creation
2. Coordinator deploys circuit to workers
3. Worker activates proxy rules
4. Client traffic routes through circuit
5. Circuit automatically deregistered on session termination

### Frontend Types

#### Port-based Frontend
- Assign unique port per service (e.g., 30001, 30002)
- Requires port forwarding in NAT environments
- Simple and direct access
- Requires firewall rule management

#### Subdomain-based Frontend
- Assign subdomain per service (e.g., `session-123.backend.ai`)
- Secure connection via SSL certificate
- Only ports 80/443 exposed
- Requires wildcard DNS

### Backend Types

Backends handle actual proxy implementation:

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
- Used for SSH, databases, etc.
- Minimal overhead

#### Traefik Backend
- Traefik integration
- Advanced routing rules
- Middleware chains
- Enterprise features

### Load Balancing Strategies

#### Round Robin
- Select workers sequentially
- Equal traffic distribution
- Simple and predictable
- Default strategy

#### Weighted
- Assign weights based on worker capacity
- Traffic distribution proportional to performance
- Suitable for heterogeneous worker environments
- Dynamic weight adjustment possible

#### Least Connections
- Select worker with fewest current connections
- Effective for long-lived connections
- Balances worker load
- Requires real-time metrics

## Coordinator Details

### Circuit Management
Coordinator manages the full lifecycle of circuits:
- Circuit registration and deregistration
- Circuit deployment to workers
- Circuit status monitoring
- Automatic redeployment on failure

### Worker Management
Worker registration and status tracking:
- Automatic worker registration and deregistration
- Periodic heartbeat reception
- Worker capacity and load monitoring
- Select target workers for circuit deployment

### Health Check
Coordinator periodically checks worker status:
- **Interval**: 5 seconds (default)
- **Timeout**: 2 seconds
- **Retries**: 3 attempts
- **Recovery**: Automatic circuit redeployment

## Worker Details

### Proxy Handling
Worker handles actual traffic proxying:
1. Receive client request
2. Look up routing rule by circuit key
3. Select appropriate backend
4. Forward request to target
5. Stream response
6. Record metrics

### Frontend Handling

#### Port-based
Worker dynamically allocates service-specific ports from specified port range.

#### Subdomain-based
Worker handles subdomain requests with wildcard SSL certificate.

### Backend Selection
Backend is automatically selected based on service type:
- **HTTP services**: HTTP or H2 backend
- **WebSocket**: HTTP backend (with upgrade support)
- **SSH/DB**: TCP backend
- **Complex routing**: Traefik backend

## Communication Protocols

### Manager → Coordinator
- **Protocol**: gRPC or REST
- **Port**: 6120 (default)
- **Authentication**: API key
- **Operations**:
  - Register/deregister circuits
  - Query worker information
  - Check health status

### Client → Worker
- **Protocol**: HTTP/HTTPS, WebSocket/WSS
- **Port**: 6130 (default) or dynamic ports
- **Operations**:
  - Access services (Jupyter, SSH, etc.)
  - WebSocket connections
  - File download/upload

### Worker → Coordinator
- **Protocol**: REST API
- **Operations**:
  - Worker registration and heartbeat
  - Circuit status updates
  - Metrics reporting

### Worker → Agent
- **Protocol**: HTTP/WebSocket or TCP
- **Operations**:
  - Forward traffic to actual service ports
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
Mitigate network bottlenecks by distributing traffic across workers

### Multiple Session Replicas
```
Client → Worker → Agent Pool
                  ├─ Agent 1 (Container Replica 1)
                  ├─ Agent 2 (Container Replica 2)
                  └─ Agent N (Container Replica N)
```
Provide high availability through load balancing across session replicas

## Configuration

See `configs/app-proxy-coordinator/halfstack.toml` and `configs/app-proxy-worker/halfstack.toml` for configuration file examples.

### Key Configuration Items

**Coordinator**:
- PostgreSQL database connection
- Worker health check interval
- etcd connection information

**Worker**:
- Coordinator connection information
- Frontend mode (port or subdomain)
- Backend timeout settings

## Infrastructure Dependencies

App Proxy consists of Coordinator and Worker, each with different infrastructure dependencies.

### Coordinator Infrastructure

#### PostgreSQL (Database)
- **Purpose**:
  - Store circuit routing rules
  - Manage worker registration information
  - Store health check status
- **Halfstack Port**: 8101 (shared with Manager)
- **Key Tables**:
  - `circuits` - Circuit routing information
  - `workers` - Worker registration and status
- **Schema Management**: Alembic migrations

#### etcd (Service Discovery)
- **Purpose**:
  - Worker auto-discovery
  - Distributed configuration management
  - Circuit synchronization
- **Halfstack Port**: 8121
- **Key Paths**:
  - `/appproxy/workers/{worker_id}` - Worker information
  - `/appproxy/circuits/{circuit_key}` - Circuit configuration

### Worker Infrastructure

#### Coordinator Connection
- **Purpose**:
  - Receive circuit deployments
  - Send heartbeats
  - Report metrics
- **Protocol**: REST API
- **Halfstack Port**: 6120 (Coordinator)

### Observability Infrastructure

#### Prometheus (Metrics Collection)
- **Coordinator Endpoint**: `http://localhost:6120/metrics`
- **Worker Endpoint**: `http://localhost:6130/metrics`
- **Key Metrics**:
  - Coordinator: Circuit/Worker management metrics
  - Worker: Proxy request and performance metrics
- **Service Discovery**: Automatic registration via Manager HTTP SD

#### Loki (Log Aggregation)
- **Purpose**:
  - Circuit creation/deletion events
  - Worker registration/deregistration events
  - Proxy request logs
  - Health check and error logs
- **Log Labels**:
  - `component` - coordinator or worker
  - `circuit_key` - Circuit identifier
  - `worker_id` - Worker identifier

#### Tempo (Distributed Tracing)
- **Purpose**:
  - Trace full requests through Circuit → Worker → Agent
  - Analyze proxy latency
  - Identify performance bottlenecks
- **Trace Transmission**: OpenTelemetry SDK

### Halfstack Configuration

**Recommended**: Use the `./scripts/install-dev.sh` script for development environment setup.

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
- Circuit creation/deletion events
- Worker registration/deregistration events
- Proxy request tracking
- Health check results
- Errors and warnings

## Development

See [README.md](./README.md) for development setup instructions.

## Related Documentation

- [Coordinator README](./coordinator/README.md) - Coordinator details
- [Worker README](./worker/README.md) - Worker details
- [Manager Component](../manager/README.md) - API gateway
- [Agent Component](../agent/README.md) - Container management
- [Overall Architecture](../README.md) - System-wide architecture
