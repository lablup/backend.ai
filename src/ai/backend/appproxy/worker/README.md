# Backend.AI App Proxy Worker

## Purpose

The App Proxy Worker is a high-performance reverse proxy that routes user traffic to compute session services (Jupyter, SSH, TensorBoard, etc.) running on agents. It receives routing information from the Coordinator and handles SSL/TLS termination, load balancing, and traffic forwarding.

## Key Responsibilities

### 1. Traffic Proxying
- Proxy HTTP/HTTPS requests to session services
- Proxy WebSocket connections for interactive services
- Handle SSL/TLS termination
- Stream responses efficiently

### 2. Route Resolution
- Receive routing tables from Coordinator
- Resolve session services from URLs
- Cache routing information locally
- Update routes dynamically

### 3. Health Checking
- Monitor backend service health
- Detect failed services
- Report health status to Coordinator
- Handle service failover

## Architecture

### 1. Traffic Proxy (Main)

**Framework**: aiohttp + custom reverse proxy

**Port**: 5050 (default, HTTPS)

**Protocol**: HTTP/HTTPS, WebSocket

**Key Features**:

#### HTTP/HTTPS Proxy
- Route user requests to session services
- URL Pattern: `https://<worker-domain>/<session-id>/<service-name>/...`

#### WebSocket Proxy
- Interactive service communication (Jupyter Kernel, SSH, etc.)
- Real-time log streaming

**Key Characteristics**:
- SSL/TLS termination (Let's Encrypt auto-certificate)
- High-performance async proxy
- Connection pooling and reuse
- Streaming support (large file downloads)
- Sticky session support
- Auto-retry and failover

**Processing Flow**:

#### HTTP Proxy Flow
```
User → HTTPS Request → Worker (SSL termination)
                           ↓
                       Parse URL (extract session_id, service_name)
                           ↓
                       Lookup route from local cache
                           ↓
                       Resolve backend address (agent:port)
                           ↓
                       Proxy request to agent
                           ↓
                       Stream response back to user
```

#### WebSocket Proxy Flow
```
User → WS Upgrade Request → Worker
                               ↓
                           Establish WS connection to agent
                               ↓
                           Bidirectional message forwarding
```

### 2. REST API (Management)

**Framework**: aiohttp (async HTTP server)

**Port**: 6040 (default, separate management port)

**Key Features**:
- Communication with Coordinator
- Health check endpoints
- Metrics exposure (Prometheus)
- Internal management (no external access)

### Component Interaction

**Traffic Proxy Flow**:
```
User (Browser) → Worker (Port 5050) → Kernel (on Agent)
                    │
                    ├─ SSL/TLS termination
                    ├─ Route resolution
                    └─ Traffic proxying
```

**Management Flow**:
```
Coordinator → Worker REST API (Port 6040) → Route updates
```