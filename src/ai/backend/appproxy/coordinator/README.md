# Backend.AI app proxy coordinator

## Purpose

The app proxy coordinator manages routing information for app proxy workers, coordinates worker instances, and handles service port mappings for session services (Jupyter, SSH, TensorBoard, and so on).

## Key Responsibilities

### 1. Worker Management
- Register and track app proxy worker instances
- Monitor worker health and availability
- Distribute routing information to app proxy workers
- Handle worker failover

### 2. Route Management
- Manage service port mappings (session → service → port)
- Update routing tables dynamically
- Propagate route changes to app proxy workers
- Handle route conflicts and resolve them

### 3. Service Discovery
- Maintain the service registry
- Provide route lookup for app proxy workers
- Update routes when sessions change
- Clean up routes for terminated sessions

## Entry Points

The app proxy coordinator has one entry point to receive and process requests.

### 1. REST API

**Framework**: aiohttp (async HTTP server)

**Port**: 6030 (default)

**Primary Purpose**:
- Worker management (registration, monitoring)
- Routing information management (session-to-service port mapping)

**Key Features**:
- HTTP/HTTPS-based communication
- Centralized service routing information management
- Real-time route updates
- Persistent routing information storage in PostgreSQL

**Processing Flow**:

#### Worker Registration Flow
```
Worker → POST /workers/register → Coordinator
                                      ↓
                                  Register worker in DB
                                      ↓
                                  Return worker ID and routes
```

#### Route Creation Flow
```
Manager → POST /routes → Coordinator
                             ↓
                         Store route in DB
                             ↓
                         Notify all workers
                             ↓
                         Workers update local routing table
```

**Integrated Architecture**:

```
┌──────────────┐
│   Manager    │
│              │
└──────┬───────┘
       │ Route Management (REST)
       ▼
┌─────────────────────────────────────┐
│  App Proxy Coordinator (Port 6030)  │
│  - Worker registration              │
│  - Route management                 │
│  - Service port mapping             │
│  - Route propagation                │
└─────────┬───────────────────────────┘
          │
          ▼ Worker Registration & Route Updates
    ┌─────┴─────┬─────────┬─────────┐
    ▼           ▼         ▼         ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│Worker 1│ │Worker 2│ │Worker 3│ │Worker N│
└────────┘ └────────┘ └────────┘ └────────┘
```
