Backend.AI Common Package
=========================

← [Back to Backend.AI Architecture](../README.md)

[![PyPI release version](https://badge.fury.io/py/backend.ai-common.svg)](https://pypi.org/project/backend.ai-common/)
![Supported Python versions](https://img.shields.io/pypi/pyversions/backend.ai-common.svg)
[![Gitter](https://badges.gitter.im/lablup/backend.ai-common.svg)](https://gitter.im/lablup/backend.ai-common)

## Overview

The Backend.AI Common package provides utilities, infrastructure, and shared components used across all Backend.AI components (Manager, Agent, Storage Proxy, Webserver, App Proxy, etc.).

## Package Structure

### Entry Point System

Core event-based communication and asynchronous task processing framework for Backend.AI.

- **[events/](./events/README.md)** - Event Dispatcher System
  - Asynchronous event-based communication between components
  - Broadcast and Anycast event type support
  - Message queue-based event delivery
  - Event handler registration and routing

- **[bgtask/](./bgtask/README.md)** - Background Task Handler System
  - Process long-running tasks asynchronously
  - Issue Task IDs and track tasks
  - Progress monitoring and Heartbeat
  - Notify via event publishing upon completion

### Infrastructure Components

Client and abstraction layer for integration with external services and systems.

- **clients/** - External service client wrappers
  - Agent client (ZeroMQ RPC)
  - Storage Proxy client (HTTP)
  - Valkey/Redis client
  - etcd client

- **message_queue/** - Message queue interface and implementation
  - Provide message publish/subscribe interface
  - Currently implemented based on Redis Streams
  - Consumer Group management
  - Future support for other message queue systems planned

- **service_discovery/** - Service registration and integration
  - etcd-based service registration and discovery
  - Provide service information for Prometheus metrics collection
  - Automatic health check and update
  - Future expansion of additional service discovery features planned

- **resilience/** - Inter-layer communication resilience patterns
  - Generalize request processing between layers
  - Retry, Timeout, Circuit Breaker
  - Automatic metric collection
  - Fallback support

### Data and Types

Common structures for data exchange and type definitions between components.

- **dto/** - Data Transfer Objects (for inter-component communication)
  - Data structures used for inter-component communication
  - Request/Response models
  - Event payloads
  - Recommended to use Pydantic-based

- **types.py** - Common type definitions (for internal logic)
  - Domain types used within components (SessionId, AgentId, AccessKey, etc.)
  - Shared Enum types
  - Common constants
  - Mainly used in internal business logic

### Utilities

Utility modules for development convenience and common functionality.

- **metrics/** - Metrics collection and Prometheus integration
  - Metric observer pattern
  - Prometheus metric types (Counter, Gauge, Histogram)
  - HTTP metrics middleware

- **auth/** - Authentication utilities
  - Authentication between Webserver (Gateway) and Manager
  - JWT token generation/verification
  - Signature generation/verification
  - API Key management

- **web/** - Web utilities
  - HTTP helper functions
  - CORS configuration
  - Request/response processing

- **middlewares/** - Common middlewares
  - Commonly used across all components
  - Authentication middleware
  - Logging middleware
  - Error handling middleware

- **configs/** - Configuration management utilities
  - Configuration processing commonly used internally
  - Configuration file parsing (TOML, YAML)
  - Environment variable processing
  - Configuration validation

### Other Components

- **contexts/** - Context management utilities
  - ContextVar-based request and user tracking
  - Current request ID tracking
  - Current user information management
  - Context propagation

- **data/** - Common data utilities
  - Data-based value processing used in internal logic
  - Data transformation and validation
  - Common data type handling

- **exception.py** - Common exception classes
  - Base exceptions for all Backend.AI services
  - Exception definitions must inherit from BackendAIError
  - Domain-specific exception classes
  - Communicate error situations externally

- **utils.py** - Other utility functions
  - String processing
  - Time conversion
  - Other helper functions

## Installation

```console
$ pip install backend.ai-common
```

## For development

```console
$ pip install -U pip setuptools
$ pip install -U -r requirements/dev.txt
```

### Running test suite

```console
$ python -m pytest
```

With the default halfstack setup, you may need to set the environment variable `BACKEND_ETCD_ADDR`
to specify the non-standard etcd service port (e.g., `localhost:8110`).

The tests for `common.redis` module requires availability of local TCP ports 16379, 16380, 16381,
26379, 26380, and 26381 to launch a temporary Redis sentinel cluster via `docker compose`.

In macOS, they require a local `redis-server` executable to be installed, preferably via `brew`,
because `docker compose` in macOS does not support host-mode networking and Redis *cannot* be
configured to use different self IP addresses to announce to the cluster nodes and clients.

## Related Documentation

- [Event Dispatcher System](./events/README.md)
- [Background Task Handler System](./bgtask/README.md)
- [Manager Component](../manager/README.md)
- [Agent Component](../agent/README.md)
- [Storage Proxy Component](../storage/README.md)
